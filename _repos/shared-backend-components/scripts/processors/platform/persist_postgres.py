#!/usr/bin/env python3
"""Backs ``processor/persist-postgres``. Canonical wiring: the manifest
``_repos/shared-backend-components/catalog/processors/platform/persist-postgres.yaml`` (process_kind
``platform.postgres_upsert``). This planner builds a deterministic, content-hash
idempotent upsert plan for structured rows into a named table; it does not open
a database connection (one source of truth for the contract is the manifest).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    as_rows,
    content_address,
    content_hash,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "platform.postgres_upsert"


def run(rows: Any, table: Any) -> dict[str, Any]:
    """Plan an idempotent upsert of ``rows`` into ``table``. Returns ``{upserted}``."""
    require(table, "table")
    table_name = table.get("name") if isinstance(table, dict) else str(table)
    require(table_name, "table.name")
    row_list = as_rows(rows)
    planned = [
        {"row_hash": content_hash(row), "row": row}
        for row in row_list
    ]
    upserted = plan_row(
        action=PROCESS_KIND,
        target=str(table_name),
        payload=row_list,
        extra={
            "upsert_id": content_address("postgres-upsert", {"table": table_name, "rows": row_list}),
            "row_count": len(row_list),
            "rows": planned,
            "conflict_strategy": "content_hash_idempotent",
        },
    )
    return {"upserted": upserted}


def _self_test() -> int:
    result = run(rows=[{"id": "a", "v": 1}, {"id": "b", "v": 2}], table={"name": "facts"})
    assert result["upserted"]["row_count"] == 2, result
    assert result["upserted"]["conflict_strategy"] == "content_hash_idempotent", result
    return selftest_run(run, {"rows": [{"id": "a"}], "table": {"name": "facts"}}, ("upserted",))


if __name__ == "__main__":
    raise SystemExit(_self_test())
