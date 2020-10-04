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

from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

from mongoengine import EmbeddedDocument, IntField, StringField, ListField

from immuni_common.helpers.sanic import Serializable
from immuni_common.models.enums import TransmissionRiskLevel
from immuni_common.models.mongoengine.enum_field import EnumField


class TemporaryExposureKey(EmbeddedDocument, Serializable):
    """
    The Temporary Exposure Key (TEK) model.
    """

    key_data: str = StringField(required=True, description="")
    transmission_risk_level: Enum = EnumField(TransmissionRiskLevel)
    rolling_start_number: int = IntField(required=True)
    rolling_period: int = IntField(required=False)
    country_of_interest: str = ListField(required=False)

    @property
    def created_at(self) -> datetime:
        """
        Retrieve the creation datetime of the key.
        NOTE: The "rolling period" is a timestamp divided by 10 minutes.
          Multiplying it back give the creation timestamp.

        :return: the datetime when the key was created.
        """
        return datetime.utcfromtimestamp(
            self.rolling_start_number * timedelta(minutes=10).total_seconds()
        )

    @property
    def expires_at(self) -> datetime:
        """
        The datetime when the current key stops being used by the client to generate RPIs.

        :return: the datetime the current key expires.
        """
        return self.created_at + timedelta(minutes=10 * self.rolling_period)

    def serialize(self) -> Dict[str, Any]:
        """
        Serialization method (overrides the Serializable subclass method).

        :return: the serialized TemporaryExposureKey.
        """
        return dict(
            key_data=self.key_data,
            transmission_risk_level=self.transmission_risk_level.value,  # pylint: disable=no-member
            rolling_start_number=self.rolling_start_number,
            country_of_interest=self.country_of_interest
        )
