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

from uvicorn.workers import UvicornWorker


class ImmuniUvicornWorker(UvicornWorker):
    """
    Custom worker setting lifespan=on to fail over exceptions raised within the worker startup.

    For instance, without this, an exception triggered during the managers initialization is
    never caught.

    NOTE: This lifespan option cannot be passed through the command line of gunicorn since the
     latter does not support it.
    """

    CONFIG_KWARGS = dict(lifespan="on")

