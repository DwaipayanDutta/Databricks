"""Schemas for the Workspace / Notebooks API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    """Base for Workspace/Notebooks request schemas: rejects unknown
    fields. Not applied to WorkspaceObjectResponse below, which mirrors
    Databricks' own (evolving) response shape."""

    model_config = ConfigDict(extra="forbid")


class ImportNotebookRequest(_StrictModel):
    path: str
    content: str  # base64-encoded content
    language: str | None = "PYTHON"
    format: str = "SOURCE"  # SOURCE, HTML, JUPYTER, DBC
    overwrite: bool = False


class ExportNotebookRequest(_StrictModel):
    path: str
    format: str = "SOURCE"


class ListWorkspaceRequest(_StrictModel):
    path: str = "/"


class DeleteWorkspaceObjectRequest(_StrictModel):
    path: str
    recursive: bool = False


class GetStatusRequest(_StrictModel):
    path: str


class CreateFolderRequest(_StrictModel):
    path: str


class MoveObjectRequest(_StrictModel):
    source_path: str
    destination_path: str


class CopyObjectRequest(_StrictModel):
    source_path: str
    destination_path: str
    overwrite: bool = False


class WorkspaceObjectResponse(BaseModel):
    path: str
    object_type: str | None = None
    object_id: int | None = None
    language: str | None = None

    model_config = ConfigDict(extra="allow")
