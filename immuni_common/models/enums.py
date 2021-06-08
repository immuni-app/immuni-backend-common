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

from __future__ import annotations

import logging
from enum import Enum
from typing import Type, TypeVar

from immuni_common.core.exceptions import ImmuniException

T = TypeVar("T")


class EnvarEnum(Enum):
    """
    Superclass for environment variables to be parsed as Enum.
    """

    @classmethod
    def from_env_var(cls: Type[T], value: str) -> T:
        """
        Parse the environment variable value and provide an informative error message on failure.

        :param value: the environment variable value.
        :return: the corresponding Enum entry.
        """
        try:
            return cls(value)  # type: ignore
        except ValueError as error:
            allowed = ", ".join(e.value for e in cls)  # type: ignore
            raise ImmuniException(f"Invalid environment: {value} (allowed: {allowed})") from error


class Environment(EnvarEnum):
    """
    Enumeration of the possible running environments.
    """

    DEVELOPMENT = "development"
    RELEASE = "release"
    STAGING = "staging"
    TESTING = "testing"


class LogLevel(EnvarEnum):
    """
    Enumeration of the possible log levels.
    """

    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"

    @classmethod
    def from_env_var(cls, value: str) -> LogLevel:
        """
        Parse the environment variable value and provide an informative error message on failure.

        :param value: the environment variable value.
        :return: the corresponding LogLevel entry.
        :raises: ImmuniException if the given log level is deprecated in the logging library.
        """
        environment = super().from_env_var(value)

        if environment.name not in logging._nameToLevel:  # pylint: disable=protected-access
            raise ImmuniException(f"Deprecated log level: {value}. Code update needed.")

        return environment


class Location(Enum):
    """
    Enumeration of the possible parameters locations.
    """

    HEADERS = "headers"
    JSON = "json"
    QUERY = "args"


class Platform(Enum):
    """
    Enumeration of the possible Mobile Clients platforms.
    """

    ANDROID = "android"
    IOS = "ios"


class TransmissionRiskLevel(Enum):
    """
    Enumeration of the different transmission risk levels.

    Taken from the official Apple documentation.
    See https://developer.apple.com/documentation/exposurenotification/enexposureinfo/3583716-transmissionrisklevel#discussion  # noqa: E501, pylint: disable=line-too-long
    """

    UNUSED_CUSTOM = 0
    CONFIRMED_TEST_LOW = 1
    CONFIRMED_TEST_STANDARD = 2
    CONFIRMED_TEST_HIGH = 3
    CONFIRMED_CLINICAL_DIAGNOSIS = 4
    SELF_REPORT = 5
    NEGATIVE_CASE = 6
    RECURSIVE_CASE = 7
    highest = 8  # TODO: remove after migrating Mongo document to use CONFIRMED_TEST_HIGH


class TokenType(Enum):
    """
    Enumeration of the possible token types.
    """

    CUN = "cun"
    NRFE = "nrfe"
    NUCG = "nucg"
    AUTHCODE = "authcode"
