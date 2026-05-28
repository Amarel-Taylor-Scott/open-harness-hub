"""Export a built flow as a portable Open Harness Hub *pipeline* component."""
from __future__ import annotations

import re
import time

# Map a component's schema type to a valid pipeline step kind.
_STEP_KIND = {
    "knowledge-pack": "knowledge_pack", "logic-pack": "knowledge_pack",
    "rule-pack": "rule_pack", "tool": "tool", "processor": "processor",
    "harness": "harness", "adapter": "adapter", "pipeline": "pipeline",
}


def _slugify(text: str) -> str:
    return (re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:48].strip("-")) or "assembled-flow"


def export_flow(result: dict) -> dict:
    """Standardize the assembled flow as a portable catalog *pipeline* component
    so a builder output round-trips back into the registry as a reusable,
    schema-validatable component. Per-component exports (MCP, Croissant, HF card,
    SPDX, …) live in scripts/emit/."""
    task = result["task"]
    steps, defaults, success = [], {}, []
    for c in result["flow"]["steps"]:
        t = c["type"]
        if t == "persona":
            defaults["persona"] = c["id"]
        elif t == "rubric":
            success.append({"rubric": c["id"], "threshold": 0.7})
        elif t in _STEP_KIND:
            steps.append({"id": c["id"].split("/")[-1], "kind": _STEP_KIND[t], "ref": c["id"]})
    spec = {
        "id": f"pipeline/{_slugify(task)}",
        "type": "pipeline",
        "version": "0.1.0",
        "name": f"Assembled flow: {task[:56]}",
        "description": f"Auto-assembled by the Open Harness Hub builder for: {task}",
        "authors": [{"name": "Open Harness Hub builder"}],
        "license": "MIT",
        "industry": ["cross_industry"],
        "capability": ["reasoning", "retrieval"],
        "modality": ["text"],
        "lifecycle": "experimental",
        "trust_boundary": "local",
        "freshness": "volatile",
        "tags": ["assembled", "builder-export"],
        "created": time.strftime("%Y-%m-%d"),
        "updated": time.strftime("%Y-%m-%d"),
        "task": task,
        "pipeline_kind": "assembled",
        "steps": steps or [{"id": "review", "kind": "harness", "ref": "harness/text-safety-review"}],
    }
    if defaults:
        spec["defaults"] = defaults
    if success:
        spec["success_criteria"] = success
    return spec
