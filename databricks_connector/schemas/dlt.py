"""Schemas for the Delta Live Tables (DLT) API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CreatePipelineRequest(BaseModel):
    name: str
    storage: str | None = None
    target: str | None = None
    libraries: list[dict[str, Any]] = Field(default_factory=list)
    clusters: list[dict[str, Any]] = Field(default_factory=list)
    continuous: bool = False
    development: bool = True
    channel: str = "CURRENT"

    model_config = ConfigDict(extra="allow")


class UpdatePipelineRequest(CreatePipelineRequest):
    pipeline_id: str


class PipelineIdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline_id: str


class StartPipelineUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pipeline_id: str
    full_refresh: bool = False
