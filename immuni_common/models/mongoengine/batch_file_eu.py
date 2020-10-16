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

import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from bson import ObjectId
from mongoengine import (
    BinaryField,
    DateTimeField,
    Document,
    EmbeddedDocumentListField,
    IntField,
    StringField,
)

from immuni_common.core.exceptions import NoBatchesException
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey

_LOGGER = logging.getLogger(__name__)


class BatchFileEu(Document):
    """
    Document to wrap a batch of EU-TEKs .
    """

    index: int = IntField(min_value=0, required=True)
    keys: List[TemporaryExposureKey] = EmbeddedDocumentListField(
        TemporaryExposureKey, required=True
    )
    period_start: datetime = DateTimeField(required=True)
    period_end: datetime = DateTimeField(required=True)

    sub_batch_index: int = IntField()
    sub_batch_count: int = IntField()

    origin: str = StringField(required=True)

    client_content: bytes = BinaryField()

    meta = {
        "indexes": [
            {"fields": ("origin", "index"), "unique": True},
            {"fields": ("origin", "period_start")},
        ]
    }

    @classmethod
    def from_index(cls, country: str, index: int) -> BatchFileEu:
        """
        Fetch a single BatchFile from the database given its index.

        :param country: the country of interest.
        :param index: the index of the BatchFile to fetch.
        :return: the BatchFile, if any.
        :raises: DoesNotExist if the BatchFile associated with the given index does not exist.
        """
        return BatchFileEu.objects.filter(origin=country).get(index=index)

    @classmethod
    def get_latest_info(cls, country: str) -> Optional[Tuple[datetime, int]]:
        """
        Fetch the most recent BatchFile and return its period_end and index.

        :param country: the country of interest.
        :return: the period_end and index tuple if there is at least a BatchFile, None otherwise.
        """
        last_batch = (
            cls.objects.filter(origin=country)
            .order_by("-index")
            .only("period_end", "index")
            .first()
        )
        if not last_batch:
            return None
        return last_batch.period_end, last_batch.index

    @classmethod
    def delete_older_than(cls, datetime_: datetime) -> int:
        """
        Delete all batches older than the given datetime.

        :param datetime_: the datetime before which the batches are to be deleted.
        :return: the number of batches that were deleted.
        """
        return cls.objects.filter(id__lte=ObjectId.from_datetime(datetime_)).delete()

    @staticmethod
    def _get_oldest_and_newest_indexes_pipeline(days: int) -> List[Dict]:
        """
        Return the aggregation pipeline for retrieving the oldest and newest indexes.

        :param days: the number of days since when to look for relevant BatchFiles.
        :return: the list of aggregation stages to perform the query.
        """
        return [
            {
                "$match": {
                    "period_start": {
                        "$gt": datetime.combine(date.today(), datetime.min.time())
                        - timedelta(days=days)
                    }
                }
            },
            {"$sort": {"index": 1}},
            {
                "$group": {
                    "_id": None,
                    "oldest": {"$first": "$index"},
                    "newest": {"$last": "$index"},
                }
            },
            {"$project": {"_id": 0, "oldest": 1, "newest": 1}},
        ]

    @classmethod
    def get_oldest_and_newest_indexes(cls, country: str, days: int) -> Dict[str, int]:
        """
        Fetch the oldest and newest indexes of the last N days.

        :param days: the number of days since when to look for relevant BatchFiles.
        :param country: the country of interest.
        :return: the dictionary with the oldest and newest indexes of the last N days.
        :raises: NoBatchesException if there are no batches in the database.
        """
        try:
            result = next(
                cls.objects.filter(origin=country).aggregate(
                    *cls._get_oldest_and_newest_indexes_pipeline(days)
                )
            )
            result["oldest"] = int(result["oldest"])
            result["newest"] = int(result["newest"])
        except StopIteration:
            raise NoBatchesException()
        return result
