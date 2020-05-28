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

from enum import Enum

from prometheus_client import Gauge, multiprocess
from prometheus_client.registry import CollectorRegistry

from immuni_common.core import config

NAMESPACE = "immuni"


class Subsystem(Enum):
    """
    Enumeration of possible monitoring subsystems.
    """

    API = "api"
    BUILD = "build"


# NOTE: Using Gauge since Info does not work in a Prometheus multiprocess setup.
_BUILD_INFO = Gauge(
    namespace=NAMESPACE,
    name=Subsystem.BUILD.value,
    documentation="Git build information.",
    labelnames=("git_short_sha", "git_sha", "git_branch", "git_tag", "build_date"),
    multiprocess_mode="liveall",
)


def _expose_build_info(git_sha: str, git_branch: str, git_tag: str, build_date: str) -> None:
    """
    Expose the build information as a Prometheus metric.

    :param git_sha: the Git SHA of the running code.
    :param git_branch: the Git branch of the running code.
    :param git_tag: the Git tag of the running code.
    :param build_date: the date the running code image was built.
    """

    _BUILD_INFO.labels(git_sha[:7], git_sha, git_branch, git_tag, build_date).set(1)


def initialize_monitoring() -> CollectorRegistry:
    """
    Setup for Prometheus multiprocess mode, exposing build info right away.

    :return: the multiprocess registry, where the different processes are to store metrics.
    """
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    _expose_build_info(
        git_sha=config.GIT_SHA,
        git_branch=config.GIT_BRANCH,
        git_tag=config.GIT_TAG,
        build_date=config.BUILD_DATE,
    )
    return registry
