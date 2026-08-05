"""Prometheus metrics endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Response

from databricks_connector.core.circuit_breaker import get_circuit_breaker
from databricks_connector.core.metrics import record_circuit_breaker_state, render_metrics

router = APIRouter(tags=["Metrics"])


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description=(
        "Exposes connector HTTP traffic, Databricks API call, and circuit "
        "breaker metrics in Prometheus text exposition format."
    ),
    response_class=Response,
)
async def metrics() -> Response:
    # Sample the circuit breaker's current state at scrape time rather than
    # push-updating the gauge from core.circuit_breaker (keeps that module
    # free of a hard dependency on the metrics/Prometheus stack).
    breaker = get_circuit_breaker("databricks")
    record_circuit_breaker_state(name="databricks", state=breaker.state.value)

    body, content_type = render_metrics()
    return Response(content=body, media_type=content_type)
