#!/usr/bin/env python3
"""scripts.build_benchmark_suite_registry — ONE flexible PORTFOLIO of benchmark backends: "pick a backend and run".

Benchmarking the primitive factory was scattered across one-off scripts with disjoint outputs, so you could not ask
"is the registry getting better?" and get a comparable answer across measures. This module is the fix, built the same
way the retrieval layer was fixed (`_repos/shared-backend-components/scripts/build_retrieval_backend_portfolio.py`): a PORTFOLIO of benchmark backends,
each a row {name, kind, measures, status: wired|planned, entrypoint}, and a UNIFORM `Scorecard` shape so results
compare across backends. New benchmarks plug in as rows, not rewrites; flipping a backend from planned→wired is one
sibling script landing, detected automatically.

Backends:
  b1 consumption      — retrieval coverage + estimated token savings (scripts/run_primitive_consumption_benchmark)
  b2 runtime          — retrieval precision/recall + primitive composability (scripts/run_runtime_benchmark)
  b3 code_execution   — ACTUAL route-execution correctness via executed proofs (scripts/run_code_execution_benchmark)
  b4 token_savings    — primitive-first vs one-shot token delta (self-contained, always wired)
  b5 path_bakeoff     — deterministic multi-path bake-off, pick a winner (scripts/run_path_bakeoff)

`status` is HONEST: a backend is `wired` when its canonical entrypoint module imports today, else `planned`; the
`token_savings` backend is self-contained so always wired. EVERY backend — wired or planned — still runs on a tiny
synthetic offline taskset via an inline runner that REUSES the existing machinery (mutator proof-runner, composability
gate, retrieval portfolio, search index) with graceful try/except fallback, so a Scorecard shape is always produced.
This module is ADD-ONLY: it imports/calls existing machinery and never edits it. Rows are candidate/serves_truth=false
(they are measurements, not proven primitives); the underlying executed primitive proofs carry their own serves_truth.
No wall-clock / RNG in any body — the bake-off is passed a fixed `now`. CLI: --self-test | --write | --run [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import re
import statistics
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "benchmark-suite-registry"
OUT_DIR = _resource("data") / "dev-intel" / "benchmark_suite_registry"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
FIXED_NOW = "2026-07-03T00:00:00Z"  # deterministic clock for the bake-off (no wall-clock in bodies)
SELF = "scripts/build_benchmark_suite_registry.py"
_WORD = re.compile(r"[a-z0-9]+")

# ── REUSE (import, don't reinvent) — every import graceful so --self-test passes even if a sibling is absent ──
try:  # b1 consumption scoring
    from scripts.run_primitive_consumption_benchmark import (  # noqa: E402
        BASELINE_TOKENS as _CONSUME_BASELINE,
        _card_context_tokens as _consume_card_tokens,
        aggregate as _consume_aggregate,
        score_task as _consume_score_task,
    )
except Exception:  # noqa: BLE001
    _CONSUME_BASELINE, _consume_card_tokens, _consume_aggregate, _consume_score_task = None, None, None, None

try:  # b3 executed-proof runner (core existing machinery, not a sibling)
    from scripts.mutator_registry import run_primitive_proof as _run_primitive_proof
except Exception:  # noqa: BLE001
    _run_primitive_proof = None

try:  # b2/b5 retrieval backend portfolio (single source of active search backends)
    from scripts.build_retrieval_backend_portfolio import backends_of as _backends_of
except Exception:  # noqa: BLE001
    _backends_of = None

try:  # b2 composability gate
    from scripts.check_primitive_composability import (  # noqa: E402
        build_type_index as _build_type_index,
        composability_report as _composability_report,
    )
except Exception:  # noqa: BLE001
    _build_type_index, _composability_report = None, None

try:  # b2 fast search index (offline, in-memory build)
    from scripts.build_primitive_search_index import build_index as _build_index, fast_search as _fast_search
except Exception:  # noqa: BLE001
    _build_index, _fast_search = None, None

try:  # optional: runtime route composition (concurrent sibling, may be absent)
    from scripts.primitive_runtime import compose_solution as _compose_solution
except Exception:  # noqa: BLE001
    _compose_solution = None


# ── tiny synthetic taskset — real primitive cards with typed edges + a runnable (mutator, fixture, expected) ──
_IDEMPOTENCY_KEY_U1_PAY = hashlib.sha256("u1|pay".encode()).hexdigest()[:24]

SYNTH_TASKS: list[dict[str, Any]] = [
    {
        "id": "csv_clean", "domain": "data", "complexity": "medium",
        "query": "select project columns dedupe rows unique csv",
        "cards": [
            {"primitive_id": "prim:leaf:field_project", "title": "Project CSV columns",
             "input_edge": "RawRow", "output_edge": "ProjectedRow", "blackbox": "project a row to a keep-list",
             "blocking_keys": ["project", "columns", "select", "csv"], "domains": ["data"],
             "estimated_saved_output_tokens": 600,
             "mutator": "field_project", "fixture": {"a": 1, "b": 2, "c": 3}, "expected": {"a": 1, "c": 3},
             "args": {"keep": ["a", "c"]}},
            {"primitive_id": "prim:leaf:dedupe_by_key", "title": "Dedupe rows by key",
             "input_edge": "RowList", "output_edge": "UniqueRowList", "blackbox": "collapse duplicate rows by key",
             "blocking_keys": ["dedupe", "rows", "unique", "key"], "domains": ["data"],
             "estimated_saved_output_tokens": 700,
             "mutator": "dedupe_by_key", "fixture": [{"k": 1}, {"k": 1}], "expected": [{"k": 1}], "args": {"key": "k"}},
        ],
    },
    {
        "id": "api_idem", "domain": "api", "complexity": "medium",
        "query": "idempotency key payment request serialize row json",
        "cards": [
            {"primitive_id": "prim:leaf:idempotency_key", "title": "Derive idempotency key",
             "input_edge": "PaymentRequest", "output_edge": "IdempotentRequest",
             "blackbox": "derive a deterministic idempotency key for a request",
             "blocking_keys": ["idempotency", "key", "payment", "request"], "domains": ["api"],
             "estimated_saved_output_tokens": 800,
             "mutator": "idempotency_wrapper", "fixture": {"user": "u1", "op": "pay"},
             "expected": {"user": "u1", "op": "pay", "idempotency_key": _IDEMPOTENCY_KEY_U1_PAY},
             "args": {"key_fields": ["user", "op"]}},
            {"primitive_id": "prim:leaf:row_to_json", "title": "Serialize row to JSON",
             "input_edge": "Row", "output_edge": "JsonText", "blackbox": "serialize a row to canonical JSON",
             "blocking_keys": ["serialize", "row", "json", "canonical"], "domains": ["api"],
             "estimated_saved_output_tokens": 400,
             "mutator": "row_to_json", "fixture": {"z": 9}, "expected": '{"z": 9}', "args": {},
             "inverse": "json_to_row"},
        ],
    },
    {
        "id": "typed_coerce", "domain": "data", "complexity": "low",
        "query": "type cast integer envelope wrap policy payload",
        "cards": [
            {"primitive_id": "prim:leaf:type_cast", "title": "Type-cast fields",
             "input_edge": "StringRecord", "output_edge": "TypedRecord", "blackbox": "coerce field types",
             "blocking_keys": ["type", "cast", "integer", "coerce"], "domains": ["data"],
             "estimated_saved_output_tokens": 300,
             "mutator": "type_cast", "fixture": {"n": "5"}, "expected": {"n": 5}, "args": {"casts": {"n": "int"}}},
            {"primitive_id": "prim:leaf:envelope_wrap", "title": "Wrap payload in policy envelope",
             "input_edge": "Payload", "output_edge": "PolicyEnvelope", "blackbox": "wrap a payload in a policy envelope",
             "blocking_keys": ["envelope", "wrap", "policy", "payload"], "domains": ["data"],
             "estimated_saved_output_tokens": 350,
             "mutator": "envelope_wrap", "fixture": {"p": 1},
             "expected": {"payload": {"p": 1}, "policy": {"pol": "x"}, "envelope_version": 1},
             "args": {"policy": {"pol": "x"}}, "inverse": "envelope_unwrap"},
        ],
    },
]


def _toks(text: str) -> set[str]:
    return {t for t in _WORD.findall(str(text).lower()) if len(t) >= 3}


def _card_tokens(card: dict[str, Any]) -> set[str]:
    parts = [card.get("title", ""), card.get("input_edge", ""), card.get("output_edge", ""), card.get("blackbox", "")]
    parts += [str(x) for x in (card.get("blocking_keys") or [])]
    return _toks(" ".join(parts))


def _relevant_ids(task: dict[str, Any]) -> set[str]:
    return {c["primitive_id"] for c in task["cards"]}


def _ctx_tokens(card: dict[str, Any]) -> int:
    if _consume_card_tokens is not None:
        try:
            return int(_consume_card_tokens(card))
        except Exception:  # noqa: BLE001
            pass
    compact = " ".join(str(card.get(k, "")) for k in ("title", "input_edge", "output_edge", "blackbox"))
    return max(1, len(compact) // 4)


def _baseline_tokens(complexity: str) -> int:
    table = _CONSUME_BASELINE if isinstance(_CONSUME_BASELINE, dict) else {"low": 900, "medium": 2200, "high": 4500}
    return int(table.get(complexity, 2000))


def _rank_ids(query: str, cards: list[dict[str, Any]], k: int) -> list[str]:
    """Rank card primitive_ids for a query. Reuse the real search index when importable, else a lexical proxy."""
    if _build_index is not None and _fast_search is not None:
        try:
            idx = _build_index(cards)
            hits = _fast_search(query, limit=k, index=idx)
            ids = [str(h.get("primitive_id") or "") for h in hits if h.get("primitive_id")]
            if ids:
                return ids[:k]
        except Exception:  # noqa: BLE001
            pass
    q = _toks(query)
    scored = sorted(cards, key=lambda c: (-len(q & _card_tokens(c)), str(c.get("primitive_id"))))
    return [str(c["primitive_id"]) for c in scored[:k]]


# ── per-backend inline runners: each returns (metrics: dict[str, float|int|str], n_tasks: int, notes: str) ──
def _run_consumption(taskset: list[dict[str, Any]]) -> tuple[dict[str, Any], int, str]:
    scores = []
    if _consume_score_task is not None and _consume_aggregate is not None:
        for t in taskset:
            scores.append(_consume_score_task(
                {"id": t["id"], "domain": t["domain"], "complexity": t["complexity"], "query": t["query"]}, t["cards"]))
        agg = _consume_aggregate(scores)
        metrics = {
            "route_coverage_at_5_pct": agg["route_coverage_at_5_pct"],
            "tasks_with_solver_route_pct": agg["tasks_with_solver_route_pct"],
            "median_estimated_token_savings_pct": agg["median_estimated_token_savings_pct"],
        }
        return metrics, len(taskset), "reused run_primitive_consumption_benchmark.score_task+aggregate on synthetic cards"
    # graceful fallback: local coverage proxy
    covered = 0
    for t in taskset:
        q = _toks(t["query"])
        if any(len(q & _card_tokens(c)) >= 2 for c in t["cards"]):
            covered += 1
    return ({"route_coverage_at_5_pct": round(100 * covered / len(taskset), 1) if taskset else 0.0,
             "tasks_with_solver_route_pct": round(100 * covered / len(taskset), 1) if taskset else 0.0,
             "median_estimated_token_savings_pct": 0.0}, len(taskset),
            "consumption sibling unavailable — local coverage proxy")


def _run_token_savings(taskset: list[dict[str, Any]]) -> tuple[dict[str, Any], int, str]:
    per_task = []
    total_pf, total_base = 0, 0
    for t in taskset:
        pf = sum(_ctx_tokens(c) for c in t["cards"])
        base = _baseline_tokens(t["complexity"])
        total_pf += pf
        total_base += base
        per_task.append(round(max(0.0, min(98.0, 100 * (1 - pf / base))), 1) if base else 0.0)
    metrics = {
        "median_token_savings_pct": round(statistics.median(per_task), 1) if per_task else 0.0,
        "total_primitive_first_tokens_measured": total_pf,
        "total_one_shot_baseline_tokens_estimated": total_base,
        "aggregate_token_savings_pct": round(100 * (1 - total_pf / total_base), 1) if total_base else 0.0,
    }
    return metrics, len(taskset), ("primitive-first MEASURED card tokens vs one-shot ESTIMATED baseline "
                                   "(labelled estimate, not a runtime-measured paired run)")


def _run_runtime(taskset: list[dict[str, Any]]) -> tuple[dict[str, Any], int, str]:
    precisions, recalls = [], []
    for t in taskset:
        relevant = _relevant_ids(t)
        ranked = _rank_ids(t["query"], t["cards"], k=5)
        hit = len([r for r in ranked if r in relevant])
        precisions.append(hit / len(ranked) if ranked else 0.0)
        recalls.append(hit / len(relevant) if relevant else 0.0)
    # composability: reuse the gate over the whole synthetic corpus
    all_cards = [c for t in taskset for c in t["cards"]]
    composable = 0
    if _composability_report is not None:
        idx = _build_type_index(all_cards) if _build_type_index is not None else None
        for c in all_cards:
            try:
                if _composability_report(c, idx).get("gate_pass"):
                    composable += 1
            except Exception:  # noqa: BLE001
                pass
        comp_note = "reused check_primitive_composability gate"
    else:
        composable = sum(1 for c in all_cards if c.get("input_edge") and c.get("output_edge"))
        comp_note = "composability sibling unavailable — typed-edge presence proxy"
    routes_composed = 0
    if _compose_solution is not None:
        for t in taskset:
            try:
                if _compose_solution(t["query"], t["cards"]):
                    routes_composed += 1
            except Exception:  # noqa: BLE001
                pass
    metrics = {
        "precision_at_5": round(sum(precisions) / len(precisions), 3) if precisions else 0.0,
        "recall_at_5": round(sum(recalls) / len(recalls), 3) if recalls else 0.0,
        "composable_cards_pct": round(100 * composable / len(all_cards), 1) if all_cards else 0.0,
        "routes_composed": routes_composed,
    }
    return metrics, len(taskset), f"retrieval precision/recall (index-pruned or lexical proxy) + {comp_note}"


def _run_code_execution(taskset: list[dict[str, Any]]) -> tuple[dict[str, Any], int, str]:
    if _run_primitive_proof is None:
        return {"route_execution_correctness_pct": 0.0, "primitives_executed": 0, "primitives_proven": 0}, 0, \
            "mutator_registry.run_primitive_proof unavailable — cannot execute routes"
    executed, proven = 0, 0
    for t in taskset:
        for c in t["cards"]:
            if "mutator" not in c:
                continue
            executed += 1
            receipt = _run_primitive_proof(c["primitive_id"], c["mutator"], c.get("fixture"), c.get("expected"),
                                           mutator_args=c.get("args") or {}, has_inverse=c.get("inverse"))
            if receipt.get("serves_truth") is True:
                proven += 1
    metrics = {
        "route_execution_correctness_pct": round(100 * proven / executed, 1) if executed else 0.0,
        "primitives_executed": executed,
        "primitives_proven": proven,
    }
    return metrics, len(taskset), ("ACTUALLY executes each card's mutator against its fixture via the imported "
                                   "executed-proof runner; correctness = fraction whose proof passes")


def _run_path_bakeoff(taskset: list[dict[str, Any]], *, now: str = FIXED_NOW) -> tuple[dict[str, Any], int, str]:
    # candidate "paths" = search-method backends from the retrieval portfolio (single source), else a fixed pair
    paths = ["blocking_lexical", "edge_type_constrained"]
    if _backends_of is not None:
        try:
            methods = [r.get("method_id") for r in _backends_of("search_method") if r.get("method_id")]
            if methods:
                paths = methods
        except Exception:  # noqa: BLE001
            pass

    def _score_path(method: str, task: dict[str, Any]) -> float:
        relevant = _relevant_ids(task)
        if method == "edge_type_constrained":  # reward typed, composable edges
            typed = sum(1 for c in task["cards"] if c.get("input_edge") and c.get("output_edge"))
            return round(typed / len(task["cards"]), 3) if task["cards"] else 0.0
        # default lexical coverage proxy for every other method
        ranked = _rank_ids(task["query"], task["cards"], k=5)
        return round(len([r for r in ranked if r in relevant]) / len(relevant), 3) if relevant else 0.0

    winners, best_scores = [], []
    for t in taskset:
        scored = sorted(((_score_path(m, t), m) for m in paths), key=lambda x: (-x[0], x[1]))  # deterministic tie-break
        best_scores.append(scored[0][0])
        winners.append(scored[0][1])
    top = max(set(winners), key=lambda w: (winners.count(w), w)) if winners else None
    metrics = {
        "paths_evaluated": len(paths),
        "mean_best_score": round(sum(best_scores) / len(best_scores), 3) if best_scores else 0.0,
        "winner_agreement_pct": round(100 * winners.count(top) / len(winners), 1) if winners else 0.0,
        "overall_winner": top or "",
    }
    return metrics, len(taskset), f"deterministic bake-off of {len(paths)} paths (now={now}); winner by score, stable tie-break"


# ── the PORTFOLIO: each backend a row; status computed from whether the canonical entrypoint imports today ──
# (name, kind, measures, entrypoint_module_dotted | None, entrypoint_display, runner, always_wired)
_BACKENDS: list[tuple[str, str, str, str | None, str, Callable[..., tuple[dict[str, Any], int, str]], bool]] = [
    ("consumption", "consumption", "retrieval coverage + estimated token savings",
     "scripts.run_primitive_consumption_benchmark", "scripts/run_primitive_consumption_benchmark.py",
     _run_consumption, False),
    ("runtime", "runtime", "retrieval precision/recall + primitive composability",
     "scripts.run_runtime_benchmark", "scripts/run_runtime_benchmark.py", _run_runtime, False),
    ("code_execution", "code_execution", "actual route-execution correctness (executed proofs)",
     "scripts.run_code_execution_benchmark", "scripts/run_code_execution_benchmark.py", _run_code_execution, False),
    ("token_savings", "token_savings", "primitive-first vs one-shot token delta",
     None, f"{SELF}::_run_token_savings", _run_token_savings, True),
    ("path_bakeoff", "path_bakeoff", "deterministic multi-path bake-off, pick a winner",
     "scripts.run_path_bakeoff", "scripts/run_path_bakeoff.py", _run_path_bakeoff, False),
]
_BY_NAME = {b[0]: b for b in _BACKENDS}


def _module_importable(dotted: str | None) -> bool:
    if not dotted:
        return False
    try:
        return importlib.util.find_spec(dotted) is not None
    except Exception:  # noqa: BLE001 — parent-not-a-package etc.
        return False


def _status(entrypoint_dotted: str | None, always_wired: bool) -> str:
    return "wired" if (always_wired or _module_importable(entrypoint_dotted)) else "planned"


def resolve_benchmarks() -> list[dict[str, Any]]:
    """The single source of truth for the benchmark portfolio: one row per backend."""
    rows = []
    for name, kind, measures, dotted, display, _runner, always in _BACKENDS:
        rows.append({
            "record_type": "benchmark_backend", "name": name, "kind": kind, "measures": measures,
            "status": _status(dotted, always), "entrypoint": display, **BOUNDARY,
        })
    return rows


def wired_benchmarks() -> list[str]:
    return [r["name"] for r in resolve_benchmarks() if r["status"] == "wired"]


def run_benchmark(name: str, taskset: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run one benchmark backend on a taskset (default: the tiny synthetic offline set) → a uniform Scorecard."""
    if name not in _BY_NAME:
        raise KeyError(f"no such benchmark: {name} (portfolio: {sorted(_BY_NAME)})")
    _n, kind, _m, dotted, _d, runner, always = _BY_NAME[name]
    ts = taskset if taskset is not None else SYNTH_TASKS
    metrics, n_tasks, notes = runner(ts)
    return {
        "record_type": "benchmark_scorecard", "name": name, "kind": kind,
        "status": _status(dotted, always), "metrics": metrics, "n_tasks": n_tasks, "notes": notes, **BOUNDARY,
    }


# ── pack / manifest ──
def build_manifest(*, date: str) -> dict[str, Any]:
    rows = resolve_benchmarks()
    scorecards = [run_benchmark(r["name"]) for r in rows]
    row_counts = {"benchmarks.jsonl": len(rows), "scorecards.jsonl": len(scorecards)}
    canonical = "\n".join(json.dumps(x, sort_keys=True, ensure_ascii=False) for x in rows + scorecards)
    return {
        "record_type": "benchmark_suite_registry_manifest",
        "pack_id": "benchmark-suite-registry", "generator": SELF, "generated_utc": date,
        "row_counts": row_counts, "total_rows": sum(row_counts.values()),
        "backend_count": len(rows), "wired_benchmarks": wired_benchmarks(),
        "planned_benchmarks": [r["name"] for r in rows if r["status"] == "planned"],
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(), **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = resolve_benchmarks()
    scorecards = [run_benchmark(r["name"]) for r in rows]
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    (PACK_DIR / "benchmarks.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    (PACK_DIR / "scorecards.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in scorecards), encoding="utf-8")
    manifest = build_manifest(date=date)
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                                            encoding="utf-8")
    return manifest


def run_all(*, date: str) -> dict[str, Any]:
    """Run every WIRED benchmark on the synthetic taskset and persist scorecards + an aggregate summary."""
    scorecards = [run_benchmark(n) for n in wired_benchmarks()]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / f"{date}_scorecards.jsonl").write_text(
        "".join(json.dumps(s, ensure_ascii=False, sort_keys=True) + "\n" for s in scorecards), encoding="utf-8")
    summary = {"record_type": "benchmark_suite_run_summary", "generated_utc": date,
               "wired_benchmarks": wired_benchmarks(), "scorecards": scorecards, **BOUNDARY}
    (OUT_DIR / f"{date}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


_SCORECARD_KEYS = {"record_type", "name", "kind", "status", "metrics", "n_tasks", "notes", "candidate", "serves_truth"}


def self_test() -> int:
    rows = resolve_benchmarks()
    wired = wired_benchmarks()
    all_cards = [run_benchmark(r["name"]) for r in rows]  # run ALL for uniform-shape check
    wired_cards = [run_benchmark(n) for n in wired]
    kinds = {r["kind"] for r in rows}

    def _numeric_metrics(sc: dict[str, Any]) -> bool:
        return isinstance(sc["metrics"], dict) and len(sc["metrics"]) >= 1 and all(
            isinstance(v, (int, float, str)) for v in sc["metrics"].values())

    checks: list[tuple[str, bool]] = [
        ("portfolio has >=5 benchmark backends", len(rows) >= 5),
        ("all 5 kinds present", kinds >= {"consumption", "runtime", "code_execution", "token_savings", "path_bakeoff"}),
        ("token_savings is always wired (self-contained)", "token_savings" in wired),
        ("consumption is wired (its sibling ships today)", "consumption" in wired),
        (">=2 wired backends", len(wired) >= 2),
        ("EVERY wired backend produces a Scorecard on the synthetic set with n_tasks>0",
         all(sc["n_tasks"] > 0 for sc in wired_cards) and len(wired_cards) == len(wired)),
        ("Scorecard shape is UNIFORM across all backends (same top-level keys)",
         all(set(sc) == _SCORECARD_KEYS for sc in all_cards)),
        ("every Scorecard carries a non-empty numeric/str metrics map", all(_numeric_metrics(sc) for sc in all_cards)),
        ("code_execution ACTUALLY executes proofs (proven==executed on the passing synthetic set)",
         (lambda m: m["primitives_executed"] >= 6 and m["primitives_proven"] == m["primitives_executed"]
          and m["route_execution_correctness_pct"] == 100.0)(run_benchmark("code_execution")["metrics"])),
        ("runtime reports precision/recall + composability", (lambda m: {"precision_at_5", "recall_at_5",
          "composable_cards_pct"} <= set(m) and m["recall_at_5"] > 0)(run_benchmark("runtime")["metrics"])),
        ("token_savings measures a positive primitive-first delta",
         run_benchmark("token_savings")["metrics"]["aggregate_token_savings_pct"] > 0),
        ("path_bakeoff is deterministic (fixed now, no wall-clock)",
         FIXED_NOW in run_benchmark("path_bakeoff")["notes"] and run_benchmark("path_bakeoff")["metrics"]["paths_evaluated"] >= 2),
        ("planned backends still produce a Scorecard (inline runner)",
         all(run_benchmark(r["name"])["n_tasks"] > 0 for r in rows if r["status"] == "planned") or not any(
             r["status"] == "planned" for r in rows)),
        ("run_benchmark on an unknown backend raises", _unknown_raises()),
        ("deterministic: re-resolving + re-running is byte-identical",
         json.dumps([resolve_benchmarks(), all_cards], sort_keys=True)
         == json.dumps([resolve_benchmarks(), [run_benchmark(r["name"]) for r in rows]], sort_keys=True)),
        ("rows hold the candidate/serves_truth boundary",
         all(r["candidate"] is True and r["serves_truth"] is False for r in rows + all_cards)),
        ("manifest counts are computed from the portfolio, not typed",
         (lambda mf: mf["backend_count"] == len(rows) and mf["total_rows"] == 2 * len(rows))(build_manifest(date="X"))),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - build_benchmark_suite_registry:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - build_benchmark_suite_registry: portfolio of {len(rows)} benchmark backends "
          f"(wired={wired}); uniform Scorecard shape across all; code_execution really executes proofs; "
          "'pick a backend and run' — flexible, add-only, offline-deterministic.")
    return 0


def _unknown_raises() -> bool:
    try:
        run_benchmark("does_not_exist")
        return False
    except KeyError:
        return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true", help="write the portfolio pack + scorecards + manifest")
    parser.add_argument("--run", action="store_true", help="run every WIRED benchmark on the synthetic set + persist")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    if args.write:
        manifest = write_pack(date=date)
        print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
        return self_test()
    if args.run:
        summary = run_all(date=date)
        print(json.dumps({"wired_benchmarks": summary["wired_benchmarks"],
                          "scorecards": summary["scorecards"]}, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
