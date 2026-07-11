#!/usr/bin/env python3
"""Backs ``processor/persist-run-store``. Canonical wiring: the manifest
``_repos/shared-backend-components/catalog/processors/platform/persist-run-store.yaml`` (process_kind
``audit.trace``). This planner assigns a deterministic, content-addressed run id
to a run object (steps, cost, citations) so the trace is replayable and
idempotent; it writes nothing (the manifest is the source of truth).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_address,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "audit.trace"


def run(run: Any) -> dict[str, Any]:
    """Plan persistence of a ``run`` object as a replayable trace. Returns ``{run_id}``."""
    require(run, "run")
    # Honor an explicit run id if present; otherwise derive one from content.
    explicit = run.get("run_id") if isinstance(run, dict) else None
    run_id_value = str(explicit) if explicit else content_address("run", run)
    plan = plan_row(
        action=PROCESS_KIND,
        target=run_id_value,
        payload=run,
        extra={
            "run_id": run_id_value,
            "step_count": len(run.get("steps", [])) if isinstance(run, dict) else 0,
            "replayable": True,
        },
    )
    return {"run_id": plan}


def _self_test() -> int:
    # Explicit run_id is honored.
    explicit = run(run={"run_id": "run/abc", "steps": [1, 2]})
    assert explicit["run_id"]["run_id"] == "run/abc", explicit
    assert explicit["run_id"]["step_count"] == 2, explicit
    # Derived run_id is content-addressed + deterministic.
    return selftest_run(run, {"run": {"steps": [1], "cost": 0.1}}, ("run_id",))


if __name__ == "__main__":
    raise SystemExit(_self_test())
