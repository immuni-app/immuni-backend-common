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

from enum import Enum
from typing import Any, Type, TypeVar, Union

from mongoengine import StringField

T = TypeVar("T", bound=Enum)


class EnumField(StringField):
    """
    Enum field to store (and retrieve) Enum values from (and to) the mongo database seamlessly.
    """

    def __init__(self, enum: Type[T], **kwargs: Any) -> None:
        """
        :param enum: the enum class associated with the MongoDB's field.
        :param kwargs: the currently ignored additional initialisation arguments.
        """
        self._enum = enum
        super().__init__(**kwargs)

    def _invalid_value_error(self, value: Union[T, str]) -> None:
        """
        Raise error exception for invalid value.

        :param value: the invalid value.
        :raises: ValidationError.
        """
        self.error(
            f"Invalid value for enum {self._enum}. "
            f"Given: {value}, allowed: {[v.name for v in self._enum]}"
        )

    def to_python(self, value: str) -> T:
        """
        Return the Python Enum entry corresponding to given value, for seamless retrieval.

        :param value: the value to translate into Python Enum.
        :return: the Python Enum entry corresponding to the given value.
        :raises: ValidationError if the value is invalid.
        """
        if isinstance(value, self._enum):
            return value
        string_value = super().to_python(value)
        try:
            enum_value = self._enum[string_value]
        except KeyError:
            self._invalid_value_error(string_value)
        return enum_value

    def validate(self, value: T) -> None:
        """
        Assess the value corresponds to one of the Enum entries.

        :param value: the value to validate.
        :raises: ValidationError if the value is not one of the Enum entries.
        """
        if value not in self._enum:
            self._invalid_value_error(value)

    def to_mongo(self, value: T) -> str:
        """
        Return the string counterpart of the given Enum value, for seamless storage.

        :param value: the Enum value to convert into string.
        :return: the string counterpart of the given Enum value
        """
        return value.name

    def prepare_query_value(self, op: str, value: T) -> str:
        """
        Prepare the value for query execution.

        :param op: the operation, ignored here.
        :param value: the value to prepare for query execution.
        :return: the value for query execution.
        """
        return self.to_mongo(value)
