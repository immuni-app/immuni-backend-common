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

from enum import Enum, auto
from typing import Any

from mongoengine import Document, ValidationError
from pytest import mark, raises

from immuni_common.models.mongoengine.enum_field import EnumField


class MyEnum(Enum):
    FIRST_VALUE = "some_value"
    SECOND_VALUE = "another_value"


class MyDocument(Document):
    enum_field = EnumField(MyEnum)


class AnotherEnum(Enum):
    A = auto()
    B = auto()


def test_enum_field() -> None:
    MyDocument(enum_field=MyEnum.FIRST_VALUE).save()
    MyDocument(enum_field=MyEnum.SECOND_VALUE).save()
    MyDocument(enum_field=MyEnum.SECOND_VALUE).save()

    assert MyDocument.objects.count() == 3
    assert MyDocument.objects.filter(enum_field=MyEnum.FIRST_VALUE).count() == 1
    assert MyDocument.objects.filter(enum_field=MyEnum.SECOND_VALUE).count() == 2

    reloaded = MyDocument.objects.get(enum_field=MyEnum.FIRST_VALUE)
    assert reloaded.enum_field == MyEnum.FIRST_VALUE


def test_enum_field_invalid_value() -> None:
    with raises(ValidationError):
        MyDocument(enum_field="INVALID_VALUE").save()


@mark.parametrize(
    "value", (MyEnum.FIRST_VALUE.name, MyEnum.FIRST_VALUE.value, "a_string", 0, None, dict())
)
def test_validate_raises_type_error(value: Any) -> None:
    with raises(TypeError):
        EnumField(MyEnum).validate(value)


@mark.parametrize("value", tuple(v for v in AnotherEnum))
def test_validate_raises_validation_error(value: Any) -> None:
    with raises(ValidationError):
        EnumField(MyEnum).validate(value)
