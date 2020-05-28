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

from time import monotonic

from prometheus_client import Histogram
from sanic.request import Request
from sanic.response import HTTPResponse

from immuni_common.monitoring.core import NAMESPACE, Subsystem

_START_TIME = "__START_TIME__"

REQUESTS_LATENCY = Histogram(
    namespace=NAMESPACE,
    subsystem=Subsystem.API.value,
    name="requests_latency",
    unit="seconds",
    labelnames=("path", "method", "http_status"),
    documentation="Requests latency in seconds.",
)


def sanic_before_request_handler(request: Request) -> None:
    """
    Collect metrics before a Sanic request has been handled.
    The collected values are stored in the request context allowing for the actual metric value
    computation after the request has been handled.

    :param request: request to be handled
    """
    request[_START_TIME] = monotonic()


def sanic_after_request_handler(request: Request, response: HTTPResponse) -> None:
    """
    Collect metrics after a Sanic request has been handled.

    :param request: handled request
    :param response: response of the handled request
    """
    latency = monotonic() - request[_START_TIME]
    labels = (
        request.path,
        request.method,
        # NOTE: Some handlers can ignore response logic (e.g., websocket handler)
        response.status if response else 200,
    )
    REQUESTS_LATENCY.labels(*labels).observe(latency)
