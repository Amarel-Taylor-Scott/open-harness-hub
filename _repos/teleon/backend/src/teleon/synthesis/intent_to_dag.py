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
from scripts._repo_paths import resource as _resource

import json
from pathlib import Path

from src.teleon.capability_planner import classify_capability_type

py_var_src_teleon_synthesis_intent_to_dag___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
py_var_src_teleon_synthesis_intent_to_dag___5W1H = ("who", "what", "where", "when", "why", "how")
#: classify_capability_type() output -> capability_ladders id (fallback = keyword match then search_research)
py_var_src_teleon_synthesis_intent_to_dag___TYPE_TO_LADDER = {
    "document_extraction": "document_extraction",
    "task:entity-fact-lookup": "contact_lookup",
    "task:stance-contradiction-detection": "public_statement_tracking",
    "task:text-classification": "document_classification",
    "task:grounded-answer": "search_research",
    "task:entity-resolution": "entity_resolution",
    "task:transcription-asr": "transcription_asr",
    "task:translation": "translation",
}


def py_function_src_teleon_synthesis_intent_to_dag___load(py_arg_src_teleon_synthesis_intent_to_dag__load__name):
    return json.loads((_resource("architecture") / py_arg_src_teleon_synthesis_intent_to_dag__load__name).read_text(encoding="utf-8"))


def py_function_src_teleon_synthesis_intent_to_dag___ladders() -> dict:
    return {l["capability"]: l for l in py_function_src_teleon_synthesis_intent_to_dag___load("capability_ladders.json")["ladders"]}


def py_function_src_teleon_synthesis_intent_to_dag__pick_ladder(py_arg_src_teleon_synthesis_intent_to_dag__pick_ladder__intent: str) -> dict | None:
    """Stage 1 routing: classify -> a ladder; fall back to a keyword match on ladder ids; else search_research."""
    py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__ladders = py_function_src_teleon_synthesis_intent_to_dag___ladders()
    py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cap = py_var_src_teleon_synthesis_intent_to_dag___TYPE_TO_LADDER.get(classify_capability_type(py_arg_src_teleon_synthesis_intent_to_dag__pick_ladder__intent))
    if py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cap and py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cap in py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__ladders:
        return py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__ladders[py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cap]
    py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__t = (py_arg_src_teleon_synthesis_intent_to_dag__pick_ladder__intent or "").lower()
    for py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cid, py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__lad in py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__ladders.items():
        if py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cid.replace("_", " ") in py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__t or all(w in py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__t for w in py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__cid.split("_")[:2]):
            return py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__lad
    return py_local_src_teleon_synthesis_intent_to_dag__pick_ladder__ladders.get("search_research")


def py_function_src_teleon_synthesis_intent_to_dag__outline(py_arg_src_teleon_synthesis_intent_to_dag__outline__intent: str) -> dict:
    """Stages 1-2: the capability + its ordered outline (the ladder's rungs as steps)."""
    py_local_src_teleon_synthesis_intent_to_dag__outline__lad = py_function_src_teleon_synthesis_intent_to_dag__pick_ladder(py_arg_src_teleon_synthesis_intent_to_dag__outline__intent)
    if not py_local_src_teleon_synthesis_intent_to_dag__outline__lad:
        return {"intent": py_arg_src_teleon_synthesis_intent_to_dag__outline__intent, "capability": None, "steps": [], "note": "no ladder matched"}
    py_local_src_teleon_synthesis_intent_to_dag__outline__steps = [{"step": py_arg_src_teleon_synthesis_intent_to_dag__outline__r["tier"], "method": py_arg_src_teleon_synthesis_intent_to_dag__outline__r["method"], "deterministic": py_arg_src_teleon_synthesis_intent_to_dag__outline__r["deterministic"]}
             for py_arg_src_teleon_synthesis_intent_to_dag__outline__r in sorted(py_local_src_teleon_synthesis_intent_to_dag__outline__lad["rungs"], key=lambda py_arg_src_teleon_synthesis_intent_to_dag__outline__r: py_arg_src_teleon_synthesis_intent_to_dag__outline__r["cost_rank"])]
    return {"intent": py_arg_src_teleon_synthesis_intent_to_dag__outline__intent, "capability": py_local_src_teleon_synthesis_intent_to_dag__outline__lad["capability"], "plane": py_local_src_teleon_synthesis_intent_to_dag__outline__lad.get("plane"),
            "governance": py_local_src_teleon_synthesis_intent_to_dag__outline__lad.get("governance"), "steps": py_local_src_teleon_synthesis_intent_to_dag__outline__steps}


def py_function_src_teleon_synthesis_intent_to_dag__build_dag(py_arg_src_teleon_synthesis_intent_to_dag__build_dag__intent: str) -> dict:
    """Stage 3: a DAG of component nodes (one per rung) with cheapest-first OPTIONS; edges = the descent order."""
    py_local_src_teleon_synthesis_intent_to_dag__build_dag__lad = py_function_src_teleon_synthesis_intent_to_dag__pick_ladder(py_arg_src_teleon_synthesis_intent_to_dag__build_dag__intent)
    if not py_local_src_teleon_synthesis_intent_to_dag__build_dag__lad:
        return {"nodes": [], "edges": []}
    py_local_src_teleon_synthesis_intent_to_dag__build_dag__rungs = sorted(py_local_src_teleon_synthesis_intent_to_dag__build_dag__lad["rungs"], key=lambda py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r: py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r["cost_rank"])
    py_local_src_teleon_synthesis_intent_to_dag__build_dag__nodes = []
    for py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r in py_local_src_teleon_synthesis_intent_to_dag__build_dag__rungs:
        py_local_src_teleon_synthesis_intent_to_dag__build_dag__opts = list(py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r.get("tools", [])) + list(py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r.get("external_apis", []))
        py_local_src_teleon_synthesis_intent_to_dag__build_dag__nodes.append({"id": py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r["tier"], "planes": py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r.get("planes", []), "options": py_local_src_teleon_synthesis_intent_to_dag__build_dag__opts,
                      "governance": py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r.get("governance") or py_local_src_teleon_synthesis_intent_to_dag__build_dag__lad.get("governance"),
                      "deterministic": py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r["deterministic"], "status": py_arg_src_teleon_synthesis_intent_to_dag__build_dag__r["status"]})
    py_local_src_teleon_synthesis_intent_to_dag__build_dag__edges = [(py_local_src_teleon_synthesis_intent_to_dag__build_dag__rungs[i]["tier"], py_local_src_teleon_synthesis_intent_to_dag__build_dag__rungs[i + 1]["tier"]) for i in range(len(py_local_src_teleon_synthesis_intent_to_dag__build_dag__rungs) - 1)]
    return {"capability": py_local_src_teleon_synthesis_intent_to_dag__build_dag__lad["capability"], "nodes": py_local_src_teleon_synthesis_intent_to_dag__build_dag__nodes, "edges": py_local_src_teleon_synthesis_intent_to_dag__build_dag__edges}


def py_function_src_teleon_synthesis_intent_to_dag__decision_points(py_arg_src_teleon_synthesis_intent_to_dag__decision_points__intent: str, *, principal=None) -> list:
    """The ordered (point_id, [options]) for SynthesisTree — branch over the component choice at each DAG node. A node
    with no concrete tool (pure-LLM rung) gets a single 'llm' option. When a `principal` is given, each node's options are
    GATED to what they're entitled to (restricted/plan-gated tools they lack drop out; a node with none left gets an
    honest 'blocked:needs-<grant/tier>' option) — so the descent only ever proposes tools the principal may use."""
    py_local_src_teleon_synthesis_intent_to_dag__decision_points__dag = py_function_src_teleon_synthesis_intent_to_dag__build_dag(py_arg_src_teleon_synthesis_intent_to_dag__decision_points__intent)
    py_local_src_teleon_synthesis_intent_to_dag__decision_points__out = []
    for py_local_src_teleon_synthesis_intent_to_dag__decision_points__n in py_local_src_teleon_synthesis_intent_to_dag__decision_points__dag["nodes"]:
        py_local_src_teleon_synthesis_intent_to_dag__decision_points__opts = py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["options"] or ["llm:" + (py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["planes"][0] if py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["planes"] else "model")]
        if principal is not None and py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["options"]:
            from src.teleon.runtime import entitlements as E
            py_local_src_teleon_synthesis_intent_to_dag__decision_points__opts = E.py_function_src_teleon_runtime_entitlements__gate_options(principal, py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["options"], plane=(py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["planes"] or [None])[0], governance=py_local_src_teleon_synthesis_intent_to_dag__decision_points__n.get("governance"))
        py_local_src_teleon_synthesis_intent_to_dag__decision_points__out.append((py_local_src_teleon_synthesis_intent_to_dag__decision_points__n["id"], py_local_src_teleon_synthesis_intent_to_dag__decision_points__opts))
    return py_local_src_teleon_synthesis_intent_to_dag__decision_points__out


def py_function_src_teleon_synthesis_intent_to_dag__verification_ladder(py_arg_src_teleon_synthesis_intent_to_dag__verification_ladder__node: dict) -> dict:
    """Stage 4: the 5W1H verification questions for a DAG node (governance-aware — provenance/why-this-rung/honest-fail)."""
    py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__nid, py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__planes = py_arg_src_teleon_synthesis_intent_to_dag__verification_ladder__node.get("id", "?"), ", ".join(py_arg_src_teleon_synthesis_intent_to_dag__verification_ladder__node.get("planes", [])) or "?"
    return {"node": py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__nid, "questions": {
        "who": f"who/what produced '{py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__nid}' output, and who consumes it downstream?",
        "what": f"what exactly does '{py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__nid}' assert, and is it deterministic ({py_arg_src_teleon_synthesis_intent_to_dag__verification_ladder__node.get('deterministic')})?",
        "where": f"where does each value come from (provenance / source handle on plane {py_local_src_teleon_synthesis_intent_to_dag__verification_ladder__planes})?",
        "when": f"when was it computed, and does it go stale (freshness/CDC)?",
        "why": f"why this rung over the cheaper one below / the dearer one above (the descent rationale)?",
        "how": f"how is it verified, and how does it fail HONESTLY (MISSING, not fabricated)?",
    }}


def py_function_src_teleon_synthesis_intent_to_dag__alternatives_ladder(py_arg_src_teleon_synthesis_intent_to_dag__alternatives_ladder__node: dict) -> dict:
    """Stage 5: the critique ladder for a node — other components on its plane + the best-way / pros-cons prompts."""
    py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__plane = (py_arg_src_teleon_synthesis_intent_to_dag__alternatives_ladder__node.get("planes") or [None])[0]
    py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__tools = py_function_src_teleon_synthesis_intent_to_dag___load("tool_registry.json")["tools"]
    py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__alts = [t["id"] for t in py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__tools if py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__plane and py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__plane in (t.get("plane"),) and t["id"] not in py_arg_src_teleon_synthesis_intent_to_dag__alternatives_ladder__node.get("options", [])]
    return {"node": py_arg_src_teleon_synthesis_intent_to_dag__alternatives_ladder__node.get("id"), "current": py_arg_src_teleon_synthesis_intent_to_dag__alternatives_ladder__node.get("options", []), "alternatives_same_plane": py_local_src_teleon_synthesis_intent_to_dag__alternatives_ladder__alts[:8],
            "prompts": ["Is this the best component for the bar + budget?", "What are cheaper/stronger alternatives?",
                        "Pros/cons vs the alternatives (cost, latency, license, determinism, governance)?",
                        "Could a deterministic tool replace this model rung entirely?"]}


def py_function_src_teleon_synthesis_intent_to_dag__frontier_prompts(py_arg_src_teleon_synthesis_intent_to_dag__frontier_prompts__intent: str) -> list[dict]:
    """Disciplined per-stage prompts from _repos/shared-backend-components/architecture/synthesis_prompt_templates.json (enumerate-before-commit,
    deterministic-before-model, test-before-descend, troubleshoot-before-backtrack, track-data-every-step) + live
    context. Sent via the LLM PORT when available; the deterministic scaffold stands in offline (never a fabricated DAG)."""
    py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__tmpl = py_function_src_teleon_synthesis_intent_to_dag___load("synthesis_prompt_templates.json")
    py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__o = py_function_src_teleon_synthesis_intent_to_dag__outline(py_arg_src_teleon_synthesis_intent_to_dag__frontier_prompts__intent)
    py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__ctx = f"capability={py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__o.get('capability')} plane={py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__o.get('plane')} governance={bool(py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__o.get('governance'))} steps={[py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s['step'] for py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s in py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__o.get('steps', [])]}"
    py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__discipline = "; ".join(d["rule"] for d in py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__tmpl["discipline"])
    py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__out = []
    for py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s in py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__tmpl["stages"]:
        py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__out.append({"stage": py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s["stage"], "goal": py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s["goal"],
                    "prompt": f"{py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s['prompt']}\nContext: {py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__ctx}.\nMUST: {py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s['must']}. AVOID: {py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s['avoid']}. "
                              f"TRACK (record this data): {py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s['track']}.\nDiscipline in force: {py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__discipline}.",
                    "must": py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s["must"], "avoid": py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s["avoid"], "track": py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__s["track"]})
    return py_local_src_teleon_synthesis_intent_to_dag__frontier_prompts__out
