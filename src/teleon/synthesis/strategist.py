"""src.teleon.synthesis.strategist — resilient synthesis: when backtracking exhausts the tree, ESCAPE the dead-end.

Owner: backtracking tries alternatives WITHIN a plan; but if NO branch of the current plan solves, we need logic to
SPROUT new branches, BREAK OUT of the current shape, or try something COMPLETELY NEW before giving up. This runs an
escalating ladder of escape strategies, each producing a NEW plan that gets its own versioned SynthesisTree + trace; the
first that solves wins; if all are exhausted it reports an HONEST no-solution (never fabricates). Every attempt (winners +
losers) is kept (lossless). Strategies are pluggable; the defaults are registry-driven (sprout same-plane options -> add
external-API rungs -> add module bundles -> reframe to a different ladder -> ask the LLM for a novel plan). serves_truth=false.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis.synthesis_trace import SynthesisTrace
from src.teleon.synthesis.synthesis_tree import SynthesisTree

_REPO = Path(__file__).resolve().parents[3]


def _load(name):
    return json.loads((_REPO / "architecture" / name).read_text(encoding="utf-8"))


@dataclass
class EscapeAttempt:
    strategy: str
    points: list
    solved: bool
    trace: SynthesisTrace


def resilient_synthesize(base_points, tester, *, intent: str = "", strategies=()):
    """Try base_points; on failure, try each escape strategy (a fn(history_of_tried_plans) -> new_points | None) in order.
    Returns (solution | None, winning_strategy | None, attempts). attempts keeps EVERY plan tried (lossless)."""
    attempts: list[EscapeAttempt] = []

    def run(name, points):
        t = SynthesisTree()
        sol = t.synthesize(points, tester)
        attempts.append(EscapeAttempt(name, points, sol is not None, SynthesisTrace.from_tree(t, intent=intent, strategy=name)))
        return sol

    sol = run("base", base_points)
    if sol is not None:
        return sol, "base", attempts
    tried = [base_points]
    for name, fn in strategies:
        new_points = fn(tried)
        if not new_points or new_points in tried:
            continue                          # nothing new to try with this strategy
        tried.append(new_points)
        sol = run(name, new_points)
        if sol is not None:
            return sol, name, attempts        # escaped the dead-end
    return None, None, attempts               # honest: exhausted backtracking + every escape strategy


# ── default registry-driven escape strategies (real; each takes the history of tried plans) ───────────────────────
def _planes_for_intent(intent: str) -> dict:
    return {n["id"]: n.get("planes", []) for n in I.build_dag(intent)["nodes"]}


def default_strategies(intent: str):
    base = I.build_dag(intent)
    base_pts = {n["id"]: list(n["options"]) for n in base["nodes"]}
    planes = _planes_for_intent(intent)
    tools = _load("tool_registry.json")["tools"]
    ext = _load("external_api_registry.json")["apis"]
    bundles = _load("module_bundles.json")["bundles"]

    def sprout_same_plane(_history):
        """SPROUT: add more same-plane components to each node (new branches that weren't in the original plan)."""
        out = []
        for nid, opts in base_pts.items():
            pls = set(planes.get(nid, []))
            extra = [t["id"] for t in tools if t.get("plane") in pls and t["id"] not in opts]
            out.append((nid, opts + extra))
        return out if any(len(o) > len(base_pts[i]) for i, o in out) else None

    def add_external_apis(_history):
        """BREAK OUT: try hosted external-API components for the node's planes (a different kind of rung)."""
        out, changed = [], False
        for nid, opts in base_pts.items():
            pls = set(planes.get(nid, []))
            api = [a["id"] for a in ext if a["plane"] in pls and a["id"] not in opts]
            if api:
                changed = True
            out.append((nid, opts + api))
        return out if changed else None

    def add_bundles(_history):
        """try a vetted module BUNDLE as an extra option on a matching node."""
        out, changed = [], False
        for nid, opts in base_pts.items():
            pls = set(planes.get(nid, []))
            comps = [c for b in bundles if pls & set(b["planes"]) for c in b["components"] if c not in opts]
            if comps:
                changed = True
            out.append((nid, opts + comps))
        return out if changed else None

    def reframe_ladder(_history):
        """SOMETHING COMPLETELY NEW: decompose with a DIFFERENT capability ladder (a different shape entirely)."""
        ladders = {l["capability"]: l for l in _load("capability_ladders.json")["ladders"]}
        cur = I.pick_ladder(intent)
        cur_id = cur["capability"] if cur else None
        t = (intent or "").lower()
        for cid, lad in ladders.items():
            if cid == cur_id:
                continue
            if any(w in t for w in cid.split("_")):           # a plausible alternative decomposition
                rungs = sorted(lad["rungs"], key=lambda r: r["cost_rank"])
                return [(r["tier"], list(r.get("tools", [])) + list(r.get("external_apis", [])) or ["llm:" + (r.get("planes", ["model"])[0])]) for r in rungs]
        return None

    def llm_novel(_history):
        """LAST: ask the frontier LLM (port) for a brand-new plan. Honest: returns None when no LLM is wired (no fabrication)."""
        return None   # the LLM port fills this when available; offline it yields nothing rather than inventing a plan

    return [("sprout_same_plane", sprout_same_plane), ("add_external_apis", add_external_apis),
            ("add_bundles", add_bundles), ("reframe_ladder", reframe_ladder), ("llm_novel", llm_novel)]
