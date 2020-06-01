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

from decouple import config

from immuni_common.helpers.logging import initialize_logging
from immuni_common.models.enums import Environment, LogLevel

LOG_LEVEL: LogLevel = config("LOGLEVEL", cast=LogLevel.from_env_var, default=LogLevel.INFO)
LOG_JSON_INDENT: int = config("LOG_JSON_INDENT", cast=int, default=0)
initialize_logging(LOG_LEVEL, LOG_JSON_INDENT)

# The following are supposed to be filled at Docker build time.
GIT_BRANCH: str = config("GIT_BRANCH", default="no-release")
GIT_SHA: str = config("GIT_SHA", default="no-release")
GIT_TAG: str = config("GIT_TAG", default="no-release")
BUILD_DATE: str = config("BUILD_DATE", default="no-release")

ENV: Environment = config("ENV", cast=Environment.from_env_var, default=Environment.TESTING)

API_HOST: str = config("API_HOST", default="0.0.0.0")
API_PORT: int = config("API_PORT", default="5000", cast=int)

CACHE_ENABLED: bool = config("CACHE_ENABLED", cast=bool, default=True)

MAX_ISO_DATE_BACKWARD_DIFF: int = config("MAX_ISO_DATE_BACKWARD_DIFF", cast=int, default=180)
MAX_ROLLING_PERIOD: int = config("MAX_ROLLING_PERIOD", cast=int, default=1000)
