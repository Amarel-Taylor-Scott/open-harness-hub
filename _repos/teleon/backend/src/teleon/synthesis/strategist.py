"""src.teleon.synthesis.strategist — resilient synthesis: when backtracking exhausts the tree, ESCAPE the dead-end.

Owner: backtracking tries alternatives WITHIN a plan; but if NO branch of the current plan solves, we need logic to
SPROUT new branches, BREAK OUT of the current shape, or try something COMPLETELY NEW before giving up. This runs an
escalating ladder of escape strategies, each producing a NEW plan that gets its own versioned SynthesisTree + trace; the
first that solves wins; if all are exhausted it reports an HONEST no-solution (never fabricates). Every attempt (winners +
losers) is kept (lossless). Strategies are pluggable; the defaults are registry-driven (sprout same-plane options -> add
external-API rungs -> add module bundles -> reframe to a different ladder -> ask the LLM for a novel plan). serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
from dataclasses import dataclass
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis.synthesis_trace import py_class_src_teleon_synthesis_synthesis_trace__SynthesisTrace
from src.teleon.synthesis.synthesis_tree import py_class_src_teleon_synthesis_synthesis_tree__SynthesisTree

py_var_src_teleon_synthesis_strategist___REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])


def py_function_src_teleon_synthesis_strategist___load(py_arg_src_teleon_synthesis_strategist__load__name):
    return json.loads((_resource("architecture") / py_arg_src_teleon_synthesis_strategist__load__name).read_text(encoding="utf-8"))


@dataclass
class py_class_src_teleon_synthesis_strategist__EscapeAttempt:
    strategy: str
    points: list
    solved: bool
    trace: py_class_src_teleon_synthesis_synthesis_trace__SynthesisTrace


def py_function_src_teleon_synthesis_strategist__resilient_synthesize(py_arg_src_teleon_synthesis_strategist__resilient_synthesize__base_points, py_arg_src_teleon_synthesis_strategist__resilient_synthesize__tester, *, intent: str = "", strategies=()):
    """Try base_points; on failure, try each escape strategy (a fn(history_of_tried_plans) -> new_points | None) in order.
    Returns (solution | None, winning_strategy | None, attempts). attempts keeps EVERY plan tried (lossless)."""
    py_local_src_teleon_synthesis_strategist__resilient_synthesize__attempts: list[py_class_src_teleon_synthesis_strategist__EscapeAttempt] = []

    def run(name, points):
        t = py_class_src_teleon_synthesis_synthesis_tree__SynthesisTree()
        py_local_src_teleon_synthesis_strategist__resilient_synthesize_run__sol = t.synthesize(points, py_arg_src_teleon_synthesis_strategist__resilient_synthesize__tester)
        py_local_src_teleon_synthesis_strategist__resilient_synthesize__attempts.append(py_class_src_teleon_synthesis_strategist__EscapeAttempt(name, points, py_local_src_teleon_synthesis_strategist__resilient_synthesize_run__sol is not None, py_class_src_teleon_synthesis_synthesis_trace__SynthesisTrace.from_tree(t, intent=intent, strategy=name)))
        return py_local_src_teleon_synthesis_strategist__resilient_synthesize_run__sol

    py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol = run("base", py_arg_src_teleon_synthesis_strategist__resilient_synthesize__base_points)
    if py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol is not None:
        return py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol, "base", py_local_src_teleon_synthesis_strategist__resilient_synthesize__attempts
    py_local_src_teleon_synthesis_strategist__resilient_synthesize__tried = [py_arg_src_teleon_synthesis_strategist__resilient_synthesize__base_points]
    for py_local_src_teleon_synthesis_strategist__resilient_synthesize__name, py_local_src_teleon_synthesis_strategist__resilient_synthesize__fn in strategies:
        py_local_src_teleon_synthesis_strategist__resilient_synthesize__new_points = py_local_src_teleon_synthesis_strategist__resilient_synthesize__fn(py_local_src_teleon_synthesis_strategist__resilient_synthesize__tried)
        if not py_local_src_teleon_synthesis_strategist__resilient_synthesize__new_points or py_local_src_teleon_synthesis_strategist__resilient_synthesize__new_points in py_local_src_teleon_synthesis_strategist__resilient_synthesize__tried:
            continue                          # nothing new to try with this strategy
        py_local_src_teleon_synthesis_strategist__resilient_synthesize__tried.append(py_local_src_teleon_synthesis_strategist__resilient_synthesize__new_points)
        py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol = run(py_local_src_teleon_synthesis_strategist__resilient_synthesize__name, py_local_src_teleon_synthesis_strategist__resilient_synthesize__new_points)
        if py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol is not None:
            return py_local_src_teleon_synthesis_strategist__resilient_synthesize__sol, py_local_src_teleon_synthesis_strategist__resilient_synthesize__name, py_local_src_teleon_synthesis_strategist__resilient_synthesize__attempts        # escaped the dead-end
    return None, None, py_local_src_teleon_synthesis_strategist__resilient_synthesize__attempts               # honest: exhausted backtracking + every escape strategy


# ── default registry-driven escape strategies (real; each takes the history of tried plans) ───────────────────────
def py_function_src_teleon_synthesis_strategist___planes_for_intent(py_arg_src_teleon_synthesis_strategist__planes_for_intent__intent: str) -> dict:
    return {n["id"]: n.get("planes", []) for n in I.py_function_src_teleon_synthesis_intent_to_dag__build_dag(py_arg_src_teleon_synthesis_strategist__planes_for_intent__intent)["nodes"]}


def py_function_src_teleon_synthesis_strategist__default_strategies(py_arg_src_teleon_synthesis_strategist__default_strategies__intent: str):
    py_local_src_teleon_synthesis_strategist__default_strategies__base = I.py_function_src_teleon_synthesis_intent_to_dag__build_dag(py_arg_src_teleon_synthesis_strategist__default_strategies__intent)
    py_local_src_teleon_synthesis_strategist__default_strategies__base_pts = {n["id"]: list(n["options"]) for n in py_local_src_teleon_synthesis_strategist__default_strategies__base["nodes"]}
    py_local_src_teleon_synthesis_strategist__default_strategies__planes = py_function_src_teleon_synthesis_strategist___planes_for_intent(py_arg_src_teleon_synthesis_strategist__default_strategies__intent)
    py_local_src_teleon_synthesis_strategist__default_strategies__tools = py_function_src_teleon_synthesis_strategist___load("tool_registry.json")["tools"]
    py_local_src_teleon_synthesis_strategist__default_strategies__ext = py_function_src_teleon_synthesis_strategist___load("external_api_registry.json")["apis"]
    py_local_src_teleon_synthesis_strategist__default_strategies__bundles = py_function_src_teleon_synthesis_strategist___load("module_bundles.json")["bundles"]

    def sprout_same_plane(py_arg_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane___history):
        """SPROUT: add more same-plane components to each node (new branches that weren't in the original plan)."""
        py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__out = []
        for py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__nid, py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__opts in py_local_src_teleon_synthesis_strategist__default_strategies__base_pts.items():
            py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__pls = set(py_local_src_teleon_synthesis_strategist__default_strategies__planes.get(py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__nid, []))
            py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__extra = [t["id"] for t in py_local_src_teleon_synthesis_strategist__default_strategies__tools if t.get("plane") in py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__pls and t["id"] not in py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__opts]
            py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__out.append((py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__nid, py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__opts + py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__extra))
        return py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__out if any(len(o) > len(py_local_src_teleon_synthesis_strategist__default_strategies__base_pts[i]) for i, o in py_local_src_teleon_synthesis_strategist__default_strategies_sprout_same_plane__out) else None

    def add_external_apis(py_arg_src_teleon_synthesis_strategist__default_strategies_add_external_apis___history):
        """BREAK OUT: try hosted external-API components for the node's planes (a different kind of rung)."""
        py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__out, py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__changed = [], False
        for py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__nid, py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__opts in py_local_src_teleon_synthesis_strategist__default_strategies__base_pts.items():
            py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__pls = set(py_local_src_teleon_synthesis_strategist__default_strategies__planes.get(py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__nid, []))
            py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__api = [a["id"] for a in py_local_src_teleon_synthesis_strategist__default_strategies__ext if a["plane"] in py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__pls and a["id"] not in py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__opts]
            if py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__api:
                py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__changed = True
            py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__out.append((py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__nid, py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__opts + py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__api))
        return py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__out if py_local_src_teleon_synthesis_strategist__default_strategies_add_external_apis__changed else None

    def add_bundles(py_arg_src_teleon_synthesis_strategist__default_strategies_add_bundles___history):
        """try a vetted module BUNDLE as an extra option on a matching node."""
        py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__out, py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__changed = [], False
        for py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__nid, py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__opts in py_local_src_teleon_synthesis_strategist__default_strategies__base_pts.items():
            py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__pls = set(py_local_src_teleon_synthesis_strategist__default_strategies__planes.get(py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__nid, []))
            py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__comps = [c for b in py_local_src_teleon_synthesis_strategist__default_strategies__bundles if py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__pls & set(b["planes"]) for c in b["components"] if c not in py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__opts]
            if py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__comps:
                py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__changed = True
            py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__out.append((py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__nid, py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__opts + py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__comps))
        return py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__out if py_local_src_teleon_synthesis_strategist__default_strategies_add_bundles__changed else None

    def reframe_ladder(py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder___history):
        """SOMETHING COMPLETELY NEW: decompose with a DIFFERENT capability ladder (a different shape entirely)."""
        py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__ladders = {l["capability"]: l for l in py_function_src_teleon_synthesis_strategist___load("capability_ladders.json")["ladders"]}
        py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cur = I.py_function_src_teleon_synthesis_intent_to_dag__pick_ladder(py_arg_src_teleon_synthesis_strategist__default_strategies__intent)
        py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cur_id = py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cur["capability"] if py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cur else None
        py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__t = (py_arg_src_teleon_synthesis_strategist__default_strategies__intent or "").lower()
        for py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cid, py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__lad in py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__ladders.items():
            if py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cid == py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cur_id:
                continue
            if any(w in py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__t for w in py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__cid.split("_")):           # a plausible alternative decomposition
                py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__rungs = sorted(py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__lad["rungs"], key=lambda py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r: py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r["cost_rank"])
                return [(py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r["tier"], list(py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r.get("tools", [])) + list(py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r.get("external_apis", [])) or ["llm:" + (py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r.get("planes", ["model"])[0])]) for py_arg_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__r in py_local_src_teleon_synthesis_strategist__default_strategies_reframe_ladder__rungs]
        return None

    def llm_novel(py_arg_src_teleon_synthesis_strategist__default_strategies_llm_novel___history):
        """LAST: ask the frontier LLM (port) for a brand-new plan. Honest: returns None when no LLM is wired (no fabrication)."""
        return None   # the LLM port fills this when available; offline it yields nothing rather than inventing a plan

    return [("sprout_same_plane", sprout_same_plane), ("add_external_apis", add_external_apis),
            ("add_bundles", add_bundles), ("reframe_ladder", reframe_ladder), ("llm_novel", llm_novel)]
