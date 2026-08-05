"""Schemas for the Permissions API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    """Base for Permissions schemas: rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class AccessControlEntry(_StrictModel):
    """A single ACL entry.

    Mirrors Databricks' actual wire format for the Permissions API
    (`PUT /api/2.0/permissions/{request_object_type}/{request_object_id}`),
    which identifies the principal via exactly one of `user_name`,
    `group_name`, or `service_principal_name` -- there is no generic
    `principal` field on the real API. Sending `{"principal": ...}` instead
    of one of these three field names is silently ignored/rejected by
    Databricks, which is why this previously used a made-up `principal`
    field: verified against the current Databricks REST API reference.
    """

    user_name: str | None = Field(default=None, description="Email/username of a user.")
    group_name: str | None = Field(default=None, description="Name of a group.")
    service_principal_name: str | None = Field(
        default=None, description="Application ID of a service principal."
    )
    permission_level: str = Field(..., description="Permission level, e.g. 'CAN_MANAGE'.")

    @model_validator(mode="after")
    def _exactly_one_identity(self) -> AccessControlEntry:
        identities = [self.user_name, self.group_name, self.service_principal_name]
        provided = [value for value in identities if value]
        if len(provided) != 1:
            raise ValueError(
                "Exactly one of 'user_name', 'group_name', or 'service_principal_name' must be set."
            )
        return self


class GetPermissionsRequest(_StrictModel):
    object_type: str  # e.g. "jobs", "clusters", "notebooks"
    object_id: str


class UpdatePermissionsRequest(_StrictModel):
    object_type: str
    object_id: str
    access_control_list: list[AccessControlEntry] = Field(default_factory=list)

    def to_wire_acl(self) -> list[dict[str, Any]]:
        """Serialize `access_control_list` the way Databricks expects:
        only the identity field that's actually set, plus `permission_level`
        -- never a `None` `group_name`/`service_principal_name` alongside it.
        """
        return [entry.model_dump(exclude_none=True) for entry in self.access_control_list]


class GrantPermissionRequest(_StrictModel):
    object_type: str
    object_id: str
    principal: str
    permission_level: str


class RevokePermissionRequest(_StrictModel):
    object_type: str
    object_id: str
    principal: str
