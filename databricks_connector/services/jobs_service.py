"""Service layer for Jobs and Job Runs.

Wraps the Databricks Jobs API (2.1): https://docs.databricks.com/api/workspace/jobs
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from databricks_connector.core.client import DatabricksClient
from databricks_connector.core.exceptions import TimeoutErrorConnector
from databricks_connector.core.logging import get_logger

logger = get_logger(__name__)

_BASE = "/api/2.1/jobs"


class JobsService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    # --- Jobs ---

    async def list_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        name: str | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List jobs. Prefer `page_token` (from a previous response's
        `next_page_token`) over `offset`, which Databricks has deprecated
        in favor of token-based pagination; `offset` is still accepted for
        backward compatibility but is ignored once `page_token` is given.
        """
        params: dict[str, Any] = {"limit": limit}
        if page_token:
            params["page_token"] = page_token
        else:
            params["offset"] = offset
        if name:
            params["name"] = name
        return await self._client.get(f"{_BASE}/list", params=params)

    async def get_job(self, job_id: int) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/get", params={"job_id": job_id})

    async def create_job(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/create", json_body=settings)

    async def update_job(
        self, job_id: int, new_settings: dict[str, Any], fields_to_remove: list[str]
    ) -> dict[str, Any]:
        body = {"job_id": job_id, "new_settings": new_settings, "fields_to_remove": fields_to_remove}
        return await self._client.post(f"{_BASE}/update", json_body=body)

    async def delete_job(self, job_id: int) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/delete", json_body={"job_id": job_id})

    async def trigger_job(self, job_id: int, **params: Any) -> dict[str, Any]:
        body = {"job_id": job_id, **{k: v for k, v in params.items() if v}}
        return await self._client.post(f"{_BASE}/run-now", json_body=body)

    async def run_now(self, job_id: int, **params: Any) -> dict[str, Any]:
        return await self.trigger_job(job_id, **params)

    async def reset_job(self, job_id: int, new_settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/reset", json_body={"job_id": job_id, "new_settings": new_settings}
        )

    async def repair_run(
        self, run_id: int, rerun_tasks: list[str], latest_repair_id: int | None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"run_id": run_id}
        if rerun_tasks:
            body["rerun_tasks"] = rerun_tasks
        if latest_repair_id is not None:
            body["latest_repair_id"] = latest_repair_id
        return await self._client.post(f"{_BASE}/runs/repair", json_body=body)

    async def cancel_run(self, run_id: int) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/runs/cancel", json_body={"run_id": run_id})

    async def _set_schedule_pause_status(self, job_id: int, pause_status: str) -> dict[str, Any]:
        """Shared by pause_job/resume_job: flip a job's schedule.pause_status
        in place, since Databricks has no dedicated pause/resume endpoint.
        """
        job = await self.get_job(job_id)
        settings = job.get("settings", {})
        schedule = dict(settings.get("schedule", {}))
        schedule["pause_status"] = pause_status
        return await self.update_job(job_id, {"schedule": schedule}, [])

    async def pause_job(self, job_id: int) -> dict[str, Any]:
        return await self._set_schedule_pause_status(job_id, "PAUSED")

    async def resume_job(self, job_id: int) -> dict[str, Any]:
        return await self._set_schedule_pause_status(job_id, "UNPAUSED")

    async def clone_job(self, job_id: int, new_name: str | None = None) -> dict[str, Any]:
        job = await self.get_job(job_id)
        settings = dict(job.get("settings", {}))
        if new_name:
            settings["name"] = new_name
        else:
            settings["name"] = f"{settings.get('name', 'job')}-clone"
        return await self.create_job(settings)

    async def export_job(self, job_id: int) -> dict[str, Any]:
        return await self.get_job(job_id)

    async def import_job(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self.create_job(settings)

    # --- Job Runs ---

    async def list_runs(
        self,
        job_id: int | None = None,
        limit: int = 20,
        offset: int = 0,
        active_only: bool = False,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        """List job runs. Prefer `page_token` over `offset`, which
        Databricks deprecated for this endpoint in June 2023 in favor of
        token-based pagination; `offset` is still accepted for backward
        compatibility but is ignored once `page_token` is given.
        """
        params: dict[str, Any] = {"limit": limit, "active_only": active_only}
        if page_token:
            params["page_token"] = page_token
        else:
            params["offset"] = offset
        if job_id is not None:
            params["job_id"] = job_id
        return await self._client.get(f"{_BASE}/runs/list", params=params)

    async def get_run(self, run_id: int) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/runs/get", params={"run_id": run_id})

    async def get_run_output(self, run_id: int) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/runs/get-output", params={"run_id": run_id})

    async def get_run_logs(self, run_id: int) -> dict[str, Any]:
        output = await self.get_run_output(run_id)
        return {
            "run_id": run_id,
            "logs": output.get("logs"),
            "error": output.get("error"),
            "error_trace": output.get("error_trace"),
        }

    async def retry_run(self, run_id: int) -> dict[str, Any]:
        run = await self.get_run(run_id)
        job_id = run.get("job_id")
        if job_id is None:
            raise ValueError(f"Unable to determine job_id for run {run_id}; cannot retry")
        return await self.run_now(job_id)

    async def wait_for_run(
        self, run_id: int, timeout_seconds: int = 600, poll_interval_seconds: int = 5
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        terminal_states = {"TERMINATED", "SKIPPED", "INTERNAL_ERROR"}
        while True:
            run = await self.get_run(run_id)
            life_cycle_state = run.get("state", {}).get("life_cycle_state")
            if life_cycle_state in terminal_states:
                return run
            if time.monotonic() >= deadline:
                raise TimeoutErrorConnector(f"Run {run_id} did not complete within {timeout_seconds}s")
            await asyncio.sleep(poll_interval_seconds)
