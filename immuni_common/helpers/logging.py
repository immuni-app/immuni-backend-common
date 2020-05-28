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
import sys

from pythonjsonlogger import jsonlogger

from immuni_common.models.enums import LogLevel


def initialize_logging(log_level: LogLevel) -> None:
    """
    Initialize logging and set proper default levels and formatters.

    :param log_level: the log level to set.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.name)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level.name)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s "
        "%(name)s "
        "%(pathname)s "
        "%(funcName)s "
        "%(lineno)d "
        "%(process)d "
        "%(processName)s "
        "%(thread)d "
        "%(threadName)s "
        "%(levelname)s  "
        "%(message)s",
        json_indent=2,
    )
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
