#!/usr/bin/env python3
"""Backs ``processor/register-component``. Canonical wiring: the manifest
``catalog/processors/platform/register-component.yaml`` (process_kind
``platform.register_component``). This planner derives a deterministic component
id for a validated result plus its manifest, carrying provenance; it does not
write to the live registry — registration is an approved promotion step
elsewhere (the manifest is the source of truth, and CLAUDE.md's promotion
boundary forbids auto-activation).
"""
from __future__ import annotations

from typing import Any

from scripts.processors.platform._platform_base import (
    content_hash,
    plan_row,
    require,
    selftest_run,
)

PROCESS_KIND = "platform.register_component"


def run(result: Any, manifest: Any) -> dict[str, Any]:
    """Plan registration of ``result`` as a versioned component. Returns ``{component_id}``."""
    require(result, "result")
    require(manifest, "manifest")
    # Prefer the manifest's declared id; else derive a candidate id from content.
    declared = manifest.get("id") if isinstance(manifest, dict) else None
    if declared:
        component_id_value = str(declared)
    else:
        digest = content_hash({"result": result, "manifest": manifest}).split(":", 1)[1]
        component_id_value = f"component/candidate-{digest[:16]}"
    plan = plan_row(
        action=PROCESS_KIND,
        target=component_id_value,
        payload={"result": result, "manifest": manifest},
        extra={
            "component_id": component_id_value,
            "result_hash": content_hash(result),
            "manifest_hash": content_hash(manifest),
            # Honest: a registration plan is a CANDIDATE, never auto-active.
            "promotion_state": "candidate",
        },
    )
    return {"component_id": plan}


def _self_test() -> int:
    # Declared id is honored; promotion_state stays candidate (honest).
    declared = run(result={"fact": "x"}, manifest={"id": "component/foo"})
    assert declared["component_id"]["component_id"] == "component/foo", declared
    assert declared["component_id"]["promotion_state"] == "candidate", declared
    # No id -> derived candidate id.
    derived = run(result={"fact": "y"}, manifest={"name": "no-id"})
    assert derived["component_id"]["component_id"].startswith("component/candidate-"), derived
    return selftest_run(
        run, {"result": {"fact": "x"}, "manifest": {"id": "component/foo"}}, ("component_id",)
    )


if __name__ == "__main__":
    raise SystemExit(_self_test())
