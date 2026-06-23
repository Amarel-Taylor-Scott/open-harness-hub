"""passes — System 8/9: the PassManager (LLVM for cognition). Optimization passes are IR→IR rewrites, each gated by a
LEGALITY check (re-verify the DAG if the pass changes observable behavior) and a COST gate (a pass fires only if it does
NOT worsen the objective, scored by the analytic simulator). A handful of rigorously-gated passes beats a pile of unsafe
ones — pass phase-ordering is unsolved in general, so every behavior-changing pass re-triggers verification. This is where
"remove unnecessary intelligence" literally happens (the deterministic-replacement pass). serves_truth=false.
"""
from __future__ import annotations

from src.teleon.economics import simulator as SIM
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first
from src.teleon.synthesis.dag_contract import verify_buildable_dag


def pass_cse(dag: dict, **_) -> tuple:
    """Common-subexpression elimination: nodes with identical (component, plane, predecessors) are duplicates → keep one,
    reroute edges. Mechanical (behavior-preserving)."""
    nodes, edges = dag["nodes"], [list(e) for e in dag.get("edges", [])]
    preds: dict = {}
    for a, b in edges:
        preds.setdefault(b, []).append(a)
    survivor, remap, keep = {}, {}, []
    for n in nodes:
        sig = (n.get("component"), n.get("plane"), tuple(sorted(preds.get(n["step"], []))))
        if sig in survivor:
            remap[n["step"]] = survivor[sig]
        else:
            survivor[sig] = n["step"]
            keep.append(n)
    if not remap:
        return dag, False, "no common subexpressions"
    seen, new_edges = set(), []
    for a, b in edges:
        a2, b2 = remap.get(a, a), remap.get(b, b)
        if a2 != b2 and (a2, b2) not in seen:
            seen.add((a2, b2))
            new_edges.append([a2, b2])
    return {"nodes": keep, "edges": new_edges}, True, f"merged {len(remap)} duplicate node(s)"


def pass_deterministic_replacement(dag: dict, *, substitutions: dict | None = None, **_) -> tuple:
    """Replace an llm node with a DETERMINISTIC substitute (the core descent move — remove unnecessary intelligence).
    substitutions: {step: {component, plane}}. Behavior-changing → the manager re-verifies + cost-gates it."""
    subs = substitutions or {}
    if not subs:
        return dag, False, "no substitutions provided"
    nodes, changed = [], 0
    for n in dag["nodes"]:
        if n["step"] in subs and n.get("plane") == "llm":
            s = subs[n["step"]]
            nodes.append({**n, "component": s["component"], "plane": s.get("plane", "field_parsing"), "_replaced_from": "llm"})
            changed += 1
        else:
            nodes.append(n)
    if not changed:
        return dag, False, "no llm node matched a substitution"
    return {"nodes": nodes, "edges": [list(e) for e in dag.get("edges", [])]}, True, f"replaced {changed} llm node(s) with deterministic"


_PASS_TABLE = {"cse": (pass_cse, False), "deterministic_replacement": (pass_deterministic_replacement, True)}
DEFAULT_PASSES = ["cse", "deterministic_replacement"]


def _cost(dag: dict, shard: str = "000") -> float:
    return SIM.simulate_dag(dag["nodes"], dag.get("edges"), shard=shard)["total_cost"]


def run_passes(dag: dict, *, passes: list | None = None, profile: PreferenceProfile | None = None,
               shard: str = "000", **opts) -> dict:
    """Run the pass pipeline. Each pass: legality (re-verify if behavior-changing) + a cost gate (never worsen the
    objective). Returns {dag, applied:[{pass, applied, note|reason}], before_cost, after_cost, savings}."""
    profile = profile or cost_first()
    cur = {"nodes": list(dag["nodes"]), "edges": [list(e) for e in dag.get("edges", [])]}
    before, applied = _cost(cur, shard), []
    for name in (passes or DEFAULT_PASSES):
        fn, reverify = _PASS_TABLE[name]
        new, changed, note = fn(cur, **opts)
        if not changed:
            applied.append({"pass": name, "applied": False, "reason": note})
            continue
        if reverify and not verify_buildable_dag(new["nodes"], new.get("edges") or [])["verified_working"]:
            applied.append({"pass": name, "applied": False, "reason": "re-verify failed (illegal rewrite)"})
            continue
        if _cost(new, shard) > _cost(cur, shard) + 1e-12:        # cost gate: never worsen the objective
            applied.append({"pass": name, "applied": False, "reason": "would worsen the objective"})
            continue
        cur = new
        applied.append({"pass": name, "applied": True, "note": note})
    after = _cost(cur, shard)
    return {"dag": cur, "applied": applied, "before_cost": round(before, 8), "after_cost": round(after, 8),
            "savings": round(before - after, 8), "serves_truth": False}
