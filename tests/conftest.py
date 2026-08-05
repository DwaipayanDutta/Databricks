"""Shared pytest fixtures.

Tests never call the real Databricks API. Instead, we override the
`get_databricks_client` FastAPI dependency with a fake client whose HTTP
verbs are AsyncMock-backed, so we assert on *what* was requested rather than
performing real network I/O.
"""

from __future__ import annotations

import os
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATABRICKS_HOST", "https://example.cloud.databricks.com")
os.environ.setdefault("DATABRICKS_TOKEN", "dummy-token-for-tests")
os.environ.setdefault("AUTH_MODE", "pat")

from app import create_app  # noqa: E402
from core.client import get_databricks_client  # noqa: E402


class FakeDatabricksClient:
    """A stand-in for DatabricksClient with AsyncMock verb methods."""

    def __init__(self) -> None:
        self.get = AsyncMock(return_value={})
        self.post = AsyncMock(return_value={})
        self.put = AsyncMock(return_value={})
        self.patch = AsyncMock(return_value={})
        self.delete = AsyncMock(return_value={})

    async def aclose(self) -> None:
        return None


@pytest.fixture
def fake_client() -> FakeDatabricksClient:
    return FakeDatabricksClient()


@pytest.fixture
def client(fake_client: FakeDatabricksClient) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_databricks_client] = lambda: fake_client
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
