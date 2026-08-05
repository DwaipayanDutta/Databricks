"""Health, readiness, and liveness endpoints.

Thin by design: all readiness decision logic lives in HealthService.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.client import DatabricksClient, get_databricks_client
from core.config import Settings, get_settings
from core.constants import CONNECTOR_VERSION
from schemas.common import HealthStatus, ReadinessStatus
from services.health_service import HealthService

router = APIRouter(tags=["Health"])


def get_health_service(client: DatabricksClient = Depends(get_databricks_client)) -> HealthService:
    return HealthService(client)


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
async def ready(service: HealthService = Depends(get_health_service)) -> ReadinessStatus:
    result = await service.check_readiness()
    return ReadinessStatus(**result)


@router.get(
    "/live",
    summary="Liveness check",
    description="Simple liveness probe for orchestrators (Kubernetes, etc.).",
)
async def live() -> dict[str, str]:
    return {"status": "alive"}
