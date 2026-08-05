"""Service layer for monitoring: cluster/job health, connector self-metrics."""

from __future__ import annotations

import time
from typing import Any

from databricks_connector.core.client import DatabricksClient
from databricks_connector.core.config import Settings

_START_TIME = time.monotonic()

# Both summary endpoints below page through Databricks' list APIs to avoid
# silently under-reporting counts for workspaces with more clusters/jobs
# than fit in a single page; capped so a misbehaving/huge workspace (or a
# pathological page_token loop) can't turn a "summary" call into an
# effectively unbounded number of upstream requests.
_MAX_SUMMARY_PAGES = 20


class MonitoringService:
    def __init__(self, client: DatabricksClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    async def cluster_health(self, cluster_id: str) -> dict[str, Any]:
        cluster = await self._client.get("/api/2.1/clusters/get", params={"cluster_id": cluster_id})
        state = cluster.get("state")
        healthy_states = {"RUNNING", "RESIZING"}
        return {
            "cluster_id": cluster_id,
            "state": state,
            "healthy": state in healthy_states,
            "state_message": cluster.get("state_message"),
        }

    async def job_health(self, job_id: int) -> dict[str, Any]:
        runs = await self._client.get("/api/2.1/jobs/runs/list", params={"job_id": job_id, "limit": 5})
        recent = runs.get("runs", [])
        failures = [r for r in recent if r.get("state", {}).get("result_state") == "FAILED"]
        return {
            "job_id": job_id,
            "recent_run_count": len(recent),
            "recent_failure_count": len(failures),
            "healthy": len(failures) == 0,
        }

    async def cluster_metrics_summary(self) -> dict[str, Any]:
        by_state: dict[str, int] = {}
        total = 0
        page_token: str | None = None
        for _ in range(_MAX_SUMMARY_PAGES):
            params: dict[str, Any] = {"page_token": page_token} if page_token else {}
            clusters = await self._client.get("/api/2.1/clusters/list", params=params or None)
            items = clusters.get("clusters", [])
            total += len(items)
            for c in items:
                state = c.get("state", "UNKNOWN")
                by_state[state] = by_state.get(state, 0) + 1
            page_token = clusters.get("next_page_token")
            if not page_token:
                break
        return {"total_clusters": total, "by_state": by_state}

    async def job_metrics_summary(self) -> dict[str, Any]:
        total = 0
        page_token: str | None = None
        for _ in range(_MAX_SUMMARY_PAGES):
            params: dict[str, Any] = {"limit": 100}
            if page_token:
                params["page_token"] = page_token
            jobs = await self._client.get("/api/2.1/jobs/list", params=params)
            total += len(jobs.get("jobs", []))
            page_token = jobs.get("next_page_token")
            if not page_token:
                break
        return {"total_jobs": total}

    def connector_info(self) -> dict[str, Any]:
        from databricks_connector.core.constants import CONNECTOR_NAME, CONNECTOR_VERSION

        return {
            "name": CONNECTOR_NAME,
            "version": CONNECTOR_VERSION,
            "environment": self._settings.app_env,
            "uptime_seconds": round(time.monotonic() - _START_TIME, 2),
        }

    def connector_configuration(self) -> dict[str, Any]:
        return {
            "auth_mode": self._settings.auth_mode.value,
            "databricks_host": self._settings.databricks_host,
            "cache_enabled": self._settings.cache_enabled,
            "max_retries": self._settings.max_retries,
            "circuit_breaker_failure_threshold": self._settings.circuit_breaker_failure_threshold,
        }
