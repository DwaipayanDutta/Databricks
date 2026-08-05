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

RUN pip install --user --no-cache-dir .


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
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/live', timeout=3).status==200 else 1)"

CMD ["uvicorn", "databricks_connector.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
