"""Service layer for Secrets: /api/2.0/secrets"""

from __future__ import annotations

from typing import Any

from core.client import DatabricksClient

_BASE = "/api/2.0/secrets"


class SecretsService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def list_scopes(self) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/scopes/list")

    async def create_scope(
        self, scope: str, initial_manage_principal: str | None, backend_type: str
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"scope": scope, "backend_type": backend_type}
        if initial_manage_principal:
            body["initial_manage_principal"] = initial_manage_principal
        return await self._client.post(f"{_BASE}/scopes/create", json_body=body)

    async def delete_scope(self, scope: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/scopes/delete", json_body={"scope": scope})

    async def put_secret(
        self, scope: str, key: str, string_value: str | None, bytes_value: str | None
    ) -> dict[str, Any]:
        body: dict[str, Any] = {"scope": scope, "key": key}
        if string_value is not None:
            body["string_value"] = string_value
        if bytes_value is not None:
            body["bytes_value"] = bytes_value
        return await self._client.post(f"{_BASE}/put", json_body=body)

    async def delete_secret(self, scope: str, key: str) -> dict[str, Any]:
        return await self._client.post(f"{_BASE}/delete", json_body={"scope": scope, "key": key})

    async def list_secrets(self, scope: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/list", params={"scope": scope})

    async def list_acls(self, scope: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/acls/list", params={"scope": scope})

    async def put_acl(self, scope: str, principal: str, permission: str) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/acls/put", json_body={"scope": scope, "principal": principal, "permission": permission}
        )

    async def delete_acl(self, scope: str, principal: str) -> dict[str, Any]:
        return await self._client.post(
            f"{_BASE}/acls/delete", json_body={"scope": scope, "principal": principal}
        )
