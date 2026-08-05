"""Schemas for Jobs and Job Runs APIs."""

from __future__ import annotations

from typing import Annotated, Any

from pydantic import BaseModel, ConfigDict, Field


class JobSettings(BaseModel):
    """Pass-through container for Databricks job settings (tasks, schedule, etc.).

    `extra="allow"` because Databricks' job settings payload is large and
    evolves independently of this connector; unknown fields are forwarded
    to Databricks as-is rather than rejected.
    """

    model_config = ConfigDict(extra="allow")

    name: Annotated[str | None, Field(description="Human-readable job name.")] = None
    tags: Annotated[dict[str, str], Field(description="Arbitrary key/value tags for the job.")] = Field(
        default_factory=dict
    )
    tasks: Annotated[
        list[dict[str, Any]], Field(description="List of task definitions (notebook, JAR, Python, etc.).")
    ] = Field(default_factory=list)
    schedule: Annotated[
        dict[str, Any] | None, Field(description="Cron schedule definition, if the job is scheduled.")
    ] = None
    max_concurrent_runs: Annotated[
        int | None, Field(description="Maximum number of concurrent runs allowed for this job.", ge=1)
    ] = None
    timeout_seconds: Annotated[int | None, Field(description="Per-run timeout in seconds.", ge=0)] = None
    email_notifications: Annotated[
        dict[str, Any] | None, Field(description="Email notification settings for run start/success/failure.")
    ] = None


class CreateJobRequest(JobSettings):
    """Request body for `POST /api/v1/jobs/create`."""

    model_config = ConfigDict(
        extra="allow",
        json_schema_extra={
            "example": {
                "name": "nightly-etl",
                "tasks": [{"task_key": "main", "notebook_task": {"notebook_path": "/Repos/etl/main"}}],
            }
        },
    )


class UpdateJobRequest(BaseModel):
    """Request body for `PUT /api/v1/jobs/update`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job to update.", gt=0)]
    new_settings: Annotated[JobSettings, Field(description="Settings to merge into the existing job.")]
    fields_to_remove: Annotated[
        list[str], Field(description="Top-level setting fields to remove entirely.")
    ] = Field(default_factory=list)


class DeleteJobRequest(BaseModel):
    """Request body for `DELETE /api/v1/jobs/delete`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job to delete.", gt=0)]


class TriggerJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/trigger`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job to run.", gt=0)]
    notebook_params: Annotated[
        dict[str, str], Field(description="Widget parameters passed to a notebook task.")
    ] = Field(default_factory=dict)
    jar_params: Annotated[list[str], Field(description="Positional parameters for a JAR task.")] = Field(
        default_factory=list
    )
    python_params: Annotated[list[str], Field(description="Positional parameters for a Python task.")] = (
        Field(default_factory=list)
    )
    idempotency_token: Annotated[
        str | None,
        Field(description="Token that de-duplicates run-now requests submitted within the same window."),
    ] = None


class RunNowRequest(TriggerJobRequest):
    """Request body for `POST /api/v1/jobs/run-now` (alias of trigger)."""


class ResetJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/reset`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job whose settings will be fully overwritten.", gt=0)]
    new_settings: Annotated[JobSettings, Field(description="Complete replacement settings for the job.")]


class RepairRunRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/repair`."""

    model_config = ConfigDict(extra="forbid")

    run_id: Annotated[int, Field(description="ID of the run to repair.", gt=0)]
    rerun_tasks: Annotated[
        list[str], Field(description="Task keys to re-run. Empty reruns all failed/skipped tasks.")
    ] = Field(default_factory=list)
    latest_repair_id: Annotated[
        int | None, Field(description="ID of the latest repair attempt, required for chained repairs.")
    ] = None


class CancelRunRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/cancel`."""

    model_config = ConfigDict(extra="forbid")

    run_id: Annotated[int, Field(description="ID of the run to cancel.", gt=0)]


class PauseJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/pause`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job whose schedule will be paused.", gt=0)]


class ResumeJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/resume`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job whose schedule will be resumed.", gt=0)]


class CloneJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/clone`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job to clone.", gt=0)]
    new_name: Annotated[
        str | None, Field(description="Name for the cloned job; defaults to '<name>-clone'.")
    ] = None


class ExportJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/export`."""

    model_config = ConfigDict(extra="forbid")

    job_id: Annotated[int, Field(description="ID of the job to export.", gt=0)]


class ImportJobRequest(BaseModel):
    """Request body for `POST /api/v1/jobs/import`."""

    model_config = ConfigDict(extra="forbid")

    settings: Annotated[JobSettings, Field(description="Job settings to import as a new job.")]


class JobResponse(BaseModel):
    """Representative response shape for job read endpoints.

    `extra="allow"` because Databricks returns additional fields (e.g.
    `creator_user_name`) that vary by workspace configuration; this model
    documents the fields callers can always rely on without rejecting the
    rest.
    """

    model_config = ConfigDict(extra="allow")

    job_id: Annotated[int, Field(description="Unique identifier of the job.")]
    settings: Annotated[dict[str, Any], Field(description="The job's current settings.")] = Field(
        default_factory=dict
    )
    created_time: Annotated[int | None, Field(description="Job creation time in epoch milliseconds.")] = None


class WaitForRunRequest(BaseModel):
    """Request body for `POST /api/v1/job-runs/{run_id}/wait`.

    `run_id` is taken from the URL path, not this body, so it is
    intentionally not duplicated here.
    """

    model_config = ConfigDict(extra="forbid")

    timeout_seconds: Annotated[
        int, Field(description="Maximum time to poll before giving up.", gt=0, le=3600)
    ] = 600
    poll_interval_seconds: Annotated[
        int, Field(description="Delay between polling attempts.", gt=0, le=60)
    ] = 5
