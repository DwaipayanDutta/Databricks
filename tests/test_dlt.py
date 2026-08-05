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


def test_list_pipelines_with_page_token(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"statuses": [], "next_page_token": "tok"}
    response = client.get("/api/v1/dlt/pipelines", params={"page_token": "abc"})
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["page_token"] == "abc"
    assert "filter" not in kwargs["params"]


def test_list_pipeline_events_with_page_token(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"events": []}
    response = client.get("/api/v1/dlt/pipelines/pl-1/events", params={"page_token": "tok-2"})
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["page_token"] == "tok-2"
