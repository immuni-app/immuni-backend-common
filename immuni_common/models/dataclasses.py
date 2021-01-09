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

from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from immuni_common.models.enums import TransmissionRiskLevel


@dataclass(frozen=True)
class ExposureInfo:
    """
    Exposure Info provided by the clients.
    """

    date: date
    duration: int
    attenuation_value: int
    attenuation_durations: List[int]
    transmission_risk_level: TransmissionRiskLevel
    total_risk_score: int


@dataclass(frozen=True)
class ExposureDetectionSummary:
    """
    Exposure Detection Summary provided by the clients.
    """

    date: date
    matched_key_count: int
    days_since_last_exposure: int
    attenuation_durations: List[int]
    maximum_risk_score: int
    exposure_info: ExposureInfo


@dataclass(frozen=True)
class OtpData:
    """
    Information associated with an OTP received from the health information system (HIS).
    """

    id_test_verification: Optional[str]
    symptoms_started_on: date
