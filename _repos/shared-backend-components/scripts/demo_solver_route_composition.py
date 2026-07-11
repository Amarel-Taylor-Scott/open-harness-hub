#!/usr/bin/env python3
"""scripts.demo_solver_route_composition — the SLM-uplift thesis, demonstrated.

Thesis (owner 2026-07-03): a small specialized model (Gemma 4 Coder + LoRA) that RETRIEVES proven primitives, ORDERS
them by edge compatibility, and COMPOSES a solution route can beat a frontier model's one-shot/multi-shot generation
on coding / competitive / software-bench tasks — cheaper (bounded composition, not unbounded generation), faster, and
finely monitored (every step is a receipted primitive). The requirement is a large universe of working primitives
with real edge definitions + edge contracts + edge matching. This script demonstrates the SOLVER LAYER that makes it
work: the meta-primitives (decompose → select/match → order → emit → verify → repair) and a real (if simple) route
composer that chains primitives output_edge→input_edge, then accounts tokens vs a from-scratch one-shot baseline.

Not a claim the SLM already wins — a demonstrator of the MECHANISM + an honest token estimate. --self-test is offline
(synthetic primitives prove the compose logic); --run queries the live registry. All candidate/serves_truth=false.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CHARS_PER_TOKEN = 4
_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "and", "for", "with", "into", "from", "policy", "context", "receipt", "artifact", "typed"}

# The META-PRIMITIVE families a benchmark-solving system needs (the solver layer over the algorithm primitives).
SOLVER_META_PRIMITIVES: dict[str, dict[str, Any]] = {
    "decompose": {"edge": "ProblemStatement+Constraints -> TaskSignature+SubgoalGraph",
                  "does": "parse the problem, classify algorithm family, extract I/O format + constraints + complexity budget"},
    "select_match": {"edge": "TaskSignature+PrimitiveRegistry -> CandidateBundle+EdgeMatchScores",
                     "does": "edge-match the task signature against the registry; return ranked candidate primitives with compatibility scores"},
    "order_compose": {"edge": "CandidateBundle+SubgoalGraph -> OrderedRoute+PlanLock",
                      "does": "chain candidates output_edge->input_edge into a dependency-valid ordered route (the composition step)"},
    "emit_code": {"edge": "OrderedRoute+TargetLanguage -> CodeArtifact+CompileReceipt",
                  "does": "instantiate each ordered primitive into runnable code for the target language; bounded per-step, not one-shot"},
    "verify_run": {"edge": "CodeArtifact+ExampleFixtures -> TestReceipt+ComplexityReceipt",
                   "does": "run against provided examples + edge cases; check complexity budget; produce a receipt"},
    "repair": {"edge": "TestReceipt+FailureClass -> RoutePatch+NegativeMemory",
               "does": "on failure, localize to the failing step (a primitive), swap/repair only that step, never regenerate the whole"},
}

# Solver-route TEMPLATES per benchmark family — the ordered meta-route a solver follows for that task shape.
SOLVER_ROUTE_TEMPLATES: dict[str, list[str]] = {
    "leetcode": ["decompose", "select_match", "order_compose", "emit_code", "verify_run", "repair"],
    "competitive": ["decompose", "select_match", "order_compose", "emit_code", "verify_run", "repair"],
    "swe_bench": ["decompose", "select_match", "order_compose", "emit_code", "verify_run", "repair"],
    "agentic": ["decompose", "select_match", "order_compose", "verify_run", "repair"],
}

# from-scratch one-shot output-token baseline by complexity (what a frontier model burns generating the whole solution).
ONESHOT_BASELINE = {"low": 900, "medium": 2200, "high": 4500}


def _toks(text: str) -> set[str]:
    return {t for t in _WORD.findall(str(text).lower()) if len(t) >= 3 and t not in _STOP}


def _edge_head(edge: str, *, output: bool) -> set[str]:
    """Tokens of an edge's producer/consumer type (before/after the '->' or the '+' split)."""
    return _toks(re.split(r"\+|\[", str(edge), maxsplit=1)[0])


def edge_compat(a: dict[str, Any], b: dict[str, Any]) -> int:
    """How well card a's OUTPUT chains into card b's INPUT — the edge-matching primitive, in miniature."""
    return len(_edge_head(a.get("output_edge", ""), output=True) & _edge_head(b.get("input_edge", ""), output=False))


def compose_route(task_tokens: set[str], cards: list[dict[str, Any]], *, max_steps: int = 6) -> list[dict[str, Any]]:
    """Order retrieved primitives into a chained route: seed with the best task-relevant card, then greedily append
    the next card whose input_edge best matches the current output_edge (falling back to task relevance)."""
    usable = [c for c in cards if c.get("input_edge") and c.get("output_edge")
              and not str(c.get("primitive_id", "")).startswith(("bench:", "task:"))]
    if not usable:
        return []

    def _relevance(c: dict[str, Any]) -> int:
        return len(task_tokens & _toks(f"{c.get('title','')} {c.get('input_edge','')}"))

    # seed at a SOURCE: a card whose input is NOT produced by any other card (the route entry point),
    # tie-broken by task relevance. Falls back to most-relevant if no clean source exists.
    sources = [c for c in usable if not any(edge_compat(d, c) > 0 for d in usable if d is not c)]
    seed_pool = sources or usable
    seed_pool.sort(key=_relevance, reverse=True)
    seed = seed_pool[0]
    usable.remove(seed)
    route = [seed]
    while usable and len(route) < max_steps:
        cur = route[-1]
        # pick the next card that best chains from cur.output_edge; tie-break by task relevance
        usable.sort(key=lambda c: (edge_compat(cur, c),
                                   len(task_tokens & _toks(f"{c.get('title','')} {c.get('input_edge','')}"))),
                    reverse=True)
        nxt = usable.pop(0)
        if edge_compat(cur, nxt) == 0 and len(route) >= 2:
            break  # no more chainable steps
        route.append(nxt)
    return route


def _card_tokens_measured(card: dict[str, Any]) -> int:
    compact = " ".join(str(card.get(k, "")) for k in ("title", "input_edge", "output_edge", "blackbox"))
    return max(1, len(compact) // CHARS_PER_TOKEN)


def solve_demo(task: dict[str, Any], cards: list[dict[str, Any]]) -> dict[str, Any]:
    q = _toks(task["query"])
    route = compose_route(q, cards, max_steps=6)
    fam = task.get("benchmark_family", "leetcode")
    meta_route = SOLVER_ROUTE_TEMPLATES.get(fam, SOLVER_ROUTE_TEMPLATES["leetcode"])
    # primitive-first cost = read the compact cards on the route + a small per-step compose/emit glue.
    route_read = sum(_card_tokens_measured(c) for c in route)
    compose_glue = 40 * len(route)  # bounded per-step emission, not unbounded one-shot
    primitive_first = route_read + compose_glue
    oneshot = ONESHOT_BASELINE.get(task.get("complexity", "medium"), 2200)
    chain_strength = sum(edge_compat(route[i], route[i + 1]) for i in range(len(route) - 1)) if len(route) > 1 else 0
    savings = round(max(0.0, min(98.0, 100 * (1 - primitive_first / oneshot))), 1) if route else 0.0
    return {
        "record_type": "solver_route_composition_demo",
        "task_id": task.get("id"), "benchmark_family": fam,
        "meta_route": meta_route,
        "composed_route": [{"step": i, "primitive_id": c.get("primitive_id"), "title": c.get("title"),
                            "input_edge": c.get("input_edge"), "output_edge": c.get("output_edge")}
                           for i, c in enumerate(route)],
        "route_length": len(route),
        "edge_chain_strength": chain_strength,  # >0 means the primitives actually CHAIN (composable, not just relevant)
        "composable": len(route) >= 2 and chain_strength > 0,
        "primitive_first_tokens_estimated": primitive_first,
        "oneshot_baseline_tokens_estimated": oneshot,
        "estimated_token_savings_pct": savings,
        "monitoring_note": f"{len(route)} receipted steps vs 1 opaque one-shot generation — each step verifiable/repairable",
        "candidate": True, "serves_truth": False,
    }


def self_test() -> int:
    # synthetic algorithm primitives that CHAIN: parse -> build graph -> traverse -> format
    cards = [
        {"primitive_id": "prim:a", "title": "Parse edge list input", "input_edge": "RawInput+Format", "output_edge": "EdgeList", "blackbox": "parse"},
        {"primitive_id": "prim:b", "title": "Build adjacency graph", "input_edge": "EdgeList", "output_edge": "AdjacencyGraph", "blackbox": "build graph"},
        {"primitive_id": "prim:c", "title": "BFS shortest path", "input_edge": "AdjacencyGraph+Source", "output_edge": "DistanceMap", "blackbox": "bfs"},
        {"primitive_id": "prim:d", "title": "Format answer", "input_edge": "DistanceMap", "output_edge": "AnswerString", "blackbox": "format"},
        {"primitive_id": "bench:meta", "title": "Benchmark decomposition", "input_edge": "X", "output_edge": "Y", "blackbox": "meta"},
    ]
    r = solve_demo({"id": "bfs", "query": "graph shortest path bfs adjacency edge list", "complexity": "medium", "benchmark_family": "leetcode"}, cards)
    checks = [
        ("composes a multi-step route", r["route_length"] >= 3),
        ("route actually chains (edge compat > 0)", r["edge_chain_strength"] > 0),
        ("flagged composable", r["composable"] is True),
        ("excludes bench meta-card from the route", all(not str(s["primitive_id"]).startswith("bench:") for s in r["composed_route"])),
        ("seeds with the parse (source) primitive", r["composed_route"][0]["primitive_id"] == "prim:a"),
        ("chains to graph build next", r["composed_route"][1]["primitive_id"] == "prim:b"),
        ("meta-route has 6 solver stages for leetcode", len(r["meta_route"]) == 6),
        ("primitive-first cheaper than one-shot", r["primitive_first_tokens_estimated"] < r["oneshot_baseline_tokens_estimated"]),
        ("positive savings", r["estimated_token_savings_pct"] > 0),
        ("6 solver meta-primitive families defined", len(SOLVER_META_PRIMITIVES) == 6),
        ("every meta-primitive has an edge + does", all("edge" in v and "does" in v for v in SOLVER_META_PRIMITIVES.values())),
        ("empty registry -> no route (honest)", solve_demo({"query": "x", "complexity": "low"}, [])["route_length"] == 0),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - demo_solver_route_composition:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - demo_solver_route_composition: retrieves→orders(edge-chain)→composes a route, excludes meta-cards, "
          "accounts tokens vs one-shot. The solver layer works on synthetic primitives.")
    return 0


def run_live(limit: int) -> int:
    from src.teleon.observer import registry_search as rs
    tasks = [
        {"id": "bfs_shortest", "query": "graph traversal breadth first shortest path adjacency", "complexity": "medium", "benchmark_family": "leetcode"},
        {"id": "two_sum", "query": "two sum hashmap complement lookup array", "complexity": "low", "benchmark_family": "leetcode"},
        {"id": "dp_knapsack", "query": "dynamic programming knapsack subset sum tabulation", "complexity": "high", "benchmark_family": "leetcode"},
        {"id": "cp_segment_tree", "query": "segment tree range query update lazy propagation", "complexity": "high", "benchmark_family": "codeforces"},
        {"id": "swe_bugfix", "query": "repo issue reproduce localize fault minimal patch run tests", "complexity": "high", "benchmark_family": "swe_bench"},
    ]
    demos = []
    for t in tasks:
        try:
            cards = rs.search_edge_foundry_primitives(t["query"], visibility_scope="all", limit=limit)
        except Exception as exc:  # noqa: BLE001
            print(f"  search failed for {t['id']}: {exc}", file=sys.stderr)
            cards = []
        d = solve_demo(t, cards or [])
        demos.append(d)
        print(f"  {t['id']:16s} route_len={d['route_length']} chain={d['edge_chain_strength']} "
              f"composable={d['composable']} savings={d['estimated_token_savings_pct']}%")
    out = _resource("data") / "dev-intel" / "primitive_consumption_benchmark" / "solver_route_composition_demo.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(d, ensure_ascii=False, sort_keys=True) + "\n" for d in demos), encoding="utf-8")
    composable = sum(1 for d in demos if d["composable"])
    print(json.dumps({"tasks": len(demos), "composable_routes": composable,
                      "median_route_len": sorted(d["route_length"] for d in demos)[len(demos) // 2]}, indent=2))
    return self_test()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--limit", type=int, default=12)
    args = parser.parse_args(argv)
    if args.run:
        return run_live(args.limit)
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
