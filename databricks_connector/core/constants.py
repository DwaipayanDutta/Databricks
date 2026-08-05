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
CONNECTOR_VERSION = "1.0.0"
