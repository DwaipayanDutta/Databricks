"""Schemas for the DBFS API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    """Base for DBFS schemas: rejects unknown fields (path-based requests
    benefit especially from this -- a typo'd extra field should fail loudly
    rather than being silently ignored)."""

    model_config = ConfigDict(extra="forbid")


class DbfsPathRequest(_StrictModel):
    path: str


class DbfsMkdirRequest(_StrictModel):
    path: str


class DbfsMoveRequest(_StrictModel):
    source_path: str
    destination_path: str


class DbfsDeleteRequest(_StrictModel):
    path: str
    recursive: bool = False


class DbfsPutRequest(_StrictModel):
    path: str
    contents: str  # base64-encoded
    overwrite: bool = True


class DbfsCreateRequest(_StrictModel):
    path: str
    overwrite: bool = True


class DbfsAddBlockRequest(_StrictModel):
    handle: int
    data: str  # base64-encoded chunk


class DbfsCloseRequest(_StrictModel):
    handle: int


class DbfsReadRequest(_StrictModel):
    path: str
    offset: int = 0
    length: int = 1024 * 1024
