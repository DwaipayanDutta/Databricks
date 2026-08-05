"""Schemas for the Permissions API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AccessControlEntry(BaseModel):
    principal: str = Field(..., description="User, group, or service principal")
    permission_level: str


class GetPermissionsRequest(BaseModel):
    object_type: str  # e.g. "jobs", "clusters", "notebooks"
    object_id: str


class UpdatePermissionsRequest(BaseModel):
    object_type: str
    object_id: str
    access_control_list: list[AccessControlEntry] = Field(default_factory=list)


class GrantPermissionRequest(BaseModel):
    object_type: str
    object_id: str
    principal: str
    permission_level: str


class RevokePermissionRequest(BaseModel):
    object_type: str
    object_id: str
    principal: str
