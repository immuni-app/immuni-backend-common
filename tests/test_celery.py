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

from datetime import datetime
from typing import Any, Dict, Tuple

from pytest import fixture

from celery import Celery
from celery.apps.worker import Worker
from celery.local import PromiseProxy
from celery.schedules import crontab
from celery.task import Task
from immuni_common.celery import CeleryApp, Schedule, _overall_schedule
from tests import fake_tasks_module
from tests.conftest import REDIS_URL


@fixture
def local_celery_app_config(monitoring_setup: None) -> Dict[str, Any]:
    return dict(
        service_dir_name="mock",
        broker_redis_url=REDIS_URL,
        always_eager=True,
        tasks_module=fake_tasks_module,
    )


@fixture
def local_celery_app(local_celery_app_config: Dict[str, Any]) -> CeleryApp:
    return CeleryApp(**local_celery_app_config)


@fixture
def a_dummy_celery_task(local_celery_app: CeleryApp, celery_worker: Worker) -> PromiseProxy:
    @local_celery_app.task
    def _a_dummy() -> int:
        return 42

    # NOTE: Avoiding the following reload causes the worker not to know about the just registered
    #       task and raise UnrecoverableError
    celery_worker.reload()

    return _a_dummy


@fixture
def another_dummy_celery_task(local_celery_app: Celery, celery_worker: Worker) -> PromiseProxy:
    @local_celery_app.task()
    def _another_dummy() -> None:
        pass

    # NOTE: Avoiding the following reload causes the worker not to know about the just registered
    #       task and raise UnrecoverableError
    celery_worker.reload()

    return _another_dummy


def _schedule_crontab(minute: int) -> crontab:
    """
    Schedule to avoid having a task running during the tests execution.
    :return: the
    """
    now_hour = datetime.utcnow().hour
    return crontab(hour=1 if now_hour == 0 else (now_hour - 1), minute=minute)


def test_celery_app_creation(local_celery_app: CeleryApp) -> None:
    assert local_celery_app.conf.task_default_queue == "mock"


def test_celery_task_can_execute(a_dummy_celery_task: Task) -> None:
    assert a_dummy_celery_task.delay().get(timeout=2) == 42


def test_overall_schedule_different_tasks(
    a_dummy_celery_task: Task, another_dummy_celery_task: Task
) -> None:
    a_schedule_crontab = _schedule_crontab(minute=0)
    a_schedule = Schedule(task=a_dummy_celery_task, when=a_schedule_crontab)

    another_schedule_crontab = _schedule_crontab(minute=1)
    another_schedule = Schedule(task=another_dummy_celery_task, when=another_schedule_crontab,)

    actual = _overall_schedule(a_schedule, another_schedule)
    expected = {
        "celery._a_dummy": {"task": "celery._a_dummy", "schedule": a_schedule_crontab},
        "celery._another_dummy": {
            "task": "celery._another_dummy",
            "schedule": another_schedule_crontab,
        },
    }
    assert actual == expected


def test_overall_schedule_same_task(a_dummy_celery_task: Task) -> None:
    a_schedule_crontab = _schedule_crontab(minute=0)
    a_schedule = Schedule(task=a_dummy_celery_task, when=a_schedule_crontab)

    another_schedule_crontab = _schedule_crontab(minute=0)
    another_schedule_for_same_task = Schedule(task=a_schedule.task, when=another_schedule_crontab,)

    # NOTE: order matters, the last prevails
    actual = _overall_schedule(a_schedule, another_schedule_for_same_task)
    expected = {
        "celery._a_dummy": {"task": "celery._a_dummy", "schedule": another_schedule_crontab},
    }
    assert actual == expected


def test_celery_app_creation_with_schedules(
    local_celery_app_config: Dict[str, Any],
    a_dummy_celery_task: Task,
    another_dummy_celery_task: Task,
) -> None:
    def _get_schedule() -> Tuple[Schedule, ...]:
        return (
            Schedule(task=a_dummy_celery_task, when=_schedule_crontab(minute=0)),
            Schedule(task=another_dummy_celery_task, when=_schedule_crontab(minute=0)),
        )

    celery_app = CeleryApp(
        **local_celery_app_config, schedules_function=_get_schedule  # type:ignore
    )
    assert len(celery_app.conf.beat_schedule) == 2


def test_celery_app_creation_with_routes(
    local_celery_app_config: Dict[str, Any],
    a_dummy_celery_task: Task,
    another_dummy_celery_task: Task,
) -> None:
    def _get_route() -> Dict[str, Dict]:
        return {
            a_dummy_celery_task.name: dict(queue="a_queue"),
            another_dummy_celery_task.name: dict(queue="mock"),
        }

    celery_app = CeleryApp(
        **local_celery_app_config, routes_function=_get_route  # type: ignore
    )
    assert len(celery_app.conf.task_routes) == 2
    assert celery_app.conf.task_routes == _get_route()
