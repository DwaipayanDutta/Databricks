"""Tests for the DBFS router/service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import FakeDatabricksClient


def test_list_dir(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.return_value = {"files": []}
    response = client.get("/api/v1/dbfs/list", params={"path": "/tmp"})
    assert response.status_code == 200


def test_upload(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {"path": "/tmp/file.txt", "contents": "aGVsbG8=", "overwrite": True}
    response = client.post("/api/v1/dbfs/upload", json=payload)
    assert response.status_code == 200


def test_download(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.get.side_effect = [
        {"file_size": 0},
    ]
    response = client.get("/api/v1/dbfs/download", params={"path": "/tmp/file.txt"})
    assert response.status_code == 200
    assert response.json()["file_size"] == 0


def test_delete(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/dbfs/delete", json={"path": "/tmp/file.txt", "recursive": False})
    assert response.status_code == 200


def test_mkdir(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    response = client.post("/api/v1/dbfs/mkdir", json={"path": "/tmp/newdir"})
    assert response.status_code == 200


def test_move(client: TestClient, fake_client: FakeDatabricksClient) -> None:
    fake_client.post.return_value = {}
    payload = {"source_path": "/tmp/a.txt", "destination_path": "/tmp/b.txt"}
    response = client.post("/api/v1/dbfs/move", json=payload)
    assert response.status_code == 200
