"""Schemas for the Delta Live Tables (DLT) API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CreatePipelineRequest(BaseModel):
    name: str
    storage: str | None = None
    target: str | None = None
    libraries: list[dict[str, Any]] = Field(default_factory=list)
    clusters: list[dict[str, Any]] = Field(default_factory=list)
    continuous: bool = False
    development: bool = True
    channel: str = "CURRENT"

    model_config = {"extra": "allow"}


class UpdatePipelineRequest(CreatePipelineRequest):
    pipeline_id: str


class PipelineIdRequest(BaseModel):
    pipeline_id: str


class StartPipelineUpdateRequest(BaseModel):
    pipeline_id: str
    full_refresh: bool = False
