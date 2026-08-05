"""Schemas for Jobs and Job Runs APIs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobSettings(BaseModel):
    """Pass-through container for Databricks job settings (tasks, schedule, etc.)."""

    name: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)
    tasks: list[dict[str, Any]] = Field(default_factory=list)
    schedule: dict[str, Any] | None = None
    max_concurrent_runs: int | None = None
    timeout_seconds: int | None = None
    email_notifications: dict[str, Any] | None = None

    model_config = {"extra": "allow"}


class CreateJobRequest(JobSettings):
    class Config:
        json_schema_extra = {
            "example": {
                "name": "nightly-etl",
                "tasks": [{"task_key": "main", "notebook_task": {"notebook_path": "/Repos/etl/main"}}],
            }
        }


class UpdateJobRequest(BaseModel):
    job_id: int
    new_settings: JobSettings
    fields_to_remove: list[str] = Field(default_factory=list)


class DeleteJobRequest(BaseModel):
    job_id: int


class TriggerJobRequest(BaseModel):
    job_id: int
    notebook_params: dict[str, str] = Field(default_factory=dict)
    jar_params: list[str] = Field(default_factory=list)
    python_params: list[str] = Field(default_factory=list)
    idempotency_token: str | None = None


class RunNowRequest(TriggerJobRequest):
    pass


class ResetJobRequest(BaseModel):
    job_id: int
    new_settings: JobSettings


class RepairRunRequest(BaseModel):
    run_id: int
    rerun_tasks: list[str] = Field(default_factory=list)
    latest_repair_id: int | None = None


class CancelRunRequest(BaseModel):
    run_id: int


class PauseJobRequest(BaseModel):
    job_id: int


class ResumeJobRequest(BaseModel):
    job_id: int


class CloneJobRequest(BaseModel):
    job_id: int
    new_name: str | None = None


class ExportJobRequest(BaseModel):
    job_id: int


class ImportJobRequest(BaseModel):
    settings: JobSettings


class JobResponse(BaseModel):
    job_id: int
    settings: dict[str, Any] = Field(default_factory=dict)
    created_time: int | None = None

    model_config = {"extra": "allow"}


class WaitForRunRequest(BaseModel):
    run_id: int
    timeout_seconds: int = 600
    poll_interval_seconds: int = 5
