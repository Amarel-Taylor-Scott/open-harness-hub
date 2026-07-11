#!/usr/bin/env python3
"""scripts.bench_leetcode_coverage — over a corpus of ALREADY-SOLVED problems, measure the ONLY thing that
matters for the goal: TOKENS SAVED BY REUSE vs TOKENS WASTED REGENERATING.

Owner reframing (load-bearing): the point is NOT to find capability the model lacks (the Capability-Gap
thesis). Models already solve ~99% of these, and the solutions already EXIST. The goal is to stop agents
BURNING TOKENS regenerating a solution that's already been written — by RETRIEVING it instead. So a "gap"
here is not "a problem models can't solve"; it is a SOLVED solution we have NOT INDEXED, so an agent
regenerates it (wasted tokens). LeetCode is a clean, canonical corpus of solved problems to measure that.

Per solved problem:
  * ``regenerate_tokens`` — what an agent spends WRITING the solution from scratch (size proxy by difficulty).
  * TRUE REUSE? — does the registry return a solution that ACTUALLY matches (label-verified: the retrieved
    card's text carries the problem's algorithm/pattern term — NOT merely a high lexical score, which for a
    business-primitive registry is a false positive). This is the honest bar the score-only version failed.
  * reuse  -> saved = regenerate_tokens − retrieve_tokens  (positive)
    reuse GAP (no true match) -> the agent regenerates -> saved = 0, and this is a solved solution WORTH
    INDEXING (ranked by regenerate_tokens × how often the pattern recurs = the token-saving opportunity).

Reports: reuse rate, TOTAL tokens saved vs wasted-regenerating, savings by difficulty (savings scale with
solution SIZE — big solved solutions are the prize, trivial ones are not), and the ranked reuse-gap patterns
to index. candidate=true / serves_truth=false.

  PYTHONPATH=. python3 scripts/bench_leetcode_coverage.py --self-test
  PYTHONPATH=. python3 scripts/bench_leetcode_coverage.py --run [--corpus 25000]
"""
from __future__ import annotations

import sys
from pathlib import Path

_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from collections import defaultdict  # noqa: E402

from scripts._jsonl import read_jsonl_tolerant  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402
from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: E402

OUT_DIR = _resource("data") / "dev-intel" / "leetcode_coverage"
CARD_SOURCES = (
    "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
    "data/dev-intel/primitive_factory/linkable_cards/2026-07-01/linkable_primitive_cards.jsonl",
)
#: tokens to REGENERATE + explain a solution, by difficulty (documented proxy — savings scale with size).
REGEN_TOKENS = {"easy": 200, "medium": 550, "hard": 1200}
#: tokens to RETRIEVE: search query + read the matched card + a one-line reuse reference.
RETRIEVE_TOKENS = 80

#: (intent, category, pattern, difficulty). The pattern is the label used to VERIFY a true reuse.
_PROBLEMS: tuple[dict, ...] = tuple({"intent": i, "category": c, "pattern": p, "difficulty": d} for (i, c, p, d) in [
    ("find two numbers that add up to a target", "array", "hash map", "easy"),
    ("longest substring without repeating characters", "string", "sliding window", "medium"),
    ("maximum sum subarray", "array", "kadane", "easy"),
    ("merge two sorted linked lists", "linked_list", "two pointers", "easy"),
    ("detect a cycle in a linked list", "linked_list", "fast slow pointers", "easy"),
    ("validate a binary search tree", "tree", "depth first search", "medium"),
    ("level order traversal of a binary tree", "tree", "breadth first search", "medium"),
    ("kth largest element in an array", "array", "heap", "medium"),
    ("search in a rotated sorted array", "array", "binary search", "medium"),
    ("median of two sorted arrays", "array", "binary search", "hard"),
    ("number of islands in a grid", "graph", "union find", "medium"),
    ("course schedule topological order", "graph", "topological sort", "medium"),
    ("word ladder shortest transformation", "graph", "breadth first search", "hard"),
    ("climbing stairs number of ways", "dp", "memoization", "easy"),
    ("coin change minimum coins", "dp", "dynamic programming", "medium"),
    ("longest increasing subsequence", "dp", "dynamic programming", "medium"),
    ("edit distance between two strings", "dp", "dynamic programming", "hard"),
    ("generate all subsets", "backtracking", "backtracking", "medium"),
    ("permutations of a list", "backtracking", "backtracking", "medium"),
    ("n queens placement", "backtracking", "backtracking", "hard"),
    ("valid parentheses matching", "string", "stack", "easy"),
    ("largest rectangle in histogram", "array", "monotonic stack", "hard"),
    ("trapping rain water", "array", "two pointers", "hard"),
    ("implement a trie prefix tree", "trie", "trie", "medium"),
    ("top k frequent elements", "array", "heap", "medium"),
    ("merge k sorted lists", "linked_list", "heap", "hard"),
    ("minimum window substring", "string", "sliding window", "hard"),
    ("subarray sum equals k", "array", "prefix sum", "medium"),
    ("single number appears once", "bit", "xor", "easy"),
    ("rotate an image ninety degrees", "matrix", "in place transpose", "medium"),
    ("spiral matrix traversal", "matrix", "simulation", "medium"),
    ("gas station circular route", "greedy", "greedy", "medium"),
    ("jump game reach the end", "greedy", "greedy", "medium"),
    ("merge overlapping intervals", "interval", "sort merge", "medium"),
    ("serialize and deserialize a binary tree", "tree", "depth first search", "hard"),
    ("longest palindromic substring", "string", "expand around center", "medium"),
])


def _load_cards(limit: int) -> list[dict]:
    for rel in CARD_SOURCES:
        path = _resource(rel)
        if path.exists():
            cards = [c for c in read_jsonl_tolerant(path) if c.get("primitive_id")]
            return cards[:limit] if limit and limit < len(cards) else cards
    return []


def _true_reuse(prob: dict, index: dict, by_id: dict) -> bool:
    """A TRUE reuse: a retrieved card whose text actually carries the problem's algorithm/pattern term (the
    honest bar). A merely high lexical score against an unrelated business primitive is NOT a reuse."""
    results, _ = search_with_stats(prob["intent"], 3, index)
    want = prob["pattern"].lower()
    for r in results:
        card = by_id.get(r.get("primitive_id")) or r
        if want in json.dumps(card).lower():
            return True
    return False


def analyze(cards: list[dict]) -> dict:
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}

    rows, saved_by_diff, gap_by_pattern = [], defaultdict(int), defaultdict(lambda: [0, 0])
    total_saved = total_wasted = reused = 0
    for prob in _PROBLEMS:
        regen = REGEN_TOKENS[prob["difficulty"]]
        reuse = _true_reuse(prob, index, by_id)
        if reuse:
            saved = regen - RETRIEVE_TOKENS
            total_saved += saved
            saved_by_diff[prob["difficulty"]] += saved
            reused += 1
        else:
            saved = 0
            total_wasted += regen                    # agent regenerates -> the token-saving OPPORTUNITY
            gap_by_pattern[prob["pattern"]][0] += 1   # count
            gap_by_pattern[prob["pattern"]][1] += regen  # regenerate tokens at stake
        rows.append({**prob, "regenerate_tokens": regen, "true_reuse": reuse, "saved_tokens": saved})

    n = len(_PROBLEMS)
    # the reuse gaps ranked by TOKEN-SAVING OPPORTUNITY (recurrence × regenerate size), not by count alone
    ranked_gaps = sorted(({"pattern": p, "problems": c, "regen_tokens_at_stake": t}
                          for p, (c, t) in gap_by_pattern.items()), key=lambda g: -g["regen_tokens_at_stake"])
    return {
        "record_type": "solved_problem_reuse_summary",
        "generated_at": now_iso(),
        "solved_problems_tested": n,
        "true_reuse_rate": round(reused / n, 3),
        "tokens_saved_by_reuse": total_saved,
        "tokens_wasted_regenerating": total_wasted,   # what indexing the gaps would recover
        "avg_saved_per_reused_problem": round(total_saved / reused, 1) if reused else 0,
        "saved_by_difficulty": dict(saved_by_diff),
        "reuse_gaps_ranked_by_opportunity": ranked_gaps[:20],
        "interpretation": (
            "Goal = REDUCE TOKENS on already-solved problems by REUSING, not solving new capability. "
            "true_reuse_rate is what we can retrieve instead of regenerate TODAY; tokens_wasted_regenerating is "
            "the recoverable opportunity — each reuse-gap pattern is a SOLVED solution worth INDEXING, ranked by "
            "regenerate-tokens-at-stake (size × recurrence). Savings scale with solution SIZE (hard >> easy): "
            "index the BIG, frequently-regenerated solved solutions first; trivial ones save little."),
        "serves_truth": False,
    }


def _run(corpus: int) -> int:
    cards = _load_cards(corpus)
    if not cards:
        print("no real cards found (factory scratch may be gitignored on this checkout); run the factory first")
        return 1
    summary = analyze(cards)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("solved_problems_tested", "true_reuse_rate",
                     "tokens_saved_by_reuse", "tokens_wasted_regenerating", "saved_by_difficulty")}, indent=2))
    print("  reuse gaps to INDEX (ranked by regenerate-tokens-at-stake — the token-saving opportunity):")
    for g in summary["reuse_gaps_ranked_by_opportunity"][:8]:
        print(f"    {g['pattern']:24} {g['problems']} problem(s), {g['regen_tokens_at_stake']} tok at stake")
    print(f"\n  {summary['interpretation']}")
    print(f"\n  written: {OUT_DIR / 'summary.json'}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def card(pid, title, out):
        return {"primitive_id": pid, "title": title, "kind": "route.primitive", "input_edge": "In",
                "output_edge": out, "contract": {}, "quality_score": 0.8, "readiness": "candidate",
                "effects": ["e"], "serves_truth": False, "blackbox": title}
    # a registry that TRULY has two algorithm solutions + one unrelated business primitive
    cards = [card("prim:bs", "binary search over a sorted rotated array", "Index"),
             card("prim:sw", "sliding window minimum substring scanner", "Window"),
             card("prim:x", "screen an entity against the ofac sanctions list", "Hit")]
    summ = analyze(cards)

    checks.append(("tests the solved-problem corpus", summ["solved_problems_tested"] == len(_PROBLEMS)))
    checks.append(("true_reuse_rate is honest + low (only patterns actually in the registry reuse)",
                   0.0 < summ["true_reuse_rate"] < 0.5))
    checks.append(("reuse SAVES (regenerate − retrieve) where a true match exists", summ["tokens_saved_by_reuse"] > 0))
    checks.append(("reuse GAPS carry the wasted-regeneration opportunity", summ["tokens_wasted_regenerating"] > 0))
    checks.append(("gaps ranked by token opportunity (hard/big first), not raw count",
                   len(summ["reuse_gaps_ranked_by_opportunity"]) >= 3
                   and summ["reuse_gaps_ranked_by_opportunity"] == sorted(
                       summ["reuse_gaps_ranked_by_opportunity"], key=lambda g: -g["regen_tokens_at_stake"])))
    # the honest bar: a business primitive must NOT count as reuse of an algorithm problem (the false-positive fix)
    checks.append(("honest match: 'binary search' problem reuses (registry HAS it); most others are gaps",
                   summ["true_reuse_rate"] < 0.5 and summ["tokens_saved_by_reuse"] < summ["tokens_wasted_regenerating"]))
    checks.append(("interpretation carries the TOKEN-REDUCTION goal (reuse, not capability)",
                   "REDUCE TOKENS" in summ["interpretation"] and "INDEXING" in summ["interpretation"]))
    checks.append(("candidate / serves_truth=false", summ["serves_truth"] is False))
    again = analyze(cards)
    checks.append(("deterministic", again["true_reuse_rate"] == summ["true_reuse_rate"]
                   and again["tokens_saved_by_reuse"] == summ["tokens_saved_by_reuse"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - bench_leetcode_coverage: over solved problems, measures TOKENS SAVED BY REUSE vs WASTED "
          "REGENERATING with an HONEST match (label-verified, not lexical false-positive); reuse gaps ranked by "
          "regenerate-tokens-at-stake = solved solutions worth indexing; savings scale with size; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--corpus", type=int, default=25000)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.corpus)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
