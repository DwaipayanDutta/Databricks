"""Router for Unity Catalog: catalogs, schemas, tables, volumes, functions,
permissions, grants, external locations, storage credentials."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, Query

from core.client import DatabricksClient, get_databricks_client
from services.unity_catalog_service import UnityCatalogService

router = APIRouter(prefix="/api/v1/unity-catalog", tags=["Unity Catalog"])


def get_uc_service(client: DatabricksClient = Depends(get_databricks_client)) -> UnityCatalogService:
    return UnityCatalogService(client)


# --- Catalogs ---
@router.get("/catalogs", summary="List catalogs")
async def list_catalogs(service: UnityCatalogService = Depends(get_uc_service)) -> dict[str, Any]:
    return await service.list_catalogs()


@router.post("/catalogs", summary="Create catalog")
async def create_catalog(
    body: dict[str, Any] = Body(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.create_catalog(body)


@router.get("/catalogs/{name}", summary="Get catalog")
async def get_catalog(name: str, service: UnityCatalogService = Depends(get_uc_service)) -> dict[str, Any]:
    return await service.get_catalog(name)


@router.delete("/catalogs/{name}", summary="Delete catalog")
async def delete_catalog(
    name: str, force: bool = Query(default=False), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_catalog(name, force)


# --- Schemas ---
@router.get("/schemas", summary="List schemas")
async def list_schemas(
    catalog_name: str = Query(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.list_schemas(catalog_name)


@router.post("/schemas", summary="Create schema")
async def create_schema(
    body: dict[str, Any] = Body(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.create_schema(body)


@router.get("/schemas/{full_name}", summary="Get schema")
async def get_schema(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_schema(full_name)


@router.delete("/schemas/{full_name}", summary="Delete schema")
async def delete_schema(
    full_name: str, force: bool = Query(default=False), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_schema(full_name, force)


# --- Tables ---
@router.get("/tables", summary="List tables")
async def list_tables(
    catalog_name: str = Query(...),
    schema_name: str = Query(...),
    service: UnityCatalogService = Depends(get_uc_service),
) -> dict[str, Any]:
    return await service.list_tables(catalog_name, schema_name)


@router.get("/tables/{full_name}", summary="Get table")
async def get_table(full_name: str, service: UnityCatalogService = Depends(get_uc_service)) -> dict[str, Any]:
    return await service.get_table(full_name)


@router.delete("/tables/{full_name}", summary="Delete table")
async def delete_table(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_table(full_name)


# --- Volumes ---
@router.get("/volumes", summary="List volumes")
async def list_volumes(
    catalog_name: str = Query(...),
    schema_name: str = Query(...),
    service: UnityCatalogService = Depends(get_uc_service),
) -> dict[str, Any]:
    return await service.list_volumes(catalog_name, schema_name)


@router.post("/volumes", summary="Create volume")
async def create_volume(
    body: dict[str, Any] = Body(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.create_volume(body)


@router.get("/volumes/{full_name}", summary="Get volume")
async def get_volume(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_volume(full_name)


@router.delete("/volumes/{full_name}", summary="Delete volume")
async def delete_volume(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_volume(full_name)


# --- Functions ---
@router.get("/functions", summary="List functions")
async def list_functions(
    catalog_name: str = Query(...),
    schema_name: str = Query(...),
    service: UnityCatalogService = Depends(get_uc_service),
) -> dict[str, Any]:
    return await service.list_functions(catalog_name, schema_name)


@router.get("/functions/{full_name}", summary="Get function")
async def get_function(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_function(full_name)


@router.delete("/functions/{full_name}", summary="Delete function")
async def delete_function(
    full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_function(full_name)


# --- Permissions / Grants ---
@router.get("/permissions/{securable_type}/{full_name}", summary="Get permissions")
async def get_permissions(
    securable_type: str, full_name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_permissions(securable_type, full_name)


@router.patch("/permissions/{securable_type}/{full_name}", summary="Update permissions / grants")
async def update_permissions(
    securable_type: str,
    full_name: str,
    changes: list[dict[str, Any]] = Body(...),
    service: UnityCatalogService = Depends(get_uc_service),
) -> dict[str, Any]:
    return await service.update_permissions(securable_type, full_name, changes)


@router.get("/grants/{securable_type}/{full_name}", summary="Get effective grants")
async def get_grants(
    securable_type: str,
    full_name: str,
    principal: str | None = Query(default=None),
    service: UnityCatalogService = Depends(get_uc_service),
) -> dict[str, Any]:
    return await service.get_grants(securable_type, full_name, principal)


# --- External Locations ---
@router.get("/external-locations", summary="List external locations")
async def list_external_locations(service: UnityCatalogService = Depends(get_uc_service)) -> dict[str, Any]:
    return await service.list_external_locations()


@router.post("/external-locations", summary="Create external location")
async def create_external_location(
    body: dict[str, Any] = Body(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.create_external_location(body)


@router.get("/external-locations/{name}", summary="Get external location")
async def get_external_location(
    name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_external_location(name)


@router.delete("/external-locations/{name}", summary="Delete external location")
async def delete_external_location(
    name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_external_location(name)


# --- Storage Credentials ---
@router.get("/storage-credentials", summary="List storage credentials")
async def list_storage_credentials(service: UnityCatalogService = Depends(get_uc_service)) -> dict[str, Any]:
    return await service.list_storage_credentials()


@router.post("/storage-credentials", summary="Create storage credential")
async def create_storage_credential(
    body: dict[str, Any] = Body(...), service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.create_storage_credential(body)


@router.get("/storage-credentials/{name}", summary="Get storage credential")
async def get_storage_credential(
    name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.get_storage_credential(name)


@router.delete("/storage-credentials/{name}", summary="Delete storage credential")
async def delete_storage_credential(
    name: str, service: UnityCatalogService = Depends(get_uc_service)
) -> dict[str, Any]:
    return await service.delete_storage_credential(name)
