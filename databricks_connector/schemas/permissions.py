"""Schemas for the Permissions API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    """Base for Permissions schemas: rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class AccessControlEntry(_StrictModel):
    principal: str = Field(..., description="User, group, or service principal")
    permission_level: str


class GetPermissionsRequest(_StrictModel):
    object_type: str  # e.g. "jobs", "clusters", "notebooks"
    object_id: str


class UpdatePermissionsRequest(_StrictModel):
    object_type: str
    object_id: str
    access_control_list: list[AccessControlEntry] = Field(default_factory=list)


class GrantPermissionRequest(_StrictModel):
    object_type: str
    object_id: str
    principal: str
    permission_level: str


class RevokePermissionRequest(_StrictModel):
    object_type: str
    object_id: str
    principal: str
