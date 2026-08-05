"""Prometheus metrics for the connector.

Two families of metrics are tracked:
  * `connector_http_*`      -- traffic served *by* this connector's own API
  * `databricks_api_*`      -- calls this connector makes *to* Databricks

Kept as a standalone module (no dependency on `core.client` or
`core.middleware`) so both can import it without creating a cycle.
"""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

registry = CollectorRegistry()

HTTP_REQUEST_COUNT = Counter(
    "connector_http_requests_total",
    "Total HTTP requests served by the connector's own API.",
    ["method", "path", "status"],
    registry=registry,
)

HTTP_REQUEST_LATENCY = Histogram(
    "connector_http_request_duration_seconds",
    "Latency of HTTP requests served by the connector's own API.",
    ["method", "path"],
    registry=registry,
)

DATABRICKS_CALL_COUNT = Counter(
    "databricks_api_calls_total",
    "Total calls made to the Databricks REST API.",
    ["method", "path", "status"],
    registry=registry,
)

DATABRICKS_CALL_LATENCY = Histogram(
    "databricks_api_call_duration_seconds",
    "Latency of calls made to the Databricks REST API.",
    ["method", "path"],
    registry=registry,
)

CIRCUIT_BREAKER_STATE = Gauge(
    "databricks_circuit_breaker_state",
    "Circuit breaker state: 0=closed, 1=open, 2=half_open.",
    ["name"],
    registry=registry,
)

_CIRCUIT_STATE_VALUES = {"closed": 0, "open": 1, "half_open": 2}


def record_http_request(*, method: str, path: str, status_code: int, elapsed_ms: float) -> None:
    HTTP_REQUEST_COUNT.labels(method=method, path=path, status=str(status_code)).inc()
    HTTP_REQUEST_LATENCY.labels(method=method, path=path).observe(elapsed_ms / 1000.0)


def record_databricks_call(*, method: str, path: str, status_code: int, elapsed_ms: float) -> None:
    DATABRICKS_CALL_COUNT.labels(method=method, path=path, status=str(status_code)).inc()
    DATABRICKS_CALL_LATENCY.labels(method=method, path=path).observe(elapsed_ms / 1000.0)


def record_circuit_breaker_state(*, name: str, state: str) -> None:
    CIRCUIT_BREAKER_STATE.labels(name=name).set(_CIRCUIT_STATE_VALUES.get(state, -1))


def render_metrics() -> tuple[bytes, str]:
    """Return (body, content_type) for the `/metrics` endpoint."""
    return generate_latest(registry), CONTENT_TYPE_LATEST
