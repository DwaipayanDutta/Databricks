"""Regression tests for the enterprise production audit pass.

Each test below is anchored to a specific defect found and fixed during the
audit (see CHANGELOG.md's latest entry). Kept in one file, separate from the
per-domain test modules, so the audit's fixes and their coverage are easy to
review together.
"""

from __future__ import annotations

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient

# --- Permissions: access_control_list must use Databricks' real field names ---


def test_update_permissions_sends_user_name_not_principal(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    """Regression test: the ACL entries PUT to Databricks must use
    `user_name`/`group_name`/`service_principal_name`, never a made-up
    `principal` field the real API doesn't understand."""
    fake_client.put.return_value = {}
    payload = {
        "object_type": "jobs",
        "object_id": "123",
        "access_control_list": [{"user_name": "user@example.com", "permission_level": "CAN_MANAGE"}],
    }
    response = client.put("/api/v1/permissions/jobs/123", json=payload)
    assert response.status_code == 200

    args, kwargs = fake_client.put.call_args
    assert args[0] == "/api/2.0/permissions/jobs/123"
    sent_acl = kwargs["json_body"]["access_control_list"]
    assert sent_acl == [{"user_name": "user@example.com", "permission_level": "CAN_MANAGE"}]
    assert "principal" not in sent_acl[0]


def test_update_permissions_accepts_group_and_service_principal(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    fake_client.put.return_value = {}
    payload = {
        "object_type": "clusters",
        "object_id": "abc",
        "access_control_list": [
            {"group_name": "data-engineers", "permission_level": "CAN_RESTART"},
            {"service_principal_name": "sp-app-id", "permission_level": "CAN_MANAGE"},
        ],
    }
    response = client.put("/api/v1/permissions/clusters/abc", json=payload)
    assert response.status_code == 200
    _, kwargs = fake_client.put.call_args
    sent_acl = kwargs["json_body"]["access_control_list"]
    assert sent_acl[0] == {"group_name": "data-engineers", "permission_level": "CAN_RESTART"}
    assert sent_acl[1] == {"service_principal_name": "sp-app-id", "permission_level": "CAN_MANAGE"}


def test_update_permissions_rejects_ambiguous_identity(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    """An ACL entry with zero or multiple identity fields set is invalid
    and must be rejected with 422 before ever reaching Databricks."""
    payload = {
        "object_type": "jobs",
        "object_id": "123",
        "access_control_list": [
            {"user_name": "a@example.com", "group_name": "b", "permission_level": "CAN_MANAGE"}
        ],
    }
    response = client.put("/api/v1/permissions/jobs/123", json=payload)
    assert response.status_code == 422
    fake_client.put.assert_not_called()

    payload_empty = {
        "object_type": "jobs",
        "object_id": "123",
        "access_control_list": [{"permission_level": "CAN_MANAGE"}],
    }
    response2 = client.put("/api/v1/permissions/jobs/123", json=payload_empty)
    assert response2.status_code == 422


def test_update_permissions_rejects_legacy_principal_field(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    """The old (buggy) request shape using `principal` must now be rejected
    outright by `extra='forbid'` rather than silently accepted and sent to
    Databricks in a form it ignores."""
    payload = {
        "object_type": "jobs",
        "object_id": "123",
        "access_control_list": [{"principal": "user@example.com", "permission_level": "CAN_MANAGE"}],
    }
    response = client.put("/api/v1/permissions/jobs/123", json=payload)
    assert response.status_code == 422


# --- Connector API key gate: previously defined but never enforced ---


def test_api_key_gate_blocks_business_endpoints_when_configured(
    monkeypatch: pytest.MonkeyPatch, fake_client: FakeDatabricksClient
) -> None:
    import os

    from databricks_connector.app import create_app
    from databricks_connector.core.client import get_databricks_client
    from databricks_connector.core.config import get_settings

    monkeypatch.setenv("CONNECTOR_API_KEY", "secret-key-123")
    get_settings.cache_clear()
    try:
        app = create_app()
        app.dependency_overrides[get_databricks_client] = lambda: fake_client
        with TestClient(app) as test_client:
            # No key -> rejected.
            resp = test_client.get("/api/v1/jobs")
            assert resp.status_code == 401

            # Wrong key -> rejected.
            resp = test_client.get("/api/v1/jobs", headers={"X-API-Key": "wrong"})
            assert resp.status_code == 401

            # Correct key -> allowed through.
            fake_client.get.return_value = {"jobs": []}
            resp = test_client.get("/api/v1/jobs", headers={"X-API-Key": "secret-key-123"})
            assert resp.status_code == 200

            # Health/live/ready/metrics stay open regardless.
            assert test_client.get("/health").status_code == 200
            assert test_client.get("/live").status_code == 200
    finally:
        monkeypatch.delenv("CONNECTOR_API_KEY", raising=False)
        get_settings.cache_clear()


def test_api_key_gate_is_noop_when_unset(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    """Default configuration (no CONNECTOR_API_KEY): every endpoint works
    without any X-API-Key header, preserving out-of-the-box behavior."""
    fake_client.get.return_value = {"jobs": []}
    response = client.get("/api/v1/jobs")
    assert response.status_code == 200


# --- CORS: allow_credentials must never pair with a literal wildcard origin ---


def test_cors_credentials_disabled_for_wildcard_origin(client: TestClient) -> None:
    response = client.options(
        "/api/v1/jobs",
        headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "*"
    assert "access-control-allow-credentials" not in response.headers


# --- SQL: previously-missing Statement Execution API fields ---


def test_execute_statement_passes_through_disposition_format_and_limits(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    fake_client.post.return_value = {"statement_id": "stmt-1"}
    payload = {
        "statement": "SELECT 1",
        "warehouse_id": "wh-1",
        "row_limit": 100,
        "byte_limit": 1000,
        "disposition": "EXTERNAL_LINKS",
        "format": "ARROW_STREAM",
        "on_wait_timeout": "CONTINUE",
    }
    response = client.post("/api/v1/sql/statements/execute", json=payload)
    assert response.status_code == 200
    _, kwargs = fake_client.post.call_args
    body = kwargs["json_body"]
    assert body["row_limit"] == 100
    assert body["byte_limit"] == 1000
    assert body["disposition"] == "EXTERNAL_LINKS"
    assert body["format"] == "ARROW_STREAM"
    assert body["on_wait_timeout"] == "CONTINUE"


# --- DBFS: download must refuse to buffer an oversized file in memory ---


def test_dbfs_download_rejects_oversized_file(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    from databricks_connector.core.config import get_settings

    max_bytes = get_settings().dbfs_download_max_bytes
    fake_client.get.return_value = {"file_size": max_bytes + 1}
    response = client.get("/api/v1/dbfs/download", params={"path": "/huge/file.bin"})
    assert response.status_code == 413
    assert response.json()["error"] == "payload_too_large"


def test_dbfs_download_pages_through_chunks(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.side_effect = [
        {"file_size": 20},
        {"data": "AAAA", "bytes_read": 10},
        {"data": "BBBB", "bytes_read": 10},
    ]
    response = client.get("/api/v1/dbfs/download", params={"path": "/tmp/small.bin"})
    assert response.status_code == 200
    body = response.json()
    assert body["file_size"] == 20
    assert body["chunks"] == ["AAAA", "BBBB"]


# --- Monitoring: summaries must page through list results, not truncate at page 1 ---


@pytest.mark.asyncio
async def test_cluster_metrics_summary_paginates() -> None:
    from unittest.mock import AsyncMock

    from databricks_connector.core.config import AuthMode, Settings
    from databricks_connector.services.monitoring_service import MonitoringService

    fake_client = AsyncMock()
    fake_client.get.side_effect = [
        {"clusters": [{"state": "RUNNING"}], "next_page_token": "p2"},
        {"clusters": [{"state": "TERMINATED"}]},
    ]
    settings = Settings(
        databricks_host="https://example.cloud.databricks.com", auth_mode=AuthMode.PAT, databricks_token="t"
    )
    service = MonitoringService(fake_client, settings)
    result = await service.cluster_metrics_summary()
    assert result["total_clusters"] == 2
    assert result["by_state"] == {"RUNNING": 1, "TERMINATED": 1}
    assert fake_client.get.await_count == 2


# --- Secrets: ACL write endpoints were missing entirely ---


def test_put_and_delete_secret_acl(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    put_payload = {"scope": "my-scope", "principal": "user@example.com", "permission": "READ"}
    assert client.put("/api/v1/secrets/acls", json=put_payload).status_code == 200
    args, kwargs = fake_client.post.call_args
    assert args[0] == "/api/2.0/secrets/acls/put"
    assert kwargs["json_body"] == put_payload

    del_payload = {"scope": "my-scope", "principal": "user@example.com"}
    assert client.request("DELETE", "/api/v1/secrets/acls", json=del_payload).status_code == 200
    args2, kwargs2 = fake_client.post.call_args
    assert args2[0] == "/api/2.0/secrets/acls/delete"
    assert kwargs2["json_body"] == del_payload


# --- End-to-end retry: a real tenacity-driven retry against a mocked transport ---


@pytest.mark.asyncio
@respx.mock
async def test_client_retries_429_then_succeeds() -> None:
    """Proves the full stack -- DatabricksClient -> retry decorator ->
    is_retryable_status -> tenacity -- actually retries a 429 and returns
    the eventual success, not just that the pieces are individually
    correct in isolation."""
    from databricks_connector.core.auth import AuthManager
    from databricks_connector.core.circuit_breaker import CircuitBreaker
    from databricks_connector.core.client import DatabricksClient
    from databricks_connector.core.config import AuthMode, Settings

    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        max_retries=3,
        backoff_factor=0.01,
    )
    auth_manager = AuthManager(settings)
    breaker = CircuitBreaker(failure_threshold=10, recovery_timeout=30, name="retry-test")
    client = DatabricksClient(settings=settings, auth_manager=auth_manager, circuit_breaker=breaker)

    route = respx.get("https://example.cloud.databricks.com/api/2.1/clusters/list")
    route.side_effect = [
        httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "rate limited"}),
        httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "rate limited"}),
        httpx.Response(200, json={"clusters": []}),
    ]

    result = await client.get("/api/2.1/clusters/list")
    assert result == {"clusters": []}
    assert route.call_count == 3
    await client.aclose()


@pytest.mark.asyncio
@respx.mock
async def test_client_does_not_retry_400() -> None:
    """A non-retryable client error must fail immediately (single attempt),
    not burn through the retry budget."""
    from databricks_connector.core.auth import AuthManager
    from databricks_connector.core.circuit_breaker import CircuitBreaker
    from databricks_connector.core.client import DatabricksClient
    from databricks_connector.core.config import AuthMode, Settings
    from databricks_connector.core.exceptions import ValidationAPIError

    settings = Settings(
        databricks_host="https://example.cloud.databricks.com",
        databricks_token="dummy",
        auth_mode=AuthMode.PAT,
        max_retries=3,
    )
    auth_manager = AuthManager(settings)
    breaker = CircuitBreaker(failure_threshold=10, recovery_timeout=30, name="no-retry-test")
    client = DatabricksClient(settings=settings, auth_manager=auth_manager, circuit_breaker=breaker)

    route = respx.post("https://example.cloud.databricks.com/api/2.1/jobs/create").mock(
        return_value=httpx.Response(400, json={"message": "bad request"})
    )

    with pytest.raises(ValidationAPIError):
        await client.post("/api/2.1/jobs/create", json_body={})
    assert route.call_count == 1
    await client.aclose()
