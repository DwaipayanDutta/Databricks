"""Service layer for SQL statement execution and warehouses.

Statement Execution API: /api/2.0/sql/statements
Warehouses API: /api/2.0/sql/warehouses
Query History API: /api/2.0/sql/history/queries
"""

from __future__ import annotations

from typing import Any

from databricks_connector.core.client import DatabricksClient

_STMT_BASE = "/api/2.0/sql/statements"
_WH_BASE = "/api/2.0/sql/warehouses"
_HISTORY_BASE = "/api/2.0/sql/history/queries"


class SqlService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    # --- Statement execution ---

    async def execute_statement(
        self,
        statement: str,
        warehouse_id: str,
        catalog: str | None = None,
        schema: str | None = None,
        parameters: list[dict[str, Any]] | None = None,
        wait_timeout: str = "10s",
        row_limit: int | None = None,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "statement": statement,
            "warehouse_id": warehouse_id,
            "wait_timeout": wait_timeout,
        }
        if catalog:
            body["catalog"] = catalog
        if schema:
            body["schema"] = schema
        if parameters:
            body["parameters"] = parameters
        if row_limit:
            body["row_limit"] = row_limit
        return await self._client.post(_STMT_BASE, json_body=body)

    async def get_statement_status(self, statement_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_STMT_BASE}/{statement_id}")

    async def cancel_statement(self, statement_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_STMT_BASE}/{statement_id}/cancel")

    # --- Warehouses ---

    async def list_warehouses(self) -> dict[str, Any]:
        return await self._client.get(_WH_BASE)

    async def create_warehouse(self, settings: dict[str, Any]) -> dict[str, Any]:
        return await self._client.post(_WH_BASE, json_body=settings)

    async def get_warehouse(self, warehouse_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_WH_BASE}/{warehouse_id}")

    async def start_warehouse(self, warehouse_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_WH_BASE}/{warehouse_id}/start")

    async def stop_warehouse(self, warehouse_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_WH_BASE}/{warehouse_id}/stop")

    async def delete_warehouse(self, warehouse_id: str) -> dict[str, Any]:
        return await self._client.delete(f"{_WH_BASE}/{warehouse_id}")

    # --- Query history ---

    async def query_history(
        self,
        warehouse_ids: list[str] | None = None,
        start_time_ms: int | None = None,
        end_time_ms: int | None = None,
        max_results: int = 100,
    ) -> dict[str, Any]:
        filter_by: dict[str, Any] = {}
        if warehouse_ids:
            filter_by["warehouse_ids"] = warehouse_ids
        if start_time_ms:
            filter_by["query_start_time_range"] = {"start_time_ms": start_time_ms, "end_time_ms": end_time_ms}
        params: dict[str, Any] = {"max_results": max_results}
        return await self._client.get(_HISTORY_BASE, params=params)
