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

from http import HTTPStatus


class ImmuniException(Exception):
    """
    Base exception for any exception thrown within this project.
    """


# 1000-1099: immuni-common


class ApiException(ImmuniException):
    """
    Base exception for any API unexpected behaviour.
    """

    status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    error_message = "An unknown error occurred."
    error_code = 1000


class SchemaValidationException(ApiException):
    """
    Raised when the request is not compliant with the defined schema.
    """

    status_code = HTTPStatus.BAD_REQUEST
    error_message = "Request not compliant with the defined schema."
    error_code = 1001


class DgcNotFoundException(ApiException):
    """
    Raised when there is no DGC found, at all.
    """

    status_code = HTTPStatus.NOT_FOUND
    error_message = "No DGC found."
    error_code = 1102


# 1100-1199: immuni-exposure-ingestion


class UnauthorizedOtpException(ApiException):
    """
    Raised when a user is attempting to upload data with an unauthorized OTP.
    """

    status_code = HTTPStatus.UNAUTHORIZED
    error_message = "Unauthorized OTP."
    error_code = 1101


# 1200-1299: immuni-analytics
# 1300-1399: immuni-exposure-reporting


class BatchNotFoundException(ApiException):
    """
    Raised when the requested batch is not found.
    """

    status_code = HTTPStatus.NOT_FOUND
    error_message = "Batch not found."
    error_code = 1300


class NoBatchesException(ApiException):
    """
    Raised when there are no batches, at all.
    """

    status_code = HTTPStatus.NOT_FOUND
    error_message = "No batches found."
    error_code = 1301


# 1400-1499: immuni-otp


class OtpCollisionException(ApiException):
    """
    Raised when attempting to (re-)authorize an OTP which is already in the database.
    """

    status_code = HTTPStatus.CONFLICT
    error_message = "OTP already authorized."
    error_code = 1400


# 1500-1599: immuni-app-configuration
