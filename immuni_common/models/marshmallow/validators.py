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
from datetime import date, timedelta
from typing import Iterable, List, Optional

from marshmallow import ValidationError
from marshmallow.validate import Validator

from immuni_common.core import config
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey


class Base64StringValidator(Validator):
    """
    A validator for base64 strings.
    """

    def __init__(self, length: Optional[int]) -> None:
        super().__init__()
        self._length = length

    def __call__(self, value: str) -> str:
        try:
            decoded = base64.b64decode(value)
        except binascii.Error:
            raise ValidationError("Invalid base64 string.")
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


class OtpCodeValidator(Validator):
    """
    A validator for the defined OTP format.
    """

    _OTP_LENGTH = 10
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
        if not self._is_valid_otp(value):
            raise ValidationError("Invalid OTP code.")
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
        except KeyError:
            raise ValidationError("The OTP code contains forbidden characters.")
        return check_digit

    @classmethod
    def _is_valid_otp(cls, otp: str) -> bool:
        """
        Assess whether the OTP code iv valid.

        :param otp: the OTP code to validate.
        :return: True if the OTP code is valid, False otherwise.
        """
        if len(otp) != cls._OTP_LENGTH:
            return False
        expected = otp[-1]
        computed = cls._compute_check_digit(otp[:-1])
        return expected == computed


class TekListValidator(Validator):
    """
    A validator for a list of TEKs.
    """

    def __call__(self, value: List[TemporaryExposureKey]) -> None:
        """
        Validations to be performed according to Apple's documentation:

        - Any ENIntervalNumber values from the same user are not unique.
        - The period of time covered by the data file exceeds 14 days.
        - There are any gaps in the ENIntervalNumber values for a user.
        - Any keys in the file have overlapping time windows.
        - The TEKRollingPeriod value is not 144.

        :param value: the value of the schema being validated.
        """

        # NOTE: This kind of validation (rolling_period == 144) could be performed at field level.
        #   We expect all of these validations to change in the future, so having them all together
        #   here is done on purpose to make things simpler in case of changes in validation.
        #   We would like to keep field validation more flexible as not to spread strict validation
        #   logic in many places.
        if len(value) == 0:
            return

        if any(tek.rolling_period != 144 for tek in value):
            raise ValidationError("Some rolling values are not 144.")

        if (n_keys := len(value)) > 14:
            raise ValidationError(f"Too many TEKs. (actual: {n_keys}, max_allowed: 14)")

        rolling_start_numbers = set(tek.rolling_start_number for tek in value)
        min_start_number = min(rolling_start_numbers)
        expected_start_numbers = set(min_start_number + 144 * i for i in range(n_keys))

        if rolling_start_numbers != expected_start_numbers:
            raise ValidationError("Unexpected rolling start numbers identified.")
