#!/usr/bin/env python3
"""scripts.run_primitive_consumption_benchmark — is the registry actually CONSUMABLE?

The product thesis: when a programmer or agent asks to build something, the system retrieves reusable primitives and
strings them together instead of burning output tokens re-writing the capability. This harness TESTS that against the
LIVE registry (``src.teleon.observer.registry_search``, ~113k cards): it fires realistic development-task queries,
inspects the CandidateBundle each returns, and scores three things per task —

  1. COVERAGE     — did the registry surface a plausibly-usable primitive in the top-K? (token-overlap match on the
                    card's blocking_keys / title / edges) → coverage@1/@5/@10.
  2. STRINGABILITY — how many DISTINCT primitive edges in the top-K could compose a route? (can we string them?)
  3. TOKEN SAVINGS — primitive-first context tokens (the compact cards the agent actually reads, MEASURED) vs a
                    from-scratch baseline estimate (from the matched card's own reuse metadata where present, else a
                    task-complexity heuristic). Labelled evidence_class so measured ≠ estimated ≠ projected.

Emits a scorecard JSONL + a Markdown report. Numbers are candidate/serves_truth=false; the token-savings figure is an
ESTIMATE (registry-carried reuse metadata + measured card sizes), not a runtime-measured end-to-end run — it is
explicitly labelled as such. ``--self-test`` runs fully offline on a synthetic card set (no registry, no network).
CLI: --self-test | --run [--limit K] [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

OUT_DIR = _resource("data") / "dev-intel" / "primitive_consumption_benchmark"
CHARS_PER_TOKEN = 4  # rough token estimate for measured card text
COVERAGE_MIN_OVERLAP = 2  # >=2 shared meaningful tokens = a plausible match
THIN_COVERAGE_MIN_EDGES = 3  # < this many distinct stringable edges = thin coverage (soft gap): can't compose a route
_WORD = re.compile(r"[a-z0-9]+")
_STOP = {"the", "and", "for", "with", "into", "from", "that", "this", "how", "what", "can", "our", "are",
         "build", "make", "create", "get", "set", "use", "using", "add", "want", "need", "task", "then"}

# 24 realistic development-task intents a programmer/agent would ask, across the macro-domains.
TASKS: list[dict[str, str]] = [
    {"id": "crm_csv_import", "domain": "data", "query": "import messy customer csv validate normalize dedupe into crm with receipt", "complexity": "high"},
    {"id": "password_reset", "domain": "auth", "query": "password reset flow with token policy and audit receipt", "complexity": "medium"},
    {"id": "rag_grounding", "domain": "ai", "query": "rag retrieval grounding gate with citation support and abstain when unsupported", "complexity": "high"},
    {"id": "invoice_extract", "domain": "document", "query": "extract structured fields from invoice pdf with source span receipt", "complexity": "high"},
    {"id": "webhook_verify", "domain": "api", "query": "verify webhook signature and route event idempotently", "complexity": "medium"},
    {"id": "openapi_to_mcp", "domain": "api", "query": "wrap openapi operation as mcp tool with auth scope and schema validation", "complexity": "high"},
    {"id": "js_scrape_receipt", "domain": "browser", "query": "scrape javascript rendered site with fragility guard and evidence receipt", "complexity": "high"},
    {"id": "entity_resolution", "domain": "data", "query": "record linkage blocking candidate pairs match score cluster canonical entity", "complexity": "high"},
    {"id": "terraform_deploy", "domain": "devops", "query": "terraform module for cloud run service with plan receipt and rollback", "complexity": "high"},
    {"id": "helm_chart", "domain": "devops", "query": "package service as helm chart with values schema and install smoke test", "complexity": "medium"},
    {"id": "sbom_scan", "domain": "security", "query": "generate sbom scan vulnerabilities and sign attestation", "complexity": "medium"},
    {"id": "csv_to_parquet", "domain": "data", "query": "convert csv to parquet with schema inference and roundtrip proof", "complexity": "low"},
    {"id": "prompt_injection_guard", "domain": "security", "query": "prompt injection detection guardrail with policy version pin", "complexity": "medium"},
    {"id": "kaggle_pipeline", "domain": "ml", "query": "kaggle data science pipeline train validation split metric parse submission", "complexity": "high"},
    {"id": "queue_worker", "domain": "backend", "query": "queue worker with retry backoff idempotency key and dead letter routing", "complexity": "medium"},
    {"id": "schema_migration", "domain": "data", "query": "postgres migration plan apply with transactional rollback handle", "complexity": "medium"},
    {"id": "sso_saml", "domain": "auth", "query": "sso saml login with tenant boundary check and session management", "complexity": "high"},
    {"id": "data_quality_gate", "domain": "data", "query": "data quality validation severity gate anomaly detection quarantine bad rows", "complexity": "medium"},
    {"id": "observability_trace", "domain": "ops", "query": "opentelemetry span emission trace assembly slo burn rate alert", "complexity": "medium"},
    {"id": "cron_job", "domain": "backend", "query": "scheduled cron job with idempotency and audit log", "complexity": "low"},
    {"id": "chart_report", "domain": "media", "query": "generate chart artifact vega lite spec with axis labels and non blank check", "complexity": "low"},
    {"id": "grant_discovery", "domain": "business", "query": "grant opportunity discovery deadline ranking eligibility scorecard", "complexity": "medium"},
    {"id": "clinic_discovery", "domain": "geospatial", "query": "clinic facility discovery entity resolution catchment analysis map artifact", "complexity": "high"},
    {"id": "api_pagination", "domain": "api", "query": "openapi list collection endpoint with cursor pagination and typed response", "complexity": "low"},
    # ---- public coding/agentic benchmark families (LeetCode / SWE-bench / HumanEval / Terminal-Bench / BFCL) ----
    {"id": "lc_two_sum_hashmap", "domain": "algorithm", "query": "two sum find pair hashmap lookup complement array", "complexity": "low", "benchmark_family": "leetcode"},
    {"id": "lc_binary_search", "domain": "algorithm", "query": "binary search sorted array lower bound insertion point", "complexity": "low", "benchmark_family": "leetcode"},
    {"id": "lc_graph_bfs_dfs", "domain": "algorithm", "query": "graph traversal breadth first depth first shortest path adjacency", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_dynamic_programming", "domain": "algorithm", "query": "dynamic programming memoization tabulation subsequence knapsack", "complexity": "high", "benchmark_family": "leetcode"},
    {"id": "lc_sliding_window", "domain": "algorithm", "query": "sliding window maximum substring two pointer array", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_union_find", "domain": "algorithm", "query": "union find disjoint set connected components path compression", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_trie", "domain": "algorithm", "query": "trie prefix tree insert search autocomplete word dictionary", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_heap_topk", "domain": "algorithm", "query": "heap priority queue top k frequent elements kth largest", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "he_string_parse", "domain": "algorithm", "query": "parse string tokenize validate format function implementation", "complexity": "low", "benchmark_family": "humaneval"},
    {"id": "swe_repo_bugfix", "domain": "swe", "query": "repo snapshot issue description reproduce fix patch run test suite", "complexity": "high", "benchmark_family": "swe_bench"},
    {"id": "swe_add_test", "domain": "swe", "query": "add unit test fixture for function contract coverage regression", "complexity": "medium", "benchmark_family": "swe_bench"},
    {"id": "tb_cli_task", "domain": "terminal", "query": "command line tool file operation subprocess exit code runtime", "complexity": "medium", "benchmark_family": "terminal_bench"},
    {"id": "bfcl_tool_route", "domain": "agentic", "query": "function calling select tool bind arguments abstain when no safe tool", "complexity": "medium", "benchmark_family": "bfcl"},
    {"id": "appworld_api_state", "domain": "agentic", "query": "multi step api state transition app workflow idempotent action receipt", "complexity": "high", "benchmark_family": "appworld"},
    {"id": "mle_data_science", "domain": "ml", "query": "mle bench feature engineering model train evaluate submission validate", "complexity": "high", "benchmark_family": "mle_bench"},
    {"id": "bigcode_data_task", "domain": "algorithm", "query": "dataframe groupby aggregate transform pandas library function call", "complexity": "medium", "benchmark_family": "bigcodebench"},
    {"id": "lcb_contest", "domain": "algorithm", "query": "competitive programming contest problem greedy math simulation implementation", "complexity": "high", "benchmark_family": "livecodebench"},
    {"id": "evalplus_edge", "domain": "algorithm", "query": "function edge case empty null boundary input robust implementation", "complexity": "low", "benchmark_family": "evalplus"},
    {"id": "mbpp_basic", "domain": "algorithm", "query": "basic programming task list string number manipulation helper function", "complexity": "low", "benchmark_family": "mbpp"},
    {"id": "codeforces_dp_graph", "domain": "algorithm", "query": "segment tree fenwick binary indexed tree range query update", "complexity": "high", "benchmark_family": "codeforces"},
    {"id": "webarena_browser", "domain": "agentic", "query": "web arena navigate click form fill extract multi page task", "complexity": "high", "benchmark_family": "webarena"},
    {"id": "gaia_multistep", "domain": "agentic", "query": "gaia multi step reasoning tool use retrieve compute answer", "complexity": "high", "benchmark_family": "gaia"},
    {"id": "ds1000_datasci", "domain": "ml", "query": "numpy scipy sklearn data science library api specific coding task", "complexity": "medium", "benchmark_family": "ds1000"},
    {"id": "beir_retrieval", "domain": "ai", "query": "beir information retrieval passage ranking recall relevance", "complexity": "medium", "benchmark_family": "beir"},
    # ---- competitive-programming problem archetypes (Codeforces/AtCoder/ICPC/USACO/Project Euler shapes) ----
    {"id": "cp_constructive", "domain": "competitive", "query": "constructive algorithm build valid configuration satisfy constraints output construction", "complexity": "high", "benchmark_family": "codeforces"},
    {"id": "cp_game_theory", "domain": "competitive", "query": "game theory nim grundy number sprague grundy winning losing position", "complexity": "high", "benchmark_family": "codeforces"},
    {"id": "cp_interactive", "domain": "competitive", "query": "interactive problem query response adaptive guess binary search hidden", "complexity": "high", "benchmark_family": "codeforces"},
    {"id": "cp_combinatorics_prob", "domain": "competitive", "query": "combinatorics counting probability expected value inclusion exclusion modular", "complexity": "high", "benchmark_family": "atcoder"},
    {"id": "cp_number_theory", "domain": "competitive", "query": "number theory modular inverse chinese remainder euler totient sieve factorization", "complexity": "high", "benchmark_family": "project_euler"},
    {"id": "cp_greedy_adhoc", "domain": "competitive", "query": "greedy exchange argument ad hoc sorting scheduling interval optimization", "complexity": "medium", "benchmark_family": "usaco"},
    {"id": "cp_graph_flow", "domain": "competitive", "query": "max flow min cut bipartite matching assignment hungarian network", "complexity": "high", "benchmark_family": "icpc"},
    {"id": "cp_string_hashing", "domain": "competitive", "query": "string hashing suffix automaton z algorithm aho corasick pattern count", "complexity": "high", "benchmark_family": "codeforces"},
    # ---- LeetCode problem CATEGORIES (the full tag taxonomy) ----
    {"id": "lc_array_manip", "domain": "algorithm", "query": "array in place rotate reverse merge intervals partition kadane", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_matrix", "domain": "algorithm", "query": "matrix spiral traverse rotate transpose set zeroes island grid", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_greedy", "domain": "algorithm", "query": "greedy interval scheduling jump game gas station assign cookies", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_backtracking", "domain": "algorithm", "query": "backtracking permutations combinations subsets n queens sudoku prune", "complexity": "high", "benchmark_family": "leetcode"},
    {"id": "lc_bit_manip", "domain": "algorithm", "query": "bit manipulation xor single number count bits mask subset enumeration", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_stack_queue", "domain": "algorithm", "query": "stack queue monotonic valid parentheses next greater element deque", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_linked_list", "domain": "algorithm", "query": "linked list reverse cycle detect merge two lists middle node fast slow", "complexity": "low", "benchmark_family": "leetcode"},
    {"id": "lc_intervals", "domain": "algorithm", "query": "merge overlapping intervals insert interval meeting rooms sweep", "complexity": "medium", "benchmark_family": "leetcode"},
    {"id": "lc_design_ds", "domain": "algorithm", "query": "design data structure lru cache min stack median stream implement", "complexity": "high", "benchmark_family": "leetcode"},
    {"id": "lc_math_geometry", "domain": "algorithm", "query": "math gcd power pow sqrt integer overflow geometry points line", "complexity": "medium", "benchmark_family": "leetcode"},
    # ---- remaining public coding/agentic benchmarks ----
    {"id": "apps_competitive", "domain": "algorithm", "query": "apps introductory interview competition problem statement stdin stdout", "complexity": "high", "benchmark_family": "apps"},
    {"id": "codecontests", "domain": "algorithm", "query": "code contests alphacode problem constraints test cases solution", "complexity": "high", "benchmark_family": "code_contests"},
    {"id": "cruxeval", "domain": "algorithm", "query": "crux eval input output prediction reason about code execution trace", "complexity": "medium", "benchmark_family": "cruxeval"},
    {"id": "classeval", "domain": "swe", "query": "class level code generation multiple methods dependencies interface", "complexity": "high", "benchmark_family": "classeval"},
    {"id": "repobench", "domain": "swe", "query": "repo level code completion cross file context retrieval next line", "complexity": "high", "benchmark_family": "repobench"},
    {"id": "crosscodeeval", "domain": "swe", "query": "cross file code completion repository dependency import usage", "complexity": "high", "benchmark_family": "crosscodeeval"},
    {"id": "commit0", "domain": "swe", "query": "commit0 implement library from spec passing test suite from scratch", "complexity": "high", "benchmark_family": "commit0"},
    {"id": "r2e", "domain": "swe", "query": "r2e repo to environment test harness function equivalence", "complexity": "high", "benchmark_family": "r2e"},
    {"id": "aider_polyglot", "domain": "swe", "query": "aider polyglot multi language edit diff apply exercism", "complexity": "medium", "benchmark_family": "aider_polyglot"},
    {"id": "taubench_retail", "domain": "agentic", "query": "tau bench retail airline tool use policy conversation multi turn", "complexity": "high", "benchmark_family": "tau_bench"},
    {"id": "osworld", "domain": "agentic", "query": "osworld computer use desktop gui screenshot action click type", "complexity": "high", "benchmark_family": "osworld"},
    {"id": "swelancer", "domain": "swe", "query": "swe lancer freelance software task real payout end to end feature", "complexity": "high", "benchmark_family": "swe_lancer"},
]

# from-scratch baseline output-token estimate by task complexity (what an agent burns writing the capability).
BASELINE_TOKENS = {"low": 900, "medium": 2200, "high": 4500}


def _toks(text: str) -> set[str]:
    return {t for t in _WORD.findall(str(text).lower()) if len(t) >= 3 and t not in _STOP}


def _card_tokens(card: dict[str, Any]) -> set[str]:
    parts = [card.get("title", ""), card.get("input_edge", ""), card.get("output_edge", ""), card.get("blackbox", "")]
    bk = card.get("blocking_keys")
    if isinstance(bk, list):
        parts += [str(x) for x in bk]
    dm = card.get("domains")
    if isinstance(dm, list):
        parts += [str(x) for x in dm]
    return _toks(" ".join(parts))


def _card_context_tokens(card: dict[str, Any]) -> int:
    """MEASURED size of the compact card an agent actually reads (edges + blackbox), in ~tokens."""
    compact = " ".join(str(card.get(k, "")) for k in ("title", "input_edge", "output_edge", "blackbox"))
    return max(1, len(compact) // CHARS_PER_TOKEN)


def _baseline_from_card(card: dict[str, Any], complexity: str) -> tuple[int, str]:
    """From-scratch estimate: prefer the card's own reuse metadata, else the complexity heuristic."""
    saved = card.get("estimated_saved_output_tokens")
    if isinstance(saved, (int, float)) and saved > 0:
        return int(saved), "estimated_from_registry_reuse_metadata"
    pct = card.get("estimated_savings_percent_avg")
    if isinstance(pct, (int, float)) and 0 < pct <= 100:
        # savings pct implies a baseline given the measured primitive-first cost
        pf = _card_context_tokens(card)
        return int(pf / max(0.05, 1 - pct / 100)), "estimated_from_registry_savings_percent"
    return BASELINE_TOKENS.get(complexity, 2000), "estimated_from_complexity_heuristic"


def _is_usable_route(card: dict[str, Any]) -> bool:
    """A usable match SOLVES the task (primitive/group/route) — it is NOT a benchmark meta-card that merely
    DESCRIBES or measures the task. The negative-savings artifact came from matching 'bench:...decomposition...'
    descriptor cards; those are excluded so an uncovered-by-solver task surfaces as the real capability gap."""
    pid = str(card.get("primitive_id") or "")
    if pid.startswith("bench:") or pid.startswith("task:"):
        return False
    kind = str(card.get("kind") or "").lower()
    if "benchmark" in kind or "decomposition" in kind or "scorecard" in kind:
        return False
    title = str(card.get("title") or "").lower()
    if title.startswith("benchmark ") or "task family" in title:
        return False
    return bool(card.get("input_edge") and card.get("output_edge"))


def score_task(task: dict[str, str], results: list[dict[str, Any]]) -> dict[str, Any]:
    q = _toks(task["query"])
    plausible, route_matches = [], []
    for rank, card in enumerate(results):
        if len(q & _card_tokens(card)) >= COVERAGE_MIN_OVERLAP:
            plausible.append((rank, card))
            if _is_usable_route(card):
                route_matches.append((rank, card))
    covered = bool(plausible)              # something relevant surfaced
    route_covered = bool(route_matches)    # a real SOLVER surfaced (the honest signal)
    # stringability: distinct edges among usable ROUTE matches (can we string a route?)
    distinct_edges = len({(c.get("input_edge"), c.get("output_edge")) for _, c in route_matches})
    # token accounting: measured cost of the top usable routes vs a from-scratch baseline (complexity heuristic,
    # floored at the best route's own reuse claim). Savings clamped to [0, 98] — no meta-card inversion.
    top_routes = [c for _, c in route_matches[:5]]
    pf_tokens = sum(_card_context_tokens(c) for c in top_routes)
    heuristic = BASELINE_TOKENS.get(task["complexity"], 2000)
    best = route_matches[0][1] if route_matches else {}
    claimed = best.get("estimated_saved_output_tokens") if isinstance(best.get("estimated_saved_output_tokens"), (int, float)) else 0
    baseline = max(heuristic, int(claimed) + pf_tokens) if route_covered else heuristic
    savings_pct = round(max(0.0, min(98.0, 100 * (1 - pf_tokens / baseline))), 1) if route_covered and pf_tokens else 0.0
    gap_reason = None
    if not route_covered:
        gap_reason = ("only benchmark/descriptor meta-cards matched — no solver route" if plausible
                      else "no plausible match surfaced at all")
    return {
        "record_type": "consumption_benchmark_scorecard",
        "task_id": task["id"], "domain": task["domain"], "complexity": task["complexity"],
        "results_returned": len(results),
        "covered": covered,
        "route_covered": route_covered,
        "gap_reason": gap_reason,
        "first_route_rank": route_matches[0][0] if route_matches else None,
        "route_coverage_at_1": bool(route_matches and route_matches[0][0] == 0),
        "route_coverage_at_5": any(r <= 4 for r, _ in route_matches),
        "route_coverage_at_10": any(r <= 9 for r, _ in route_matches),
        "stringable_distinct_edges": distinct_edges,
        "thin_coverage_soft_gap": route_covered and distinct_edges < THIN_COVERAGE_MIN_EDGES,
        "primitive_first_context_tokens_measured": pf_tokens,
        "from_scratch_baseline_tokens_estimated": baseline,
        "estimated_token_savings_pct": savings_pct,
        "top_route_match": (best.get("primitive_id") if best else None),
        "candidate": True, "serves_truth": False,
    }


def aggregate(scores: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(scores)
    route_cov = [s for s in scores if s["route_covered"]]
    gaps = [{"task_id": s["task_id"], "domain": s["domain"], "reason": s["gap_reason"]}
            for s in scores if not s["route_covered"]]
    savings = [s["estimated_token_savings_pct"] for s in route_cov if s["estimated_token_savings_pct"] > 0]
    return {
        "record_type": "consumption_benchmark_aggregate",
        "tasks": n,
        "route_coverage_at_1_pct": round(100 * sum(s["route_coverage_at_1"] for s in scores) / n, 1) if n else 0,
        "route_coverage_at_5_pct": round(100 * sum(s["route_coverage_at_5"] for s in scores) / n, 1) if n else 0,
        "route_coverage_at_10_pct": round(100 * sum(s["route_coverage_at_10"] for s in scores) / n, 1) if n else 0,
        "tasks_with_solver_route_pct": round(100 * len(route_cov) / n, 1) if n else 0,
        "capability_gaps": gaps,
        "capability_gap_count": len(gaps),
        "thin_coverage_soft_gaps": [{"task_id": s["task_id"], "domain": s["domain"], "benchmark_family": None,
                                     "stringable_edges": s["stringable_distinct_edges"]}
                                    for s in scores if s.get("thin_coverage_soft_gap")],
        "thin_coverage_soft_gap_count": sum(1 for s in scores if s.get("thin_coverage_soft_gap")),
        "median_stringable_edges": statistics.median([s["stringable_distinct_edges"] for s in scores]) if n else 0,
        "median_estimated_token_savings_pct": round(statistics.median(savings), 1) if savings else 0.0,
        "savings_disclaimer": "ESTIMATE from measured card sizes vs a from-scratch complexity baseline; NOT a runtime-measured end-to-end paired run. Meta/benchmark cards are excluded so uncovered tasks are real solver-route gaps.",
        "candidate": True, "serves_truth": False,
    }


def _render_report(agg: dict[str, Any], scores: list[dict[str, Any]], *, date: str) -> str:
    lines = [f"# Primitive Consumption Benchmark — {date}", "",
             "> Can the registry be strung together to solve real dev tasks with fewer tokens? Queries fired at the",
             "> LIVE registry. Benchmark/descriptor meta-cards excluded — uncovered = real SOLVER-ROUTE gap. Savings",
             "> are ESTIMATES (labelled), not runtime-measured.", "",
             "## Aggregate", "",
             f"- Tasks: **{agg['tasks']}**",
             f"- Solver-route coverage@1 / @5 / @10: **{agg['route_coverage_at_1_pct']}% / {agg['route_coverage_at_5_pct']}% / {agg['route_coverage_at_10_pct']}%**",
             f"- Tasks with a real solver route: **{agg['tasks_with_solver_route_pct']}%**",
             f"- Capability gaps (no solver route): **{agg['capability_gap_count']}** → {', '.join(g['task_id'] for g in agg['capability_gaps']) or 'none'}",
             f"- Median stringable distinct edges/task: **{agg['median_stringable_edges']}**",
             f"- Median estimated token savings (solver tasks): **{agg['median_estimated_token_savings_pct']}%**",
             f"- Disclaimer: {agg['savings_disclaimer']}", "",
             "## Per task", "", "| task | domain | solver? | @1 | first rank | stringable | pf tokens | baseline | savings% | gap_reason |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in scores:
        lines.append(f"| {s['task_id']} | {s['domain']} | {'Y' if s['route_covered'] else 'GAP'} | "
                     f"{'Y' if s['route_coverage_at_1'] else '-'} | {s['first_route_rank']} | {s['stringable_distinct_edges']} | "
                     f"{s['primitive_first_context_tokens_measured']} | {s['from_scratch_baseline_tokens_estimated']} | "
                     f"{s['estimated_token_savings_pct']} | {s['gap_reason'] or '-'} |")
    return "\n".join(lines) + "\n"


def run_live(limit: int, date: str) -> dict[str, Any]:
    from src.teleon.observer import registry_search as rs
    scores = []
    for task in TASKS:
        try:
            results = rs.search_edge_foundry_primitives(task["query"], visibility_scope="all", limit=limit)
        except Exception as exc:  # noqa: BLE001 — a search failure is a data point, not a crash
            results = []
            print(f"  search failed for {task['id']}: {exc}", file=sys.stderr)
        scores.append(score_task(task, results or []))
    agg = aggregate(scores)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{date}_scorecards.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in scores), encoding="utf-8")
    (OUT_DIR / f"{date}_aggregate.json").write_text(
        json.dumps(agg, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (OUT_DIR / f"{date}_report.md").write_text(_render_report(agg, scores, date=date), encoding="utf-8")
    return agg


def self_test() -> int:
    # synthetic cards — offline, no registry. Two tasks: one well-covered, one uncovered.
    synth = {
        "import messy customer csv validate normalize dedupe into crm with receipt": [
            {"title": "Customer CSV import to CRM", "input_edge": "RawCustomerCsv+ImportPolicy",
             "output_edge": "CrmImportReceipt", "blackbox": "validate normalize dedupe customer records",
             "blocking_keys": ["customer", "csv", "import", "dedupe", "crm"], "domains": ["data"],
             "estimated_saved_output_tokens": 1400, "primitive_id": "grp:x"},
            {"title": "Schema validate", "input_edge": "Rows", "output_edge": "ValidatedRows",
             "blackbox": "validate rows", "blocking_keys": ["schema", "validate", "csv"], "primitive_id": "prim:y"},
        ],
        "quantum teleportation flux capacitor": [],
    }

    def fake_search(query, **kw):
        return synth.get(query, [])

    # add a meta-card-only task: it matches a benchmark descriptor → must surface as a GAP, not a false solver.
    synth["dijkstra shortest path graph weighted"] = [
        {"title": "Benchmark Decomposition Task Family: Shortest Path", "input_edge": "BenchmarkTaskIntent",
         "output_edge": "TokenComparisonPlan", "blackbox": "measures shortest path", "kind": "benchmark_decomposition",
         "blocking_keys": ["dijkstra", "shortest", "path", "graph"], "primitive_id": "bench:x.decomposition"},
    ]
    scores = [score_task(t, fake_search(t["query"])) for t in [
        {"id": "crm", "domain": "data", "complexity": "high",
         "query": "import messy customer csv validate normalize dedupe into crm with receipt"},
        {"id": "none", "domain": "x", "complexity": "low", "query": "quantum teleportation flux capacitor"},
        {"id": "metaonly", "domain": "algorithm", "complexity": "medium", "query": "dijkstra shortest path graph weighted"}]]
    agg = aggregate(scores)
    checks = [
        ("solver route detected", scores[0]["route_covered"] is True),
        ("no-match task is a gap", scores[1]["route_covered"] is False and scores[1]["gap_reason"]),
        ("meta-card-ONLY task surfaces as a gap (not a false solver)",
         scores[2]["route_covered"] is False and "meta-card" in (scores[2]["gap_reason"] or "")),
        ("route coverage@1 on the good task", scores[0]["route_coverage_at_1"] is True),
        ("stringable counts distinct route edges", scores[0]["stringable_distinct_edges"] == 2),
        ("measured pf tokens > 0", scores[0]["primitive_first_context_tokens_measured"] > 0),
        ("savings positive and clamped <=98 on solver task", 0 < scores[0]["estimated_token_savings_pct"] <= 98),
        ("gap tasks have 0 savings", scores[1]["estimated_token_savings_pct"] == 0.0 and scores[2]["estimated_token_savings_pct"] == 0.0),
        ("aggregate lists the capability gaps", agg["capability_gap_count"] == 2),
        ("savings disclaimer excludes meta cards", "Meta" in agg["savings_disclaimer"] or "meta" in agg["savings_disclaimer"]),
        ("report renders", "Consumption Benchmark" in _render_report(agg, scores, date="1970-01-01")),
        ("task set covers >=12 domains incl coding benchmarks", len({t["domain"] for t in TASKS}) >= 12),
        ("coding benchmark families present", len({t.get("benchmark_family") for t in TASKS if t.get("benchmark_family")}) >= 6),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_consumption_benchmark:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - primitive_consumption_benchmark: coverage + stringability + labelled token-savings scoring "
          "(synthetic offline; --run fires the real task set at the live registry).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="fire the task set at the LIVE registry and write reports")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.run:
        date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        agg = run_live(args.limit, date)
        print(json.dumps(agg, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
