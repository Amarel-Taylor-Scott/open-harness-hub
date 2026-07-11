#!/usr/bin/env python3
"""scripts.workload_token_simulation — SIMULATE a day of real usage and price it: a deterministic WORKLOAD of
dev-task queries (clean · keyboard-typo'd · verbose-padded · truncated · REPEATED — the shapes real traffic
has, reusing the esoteric probe transforms) replayed under a ZOO of token-spend POLICIES:

  * deterministic_only — routed 0-token retrieval (the default posture); LLM never fires
  * always_llm         — an LLM secondary fires on EVERY query (the naive ceiling; stub-metered)
  * difficulty_gated   — the LLM fires ONLY when the graph's own QPP analyze says the query is HARD
                         (the confidence-gate actuator, measured instead of asserted)
  * cache_reuse        — repeat queries are served from a compiled-results cache (0 retrieval, 0 tokens) —
                         the compiled-route thesis as a measured policy

Per policy the receipt prices: proxy-tokens per 1,000 queries · LLM calls · retrievals executed · cache hit
rate · retrieval quality (nDCG on the labelled families) — the SPEND-vs-QUALITY frontier, so "when should a
model spend tokens" is a receipt, not an opinion. Everything is deterministic (the LLM is a metered stub;
wall latency is reported but excluded from determinism). Adding a policy = a new POLICIES row.

serves_truth=false — simulated spend/quality numbers are measurements, never served truth.

    PYTHONPATH=. python3 scripts/workload_token_simulation.py --self-test
    PYTHONPATH=. python3 scripts/workload_token_simulation.py --run [--events 200] [--sample 200]
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import compose_token_bench as _ctb  # noqa: E402  REUSE: the chars->proxy-token constant
from scripts import esoteric_query_bench as _eso  # noqa: E402  REUSE: deterministic corruption transforms
from scripts import path_graph_bench as _bench  # noqa: E402  REUSE: labelled families, metrics, fixed prefix
from scripts import path_router_zoo as _router  # noqa: E402  REUSE: per-query routing
from scripts import pipeline_path_graph as _graph  # noqa: E402  REUSE: run_path

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DEFAULT_EVENTS = 200
#: the corruption mix in the simulated traffic — one row per esoteric probe reused (single-sourced there)
_WORKLOAD_PROBES: tuple[str, ...] = ("keyboard_typo", "verbose_padding", "truncate_head")
_EVENT_KINDS: tuple[str, ...] = ("clean", "typo", "verbose", "truncated", "repeat")


def build_workload(n: int = _DEFAULT_EVENTS) -> list[dict[str, str]]:
    """A deterministic simulated day: cycle the labelled families through clean / corrupted / repeat shapes.
    Every 5th event REPEATS the previous clean query (the cache-hit candidate); corruptions reuse the
    esoteric probe transforms verbatim (hash-seeded, reproducible)."""
    base = list(_bench._LABELLED_QUERIES)  # noqa: SLF001 — single-source labelled families
    events: list[dict[str, str]] = []
    for i in range(n):
        src = base[i % len(base)]
        kind = _EVENT_KINDS[i % len(_EVENT_KINDS)]
        if kind == "clean":
            q, fam = src["query"], src["family"]
        elif kind == "repeat":
            prev = base[(i - 4) % len(base)]  # the clean query from this cycle -> a guaranteed exact repeat
            q, fam = prev["query"], prev["family"]
        else:
            probe = {"typo": _WORKLOAD_PROBES[0], "verbose": _WORKLOAD_PROBES[1],
                     "truncated": _WORKLOAD_PROBES[2]}[kind]
            q, fam = _eso.PROBES[probe](src["query"]), src["family"]
        events.append({"query": q, "family": fam, "kind": kind})
    return events


def _metered_stub_llm(ledger: list[int]) -> Callable[[str], str]:
    """A deterministic LLM stand-in that METERS its own proxy-token bill (prompt + response chars)."""
    def _llm(prompt: str) -> str:
        response = f"a concise reformulation of the request: {prompt[:80]}"
        ledger.append(len(prompt) + len(response))
        return response
    return _llm


def _policy_config(query: str, table: Optional[dict[str, Any]]) -> dict[str, str]:
    return _router.route(query, router="learned_table", table=table)["config"]


#: the SPEND-POLICY zoo — llm: "never" | "always" | "hard_only"; cache: serve exact repeats from the compiled
#: results cache. Adding a policy (e.g. budget-capped, per-tenant, cost-tiered model lanes) = a new row here.
POLICIES: dict[str, dict[str, Any]] = {
    "deterministic_only": {"llm": "never", "cache": False},
    "always_llm": {"llm": "always", "cache": False},
    "difficulty_gated": {"llm": "hard_only", "cache": False},
    "cache_reuse": {"llm": "never", "cache": True},
}


def simulate(cards: list[dict[str, Any]], workload: list[dict[str, str]],
             *, k: int = _bench._DEFAULT_K, table: Optional[dict[str, Any]] = None) -> dict[str, Any]:  # noqa: SLF001
    """Replay the workload under every POLICIES row; account spend + quality per policy."""
    import time  # noqa: PLC0415
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    fixed = _bench._fixed_prefix()  # noqa: SLF001 — single-source neutral prefix
    receipts: list[dict[str, Any]] = []
    for name, spec in sorted(POLICIES.items()):
        ledger: list[int] = []
        llm = _metered_stub_llm(ledger)
        run_cache: dict = {}          # run_path's expand/search memo (shared per policy)
        results_cache: dict = {}      # the compiled-results cache (cache_reuse policy only)
        llm_calls = retrievals = cache_hits = 0
        ndcgs: list[float] = []
        t0 = time.perf_counter()
        for ev in workload:
            q = ev["query"]
            if spec["cache"] and q in results_cache:
                cache_hits += 1
                ids = results_cache[q]
            else:
                cfg = _policy_config(q, table)
                use_llm = (spec["llm"] == "always"
                           or (spec["llm"] == "hard_only"
                               and _router.query_class(q).endswith("|hard")))
                path = {**fixed, **cfg, **({"secondary": "llm_expand"} if use_llm else {})}
                run = _graph.run_path(q, cards, path, index=index, cache=run_cache,
                                      llm=llm if use_llm else None)
                llm_calls += run.get("llm_calls", 0)
                retrievals += 1
                ids = [r.get("primitive_id") for r in run["results"]]
                if spec["cache"]:
                    results_cache[q] = ids
            ndcgs.append(_bench._ndcg_at_k(ids, _bench._relevant(ev["family"]), k))  # noqa: SLF001
        elapsed = time.perf_counter() - t0
        n = len(workload) or 1
        tokens = sum(ledger) / _ctb._CHARS_PER_TOKEN  # noqa: SLF001 — the ONE chars->token constant
        receipts.append({"policy": name,
                         "proxy_tokens_per_1000_queries": round(tokens / n * 1000, 1),
                         "llm_calls": llm_calls, "retrievals_executed": retrievals,
                         "cache_hit_rate": round(cache_hits / n, 4),
                         "ndcg_at_k": round(sum(ndcgs) / n, 4),
                         "wall_seconds": round(elapsed, 2)})
    ranked = sorted(receipts, key=lambda r: (-r["ndcg_at_k"], r["proxy_tokens_per_1000_queries"], r["policy"]))
    kinds = {kd: sum(1 for e in workload if e["kind"] == kd) for kd in _EVENT_KINDS}
    return {"record_type": "workload_token_simulation", "events": len(workload), "k": k,
            "corpus_cards": len(cards), "workload_mix": kinds,
            "policies": ranked, "frontier_champion": ranked[0]["policy"] if ranked else None,
            "note": "deterministic simulated traffic (esoteric transforms reused verbatim); the LLM is a "
                    "metered stub so spend is proxy-tokens (chars/4), never a billing claim. The frontier "
                    "answers WHEN a model should spend tokens: policies are rows — a new spend policy is a "
                    "new row, never a rewrite.", **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _bench.bench_corpus(0)  # gold families only — hermetic
    workload = build_workload(50)
    checks.append(("the workload is deterministic and mixes all five event kinds",
                   workload == build_workload(50)
                   and {e["kind"] for e in workload} == set(_EVENT_KINDS)))
    rec = simulate(cards, workload, table={"classes": {}})  # empty table -> global-champion routing (hermetic)
    by = {r["policy"]: r for r in rec["policies"]}
    # (a) spend ordering: always > gated >= deterministic == 0; cache policy also spends 0
    checks.append(("deterministic_only and cache_reuse spend ZERO tokens",
                   by["deterministic_only"]["proxy_tokens_per_1000_queries"] == 0.0
                   and by["cache_reuse"]["proxy_tokens_per_1000_queries"] == 0.0))
    checks.append(("always_llm spends the most; difficulty_gated spends less (the gate actually gates)",
                   by["always_llm"]["proxy_tokens_per_1000_queries"]
                   > by["difficulty_gated"]["proxy_tokens_per_1000_queries"]
                   and by["always_llm"]["llm_calls"] > by["difficulty_gated"]["llm_calls"]))
    # (b) the cache works: repeats hit it, retrievals shrink, quality is NOT changed by reuse
    checks.append(("cache_reuse serves repeats from the cache (hits > 0, fewer retrievals executed)",
                   by["cache_reuse"]["cache_hit_rate"] > 0.0
                   and by["cache_reuse"]["retrievals_executed"] < len(workload)))
    checks.append(("cache reuse does not change retrieval quality (same results replayed)",
                   abs(by["cache_reuse"]["ndcg_at_k"] - by["deterministic_only"]["ndcg_at_k"]) < 1e-9))
    # (c) determinism (wall_seconds excluded — the one legitimately varying field) + governance
    def _stable(r: dict[str, Any]) -> str:
        rr = json.loads(json.dumps(r))
        for row in rr["policies"]:
            row.pop("wall_seconds", None)
        return json.dumps(rr, sort_keys=True)
    checks.append(("the simulation is deterministic (byte-identical twice, wall time excluded)",
                   _stable(simulate(cards, workload, table={"classes": {}}))
                   == _stable(simulate(cards, workload, table={"classes": {}}))))
    checks.append(("every policy reports quality alongside spend (the frontier is honest)",
                   all(0.0 <= r["ndcg_at_k"] <= 1.0 for r in rec["policies"])))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - workload_token_simulation: a deterministic simulated day of traffic (clean/typo/verbose/"
          "truncated/repeat, esoteric transforms reused) replayed under four token-spend policies — "
          "deterministic and cache policies spend 0, the difficulty gate provably gates, the cache serves "
          "repeats without changing quality, and the spend-vs-quality frontier is a byte-stable receipt. "
          "serves_truth=false.")
    return 0


def _run(events: int, sample: int) -> int:
    cards = _bench.bench_corpus(sample)
    workload = build_workload(events)
    table = _router.load_table()
    rec = simulate(cards, workload, table=table)
    out = resource("data") / "dev-intel" / "session_emulation" / "workload_token_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps(rec, indent=2, sort_keys=True))
    print(f"\nwritten: {out}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="simulate + write the spend/quality frontier receipt")
    ap.add_argument("--events", type=int, default=_DEFAULT_EVENTS)
    ap.add_argument("--sample", type=int, default=200, help="real distractor cards mixed into the corpus")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        return _run(args.events, args.sample)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
