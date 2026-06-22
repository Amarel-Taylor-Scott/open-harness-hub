"""templates — the template library (the biggest efficiency lever). Canonical typed DAG SKELETONS with named slots;
composition RETRIEVES a matching template and MUTATES its slots (fill each slot's plane with a component, drop unused
optional slots) instead of synthesizing from scratch. The honest reason: classical component synthesis scales poorly with
library size, so templates carry the common case and synthesis is the long-tail fallback. Templates are MINED from
winning traces so the library grows itself. Single source: architecture/dag_templates.json. serves_truth=false.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[3] / "architecture" / "dag_templates.json"


@lru_cache(maxsize=1)
def load_templates() -> list:
    return json.loads(_TEMPLATES.read_text())["templates"]


def _tok(s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (s or "").lower()))


def retrieve_template(query: str, *, capability_family: str | None = None) -> dict | None:
    """The best-matching template by keyword/family overlap, or None when nothing matches. Ties break by telemetry
    success_count (the library self-ranks). A matching family is worth a strong boost."""
    q = _tok(query)
    best, score = None, 0
    for t in load_templates():
        s = len(q & set(t.get("keywords", [])))
        if capability_family and t.get("capability_family") == capability_family:
            s += 3
        if s > score or (s == score and best is not None and t.get("success_count", 0) > best.get("success_count", 0)):
            best, score = t, s
    return best if score > 0 else None


def mutate(template: dict, fills: dict, *, drop_unfilled_optional: bool = True) -> dict:
    """Fill a template's slots into a concrete DAG. fills: {step: component_id}. An unfilled OPTIONAL slot is dropped (its
    edges rerouted out); an unfilled REQUIRED slot stays plane-bound (component=None) for the composer to fill. Returns
    {template_id, nodes:[{step,component,plane}], edges, unfilled_required, dropped_optional}."""
    slots = {s["step"]: s for s in template["slots"]}
    dropped, nodes, unfilled_req = set(), [], []
    for step, s in slots.items():
        comp = fills.get(step)
        if comp is None and s.get("optional") and drop_unfilled_optional:
            dropped.add(step)
            continue
        if comp is None and not s.get("optional"):
            unfilled_req.append(step)
        nodes.append({"step": step, "component": comp, "plane": s["plane"]})
    edges = [[a, b] for a, b in template.get("edges", []) if a not in dropped and b not in dropped]
    return {"template_id": template["template_id"], "nodes": nodes, "edges": edges,
            "unfilled_required": unfilled_req, "dropped_optional": sorted(dropped), "serves_truth": False}


def mine_template(nodes: list, edges: list, *, capability_family: str, keywords: list | None = None) -> dict:
    """Propose a NEW template from a winning trace — slots = the planes of the trace nodes. The library grows itself
    (candidate-only until promoted, like every other discovery). serves_truth=false."""
    slots = [{"step": n.get("step") or f"s{i}", "plane": n.get("plane")} for i, n in enumerate(nodes)]
    return {"template_id": f"mined.{capability_family}", "capability_family": capability_family,
            "keywords": keywords or [], "slots": slots, "edges": [list(e) for e in edges],
            "success_count": 0, "mined": True, "serves_truth": False}
