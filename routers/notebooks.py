"""Router for the Workspace / Notebooks API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from core.client import DatabricksClient, get_databricks_client
from schemas.notebooks import (
    CopyObjectRequest,
    CreateFolderRequest,
    DeleteWorkspaceObjectRequest,
    ExportNotebookRequest,
    ImportNotebookRequest,
    MoveObjectRequest,
)
from services.notebook_service import NotebookService

router = APIRouter(prefix="/api/v1/notebooks", tags=["Workspace / Notebooks"])


def get_notebook_service(client: DatabricksClient = Depends(get_databricks_client)) -> NotebookService:
    return NotebookService(client)


@router.post(
    "/import", summary="Import notebook", description="Import a notebook (base64 content) into the workspace."
)
async def import_notebook(
    body: ImportNotebookRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.import_notebook(
        body.path, body.content, body.language or "PYTHON", body.format, body.overwrite
    )


@router.post(
    "/export", summary="Export notebook", description="Export a notebook's content in the requested format."
)
async def export_notebook(
    body: ExportNotebookRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.export_notebook(body.path, body.format)


@router.get(
    "", summary="List workspace objects", description="List notebooks/folders under a workspace path."
)
async def list_workspace(
    path: str = Query(default="/"), service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.list_workspace(path)


@router.delete("", summary="Delete workspace object", description="Delete a notebook or folder.")
async def delete_object(
    body: DeleteWorkspaceObjectRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.delete_object(body.path, body.recursive)


@router.get("/status", summary="Get object status", description="Get metadata for a workspace path.")
async def get_status(
    path: str = Query(...), service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.get_status(path)


@router.post(
    "/folders", summary="Create folder", description="Create a folder (and parents) at the given path."
)
async def create_folder(
    body: CreateFolderRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.create_folder(body.path)


@router.post("/move", summary="Move object", description="Move a notebook or folder to a new path.")
async def move_object(
    body: MoveObjectRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.move_object(body.source_path, body.destination_path)


@router.post("/copy", summary="Copy object", description="Copy a notebook to a new path.")
async def copy_object(
    body: CopyObjectRequest, service: NotebookService = Depends(get_notebook_service)
) -> dict[str, Any]:
    return await service.copy_object(body.source_path, body.destination_path, body.overwrite)
