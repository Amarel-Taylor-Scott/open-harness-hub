#!/usr/bin/env python3
"""Backs ``processor/memory-write``. Canonical wiring: the manifest
``catalog/processors/platform/memory-write.yaml`` (process_kind
``memory.write_conversational``). This planner builds a deterministic memory
write entry for a conversational turn scoped to a session; it does not persist
to a live memory store (the manifest is the source of truth).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_address,
    content_hash,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "memory.write_conversational"


def run(turn: Any, session: Any) -> dict[str, Any]:
    """Plan a write of ``turn`` into ``session`` memory. Returns ``{written}``."""
    require(turn, "turn")
    require(session, "session")
    session_id = session.get("id") if isinstance(session, dict) else str(session)
    require(session_id, "session.id")
    written = plan_row(
        action=PROCESS_KIND,
        target=str(session_id),
        payload=turn,
        extra={
            "memory_entry_id": content_address("memory", {"session": session_id, "turn": turn}),
            "session_id": str(session_id),
            "turn_hash": content_hash(turn),
        },
    )
    return {"written": written}


def _self_test() -> int:
    result = run(turn={"role": "user", "text": "hi"}, session={"id": "sess-1"})
    assert result["written"]["session_id"] == "sess-1", result
    assert result["written"]["memory_entry_id"].startswith("memory/"), result
    return selftest_run(run, {"turn": {"text": "hi"}, "session": {"id": "s"}}, ("written",))


if __name__ == "__main__":
    raise SystemExit(_self_test())
