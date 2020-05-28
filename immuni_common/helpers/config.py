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
import logging
import pathlib
from typing import Callable

from croniter import croniter

from immuni_common.core.exceptions import ImmuniException

_LOGGER = logging.getLogger(__name__)


def load_certificate(config_name: str) -> Callable[[str], str]:
    """
    Return a callback to load a certificate from the given config.
    Try to load from a file, fallback on base64 content, then on plain content.

    :param config_name: the name of the config.
    :return: the callback to actually load the certificate from the given config.
    """

    def _load_certificate_value(config_content: str) -> str:
        is_base64 = False
        try:
            is_file = (path := pathlib.Path(config_content)).is_file()
            certificate = path.read_text()
        except (OSError, FileNotFoundError):
            is_file = False
            try:
                certificate = base64.b64decode(config_content).decode("utf-8")
                is_base64 = True
            except (binascii.Error, ValueError):
                certificate = config_content

        _LOGGER.debug(
            "Loaded certificate from %s",
            config_name,
            extra=dict(content_length=len(certificate), is_file=is_file, is_base64=is_base64),
        )
        return certificate

    return _load_certificate_value


def validate_crontab(config_name: str) -> Callable[[str], str]:
    """
    Return a callback to ensure the given config is a valid crontab string.

    :param config_name: the name of the config.
    :return: the callback to actually validate the crontab string.
    :raises: ImmuniException if the crontab string is invalid.
    """

    def _validate_crontab(value: str) -> str:
        if not croniter.is_valid(value):
            raise ImmuniException(f"Invalid crontab string for {config_name}: {value}.")
        return value

    return _validate_crontab
