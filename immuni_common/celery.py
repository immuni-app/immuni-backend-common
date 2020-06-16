#  Copyright (C) 2020 Presidenza del Consiglio dei Ministri.
#  Please refer to the AUTHORS file for more information.
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <https://www.gnu.org/licenses/>.

from dataclasses import dataclass
from datetime import timedelta
from logging import Logger
from types import ModuleType
from typing import Any, Callable, Dict, ItemsView, Iterable, Optional, Union

from celery import Celery
from celery.schedules import crontab
from celery.signals import after_setup_logger
from celery.task import Task
from croniter import croniter

from immuni_common.core import config
from immuni_common.helpers.logging import setup_celery_logger
from immuni_common.helpers.utils import dense_dict, modules_in_package


def string_to_crontab(crontab_string: str) -> crontab:
    """
    Parse a crontab string into a crontab object.

    :param crontab_string: the crontab string to parse.
    :return: the parsed crontab object.
    """
    return crontab(*[",".join(map(str, x)) for x in croniter(crontab_string).expanded])


@dataclass(frozen=True)
class Schedule:
    """
    Human friendly representation of a task schedule.
    """

    task: Task
    when: Union[crontab, timedelta]
    with_params: Optional[Dict[str, Any]] = None

    def to_celery(self) -> ItemsView:
        """
        Translate the object in a format suitable for Celery.

        :return: the items view of the different schedules in a format suitable for Celery.
        """
        return {
            self.task.name: dense_dict(
                dict(task=self.task.name, schedule=self.when, kwargs=self.with_params)
            )
        }.items()


def _overall_schedule(*schedules: Schedule) -> Dict[Any, Any]:
    """
    Compute the overall schedule in a suitable format for Celery based on the given schedules
    objects.

    :param schedules: the schedules objects to be serialized in a suitable format for Celery.
    :return: the dict of serialized schedules in a suitable format for Celery.
    """
    return {
        task_name: task_schedule_dict
        for s in schedules
        for task_name, task_schedule_dict in s.to_celery()
    }


class CeleryApp(Celery):
    """
    Wrapper around Celery aimed at standardizing the configuration among Immuni's microservices.
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        service_dir_name: str,
        broker_redis_url: str,
        always_eager: bool,
        tasks_module: ModuleType,
        schedules_function: Optional[Callable[[], Iterable[Schedule]]] = None,
        routes_function: Optional[Callable[[], Dict[str, Dict]]] = None,
    ) -> None:
        """
        :param service_dir_name: the microservice directory name.
        :param broker_redis_url: the Redis instance URL to be used as broker.
        :param always_eager: whether or not tasks should be executed in eager mode.
        :param tasks_module: the module where tasks are to be found.
        :param schedules_function: the callback function to retrieve the tasks' schedules, if any.
        :param routes_function: the callback function to retrieve the tasks' routes, if any.
        """

        super().__init__(__name__, broker=broker_redis_url)
        self.conf.enable_utc = True
        self.conf.worker_max_tasks_per_child = 100  # to keep workers relatively fresh
        self.conf.worker_send_task_events = True
        self.conf.task_send_sent_event = True
        self.conf.imports = modules_in_package(tasks_module)
        self.conf.task_always_eager = self.conf.task_eager_propagates = always_eager
        self.conf.task_default_queue = service_dir_name
        self.__service_dir_name__ = service_dir_name
        self.__schedules_function = schedules_function
        self.__routes_function = routes_function

        self.on_after_configure.connect(self._after_configure)

    def _after_configure(self, sender: Celery, **kwargs: Any) -> None:
        """
        Hook to avoid circular imports.
        Providing the schedules and routes functions to the __init__ method and calling them there
        creates a circular import. This is because the Celery app (self) is not initialized yet when
        the function reaches the tasks code, which in turn requires the Celery app to decorate the
        task with `@celery_app.task`. Calling these functions here make it so that the Celery app
        has already been initialized upfront, yet we call them before the Celery app is actually
        started.
        """
        if self.__schedules_function:
            self.conf.beat_schedule = _overall_schedule(*self.__schedules_function())
        if self.__routes_function:
            self.conf.task_routes = self.__routes_function()

    def gen_task_name(self, name: str, module: str) -> str:
        """
        Generate the task name.

        :param name: the name of the function implementing the task.
        :param module: the module containing the function implementing the task.
        :return: the name of the task stripped of the common path.
        """
        return super().gen_task_name(
            name, module[len(f"{self.__service_dir_name__}.tasks.") :]  # noqa
        )


@after_setup_logger.connect
def setup_loggers(logger: Logger, *args: Any, **kwargs: Any) -> None:
    """
    Callback to execute after the original Celery logger is set.

    :param logger: the Celery logger.
    :param args: the additional positional arguments, ignored here.
    :param kwargs: the additional keyword arguments, ignored here.
    """
    setup_celery_logger(logger, config.LOG_JSON_INDENT)
