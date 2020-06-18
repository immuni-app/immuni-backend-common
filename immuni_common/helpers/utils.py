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
import pkgutil
import random
from types import ModuleType
from typing import Any, Dict, List, NamedTuple


def modules_in_package(package: ModuleType) -> List[str]:
    """
    Retrieve the list of modules within a package, recursively.

    :param package: the starting point package for retrieval of modules.
    :return: the list of modules within the given package.
    """

    def _modules_in_package(package_dir: str, package_name: str) -> List[str]:
        modules = list()
        for mod in pkgutil.walk_packages([package_dir], prefix=f"{package_name}."):
            sub_module = mod.name
            if mod.ispkg:
                modules.extend(
                    _modules_in_package(os.path.join(mod.module_finder.path, mod.name), sub_module)
                )
            else:
                modules.append(sub_module)
        return modules

    return _modules_in_package(os.path.dirname(package.__file__), package.__name__)


def dense_dict(dictionary: Dict) -> Dict:
    """
    Return a dictionary ignoring keys with None values, recursively.

    :param dictionary: the input dictionary, possibly containing None values.
    :return: a new dictionary without keys having a None value.
    """
    return {
        k: dense_dict(v) if isinstance(v, dict) else v
        for k, v in dictionary.items()
        if v is not None
    }


# Note: This could be a Generic[T] with T as TypeVar. That would allow
#  us to define a WeightedPair[str] and have the weighted_random
#  return a valid typed str when used, but generic NamedTuples are not yet
#  supported by mypy:
#  https://github.com/python/mypy/issues/685
class WeightedPair(NamedTuple):
    """
    Simple NamedTuple that allows us to describe
    weighted key/value pairs for weighted random.
    """

    weight: int
    payload: Any


def weighted_random(pairs: List[WeightedPair]) -> Any:
    """
    Returns one of the values in the WeightedPair list randomly based on the
    weights defined in the given WeightedPair list.

    :param pairs: The list of WeightedPair to pick the random value from.
    """
    return random.choices(
        population=tuple(p.payload for p in pairs), weights=tuple(p.weight for p in pairs), k=1,
    )[0]
