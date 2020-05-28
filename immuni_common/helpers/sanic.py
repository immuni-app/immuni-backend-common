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

import json
from collections.abc import Iterable
from datetime import date, datetime
from functools import wraps
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Dict, Optional, Union

from marshmallow import Schema, ValidationError
from marshmallow.fields import Field
from sanic.request import Request
from sanic.response import HTTPResponse

from immuni_common.core.exceptions import ImmuniException, SchemaValidationException
from immuni_common.models.enums import Location

_ALLOWED_JSON_CONTENT_TYPES = {
    "application/json; charset=utf-8",
    "application/json",
}


class Serializable:
    """
    Base class for serializable objects.
    All subclasses can be serialized with the CustomJSONEncoder.
    """

    def serialize(self) -> Dict[str, Any]:
        """
        Abstract method to serialize the class instance.

        :return: the serialized class instance.
        :raises: NotImplementedError if the subclass does not overrides this method.
        """
        raise NotImplementedError()


class CustomJSONEncoder(json.JSONEncoder):
    """
    JSON encoder class to serialize objects not serializable with the default JSON serializer.
    """

    def default(self, o: Any) -> Any:
        """
        Default serialization of this encoder.

        :param o: the object to be serialized.
        :return: the serialized object.
        """
        if isinstance(o, Serializable):
            return o.serialize()
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        if isinstance(o, Iterable):
            return list(o)
        return super().default(o)


def json_response(
    body: Any,
    status: HTTPStatus = HTTPStatus.OK,
    headers: Optional[Dict] = None,
    content_type: str = "application/json; charset=utf-8",
) -> HTTPResponse:
    """
    Compute a JSON response from the input arguments.

    :param body: the response body.
    :param status: the response HTTP status.
    :param headers: the response HTTP headers.
    :param content_type: the response content type.
    :return: the resulting HTTPResponse object.
    """
    return HTTPResponse(
        body="" if body is None else json.dumps(body, cls=CustomJSONEncoder),
        status=status.value,
        headers=headers,
        content_type=content_type,
    )


def validate(*, location: Location, **fields: Union[Field, type],) -> Callable:
    """
    Validate the request input data given a location and marshmallow fields.

    :param location: the request location where to look for the specified fields.
    :param fields: the fields to validate.
    :return: the decorator in charge of validating the request input data.
    :raises:
        SchemaValidationException: on request's invalid input data.
        ImmuniException: if the specified fields have already been validated.
    """

    def _decorator(
        f: Callable[..., Awaitable[HTTPResponse]]
    ) -> Callable[..., Awaitable[HTTPResponse]]:
        @wraps(f)
        async def _wrapper(request: Request, *args: Any, **kwargs: Any) -> HTTPResponse:
            data = getattr(request, location.value, {})
            if location == Location.HEADERS:
                data = _remap_data_keys(data)
            elif location == Location.QUERY:
                _validate_query_args_length(data)
            elif location == Location.JSON:
                _validate_json_content_type(request)
            schema = Schema.from_dict(fields)
            try:
                valid_data = schema().load(data)  # pylint: disable=no-member
            except ValidationError as exc:
                raise SchemaValidationException(exc.messages) from exc

            if intersection := set(kwargs.keys()).intersection(set(valid_data.keys())):
                raise ImmuniException(
                    f"Trying to validate some fields more than once: {list(intersection)}."
                )

            kwargs.update(**valid_data)

            return await f(request, *args, **kwargs)

        def _remap_data_keys(data: Dict[str, Any]) -> Dict[str, Any]:
            """
            Remap headers to specified keys, if any.

            :param data: the headers dictionary.
            :return: the remapped headers, with map keys being the specified ones.
            """
            filtered_headers = dict()
            for field_key, field in fields.items():
                lookup_key = (
                    field.data_key if isinstance(field, Field) and field.data_key else field_key
                )
                value = data.get(lookup_key)
                if value is not None:
                    filtered_headers[lookup_key] = value
            return filtered_headers

        def _validate_query_args_length(data: Dict[str, Any]) -> None:
            """
            Assess there is exactly one value for each query arg.

            :param data: the query args dictionary.
            :raises: SchemaValidationException if any of the query args does not have exactly one
              value.
            """
            if any(len(val) != 1 for val in data.values()):
                raise SchemaValidationException("Query args with more than one value found.")

        def _validate_json_content_type(request: Request) -> None:
            """
            Assess the content type is application/json for POST requests.

            :param request: the Sanic request object.
            :raises: SchemaValidationException if the content type is not application/json
            """
            if (
                request.method == "POST"
                and request.headers.get("content-type", "missing").lower()
                not in _ALLOWED_JSON_CONTENT_TYPES
            ):
                raise SchemaValidationException(
                    "Content type is not application/json for post request."
                )

        return _wrapper

    return _decorator
