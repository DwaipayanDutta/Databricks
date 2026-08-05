"""Tests for the Clusters router/service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_list_clusters(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"clusters": [{"cluster_id": "abc"}]}
    response = client.get("/api/v1/clusters")
    assert response.status_code == 200
    assert response.json()["clusters"][0]["cluster_id"] == "abc"


def test_create_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"cluster_id": "new-cluster"}
    payload = {
        "cluster_name": "etl-cluster",
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
        "num_workers": 2,
    }
    response = client.post("/api/v1/clusters/create", json=payload)
    assert response.status_code == 200
    assert response.json()["cluster_id"] == "new-cluster"


def test_get_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"cluster_id": "abc", "state": "RUNNING"}
    response = client.get("/api/v1/clusters/abc")
    assert response.status_code == 200
    assert response.json()["state"] == "RUNNING"


def test_start_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/clusters/start", json={"cluster_id": "abc"})
    assert response.status_code == 200


def test_resize_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/clusters/resize", json={"cluster_id": "abc", "num_workers": 4})
    assert response.status_code == 200


def test_terminate_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/clusters/terminate", json={"cluster_id": "abc"})
    assert response.status_code == 200


def test_pin_unpin_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    assert client.post("/api/v1/clusters/pin", json={"cluster_id": "abc"}).status_code == 200
    assert client.post("/api/v1/clusters/unpin", json={"cluster_id": "abc"}).status_code == 200


def test_list_node_types(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"node_types": []}
    response = client.get("/api/v1/clusters/meta/node-types")
    assert response.status_code == 200


def test_list_clusters_with_pagination(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"clusters": [], "next_page_token": "tok"}
    response = client.get("/api/v1/clusters", params={"page_token": "abc", "limit": 10})
    assert response.status_code == 200
    _, kwargs = fake_client.get.call_args
    assert kwargs["params"]["page_token"] == "abc"
    assert kwargs["params"]["limit"] == 10


def test_get_cluster_events_uses_token_pagination(
    client: TestClient, fake_client: FakeDatabricksClient
) -> None:
    """Regression test: Databricks is deprecating limit/offset on the
    cluster events endpoint in favor of page_size/page_token."""
    fake_client.post.return_value = {"events": []}
    response = client.get("/api/v1/clusters/abc/events", params={"page_size": 25})
    assert response.status_code == 200
    _, kwargs = fake_client.post.call_args
    assert kwargs["json_body"]["page_size"] == 25
    assert "limit" not in kwargs["json_body"]
    assert "offset" not in kwargs["json_body"]


def test_resize_cluster_rejects_unknown_field(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    response = client.post(
        "/api/v1/clusters/resize", json={"cluster_id": "abc", "num_workers": 2, "bogus_field": True}
    )
    assert response.status_code == 422


def test_restart_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/clusters/restart", json={"cluster_id": "abc"})
    assert response.status_code == 200


def test_edit_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {
        "cluster_id": "abc",
        "cluster_name": "renamed",
        "spark_version": "14.3.x-scala2.12",
        "node_type_id": "i3.xlarge",
    }
    response = client.post("/api/v1/clusters/edit", json=payload)
    assert response.status_code == 200


def test_permanent_delete_cluster(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/clusters/permanent-delete", json={"cluster_id": "abc"})
    assert response.status_code == 200
    args, _ = fake_client.post.call_args
    assert args[0] == "/api/2.1/clusters/permanent-delete"


def test_list_spark_versions(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"versions": []}
    response = client.get("/api/v1/clusters/meta/spark-versions")
    assert response.status_code == 200


def test_get_cluster_events_with_time_range(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {"events": []}
    response = client.get("/api/v1/clusters/abc/events", params={"start_time": 1000, "end_time": 2000})
    assert response.status_code == 200
    _, kwargs = fake_client.post.call_args
    assert kwargs["json_body"]["start_time"] == 1000
    assert kwargs["json_body"]["end_time"] == 2000
