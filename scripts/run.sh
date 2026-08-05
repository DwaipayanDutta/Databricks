#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# No PYTHONPATH hack needed: databricks_connector is a proper installed
# package (`pip install -e .`), importable from anywhere.
python -m databricks_connector.main
