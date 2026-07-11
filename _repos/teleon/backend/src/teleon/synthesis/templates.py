"""templates — the template library (the biggest efficiency lever). Canonical typed DAG SKELETONS with named slots;
composition RETRIEVES a matching template and MUTATES its slots (fill each slot's plane with a component, drop unused
optional slots) instead of synthesizing from scratch. The honest reason: classical component synthesis scales poorly with
library size, so templates carry the common case and synthesis is the long-tail fallback. Templates are MINED from
winning traces so the library grows itself. Single source: _repos/shared-backend-components/architecture/dag_templates.json. serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
from functools import lru_cache
from pathlib import Path

py_var_src_teleon_synthesis_templates___TEMPLATES = _resource("architecture") / "dag_templates.json"


@lru_cache(maxsize=1)
def py_function_src_teleon_synthesis_templates__load_templates() -> list:
    return json.loads(py_var_src_teleon_synthesis_templates___TEMPLATES.read_text())["templates"]


def py_function_src_teleon_synthesis_templates___tok(py_arg_src_teleon_synthesis_templates__tok__s: str) -> set:
    return set(re.findall(r"[a-z0-9]+", (py_arg_src_teleon_synthesis_templates__tok__s or "").lower()))


def py_function_src_teleon_synthesis_templates__retrieve_template(py_arg_src_teleon_synthesis_templates__retrieve_template__query: str, *, py_arg_src_teleon_synthesis_templates__retrieve_template__capability_family: str | None = None) -> dict | None:
    """The best-matching template by keyword/family overlap, or None when nothing matches. Ties break by telemetry
    success_count (the library self-ranks). A matching family is worth a strong boost."""
    py_local_src_teleon_synthesis_templates__retrieve_template__q = py_function_src_teleon_synthesis_templates___tok(py_arg_src_teleon_synthesis_templates__retrieve_template__query)
    py_local_src_teleon_synthesis_templates__retrieve_template__best, py_local_src_teleon_synthesis_templates__retrieve_template__score = None, 0
    for py_local_src_teleon_synthesis_templates__retrieve_template__t in py_function_src_teleon_synthesis_templates__load_templates():
        py_local_src_teleon_synthesis_templates__retrieve_template__s = len(py_local_src_teleon_synthesis_templates__retrieve_template__q & set(py_local_src_teleon_synthesis_templates__retrieve_template__t.get("keywords", [])))
        if py_arg_src_teleon_synthesis_templates__retrieve_template__capability_family and py_local_src_teleon_synthesis_templates__retrieve_template__t.get("capability_family") == py_arg_src_teleon_synthesis_templates__retrieve_template__capability_family:
            py_local_src_teleon_synthesis_templates__retrieve_template__s += 3
        if py_local_src_teleon_synthesis_templates__retrieve_template__s > py_local_src_teleon_synthesis_templates__retrieve_template__score or (py_local_src_teleon_synthesis_templates__retrieve_template__s == py_local_src_teleon_synthesis_templates__retrieve_template__score and py_local_src_teleon_synthesis_templates__retrieve_template__best is not None and py_local_src_teleon_synthesis_templates__retrieve_template__t.get("success_count", 0) > py_local_src_teleon_synthesis_templates__retrieve_template__best.get("success_count", 0)):
            py_local_src_teleon_synthesis_templates__retrieve_template__best, py_local_src_teleon_synthesis_templates__retrieve_template__score = py_local_src_teleon_synthesis_templates__retrieve_template__t, py_local_src_teleon_synthesis_templates__retrieve_template__s
    return py_local_src_teleon_synthesis_templates__retrieve_template__best if py_local_src_teleon_synthesis_templates__retrieve_template__score > 0 else None


def py_function_src_teleon_synthesis_templates__mutate(py_arg_src_teleon_synthesis_templates__mutate__template: dict, py_arg_src_teleon_synthesis_templates__mutate__fills: dict, *, py_arg_src_teleon_synthesis_templates__mutate__drop_unfilled_optional: bool = True) -> dict:
    """Fill a template's slots into a concrete DAG. fills: {step: component_id}. An unfilled OPTIONAL slot is dropped (its
    edges rerouted out); an unfilled REQUIRED slot stays plane-bound (component=None) for the composer to fill. Returns
    {template_id, nodes:[{step,component,plane}], edges, unfilled_required, dropped_optional}."""
    py_local_src_teleon_synthesis_templates__mutate__slots = {py_local_src_teleon_synthesis_templates__mutate__s["step"]: py_local_src_teleon_synthesis_templates__mutate__s for py_local_src_teleon_synthesis_templates__mutate__s in py_arg_src_teleon_synthesis_templates__mutate__template["slots"]}
    py_local_src_teleon_synthesis_templates__mutate__dropped, py_local_src_teleon_synthesis_templates__mutate__nodes, py_local_src_teleon_synthesis_templates__mutate__unfilled_req = set(), [], []
    for py_local_src_teleon_synthesis_templates__mutate__step, py_local_src_teleon_synthesis_templates__mutate__s in py_local_src_teleon_synthesis_templates__mutate__slots.items():
        py_local_src_teleon_synthesis_templates__mutate__comp = py_arg_src_teleon_synthesis_templates__mutate__fills.get(py_local_src_teleon_synthesis_templates__mutate__step)
        if py_local_src_teleon_synthesis_templates__mutate__comp is None and py_local_src_teleon_synthesis_templates__mutate__s.get("optional") and py_arg_src_teleon_synthesis_templates__mutate__drop_unfilled_optional:
            py_local_src_teleon_synthesis_templates__mutate__dropped.add(py_local_src_teleon_synthesis_templates__mutate__step)
            continue
        if py_local_src_teleon_synthesis_templates__mutate__comp is None and not py_local_src_teleon_synthesis_templates__mutate__s.get("optional"):
            py_local_src_teleon_synthesis_templates__mutate__unfilled_req.append(py_local_src_teleon_synthesis_templates__mutate__step)
        py_local_src_teleon_synthesis_templates__mutate__nodes.append({"step": py_local_src_teleon_synthesis_templates__mutate__step, "component": py_local_src_teleon_synthesis_templates__mutate__comp, "plane": py_local_src_teleon_synthesis_templates__mutate__s["plane"]})
    py_local_src_teleon_synthesis_templates__mutate__edges = [[a, b] for a, b in py_arg_src_teleon_synthesis_templates__mutate__template.get("edges", []) if a not in py_local_src_teleon_synthesis_templates__mutate__dropped and b not in py_local_src_teleon_synthesis_templates__mutate__dropped]
    return {"template_id": py_arg_src_teleon_synthesis_templates__mutate__template["template_id"], "nodes": py_local_src_teleon_synthesis_templates__mutate__nodes, "edges": py_local_src_teleon_synthesis_templates__mutate__edges,
            "unfilled_required": py_local_src_teleon_synthesis_templates__mutate__unfilled_req, "dropped_optional": sorted(py_local_src_teleon_synthesis_templates__mutate__dropped), "serves_truth": False}


def py_function_src_teleon_synthesis_templates__mine_template(py_arg_src_teleon_synthesis_templates__mine_template__nodes: list, py_arg_src_teleon_synthesis_templates__mine_template__edges: list, *, capability_family: str, keywords: list | None = None) -> dict:
    """Propose a NEW template from a winning trace — slots = the planes of the trace nodes. The library grows itself
    (candidate-only until promoted, like every other discovery). serves_truth=false."""
    py_local_src_teleon_synthesis_templates__mine_template__slots = [{"step": n.get("step") or f"s{i}", "plane": n.get("plane")} for i, n in enumerate(py_arg_src_teleon_synthesis_templates__mine_template__nodes)]
    return {"template_id": f"mined.{capability_family}", "capability_family": capability_family,
            "keywords": keywords or [], "slots": py_local_src_teleon_synthesis_templates__mine_template__slots, "edges": [list(e) for e in py_arg_src_teleon_synthesis_templates__mine_template__edges],
            "success_count": 0, "mined": True, "serves_truth": False}
