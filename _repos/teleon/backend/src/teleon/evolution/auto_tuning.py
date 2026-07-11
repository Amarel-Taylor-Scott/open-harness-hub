"""src.teleon.evolution.auto_tuning — automated SETUP TUNING for any agentic task.

Generalizes the document-extraction cascade: any task with tiered method options (deterministic → small model →
frontier LLM) of differing cost + a measurable requirement can be auto-tuned — walk the tiers cheapest-first,
escalate only as far as the requirement forces, and pick the cheapest variation that meets it. Reads
_repos/shared-backend-components/architecture/tunable_task_catalog.json. Pure + deterministic; the plan is evidence, never truth (serves_truth False).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

_CATALOG = _resource("architecture") / "tunable_task_catalog.json"


def load_catalog() -> dict:
    return json.loads(_CATALOG.read_text())


def get_task(task_id: str) -> dict | None:
    return next((t for t in load_catalog()["tasks"] if t["task_id"] == task_id), None)


def tuning_ladder(task: dict) -> list[dict]:
    """The task's method tiers, cheapest-first (the escalation order)."""
    return sorted(task["tiers"], key=lambda t: (t["cost_rank"], t["tier"]))


def auto_tune_setup(task_id: str, *, available_keys: tuple = (), require_deterministic: bool = False) -> dict:
    """The automated setup plan for a task: the reachable tiers (filtered by available keys), cheapest-first, the
    deterministic floor, and whether the task can complete on deterministic tiers alone."""
    task = get_task(task_id)
    if not task:
        return {"task_id": task_id, "error": "unknown task", "serves_truth": False}
    have = {k.upper() for k in available_keys}
    reachable = [t for t in tuning_ladder(task)
                 if set(k.upper() for k in t["requires_keys"]) <= have
                 and (t["deterministic"] if require_deterministic else True)]
    det_tiers = [t["tier"] for t in reachable if t["deterministic"]]
    return {
        "task_id": task_id, "objective": task["objective"], "requirement_metric": task["requirement_metric"],
        "escalation_order": [t["tier"] for t in reachable],     # try cheapest-first, escalate only if unmet
        "cheapest_tier": reachable[0]["tier"] if reachable else None,
        "deterministic_floor": det_tiers[0] if det_tiers else None,
        "can_complete_deterministically": bool(task["deterministic_possible"] and det_tiers),
        "excluded_for_missing_keys": [t["tier"] for t in tuning_ladder(task)
                                      if not set(k.upper() for k in t["requires_keys"]) <= have],
        "serves_truth": False,
    }
