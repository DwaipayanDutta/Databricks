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
