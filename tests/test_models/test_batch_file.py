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

import base64
import random
from datetime import datetime, timedelta
from typing import List

import pytest
from freezegun import freeze_time
from mongoengine import get_db

from immuni_common.models.enums import TransmissionRiskLevel
from immuni_common.models.mongoengine.batch_file import BatchFile
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey


def generate_random_key_data(size_bytes: int = 16) -> str:
    return base64.b64encode(
        bytes(bytearray(random.getrandbits(8) for _ in range(size_bytes)))
    ).decode("utf-8")


@pytest.fixture
def batch_files() -> List[BatchFile]:
    num_batches = 10
    start_datetime = datetime.utcnow() - timedelta(days=num_batches - 1)
    batches = []
    for i in range(num_batches):
        with freeze_time(start_datetime + timedelta(days=i)):
            batches.append(
                BatchFile(
                    index=i + 1,
                    keys=[
                        TemporaryExposureKey(
                            key_data=generate_random_key_data(),
                            transmission_risk_level=TransmissionRiskLevel.highest,
                            rolling_start_number=int(
                                datetime.utcnow().timestamp()
                                / timedelta(minutes=10).total_seconds()
                            ),
                            rolling_period=144,
                        )
                    ],
                    period_start=datetime.utcnow() - timedelta(days=1),
                    period_end=datetime.utcnow(),
                    sub_batch_index=1,
                    sub_batch_count=1,
                ).save()
            )
    return batches


def test_get_latest_info(batch_files: List[BatchFile]) -> None:
    info = BatchFile.get_latest_info()
    assert info
    last_period, last_index = info

    assert (last_period - datetime.utcnow()).total_seconds() < 1
    assert last_index == 10


def test_info_empty() -> None:
    assert BatchFile.get_latest_info() is None


def test_from_index(batch_files: List[BatchFile]) -> None:
    assert BatchFile.from_index(1) == batch_files[0]


def test_delete_old_batches(batch_files: List[BatchFile]) -> None:
    BatchFile.delete_older_than(datetime.utcnow() - timedelta(days=8, seconds=1))
    assert BatchFile.objects.count() == 9


def test_oldest_newest_batches(batch_files: List[BatchFile]) -> None:
    assert BatchFile.get_oldest_and_newest_indexes(days=4) == {
        "oldest": 7,
        "newest": 10,
    }


def test_indexes(batch_files: List[BatchFile]) -> None:
    explain = get_db().command(
        "aggregate",
        BatchFile._meta["collection"],
        pipeline=BatchFile._get_oldest_and_newest_indexes_pipeline(2),
        explain=True,
    )

    assert (
        explain["stages"][0]["$cursor"]["queryPlanner"]["winningPlan"]["inputStage"]["stage"]
        == "IXSCAN"
    )
    # sort should not be executed
    assert len(explain["stages"]) == 3
