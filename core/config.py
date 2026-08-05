"""Centralized configuration for the Databricks connector.

Configuration is loaded from environment variables (optionally via a .env
file). Pydantic's BaseSettings gives us validation and type coercion for
free, and a single Settings object is shared across the app via
functools.lru_cache so environment variables are only parsed once.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthMode(str, Enum):
    """Supported Databricks authentication strategies."""

    PAT = "pat"
    OAUTH = "oauth"
    AZURE_SERVICE_PRINCIPAL = "azure_service_principal"
    MANAGED_IDENTITY = "managed_identity"
    BEARER = "bearer"


class Settings(BaseSettings):
    """Application settings, populated from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Application ---
    app_name: str = Field(default="databricks-connector")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")
    log_format: str = Field(default="json")

    # --- Server ---
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # --- Databricks core ---
    databricks_host: str = Field(default="https://your-workspace.cloud.databricks.com")
    databricks_account_id: str | None = Field(default=None)

    # --- Auth mode ---
    auth_mode: AuthMode = Field(default=AuthMode.PAT)

    # --- Personal Access Token ---
    databricks_token: str | None = Field(default=None)

    # --- OAuth ---
    databricks_client_id: str | None = Field(default=None)
    databricks_client_secret: str | None = Field(default=None)
    databricks_oauth_token_url: str | None = Field(default=None)
    databricks_oauth_scope: str = Field(default="all-apis")

    # --- Azure Service Principal ---
    azure_tenant_id: str | None = Field(default=None)
    azure_client_id: str | None = Field(default=None)
    azure_client_secret: str | None = Field(default=None)
    azure_resource_id: str = Field(
        default="2ff814a6-3304-4ab8-85cb-cd0e6f879c1d"
    )  # Databricks AAD resource id

    # --- Managed Identity ---
    azure_managed_identity_client_id: str | None = Field(default=None)
    azure_imds_endpoint: str = Field(default="http://169.254.169.254/metadata/identity/oauth2/token")

    # --- Bearer (static, externally minted) ---
    bearer_token: str | None = Field(default=None)

    # --- HTTP client ---
    request_timeout_seconds: float = Field(default=30.0)
    connect_timeout_seconds: float = Field(default=10.0)
    max_retries: int = Field(default=3)
    backoff_factor: float = Field(default=0.5)

    # --- Circuit breaker ---
    circuit_breaker_failure_threshold: int = Field(default=5)
    circuit_breaker_recovery_timeout: float = Field(default=30.0)

    # --- Caching ---
    cache_enabled: bool = Field(default=False)
    redis_url: str | None = Field(default=None)
    cache_ttl_seconds: int = Field(default=60)

    # --- CORS ---
    cors_allow_origins: str = Field(default="*")

    # --- Observability ---
    otel_enabled: bool = Field(default=False)
    otel_exporter_endpoint: str | None = Field(default=None)
    otel_service_name: str = Field(default="databricks-connector")

    # --- Security ---
    connector_api_key: str | None = Field(
        default=None,
        description="Optional API key required to call this connector's own endpoints.",
    )

    @model_validator(mode="after")
    def _validate_auth_fields(self) -> Settings:
        """Ensure the fields required for the selected auth mode are present.

        We only warn via exception at startup time (see core/auth.py) rather
        than here, to keep config loading side-effect free and testable.
        """
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_allow_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allow_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (singleton within a process)."""
    return Settings()
