"""Schemas for the SQL (Statement Execution + Warehouses) API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExecuteStatementRequest(BaseModel):
    statement: str
    warehouse_id: str
    catalog: str | None = None
    schema_: str | None = Field(default=None, alias="schema")
    parameters: list[dict[str, Any]] = Field(default_factory=list)
    wait_timeout: str = "10s"
    row_limit: int | None = Field(default=None, description="Max rows to return (LIMIT-equivalent).")
    byte_limit: int | None = Field(default=None, description="Max total bytes of result data to return.")
    disposition: str | None = Field(
        default=None, description="'INLINE' or 'EXTERNAL_LINKS' result delivery mode."
    )
    format: str | None = Field(
        default=None, description="Result format: 'JSON_ARRAY', 'ARROW_STREAM', or 'CSV'."
    )
    on_wait_timeout: str | None = Field(
        default=None, description="'CONTINUE' or 'CANCEL' behavior when wait_timeout elapses."
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class StatementIdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statement_id: str


class CreateWarehouseRequest(BaseModel):
    name: str
    cluster_size: str = "Small"
    min_num_clusters: int = 1
    max_num_clusters: int = 1
    auto_stop_mins: int = 10
    enable_serverless_compute: bool = True

    model_config = ConfigDict(extra="allow")


class WarehouseIdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warehouse_id: str


class QueryHistoryRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    warehouse_ids: list[str] = Field(default_factory=list)
    start_time_ms: int | None = None
    end_time_ms: int | None = None
    max_results: int = 100
