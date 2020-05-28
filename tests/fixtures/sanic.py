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

from asyncio import AbstractEventLoop
from typing import Awaitable, Callable

from pytest import fixture
from pytest_sanic.utils import TestClient
from sanic import Sanic

from immuni_common.core.managers import BaseManagers
from immuni_common.sanic import create_app


@fixture
def sanic(monitoring_setup: None) -> Sanic:
    yield create_app(api_title="", api_description="", blueprints=tuple(), managers=BaseManagers())


@fixture
async def sanic_custom_client(sanic_client: TestClient) -> TestClient:
    yield sanic_client


@fixture
def client(
    loop: AbstractEventLoop, sanic: Sanic, sanic_custom_client: Callable[[Sanic], Awaitable]
) -> TestClient:
    return loop.run_until_complete(sanic_custom_client(sanic))
