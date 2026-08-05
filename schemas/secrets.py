"""Schemas for the Secrets API."""

from __future__ import annotations

from pydantic import BaseModel


class CreateScopeRequest(BaseModel):
    scope: str
    initial_manage_principal: str | None = "users"
    backend_type: str = "DATABRICKS"


class DeleteScopeRequest(BaseModel):
    scope: str


class PutSecretRequest(BaseModel):
    scope: str
    key: str
    string_value: str | None = None
    bytes_value: str | None = None  # base64


class DeleteSecretRequest(BaseModel):
    scope: str
    key: str


class ListSecretsRequest(BaseModel):
    scope: str
