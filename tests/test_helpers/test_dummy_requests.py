from http import HTTPStatus
from typing import Tuple

import pytest
from pytest_sanic.utils import TestClient
from sanic import Sanic
from sanic.request import Request
from sanic.response import HTTPResponse

from immuni_common.helpers.sanic import handle_dummy_requests
from immuni_common.helpers.utils import WeightedPair


@pytest.mark.parametrize(
    "conf",
    [
        (0, 1, HTTPStatus.NOT_FOUND),
        (1, 0, HTTPStatus.BAD_REQUEST),
        (0, 4, HTTPStatus.NOT_FOUND),
        (10, 0, HTTPStatus.BAD_REQUEST),
    ],
)
async def test_dummy_endpoints_simple(
    sanic: Sanic, conf: Tuple[int, int, HTTPStatus], client: TestClient
) -> None:
    bad_request_weight, not_found_weight, expected_status = conf

    @sanic.route("/dummy")
    @handle_dummy_requests(
        [
            WeightedPair(
                weight=bad_request_weight, payload=HTTPResponse(status=HTTPStatus.BAD_REQUEST)
            ),
            WeightedPair(
                weight=not_found_weight, payload=HTTPResponse(status=HTTPStatus.NOT_FOUND)
            ),
        ]
    )
    async def dummy(request: Request) -> HTTPResponse:
        return HTTPResponse(status=HTTPStatus.OK)

    response = await client.get("/dummy", headers={"Immuni-Dummy-Data": "0"})
    assert response.status == HTTPStatus.OK

    response = await client.get("/dummy", headers={"Immuni-Dummy-Data": "1"})
    assert response.status == expected_status
