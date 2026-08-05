"""Service layer for Clusters API (2.1): https://docs.databricks.com/api/workspace/clusters"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_BASE = "/api/2.1/clusters"


class ClusterService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def list_clusters(
        self,
        page_token: str | None = None,
        limit: int | None = None,
        filter_by: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """List clusters, paginated via `page_token`/`next_page_token` per the
        current Clusters API (superseding the older unpaginated response)."""
        params: dict[str, Any] = {}
        if page_token:
            params["page_token"] = page_token
        if limit is not None:
            params["limit"] = limit
        if filter_by:
            params["filter_by"] = filter_by
        return await self._client.get(f"{_BASE}/list", params=params or None)

    async def create_cluster(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/create", json_body=settings)

    async def get_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/get", params={"cluster_id": cluster_id})

    async def start_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/start", json_body={"cluster_id": cluster_id})

    async def restart_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/restart", json_body={"cluster_id": cluster_id})

    async def resize_cluster(
        self, cluster_id: str, num_workers: int | None, autoscale: dict[str, Any] | None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"cluster_id": cluster_id}
        if num_workers is not None:
            body["num_workers"] = num_workers
        if autoscale is not None:
            body["autoscale"] = autoscale
        return await self._client.post(f"{_BASE}/resize", json_body=body)

    async def edit_cluster(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/edit", json_body=settings)

    async def terminate_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/delete", json_body={"cluster_id": cluster_id})

    async def permanent_delete_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/permanent-delete", json_body={"cluster_id": cluster_id})

    async def pin_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/pin", json_body={"cluster_id": cluster_id})

    async def unpin_cluster(self, cluster_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/unpin", json_body={"cluster_id": cluster_id})

    async def list_node_types(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/list-node-types")

    async def list_spark_versions(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/spark-versions")

    async def get_cluster_events(
        self,
        cluster_id: str,
        page_size: int = 50,
        page_token: str | None = None,
        start_time: int | None = None,
        end_time: int | None = None,
        event_types: list[str] | None = None,
    ) -> dict[str, Any]:
        """List cluster lifecycle events using token-based pagination
        (`page_size`/`page_token`), which supersedes the deprecated
        `limit`/`offset`/`total_count` fields on this endpoint."""
        body: dict[str, Any] = {"cluster_id": cluster_id, "page_size": page_size}
        if page_token:
            body["page_token"] = page_token
        if start_time is not None:
            body["start_time"] = start_time
        if end_time is not None:
            body["end_time"] = end_time
        if event_types:
            body["event_types"] = event_types
        return await self._client.post(f"{_BASE}/events", json_body=body)
