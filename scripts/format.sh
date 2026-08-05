#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
echo "Running black..."
black .
echo "Running ruff --fix..."
ruff check --fix .
