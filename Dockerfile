# ============================================================
# Databricks Connector - Production Dockerfile
# Multi-stage build: slim runtime image, non-root user.
# The connector is installed as a proper Python package
# (`pip install .`), so it is importable as `databricks_connector`
# regardless of the container's working directory.
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY pyproject.toml setup.py requirements.txt ./
COPY databricks_connector/ ./databricks_connector/
COPY README.md ./

# Installs the `cache` extra (redis client) alongside the base package so
# CACHE_ENABLED=true + REDIS_URL works out of the box in the runtime image.
# Without this, CacheClient silently falls back to the in-memory backend
# (RedisCache's `import redis` raises ImportError, which is caught) even
# though docker-compose.yml provisions a Redis service to be used.
RUN pip install --user --no-cache-dir ".[cache]"


FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 connector \
    && useradd --uid 1000 --gid connector --shell /bin/bash --create-home connector

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/connector/.local/bin:$PATH

COPY --from=builder --chown=connector:connector /root/.local /home/connector/.local

USER connector

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request,sys; sys.exit(0 if urllib.request.urlopen(f'http://localhost:{os.environ.get(\"PORT\", 8000)}/live', timeout=3).status==200 else 1)"

# Shell form (not exec-array form) so HOST/PORT/UVICORN_WORKERS env vars are
# actually honored at container start -- the array form below previously
# hardcoded 0.0.0.0:8000/2 workers regardless of what Settings/.env
# configured. `exec` replaces the shell process so uvicorn still receives
# SIGTERM directly (graceful shutdown via app.py's lifespan hook still
# works exactly as with the array form).
CMD exec uvicorn databricks_connector.main:app \
    --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}" --workers "${UVICORN_WORKERS:-2}"
