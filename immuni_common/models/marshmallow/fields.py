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

import sys
from enum import Enum
from typing import Any, Optional, Type

from marshmallow import ValidationError, validate
from marshmallow.fields import Date, Field, Integer, List, String
from marshmallow.validate import Length, Range

from immuni_common.models.marshmallow.validators import (
    Base64StringValidator,
    IsoDateValidator,
    OtpCodeValidator,
)


class AttenuationDurations(List):
    """
    Validate the attenuation_duration
    """

    def __init__(self) -> None:
        super().__init__(
            Integer(validate=Range(min=0, max=sys.maxsize)),
            required=True,
            validate=Length(min=3, max=4),
        )


class Base64String(String):
    """
    Validate a base64-encoded string.
    """

    def __init__(
        self,
        *args: Any,
        length: Optional[int] = None,
        min_encoded_length: Optional[int] = None,
        max_encoded_length: Optional[int] = None,
        **kwargs: Any,
    ) -> None:
        """
        :param args: the positional arguments of the String field.
        :param length: the length, if any, the string shall have to be considered valid.
        :param min_encoded_length: the minimum length, if any, the encoded string shall have
         to be considered valid.
        :param max_encoded_length: the maximum length, if any, the encoded string shall have
         to be considered valid.
        :param kwargs: the keyword arguments of the String field.
        :raises: ValueError if the keyword arguments specify the "validate" keyword.
        """
        if "validate" in kwargs:
            raise ValueError(f"{Base64String.__name__} does not accept validate.")

        super().__init__(
            *args,
            **kwargs,
            validate=Base64StringValidator(
                length=length,
                min_encoded_length=min_encoded_length,
                max_encoded_length=max_encoded_length,
            ),
        )  # type: ignore


class EnumField(Field):
    """
    Validate enumerations.
    """

    def __init__(self, enum: Type[Enum]) -> None:
        """
        :param enum: the Enum class to validate against.
        """
        self._enum: Type[Enum] = enum
        super().__init__(required=True)

    def _serialize(self, value: Any, attr: str, obj: Any, **kwargs: Any) -> Any:
        return value.value

    def _deserialize(self, value: str, attr: Any, data: Any, **kwargs: Any) -> Any:
        try:
            return self._enum(value)
        except ValueError:
            raise ValidationError(f"{value} is not in {[e.name for e in self._enum]}")


class IntegerBoolField(Field):
    """
    Validate an integer in range [0,1].
    """

    def __init__(self, *args: Any, allow_strings: bool = False, **kwargs: Any) -> None:
        self.allow_strings = allow_strings
        super(IntegerBoolField, self).__init__(*args, **kwargs)

    def _deserialize(self, value: Any, attr: Any, data: Any, **kwargs: Any) -> bool:
        if self.allow_strings and isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                raise ValidationError(f"{value} is not a valid integer.")

        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 1:
            return bool(value)

        raise ValidationError(f"{value} is not an integer in range [0,1].")


class IsoDate(Date):
    """
    Validate a date in ISO format, not in the future, nor too back in time.
    """

    def __init__(self) -> None:
        super().__init__(required=True, format="%Y-%m-%d", validate=IsoDateValidator())


class OtpCode(String):
    """
    Validate the OTP code format.
    """

    def __init__(self) -> None:
        super().__init__(required=True, validate=OtpCodeValidator())


class Province(String):
    """
    Validate the province.
    """

    def __init__(self) -> None:
        super().__init__(required=True, validate=validate.Regexp(r"^[A-Z]{2}$"))


class RiskScore(Integer):
    """
    Validate a risk score.
    """

    def __init__(self) -> None:
        super().__init__(required=True, validate=Range(min=0, max=sys.maxsize))
