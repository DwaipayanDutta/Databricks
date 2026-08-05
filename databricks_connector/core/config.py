"""Centralized configuration for the Databricks connector.

Configuration is loaded from environment variables (optionally via a .env
file). Pydantic's BaseSettings gives us validation and type coercion for
free, and a single Settings object is shared across the app via
functools.lru_cache so environment variables are only parsed once.
"""

from __future__ import annotations

from enum import StrEnum
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthMode(StrEnum):
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

    # --- HTTP connection pooling ---
    http_max_connections: int = Field(
        default=100, description="Max total concurrent connections in the pool."
    )
    http_max_keepalive_connections: int = Field(
        default=20, description="Max idle keep-alive connections retained in the pool."
    )
    http_keepalive_expiry_seconds: float = Field(
        default=30.0, description="How long an idle keep-alive connection is kept open."
    )

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

    # --- DBFS ---
    dbfs_download_max_bytes: int = Field(
        default=256 * 1024 * 1024,
        description=(
            "Refuse to buffer a DBFS /download response larger than this "
            "many bytes. The response is returned as a single in-memory "
            "JSON payload (never streamed to the caller), so an unbounded "
            "download is a real memory-exhaustion risk for any caller who "
            "can point this endpoint at a large file."
        ),
    )

    # --- Security ---
    connector_api_key: str | None = Field(
        default=None,
        description="Optional API key required to call this connector's own endpoints.",
    )

    @model_validator(mode="after")
    def _validate_auth_fields(self) -> Settings:
        """Fail fast at startup if the fields required for the selected
        `auth_mode` are missing, instead of only discovering it on the
        first real request (when `AuthManager` builds its `TokenProvider`).

        `Settings` is constructed once, eagerly, at import time (see
        `get_settings()` below and its call site in `app.py`), so a
        `ValueError` raised here surfaces immediately when the process
        starts -- before it ever accepts traffic.
        """
        mode = self.auth_mode
        missing: list[str] = []

        if mode == AuthMode.PAT and not self.databricks_token:
            missing.append("DATABRICKS_TOKEN")
        elif mode == AuthMode.BEARER and not self.bearer_token:
            missing.append("BEARER_TOKEN")
        elif mode == AuthMode.OAUTH:
            if not self.databricks_client_id:
                missing.append("DATABRICKS_CLIENT_ID")
            if not self.databricks_client_secret:
                missing.append("DATABRICKS_CLIENT_SECRET")
        elif mode == AuthMode.AZURE_SERVICE_PRINCIPAL:
            if not self.azure_tenant_id:
                missing.append("AZURE_TENANT_ID")
            if not self.azure_client_id:
                missing.append("AZURE_CLIENT_ID")
            if not self.azure_client_secret:
                missing.append("AZURE_CLIENT_SECRET")
        # AuthMode.MANAGED_IDENTITY has no required fields (the system-
        # assigned identity is used when azure_managed_identity_client_id
        # is unset).

        if missing:
            raise ValueError(
                f"AUTH_MODE={mode.value!r} requires the following environment "
                f"variable(s), which are missing or empty: {', '.join(missing)}"
            )

        if not self.databricks_host or not self.databricks_host.startswith(("http://", "https://")):
            raise ValueError(
                "DATABRICKS_HOST must be set to a full URL, e.g. "
                "'https://your-workspace.cloud.databricks.com' "
                f"(got: {self.databricks_host!r})"
            )

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
