"""
All of the methods and objects defined in this module are meant to be used in the testing
environment only.
"""

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

import os
import random
from functools import wraps
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any, AsyncGenerator, Callable, Generator, Iterable, Set
from unittest.mock import patch
from urllib.parse import urlparse

import prometheus_client.values
import pytest
from _pytest.fixtures import FixtureFunctionMarker
from aioredis import Redis

from immuni_common.core import config
from immuni_common.models.enums import Environment
from immuni_common.models.marshmallow.validators import OtpCodeValidator

_ALLOWED_REDIS_SCHEMES = {"redis"}
_ALLOWED_REDIS_HOSTNAMES = {"redis", "localhost"}

_ALLOWED_MONGO_SCHEMES = {"mongodb"}
_ALLOWED_MONGO_HOSTNAMES = {"mongo", "localhost"}


class OutsideTestingEnvironment(Exception):
    """
    Raised when running outside of the testing environment.
    """

    def __init__(self, current: Environment) -> None:
        """
        :param current: the environment the code is running in.
        """
        super().__init__(
            f"Refusing to execute tests outside of testing environment (current: {current.value})."
        )


class UnsafeTestingUrl(Exception):
    """
    Raised when the URL is not suitable for a testing environment.
    """

    def __init__(self, config_name: str, field: str, value: str, allowed: Iterable[str]) -> None:
        """
        :param config_name: the name of the unsafe configuration environment variable.
        :param field: the URL field which is invalid.
        :param value: the invalid URL field value.
        :param allowed: the allowed values for the given URL field.
        """
        super().__init__(f"{config_name}: invalid '{value}' {field} (allowed: {list(allowed)})")


def _check_testing_url(
    url: str, config_name: str, allowed_schemes: Set[str], allowed_hostnames: Set[str]
) -> None:
    """
    Assess whether the given URL is suitable for a testing environment.

    :param url: the URL of the configuration environment variable.
    :param config_name: the name of the configuration environment variable.
    :param allowed_schemes: the allowed values for the scheme URL field.
    :param allowed_hostnames: the allowed values for the hostname URL field.
    :raises: UnsafeTestingUrl if either the scheme or hostname is not among the allowed ones.
    """
    parsed = urlparse(url)
    if parsed.scheme not in allowed_schemes:
        raise UnsafeTestingUrl(
            config_name=config_name, field="scheme", value=parsed.scheme, allowed=allowed_schemes
        )
    if (hostname := str(parsed.hostname)) not in allowed_hostnames:
        raise UnsafeTestingUrl(
            config_name=config_name, field="hostname", value=hostname, allowed=allowed_hostnames
        )


def check_redis_url(url: str, config_name: str) -> None:
    """
    Assess whether the given Redis URL is suitable for a testing environment.

    :param url: the URL of the configuration environment variable.
    :param config_name: the name of the configuration environment variable.
    :raises: UnsafeTestingUrl if either the scheme or hostname is not among the allowed ones.
    """
    _check_testing_url(
        url=url,
        config_name=config_name,
        allowed_schemes=_ALLOWED_REDIS_SCHEMES,
        allowed_hostnames=_ALLOWED_REDIS_HOSTNAMES,
    )


def check_mongo_url(url: str, config_name: str) -> None:
    """
    Assess whether the given MongoDB URL is suitable for a testing environment.

    :param url: the URL of the configuration environment variable.
    :param config_name: the name of the configuration environment variable.
    :raises: UnsafeTestingUrl if either the scheme or hostname is not among the allowed ones.
    """
    _check_testing_url(
        url=url,
        config_name=config_name,
        allowed_schemes=_ALLOWED_MONGO_SCHEMES,
        allowed_hostnames=_ALLOWED_MONGO_HOSTNAMES,
    )


def check_environment() -> None:
    """
    Assess whether the code is running in the testing environment.

    :raises: OutsideTestingEnvironment if the environment is not the testing one.
    """
    if config.ENV != Environment.TESTING:
        raise OutsideTestingEnvironment(config.ENV)


@pytest.fixture
def monitoring_setup() -> Generator[None, None, None]:
    """
    Mock the directory containing the prometheus metrics.
    """
    env_var = "prometheus_multiproc_dir"  # NOTE: chosen by Prometheus, no control over it.
    with patch("prometheus_client.values.ValueClass", prometheus_client.values.MultiProcessValue()):
        with TemporaryDirectory(prefix="monitoring") as monitoring_dir:
            if os.environ.get(env_var) is not None:
                raise RuntimeError(f"{env_var} environment variable should not be None.")
            os.environ[env_var] = monitoring_dir
            yield
            del os.environ[env_var]
            # The context manager takes care of the directory cleanup.


def create_no_expired_keys_fixture(redis: Redis) -> FixtureFunctionMarker:
    """
    Create an autouse fixture to ensure there are no Redis keys without expiration time being set.
    NOTE: It should be called from another autouse fixture that depends on the redis initialization.
    """

    @pytest.fixture(autouse=True)
    async def _fixture() -> AsyncGenerator[None, None]:
        """
        After each test, ensure there are no Redis keys without expiration time being set.
        """
        yield

        keys = await redis.keys("*")
        keys_without_expiration = set()
        for key in keys:
            if await redis.ttl(key) == -1:
                keys_without_expiration.add(keys)
        if len(keys_without_expiration) != 0:
            raise RuntimeError(
                f"There are Redis keys without TTL, namely {list(keys_without_expiration)}."
            )

    return _fixture


def mock_config(config_to_mock: ModuleType, key: str, value: Any) -> Callable:
    """
    Mock a configuration value for the decorated test case.

    :param config_to_mock: the config object that contains the key to mock.
    :param key: the key to mock.
    :param value: the value to assign.
    :return: the decorator to mock the specified configuration key.
    """

    def _decorator(f: Callable) -> Callable:
        @wraps(f)
        async def _wrapper(*args: Any, **kwargs: Any) -> Any:
            old_value = getattr(config_to_mock, key)
            setattr(config_to_mock, key, value)
            ret = await f(*args, **kwargs)
            setattr(config_to_mock, key, old_value)
            return ret

        return _wrapper

    return _decorator


# pylint: disable=protected-access
def generate_otp(length: int = 10, skip_validation: bool = False) -> str:
    """
    Generate an OTP of specified length.

    :param length: the length of the OTP to generate.
    :param skip_validation: whether the validation step should be skipped, useful for negative
      testing.
    :return: the generated OTP.
    :raises:
      RuntimeError: if used outside of testing environment.
      RuntimeError: if the requested length is less than 2.
      RuntimeError: if the generated otp is invalid (when validation is not explicitly skipped).
    """
    if config.ENV != Environment.TESTING:
        raise RuntimeError("Meant to run within testing environment only.")

    if length < 2:
        raise RuntimeError("Cannot generate such a short OTP code.")

    chars = random.choices(OtpCodeValidator._ALPHABET, k=length - 1)  # no-qa
    otp = "".join(chars) + OtpCodeValidator._compute_check_digit(chars)  # no-qa

    if not skip_validation and not OtpCodeValidator._is_valid_otp(otp):
        raise RuntimeError(f"An invalid OTP code has been generated: {otp}.")

    return otp
