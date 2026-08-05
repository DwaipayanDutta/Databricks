"""Schemas for the Workspace / Notebooks API."""

from __future__ import annotations

from pydantic import BaseModel


class ImportNotebookRequest(BaseModel):
    path: str
    content: str  # base64-encoded content
    language: str | None = "PYTHON"
    format: str = "SOURCE"  # SOURCE, HTML, JUPYTER, DBC
    overwrite: bool = False


class ExportNotebookRequest(BaseModel):
    path: str
    format: str = "SOURCE"


class ListWorkspaceRequest(BaseModel):
    path: str = "/"


class DeleteWorkspaceObjectRequest(BaseModel):
    path: str
    recursive: bool = False


class GetStatusRequest(BaseModel):
    path: str


class CreateFolderRequest(BaseModel):
    path: str


class MoveObjectRequest(BaseModel):
    source_path: str
    destination_path: str


class CopyObjectRequest(BaseModel):
    source_path: str
    destination_path: str
    overwrite: bool = False


class WorkspaceObjectResponse(BaseModel):
    path: str
    object_type: str | None = None
    object_id: int | None = None
    language: str | None = None

    model_config = {"extra": "allow"}
