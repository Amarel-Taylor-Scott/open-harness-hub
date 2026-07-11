"""passes — System 8/9: the PassManager (LLVM for cognition). Optimization passes are IR→IR rewrites, each gated by a
LEGALITY check (re-verify the DAG if the pass changes observable behavior) and a COST gate (a pass fires only if it does
NOT worsen the objective, scored by the analytic simulator). A handful of rigorously-gated passes beats a pile of unsafe
ones — pass phase-ordering is unsolved in general, so every behavior-changing pass re-triggers verification. This is where
"remove unnecessary intelligence" literally happens (the deterministic-replacement pass). serves_truth=false.
"""
from __future__ import annotations

from src.teleon.economics import simulator as SIM
from src.teleon.inference.preference_profile import PreferenceProfile, cost_first
from src.teleon.synthesis.dag_contract import py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag


def py_function_src_teleon_synthesis_passes__pass_cse(py_arg_src_teleon_synthesis_passes__pass_cse__dag: dict, **py_arg_src_teleon_synthesis_passes__pass_cse___) -> tuple:
    """Common-subexpression elimination: nodes with identical (component, plane, predecessors) are duplicates → keep one,
    reroute edges. Mechanical (behavior-preserving)."""
    py_local_src_teleon_synthesis_passes__pass_cse__nodes, py_local_src_teleon_synthesis_passes__pass_cse__edges = py_arg_src_teleon_synthesis_passes__pass_cse__dag["nodes"], [list(e) for e in py_arg_src_teleon_synthesis_passes__pass_cse__dag.get("edges", [])]
    py_local_src_teleon_synthesis_passes__pass_cse__preds: dict = {}
    for py_local_src_teleon_synthesis_passes__pass_cse__a, py_local_src_teleon_synthesis_passes__pass_cse__b in py_local_src_teleon_synthesis_passes__pass_cse__edges:
        py_local_src_teleon_synthesis_passes__pass_cse__preds.setdefault(py_local_src_teleon_synthesis_passes__pass_cse__b, []).append(py_local_src_teleon_synthesis_passes__pass_cse__a)
    py_local_src_teleon_synthesis_passes__pass_cse__survivor, py_local_src_teleon_synthesis_passes__pass_cse__remap, py_local_src_teleon_synthesis_passes__pass_cse__keep = {}, {}, []
    for py_local_src_teleon_synthesis_passes__pass_cse__n in py_local_src_teleon_synthesis_passes__pass_cse__nodes:
        py_local_src_teleon_synthesis_passes__pass_cse__sig = (py_local_src_teleon_synthesis_passes__pass_cse__n.get("component"), py_local_src_teleon_synthesis_passes__pass_cse__n.get("plane"), tuple(sorted(py_local_src_teleon_synthesis_passes__pass_cse__preds.get(py_local_src_teleon_synthesis_passes__pass_cse__n["step"], []))))
        if py_local_src_teleon_synthesis_passes__pass_cse__sig in py_local_src_teleon_synthesis_passes__pass_cse__survivor:
            py_local_src_teleon_synthesis_passes__pass_cse__remap[py_local_src_teleon_synthesis_passes__pass_cse__n["step"]] = py_local_src_teleon_synthesis_passes__pass_cse__survivor[py_local_src_teleon_synthesis_passes__pass_cse__sig]
        else:
            py_local_src_teleon_synthesis_passes__pass_cse__survivor[py_local_src_teleon_synthesis_passes__pass_cse__sig] = py_local_src_teleon_synthesis_passes__pass_cse__n["step"]
            py_local_src_teleon_synthesis_passes__pass_cse__keep.append(py_local_src_teleon_synthesis_passes__pass_cse__n)
    if not py_local_src_teleon_synthesis_passes__pass_cse__remap:
        return py_arg_src_teleon_synthesis_passes__pass_cse__dag, False, "no common subexpressions"
    py_local_src_teleon_synthesis_passes__pass_cse__seen, py_local_src_teleon_synthesis_passes__pass_cse__new_edges = set(), []
    for py_local_src_teleon_synthesis_passes__pass_cse__a, py_local_src_teleon_synthesis_passes__pass_cse__b in py_local_src_teleon_synthesis_passes__pass_cse__edges:
        py_local_src_teleon_synthesis_passes__pass_cse__a2, py_local_src_teleon_synthesis_passes__pass_cse__b2 = py_local_src_teleon_synthesis_passes__pass_cse__remap.get(py_local_src_teleon_synthesis_passes__pass_cse__a, py_local_src_teleon_synthesis_passes__pass_cse__a), py_local_src_teleon_synthesis_passes__pass_cse__remap.get(py_local_src_teleon_synthesis_passes__pass_cse__b, py_local_src_teleon_synthesis_passes__pass_cse__b)
        if py_local_src_teleon_synthesis_passes__pass_cse__a2 != py_local_src_teleon_synthesis_passes__pass_cse__b2 and (py_local_src_teleon_synthesis_passes__pass_cse__a2, py_local_src_teleon_synthesis_passes__pass_cse__b2) not in py_local_src_teleon_synthesis_passes__pass_cse__seen:
            py_local_src_teleon_synthesis_passes__pass_cse__seen.add((py_local_src_teleon_synthesis_passes__pass_cse__a2, py_local_src_teleon_synthesis_passes__pass_cse__b2))
            py_local_src_teleon_synthesis_passes__pass_cse__new_edges.append([py_local_src_teleon_synthesis_passes__pass_cse__a2, py_local_src_teleon_synthesis_passes__pass_cse__b2])
    return {"nodes": py_local_src_teleon_synthesis_passes__pass_cse__keep, "edges": py_local_src_teleon_synthesis_passes__pass_cse__new_edges}, True, f"merged {len(py_local_src_teleon_synthesis_passes__pass_cse__remap)} duplicate node(s)"


def py_function_src_teleon_synthesis_passes__pass_deterministic_replacement(py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__dag: dict, *, py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__substitutions: dict | None = None, **py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement___) -> tuple:
    """Replace an llm node with a DETERMINISTIC substitute (the core descent move — remove unnecessary intelligence).
    substitutions: {step: {component, plane}}. Behavior-changing → the manager re-verifies + cost-gates it."""
    py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__subs = (
        py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__substitutions
        or py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement___.get("substitutions")
        or {}
    )
    if not py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__subs:
        return py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__dag, False, "no substitutions provided"
    py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__nodes, py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__changed = [], 0
    for py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n in py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__dag["nodes"]:
        if py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n["step"] in py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__subs and py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n.get("plane") == "llm":
            py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__s = py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__subs[py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n["step"]]
            py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__nodes.append({**py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n, "component": py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__s["component"], "plane": py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__s.get("plane", "field_parsing"), "_replaced_from": "llm"})
            py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__changed += 1
        else:
            py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__nodes.append(py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__n)
    if not py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__changed:
        return py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__dag, False, "no llm node matched a substitution"
    return {"nodes": py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__nodes, "edges": [list(e) for e in py_arg_src_teleon_synthesis_passes__pass_deterministic_replacement__dag.get("edges", [])]}, True, f"replaced {py_local_src_teleon_synthesis_passes__pass_deterministic_replacement__changed} llm node(s) with deterministic"


py_var_src_teleon_synthesis_passes___PASS_TABLE = {"cse": (py_function_src_teleon_synthesis_passes__pass_cse, False), "deterministic_replacement": (py_function_src_teleon_synthesis_passes__pass_deterministic_replacement, True)}
py_const_src_teleon_synthesis_passes__DEFAULT_PASSES = ["cse", "deterministic_replacement"]


def py_function_src_teleon_synthesis_passes___cost(py_arg_src_teleon_synthesis_passes__cost__dag: dict, py_arg_src_teleon_synthesis_passes__cost__shard: str = "000") -> float:
    return SIM.simulate_dag(py_arg_src_teleon_synthesis_passes__cost__dag["nodes"], py_arg_src_teleon_synthesis_passes__cost__dag.get("edges"), shard=py_arg_src_teleon_synthesis_passes__cost__shard)["total_cost"]


def py_function_src_teleon_synthesis_passes__run_passes(py_arg_src_teleon_synthesis_passes__run_passes__dag: dict, *, passes: list | None = None, py_arg_src_teleon_synthesis_passes__run_passes__profile: PreferenceProfile | None = None,
               shard: str = "000", **py_arg_src_teleon_synthesis_passes__run_passes__opts) -> dict:
    """Run the pass pipeline. Each pass: legality (re-verify if behavior-changing) + a cost gate (never worsen the
    objective). Returns {dag, applied:[{pass, applied, note|reason}], before_cost, after_cost, savings}."""
    py_arg_src_teleon_synthesis_passes__run_passes__profile = py_arg_src_teleon_synthesis_passes__run_passes__profile or cost_first()
    py_local_src_teleon_synthesis_passes__run_passes__cur = {"nodes": list(py_arg_src_teleon_synthesis_passes__run_passes__dag["nodes"]), "edges": [list(e) for e in py_arg_src_teleon_synthesis_passes__run_passes__dag.get("edges", [])]}
    py_local_src_teleon_synthesis_passes__run_passes__before, py_local_src_teleon_synthesis_passes__run_passes__applied = py_function_src_teleon_synthesis_passes___cost(py_local_src_teleon_synthesis_passes__run_passes__cur, shard), []
    for py_local_src_teleon_synthesis_passes__run_passes__name in (passes or py_const_src_teleon_synthesis_passes__DEFAULT_PASSES):
        py_local_src_teleon_synthesis_passes__run_passes__fn, py_local_src_teleon_synthesis_passes__run_passes__reverify = py_var_src_teleon_synthesis_passes___PASS_TABLE[py_local_src_teleon_synthesis_passes__run_passes__name]
        py_local_src_teleon_synthesis_passes__run_passes__new, py_local_src_teleon_synthesis_passes__run_passes__changed, py_local_src_teleon_synthesis_passes__run_passes__note = py_local_src_teleon_synthesis_passes__run_passes__fn(py_local_src_teleon_synthesis_passes__run_passes__cur, **py_arg_src_teleon_synthesis_passes__run_passes__opts)
        if not py_local_src_teleon_synthesis_passes__run_passes__changed:
            py_local_src_teleon_synthesis_passes__run_passes__applied.append({"pass": py_local_src_teleon_synthesis_passes__run_passes__name, "applied": False, "reason": py_local_src_teleon_synthesis_passes__run_passes__note})
            continue
        if py_local_src_teleon_synthesis_passes__run_passes__reverify and not py_function_src_teleon_synthesis_dag_contract__verify_buildable_dag(py_local_src_teleon_synthesis_passes__run_passes__new["nodes"], py_local_src_teleon_synthesis_passes__run_passes__new.get("edges") or [])["verified_working"]:
            py_local_src_teleon_synthesis_passes__run_passes__applied.append({"pass": py_local_src_teleon_synthesis_passes__run_passes__name, "applied": False, "reason": "re-verify failed (illegal rewrite)"})
            continue
        if py_function_src_teleon_synthesis_passes___cost(py_local_src_teleon_synthesis_passes__run_passes__new, shard) > py_function_src_teleon_synthesis_passes___cost(py_local_src_teleon_synthesis_passes__run_passes__cur, shard) + 1e-12:        # cost gate: never worsen the objective
            py_local_src_teleon_synthesis_passes__run_passes__applied.append({"pass": py_local_src_teleon_synthesis_passes__run_passes__name, "applied": False, "reason": "would worsen the objective"})
            continue
        py_local_src_teleon_synthesis_passes__run_passes__cur = py_local_src_teleon_synthesis_passes__run_passes__new
        py_local_src_teleon_synthesis_passes__run_passes__applied.append({"pass": py_local_src_teleon_synthesis_passes__run_passes__name, "applied": True, "note": py_local_src_teleon_synthesis_passes__run_passes__note})
    py_local_src_teleon_synthesis_passes__run_passes__after = py_function_src_teleon_synthesis_passes___cost(py_local_src_teleon_synthesis_passes__run_passes__cur, shard)
    return {"dag": py_local_src_teleon_synthesis_passes__run_passes__cur, "applied": py_local_src_teleon_synthesis_passes__run_passes__applied, "before_cost": round(py_local_src_teleon_synthesis_passes__run_passes__before, 8), "after_cost": round(py_local_src_teleon_synthesis_passes__run_passes__after, 8),
            "savings": round(py_local_src_teleon_synthesis_passes__run_passes__before - py_local_src_teleon_synthesis_passes__run_passes__after, 8), "serves_truth": False}
