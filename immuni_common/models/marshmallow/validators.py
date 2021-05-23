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
import binascii
import re
from datetime import date, timedelta
from typing import Iterable, Optional

from marshmallow import ValidationError
from marshmallow.validate import Validator

from immuni_common.core import config

OTP_LENGTH = 10


class Base64StringValidator(Validator):
    """
    A validator for base64 strings.
    """

    def __init__(
        self,
        length: Optional[int],
        min_encoded_length: Optional[int],
        max_encoded_length: Optional[int],
    ) -> None:
        super().__init__()
        self._length = length
        self._min_encoded_length = min_encoded_length
        self._max_encoded_length = max_encoded_length

    def __call__(self, value: str) -> str:
        if self._min_encoded_length and (length := len(value)) < self._min_encoded_length:
            raise ValidationError(
                f"Invalid base64 string length: {length} minimum required length "
                f"{self._min_encoded_length}."
            )

        if self._max_encoded_length and (length := len(value)) > self._max_encoded_length:
            raise ValidationError(
                f"Invalid base64 string length: {length} maximum required length "
                f"{self._max_encoded_length}."
            )

        try:
            decoded = base64.b64decode(value)
        except binascii.Error as error:
            raise ValidationError("Invalid base64 string.") from error
        if self._length and (length := len(decoded)) != self._length:
            raise ValidationError(
                f"Invalid base64 string length: {length} instead of {self._length}."
            )
        return value


class IsoDateValidator(Validator):
    """
    A validator for date range.
    """

    _ALLOWED_TIMEDELTA = timedelta(days=config.MAX_ISO_DATE_BACKWARD_DIFF)

    def __call__(self, value: date) -> None:
        """
        Validate the date object.

        :param value: the date object to validate.
        :raises:
          ValidationError: if the date is more than _ALLOWED_TIMEDELTA days old.
          ValidationError: if the date is in the future.
        """
        today = date.today()
        if value > today:
            raise ValidationError(f"{value} is in the future.")
        if (today - value) > self._ALLOWED_TIMEDELTA:
            raise ValidationError(f"{value} is too far back in time.")


class HisCardExpiringDateValidator(Validator):
    """
    A validator for HIS (Health Information System) card expiring date.
    """

    def __call__(self, value: date) -> None:
        """
        Validate the date object.

        :param value: the date object to validate.
        :raises:
          ValidationError: if the date is in the past.
        """
        today = date.today()
        if value < today:
            raise ValidationError(f"{value} is in the past.")


class OtpCodeValidator(Validator):
    """
    A validator for the defined OTP format.
    """

    _ODD_MAP = {
        "1": 0,
        "2": 5,
        "3": 7,
        "4": 9,
        "5": 13,
        "6": 15,
        "7": 17,
        "8": 19,
        "9": 21,
        "A": 1,
        "E": 9,
        "F": 13,
        "H": 17,
        "I": 19,
        "J": 21,
        "K": 2,
        "L": 4,
        "Q": 6,
        "R": 8,
        "S": 12,
        "U": 16,
        "W": 22,
        "X": 25,
        "Y": 24,
        "Z": 23,
    }
    _EVEN_MAP = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "A": 0,
        "E": 4,
        "F": 5,
        "H": 7,
        "I": 8,
        "J": 9,
        "K": 10,
        "L": 11,
        "Q": 16,
        "R": 17,
        "S": 18,
        "U": 20,
        "W": 22,
        "X": 23,
        "Y": 24,
        "Z": 25,
    }
    # NOTE: The order must be preserved, do not change to set.
    _ALPHABET: tuple = (
        "A",
        "E",
        "F",
        "H",
        "I",
        "J",
        "K",
        "L",
        "Q",
        "R",
        "S",
        "U",
        "W",
        "X",
        "Y",
        "Z",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
    )
    _CHECK_DIGIT_MAP = dict(enumerate(_ALPHABET))

    def __call__(self, value: str) -> str:
        if len(value) == OTP_LENGTH:
            if not self._is_valid_otp(value):
                raise ValidationError("Invalid OTP code.")
        else:
            if not self._is_valid_otp_sha(value):
                raise ValidationError("Invalid OTP SHA256 code.")
        return value

    @classmethod
    def _compute_check_digit(cls, otp_without_check_digit: Iterable[str]) -> str:
        """
        Compute the check digit of the OTP code.

        :param otp_without_check_digit: the OTP code without the check digit.
        :return: the check digit char.
        """
        try:
            char_sum = sum(
                cls._ODD_MAP[char] if (index + 1) % 2 else cls._EVEN_MAP[char]
                for index, char in enumerate(otp_without_check_digit)
            )
            check_digit = cls._CHECK_DIGIT_MAP[char_sum % 25]
        except KeyError as error:
            raise ValidationError("The OTP code contains forbidden characters.") from error
        return check_digit

    @classmethod
    def _is_valid_otp(cls, otp: str) -> bool:
        """
        Assess whether the OTP code iv valid.

        :param otp: the OTP code to validate.
        :return: True if the OTP code is valid, False otherwise.
        """
        if len(otp) != OTP_LENGTH:
            return False
        expected = otp[-1]
        computed = cls._compute_check_digit(otp[:-1])
        return expected == computed

    @classmethod
    def _is_valid_otp_sha(cls, otp: str) -> bool:
        """
        Assess whether the OTP code is a valid sha256.

        :param otp: the OTP code to validate.
        :return: True if the OTP code is valid, False otherwise.
        """
        if otp is None or not re.match(r"^[A-Fa-f0-9]{64}$", str(otp)):
            return False
        return True
