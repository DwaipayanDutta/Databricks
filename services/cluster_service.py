"""Service layer for Clusters API (2.1): https://docs.databricks.com/api/workspace/clusters"""

from __future__ import annotations

from typing import Any

from core.client import DatabricksClient

_BASE = "/api/2.1/clusters"


class ClusterService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def list_clusters(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/list")

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

    async def get_cluster_events(self, cluster_id: str, limit: int = 50) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/events", json_body={"cluster_id": cluster_id, "limit": limit}
        )
