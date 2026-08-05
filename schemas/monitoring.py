"""Schemas for the Monitoring API."""

from __future__ import annotations

from pydantic import BaseModel


class ClusterHealthRequest(BaseModel):
    cluster_id: str


class JobHealthRequest(BaseModel):
    job_id: int


class ConnectorInfoResponse(BaseModel):
    name: str
    version: str
    environment: str
    uptime_seconds: float
