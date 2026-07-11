#!/usr/bin/env python3
"""scripts.compose_token_bench — the ANSWER-A-PROMPT-WITHOUT-TOKEN-SPEND benchmark: from a natural-language
request, RETRIEVE primitives (reuse what the corpus already knows), REORDER them by canonical edge types, and
PIECE THEM TOGETHER into a runnable wiring — racing the compose zoo and pricing the token bill against the
naive LLM alternative.

What it measures (the three verbs in the question, each a number):

  * REUSE   — pieces_wired: how many retrieved primitives the composition incorporates (retrieval IS the
              decomposition; nothing is generated).
  * REORDER — gold_in_order rate (the wired ids respect the task's known step order) and typed_join_rate
              (adjacent output->input canonical-TYPE agreement — geometry, not text).
  * TOKENS  — llm_calls across every raced run (0 on the deterministic rows) plus the PROXY-token bill of the
              alternatives: naive (an LLM reads the top-k FULL card bodies and writes the plan) vs
              signature-lane (an LLM reads only the primitive_onion signatures) vs deterministic (0).

Compose options are read from the live graph (pipeline_path_graph.STAGE_OPTIONS["compose"]) — a NEW compose
row races here automatically, no edit needed (zoo law; counts computed, never typed). Gold tasks are synthetic
chain-complete families (KNOWN step order), so the ordering metrics are real; real-query gold is roadmap #2.

serves_truth=false — a benchmark receipt is a measurement, never served truth.

    PYTHONPATH=. python3 scripts/compose_token_bench.py --self-test
    PYTHONPATH=. python3 scripts/compose_token_bench.py --run          # race + token bill + 112K end-to-end probe
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
import time  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import pipeline_path_graph as _graph  # noqa: E402  REUSE: the graph (compose zoo lives there)
from scripts import primitive_onion as _onion  # noqa: E402  REUSE: the tiny signature layer (names+edges)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: the standard rough chars->tokens proxy (≈4 chars/token for English/JSON). Every figure derived from it is
#: labelled proxy_tokens — an estimate for comparing lanes, never a billing claim.
_CHARS_PER_TOKEN = 4
#: pieces available to compose == the graph's fused depth (single source — never retyped here).
_PIECES_K = _graph._FUSE_TOP_K  # noqa: SLF001
#: fixed non-compose stages for the race: search "all" (give compose the full multi-path piece pool) and fuse
#: "combmnz" (the measured fuse champion); everything else neutral. Computed against the live graph so a new
#: stage/option cannot silently break the bench.
_RACE_SEARCH = "all"
_RACE_FUSE = "combmnz"


def _fixed_prefix() -> dict[str, str]:
    """One option per non-compose stage, computed from the live graph (a new stage auto-gets a neutral pick)."""
    prefix: dict[str, str] = {}
    for stage in _graph.STAGES:
        if stage == "compose":
            continue
        opts = _graph.STAGE_OPTIONS[stage]
        if stage == "search":
            prefix[stage] = _RACE_SEARCH if _RACE_SEARCH in opts else next(iter(opts))
        elif stage == "fuse":
            prefix[stage] = _RACE_FUSE if _RACE_FUSE in opts else next(iter(opts))
        else:
            prefix[stage] = next((o for o in ("none", "skip") if o in opts), None) or next(iter(opts))
    return prefix


def compose_options() -> list[str]:
    """The compose zoo, read from the live graph — a new row races automatically (computed, never typed)."""
    return sorted(_graph.STAGE_OPTIONS["compose"])


# ── the gold corpus: chain-complete families with KNOWN step order + token-disjoint distractors ──────────────
def _chainable_corpus() -> list[dict[str, Any]]:
    chain = [
        {"primitive_id": "cp:scrape", "title": "Scrape website rows",
         "blackbox": "Crawl a website and pull raw rows from its pages.",
         "input_edge": "SiteUrl", "output_edge": "RawRows", **BOUNDARY},
        {"primitive_id": "cp:normalize", "title": "Normalize raw rows",
         "blackbox": "Tidy messy raw rows into one consistent clean shape.",
         "input_edge": "RawRows", "output_edge": "CleanRows", **BOUNDARY},
        {"primitive_id": "cp:dedup", "title": "Deduplicate clean rows",
         "blackbox": "Remove duplicate records by clustering near identical rows.",
         "input_edge": "CleanRows", "output_edge": "UniqueRows", **BOUNDARY},
        {"primitive_id": "cp:store", "title": "Store unique rows",
         "blackbox": "Save the final records into a datastore table.",
         "input_edge": "UniqueRows", "output_edge": "StoredRecords", **BOUNDARY},
    ]
    # distractors share NO significant token with the tasks (and no operations), so they never pollute top-k —
    # the ordering metrics then measure ORDERING, not retrieval luck.
    distractors = [{"primitive_id": f"cp:zeta{i}", "title": f"Zeta{i} widget",
                    "blackbox": f"Sigma{i} gadget flux capacitor {i}.",
                    "input_edge": f"ZetaIn{i}", "output_edge": f"ZetaOut{i}", **BOUNDARY} for i in range(3)]
    return chain + distractors


#: multi-step tasks with KNOWN gold step order (chain-complete: every adjacent gold pair type-joins).
_TASKS: tuple[dict[str, Any], ...] = (
    {"query": "scrape the site pages, tidy the messy raw rows, remove repeated records, then save everything",
     "gold_order": ["cp:scrape", "cp:normalize", "cp:dedup", "cp:store"]},
    {"query": "tidy the raw rows into one clean shape then drop the duplicate records",
     "gold_order": ["cp:normalize", "cp:dedup"]},
    {"query": "crawl the website for rows and clean them up",
     "gold_order": ["cp:scrape", "cp:normalize"]},
)


def _gold_in_order(wired_ids: list[str], gold: list[str]) -> bool:
    """Every gold step present AND in the gold relative order (extra reused pieces may interleave)."""
    positions = {pid: i for i, pid in enumerate(wired_ids)}
    if any(g not in positions for g in gold):
        return False
    return all(positions[a] < positions[b] for a, b in zip(gold, gold[1:]))


# ── the RACE: every compose option over the labelled tasks ────────────────────────────────────────────────────
def race_compose(cards: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Run every compose-zoo option over every task (fixed retrieval prefix, shared cache) and score REUSE /
    REORDER / TOKENS per option. Deterministic; 0 LLM calls by construction on the deterministic rows."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    cache: dict = {}
    prefix = _fixed_prefix()
    receipts: list[dict[str, Any]] = []
    for opt in compose_options():
        pieces, joins_frac, gold_ok, llm_total, lat_ms = [], [], [], 0, []
        route_found = 0
        for task in tasks:
            t0 = time.perf_counter()
            run = _graph.run_path(task["query"], cards, {**prefix, "compose": opt}, index=index, cache=cache)
            lat_ms.append((time.perf_counter() - t0) * 1000.0)
            llm_total += run.get("llm_calls", 0)
            comp = run.get("composition") or {}
            wired_ids = [w for w in (run.get("wiring") or "").split(" >> ") if w]
            pieces.append(comp.get("pieces_wired", 0))
            if comp.get("max_possible_joins"):
                joins_frac.append(comp["typed_joins"] / comp["max_possible_joins"])
            if comp.get("route_found"):
                route_found += 1
            gold_ok.append(_gold_in_order(wired_ids, task["gold_order"]))
        n = len(tasks) or 1
        receipts.append({"compose": opt,
                         "pieces_wired_mean": round(sum(pieces) / n, 2),
                         "typed_join_rate": round(sum(joins_frac) / len(joins_frac), 3) if joins_frac else 0.0,
                         "route_found_rate": round(route_found / n, 3),
                         "gold_in_order_rate": round(sum(gold_ok) / n, 3),
                         "llm_calls_total": llm_total,
                         "mean_latency_ms": round(sum(lat_ms) / n, 2)})
    ranked = sorted(receipts, key=lambda r: (-r["gold_in_order_rate"], -r["typed_join_rate"],
                                             -r["pieces_wired_mean"], r["compose"]))
    return {"record_type": "compose_race_receipt", "tasks": len(tasks), "corpus_cards": len(cards),
            "fixed_prefix": _fixed_prefix(), "options_raced": [r["compose"] for r in receipts],
            "ranked": ranked, "champion": ranked[0] if ranked else None,
            "note": "gold tasks are synthetic chain-complete families (KNOWN step order) — ordering metrics "
                    "are real, absolute rates are easy-mode; a real dev-query gold set is roadmap #2.",
            **BOUNDARY}


# ── the TOKEN BILL: what answering costs per lane ─────────────────────────────────────────────────────────────
def token_lanes(cards: list[dict[str, Any]], tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """PROXY-token bill per answer lane, over the same retrieval the race used: naive (LLM reads top-k FULL
    card bodies + the query, then writes the plan) vs signature-lane (LLM reads only the tiny signatures) vs
    deterministic compose (0 — the typed-edge geometry does the ordering). chars/4 proxy, labelled."""
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    index = build_index(cards)
    cache: dict = {}
    prefix = _fixed_prefix()
    by_id = {c.get("primitive_id"): c for c in cards}
    naive, sig = [], []
    for task in tasks:
        run = _graph.run_path(task["query"], cards, {**prefix, "compose": "skip"}, index=index, cache=cache)
        top = [by_id[r["primitive_id"]] for r in run.get("results", []) if r.get("primitive_id") in by_id]
        naive.append((len(task["query"]) + len(json.dumps(top, default=str))) / _CHARS_PER_TOKEN)
        sigs = [_onion.signature(c) for c in top]
        sig.append((len(task["query"]) + len(json.dumps(sigs, default=str))) / _CHARS_PER_TOKEN)
    n = len(tasks) or 1
    naive_mean, sig_mean = sum(naive) / n, sum(sig) / n
    return {"record_type": "compose_token_lane_receipt", "tasks": len(tasks), "k": _PIECES_K,
            "proxy_tokens_per_answer": {"naive_llm_reads_card_bodies": round(naive_mean, 1),
                                        "llm_reads_signatures_only": round(sig_mean, 1),
                                        "deterministic_compose": 0.0},
            "signature_vs_naive_reduction_x": round(naive_mean / sig_mean, 1) if sig_mean else None,
            "deterministic_saves_fraction": 1.0,
            "note": f"chars/{_CHARS_PER_TOKEN} proxy-token estimate (labelled, never a billing claim). The "
                    "deterministic compose rows spend 0 LLM tokens end-to-end; the signature lane is the "
                    "opt-in when a model must arbitrate.", **BOUNDARY}


# ── the REAL-corpus end-to-end probe: one NL prompt -> wiring over 112K, timed, 0 tokens ─────────────────────
def scale_probe(query: str, *, max_cards: Optional[int] = None) -> dict[str, Any]:
    """Full-corpus proof: retrieve over the real ~112K cards (semantic via the STORED-MATRIX lane + lexical),
    compose with each real compose row, report latency + llm_calls + the emitted wiring."""
    from scripts import path_graph_bench as _bench  # noqa: PLC0415  REUSE: corpus loader
    from scripts.build_primitive_search_index import build_index  # noqa: PLC0415
    cards = _bench._load_scale_corpus(max_cards)  # noqa: SLF001
    index = build_index(cards)
    prefix = {**_fixed_prefix(), "search": "semantic_embedding"}  # the stored lane carries scale
    out: dict[str, Any] = {"record_type": "compose_scale_probe", "query": query, "corpus_cards": len(cards),
                           "search": "semantic_embedding", **BOUNDARY}
    for opt in ("edge_chain", "edge_chain_tokens", "route_compose"):
        if opt not in _graph.STAGE_OPTIONS["compose"]:
            continue
        t0 = time.perf_counter()
        run = _graph.run_path(query, cards, {**prefix, "compose": opt}, index=index)
        out[opt] = {"latency_s": round(time.perf_counter() - t0, 3), "llm_calls": run.get("llm_calls", 0),
                    "wiring": run.get("wiring"), "composition": run.get("composition")}
    return out


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _chainable_corpus()
    tasks = list(_TASKS)
    race = race_compose(cards, tasks)
    by_opt = {r["compose"]: r for r in race["ranked"]}

    # (a) the race covers the LIVE compose zoo (computed — a new row races automatically)
    checks.append(("every live compose option is raced (computed from the graph, never typed)",
                   set(race["options_raced"]) == set(_graph.STAGE_OPTIONS["compose"])))

    # (b) REORDER: the typed rows order the steps correctly; the clause-join baseline cannot order primitives
    checks.append(("edge_chain orders every task's steps correctly (gold_in_order 1.0)",
                   by_opt["edge_chain"]["gold_in_order_rate"] == 1.0))
    checks.append(("the clause-join baseline cannot order primitives (gold_in_order 0.0) — the zoo rows add "
                   "real capability, not a relabel",
                   by_opt["wiring"]["gold_in_order_rate"] == 0.0))
    # rate floor 0.7, not 1.0: fuse hands compose its top-_PIECES_K, so a weakly-scoring extra piece can ride
    # along un-joined (lossless — never dropped), capping a 4-step chain + 1 dangler at 3/4 joins = 0.75.
    checks.append(("edge_chain chains type-check on chain-complete tasks (typed_join_rate >= 0.7)",
                   by_opt["edge_chain"]["typed_join_rate"] >= 0.7))
    checks.append(("route_compose finds an edge-VALID route on every task (the strict composer)",
                   by_opt["route_compose"]["route_found_rate"] == 1.0
                   and by_opt["route_compose"]["gold_in_order_rate"] == 1.0))

    # (c) REUSE: compositions are built from retrieved pieces, several per answer
    checks.append(("compositions REUSE retrieved pieces (mean pieces wired >= 2)",
                   by_opt["edge_chain"]["pieces_wired_mean"] >= 2.0))
    checks.append(("the type-TOKEN row is an upper bound on the exact row (soft >= strict, gold order kept)",
                   by_opt["edge_chain_tokens"]["typed_join_rate"] >= by_opt["edge_chain"]["typed_join_rate"]
                   and by_opt["edge_chain_tokens"]["gold_in_order_rate"] == 1.0))

    # (d) TOKENS: the whole race ran with ZERO llm calls, and the lanes price the alternative honestly
    checks.append(("the entire race answers 0-token (llm_calls_total == 0 for every option)",
                   all(r["llm_calls_total"] == 0 for r in race["ranked"])))
    lanes = token_lanes(cards, tasks)
    per = lanes["proxy_tokens_per_answer"]
    checks.append(("token lanes: naive body-reading > signature-only > deterministic == 0",
                   per["naive_llm_reads_card_bodies"] > per["llm_reads_signatures_only"] > 0.0
                   and per["deterministic_compose"] == 0.0
                   and lanes["signature_vs_naive_reduction_x"] > 1.0))

    # (e) determinism + governance (wall-clock latency is the ONE legitimately varying field — excluded)
    def _stable(rec: dict[str, Any]) -> str:
        r = json.loads(json.dumps(rec))
        for row in r["ranked"] + ([r["champion"]] if r.get("champion") else []):
            row.pop("mean_latency_ms", None)
        return json.dumps(r, sort_keys=True)
    checks.append(("the race is deterministic (byte-identical twice, latency excluded)",
                   _stable(race_compose(cards, tasks)) == _stable(race_compose(cards, tasks))))
    checks.append(("receipts are candidate/serves_truth=false",
                   race["serves_truth"] is False and lanes["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - compose_token_bench: a natural-language request is answered by REUSING retrieved "
          f"primitives, REORDERING them by canonical edge types, and WIRING them — the compose zoo raced "
          f"({len(race['options_raced'])} options, computed from the live graph), edge_chain and the real "
          f"composer both hit gold order 1.0 on chain-complete tasks while the clause-join baseline scores 0, "
          f"every run 0 LLM calls, and the token lanes price the naive alternative at "
          f"{per['naive_llm_reads_card_bodies']} proxy-tokens vs {per['llm_reads_signatures_only']} "
          f"(signatures) vs 0 (deterministic). serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="race + token bill + the 112K end-to-end probe")
    ap.add_argument("--max-cards", type=int, default=None, help="cap the scale-probe corpus (default: all)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        cards = _chainable_corpus()
        tasks = list(_TASKS)
        receipt = {"race": race_compose(cards, tasks), "token_lanes": token_lanes(cards, tasks),
                   "scale_probe": scale_probe(
                       "scrape the vendor site, clean the messy rows, drop duplicate records, then store them",
                       max_cards=args.max_cards),
                   "record_type": "compose_token_benchmark", **BOUNDARY}
        out = resource("data") / "dev-intel" / "session_emulation" / "compose_token_receipt.json"
        out.write_text(json.dumps(receipt, indent=2, sort_keys=True))
        print(json.dumps(receipt, indent=2, sort_keys=True))
        print(f"\nwritten: {out}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
