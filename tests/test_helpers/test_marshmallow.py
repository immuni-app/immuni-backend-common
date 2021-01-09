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

import base64
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, Optional, Tuple, Type

from marshmallow import ValidationError
from pytest import mark, raises

from immuni_common.helpers.tests import generate_otp
from immuni_common.models.marshmallow.fields import (
    Base64String,
    Countries,
    EnumField,
    IdTestVerification,
    IntegerBoolField,
    IsoDate,
    LastHisNumber,
    OtpCode,
    Province,
)
from immuni_common.models.marshmallow.schemas import OtpDataSchema
from immuni_common.models.marshmallow.validators import IsoDateValidator, OtpCodeValidator

_OTP_DATA_SERIALIZED = {"symptoms_started_on": date.today().isoformat()}

_COMMON_INVALID_FIELD_VALUES: Tuple[Any, ...] = (
    "invalid",
    1,
    2.0,
    None,
    dict(),
    list(),
    set(),
    tuple(),
)


def test_otp_code_validator_odd_map() -> None:
    assert set(OtpCodeValidator._ODD_MAP.keys()) == set(OtpCodeValidator._ALPHABET)


def test_otp_code_validator_even_map() -> None:
    assert set(OtpCodeValidator._EVEN_MAP.keys()) == set(OtpCodeValidator._ALPHABET)


@mark.parametrize("value", ("mock", ""))
def test_base64_string_success(value: str) -> None:
    bas64encoded = base64.b64encode(value.encode("utf-8"))

    Base64String().validate(bas64encoded)  # type:ignore
    Base64String(length=len(value)).validate(bas64encoded)  # type:ignore


@mark.parametrize(
    "length, value",
    (
        (None, "non-base64-string"),
        (16, base64.b64encode("non-16-bytes-long-string".encode("utf-8"))),
    ),
)
def test_base64_string_failure_on_value(length: Optional[int], value: str) -> None:
    with raises(ValidationError):
        Base64String(length=length).validate(value)  # type:ignore


def test_base64_string_failure_on_init() -> None:
    with raises(ValueError):
        Base64String(validate=lambda value: print("dummy"))


def test_base64_string_max_length() -> None:
    with raises(ValidationError):
        Base64String(max_encoded_length=5).validate("123456")  # type:ignore


def test_base64_string_min_length() -> None:
    with raises(ValidationError):
        Base64String(min_encoded_length=5).validate("1234")  # type:ignore


@mark.parametrize("value", ["YWJj", "YWE="])
def test_base64_string_length(value: str) -> None:
    with raises(ValidationError):
        Base64String(min_encoded_length=1, max_encoded_length=5).validate("123456")  # type:ignore


@mark.parametrize(
    "otp",
    (
        "XSZ4RAQ3KY",
        "X65FS597US",
        "S8SJ6UZRHQ",
        "8UZLUU8UW5",
        "Z86JQXHAW8",
        "HEQHQ7FYQZ",
        "JAS62UHE58",
        "FQ2YQE43LR",
        "87S8QWH1EE",
        "527AZ66UHX",
        "b39e0733843b1b5d7c558f52f117a824dc41216e0c2bb671b3d79ba82105dd94",
        generate_otp(),
    ),
)
def test_otp_code_success(otp: str) -> None:
    OtpCode().validate(otp)  # type:ignore


@mark.parametrize(
    "value",
    (
        generate_otp(length=2, skip_validation=True),
        generate_otp(length=9, skip_validation=True),
        generate_otp(length=11, skip_validation=True),
        generate_otp(length=100, skip_validation=True),
        "AEFHIJ1234",  # 10 chars, all allowed.
        "AEFHIJ123N",  # 10 chars, one not allowed, check digit (i.e., N).
        "NEFHIJ1234",  # 10 chars, one not allowed (i.e., N).
        # Generated as valid, then replaced check-digit with first, and assessed invalidity.
        "UFKLYIZXLU",
        "3QW6EYRU53",
        "47F2JAKRF4",
        "F5YEH3128F",
        "QK7W33UU8Q",
        "8L4FQZ8UX8",
        "6EQSE6KW56",
        "XZ2LR2245X",
        "A6F3XQQ1YA",
        "HL2S4U3A6H",
        "b39e0733843b1b5d7c558f52f117a824dc41216e0c2bb671b3d79ba82105dd94784728afb",  # not valid sha256
        *(v for v in _COMMON_INVALID_FIELD_VALUES if hasattr(v, "__len__")),
    ),
)
def test_otp_code_failure(value: str) -> None:
    with raises(ValidationError):
        OtpCode().validate(value)  # type:ignore


@mark.parametrize("value", ["FC", "MI"])
def test_province_success(value: str) -> None:
    Province().validate(value)  # type:ignore


@mark.parametrize("value", ["FCA", "M", "", "as"])
def test_province_failure(value: str) -> None:
    with raises(ValidationError):
        Province().validate(value)  # type:ignore


@mark.parametrize("value", [["DK", "DE"], ["ES", "AT", "PL"], []])
def test_countries_success(value: list) -> None:
    Countries().validate(value)  # type:ignore


def test_symptoms_started_on_success_format() -> None:
    IsoDate()._deserialize(date.today().isoformat(), None, None)  # type:ignore


@mark.parametrize(
    "value", (date.today(), date.today() - IsoDateValidator._ALLOWED_TIMEDELTA,),
)
def test_symptoms_started_on_success_value(value: date) -> None:
    IsoDate().validate(value)  # type: ignore


@mark.parametrize(
    "value",
    (
        "02/29/2020",
        "20200229",
        "20200229T21:23:58.970460+00:00",
        "2020-02-29T21:23:58.970460+00:00",
        *_COMMON_INVALID_FIELD_VALUES,
    ),
)
def test_symptoms_started_on_failure_format(value: str) -> None:
    with raises(ValidationError):
        IsoDate()._deserialize(value, None, None)  # type:ignore


@mark.parametrize(
    "value",
    (
        date.today() + timedelta(days=1),
        date.today() - timedelta(days=1) - IsoDateValidator._ALLOWED_TIMEDELTA,
    ),
)
def test_symptoms_started_on_failure_value(value: date) -> None:
    with raises(ValidationError):
        IsoDate().validate(value)  # type: ignore


def test_otp_data_schema_success() -> None:
    OtpDataSchema().load(_OTP_DATA_SERIALIZED)


def test_otp_schema_fails_on_missing_required() -> None:
    with raises(ValidationError):
        OtpDataSchema().load(dict())


@mark.parametrize(
    "invalid_json",
    tuple(
        {additional_field: additional_value, **_OTP_DATA_SERIALIZED}
        for additional_field, additional_value in {
            "another": "field",
            "leads": 2,
            "failure": True,
        }.items()
    ),
)
def test_otp_schema_fails_on_additional(invalid_json: Dict[str, str]) -> None:
    with raises(ValidationError):
        OtpDataSchema().load(invalid_json)


class TestEnum(Enum):
    NAME_1 = "value_1"
    NAME_2 = "value_2"
    NAME_3 = "value_3"


@mark.parametrize("enum,value", list((TestEnum, v.value) for v in TestEnum))
def test_enum_field(enum: Type[Enum], value: str) -> None:
    EnumField(enum=enum)._deserialize(value, None, None)


@mark.parametrize(
    "enum,value",
    [(TestEnum, v) for v in ["value_4", "value1", None, [], 0, 1, False, True, {}]],  # type: ignore
)
def test_enum_field_raises(enum: Type[Enum], value: Any) -> None:
    with raises(ValidationError):
        EnumField(enum=enum)._deserialize(value, None, None)


def test_enum_field_serialize() -> None:
    assert EnumField(enum=TestEnum)._serialize(TestEnum.NAME_1, "", None) == TestEnum.NAME_1.value


@mark.parametrize("value", [0, 1])
def test_integerbool_field(value: int) -> None:
    IntegerBoolField()._deserialize(value, None, None)


@mark.parametrize(
    "value", ["0", "1", True, False, "true", "false", "True", "False", None, "", "1", "0", [], {}]
)
def test_integerbool_field_raises(value: Any) -> None:
    with raises(ValidationError):
        IntegerBoolField()._deserialize(value, None, None)


@mark.parametrize("value", ["FCA", "123456", "12345A569", "00981", "123456789"])
def test_last_his_number_failure(value: str) -> None:
    with raises(ValidationError):
        LastHisNumber().validate(value)  # type:ignore


@mark.parametrize(
    "value",
    [
        "2d8af3b92c0a4efc9e1572454f994e1f",
        "d8af3b9-2c0a-4efc-9e15-72454f994e1f",
        "72454f994e1f2c0a-4efc-9e15-d8af3b9",
        "123456789jshq04251701",
    ],
)
def test_id_test_verification_failure(value: str) -> None:
    with raises(ValidationError):
        IdTestVerification().validate(value)  # type:ignore
