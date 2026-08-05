"""Tests for /health, /ready, /live."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert "version" in body


def test_live(client: TestClient) -> None:
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_ready_success(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"versions": []}
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["dependencies"]["databricks_api"] == "reachable"


def test_ready_failure(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    from core.exceptions import ServiceUnavailableError

    fake_client.get.side_effect = ServiceUnavailableError("down")
    response = client.get("/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "not_ready"


def test_response_has_correlation_headers(client: TestClient) -> None:
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert "X-Correlation-ID" in response.headers
