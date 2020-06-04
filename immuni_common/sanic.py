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

import logging
import os
from http import HTTPStatus
from typing import Any, Iterable, Optional

import prometheus_client
from prometheus_client import multiprocess
from sanic import Blueprint, Sanic
from sanic.exceptions import SanicException
from sanic.request import Request
from sanic.response import HTTPResponse
from sanic_openapi import doc, swagger_blueprint

from immuni_common.core import config
from immuni_common.core.exceptions import ApiException
from immuni_common.core.managers import BaseManagers
from immuni_common.helpers.logging import get_sanic_logger_config
from immuni_common.helpers.sanic import json_response
from immuni_common.models.enums import Environment
from immuni_common.monitoring.core import initialize_monitoring
from immuni_common.monitoring.sanic import sanic_after_request_handler, sanic_before_request_handler

_LOGGER = logging.getLogger(__name__)


# pylint: disable=too-many-locals
def create_app(
    api_title: str, api_description: str, blueprints: Iterable[Blueprint], managers: BaseManagers,
) -> Sanic:
    """
    Create the Sanic application.

    :param api_title: the title of the API in the /swagger endpoint.
    :param api_description: the description of the API in /swagger endpoint.
    :param blueprints: the Sanic blueprints to register.
    :param managers: the microservice's managers.
    :return: the created Sanic application.
    """
    app = Sanic(__name__, log_config=get_sanic_logger_config(config.LOG_JSON_INDENT))
    app.config.TESTING = config.ENV == Environment.TESTING

    swagger_config = dict(
        API_TITLE=api_title,
        API_DESCRIPTION=api_description,
        API_SCHEMES=["https"],
        API_VERSION="1.0.0",
        SWAGGER_UI_CONFIGURATION=dict(
            validatorUrl=None, displayRequestDuration=True, docExpansion="list",
        ),
    )
    app.config.update(swagger_config)

    monitoring_registry = initialize_monitoring()

    @app.route("/")
    @doc.summary("Health check.")
    @doc.response(HTTPStatus.OK.value, "Ok", description="The server is running ok.")
    async def health_check(request: Request) -> HTTPResponse:
        return HTTPResponse(status=HTTPStatus.OK.value)

    # TODO: Evaluate whether to expose it over another port.
    @app.route("/metrics")
    @doc.summary("Expose Prometheus metrics.")
    def metrics(request: Request) -> HTTPResponse:
        latest_metrics = prometheus_client.generate_latest(monitoring_registry)
        return HTTPResponse(
            body=latest_metrics.decode("utf-8"),
            content_type=prometheus_client.CONTENT_TYPE_LATEST,
            headers={"Content-Length": str(len(latest_metrics))},
        )

    @app.listener("after_server_start")
    async def after_server_start(*args: Any, **kwargs: Any) -> None:
        await managers.initialize()

    @app.listener("before_server_stop")
    async def before_server_stop(*args: Any, **kwargs: Any) -> None:
        await managers.teardown()

    @app.listener("after_server_stop")
    async def after_server_stop(*args: Any, **kwargs: Any) -> None:
        multiprocess.mark_process_dead(os.getpid())

    @app.middleware("request")
    async def before_request(request: Request) -> None:
        sanic_before_request_handler(request)

    @app.middleware("response")
    async def after_response(request: Request, response: HTTPResponse) -> None:
        sanic_after_request_handler(request, response)

    @app.exception(ApiException)
    async def handle_exception(request: Request, exception: ApiException) -> HTTPResponse:
        _LOGGER.exception(exception)
        return json_response(
            body={"error_code": exception.error_code, "message": exception.error_message},
            status=exception.status_code,
        )

    @app.exception(SanicException)
    async def handle_unknown_exception(request: Request, exception: SanicException) -> HTTPResponse:
        _LOGGER.exception(exception)
        return json_response(
            body={"error_code": ApiException.error_code, "message": ApiException.error_message},
            status=HTTPStatus(exception.status_code),
        )

    @app.exception(Exception)
    async def handle_bare_exception(request: Request, exception: Exception) -> HTTPResponse:
        _LOGGER.exception(exception)
        return json_response(
            body={"error_code": ApiException.error_code, "message": ApiException.error_message},
            status=ApiException.status_code,
        )

    for blueprint in blueprints:
        app.blueprint(blueprint)
    app.blueprint(swagger_blueprint)

    return app


def run_app(sanic_app: Sanic, auto_reload: Optional[bool] = False) -> None:
    """
    Utility function to run the sanic application during development.

    :param sanic_app: the Sanic application to run.
    :param auto_reload: whether or not to enable the auto-reload feature.
    """
    sanic_app.run(
        host=config.API_HOST,
        port=config.API_PORT,
        debug=config.ENV != Environment.RELEASE,
        auto_reload=auto_reload,
    )
