"""Router for the DBFS API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.client import DatabricksClient, get_databricks_client
from schemas.dbfs import (
    DbfsDeleteRequest,
    DbfsMkdirRequest,
    DbfsMoveRequest,
    DbfsPutRequest,
)
from services.dbfs_service import DbfsService

router = APIRouter(prefix="/api/v1/dbfs", tags=["DBFS"])


def get_dbfs_service(client: DatabricksClient = Depends(get_databricks_client)) -> DbfsService:
    return DbfsService(client)


@router.get("/list", summary="List directory", description="List the contents of a DBFS directory.")
async def list_dir(
    path: str = Query(...), service: DbfsService = Depends(get_dbfs_service)
) -> dict[str, Any]:
    return await service.list_dir(path)


@router.post(
    "/upload",
    summary="Upload file",
    description="Upload a small file to DBFS (single-request, base64 contents).",
)
async def upload(body: DbfsPutRequest, service: DbfsService = Depends(get_dbfs_service)) -> dict[str, Any]:
    return await service.put(body.path, body.contents, body.overwrite)


@router.get(
    "/download",
    summary="Download file",
    description="Download a file from DBFS, paging through large files automatically.",
)
async def download(
    path: str = Query(...), service: DbfsService = Depends(get_dbfs_service)
) -> dict[str, Any]:
    return await service.download_file(path)


@router.post("/delete", summary="Delete path", description="Delete a file or directory from DBFS.")
async def delete(body: DbfsDeleteRequest, service: DbfsService = Depends(get_dbfs_service)) -> dict[str, Any]:
    return await service.delete(body.path, body.recursive)


@router.post("/move", summary="Move path", description="Move/rename a file or directory within DBFS.")
async def move(body: DbfsMoveRequest, service: DbfsService = Depends(get_dbfs_service)) -> dict[str, Any]:
    return await service.move(body.source_path, body.destination_path)


@router.post("/mkdir", summary="Make directory", description="Create a directory (and parents) in DBFS.")
async def mkdir(body: DbfsMkdirRequest, service: DbfsService = Depends(get_dbfs_service)) -> dict[str, Any]:
    return await service.mkdirs(body.path)


@router.get(
    "/read", summary="Read raw block", description="Read a raw block of bytes from a file (base64-encoded)."
)
async def read(
    path: str = Query(...),
    offset: int = Query(default=0, ge=0),
    length: int = Query(default=1024 * 1024, ge=1, le=1024 * 1024),
    service: DbfsService = Depends(get_dbfs_service),
) -> dict[str, Any]:
    return await service.read(path, offset, length)


@router.post(
    "/put", summary="Put small file", description="Convenience single-request upload identical to /upload."
)
async def put(body: DbfsPutRequest, service: DbfsService = Depends(get_dbfs_service)) -> dict[str, Any]:
    return await service.put(body.path, body.contents, body.overwrite)


@router.post(
    "/create",
    summary="Create streaming handle",
    description="Open a streaming upload handle for a large file.",
)
async def create(
    path: str = Query(...),
    overwrite: bool = Query(default=True),
    service: DbfsService = Depends(get_dbfs_service),
) -> dict[str, Any]:
    return await service.create(path, overwrite)
