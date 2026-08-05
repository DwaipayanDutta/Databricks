"""Router for SQL statement execution, warehouses, and query history."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.schemas.sql import (
    CreateWarehouseRequest,
    ExecuteStatementRequest,
    StatementIdRequest,
    WarehouseIdRequest,
)
from databricks_connector.services.sql_service import SqlService

router = APIRouter(prefix="/api/v1/sql", tags=["SQL"])


def get_sql_service(client: DatabricksClient = Depends(get_databricks_client)) -> SqlService:
    return SqlService(client)


@router.post(
    "/statements/execute",
    summary="Execute statement",
    description="Execute a SQL statement against a warehouse.",
)
async def execute_statement(
    body: ExecuteStatementRequest, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.execute_statement(
        statement=body.statement,
        warehouse_id=body.warehouse_id,
        catalog=body.catalog,
        schema=body.schema_,
        parameters=body.parameters,
        wait_timeout=body.wait_timeout,
        row_limit=body.row_limit,
    )


@router.get(
    "/statements/{statement_id}",
    summary="Get statement status",
    description="Poll the status/result of an executed statement.",
)
async def get_statement_status(
    statement_id: str, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.get_statement_status(statement_id)


@router.post("/statements/cancel", summary="Cancel statement", description="Cancel a running SQL statement.")
async def cancel_statement(
    body: StatementIdRequest, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.cancel_statement(body.statement_id)


@router.get("/warehouses", summary="List warehouses", description="List all SQL warehouses.")
async def list_warehouses(service: SqlService = Depends(get_sql_service)) -> dict[str, Any]:
    return await service.list_warehouses()


@router.post("/warehouses", summary="Create warehouse", description="Create a new SQL warehouse.")
async def create_warehouse(
    body: CreateWarehouseRequest, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.create_warehouse(body.model_dump(exclude_none=True))


@router.get("/warehouses/{warehouse_id}", summary="Get warehouse", description="Get warehouse details.")
async def get_warehouse(warehouse_id: str, service: SqlService = Depends(get_sql_service)) -> dict[str, Any]:
    return await service.get_warehouse(warehouse_id)


@router.post("/warehouses/start", summary="Start warehouse", description="Start a stopped SQL warehouse.")
async def start_warehouse(
    body: WarehouseIdRequest, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.start_warehouse(body.warehouse_id)


@router.post("/warehouses/stop", summary="Stop warehouse", description="Stop a running SQL warehouse.")
async def stop_warehouse(
    body: WarehouseIdRequest, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.stop_warehouse(body.warehouse_id)


@router.delete(
    "/warehouses/{warehouse_id}", summary="Delete warehouse", description="Delete a SQL warehouse."
)
async def delete_warehouse(
    warehouse_id: str, service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.delete_warehouse(warehouse_id)


@router.get("/history", summary="Query history", description="List recent SQL query history.")
async def query_history(
    max_results: int = Query(default=100, ge=1, le=1000), service: SqlService = Depends(get_sql_service)
) -> dict[str, Any]:
    return await service.query_history(max_results=max_results)
