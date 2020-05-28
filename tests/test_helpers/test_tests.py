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

from unittest.mock import patch

from pytest import mark, raises

from immuni_common.helpers.tests import generate_otp
from immuni_common.models.enums import Environment


@mark.parametrize("length", (2, 9, 11, 100))
def test_generate_otp_invalid_otp_success(length: int) -> None:
    assert len(generate_otp(length=length, skip_validation=True)) == length


@mark.parametrize("length", (2, 9, 11, 100))
def test_generate_otp_invalid_otp_failure(length: int) -> None:
    with raises(RuntimeError) as exception:
        generate_otp(length=length, skip_validation=False)
        assert "invalid" in str(exception)


def test_generate_otp_valid_success() -> None:
    assert len(generate_otp(skip_validation=False)) == 10


@mark.parametrize("length", (1, 0, -10))
def test_generate_otp_failure_too_short(length: int) -> None:
    with raises(RuntimeError) as exception:
        generate_otp(length=length)
        assert "too short" in str(exception)


def test_generate_otp_failure_wrong_environment() -> None:
    with patch("immuni_common.helpers.tests.config.ENV", Environment.RELEASE):
        with raises(RuntimeError):
            generate_otp()
