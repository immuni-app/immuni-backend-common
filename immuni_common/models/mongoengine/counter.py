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

from __future__ import annotations

from typing import Dict, Optional

from mongoengine import Document, IntField, StringField
from pymongo import ReturnDocument

from immuni_common.core.exceptions import ImmuniException


class CounterNotFoundException(ImmuniException):
    """
    Triggered when trying to get the next value for a Counter, but the counter does not exist.
    """


class Counter(Document):
    """
    Collection to keep track of monotonically increasing counters.
    """

    id = StringField(primary_key=True, required=True)
    value: int = IntField(required=True)

    @staticmethod
    def _make_identifier(collection: str, field: str) -> str:
        return f"{collection}.{field}"

    @classmethod
    def create(cls, collection: str, field: str, start_value: Optional[int] = 0) -> Counter:
        return cls(id=cls._make_identifier(collection, field), value=start_value)

    @classmethod
    def get_next(cls, collection: str, field: str) -> int:
        identifier = cls._make_identifier(collection, field)
        pymongo_counter: Optional[Dict] = cls._get_collection().find_one_and_update(
            {"_id": identifier}, {"$inc": {"value": 1}}, return_document=ReturnDocument.AFTER,
        )
        if pymongo_counter is None:
            raise CounterNotFoundException(f"No counter with '{identifier}' identifier.")
        return pymongo_counter["value"]
