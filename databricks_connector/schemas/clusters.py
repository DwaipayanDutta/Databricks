"""Schemas for the Clusters API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AutoScale(BaseModel):
    model_config = ConfigDict(extra="forbid")

    min_workers: int
    max_workers: int


class CreateClusterRequest(BaseModel):
    cluster_name: str
    spark_version: str
    node_type_id: str
    num_workers: int | None = None
    autoscale: AutoScale | None = None
    autotermination_minutes: int = 60
    spark_conf: dict[str, str] = Field(default_factory=dict)
    aws_attributes: dict[str, Any] | None = None
    azure_attributes: dict[str, Any] | None = None
    custom_tags: dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(extra="allow")


class EditClusterRequest(CreateClusterRequest):
    cluster_id: str


class ResizeClusterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str
    num_workers: int | None = None
    autoscale: AutoScale | None = None


class ClusterIdRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str


class PermanentDeleteClusterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cluster_id: str


class ClusterResponse(BaseModel):
    cluster_id: str
    cluster_name: str | None = None
    state: str | None = None

    model_config = ConfigDict(extra="allow")
