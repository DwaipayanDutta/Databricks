"""Router for the Secrets API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from databricks_connector.core.client import DatabricksClient, get_databricks_client
from databricks_connector.schemas.secrets import (
    CreateScopeRequest,
    DeleteAclRequest,
    DeleteScopeRequest,
    DeleteSecretRequest,
    PutAclRequest,
    PutSecretRequest,
)
from databricks_connector.services.secrets_service import SecretsService

router = APIRouter(prefix="/api/v1/secrets", tags=["Secrets"])


def get_secrets_service(client: DatabricksClient = Depends(get_databricks_client)) -> SecretsService:
    return SecretsService(client)


@router.get("/scopes", summary="List scopes", description="List all secret scopes.")
async def list_scopes(service: SecretsService = Depends(get_secrets_service)) -> dict[str, Any]:
    return await service.list_scopes()


@router.post("/scopes", summary="Create scope", description="Create a new secret scope.")
async def create_scope(
    body: CreateScopeRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.create_scope(body.scope, body.initial_manage_principal, body.backend_type)


@router.delete("/scopes", summary="Delete scope", description="Delete a secret scope and all its secrets.")
async def delete_scope(
    body: DeleteScopeRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.delete_scope(body.scope)


@router.put("/secret", summary="Put secret", description="Create or update a secret within a scope.")
async def put_secret(
    body: PutSecretRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.put_secret(body.scope, body.key, body.string_value, body.bytes_value)


@router.delete("/secret", summary="Delete secret", description="Delete a single secret within a scope.")
async def delete_secret(
    body: DeleteSecretRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.delete_secret(body.scope, body.key)


@router.get(
    "/secrets", summary="List secrets", description="List secret metadata (never values) within a scope."
)
async def list_secrets(
    scope: str = Query(...), service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.list_secrets(scope)


@router.get("/acls", summary="List ACLs", description="List ACLs for a secret scope.")
async def list_acls(
    scope: str = Query(...), service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.list_acls(scope)


@router.put(
    "/acls",
    summary="Put ACL",
    description="Create or overwrite a secret-scope ACL entry for a principal.",
)
async def put_acl(
    body: PutAclRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.put_acl(body.scope, body.principal, body.permission)


@router.delete("/acls", summary="Delete ACL", description="Delete a secret-scope ACL entry for a principal.")
async def delete_acl(
    body: DeleteAclRequest, service: SecretsService = Depends(get_secrets_service)
) -> dict[str, Any]:
    return await service.delete_acl(body.scope, body.principal)
