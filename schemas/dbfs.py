"""Schemas for the DBFS API."""

from __future__ import annotations

from pydantic import BaseModel


class DbfsPathRequest(BaseModel):
    path: str


class DbfsMkdirRequest(BaseModel):
    path: str


class DbfsMoveRequest(BaseModel):
    source_path: str
    destination_path: str


class DbfsDeleteRequest(BaseModel):
    path: str
    recursive: bool = False


class DbfsPutRequest(BaseModel):
    path: str
    contents: str  # base64-encoded
    overwrite: bool = True


class DbfsCreateRequest(BaseModel):
    path: str
    overwrite: bool = True


class DbfsAddBlockRequest(BaseModel):
    handle: int
    data: str  # base64-encoded chunk


class DbfsCloseRequest(BaseModel):
    handle: int


class DbfsReadRequest(BaseModel):
    path: str
    offset: int = 0
    length: int = 1024 * 1024
