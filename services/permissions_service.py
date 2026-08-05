"""Service layer for Permissions: /api/2.0/permissions"""

from __future__ import annotations

from typing import Any

from core.client import DatabricksClient

_BASE = "/api/2.0/permissions"


class PermissionsService:
    def __init__(self, client: DatabricksClient) -> None:
        self._client = client

    async def get_permissions(self, object_type: str, object_id: str) -> dict[str, Any]:
        return await self._client.get(f"{_BASE}/{object_type}/{object_id}")

    async def update_permissions(
        self, object_type: str, object_id: str, access_control_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        return await self._client.put(
            f"{_BASE}/{object_type}/{object_id}", json_body={"access_control_list": access_control_list}
        )

    async def grant_permission(
        self, object_type: str, object_id: str, principal: str, permission_level: str
    ) -> dict[str, Any]:
        current = await self.get_permissions(object_type, object_id)
        acl = current.get("access_control_list", [])
        acl.append({"user_name": principal, "permission_level": permission_level})
        return await self.update_permissions(object_type, object_id, acl)

    async def revoke_permission(self, object_type: str, object_id: str, principal: str) -> dict[str, Any]:
        current = await self.get_permissions(object_type, object_id)
        acl = [
            entry
            for entry in current.get("access_control_list", [])
            if entry.get("user_name") != principal and entry.get("group_name") != principal
        ]
        return await self.update_permissions(object_type, object_id, acl)
