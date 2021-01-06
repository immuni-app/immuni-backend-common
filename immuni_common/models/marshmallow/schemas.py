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

import sys
from typing import Any, Dict

from marshmallow import Schema, fields, post_load
from marshmallow.validate import Range

from immuni_common.core import config
from immuni_common.models.dataclasses import ExposureDetectionSummary, ExposureInfo, OtpData
from immuni_common.models.enums import TransmissionRiskLevel
from immuni_common.models.marshmallow.fields import (
    AttenuationDurations,
    Base64String,
    EnumField,
    IsoDate,
    RiskScore,
)
from immuni_common.models.mongoengine.temporary_exposure_key import TemporaryExposureKey


class OtpDataSchema(Schema):
    """
    Validate and deserialize the raw data into the corresponding OtpData object.
    """
    id_transaction = fields.String(required=False, missing=None)
    symptoms_started_on = IsoDate()

    @post_load
    def create_otp_data(self, data: Dict, **kwargs: Any) -> OtpData:  # pylint: disable=no-self-use
        """
        Return the OtpData object associated with the deserialized data.

        :param data: the deserialized data.
        :param kwargs: the additional unused arguments coming from the decorator.
        :return: the OtpData object associated with the given data.
        """
        return OtpData(**data)


class TemporaryExposureKeySchema(Schema):
    """
    Validate and deserialize the raw data into the corresponding TemporaryExposureKey object.
    """

    key_data = Base64String(required=True, length=16)
    rolling_start_number = fields.Integer(required=True, validate=Range(min=0, max=sys.maxsize))
    rolling_period = fields.Integer(
        required=False, validate=Range(min=0, max=config.MAX_ROLLING_PERIOD)
    )

    @post_load
    def create_tek(  # pylint: disable=no-self-use
            self, data: Dict, **kwargs: Any
    ) -> TemporaryExposureKey:
        """
        Return the TemporaryExposureKey object associated with the deserialized data.

        :param data: the deserialized data.
        :param kwargs: the additional unused arguments coming from the decorator.
        :return: the TemporaryExposureKey object associated with the given data.
        """
        return TemporaryExposureKey(**data)


class ExposureInfoSchema(Schema):
    """
    Validate and deserialize the raw data into the corresponding ExposureInfo object.
    """

    date = IsoDate()
    duration = fields.Integer(required=True, validate=Range(min=0, max=sys.maxsize))
    attenuation_value = fields.Integer(required=True, validate=Range(min=0, max=sys.maxsize))
    attenuation_durations = AttenuationDurations()
    transmission_risk_level = EnumField(TransmissionRiskLevel)
    total_risk_score = RiskScore()

    @post_load
    def create_exposure_info(  # pylint: disable=no-self-use
            self, data: Dict, **kwargs: Any
    ) -> ExposureInfo:
        """
        Return the ExposureInfo object associated with the deserialized data.

        :param data: the deserialized data.
        :param kwargs: the additional unused arguments coming from the decorator.
        :return: the ExposureInfo object associated with the given data.
        """
        return ExposureInfo(**data)


class ExposureDetectionSummarySchema(Schema):
    """
    Validate and deserialize the raw data into the corresponding ExposureDetectionSummary object.
    """

    date = IsoDate()
    matched_key_count = fields.Integer(required=True, validate=Range(min=0, max=sys.maxsize))
    days_since_last_exposure = fields.Integer(required=True, validate=Range(min=0, max=sys.maxsize))
    attenuation_durations = AttenuationDurations()
    maximum_risk_score = RiskScore()
    exposure_info = fields.Nested(ExposureInfoSchema, many=True)

    @post_load
    def create_exposure_detection_summary(  # pylint: disable=no-self-use
        self, data: Dict, **kwargs: Any
    ) -> ExposureDetectionSummary:
        """
        Return the ExposureDetectionSummary object associated with the deserialized data.

        :param data: the deserialized data.
        :param kwargs: the additional unused arguments coming from the decorator.
        :return: the ExposureDetectionSummary object associated with the given data.
        """
        return ExposureDetectionSummary(**data)
