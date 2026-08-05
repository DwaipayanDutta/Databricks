"""Additional coverage for Notebooks, Secrets, Permissions, Unity Catalog,
and Monitoring routers -- rounding out coverage across the full API surface."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient

# --- Notebooks / Workspace ---


def test_import_notebook(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {"path": "/Repos/x", "content": "cHJpbnQoMSk=", "language": "PYTHON"}
    response = client.post("/api/v1/notebooks/import", json=payload)
    assert response.status_code == 200


def test_export_notebook(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"content": "cHJpbnQoMSk=", "language": "PYTHON"}
    response = client.post("/api/v1/notebooks/export", json={"path": "/Repos/x"})
    assert response.status_code == 200


def test_list_workspace(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"objects": []}
    response = client.get("/api/v1/notebooks", params={"path": "/"})
    assert response.status_code == 200


def test_get_status(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"path": "/Repos/x", "object_type": "NOTEBOOK"}
    response = client.get("/api/v1/notebooks/status", params={"path": "/Repos/x"})
    assert response.status_code == 200


def test_create_folder(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/notebooks/folders", json={"path": "/Repos/new-folder"})
    assert response.status_code == 200


def test_delete_workspace_object(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.request("DELETE", "/api/v1/notebooks", json={"path": "/Repos/x", "recursive": False})
    assert response.status_code == 200


def test_move_and_copy_object(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"content": "eA==", "language": "PYTHON"}
    fake_client.post.return_value = {}
    move_payload = {"source_path": "/a", "destination_path": "/b"}
    assert client.post("/api/v1/notebooks/move", json=move_payload).status_code == 200
    copy_payload = {"source_path": "/a", "destination_path": "/c", "overwrite": True}
    assert client.post("/api/v1/notebooks/copy", json=copy_payload).status_code == 200


# --- Secrets ---


def test_list_scopes(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"scopes": []}
    response = client.get("/api/v1/secrets/scopes")
    assert response.status_code == 200


def test_create_and_delete_scope(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    assert client.post("/api/v1/secrets/scopes", json={"scope": "my-scope"}).status_code == 200
    assert client.request("DELETE", "/api/v1/secrets/scopes", json={"scope": "my-scope"}).status_code == 200


def test_put_and_delete_secret(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    put_payload = {"scope": "my-scope", "key": "api_key", "string_value": "secret-value"}
    assert client.put("/api/v1/secrets/secret", json=put_payload).status_code == 200
    del_payload = {"scope": "my-scope", "key": "api_key"}
    assert client.request("DELETE", "/api/v1/secrets/secret", json=del_payload).status_code == 200


def test_list_secrets(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"secrets": []}
    response = client.get("/api/v1/secrets/secrets", params={"scope": "my-scope"})
    assert response.status_code == 200


# --- Permissions ---


def test_get_permissions(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"access_control_list": []}
    response = client.get("/api/v1/permissions/jobs/123")
    assert response.status_code == 200


def test_grant_and_revoke_permission(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"access_control_list": []}
    fake_client.put.return_value = {}
    grant_payload = {
        "object_type": "jobs",
        "object_id": "123",
        "principal": "user@example.com",
        "permission_level": "CAN_MANAGE",
    }
    assert client.post("/api/v1/permissions/grant", json=grant_payload).status_code == 200
    revoke_payload = {"object_type": "jobs", "object_id": "123", "principal": "user@example.com"}
    assert client.post("/api/v1/permissions/revoke", json=revoke_payload).status_code == 200


# --- Unity Catalog ---


def test_list_catalogs(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"catalogs": []}
    response = client.get("/api/v1/unity-catalog/catalogs")
    assert response.status_code == 200


def test_create_and_get_catalog(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"name": "main"}
    fake_client.get.return_value = {"name": "main"}
    assert client.post("/api/v1/unity-catalog/catalogs", json={"name": "main"}).status_code == 200
    assert client.get("/api/v1/unity-catalog/catalogs/main").status_code == 200


def test_list_schemas_tables_volumes_functions(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"items": []}
    assert client.get("/api/v1/unity-catalog/schemas", params={"catalog_name": "main"}).status_code == 200
    assert (
        client.get(
            "/api/v1/unity-catalog/tables", params={"catalog_name": "main", "schema_name": "default"}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/unity-catalog/volumes", params={"catalog_name": "main", "schema_name": "default"}
        ).status_code
        == 200
    )
    assert (
        client.get(
            "/api/v1/unity-catalog/functions", params={"catalog_name": "main", "schema_name": "default"}
        ).status_code
        == 200
    )


def test_uc_permissions_and_grants(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {}
    fake_client.patch.return_value = {}
    assert client.get("/api/v1/unity-catalog/permissions/table/main.default.t1").status_code == 200
    assert (
        client.request(
            "PATCH", "/api/v1/unity-catalog/permissions/table/main.default.t1", json=[]
        ).status_code
        == 200
    )
    assert client.get("/api/v1/unity-catalog/grants/table/main.default.t1").status_code == 200


def test_external_locations_and_storage_credentials(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    fake_client.get.return_value = {"external_locations": []}
    fake_client.post.return_value = {}
    assert client.get("/api/v1/unity-catalog/external-locations").status_code == 200
    assert client.post("/api/v1/unity-catalog/external-locations", json={"name": "loc1"}).status_code == 200
    fake_client.get.return_value = {"storage_credentials": []}
    assert client.get("/api/v1/unity-catalog/storage-credentials").status_code == 200


# --- Monitoring ---


def test_cluster_and_job_metrics(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"clusters": [], "jobs": []}
    assert client.get("/api/v1/monitoring/metrics/clusters").status_code == 200
    assert client.get("/api/v1/monitoring/metrics/jobs").status_code == 200


def test_cluster_and_job_health(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"state": "RUNNING", "runs": []}
    assert client.get("/api/v1/monitoring/health/cluster/abc").status_code == 200
    assert client.get("/api/v1/monitoring/health/job/1").status_code == 200


def test_connector_info_and_config(client: TestClient) -> None:
    assert client.get("/api/v1/monitoring/connector/info").status_code == 200
    assert client.get("/api/v1/monitoring/connector/config").status_code == 200


def test_list_catalogs_with_pagination(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"catalogs": []}
    response = client.get("/api/v1/unity-catalog/catalogs", params={"max_results": 10, "page_token": "tok"})
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["max_results"] == 10
    assert kwargs["params"]["page_token"] == "tok"


def test_list_tables_with_pagination(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"tables": []}
    response = client.get(
        "/api/v1/unity-catalog/tables",
        params={"catalog_name": "main", "schema_name": "default", "max_results": 5},
    )
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["max_results"] == 5
