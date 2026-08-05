"""Router for monitoring: metrics, logs, cluster/job health, connector info."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.core.config import Settings, get_settings
from databricks_connector.services.monitoring_service import MonitoringService

router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])


def get_monitoring_service(
    client: DatabricksClient = Depends(get_databricks_client),
    settings: Settings = Depends(get_settings),
) -> MonitoringService:
    return MonitoringService(client, settings)


@router.get(
    "/metrics/clusters", summary="Cluster metrics summary", description="Aggregate cluster counts by state."
)
async def cluster_metrics(service: MonitoringService = Depends(get_monitoring_service)) -> dict[str, Any]:
    return await service.cluster_metrics_summary()


@router.get("/metrics/jobs", summary="Job metrics summary", description="Aggregate job counts.")
async def job_metrics(service: MonitoringService = Depends(get_monitoring_service)) -> dict[str, Any]:
    return await service.job_metrics_summary()


@router.get(
    "/health/cluster/{cluster_id}", summary="Cluster health", description="Health check for a single cluster."
)
async def cluster_health(
    cluster_id: str, service: MonitoringService = Depends(get_monitoring_service)
) -> dict[str, Any]:
    return await service.cluster_health(cluster_id)


@router.get(
    "/health/job/{job_id}",
    summary="Job health",
    description="Health check based on recent run outcomes for a job.",
)
async def job_health(
    job_id: int, service: MonitoringService = Depends(get_monitoring_service)
) -> dict[str, Any]:
    return await service.job_health(job_id)


@router.get(
    "/connector/info",
    summary="Connector version/info",
    description="Connector name, version, environment, and uptime.",
)
async def connector_info(service: MonitoringService = Depends(get_monitoring_service)) -> dict[str, Any]:
    return service.connector_info()


@router.get(
    "/connector/config",
    summary="Connector configuration",
    description="Non-sensitive connector configuration snapshot.",
)
async def connector_config(service: MonitoringService = Depends(get_monitoring_service)) -> dict[str, Any]:
    return service.connector_configuration()
