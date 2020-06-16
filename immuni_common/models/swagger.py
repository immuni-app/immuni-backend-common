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

from sanic_openapi import doc

from immuni_common.models.enums import TransmissionRiskLevel


class HeaderImmuniContentTypeJson(doc.String):
    """
    Documentation class for the Immuni-Dummy-Data header.
    """

    def __init__(self) -> None:
        super().__init__(name="Content-Type", description="application/json; charset=utf-8")


class HeaderImmuniDummyData(doc.Boolean):
    """
    Documentation class for the Immuni-Dummy-Data header.
    """

    DATA_KEY = "Immuni-Dummy-Data"

    def __init__(self) -> None:
        super().__init__(
            name=self.DATA_KEY,
            description="Whether the current request is dummy. Dummy requests are ignored.",
            choices=("true", "false"),
        )


class UploadedTemporaryExposureKey:
    """
    Documentation class for Uploaded Temporary Exposure Key.
    """

    key_data = doc.String("The base64-encoded version of the 16-bytes key data.", required=True)
    rolling_start_number = doc.Integer(
        "The start number of the key's rolling period: timestamp / 600.", required=True
    )
    rolling_period = doc.Integer(
        "The key's validity period in rolling periods of 10 minutes. "
        "The field is optional, and defaults to 144."
    )


class TemporaryExposureKey(UploadedTemporaryExposureKey):
    """
    Documentation class for Temporary Exposure Key.
    """

    transmission_risk_level = doc.Integer(
        "The transmission risk level, computed based on when the user started having symptoms.",
        required=True,
        choices=tuple(level for level in TransmissionRiskLevel),
    )
