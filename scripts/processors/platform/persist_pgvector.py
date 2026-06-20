#!/usr/bin/env python3
"""Backs ``processor/persist-pgvector``. Canonical wiring: the manifest
``catalog/processors/platform/persist-pgvector.yaml`` (process_kind
``index.update_vector``). This planner builds a deterministic upsert plan for
embedding records into a pgvector index, naming the embedder profile; it emits a
plan only and never contacts a database (the manifest is the source of truth).
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

PROCESS_KIND = "index.update_vector"


def run(records: Any, embedder: Any) -> dict[str, Any]:
    """Plan a pgvector upsert of ``records`` using ``embedder``. Returns ``{upserted}``."""
    require(embedder, "embedder")
    embedder_id = embedder.get("model") if isinstance(embedder, dict) else str(embedder)
    require(embedder_id, "embedder.model")
    record_list = as_rows(records)
    planned = [
        {"record_hash": content_hash(record), "record": record}
        for record in record_list
    ]
    upserted = plan_row(
        action=PROCESS_KIND,
        target=str(embedder_id),
        payload=record_list,
        extra={
            "upsert_id": content_address("pgvector-upsert", {"embedder": embedder_id, "records": record_list}),
            "record_count": len(record_list),
            "records": planned,
            "embedder": embedder if isinstance(embedder, dict) else {"model": embedder_id},
            "needs_embedding": True,
        },
    )
    return {"upserted": upserted}


def _self_test() -> int:
    result = run(records=[{"id": "a"}, {"id": "b"}], embedder={"model": "all-MiniLM-L6-v2"})
    assert result["upserted"]["record_count"] == 2, result
    assert result["upserted"]["needs_embedding"] is True, result
    return selftest_run(
        run, {"records": [{"id": "a"}], "embedder": {"model": "all-MiniLM-L6-v2"}}, ("upserted",)
    )


if __name__ == "__main__":
    raise SystemExit(_self_test())
