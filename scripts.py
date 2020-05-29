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
import os
import sys
from pathlib import Path
from subprocess import call
from typing import Tuple

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
    parser.add_argument(
        "--ci", help="Use the CI mode, by not applying changes.", action="store_true"
    )
    return parser.parse_args()


def _get_immuni_common_root() -> Path:
    return Path(__file__).parent.absolute()


def _get_immuni_common_pyproject_toml() -> str:
    return str(_get_immuni_common_root() / "pyproject.toml")


def _isort_command(is_ci: bool) -> Tuple[str, ...]:
    command = (
        "isort",
        ".",
        "--recursive",
        "--atomic",
        "--settings-path",
        str(_get_immuni_common_root()),
    )
    return (*command, "--diff") if is_ci else command


def _black_command(is_ci: bool) -> Tuple[str, ...]:
    command = ("black", ".", "--config", _get_immuni_common_pyproject_toml())
    return (*command, "--check") if is_ci else command


def _mypy_command() -> Tuple[str, ...]:
    return "mypy", ".", "--config", str(_get_immuni_common_root() / "mypy.ini")


def _flake8_command() -> Tuple[str, ...]:
    return "flake8", ".", "--config", str(_get_immuni_common_root() / ".flake8")


def _bandit_command(service_dirname: str) -> Tuple[str, ...]:
    return "bandit", "--recursive", service_dirname


def _pylint_command(service_dirname: str, is_ci: bool) -> Tuple[str, ...]:
    command = ("pylint", service_dirname, "--rcfile", _get_immuni_common_pyproject_toml())
    # TODOs and FIXMEs should not mark the job as failed in CI, yet they should be visible while
    # developing.
    return (*command, "--disable=fixme") if is_ci else command


def _run_command(command: Tuple[str, ...]) -> int:
    _LOGGER.info(f"Running: {' '.join(command)}")
    exit_code = call(command)
    _LOGGER.info(f"Done: {command[0]} exit code is {exit_code}")
    return exit_code


def checks() -> None:
    """
    Run different linters and checks while keeping all configuration within the common repository.
    NOTE: The commands run sequentially to avoid messing up the output in case multiple linters
      produce warnings.
    """
    arguments = _parse_args()
    any_failure = False

    commands = (
        _isort_command(arguments.ci),
        _black_command(arguments.ci),
        _mypy_command(),
        _flake8_command(),
        _bandit_command(arguments.service_dirname),
        _pylint_command(arguments.service_dirname, arguments.ci),
    )

    for command in commands:
        exit_code = _run_command(command)
        any_failure = any_failure or exit_code != os.EX_OK

    if any_failure:
        _LOGGER.error("At least one check failed. Please fix them before proceeding.")
        sys.exit(os.EX_SOFTWARE)
