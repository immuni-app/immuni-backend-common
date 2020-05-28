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

import os
from typing import Generator, Iterable

import pytest
from decouple import config
from mongoengine import connect

# noinspection PyUnresolvedReferences
from immuni_common.helpers.tests import monitoring_setup  # noqa isort:skip

# noinspection PyUnresolvedReferences
from tests.fixtures.sanic import *  # noqa isort:skip


def _monitoring_files(directory: str) -> Iterable[str]:
    return (filename for filename in os.listdir(directory) if filename.endswith(".db"))


@pytest.fixture(autouse=True, scope="function")
def init_db() -> Generator[None, None, None]:
    db = connect("test")
    yield
    db.drop_database("test")


REDIS_URL: str = config("REDIS_URL", default="redis://localhost:6379/0")
