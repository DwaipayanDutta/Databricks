"""Small helpers shared across service modules.

Kept deliberately tiny and dependency-free (no DatabricksClient here) so it
can be imported by any service without risk of circular imports. Prefixed
with an underscore because it is an internal implementation detail of the
services package, not part of the connector's public surface.
"""

from __future__ import annotations

from typing import Any


def tags_dict_to_kv_list(tags: dict[str, str] | None) -> list[dict[str, str]]:
    """Convert a `{key: value}` mapping into Databricks' `[{"key": k, "value": v}, ...]`
    wire format, used by several MLflow endpoints (experiments, runs,
    registered models).

    Returns an empty list (never None) for an empty/None mapping so callers
    can always safely include the result in a request body.
    """
    if not tags:
        return []
    return [{"key": key, "value": value} for key, value in tags.items()]


def prune_none(values: dict[str, Any]) -> dict[str, Any]:
    """Drop keys whose value is None, useful when building optional request bodies."""
    return {key: value for key, value in values.items() if value is not None}
