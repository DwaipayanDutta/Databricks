#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="${PYTHONPATH:-.}"
pytest -v --cov=core --cov=services --cov=routers --cov-report=term-missing
