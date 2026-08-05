"""Schemas for the Secrets API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    """Base for Secrets schemas: rejects unknown fields."""

    model_config = ConfigDict(extra="forbid")


class CreateScopeRequest(_StrictModel):
    scope: str
    initial_manage_principal: str | None = "users"
    backend_type: str = "DATABRICKS"


class DeleteScopeRequest(_StrictModel):
    scope: str


class PutSecretRequest(_StrictModel):
    scope: str
    key: str
    string_value: str | None = None
    bytes_value: str | None = None  # base64


class DeleteSecretRequest(_StrictModel):
    scope: str
    key: str


class ListSecretsRequest(_StrictModel):
    scope: str
