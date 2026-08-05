"""Router for MLflow: experiments, runs, artifacts, model registry."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.schemas.mlflow import (
    CreateExperimentRequest,
    CreateModelVersionRequest,
    CreateRegisteredModelRequest,
    CreateRunRequest,
    LogMetricRequest,
    LogParamRequest,
    TransitionModelVersionStageRequest,
)
from databricks_connector.services.mlflow_service import MlflowService

router = APIRouter(prefix="/api/v1/mlflow", tags=["MLflow"])


def get_mlflow_service(client: DatabricksClient = Depends(get_databricks_client)) -> MlflowService:
    return MlflowService(client)


# --- Experiments ---
@router.post("/experiments", summary="Create experiment")
async def create_experiment(
    body: CreateExperimentRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.create_experiment(body.name, body.artifact_location, body.tags)


@router.get("/experiments/{experiment_id}", summary="Get experiment")
async def get_experiment(
    experiment_id: str, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.get_experiment(experiment_id)


@router.get("/experiments", summary="List experiments")
async def list_experiments(
    max_results: int = Query(default=100, ge=1, le=1000),
    page_token: str | None = Query(
        default=None, description="Token from a previous response's next_page_token."
    ),
    service: MlflowService = Depends(get_mlflow_service),
) -> dict[str, Any]:
    return await service.list_experiments(max_results, page_token)


@router.delete("/experiments/{experiment_id}", summary="Delete experiment")
async def delete_experiment(
    experiment_id: str, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.delete_experiment(experiment_id)


# --- Runs ---
@router.post("/runs", summary="Create run")
async def create_run(
    body: CreateRunRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.create_run(body.experiment_id, body.run_name, body.tags)


@router.get("/runs/{run_id}", summary="Get run")
async def get_run(run_id: str, service: MlflowService = Depends(get_mlflow_service)) -> dict[str, Any]:
    return await service.get_run(run_id)


@router.delete("/runs/{run_id}", summary="Delete run")
async def delete_run(run_id: str, service: MlflowService = Depends(get_mlflow_service)) -> dict[str, Any]:
    return await service.delete_run(run_id)


@router.get("/runs", summary="List/search runs")
async def list_runs(
    experiment_ids: list[str] = Query(...),
    max_results: int = Query(default=1000, ge=1, le=50000),
    page_token: str | None = Query(
        default=None, description="Token from a previous response's next_page_token."
    ),
    service: MlflowService = Depends(get_mlflow_service),
) -> dict[str, Any]:
    return await service.list_runs(experiment_ids, max_results, page_token)


@router.post("/runs/log-metric", summary="Log metric")
async def log_metric(
    body: LogMetricRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.log_metric(body.run_id, body.key, body.value, body.timestamp, body.step)


@router.post("/runs/log-param", summary="Log parameter")
async def log_param(
    body: LogParamRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.log_param(body.run_id, body.key, body.value)


# --- Artifacts ---
@router.get("/artifacts", summary="List artifacts")
async def list_artifacts(
    run_id: str = Query(...),
    path: str = Query(default=None),
    service: MlflowService = Depends(get_mlflow_service),
) -> dict[str, Any]:
    return await service.list_artifacts(run_id, path)


# --- Model Registry ---
@router.post("/models", summary="Create registered model")
async def create_registered_model(
    body: CreateRegisteredModelRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.create_registered_model(body.name, body.tags, body.description)


@router.get("/models/{name}", summary="Get registered model")
async def get_registered_model(
    name: str, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.get_registered_model(name)


@router.get("/models", summary="List registered models")
async def list_registered_models(
    max_results: int = Query(default=100, ge=1, le=1000),
    page_token: str | None = Query(
        default=None, description="Token from a previous response's next_page_token."
    ),
    service: MlflowService = Depends(get_mlflow_service),
) -> dict[str, Any]:
    return await service.list_registered_models(max_results, page_token)


@router.delete("/models/{name}", summary="Delete registered model")
async def delete_registered_model(
    name: str, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.delete_registered_model(name)


@router.post("/model-versions", summary="Create model version")
async def create_model_version(
    body: CreateModelVersionRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.create_model_version(body.name, body.source, body.run_id)


@router.get("/model-versions/{name}/{version}", summary="Get model version")
async def get_model_version(
    name: str, version: str, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.get_model_version(name, version)


@router.post("/model-versions/transition-stage", summary="Transition model version stage")
async def transition_stage(
    body: TransitionModelVersionStageRequest, service: MlflowService = Depends(get_mlflow_service)
) -> dict[str, Any]:
    return await service.transition_model_version_stage(
        body.name, body.version, body.stage, body.archive_existing_versions
    )
