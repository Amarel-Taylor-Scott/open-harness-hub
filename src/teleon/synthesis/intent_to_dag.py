"""src.teleon.synthesis.intent_to_dag — intent -> outline -> component DAG -> verification ladder -> alternatives ladder.

The owner's 5-stage synthesis flow, registry-driven so it's deterministic + testable; the frontier LLM is a PORT that
FILLS the scaffold (and the prompts are produced here), never the source of truth:
  1. outline      classify the capability + select its descent ladder (capability_ladders) -> an ordered outline
  2. fill         each outline step -> a DAG node with cheapest-first component OPTIONS (from the ladder rungs)
  3. dag + test   build the DAG; SynthesisTree branches over component choices + tests each (synthesis_tree.py)
  4. verify       a 5W1H verification ladder (who/what/where/when/why/how) per node / group / whole DAG
  5. alternatives a critique ladder per node/group: is this the best way? alternatives? pros/cons?
serves_truth=false; Teleon layer.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.capability_planner import classify_capability_type

_REPO = Path(__file__).resolve().parents[3]
_5W1H = ("who", "what", "where", "when", "why", "how")
#: classify_capability_type() output -> capability_ladders id (fallback = keyword match then search_research)
_TYPE_TO_LADDER = {
    "document_extraction": "document_extraction",
    "task:entity-fact-lookup": "contact_lookup",
    "task:stance-contradiction-detection": "public_statement_tracking",
    "task:text-classification": "document_classification",
    "task:grounded-answer": "search_research",
    "task:entity-resolution": "entity_resolution",
    "task:transcription-asr": "transcription_asr",
    "task:translation": "translation",
}


def _load(name):
    return json.loads((_REPO / "architecture" / name).read_text(encoding="utf-8"))


def _ladders() -> dict:
    return {l["capability"]: l for l in _load("capability_ladders.json")["ladders"]}


def pick_ladder(intent: str) -> dict | None:
    """Stage 1 routing: classify -> a ladder; fall back to a keyword match on ladder ids; else search_research."""
    ladders = _ladders()
    cap = _TYPE_TO_LADDER.get(classify_capability_type(intent))
    if cap and cap in ladders:
        return ladders[cap]
    t = (intent or "").lower()
    for cid, lad in ladders.items():
        if cid.replace("_", " ") in t or all(w in t for w in cid.split("_")[:2]):
            return lad
    return ladders.get("search_research")


def outline(intent: str) -> dict:
    """Stages 1-2: the capability + its ordered outline (the ladder's rungs as steps)."""
    lad = pick_ladder(intent)
    if not lad:
        return {"intent": intent, "capability": None, "steps": [], "note": "no ladder matched"}
    steps = [{"step": r["tier"], "method": r["method"], "deterministic": r["deterministic"]}
             for r in sorted(lad["rungs"], key=lambda r: r["cost_rank"])]
    return {"intent": intent, "capability": lad["capability"], "plane": lad.get("plane"),
            "governance": lad.get("governance"), "steps": steps}


def build_dag(intent: str) -> dict:
    """Stage 3: a DAG of component nodes (one per rung) with cheapest-first OPTIONS; edges = the descent order."""
    lad = pick_ladder(intent)
    if not lad:
        return {"nodes": [], "edges": []}
    rungs = sorted(lad["rungs"], key=lambda r: r["cost_rank"])
    nodes = []
    for r in rungs:
        opts = list(r.get("tools", [])) + list(r.get("external_apis", []))
        nodes.append({"id": r["tier"], "planes": r.get("planes", []), "options": opts,
                      "deterministic": r["deterministic"], "status": r["status"]})
    edges = [(rungs[i]["tier"], rungs[i + 1]["tier"]) for i in range(len(rungs) - 1)]
    return {"capability": lad["capability"], "nodes": nodes, "edges": edges}


def decision_points(intent: str) -> list:
    """The ordered (point_id, [options]) for SynthesisTree — branch over the component choice at each DAG node. A node
    with no concrete tool (pure-LLM rung) gets a single 'llm' option (still a decision, still testable)."""
    dag = build_dag(intent)
    return [(n["id"], n["options"] or ["llm:" + (n["planes"][0] if n["planes"] else "model")]) for n in dag["nodes"]]


def verification_ladder(node: dict) -> dict:
    """Stage 4: the 5W1H verification questions for a DAG node (governance-aware — provenance/why-this-rung/honest-fail)."""
    nid, planes = node.get("id", "?"), ", ".join(node.get("planes", [])) or "?"
    return {"node": nid, "questions": {
        "who": f"who/what produced '{nid}' output, and who consumes it downstream?",
        "what": f"what exactly does '{nid}' assert, and is it deterministic ({node.get('deterministic')})?",
        "where": f"where does each value come from (provenance / source handle on plane {planes})?",
        "when": f"when was it computed, and does it go stale (freshness/CDC)?",
        "why": f"why this rung over the cheaper one below / the dearer one above (the descent rationale)?",
        "how": f"how is it verified, and how does it fail HONESTLY (MISSING, not fabricated)?",
    }}


def alternatives_ladder(node: dict) -> dict:
    """Stage 5: the critique ladder for a node — other components on its plane + the best-way / pros-cons prompts."""
    plane = (node.get("planes") or [None])[0]
    tools = _load("tool_registry.json")["tools"]
    alts = [t["id"] for t in tools if plane and plane in (t.get("plane"),) and t["id"] not in node.get("options", [])]
    return {"node": node.get("id"), "current": node.get("options", []), "alternatives_same_plane": alts[:8],
            "prompts": ["Is this the best component for the bar + budget?", "What are cheaper/stronger alternatives?",
                        "Pros/cons vs the alternatives (cost, latency, license, determinism, governance)?",
                        "Could a deterministic tool replace this model rung entirely?"]}


def frontier_prompts(intent: str) -> list[dict]:
    """The 5 prompts to a frontier LLM (the owner's flow). Context = the selected ladder + registries; sent via the LLM
    PORT when available, else the deterministic scaffold above stands in (honest — never a fabricated DAG)."""
    o = outline(intent)
    ctx = f"capability={o.get('capability')} plane={o.get('plane')} governance={bool(o.get('governance'))}"
    return [
        {"stage": "outline", "prompt": f"How can we make this work? Outline the steps. Intent: {intent}. Context: {ctx}. "
                                       "Prefer the cheapest deterministic method per step; escalate only when needed."},
        {"stage": "fill", "prompt": f"Fill in this outline with concrete components from the registries: {o['steps']}."},
        {"stage": "dag_test", "prompt": "Assemble these into a DAG and define a test for EACH component + the whole DAG."},
        {"stage": "verify", "prompt": f"For each DAG node/group answer the 5W1H verification ladder {list(_5W1H)} "
                                      "(provenance, freshness, why-this-rung, honest-failure)."},
        {"stage": "alternatives", "prompt": "For each node/group: is this the best way? alternatives? pros/cons "
                                            "(cost/latency/license/determinism/governance)? Could a deterministic tool replace a model?"},
    ]
