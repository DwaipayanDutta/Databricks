"""Tests for the Delta Live Tables router/service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_create_pipeline(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"pipeline_id": "pl-1"}
    response = client.post("/api/v1/dlt/pipelines", json={"name": "bronze-to-silver"})
    assert response.status_code == 200
    assert response.json()["pipeline_id"] == "pl-1"


def test_list_pipelines(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"statuses": []}
    response = client.get("/api/v1/dlt/pipelines")
    assert response.status_code == 200


def test_get_pipeline(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"pipeline_id": "pl-1", "state": "IDLE"}
    response = client.get("/api/v1/dlt/pipelines/pl-1")
    assert response.status_code == 200


def test_start_pipeline(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"update_id": "u-1"}
    response = client.post("/api/v1/dlt/pipelines/start", json={"pipeline_id": "pl-1"})
    assert response.status_code == 200


def test_stop_pipeline(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/dlt/pipelines/stop", json={"pipeline_id": "pl-1"})
    assert response.status_code == 200


def test_delete_pipeline(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.delete.return_value = {}
    response = client.delete("/api/v1/dlt/pipelines/pl-1")
    assert response.status_code == 200
