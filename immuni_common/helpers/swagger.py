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

from typing import Callable, Type

from sanic_openapi import doc

from immuni_common.core.exceptions import ApiException


def doc_exception(exception: Type[ApiException]) -> Callable:
    """
    Decorator to document the provided exception in Swagger.

    :param exception: the exception to document.
    :return: the decorator to document the provided exception.
    """
    return doc.response(
        exception.status_code.value,
        dict(
            error_code=doc.String(
                description=exception.error_code, choices=(exception.error_code,), required=True
            ),
            message=doc.String(
                description=exception.error_message,
                choices=(exception.error_message,),
                required=True,
            ),
        ),
        description=exception.error_message,
    )
