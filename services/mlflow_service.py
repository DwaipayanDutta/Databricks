"""Service layer for MLflow (experiments, runs, artifacts, model registry): /api/2.0/mlflow"""

from __future__ import annotations

from typing import Any

from core.client import DatabricksClient

_BASE = "/api/2.0/mlflow"


class MlflowService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    # --- Experiments ---
    async def create_experiment(
        self, name: str, artifact_location: str | None, tags: dict[str, str]
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if artifact_location:
            body["artifact_location"] = artifact_location
        if tags:
            body["tags"] = [{"key": k, "value": v} for k, v in tags.items()]
        return await self._client.post(f"{_BASE}/experiments/create", json_body=body)

    async def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/experiments/get", params={"experiment_id": experiment_id})

    async def list_experiments(self, max_results: int = 100) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/experiments/search", params={"max_results": max_results})

    async def delete_experiment(self, experiment_id: str) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/experiments/delete", json_body={"experiment_id": experiment_id}
        )

    # --- Runs ---
    async def create_run(
        self, experiment_id: str, run_name: str | None, tags: dict[str, str]
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"experiment_id": experiment_id}
        if run_name:
            body["run_name"] = run_name
        if tags:
            body["tags"] = [{"key": k, "value": v} for k, v in tags.items()]
        return await self._client.post(f"{_BASE}/runs/create", json_body=body)

    async def get_run(self, run_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/runs/get", params={"run_id": run_id})

    async def delete_run(self, run_id: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/runs/delete", json_body={"run_id": run_id})

    async def list_runs(self, experiment_ids: list[str]) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/runs/search", json_body={"experiment_ids": experiment_ids})

    async def log_metric(
        self, run_id: str, key: str, value: float, timestamp: int | None, step: int | None
    ) -> dict[str, Any]:
        import time as _time

        body = {
            "run_id": run_id,
            "key": key,
            "value": value,
            "timestamp": timestamp or int(_time.time() * 1000),
            "step": step or 0,
        }
        return await self._client.post(f"{_BASE}/runs/log-metric", json_body=body)

    async def log_param(self, run_id: str, key: str, value: str) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/runs/log-parameter", json_body={"run_id": run_id, "key": key, "value": value}
        )

    # --- Artifacts ---
    async def list_artifacts(self, run_id: str, path: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {"run_id": run_id}
        if path:
            params["path"] = path
        return await self._client.get(f"{_BASE}/artifacts/list", params=params)

    # --- Model Registry ---
    async def create_registered_model(
        self, name: str, tags: dict[str, str], description: str | None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name}
        if description:
            body["description"] = description
        if tags:
            body["tags"] = [{"key": k, "value": v} for k, v in tags.items()]
        return await self._client.post(f"{_BASE}/registered-models/create", json_body=body)

    async def get_registered_model(self, name: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/registered-models/get", params={"name": name})

    async def list_registered_models(self, max_results: int = 100) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/registered-models/list", params={"max_results": max_results})

    async def delete_registered_model(self, name: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/registered-models/delete", json_body={"name": name})

    async def create_model_version(self, name: str, source: str, run_id: str | None) -> dict[str, Any]:
        body: dict[str, Any] = {"name": name, "source": source}
        if run_id:
            body["run_id"] = run_id
        return await self._client.post(f"{_BASE}/model-versions/create", json_body=body)

    async def get_model_version(self, name: str, version: str) -> dict[str, Any]:
        return await self._client.get(
            f"{_BASE}/model-versions/get", params={"name": name, "version": version}
        )

    async def transition_model_version_stage(
        self, name: str, version: str, stage: str, archive_existing: bool
    ) -> dict[str, Any]:
        body = {
            "name": name,
            "version": version,
            "stage": stage,
            "archive_existing_versions": archive_existing,
        }
        return await self._client.post(f"{_BASE}/model-versions/transition-stage", json_body=body)
