"""Constants used across the connector."""

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 0.5
DEFAULT_CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 30.0

RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

HEADER_REQUEST_ID = "X-Request-ID"
HEADER_CORRELATION_ID = "X-Correlation-ID"

MASKED_KEYS = {
    "authorization",
    "token",
    "password",
    "secret",
    "api_key",
    "apikey",
    "access_token",
    "client_secret",
}

CONNECTOR_NAME = "databricks-connector"
# Kept in lockstep with pyproject.toml's [project].version, setup.py's
# version=, and databricks_connector/__init__.py's __version__ -- these had
# drifted (this constant alone was still "1.0.0" while every other version
# marker in the repo said "1.0.2"), so `/health`, `/api/v1/monitoring/connector/info`,
# and the OpenAPI schema's `info.version` disagreed with the installed
# package's own version.
CONNECTOR_VERSION = "1.1.0"
