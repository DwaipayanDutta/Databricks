"""Schemas for the MLflow API (experiments, runs, models, registry)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    """Base for MLflow schemas: rejects unknown fields so a client typo in
    a request body (e.g. `experment_id`) surfaces as a clear 422 instead of
    being silently dropped."""

    model_config = ConfigDict(extra="forbid")


class CreateExperimentRequest(_StrictModel):
    name: str
    artifact_location: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class ExperimentIdRequest(_StrictModel):
    experiment_id: str


class CreateRunRequest(_StrictModel):
    experiment_id: str
    run_name: str | None = None
    tags: dict[str, str] = Field(default_factory=dict)


class RunIdRequest(_StrictModel):
    run_id: str


class LogMetricRequest(_StrictModel):
    run_id: str
    key: str
    value: float
    timestamp: int | None = None
    step: int | None = None


class LogParamRequest(_StrictModel):
    run_id: str
    key: str
    value: str


class ListArtifactsRequest(_StrictModel):
    run_id: str
    path: str | None = None


class CreateRegisteredModelRequest(_StrictModel):
    name: str
    tags: dict[str, str] = Field(default_factory=dict)
    description: str | None = None


class CreateModelVersionRequest(_StrictModel):
    name: str
    source: str
    run_id: str | None = None


class TransitionModelVersionStageRequest(_StrictModel):
    name: str
    version: str
    stage: str
    archive_existing_versions: bool = False
