#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pytest -v --cov=databricks_connector --cov-report=term-missing
