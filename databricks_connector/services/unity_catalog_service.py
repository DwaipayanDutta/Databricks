"""Service layer for Unity Catalog: /api/2.1/unity-catalog"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_BASE = "/api/2.1/unity-catalog"


def _pagination_params(max_results: int | None, page_token: str | None) -> dict[str, Any]:
    """Build the `max_results`/`page_token` query params shared by every
    Unity Catalog list endpoint. Databricks recommends always passing
    `max_results` (even 0) to opt into the paginated response shape, since
    unpaginated calls are being deprecated.
    """
    params: dict[str, Any] = {}
    if max_results is not None:
        params["max_results"] = max_results
    if page_token:
        params["page_token"] = page_token
    return params


class UnityCatalogService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    # --- Catalogs ---
    async def list_catalogs(
        self, max_results: int | None = None, page_token: str | None = None
    ) -> dict[str, Any]:
        params = _pagination_params(max_results, page_token)
        return await self._client.get(f"{_BASE}/catalogs", params=params or None)

    async def create_catalog(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/catalogs", json_body=body)

    async def get_catalog(self, name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/catalogs/{name}")

    async def delete_catalog(self, name: str, force: bool = False) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/catalogs/{name}", params={"force": force})

    # --- Schemas ---
    async def list_schemas(
        self, catalog_name: str, max_results: int | None = None, page_token: str | None = None
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"catalog_name": catalog_name, **_pagination_params(max_results, page_token)}
        return await self._client.get(f"{_BASE}/schemas", params=params)

    async def create_schema(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/schemas", json_body=body)

    async def get_schema(self, full_name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/schemas/{full_name}")

    async def delete_schema(self, full_name: str, force: bool = False) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/schemas/{full_name}", params={"force": force})

    # --- Tables ---
    async def list_tables(
        self,
        catalog_name: str,
        schema_name: str,
        max_results: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            **_pagination_params(max_results, page_token),
        }
        return await self._client.get(f"{_BASE}/tables", params=params)

    async def get_table(self, full_name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/tables/{full_name}")

    async def delete_table(self, full_name: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/tables/{full_name}")

    # --- Volumes ---
    async def list_volumes(
        self,
        catalog_name: str,
        schema_name: str,
        max_results: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            **_pagination_params(max_results, page_token),
        }
        return await self._client.get(f"{_BASE}/volumes", params=params)

    async def create_volume(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/volumes", json_body=body)

    async def get_volume(self, full_name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/volumes/{full_name}")

    async def delete_volume(self, full_name: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/volumes/{full_name}")

    # --- Functions ---
    async def list_functions(
        self,
        catalog_name: str,
        schema_name: str,
        max_results: int | None = None,
        page_token: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "catalog_name": catalog_name,
            "schema_name": schema_name,
            **_pagination_params(max_results, page_token),
        }
        return await self._client.get(f"{_BASE}/functions", params=params)

    async def get_function(self, full_name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/functions/{full_name}")

    async def delete_function(self, full_name: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/functions/{full_name}")

    # --- Permissions / Grants ---
    async def get_permissions(self, securable_type: str, full_name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/permissions/{securable_type}/{full_name}")

    async def update_permissions(
        self, securable_type: str, full_name: str, changes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return await self._client.patch(
            f"{_BASE}/permissions/{securable_type}/{full_name}", json_body={"changes": changes}
        )

    async def get_grants(
        self, securable_type: str, full_name: str, principal: str | None = None
    ) -> dict[str, Any]:
        params = {"principal": principal} if principal else None
        return await self._client.get(
            f"{_BASE}/effective-permissions/{securable_type}/{full_name}", params=params
        )

    # --- External Locations ---
    async def list_external_locations(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/external-locations")

    async def create_external_location(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/external-locations", json_body=body)

    async def get_external_location(self, name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/external-locations/{name}")

    async def delete_external_location(self, name: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/external-locations/{name}")

    # --- Storage Credentials ---
    async def list_storage_credentials(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/storage-credentials")

    async def create_storage_credential(self, body: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/storage-credentials", json_body=body)

    async def get_storage_credential(self, name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/storage-credentials/{name}")

    async def delete_storage_credential(self, name: str) -> dict[str, Any]:
        return await self._client.delete(f"{_BASE}/storage-credentials/{name}")
