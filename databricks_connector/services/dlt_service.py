"""Service layer for Delta Live Tables: /api/2.0/pipelines"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_BASE = "/api/2.0/pipelines"


class DltService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def create_pipeline(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(_BASE, json_body=settings)

    async def update_pipeline(self, pipeline_id: str, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.put(f"{_BASE}/{pipeline_id}", json_body=settings)

    async def delete_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/{pipeline_id}")

    async def start_update(self, pipeline_id: str, full_refresh: bool = False) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/{pipeline_id}/updates", json_body={"full_refresh": full_refresh}
        )

    async def stop_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/{pipeline_id}/stop")

    async def list_pipelines(
        self,
        max_results: int = 25,
        filter_str: str | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        # Per Databricks' pipelines API: page_token is mutually exclusive
        # with filter (a page_token already encodes the original query), so
        # only send filter when we're not continuing a previous page.
        params: dict[str, Any] = {"max_results": max_results}
        if page_token:
            params["page_token"] = page_token
        elif filter_str:
            params["filter"] = filter_str
        return await self._client.get(_BASE, params=params)

    async def get_pipeline(self, pipeline_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/{pipeline_id}")

    async def list_pipeline_events(
        self, pipeline_id: str, max_results: int = 25, page_token: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"max_results": max_results}
        if page_token:
            params["page_token"] = page_token
        return await self._client.get(f"{_BASE}/{pipeline_id}/events", params=params)

    async def get_pipeline_update(self, pipeline_id: str, update_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/{pipeline_id}/updates/{update_id}")
