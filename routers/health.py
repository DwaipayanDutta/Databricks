"""Health, readiness, and liveness endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.circuit_breaker import get_circuit_breaker
from core.client import DatabricksClient, get_databricks_client
from core.config import Settings, get_settings
from core.constants import CONNECTOR_VERSION
from core.exceptions import DatabricksConnectorError
from schemas.common import HealthStatus, ReadinessStatus

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Basic health check",
    description="Returns process-level health. Does not call out to Databricks.",
)
async def health(settings: Settings = Depends(get_settings)) -> HealthStatus:
    return HealthStatus(status="healthy", version=CONNECTOR_VERSION, environment=settings.app_env)


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="Readiness check",
    description="Verifies the connector can reach Databricks and that the circuit breaker is closed.",
)
async def ready(
    client: DatabricksClient = Depends(get_databricks_client),
    settings: Settings = Depends(get_settings),
) -> ReadinessStatus:
    dependencies: dict[str, str] = {}

    breaker = get_circuit_breaker("databricks")
    dependencies["circuit_breaker"] = breaker.state.value

    try:
        await client.get("/api/2.0/clusters/spark-versions")
        dependencies["databricks_api"] = "reachable"
        status = "ready"
    except DatabricksConnectorError as exc:
        dependencies["databricks_api"] = f"unreachable: {exc.error_code}"
        status = "not_ready"
    except Exception:  # noqa: BLE001
        dependencies["databricks_api"] = "unreachable"
        status = "not_ready"

    return ReadinessStatus(status=status, dependencies=dependencies)


@router.get(
    "/live",
    summary="Liveness check",
    description="Simple liveness probe for orchestrators (Kubernetes, etc.).",
)
async def live() -> dict[str, str]:
    return {"status": "alive"}
