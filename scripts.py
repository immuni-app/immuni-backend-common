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

import argparse
import logging
from pathlib import Path
from subprocess import call

logging.basicConfig(format="[%(asctime)s][%(levelname)s] %(message)s", level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

_ALLOWED_SERVICE_DIRNAMES = {
    "immuni_common",
    "immuni_analytics",
    "immuni_app_configuration",
    "immuni_exposure_ingestion",
    "immuni_exposure_reporting",
    "immuni_otp",
}


def _validate_service_dirname(service_dirname: str) -> str:
    if service_dirname not in _ALLOWED_SERVICE_DIRNAMES:
        raise argparse.ArgumentTypeError(
            f"Invalid value '{service_dirname}' (allowed: {list(_ALLOWED_SERVICE_DIRNAMES)})."
        )
    return service_dirname


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run linter checks for the specified folder. "
        "It assumes the script runs from the parent of the specified folder."
        "The configurations being used reside within the common repository."
    )
    parser.add_argument(
        "service_dirname", help="The service directory name.", type=_validate_service_dirname
    )
    return parser.parse_args()


def _get_immuni_common_root() -> Path:
    return Path(__file__).parent.absolute()


def _get_immuni_common_pyproject_toml() -> str:
    return str(_get_immuni_common_root() / "pyproject.toml")


def _get_isort_settings_path() -> str:
    return str(_get_immuni_common_root())


def _get_black_configuration() -> str:
    return _get_immuni_common_pyproject_toml()


def _get_mypy_configuration() -> str:
    return str(_get_immuni_common_root() / "mypy.ini")


def _get_flake8_configuration() -> str:
    return str(_get_immuni_common_root() / ".flake8")


def _get_pylint_configuration() -> str:
    return _get_immuni_common_pyproject_toml()


def checks() -> None:
    """
    Run different linters and checks while keeping all configuration within the common repository.
    """
    arguments = _parse_args()

    commands = (
        ("isort", ".", "--recursive", "--atomic", "--settings-path", _get_isort_settings_path()),
        ("black", ".", "--config", _get_black_configuration()),
        ("mypy", ".", "--config", _get_mypy_configuration()),
        ("flake8", ".", "--config", _get_flake8_configuration()),
        ("bandit", "--recursive", arguments.service_dirname),
        ("pylint", arguments.service_dirname, "--rcfile", _get_pylint_configuration()),
    )
    for command in commands:
        logging.info(f"Running: {' '.join(command)}")
        call(command)
