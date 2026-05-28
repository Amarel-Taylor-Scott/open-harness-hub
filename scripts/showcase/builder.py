"""Assembly: retrieve → orchestrate → cost → narrate → build_flow.

Stage labels / per-component labels are DERIVED from the seven primitives
(scripts/primitives/) via STAGE_ORDER / stage_for_type / label_for_type — single
source, no magic-string dicts. Only the per-stage assembly caps live here.
"""
from __future__ import annotations

import json
import re

from scripts.embeddings import describe_backend
from scripts.model_routes import resolve_route
from scripts.primitives import STAGE_ORDER, label_for_type, stage_for_type
from scripts.showcase.index import Index

# Per-stage assembly caps (functional config, keyed by schema type).
STAGE_CAPS = {"persona": 1, "knowledge-pack": 2, "logic-pack": 1, "rule-pack": 2,
              "tool": 2, "processor": 1, "pattern": 1, "harness": 1, "adapter": 1,
              "pipeline": 1, "rubric": 1, "benchmark": 1, "dataset": 1}
RELEVANCE_FLOOR = 0.18  # below this a candidate is off-topic noise — drop it
_FLOW_CACHE: dict[str, dict] = {}  # task -> result; the two LLM calls are the slow part


def _coherent_select(candidates: list[dict]) -> list[dict]:
    """Deterministic fallback: relevance floor + per-type caps, ordered by stage."""
    kept_by_type: dict[str, list[dict]] = {}
    for c in sorted(candidates, key=lambda r: r["score"], reverse=True):
        if c["score"] < RELEVANCE_FLOOR:
            continue
        bucket = kept_by_type.setdefault(c["type"], [])
        if len(bucket) < STAGE_CAPS.get(c["type"], 1):
            bucket.append(c)
    flat = [c for t in STAGE_CAPS for c in kept_by_type.get(t, [])]
    return [{**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])} for c in flat]


def _parse_keep(raw: str) -> list[str]:
    """Tolerant: extract kept ids even if a verbose/reasoning model truncated the
    JSON mid-array (the cause of the silent orchestration collapse)."""
    if not raw:
        return []
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            ids = [str(x) for x in (json.loads(m.group(0)).get("keep") or []) if isinstance(x, str)]
            if ids:
                return ids
    except Exception:
        pass
    km = re.search(r'"keep"\s*:\s*\[(.*?)(?:\]|$)', raw, re.DOTALL)
    return re.findall(r'"([a-z0-9-]+/[a-z0-9-]+)"', km.group(1) if km else raw)


def orchestrate(task: str, candidates: list[dict], route) -> tuple[list[dict], list[dict], bool]:
    """Pick the coherent, on-topic subset. An LLM prunes off-domain candidates;
    falls back to deterministic selection. Returns (kept, dropped, used_llm)."""
    floored = [c for c in candidates if c["score"] >= RELEVANCE_FLOOR]
    deterministic = _coherent_select(candidates)

    def _det_result():
        kept_ids = {c["id"] for c in deterministic}
        dropped = [{"id": c["id"], "name": c["name"], "type": c["type"]}
                   for c in candidates if c["id"] not in kept_ids][:8]
        return deterministic, dropped, False

    if not floored or not route.health():
        return _det_result()

    listing = "\n".join(f"- {c['id']} [{c['type']}] {c['name']}" for c in floored)
    system = (
        "You are the Open Harness Hub orchestrator. From the CANDIDATES, keep ONLY components "
        "genuinely relevant to the user's task and DROP off-domain ones (wrong industry, modality, "
        "or purpose). Build ONE coherent pipeline: at most one persona, one model harness, one "
        "backbone pipeline, 1-2 knowledge corpora, 1-2 if-statements, 1-2 actions, one rubric. "
        "Return ONLY compact JSON with a SINGLE key and NO explanations: "
        "{\"keep\":[\"id\",\"id\",...]}. Do not include a 'drop' list or any prose. "
        "Use only ids from the list."
    )
    keep_ids = _parse_keep(route.complete(system, f"Task: {task}\n\nCANDIDATES:\n{listing}", max_tokens=2048) or "")
    if not keep_ids:
        return _det_result()

    by_id = {c["id"]: c for c in candidates}
    chosen, counts = [], {}
    for cid in keep_ids:
        c = by_id.get(cid)
        if not c or counts.get(c["type"], 0) >= STAGE_CAPS.get(c["type"], 1):
            continue
        counts[c["type"]] = counts.get(c["type"], 0) + 1
        chosen.append({**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])})
    if not chosen:
        return _det_result()
    chosen.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c["stage"] in STAGE_ORDER else 99)
    kept_ids = {c["id"] for c in chosen}
    dropped = [{"id": c["id"], "name": c["name"], "type": c["type"]}
               for c in floored if c["id"] not in kept_ids][:8]
    return chosen, dropped, True


def flowchart(kept: list[dict]) -> list[dict]:
    """Group kept components into ordered stages: Input → … → Output."""
    chart = [{"stage": "Input", "components": [
        {"id": "user task", "type": "input", "name": "User task", "role": "plain-language description"}]}]
    for stage in STAGE_ORDER:
        comps = [{"id": c["id"], "type": c["type"], "name": c["name"], "role": c["role"]}
                 for c in kept if c.get("stage") == stage]
        if comps:
            chart.append({"stage": stage, "components": comps})
    chart.append({"stage": "Output", "components": [
        {"id": "result", "type": "output", "name": "Costed, deployable flow", "role": "validated result + trace"}]})
    return chart


def estimate_cost(kept: list[dict]) -> dict:
    n_model = sum(1 for s in kept if s["type"] in {"harness", "pipeline", "adapter"})
    n_rules = sum(1 for s in kept if s["type"] in {"rule-pack", "processor"})
    return {
        "cheap":    {"per_task_usd": "0.00–0.02", "how": f"local model + {n_rules} deterministic gate(s) first; model only on the residual"},
        "balanced": {"per_task_usd": "0.01–0.10", "how": f"small hosted model for {max(1, n_model)} model step(s); rules/retrieval pre-filter"},
        "quality":  {"per_task_usd": "0.10–0.60", "how": "frontier model on the final step; full retrieval + review gate"},
        "note": "Illustrative; calibrate against real runs. Rules/retrieval before the model is the main lever.",
    }


def deterministic_narrative(task: str, kept: list[dict], cost: dict) -> str:
    parts = [f"Composed a coherent flow of {len(kept)} components:"]
    for s in kept:
        parts.append(f" • [{s.get('stage', '')}] {s['type']}/{s['id'].split('/')[-1]} — {s['role']}.")
    parts.append("Deterministic rules and retrieval run before the model to cut cost; swap the "
                 f"model via the harness/adapter. Estimated ~{cost['balanced']['per_task_usd']}/task "
                 "(balanced). Refine: \"cheaper\" (local model + more rules-first) or "
                 "\"stricter\" (review gate + tighter rubric).")
    return "\n".join(parts)


def llm_narrative(task: str, kept: list[dict], cost: dict) -> tuple[str, bool]:
    route = resolve_route()
    if not route.health() or not kept:
        return deterministic_narrative(task, kept, cost), False
    comp_lines = "\n".join(f"- [{s.get('stage', '')}] {s['type']}/{s['id'].split('/')[-1]}: {s['role']}" for s in kept)
    system = ("You are the Open Harness Hub builder. In 4-6 sentences, explain the assembled "
              "pipeline of these EXISTING components for the task: the flow from input through "
              "persona, retrieval, deterministic rules, tools, the model harness, to evaluation; "
              "why rules/retrieval run before the model to cut cost; and how to swap the model. "
              "Then two one-line refinements (cheaper / stricter). Mention ONLY the listed components.")
    user = f"Task: {task}\n\nFlow (in order):\n{comp_lines}\n\nBalanced cost ~{cost['balanced']['per_task_usd']}/task."
    text = route.complete(system, user, max_tokens=2048)
    return (text.strip(), True) if text and text.strip() else (deterministic_narrative(task, kept, cost), False)


def _stratified_pool(index: Index, task: str) -> list[dict]:
    """Candidate pool that GUARANTEES per-type representation, so a flood of
    near-duplicate top scorers can't starve whole stages."""
    flat = index.search(task, k=60)
    by_type: dict[str, list[dict]] = {}
    for c in flat:
        by_type.setdefault(c["type"], []).append(c)
    pool, seen = [], set()
    for c in flat[:18]:                       # strongest overall
        if c["id"] not in seen:
            pool.append(c); seen.add(c["id"])
    for cs in by_type.values():               # + top-3 of EVERY type
        for c in cs[:3]:
            if c["id"] not in seen:
                pool.append(c); seen.add(c["id"])
    return pool


def analyze_match(kept: list[dict], pool: list[dict]) -> dict:
    """Detect UNDER-match (a needed component available but unselected) and
    OVER-match (a type exceeds its cap). Checked by TYPE so it is robust to
    stage label changes."""
    kept_types = {c["type"] for c in kept}
    pool_types = {c["type"] for c in pool}
    under = []
    if not (kept_types & {"harness", "pipeline"}) and ({"harness", "pipeline"} & pool_types):
        under.append("Model boundary — a harness/pipeline was available but not selected")
    if not (kept_types & {"rubric", "benchmark"}) and ({"rubric", "benchmark"} & pool_types):
        under.append("Evaluate — a rubric/benchmark was available but not selected")
    if "knowledge-pack" not in kept_types and "knowledge-pack" in pool_types:
        under.append("Knowledge Corpus — a corpus was available but not selected")
    counts: dict[str, int] = {}
    for c in kept:
        counts[c["type"]] = counts.get(c["type"], 0) + 1
    over = [f"{t} ×{n}" for t, n in counts.items() if n > STAGE_CAPS.get(t, 1)]
    return {"undermatched": under, "overmatched": over,
            "stage_coverage": sorted({c["stage"] for c in kept})}


def build_flow(task: str, index: Index) -> dict:
    cache_key = " ".join(task.lower().split())
    if cache_key in _FLOW_CACHE:
        return {**_FLOW_CACHE[cache_key], "cached": True}
    route = resolve_route()
    pool = _stratified_pool(index, task)
    kept, dropped, sel_llm = orchestrate(task, pool, route)
    # Back-fill a model boundary (by TYPE) if the pool had one but selection skipped it.
    if not any(c["type"] in ("harness", "pipeline") for c in kept):
        for c in pool:
            if c["type"] in ("pipeline", "harness"):
                kept.append({**c, "stage": stage_for_type(c["type"]), "role": label_for_type(c["type"])})
                break
        kept.sort(key=lambda c: STAGE_ORDER.index(c["stage"]) if c.get("stage") in STAGE_ORDER else 99)
    cost = estimate_cost(kept)
    analysis = analyze_match(kept, pool)
    narrative, narr_llm = llm_narrative(task, kept, cost)
    result = {
        "task": task,
        "flow": {"steps": kept, "stages": flowchart(kept), "dropped": dropped, "analysis": analysis},
        "cost": cost,
        "narrative": narrative,
        "llm_used": (sel_llm or narr_llm),
        "selection_by_model": sel_llm,
        "embedding": describe_backend(),
        "cached": False,
    }
    if len(_FLOW_CACHE) > 500:  # bounded
        _FLOW_CACHE.clear()
    _FLOW_CACHE[cache_key] = result
    return result
