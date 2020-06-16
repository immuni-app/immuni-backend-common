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
from typing import Any


class BaseManagers:
    """
    Superclass for the microservice managers, defining the interface required to create a Sanic app
    using the common utilities (i.e., create_app).
    The interface defaults to `pass` since it may not be required for all microservices to
    implement them all.
    """

    async def initialize(self, **kwargs: Any) -> None:
        """
        Initialize managers on demand.
        To be overridden by subclasses, if needed.

        :param kwargs: the additional keyword arguments the subclasses may need.
        """

    async def teardown(self, **kwargs: Any) -> None:
        """
        Perform teardown actions (e.g., close open connections).
        To be overridden by subclasses, if needed.

        :param kwargs: the additional keyword arguments the subclasses may need.
        """
