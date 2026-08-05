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


def test_list_experiments_uses_post_not_get(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    """Regression test: Databricks' experiments/search endpoint requires
    POST with a JSON body; a GET request against it returns 405 on a real
    workspace. Ensure we never regress back to GET."""
    fake_client.post.return_value = {"experiments": []}
    response = client.get("/api/v1/mlflow/experiments", params={"max_results": 50})
    assert response.status_code == 200
    fake_client.post.assert_awaited_once()
    fake_client.get.assert_not_called()
    args, kwargs = fake_client.post.call_args
    assert args[0] == "/api/2.0/mlflow/experiments/search"
    assert kwargs["json_body"]["max_results"] == 50


def test_list_experiments_with_page_token(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"experiments": [], "next_page_token": "tok"}
    response = client.get("/api/v1/mlflow/experiments", params={"page_token": "abc"})
    assert response.status_code == 200
    _, kwargs = fake_client.post.call_args
    assert kwargs["json_body"]["page_token"] == "abc"


def test_list_runs_with_pagination(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"runs": []}
    response = client.get("/api/v1/mlflow/runs", params={"experiment_ids": ["exp-1"], "page_token": "tok-1"})
    assert response.status_code == 200
    _, kwargs = fake_client.post.call_args
    assert kwargs["json_body"]["page_token"] == "tok-1"


def test_list_registered_models_with_page_token(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    fake_client.get.return_value = {"registered_models": []}
    response = client.get("/api/v1/mlflow/models", params={"page_token": "tok-2"})
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["page_token"] == "tok-2"
