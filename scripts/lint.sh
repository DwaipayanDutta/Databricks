#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Running ruff..."
ruff check .
echo "Running mypy..."
mypy .
