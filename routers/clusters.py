"""Router for the Clusters API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from core.client import DatabricksClient, get_databricks_client
from schemas.clusters import (
    ClusterIdRequest,
    CreateClusterRequest,
    EditClusterRequest,
    PermanentDeleteClusterRequest,
    ResizeClusterRequest,
)
from services.cluster_service import ClusterService

router = APIRouter(prefix="/api/v1/clusters", tags=["Clusters"])


def get_cluster_service(client: DatabricksClient = Depends(get_databricks_client)) -> ClusterService:
    return ClusterService(client)


@router.get("", summary="List clusters", description="List all clusters in the workspace.")
async def list_clusters(service: ClusterService = Depends(get_cluster_service)) -> dict[str, Any]:
    return await service.list_clusters()


@router.post("/create", summary="Create cluster", description="Create a new cluster.")
async def create_cluster(
    body: CreateClusterRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.create_cluster(body.model_dump(exclude_none=True))


@router.get("/{cluster_id}", summary="Get cluster", description="Get cluster details and current state.")
async def get_cluster(
    cluster_id: str, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.get_cluster(cluster_id)


@router.post("/start", summary="Start cluster", description="Start a terminated cluster.")
async def start_cluster(
    body: ClusterIdRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.start_cluster(body.cluster_id)


@router.post("/restart", summary="Restart cluster", description="Restart a running cluster.")
async def restart_cluster(
    body: ClusterIdRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.restart_cluster(body.cluster_id)


@router.post(
    "/resize", summary="Resize cluster", description="Change the number of workers (fixed or autoscale)."
)
async def resize_cluster(
    body: ResizeClusterRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    autoscale = body.autoscale.model_dump() if body.autoscale else None
    return await service.resize_cluster(body.cluster_id, body.num_workers, autoscale)


@router.post("/edit", summary="Edit cluster", description="Edit an existing cluster's configuration.")
async def edit_cluster(
    body: EditClusterRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.edit_cluster(body.model_dump(exclude_none=True))


@router.post("/terminate", summary="Terminate cluster", description="Terminate (stop) a running cluster.")
async def terminate_cluster(
    body: ClusterIdRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.terminate_cluster(body.cluster_id)


@router.post(
    "/permanent-delete",
    summary="Permanently delete cluster",
    description="Permanently delete a cluster; cannot be undone.",
)
async def permanent_delete_cluster(
    body: PermanentDeleteClusterRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.permanent_delete_cluster(body.cluster_id)


@router.post("/pin", summary="Pin cluster", description="Pin a cluster so it's exempt from auto-deletion.")
async def pin_cluster(
    body: ClusterIdRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.pin_cluster(body.cluster_id)


@router.post("/unpin", summary="Unpin cluster", description="Unpin a previously pinned cluster.")
async def unpin_cluster(
    body: ClusterIdRequest, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.unpin_cluster(body.cluster_id)


@router.get(
    "/meta/node-types", summary="List node types", description="List available VM node types for clusters."
)
async def list_node_types(service: ClusterService = Depends(get_cluster_service)) -> dict[str, Any]:
    return await service.list_node_types()


@router.get(
    "/meta/spark-versions",
    summary="List Spark versions",
    description="List available Databricks Runtime versions.",
)
async def list_spark_versions(service: ClusterService = Depends(get_cluster_service)) -> dict[str, Any]:
    return await service.list_spark_versions()


@router.get(
    "/{cluster_id}/events",
    summary="Get cluster events",
    description="List recent lifecycle events for a cluster.",
)
async def get_cluster_events(
    cluster_id: str, service: ClusterService = Depends(get_cluster_service)
) -> dict[str, Any]:
    return await service.get_cluster_events(cluster_id)
