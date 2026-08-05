"""Exception hierarchy for the Databricks connector.

Every exception raised while talking to Databricks (or while validating
input before doing so) should be an instance of DatabricksConnectorError so
that the exception middleware can translate it into a consistent JSON error
response.
"""

from __future__ import annotations

from typing import Any


class DatabricksConnectorError(Exception):
    """Base class for all connector-raised errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(DatabricksConnectorError):
    status_code = 500
    error_code = "configuration_error"


class AuthenticationError(DatabricksConnectorError):
    status_code = 401
    error_code = "authentication_error"


class AuthorizationError(DatabricksConnectorError):
    status_code = 403
    error_code = "authorization_error"


class NotFoundError(DatabricksConnectorError):
    status_code = 404
    error_code = "not_found"


class ConflictError(DatabricksConnectorError):
    status_code = 409
    error_code = "conflict"


class ValidationAPIError(DatabricksConnectorError):
    status_code = 400
    error_code = "validation_error"


class RateLimitError(DatabricksConnectorError):
    status_code = 429
    error_code = "rate_limited"


class PayloadTooLargeError(DatabricksConnectorError):
    status_code = 413
    error_code = "payload_too_large"


class DatabricksServerError(DatabricksConnectorError):
    status_code = 502
    error_code = "databricks_server_error"


class ServiceUnavailableError(DatabricksConnectorError):
    status_code = 503
    error_code = "service_unavailable"


class CircuitBreakerOpenError(DatabricksConnectorError):
    status_code = 503
    error_code = "circuit_breaker_open"


class TimeoutErrorConnector(DatabricksConnectorError):
    status_code = 504
    error_code = "timeout"


# Every status code Databricks is documented to return from its REST APIs
# is mapped explicitly here so the connector's error body always carries a
# meaningful `error` code alongside the HTTP status -- never falls through
# to a misleading generic "internal_error" for a well-known client/server
# error status.
STATUS_CODE_EXCEPTION_MAP: dict[int, type[DatabricksConnectorError]] = {
    400: ValidationAPIError,
    401: AuthenticationError,
    403: AuthorizationError,
    404: NotFoundError,
    409: ConflictError,
    429: RateLimitError,
    500: DatabricksServerError,
    501: DatabricksServerError,
    502: DatabricksServerError,
    503: ServiceUnavailableError,
    504: TimeoutErrorConnector,
}


def exception_for_status(
    status_code: int, message: str, details: dict[str, Any] | None = None
) -> DatabricksConnectorError:
    """Map an HTTP status code returned by Databricks to a connector exception.

    Falls back to the generic `DatabricksConnectorError` (reported as HTTP
    500 / `internal_error`) only for status codes Databricks isn't
    documented to return; every mapped code above keeps the exception's
    `error_code` consistent with its `status_code`.
    """
    exc_cls = STATUS_CODE_EXCEPTION_MAP.get(status_code, DatabricksConnectorError)
    return exc_cls(message, status_code=status_code, details=details)
