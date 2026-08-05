"""Router for the Jobs API. Routers never call Databricks directly — they
delegate to the service layer, which delegates to the DatabricksClient."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.client import DatabricksClient, get_databricks_client
from schemas.jobs import (
    CancelRunRequest,
    CloneJobRequest,
    CreateJobRequest,
    DeleteJobRequest,
    ExportJobRequest,
    ImportJobRequest,
    PauseJobRequest,
    RepairRunRequest,
    ResetJobRequest,
    ResumeJobRequest,
    RunNowRequest,
    TriggerJobRequest,
    UpdateJobRequest,
)
from services.jobs_service import JobsService

router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])


def get_jobs_service(client: DatabricksClient = Depends(get_databricks_client)) -> JobsService:
    return JobsService(client)


@router.get("", summary="List jobs", description="List all jobs, optionally filtered by name.")
async def list_jobs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    name: str | None = Query(default=None),
    service: JobsService = Depends(get_jobs_service),
) -> dict[str, Any]:
    return await service.list_jobs(limit=limit, offset=offset, name=name)


@router.get("/{job_id}", summary="Get job", description="Get a single job's settings and metadata by ID.")
async def get_job(job_id: int, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.get_job(job_id)


@router.post("/create", summary="Create job", description="Create a new Databricks job.")
async def create_job(
    body: CreateJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.create_job(body.model_dump(exclude_none=True))


@router.put("/update", summary="Update job", description="Partially update an existing job's settings.")
async def update_job(
    body: UpdateJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.update_job(
        body.job_id, body.new_settings.model_dump(exclude_none=True), body.fields_to_remove
    )


@router.delete("/delete", summary="Delete job", description="Delete a job by ID.")
async def delete_job(
    body: DeleteJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.delete_job(body.job_id)


@router.post("/trigger", summary="Trigger job", description="Trigger a job run with optional parameters.")
async def trigger_job(
    body: TriggerJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.trigger_job(
        body.job_id,
        notebook_params=body.notebook_params,
        jar_params=body.jar_params,
        python_params=body.python_params,
        idempotency_token=body.idempotency_token,
    )


@router.post("/run-now", summary="Run job now", description="Alias for trigger; runs the job immediately.")
async def run_now(body: RunNowRequest, service: JobsService = Depends(get_jobs_service)) -> dict[str, Any]:
    return await service.run_now(
        body.job_id,
        notebook_params=body.notebook_params,
        jar_params=body.jar_params,
        python_params=body.python_params,
        idempotency_token=body.idempotency_token,
    )


@router.post("/reset", summary="Reset job", description="Overwrite all job settings.")
async def reset_job(
    body: ResetJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.reset_job(body.job_id, body.new_settings.model_dump(exclude_none=True))


@router.post("/repair", summary="Repair run", description="Re-run failed/skipped tasks within a job run.")
async def repair_run(
    body: RepairRunRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.repair_run(body.run_id, body.rerun_tasks, body.latest_repair_id)


@router.post("/cancel", summary="Cancel run", description="Cancel an in-progress job run.")
async def cancel_run(
    body: CancelRunRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.cancel_run(body.run_id)


@router.post("/pause", summary="Pause job", description="Pause a job's schedule.")
async def pause_job(
    body: PauseJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.pause_job(body.job_id)


@router.post("/resume", summary="Resume job", description="Resume a paused job's schedule.")
async def resume_job(
    body: ResumeJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.resume_job(body.job_id)


@router.post("/clone", summary="Clone job", description="Create a copy of an existing job.")
async def clone_job(
    body: CloneJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.clone_job(body.job_id, body.new_name)


@router.post("/export", summary="Export job", description="Export a job's full definition.")
async def export_job(
    body: ExportJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.export_job(body.job_id)


@router.post("/import", summary="Import job", description="Create a job from an exported definition.")
async def import_job(
    body: ImportJobRequest, service: JobsService = Depends(get_jobs_service)
) -> dict[str, Any]:
    return await service.import_job(body.settings.model_dump(exclude_none=True))
