"""Router for Delta Live Tables (DLT) pipelines."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.schemas.dlt import (
    CreatePipelineRequest,
    PipelineIdRequest,
    StartPipelineUpdateRequest,
    UpdatePipelineRequest,
)
from databricks_connector.services.dlt_service import DltService

router = APIRouter(prefix="/api/v1/dlt", tags=["Delta Live Tables"])


def get_dlt_service(client: DatabricksClient = Depends(get_databricks_client)) -> DltService:
    return DltService(client)


@router.post("/pipelines", summary="Create pipeline", description="Create a new DLT pipeline.")
async def create_pipeline(
    body: CreatePipelineRequest, service: DltService = Depends(get_dlt_service)
) -> dict[str, Any]:
    return await service.create_pipeline(body.model_dump(exclude_none=True))


@router.put(
    "/pipelines/{pipeline_id}",
    summary="Update pipeline",
    description="Update an existing DLT pipeline's settings.",
)
async def update_pipeline(
    pipeline_id: str, body: UpdatePipelineRequest, service: DltService = Depends(get_dlt_service)
) -> dict[str, Any]:
    settings = body.model_dump(exclude_none=True, exclude={"pipeline_id"})
    return await service.update_pipeline(pipeline_id, settings)


@router.delete("/pipelines/{pipeline_id}", summary="Delete pipeline", description="Delete a DLT pipeline.")
async def delete_pipeline(pipeline_id: str, service: DltService = Depends(get_dlt_service)) -> dict[str, Any]:
    return await service.delete_pipeline(pipeline_id)


@router.post(
    "/pipelines/start",
    summary="Start pipeline update",
    description="Trigger a new pipeline update (optionally full refresh).",
)
async def start_pipeline(
    body: StartPipelineUpdateRequest, service: DltService = Depends(get_dlt_service)
) -> dict[str, Any]:
    return await service.start_update(body.pipeline_id, body.full_refresh)


@router.post("/pipelines/stop", summary="Stop pipeline", description="Stop a running DLT pipeline.")
async def stop_pipeline(
    body: PipelineIdRequest, service: DltService = Depends(get_dlt_service)
) -> dict[str, Any]:
    return await service.stop_pipeline(body.pipeline_id)


@router.get("/pipelines", summary="List pipelines", description="List DLT pipelines, optionally filtered.")
async def list_pipelines(
    max_results: int = Query(default=25, ge=1, le=100),
    filter: str | None = Query(default=None),
    page_token: str | None = Query(
        default=None, description="Token from a previous response's next_page_token."
    ),
    service: DltService = Depends(get_dlt_service),
) -> dict[str, Any]:
    return await service.list_pipelines(max_results, filter, page_token)


@router.get(
    "/pipelines/{pipeline_id}", summary="Get pipeline", description="Get details for a single DLT pipeline."
)
async def get_pipeline(pipeline_id: str, service: DltService = Depends(get_dlt_service)) -> dict[str, Any]:
    return await service.get_pipeline(pipeline_id)


@router.get(
    "/pipelines/{pipeline_id}/events",
    summary="List pipeline events",
    description="List recent events for a DLT pipeline.",
)
async def list_pipeline_events(
    pipeline_id: str,
    max_results: int = Query(default=25, ge=1, le=100),
    page_token: str | None = Query(
        default=None, description="Token from a previous response's next_page_token."
    ),
    service: DltService = Depends(get_dlt_service),
) -> dict[str, Any]:
    return await service.list_pipeline_events(pipeline_id, max_results, page_token)
