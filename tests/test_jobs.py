"""Tests for the Jobs and Job Runs routers/services."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_list_jobs(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"jobs": [{"job_id": 1}]}
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200
    assert response.json() == {"jobs": [{"job_id": 1}]}
    fake_client.get.assert_awaited_once()


def test_get_job(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"job_id": 42, "settings": {"name": "etl"}}
    response = client.get("/api/v1/jobs/42")
    assert response.status_code == 200
    assert response.json()["job_id"] == 42


def test_create_job(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"job_id": 100}
    payload = {"name": "nightly-etl", "tasks": [{"task_key": "main"}]}
    response = client.post("/api/v1/jobs/create", json=payload)
    assert response.status_code == 200
    assert response.json() == {"job_id": 100}
    args, kwargs = fake_client.post.call_args
    assert args[0] == "/api/2.1/jobs/create"


def test_delete_job(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.request("DELETE", "/api/v1/jobs/delete", json={"job_id": 5})
    assert response.status_code == 200


def test_trigger_job(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"run_id": 999}
    response = client.post("/api/v1/jobs/trigger", json={"job_id": 5})
    assert response.status_code == 200
    assert response.json()["run_id"] == 999


def test_cancel_run(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/jobs/cancel", json={"run_id": 7})
    assert response.status_code == 200


def test_list_runs(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"runs": []}
    response = client.get("/api/v1/job-runs", params={"job_id": 5})
    assert response.status_code == 200


def test_get_run_logs(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"logs": "hello", "error": None, "error_trace": None}
    response = client.get("/api/v1/job-runs/7/logs")
    assert response.status_code == 200
    assert response.json()["logs"] == "hello"


def test_job_error_propagation(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    from databricks_connector.core.exceptions import NotFoundError

    fake_client.get.side_effect = NotFoundError("Job not found")
    response = client.get("/api/v1/jobs/999999")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "not_found"


def test_wait_for_run_uses_path_run_id_with_default_body(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    """Regression test: WaitForRunRequest no longer has a (previously
    ignored) run_id field, and the endpoint works with an empty body,
    using the path parameter as the single source of truth."""
    fake_client.get.return_value = {"state": {"life_cycle_state": "TERMINATED"}}
    response = client.post("/api/v1/job-runs/42/wait", json={})
    assert response.status_code == 200
    args, kwargs = fake_client.get.call_args
    assert kwargs["params"]["run_id"] == 42


def test_wait_for_run_custom_timeout(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"state": {"life_cycle_state": "SKIPPED"}}
    response = client.post(
        "/api/v1/job-runs/7/wait", json={"timeout_seconds": 30, "poll_interval_seconds": 1}
    )
    assert response.status_code == 200


def test_trigger_job_rejects_unknown_field(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    """Regression test for extra='forbid' hardening: an unexpected field in
    the request body should be a clear 422, not silently ignored."""
    response = client.post("/api/v1/jobs/trigger", json={"job_id": 5, "totally_made_up_field": "oops"})
    assert response.status_code == 422
