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

from datetime import timedelta
from functools import wraps
from typing import Any, Awaitable, Callable, Optional

from sanic.response import HTTPResponse

from immuni_common.core import config
from immuni_common.core.exceptions import ImmuniException

_CACHE_CONTROL = "Cache-Control"


def cache(max_age: Optional[timedelta] = None, no_store: Optional[bool] = None) -> Callable:
    """
    Decorator to add cache headers to an endpoint response.

    :param max_age: the timedelta, if any, after which the cache would expire.
    :param no_store: True if the response shall not be cached.
    :return: the decorator.
    :raises:
      ImmuniException: if none or all arguments are defined.
      ImmuniException: if attempting to redefine the Cache-Control header.
    """

    def _decorator(
        f: Callable[..., Awaitable[HTTPResponse]]
    ) -> Callable[..., Awaitable[HTTPResponse]]:
        @wraps(f)
        async def _wrapper(*args: Any, **kwargs: Any) -> HTTPResponse:
            response = await f(*args, **kwargs)

            if not config.CACHE_ENABLED:
                return response

            if _CACHE_CONTROL in response.headers:
                raise ImmuniException(f"Attempt to redefine {_CACHE_CONTROL} headers.")

            # NOTE: Check for both defined or both undefined has already been done outside.
            if max_age:
                response.headers[_CACHE_CONTROL] = f"public, max-age={int(max_age.total_seconds())}"
            if no_store:
                response.headers[_CACHE_CONTROL] = "no-store"

            return response

        return _wrapper

    if not bool(max_age) ^ bool(no_store):
        raise ImmuniException(
            f"{cache.__name__} decorator arguments are mutually exclusive, and at least one shall "
            f"be defined (max_age: {max_age}, no_store: {no_store})."
        )

    return _decorator
