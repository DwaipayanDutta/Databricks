"""Common/shared Pydantic schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ErrorResponse(BaseModel):
    """The shape of every error body this connector returns (see
    `core.exceptions.DatabricksConnectorError.to_dict()` and
    `core.middleware.ExceptionMiddleware`). Wired into the OpenAPI schema
    as the documented response model for error status codes across every
    endpoint -- see `create_app()` in `app.py`.
    """

    model_config = ConfigDict(extra="forbid")

    error: str = Field(..., description="Machine-readable error code, e.g. 'not_found'.")
    message: str = Field(..., description="Human-readable error message.")
    details: dict[str, Any] = Field(default_factory=dict, description="Additional error context, if any.")


class HealthStatus(BaseModel):
    status: str
    version: str
    environment: str


class ReadinessStatus(BaseModel):
    status: str
    dependencies: dict[str, str] = Field(default_factory=dict)
