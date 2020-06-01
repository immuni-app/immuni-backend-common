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

import logging
import re
import sys
from typing import Any, Dict, Optional, Set

from gunicorn import glogging
from pythonjsonlogger import jsonlogger
from pythonjsonlogger.jsonlogger import RESERVED_ATTRS
from sanic.log import LOGGING_CONFIG_DEFAULTS

from immuni_common.models.enums import LogLevel


class RedactingJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom logging Json formatter, in charge of redacting sensitive information too.
    """

    _LOGGING_ATTRS = {
        "%(asctime)s",
        "%(name)s",
        "%(pathname)s",
        "%(funcName)s",
        "%(lineno)d",
        "%(process)d",
        "%(processName)s",
        "%(thread)d",
        "%(threadName)s",
        "%(levelname)s ",
        "%(message)s",
    }

    _RESERVED_ATTRS = {
        "host",  # the sanic request IP.
        "scope",  # the uvicorn field containing client IP.
    }

    _REDACT_PATTERNS = [
        r"(?:[0-9]{1,3}\.){3}[0-9]{1,3}",  # Any IP (simple regex, allows numbers > 255 too).
    ]

    def __init__(
        self, json_indent: Optional[int], logging_attrs: Optional[Set[str]] = None
    ) -> None:
        """
        :param json_indent: the log json indentation.
        :param logging_attrs: the attributes to log, in addition to the default ones.
        """
        super().__init__(
            fmt=" ".join(
                sorted(
                    self._LOGGING_ATTRS.union(
                        set(
                            attr
                            for attr in logging_attrs or set()
                            if all(reserved not in attr for reserved in self._RESERVED_ATTRS)
                        )
                    )
                )
            ),
            reserved_attrs={*RESERVED_ATTRS, *self._RESERVED_ATTRS},
            json_indent=json_indent if json_indent else None,
        )

    def format(self, record: logging.LogRecord) -> str:
        """
        Format and redact the log record.

        :param record: the log record to format and redact.
        :return: the formatted and redacted log record, as string.
        """
        message = super().format(record)
        for pattern in self._REDACT_PATTERNS:
            message = re.sub(pattern, "***", message)
        return message


class CustomGunicornLogger(glogging.Logger):
    """
    Custom logger for Gunicorn log messages.

    Gunicorn should be instructed to use this logger through its specific command line option:
        --logger-class=immuni_common.helpers.logging.CustomGunicornLogger
    """

    def setup(self, cfg: Any) -> None:
        """
        Configure Gunicorn application logging configuration.
        """
        super().setup(cfg)
        self._set_handler(self.error_log, cfg.errorlog, RedactingJsonFormatter(json_indent=None))
        self._set_handler(self.access_log, cfg.accesslog, RedactingJsonFormatter(json_indent=None))


def initialize_logging(log_level: LogLevel, log_json_indent: int) -> None:
    """
    Initialize logging and set proper default levels and formatters.

    :param log_level: the log level to set.
    :param log_json_indent: the log json indentation.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.name)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level.name)
    handler.setFormatter(RedactingJsonFormatter(json_indent=log_json_indent))
    root_logger.addHandler(handler)


def get_sanic_logger_config(log_json_indent: int) -> Dict[str, Any]:
    """
    Return the Sanic logger configuration.
    It starts off from the Sanic's default configuration, overriding the formatters, removing
    sensible fields (i.e., host).
    # NOTE: This is needed when running Sanic standalone. Gunicorn does not use Sanic loggers.

    :param log_json_indent: the log json indentation.
    :return: the Sanic logger configuration.
    """
    logging_config = {**LOGGING_CONFIG_DEFAULTS}
    custom_formatter = f"{RedactingJsonFormatter.__module__}.{RedactingJsonFormatter.__name__}"
    logging_config["formatters"] = {
        "generic": {
            "()": custom_formatter,
            "json_indent": log_json_indent,
            "logging_attrs": ("%(asctime)s", "%(process)d", "%(levelname)s", "%(message)s"),
        },
        "access": {
            "()": custom_formatter,
            "json_indent": log_json_indent,
            "logging_attrs": (
                "%(asctime)s",
                "%(name)s",
                "%(levelname)s",
                "%(request)s",
                "%(message)s",
                "%(status)d",
                "%(byte)d",
            ),
        },
    }
    return logging_config


def setup_celery_logger(logger: logging.Logger, log_json_indent: int) -> None:
    """
    Change the Celery logger formatters to use the custom one.

    :param logger: the Celery logger.
    :param log_json_indent: the log json indentation.
    """
    for handler in logger.handlers:
        handler.setFormatter(RedactingJsonFormatter(json_indent=log_json_indent))
