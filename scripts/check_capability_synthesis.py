#!/usr/bin/env python3
"""check_capability_synthesis — the capability-synthesis pipeline + the versioned backtracking engine are real.

Owner: intent -> outline -> fill -> DAG (test each node) -> 5W1H verify ladder -> alternatives ladder, with every decision
BRANCHED + VERSIONED and a dead-end leaf JUMPING BACK UP to try another branch (lossless). Proves: the spec has the 5
stages + the 5W1H verify ladder + the alternatives ladder + branching{versioned,backtrack,lossless}; the engine
(synthesis_tree) actually backtracks + versions + keeps losers (toy space, deterministic); intent_to_dag builds a real DAG
from the ladders + emits 5W1H + alternatives + the 5 frontier prompts; module_bundles reference real components. serves_truth=false.

  python3 scripts/check_capability_synthesis.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from src.teleon.synthesis import intent_to_dag as I
from src.teleon.synthesis.synthesis_tree import Attempt, SynthesisTree

REPO = Path(__file__).resolve().parents[1]


def _load(name):
    return json.loads((REPO / "architecture" / name).read_text(encoding="utf-8"))


def _self_test() -> int:
    spec = _load("capability_synthesis_pipeline.json")
    bundles = _load("module_bundles.json")["bundles"]
    tool_ids = {t["id"] for t in _load("tool_registry.json")["tools"]}
    planes = {p["plane"] for p in _load("tool_planes.json")["planes"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # ── spec: the owner's 5 stages + the two ladders + branching ──────────────────────────────────────────────
    stages = {s["id"] for s in spec["stages"]}
    ck("5 stages present (outline/fill/dag_test/verify/alternatives)",
       stages == {"outline", "fill", "dag_test", "verify", "alternatives"}, str(stages))
    ck("verify ladder is 5W1H", set(spec["verification_ladder"]["dimensions"]) == {"who", "what", "where", "when", "why", "how"})
    ck("alternatives ladder asks best-way/alternatives/pros-cons", {"best_way", "alternatives", "pros_cons"} <= set(spec["alternatives_ladder"]["dimensions"]))
    ck("branching is versioned + backtrack + lossless",
       all(spec["branching"].get(k) for k in ("versioned", "backtrack", "lossless")))

    # ── engine: versioned BACKTRACKING over a toy space (deterministic) ───────────────────────────────────────
    points = [("A", ["a1", "a2"]), ("B", ["b1", "b2"])]
    # a1 component is broken; only the full assembly [a2,b2] works -> must backtrack past a1, and past a2/b1
    def tester(path, partial):
        ids = [f"{d.id}={d.choice}" for d in path]
        if partial:
            return Attempt("A=a1" not in ids, "a1 broken" if "A=a1" in ids else "ok")
        return Attempt(ids == ["A=a2", "B=b2"], "assembly")
    t = SynthesisTree()
    sol = t.synthesize(points, tester)
    s = t.summary()
    ck("finds the only working assembly by backtracking", [f"{d.id}={d.choice}" for d in sol] == ["A=a2", "B=b2"])
    ck("solution is versioned (path id)", s["solution_version"] == "A=a2/B=b2")
    ck("dead-ends recorded (a1 component + a2/b1 assembly)", set(s["dead_ends"]) == {"A=a1", "A=a2/B=b1"})
    ck("lossless: every branch kept (winners + losers)", s["branches_explored"] >= 4 and s["lossless"])

    # no-solution case: honest, never fabricated; abandoned branch recorded (jumped back up + gave up honestly)
    t2 = SynthesisTree()
    sol2 = t2.synthesize(points, lambda path, partial: Attempt(partial))   # every component ok, no assembly ok
    ck("honest no-solution (never fabricates a success)", sol2 is None and t2.summary()["solved"] is False)
    ck("backtracked: parent branch marked abandoned", "A=a2" in t2.summary()["abandoned"])

    # ── intent_to_dag: a real DAG + 5W1H + alternatives + the 5 prompts from a real ladder ────────────────────
    dag = I.build_dag("extract fields from these invoices into our schema")
    ck("intent -> a non-empty DAG of nodes+edges", dag["nodes"] and len(dag["edges"]) == len(dag["nodes"]) - 1)
    bad = sorted({tid for n in dag["nodes"] for tid in n["options"]
                  if tid not in tool_ids and ":" not in tid and not tid.endswith("_api")
                  and tid not in {p.get("id") for p in _load("ocr_provider_registry.json")["providers"]}})
    ck("DAG node options are real components", not bad, str(bad))
    pts = I.decision_points("extract fields from these invoices into our schema")
    ck("decision points feed the synthesis tree (every point has >=1 option)", pts and all(o for _, o in pts))
    vq = I.verification_ladder(dag["nodes"][0])
    ck("verification ladder emits 5W1H", set(vq["questions"]) == {"who", "what", "where", "when", "why", "how"})
    ck("alternatives ladder emits same-plane alternatives + critique prompts",
       "alternatives_same_plane" in I.alternatives_ladder(dag["nodes"][0]))
    fp = I.frontier_prompts("find public statements by X and flag contradictions")
    ck("5 frontier prompts in the owner's order", [p["stage"] for p in fp] == ["outline", "fill", "dag_test", "verify", "alternatives"])

    # ── module bundles reference real components/planes ───────────────────────────────────────────────────────
    ck(f"grouped-module bundles present ({len(bundles)})", len(bundles) >= 6)
    all_components = tool_ids | {p.get("id") for p in _load("ocr_provider_registry.json")["providers"]}
    bad_b = sorted({c for b in bundles for c in b["components"] if c not in all_components})
    ck("bundle components are real registry ids (tool_registry / ocr providers)", not bad_b, str(bad_b))
    bad_bp = sorted({pl for b in bundles for pl in b["planes"] if pl not in planes})
    ck("bundle planes are declared", not bad_bp, str(bad_bp))
    ck("serves_truth=false", spec.get("serves_truth") is False and _load("module_bundles.json").get("serves_truth") is False)

    print("\n" + ("PASS - check_capability_synthesis: 5-stage pipeline + 5W1H + alternatives ladders; engine backtracks + "
                  "versions + keeps losers (lossless); intent->DAG real; bundles real." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
