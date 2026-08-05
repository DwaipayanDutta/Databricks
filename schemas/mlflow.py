"""Schemas for the MLflow API (experiments, runs, models, registry)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateExperimentRequest(BaseModel):
    name: str
    artifact_location: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class ExperimentIdRequest(BaseModel):
    experiment_id: str


class CreateRunRequest(BaseModel):
    experiment_id: str
    run_name: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class RunIdRequest(BaseModel):
    run_id: str


class LogMetricRequest(BaseModel):
    run_id: str
    key: str
    value: float
    timestamp: int | None = None
    step: int | None = None


class LogParamRequest(BaseModel):
    run_id: str
    key: str
    value: str


class ListArtifactsRequest(BaseModel):
    run_id: str
    path: str | None = None


class CreateRegisteredModelRequest(BaseModel):
    name: str
    tags: dict[str, str] = Field(default_factory=dict)
    description: str | None = None


class CreateModelVersionRequest(BaseModel):
    name: str
    source: str
    run_id: str | None = None


class TransitionModelVersionStageRequest(BaseModel):
    name: str
    version: str
    stage: str
    archive_existing_versions: bool = False
