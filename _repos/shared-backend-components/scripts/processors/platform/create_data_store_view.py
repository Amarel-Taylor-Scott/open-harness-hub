#!/usr/bin/env python3
"""Backs ``processor/create-data-store-view``. Canonical wiring: the manifest
``_repos/shared-backend-components/catalog/processors/platform/create-data-store-view.yaml`` (process_kind
``platform.create_data_store``). This planner derives a deterministic store id
and a view definition (column projection from the declared schema) over a set of
rows; it materializes nothing live (the manifest is the contract).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    as_rows,
    content_address,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "platform.create_data_store"


def _columns(schema: Any) -> list[str]:
    if isinstance(schema, dict):
        cols = schema.get("columns")
        if isinstance(cols, list):
            return [str(col.get("name") if isinstance(col, dict) else col) for col in cols]
        if isinstance(schema.get("properties"), dict):
            return sorted(schema["properties"].keys())
    return []


def run(rows: Any, schema: Any) -> dict[str, Any]:
    """Plan a queryable data store + view over ``rows`` per ``schema``.

    Returns ``{store_id, view}``.
    """
    require(schema, "schema")
    row_list = as_rows(rows)
    columns = _columns(schema)
    store_id_value = content_address("data-store", {"schema": schema, "row_count": len(row_list)})
    store_id = plan_row(
        action=PROCESS_KIND,
        target=store_id_value,
        payload=row_list,
        extra={"store_id": store_id_value, "row_count": len(row_list), "columns": columns},
    )
    view = plan_row(
        action=PROCESS_KIND + ".view",
        target=store_id_value,
        payload={"columns": columns},
        extra={
            "view_id": content_address("data-store-view", {"store": store_id_value, "columns": columns}),
            "store_id": store_id_value,
            "columns": columns,
            "select": "SELECT " + (", ".join(columns) if columns else "*") + " FROM " + store_id_value,
        },
    )
    return {"store_id": store_id, "view": view}


def _self_test() -> int:
    result = run(rows=[{"a": 1, "b": 2}], schema={"columns": [{"name": "a"}, {"name": "b"}]})
    assert result["store_id"]["columns"] == ["a", "b"], result
    assert "SELECT a, b FROM" in result["view"]["select"], result
    # properties-style schema also yields columns.
    prop = run(rows=[], schema={"properties": {"x": {}, "y": {}}})
    assert prop["store_id"]["columns"] == ["x", "y"], prop
    return selftest_run(
        run, {"rows": [{"a": 1}], "schema": {"columns": [{"name": "a"}]}}, ("store_id", "view")
    )


if __name__ == "__main__":
    raise SystemExit(_self_test())
