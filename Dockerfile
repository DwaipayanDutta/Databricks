# ============================================================
# Databricks Connector - Production Dockerfile
# Multi-stage build: slim runtime image, non-root user.
# ============================================================

FROM python:3.12-slim AS builder

WORKDIR /build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 connector \
    && useradd --uid 1000 --gid connector --shell /bin/bash --create-home connector

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/connector/.local/bin:$PATH

COPY --from=builder /root/.local /home/connector/.local

COPY --chown=connector:connector . .

RUN chown -R connector:connector /app

USER connector

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/live', timeout=3).status==200 else 1)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
