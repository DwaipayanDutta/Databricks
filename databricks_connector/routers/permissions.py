"""Router for the generic Permissions API (jobs, clusters, notebooks, etc.)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.schemas.permissions import (
    GrantPermissionRequest,
    RevokePermissionRequest,
    UpdatePermissionsRequest,
)
from databricks_connector.services.permissions_service import PermissionsService

router = APIRouter(prefix="/api/v1/permissions", tags=["Permissions"])


def get_permissions_service(client: DatabricksClient = Depends(get_databricks_client)) -> PermissionsService:
    return PermissionsService(client)


@router.get(
    "/{object_type}/{object_id}",
    summary="Get permissions",
    description="Get the access control list for a Databricks object (e.g. jobs, clusters, notebooks).",
)
async def get_permissions(
    object_type: str, object_id: str, service: PermissionsService = Depends(get_permissions_service)
) -> dict[str, Any]:
    return await service.get_permissions(object_type, object_id)


@router.put(
    "/{object_type}/{object_id}",
    summary="Update ACL",
    description="Replace the full access control list for a Databricks object.",
)
async def update_permissions(
    object_type: str,
    object_id: str,
    body: UpdatePermissionsRequest,
    service: PermissionsService = Depends(get_permissions_service),
) -> dict[str, Any]:
    return await service.update_permissions(object_type, object_id, body.to_wire_acl())


@router.post(
    "/grant", summary="Grant permission", description="Grant a permission level to a principal on an object."
)
async def grant_permission(
    body: GrantPermissionRequest, service: PermissionsService = Depends(get_permissions_service)
) -> dict[str, Any]:
    return await service.grant_permission(
        body.object_type, body.object_id, body.principal, body.permission_level
    )


@router.post(
    "/revoke", summary="Revoke permission", description="Revoke all permissions for a principal on an object."
)
async def revoke_permission(
    body: RevokePermissionRequest, service: PermissionsService = Depends(get_permissions_service)
) -> dict[str, Any]:
    return await service.revoke_permission(body.object_type, body.object_id, body.principal)
