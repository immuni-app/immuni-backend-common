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

import itertools
import json
import os
from datetime import date, datetime
from enum import Enum, auto
from http import HTTPStatus
from typing import Any, Dict

from marshmallow import fields
from marshmallow.fields import Field
from pytest import mark, raises
from pytest_sanic.utils import TestClient
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse

from immuni_common.core.exceptions import SchemaValidationException
from immuni_common.helpers.sanic import CustomJSONEncoder, Serializable, json_response, validate
from immuni_common.models.enums import Location


class ASerialisable(Serializable):
    SERIALIZED_CONSTANT = "serialized-constant"

    def serialize(self) -> Dict[str, Any]:
        return dict(serialized=self.SERIALIZED_CONSTANT)


async def test_health_check(client: TestClient) -> None:
    response = await client.get("/")
    assert response.status == HTTPStatus.OK


async def test_ips_are_not_logged(client: TestClient, capfd: Any) -> None:
    response = await client.get("/")
    assert response.status == HTTPStatus.OK
    out = capfd.readouterr()[0]
    lines = [json.loads(line) for line in out.splitlines()]
    assert any("request" in line for line in lines)
    for line in lines:
        if "request" in line:
            assert line["request"].startswith("GET http://***:")


@mark.skip(reason="Passes alone, fails when ran together with the rest")  # FIXME
async def test_metrics_at_start(client: TestClient) -> None:
    response = await client.get("/metrics")
    assert response.status == HTTPStatus.OK
    actual = await response.text()
    expected = (
        "b'# HELP immuni_build Multiprocess metric\\n"
        "# TYPE immuni_build gauge\\n"
        "immuni_build{"
        'build_date="no-release",'
        'git_branch="no-release",'
        'git_sha="no-release",'
        'git_short_sha="no-prod",'
        'git_tag="no-release",'
        f'pid="{os.getpid()}"'
        "} 1.0\\n'"
    )
    assert actual == expected


@mark.skip(reason="Passes alone, fails when ran together with the rest")  # FIXME
async def test_metrics_after_one_request(client: TestClient) -> None:
    await client.get("/")
    response = await client.get("/metrics")
    assert response.status == HTTPStatus.OK
    actual = await response.text()
    assert "immuni_api_requests_latency_seconds_count" in actual


@mark.parametrize(
    "location,validation_fields,expected",
    list(
        itertools.chain.from_iterable(
            [
                [
                    (
                        location,
                        {"test_string": fields.String(required=True)},
                        {"test_string": "test"},
                    ),
                    (location, {"test_string": fields.String(required=False)}, {}),
                    (
                        location,
                        {
                            "test_string": fields.String(required=True),
                            "test_int": fields.Int(required=True, validate=lambda x: x > 10),
                        },
                        {"test_string": "test", "test_int": 11},
                    ),
                    (
                        location,
                        {
                            "test_string": fields.String(required=True),
                            "test_int": fields.Int(required=False, validate=lambda x: x > 10),
                        },
                        {"test_string": "test"},
                    ),
                    (location, {}, {},),
                ]
                for location in Location
            ]
        ),
    ),
)
async def test_validate_query_args(
    location: Location,
    validation_fields: Dict[str, Field],
    expected: Dict[str, Any],
    sanic: Sanic,
    client: TestClient,
) -> None:
    @sanic.route("/validated")
    @validate(location=location, **validation_fields)
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response(kwargs)

    if location == Location.QUERY:
        query_string = "&".join([f"{k}={v}" for k, v in expected.items()])
        response = await client.get(f"/validated?{query_string}")
    elif location == Location.JSON:
        response = await client.get(
            "/validated", json=expected, headers={"content-type": "application/json; charset=utf-8"}
        )
    else:
        headers = {k: str(v) for k, v in expected.items()}
        response = await client.get("/validated", headers=headers)

    assert response.status == HTTPStatus.OK

    json = await response.json()
    assert json == expected


@mark.parametrize(
    "validation_fields,headers_data,expected",
    [
        (
            {"test_string": fields.String(required=True, data_key="Header-Test-String")},
            {"Header-Test-String": "test", "Ignored": "ignored"},
            {"test_string": "test"},
        )
    ],
)
async def test_validate_data_key_headers(
    validation_fields: Dict[str, Field],
    headers_data: Dict[str, str],
    expected: Dict[str, Any],
    sanic: Sanic,
    client: TestClient,
) -> None:
    @sanic.route("/validated")
    @validate(location=Location.HEADERS, **validation_fields)
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response(kwargs)

    response = await client.get("/validated", headers=headers_data)

    assert response.status == HTTPStatus.OK

    json = await response.json()
    assert json == expected


async def test_validate_raises_if_multiple_values_for_query_arg(
    sanic: Sanic, client: TestClient,
) -> None:
    @sanic.route("/validated")
    @validate(location=Location.QUERY, test_string=fields.String(required=True))
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response({})

    response = await client.get("/validated?test_string=test1&test_string=test2")

    assert response.status == HTTPStatus.BAD_REQUEST
    assert await response.json() == {
        "error_code": SchemaValidationException.error_code,
        "message": SchemaValidationException.error_message,
    }


async def test_validate_raises_if_post_has_not_json_content_type(
    sanic: Sanic, client: TestClient,
) -> None:
    @sanic.route("/validated", methods=["POST"])
    @validate(location=Location.JSON, test_string=fields.String(required=True))
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response({})

    response = await client.post(
        "/validated", headers={"Content-Type": "text/html"}, json={"test_string": "example"}
    )

    assert response.status == HTTPStatus.BAD_REQUEST
    assert await response.json() == {
        "error_code": SchemaValidationException.error_code,
        "message": SchemaValidationException.error_message,
    }


async def test_validate_raises_if_same_fields_more_than_once(
    sanic: Sanic, client: TestClient,
) -> None:
    @sanic.route("/validated", methods=["POST"])
    @validate(location=Location.JSON, test_string=fields.String(required=True))
    @validate(location=Location.JSON, test_string=fields.String(required=True))
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response({})

    response = await client.post(
        "/validated",
        headers={"content-type": "application/json; charset=utf-8"},
        json={"test_string": "example"},
    )

    assert response.status == HTTPStatus.INTERNAL_SERVER_ERROR


async def test_validate_raised_if_field_is_invalid(sanic: Sanic, client: TestClient) -> None:
    @sanic.route("/validated", methods=["GET"])
    @validate(location=Location.QUERY, test_string=fields.String(required=True))
    async def validated(request: Request, **kwargs: Dict[str, Any]) -> HTTPResponse:
        return json_response({})

    response = await client.get("/validated",)

    assert response.status == SchemaValidationException.status_code
    assert await response.json() == dict(
        error_code=SchemaValidationException.error_code,
        message=SchemaValidationException.error_message,
    )


def test_serializable_raises_when_not_overridden() -> None:
    class MySerializable(Serializable, dict):
        pass

    with raises(NotImplementedError):
        MySerializable().serialize()


@mark.parametrize(
    "value, expected",
    (
        (1, "1"),
        ("a", '"a"'),
        (None, "null"),
        (dict(), "{}"),
        (list(), "[]"),
        (set(), "[]"),
        (iter([1, 2]), "[1, 2]"),
        (date(year=2020, month=1, day=2), '"2020-01-02"'),
        (datetime(year=2020, month=1, day=2), '"2020-01-02T00:00:00"'),
        (ASerialisable(), f'{{"serialized": "{ASerialisable.SERIALIZED_CONSTANT}"}}'),
    ),
)
def test_serializer_supports_defined_types(value: Any, expected: Any) -> None:
    assert json.dumps(value, cls=CustomJSONEncoder) == expected


def test_serializer_does_not_support_undefined_types() -> None:
    class NonSerializable(Enum):
        A = auto()
        B = auto()

    with raises(TypeError) as exception:
        json.dumps(NonSerializable.A, cls=CustomJSONEncoder)
        assert "is not JSON serializable" in str(exception)
