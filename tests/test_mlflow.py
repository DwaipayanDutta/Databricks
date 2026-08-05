"""Tests for the MLflow router/service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_create_experiment(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"experiment_id": "exp-1"}
    response = client.post("/api/v1/mlflow/experiments", json={"name": "my-exp"})
    assert response.status_code == 200
    assert response.json()["experiment_id"] == "exp-1"


def test_list_experiments(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"experiments": []}
    response = client.get("/api/v1/mlflow/experiments")
    assert response.status_code == 200


def test_create_run(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"run": {"info": {"run_id": "run-1"}}}
    response = client.post("/api/v1/mlflow/runs", json={"experiment_id": "exp-1"})
    assert response.status_code == 200


def test_log_metric(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {"run_id": "run-1", "key": "accuracy", "value": 0.95}
    response = client.post("/api/v1/mlflow/runs/log-metric", json=payload)
    assert response.status_code == 200


def test_create_registered_model(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"registered_model": {"name": "my-model"}}
    response = client.post("/api/v1/mlflow/models", json={"name": "my-model"})
    assert response.status_code == 200


def test_transition_model_version_stage(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {"name": "my-model", "version": "1", "stage": "Production"}
    response = client.post("/api/v1/mlflow/model-versions/transition-stage", json=payload)
    assert response.status_code == 200
