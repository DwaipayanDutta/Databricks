"""Tests for the SQL router/service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_execute_statement(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"statement_id": "stmt-1", "status": {"state": "SUCCEEDED"}}
    payload = {"statement": "SELECT 1", "warehouse_id": "wh-1"}
    response = client.post("/api/v1/sql/statements/execute", json=payload)
    assert response.status_code == 200
    assert response.json()["statement_id"] == "stmt-1"


def test_get_statement_status(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"statement_id": "stmt-1", "status": {"state": "SUCCEEDED"}}
    response = client.get("/api/v1/sql/statements/stmt-1")
    assert response.status_code == 200


def test_cancel_statement(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/sql/statements/cancel", json={"statement_id": "stmt-1"})
    assert response.status_code == 200


def test_list_warehouses(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"warehouses": []}
    response = client.get("/api/v1/sql/warehouses")
    assert response.status_code == 200


def test_create_warehouse(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"id": "wh-2"}
    response = client.post("/api/v1/sql/warehouses", json={"name": "analytics"})
    assert response.status_code == 200
    assert response.json()["id"] == "wh-2"


def test_query_history(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"res": []}
    response = client.get("/api/v1/sql/history")
    assert response.status_code == 200
