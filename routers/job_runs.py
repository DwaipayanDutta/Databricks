"""Router for Job Runs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.client import DatabricksClient, get_databricks_client
from schemas.jobs import WaitForRunRequest
from services.jobs_service import JobsService

router = APIRouter(prefix="/api/v1/job-runs", tags=["Job Runs"])


def get_jobs_service(client: DatabricksClient = Depends(get_databricks_client)) -> JobsService:
    return JobsService(client)


@router.get("", summary="List job runs", description="List job runs, optionally filtered by job_id.")
async def list_runs(
    job_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    active_only: bool = Query(default=False),
    service: JobsService = Depends(get_jobs_service),
) -> dict[str, Any]:
    return await service.list_runs(job_id=job_id, limit=limit, offset=offset, active_only=active_only)


@router.get("/{run_id}", summary="Get job run", description="Get details for a single job run.")
async def get_run(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.get_run(run_id)


@router.get(
    "/{run_id}/logs", summary="Get run logs", description="Get stdout/stderr and error trace for a run."
)
async def get_run_logs(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.get_run_logs(run_id)


@router.get(
    "/{run_id}/output", summary="Get run output", description="Get the full output payload for a run."
)
async def get_run_output(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.get_run_output(run_id)


@router.post("/{run_id}/cancel", summary="Cancel run", description="Cancel an in-progress run.")
async def cancel_run(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.cancel_run(run_id)


@router.post("/{run_id}/repair", summary="Repair run", description="Re-run failed tasks for this run.")
async def repair_run(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.repair_run(run_id, [], None)


@router.post("/{run_id}/retry", summary="Retry run", description="Trigger a brand-new run of the same job.")
async def retry_run(run_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.retry_run(run_id)


@router.post(
    "/{run_id}/wait",
    summary="Wait for run",
    description="Block (with polling) until the run reaches a terminal state.",
)
async def wait_for_run(
    run_id: int, body: WaitForRunRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.wait_for_run(run_id, body.timeout_seconds, body.poll_interval_seconds)
