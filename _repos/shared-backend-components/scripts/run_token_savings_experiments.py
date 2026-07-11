#!/usr/bin/env python3
"""scripts.run_token_savings_experiments — the SCALED "does AIDevObserver reuse actually save tokens?" platform.

Runs THOUSANDS of reuse-vs-rebuild experiments over REAL registry cards through the REAL retrieval engine
(``scripts.build_primitive_search_index.fast_search`` — the same index the capability_retrieval MCP server
serves), and tracks the numbers the owner asked for: average tokens saved, the AREAS WHERE WE DON'T SAVE
(segments with low/negative net savings), and the AREAS WHERE WE NEED MORE (coverage gaps — intents the
search can't satisfy → candidate rows for the research queue).

This does NOT reinvent the pieces — it composes them: the retrieval engine (build_primitive_search_index),
the chars/4 token proxy + full-vs-edge basis of ``primitive_lift_benchmark`` (which measured 487x on one
task), and the research queue (``scripts.acquisition.research_queue``) as the gap sink. It is the SCALED,
precision-honest complement to those single-shot harnesses.

The honesty model (why this is not a rigged "reuse always wins" demo):
  * WITHOUT observer (rebuild): the agent regenerates the capability → ``rebuild_tokens`` = the full spec
    an agent must read/produce (contract + blackbox + effects + mutations + edges + proof_requirements).
    Conservative: the real IMPLEMENTATION is bigger than the spec, so this UNDER-counts the saving.
  * WITH observer, HIT (the true card or a same-output_edge equivalent is in the top-k): the agent reads
    the query + the top-k EDGE cards + a reuse reference and reuses → ``reuse_tokens``; it does NOT
    regenerate. net_saved = rebuild_tokens − reuse_tokens  (positive).
  * WITH observer, MISS: the agent pays the search (reads the wrong top-k) AND regenerates anyway → the
    DELTA vs not-searching is the WASTED search. net_saved = −reuse_tokens  (NEGATIVE).
  => E[net] = p·rebuild − reuse, so the BREAK-EVEN precision is avg_reuse/avg_rebuild. Retrieval that is
     worse than break-even COSTS tokens — the platform reports that, per segment, instead of hiding it.

Every row is candidate=true / serves_truth=false — measured evidence, not a promoted claim. Token counts
are a deterministic ``chars/4`` proxy (basis label on every row); the REAL-model-token complement is
``scripts.bench_token_usage`` on the live lane.

  PYTHONPATH=. python3 scripts/run_token_savings_experiments.py --self-test
  PYTHONPATH=. python3 scripts/run_token_savings_experiments.py --run --n 3000 --k 5 [--corpus 20000] [--emit-gaps]
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- bootstrap: substrate root via the scripts/_repo_paths.py sentinel, then install all code roots so
#     `scripts.*` AND `src.*` resolve on a bare `python3 .../run_token_savings_experiments.py` launch. ---
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
from collections import defaultdict  # noqa: E402
from typing import Any, Iterable  # noqa: E402

from scripts._json import read_json_or  # noqa: E402  the ONE tolerant single-JSON reader
from scripts._jsonl import read_jsonl_tolerant  # noqa: E402  the ONE tolerant JSONL reader
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402  UTC, Z-suffixed
from scripts.build_primitive_search_index import build_index, search_with_stats  # noqa: E402  the REAL engine

#: chars-per-token proxy — the SAME basis primitive_lift_benchmark uses (deterministic_proxy_chars/4), so
#: this platform's numbers are comparable to that harness rather than a 4th divergent token model.
CHARS_PER_TOKEN = 4
TOKENS_BASIS = f"deterministic_proxy_chars/{CHARS_PER_TOKEN}"

#: default real-card corpus (the verified factory cards the registry search indexes). Falls back through
#: the list until one exists — the factory scratch is .gitignored on some checkouts.
CARD_SOURCES = (
    "data/dev-intel/aidevobserver_edge_foundry/verified_factory_primitive_cards.jsonl",
    "data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl",
    "catalog/knowledge-packs/data/primitive-search-index/search_docs.jsonl",
)
OUT_DIR = _resource("data") / "dev-intel" / "token_savings_experiments"
#: spec fields an agent would have to (re)read/produce to REBUILD the capability from scratch.
_REBUILD_SPEC_FIELDS = ("contract", "edge_contract", "blackbox", "effects", "mutations",
                        "proof_requirements", "memory", "cache", "input_edge", "output_edge", "title")
#: compact EDGE-card fields the agent reads to REUSE (the "retrieve capabilities not code" surface).
_EDGE_CARD_FIELDS = ("primitive_id", "title", "input_edge", "output_edge", "kind")
#: a card scoring below this (idf-weighted overlap) is treated as "no usable hit" — a coverage gap.
GAP_SCORE_FLOOR = 1.0


def _est_tokens(text: str) -> int:
    """Deterministic token estimate (chars/4). Same basis across both arms, so the RATIO is robust even
    though the absolute count is a proxy. Never a model call."""
    return len(text) // CHARS_PER_TOKEN


def _spec_text(card: dict) -> str:
    """The full-spec text an agent must produce to REBUILD this capability (the WITHOUT-observer cost)."""
    return json.dumps({k: card[k] for k in _REBUILD_SPEC_FIELDS if k in card}, sort_keys=True)


def _edge_card_text(card: dict) -> str:
    """The compact edge card an agent reads to REUSE (the WITH-observer per-result cost)."""
    return json.dumps({k: card.get(k) for k in _EDGE_CARD_FIELDS if card.get(k)}, sort_keys=True)


def _query_for(card: dict, paraphrase: bool = False) -> str:
    """A realistic build-intent for this capability. ``descriptive`` (default): the I/O contract + the exact
    title — shares tokens with the card (a real dev would), so precision is an UPPER bound. ``paraphrase``:
    keep the I/O contract (a dev knows what they feed in / want out) but only a deterministically-subsampled
    HALF of the title wording — simulating a dev describing the need in their OWN words, not the card's. That
    is the honest lexical-robustness test: does search still find the primitive when the intent is reworded?"""
    title = str(card.get("title") or "")
    if paraphrase:
        title = " ".join(title.split()[::2])  # every-other title token — deterministic ~50% reword, no seeding
    parts = [str(card.get("input_edge") or ""), str(card.get("output_edge") or ""), title]
    return " ".join(p for p in parts if p).strip()


#: coarse rollup unit. The per-card `domain` is near-unique (one card per domain) so it makes n=1 "areas"
#: that can't average — kind × source_family gives a few dozen buckets with enough n to be a real signal.
#: The fine domain still rides on each row + drives the coverage-gap list.
def _segment_of(card: dict) -> str:
    """The (kind · source_family) bucket an experiment rolls up into — the unit of 'areas where we don't
    save'. Coarse on purpose (see note). Missing facets collapse to 'unknown' so every experiment lands."""
    kind = str(card.get("kind") or card.get("primitive_kind") or "unknown").split(".")[0]
    family = str(card.get("source_family") or "unknown")
    return f"{kind}|{family}"


def _fine_area(card: dict) -> str:
    """The FINE domain of a card — the unit of 'areas where we need more' (coverage gaps by specific domain)."""
    domains = card.get("domains") or ([card["domain"]] if card.get("domain") else [])
    return str((domains or ["unknown"])[0]) or "unknown"


#: a segment needs at least this many experiments before its average is a signal (not a single-card fluke).
MIN_SEGMENT_N = 5
#: rebuild-token buckets — the SIZE axis. Reuse can't beat rebuild for a TINY primitive (finding it costs
#: more than re-writing it), so this is where 'we don't save' really lives — independent of domain.
_SIZE_BUCKETS = ((0, 64, "tiny <64"), (64, 256, "small 64-255"), (256, 1024, "medium 256-1023"),
                 (1024, 10**9, "large >=1024"))


def _equivalent(a: dict, b: dict) -> bool:
    """A retrieved card is a valid REUSE of the target if it IS the target, or is a true functional
    equivalent — same output_edge AND same input_edge (a composable drop-in), not merely a lexical look-alike."""
    if a.get("primitive_id") and a.get("primitive_id") == b.get("primitive_id"):
        return True
    return (bool(a.get("output_edge")) and a.get("output_edge") == b.get("output_edge")
            and a.get("input_edge") == b.get("input_edge"))


def _experiment(card: dict, index: dict, by_id: dict, k: int, paraphrase: bool = False) -> dict:
    """One reuse-vs-rebuild experiment through the REAL search. Returns a candidate row (serves_truth=false)."""
    query = _query_for(card, paraphrase)
    results, stats = search_with_stats(query, k, index)
    top_score = float(results[0].get("score", 0.0)) if results else 0.0
    # map each hit id back to its full card to test functional equivalence, not just id equality
    hit_rank = None
    for rank, r in enumerate(results, 1):
        cand = by_id.get(r.get("primitive_id")) or r
        if _equivalent(cand, card):
            hit_rank = rank
            break
    hit = hit_rank is not None

    rebuild_tokens = _est_tokens(_spec_text(card))
    # reuse cost = query + the edge cards the agent actually SCANS (it stops at the hit; reads all k on a
    # miss) + a one-line reuse reference. Charging all k even on a rank-1 hit (93% of the time) would be a
    # strawman against reuse — a real agent reads down the list only until it finds the reusable card.
    read_upto = hit_rank if hit else len(results)
    reuse_tokens = _est_tokens(query) + sum(
        _est_tokens(_edge_card_text(by_id.get(r.get("primitive_id")) or r)) for r in results[:read_upto]
    ) + _est_tokens("reuse: " + str(card.get("primitive_id")))
    net_saved = (rebuild_tokens - reuse_tokens) if hit else -reuse_tokens
    # a coverage gap = nothing scored above the floor (the search had no real answer) — an "area we need more"
    is_gap = top_score < GAP_SCORE_FLOOR or not results
    return {
        "record_type": "token_savings_experiment",
        "primitive_id": card.get("primitive_id"),
        "segment": _segment_of(card),
        "fine_area": _fine_area(card),
        "query_tokens": _est_tokens(query),
        "rebuild_tokens": rebuild_tokens,
        "reuse_tokens": reuse_tokens,
        "hit": hit,
        "hit_rank": hit_rank,
        "hit_at_1": hit_rank == 1,
        "top_score": round(top_score, 4),
        "net_saved_tokens": net_saved,
        "coverage_gap": is_gap,
        "candidates_scored": stats.get("candidates_scored") or stats.get("candidate_count"),
        "tokens_basis": TOKENS_BASIS,
        "candidate": True,
        "serves_truth": False,
    }


def run_experiments(cards: list[dict], n: int, k: int, seed: int, paraphrase: bool = False) -> list[dict]:
    """Draw ``n`` experiment cards (seeded, reproducible) and run each through the REAL index built over the
    whole ``cards`` corpus (so every experiment competes against the full distractor set)."""
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    rng = random.Random(seed)
    sample = cards if n >= len(cards) else rng.sample(cards, n)
    return [_experiment(c, index, by_id, k, paraphrase) for c in sample]


def aggregate(rows: list[dict]) -> dict:
    """Roll experiments up into the owner's asks: average saved, precision, break-even, the segments where
    we DON'T save, and the coverage gaps where we NEED more."""
    n = len(rows)
    if not n:
        return {"experiments": 0}
    hits = [r for r in rows if r["hit"]]
    avg_rebuild = sum(r["rebuild_tokens"] for r in rows) / n
    avg_reuse = sum(r["reuse_tokens"] for r in rows) / n
    total_saved = sum(r["net_saved_tokens"] for r in rows)
    precision_at_1 = sum(1 for r in rows if r["hit_at_1"]) / n
    hit_rate = len(hits) / n
    # break-even precision: E[net]=p·rebuild−reuse>0 ⟺ p>reuse/rebuild
    break_even = (avg_reuse / avg_rebuild) if avg_rebuild else float("inf")

    seg: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        seg[r["segment"]].append(r)
    seg_stats = []
    for name, rs in seg.items():
        m = len(rs)
        seg_stats.append({
            "segment": name,
            "experiments": m,
            "avg_net_saved": round(sum(x["net_saved_tokens"] for x in rs) / m, 1),
            "hit_rate": round(sum(1 for x in rs if x["hit"]) / m, 3),
            "coverage_gap_rate": round(sum(1 for x in rs if x["coverage_gap"]) / m, 3),
        })
    seg_stats.sort(key=lambda s: s["avg_net_saved"])
    # "areas where we don't save" = WELL-SAMPLED segments (n>=MIN, not a single-card fluke) with avg net <= 0
    dont_save = [s for s in seg_stats if s["experiments"] >= MIN_SEGMENT_N and s["avg_net_saved"] <= 0]

    # SIZE axis — the honest 'where reuse structurally can't win': a TINY primitive costs less to rebuild
    # than to find, so it nets negative even on a hit. This is domain-independent and the real 'don't save'.
    size_stats = []
    for lo, hi, label in _SIZE_BUCKETS:
        rs = [r for r in rows if lo <= r["rebuild_tokens"] < hi]
        if rs:
            size_stats.append({
                "size_bucket": label, "experiments": len(rs),
                "avg_rebuild_tokens": round(sum(r["rebuild_tokens"] for r in rs) / len(rs), 1),
                "avg_net_saved": round(sum(r["net_saved_tokens"] for r in rs) / len(rs), 1),
                "hit_rate": round(sum(1 for r in rs if r["hit"]) / len(rs), 3),
            })

    # "areas where we need more" = FINE domains carrying the most coverage gaps (search had no usable answer)
    gap_by_area: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        gap_by_area[r.get("fine_area", "unknown")].append(r)
    need_more = sorted(
        ({"area": a, "experiments": len(rs),
          "coverage_gap_rate": round(sum(1 for x in rs if x["coverage_gap"]) / len(rs), 3),
          "avg_net_saved": round(sum(x["net_saved_tokens"] for x in rs) / len(rs), 1)}
         for a, rs in gap_by_area.items() if any(x["coverage_gap"] for x in rs)),
        key=lambda s: (-s["coverage_gap_rate"], -s["experiments"]))[:25]

    return {
        "record_type": "token_savings_summary",
        "generated_at": now_iso(),
        "experiments": n,
        "avg_net_saved_tokens": round(total_saved / n, 1),
        "total_net_saved_tokens": total_saved,
        "avg_rebuild_tokens": round(avg_rebuild, 1),
        "avg_reuse_tokens": round(avg_reuse, 1),
        "precision_at_1": round(precision_at_1, 3),
        "hit_rate": round(hit_rate, 3),
        "break_even_precision": round(break_even, 3),
        "net_positive": total_saved > 0,
        "reduction_ratio_on_hit": round(avg_rebuild / avg_reuse, 1) if avg_reuse else None,
        "net_saved_by_primitive_size": size_stats,
        "segments_ranked_worst_first": seg_stats[:50],
        "areas_where_we_dont_save": dont_save,
        "areas_where_we_need_more": need_more,
        "tokens_basis": TOKENS_BASIS,
        "serves_truth": False,
    }


# ── EXTERNAL-TASK LANE ───────────────────────────────────────────────────────────────────────────────────
# The self-retrieval lanes above hand the search the card's own I/O contract. The honest hard test is a
# FULLY EXTERNAL coding intent — a real task described with no knowledge of the registry's edge vocabulary.
# It answers the two questions self-retrieval can't: (1) verified PRECISION (does search find a TOPICALLY
# CORRECT primitive from a plain-English task?) on a hand-LABELED seed, and (2) real COVERAGE GAPS (which
# tasks the registry cannot serve → "areas where we need more") at breadth.

#: Hand-labeled external tasks. ``expected`` is a concept token that a TOPICALLY-CORRECT primitive's
#: title/edges must contain — a verifiable relevance label (not exact-id). Split across capabilities the
#: registry SHOULD have (screening/dedupe/normalize/retrieval/gov-data) and ones it likely lacks (media/
#: crypto/protocol) so both precision AND gaps are exercised honestly.
_CURATED_EXTERNAL_TASKS: tuple[dict, ...] = (
    {"intent": "screen a company name against the OFAC sanctions list", "domain": "compliance", "expected": "sanction"},
    {"intent": "deduplicate a set of customer records by identity", "domain": "data-quality", "expected": "dedup"},
    {"intent": "extract text from a scanned pdf document via ocr", "domain": "document", "expected": "extract"},
    {"intent": "normalize opportunity records coming from multiple sources", "domain": "data-quality", "expected": "normal"},
    {"intent": "map a record to its canonical entity", "domain": "entity", "expected": "canonical"},
    {"intent": "embed a document into a dense vector for semantic search", "domain": "retrieval", "expected": "embed"},
    {"intent": "rerank search candidates by relevance", "domain": "retrieval", "expected": "rank"},
    {"intent": "look up a python package on pypi", "domain": "dev-tools", "expected": "pypi"},
    {"intent": "search usajobs for federal job postings", "domain": "gov-data", "expected": "usajobs"},
    {"intent": "discover datasets published on data.gov", "domain": "gov-data", "expected": "datagov"},
    {"intent": "search sam.gov for contract opportunities", "domain": "gov-data", "expected": "sam"},
    {"intent": "generate an evidence receipt for a grant", "domain": "gov-data", "expected": "receipt"},
    {"intent": "validate a security scheme for policy compliance", "domain": "security", "expected": "auth"},
    # capabilities the registry most likely lacks — these SHOULD show up as coverage gaps ("need more"):
    {"intent": "implement an oauth2 pkce authorization code flow", "domain": "auth", "expected": "oauth"},
    {"intent": "parse an icalendar ics file into calendar events", "domain": "calendar", "expected": "ical"},
    {"intent": "generate a qr code image from a url", "domain": "encoding", "expected": "qr"},
    {"intent": "rate limit an http endpoint with a token bucket", "domain": "infra", "expected": "rate limit"},
    {"intent": "transcode a video file to h264 mp4", "domain": "media", "expected": "video"},
    {"intent": "sign a jwt access token with rs256", "domain": "auth", "expected": "jwt"},
    {"intent": "geocode a street address to latitude and longitude", "domain": "geo", "expected": "geocode"},
)
#: breadth vocab — deterministic operation × object intents (UNLABELED coverage probes) to reach scale.
_OPS = ("validate", "normalize", "deduplicate", "parse", "extract", "classify", "summarize", "translate",
        "encrypt", "compress", "geocode", "screen", "enrich", "rerank", "embed", "route", "redact", "score")
_OBJECTS = ("phone number", "email address", "postal address", "credit card", "iban", "vat id", "invoice",
            "resume", "contract clause", "medical record", "product review", "news article", "log line",
            "dns record", "git commit", "json schema", "csv row", "markdown doc", "audio clip", "shipping label")


def _generate_external_breadth(n: int, seed: int) -> list[dict]:
    """Deterministic op×object task intents (unlabeled) — coverage probes across a broad surface, so 'need
    more' is measured at scale, not just on the curated seed."""
    combos = [{"intent": f"{op} a {obj}", "domain": obj.split()[-1], "expected": None, "labeled": False}
              for op in _OPS for obj in _OBJECTS]
    rng = random.Random(seed)
    rng.shuffle(combos)
    return combos[:max(0, n)]


def _external_corpus(n: int, seed: int) -> list[dict]:
    """The external task set: the labeled curated seed (always) + generated breadth up to n."""
    curated = [{**t, "labeled": True} for t in _CURATED_EXTERNAL_TASKS]
    breadth = _generate_external_breadth(max(0, n - len(curated)), seed)
    return curated + breadth


def _external_experiment(task: dict, index: dict, by_id: dict, k: int) -> dict:
    """One EXTERNAL-intent experiment: query the plain-English task, measure coverage + (on labeled tasks)
    topical precision + candidate savings. A gap (nothing above the floor) is an 'area we need more'."""
    query = str(task["intent"])
    results, _stats = search_with_stats(query, k, index)
    top = results[0] if results else None
    top_score = float(top.get("score", 0.0)) if top else 0.0
    covered = bool(top) and top_score >= GAP_SCORE_FLOOR
    # topical relevance (labeled tasks only): a top-k card whose text carries the expected concept token
    label_hit: bool | None = None
    if task.get("labeled") and task.get("expected"):
        want = str(task["expected"]).lower()
        label_hit = any(want in (json.dumps(by_id.get(r.get("primitive_id")) or r).lower()) for r in results)

    matched = by_id.get(top.get("primitive_id")) if top else None
    rebuild_tokens = _est_tokens(_spec_text(matched)) if matched else 0
    read_upto = 1 if covered else len(results)
    reuse_tokens = _est_tokens(query) + sum(
        _est_tokens(_edge_card_text(by_id.get(r.get("primitive_id")) or r)) for r in results[:read_upto]) + 3
    # covered -> reuse the match (candidate saving); gap -> wasted search (the agent builds it: 'need more')
    net_saved = (rebuild_tokens - reuse_tokens) if covered else -reuse_tokens
    return {
        "record_type": "external_token_savings_experiment",
        "intent": query,
        "domain": task.get("domain") or "unknown",
        "labeled": bool(task.get("labeled")),
        "expected": task.get("expected"),
        "covered": covered,
        "label_hit": label_hit,
        "top_score": round(top_score, 4),
        "matched_primitive_id": top.get("primitive_id") if top else None,
        "rebuild_tokens": rebuild_tokens,
        "reuse_tokens": reuse_tokens,
        "net_saved_tokens": net_saved,
        "coverage_gap": not covered,
        "tokens_basis": TOKENS_BASIS,
        "candidate": True,
        "serves_truth": False,
    }


def run_external(cards: list[dict], n: int, k: int, seed: int) -> list[dict]:
    """Run the external task corpus against the REAL index built over ``cards``."""
    index = build_index(cards)
    by_id = {c.get("primitive_id"): c for c in cards if c.get("primitive_id")}
    return [_external_experiment(t, index, by_id, k) for t in _external_corpus(n, seed)]


def aggregate_external(rows: list[dict]) -> dict:
    """External-lane rollup: coverage, VERIFIED precision (labeled subset), candidate savings on covered, and
    the coverage-gap domains — the honest 'areas where we need more'."""
    n = len(rows)
    if not n:
        return {"experiments": 0}
    labeled = [r for r in rows if r["labeled"]]
    covered = [r for r in rows if r["covered"]]
    gaps = [r for r in rows if r["coverage_gap"]]
    gap_by_domain: dict[str, int] = defaultdict(int)
    for r in gaps:
        gap_by_domain[r["domain"]] += 1
    need_more = sorted(({"area": d, "gap_count": c} for d, c in gap_by_domain.items()),
                       key=lambda s: -s["gap_count"])[:25]
    return {
        "record_type": "external_token_savings_summary",
        "generated_at": now_iso(),
        "intent_mode": "external",
        "experiments": n,
        "coverage_rate": round(len(covered) / n, 3),
        "coverage_gap_rate": round(len(gaps) / n, 3),
        "labeled_experiments": len(labeled),
        "verified_precision_on_labeled": round(sum(1 for r in labeled if r["label_hit"]) / len(labeled), 3) if labeled else None,
        "avg_net_saved_on_covered": round(sum(r["net_saved_tokens"] for r in covered) / len(covered), 1) if covered else 0,
        "avg_net_saved_all": round(sum(r["net_saved_tokens"] for r in rows) / n, 1),
        "areas_where_we_need_more": need_more,
        "labeled_misses": [{"intent": r["intent"], "expected": r["expected"], "top_score": r["top_score"]}
                           for r in labeled if not r["label_hit"]][:25],
        "tokens_basis": TOKENS_BASIS,
        "serves_truth": False,
    }


def _run_external(n: int, k: int, seed: int, corpus: int, emit_gaps: bool) -> int:
    cards = _load_cards(corpus)
    if not cards:
        print("no real cards found (factory scratch may be gitignored on this checkout); run the factory first")
        return 1
    rows = run_external(cards, n, k, seed)
    summary = aggregate_external(rows)
    paths = _emit(rows, summary, emit_gaps)
    keys = ("intent_mode", "experiments", "coverage_rate", "verified_precision_on_labeled",
            "avg_net_saved_on_covered", "labeled_experiments")
    print(json.dumps({k2: summary[k2] for k2 in keys if k2 in summary}, indent=2))
    print(f"  labeled misses (registry can't serve): {[m['intent'] for m in summary['labeled_misses']]}")
    print(f"  top coverage-gap domains (need more): {[a['area'] for a in summary['areas_where_we_need_more'][:8]]}")
    print(f"  written: {paths['summary_path']}  |  gap areas emitted: {paths['gap_areas_emitted']}")
    return 0


def _load_cards(limit: int) -> list[dict]:
    """Load up to ``limit`` real cards from the first available source (tolerant of a torn factory tail)."""
    for rel in CARD_SOURCES:
        path = _resource(rel)
        if path.exists():
            cards = read_jsonl_tolerant(path)
            cards = [c for c in cards if c.get("primitive_id")]
            return cards[:limit] if limit and limit < len(cards) else cards
    return []


def _emit(rows: list[dict], summary: dict, emit_gaps: bool) -> dict:
    """Persist the per-experiment rows + summary (candidate-only); optionally append coverage-gap AREAS to the
    research queue so 'where we need more' becomes actual acquisition work (never truth, always candidate)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "experiments.jsonl").write_text(
        "".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    emitted = 0
    if emit_gaps and summary.get("areas_where_we_need_more"):
        from scripts.acquisition import research_queue as _rq  # noqa: PLC0415  local: only the gap-emit path needs it
        queue = getattr(_rq, "DEFAULT_QUEUE", OUT_DIR / "areas.jsonl")
        with open(queue, "a", encoding="utf-8") as fh:
            for area in summary["areas_where_we_need_more"]:
                fh.write(json.dumps({
                    "record_type": "research_area",
                    "area": area.get("area") or area.get("segment"),  # external rows key on 'area'; self-retrieval too
                    "reason": "token_savings coverage gap",
                    "coverage_gap_rate": area.get("coverage_gap_rate"),
                    "gap_count": area.get("gap_count"),
                    "source": "run_token_savings_experiments", "candidate": True, "serves_truth": False,
                }) + "\n")
                emitted += 1
    return {"experiments_path": str(OUT_DIR / "experiments.jsonl"),
            "summary_path": str(OUT_DIR / "summary.json"), "gap_areas_emitted": emitted}


def _run(n: int, k: int, seed: int, corpus: int, emit_gaps: bool, paraphrase: bool) -> int:
    cards = _load_cards(corpus)
    if not cards:
        print("no real cards found (factory scratch may be gitignored on this checkout); run the factory first")
        return 1
    rows = run_experiments(cards, n, k, seed, paraphrase)
    summary = aggregate(rows)
    summary["intent_mode"] = "paraphrase" if paraphrase else "descriptive"
    paths = _emit(rows, summary, emit_gaps)
    keys = ("intent_mode", "experiments", "avg_net_saved_tokens", "precision_at_1", "hit_rate",
            "break_even_precision", "net_positive", "reduction_ratio_on_hit")
    print(json.dumps({k2: summary[k2] for k2 in keys if k2 in summary}, indent=2))
    print(f"  worst 3 segments (don't-save first): {[s['segment'] for s in summary['segments_ranked_worst_first'][:3]]}")
    print(f"  areas needing more: {len(summary['areas_where_we_need_more'])}  |  written: {paths['summary_path']}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # A deterministic synthetic corpus: a few clearly-distinct capabilities so retrieval CAN hit, plus a
    # guaranteed-unfindable one so a MISS (negative saving) is exercised. No factory data needed.
    def card(pid, title, inp, out, kind="route", domain="d", fam="synthetic"):
        return {"primitive_id": pid, "title": title, "input_edge": inp, "output_edge": out,
                "kind": kind, "domains": [domain], "source_family": fam,
                "contract": {"in": inp, "out": out}, "blackbox": title * 20, "effects": [title]}
    corpus = [
        card("p:ocr", "extract text from a scanned pdf via ocr", "ScannedPdf", "ExtractedText"),
        card("p:dedupe", "deduplicate records by canonical entity", "RecordSet", "DedupeClusters"),
        card("p:sanction", "screen an entity against the ofac sanctions list", "EntityName", "SanctionsHit"),
        card("p:embed", "embed a document into a dense vector", "Document", "DenseVector"),
        card("p:rerank", "rerank candidates by cross encoder relevance", "Candidates", "RankedCandidates"),
    ]
    rows = run_experiments(corpus, n=len(corpus), k=3, seed=7)
    summ = aggregate(rows)

    checks.append(("every experiment ran + is candidate/serves_truth=false",
                   len(rows) == len(corpus) and all(r["serves_truth"] is False and r["candidate"] for r in rows)))
    checks.append(("token math: a HIT saves rebuild−reuse; a MISS is exactly −reuse", all(
        (r["net_saved_tokens"] == r["rebuild_tokens"] - r["reuse_tokens"]) if r["hit"]
        else (r["net_saved_tokens"] == -r["reuse_tokens"]) for r in rows)))
    checks.append(("break-even precision = avg_reuse/avg_rebuild",
                   abs(summ["break_even_precision"] - summ["avg_reuse_tokens"] / summ["avg_rebuild_tokens"]) < 0.01))
    checks.append(("summary reports the owner's three asks",
                   all(k in summ for k in ("avg_net_saved_tokens", "areas_where_we_dont_save", "areas_where_we_need_more"))))

    # MUTATION 1 — an all-MISS world (query that matches nothing) must yield NEGATIVE average savings. Proves
    # the platform is not rigged to always "win": bad retrieval visibly costs tokens.
    miss_rows = [_experiment({**card("p:unfindable", "zzqq unfindable capability xyzzy", "NoSuchIn", "NoSuchOut"),
                              "input_edge": "zzqq", "output_edge": "xyzzy"}, build_index(corpus),
                             {c["primitive_id"]: c for c in corpus}, k=3) for _ in range(3)]
    checks.append(("MUTATION: all-miss world -> negative net saving (not rigged)",
                   all(r["net_saved_tokens"] < 0 and not r["hit"] for r in miss_rows)))

    # MUTATION 2 — determinism: same seed -> identical summary (VERIFY-THE-VERIFIER).
    again = aggregate(run_experiments(corpus, n=len(corpus), k=3, seed=7))
    checks.append(("determinism: same seed -> identical avg_net_saved + precision",
                   again["avg_net_saved_tokens"] == summ["avg_net_saved_tokens"]
                   and again["precision_at_1"] == summ["precision_at_1"]))

    # A clean self-capability query should HIT (retrieval is real, not always-miss).
    checks.append(("retrieval is real: at least one clean capability is found", summ["hit_rate"] > 0.0))

    # Paraphrase mode rewords the intent (drops half the title, keeps the I/O contract) — the honest-precision
    # lane that doesn't hand the search the card's exact wording.
    c0 = corpus[0]
    checks.append(("paraphrase mode rewords the intent yet keeps the I/O contract",
                   _query_for(c0, paraphrase=True) != _query_for(c0, paraphrase=False)
                   and str(c0["input_edge"]) in _query_for(c0, paraphrase=True)))

    # External-intent lane over the synthetic corpus: curated tasks matching a card (ocr/dedupe/sanction/
    # embed/rerank) should be covered + label-hit; the many with no card must be coverage GAPS. Proves the
    # external lane measures verified precision AND real 'need more', honestly, with no card-vocab handed in.
    ext_rows = run_external(corpus, n=len(_CURATED_EXTERNAL_TASKS), k=3, seed=7)
    ext = aggregate_external(ext_rows)
    checks.append(("external lane: verified precision computed + at least one labeled task hits",
                   ext["verified_precision_on_labeled"] is not None and ext["verified_precision_on_labeled"] > 0.0))
    checks.append(("external lane: capabilities with no card become coverage gaps ('need more')",
                   ext["coverage_gap_rate"] > 0.0 and len(ext["areas_where_we_need_more"]) > 0))
    checks.append(("external rows are candidate/serves_truth=false",
                   all(r["serves_truth"] is False and r["candidate"] for r in ext_rows)))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - run_token_savings_experiments: scaled reuse-vs-rebuild experiments over the REAL search; "
          "net_saved = hit?(rebuild−reuse):(−reuse); misses cost tokens (break-even precision reported); "
          "avg saved + don't-save segments + need-more gaps rolled up; deterministic; serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="bounded offline proof (synthetic corpus, mutation-tested)")
    ap.add_argument("--run", action="store_true", help="run experiments over the real card corpus")
    ap.add_argument("--n", type=int, default=3000, help="number of experiments to run")
    ap.add_argument("--k", type=int, default=5, help="top-k the agent scans per search")
    ap.add_argument("--seed", type=int, default=1, help="sampling seed (reproducible)")
    ap.add_argument("--corpus", type=int, default=0,
                    help="max real cards to index as the distractor set; 0 = FULL corpus (caps are opt-in)")
    ap.add_argument("--emit-gaps", action="store_true", help="append coverage-gap areas to the research queue")
    ap.add_argument("--intent-mode", choices=["descriptive", "paraphrase", "external"], default="descriptive",
                    help="descriptive = I/O + exact title (upper bound); paraphrase = reworded intent (honest); "
                         "external = fully external coding intents (verified precision on a labeled seed + real coverage gaps)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        if args.intent_mode == "external":
            return _run_external(args.n, args.k, args.seed, args.corpus, args.emit_gaps)
        return _run(args.n, args.k, args.seed, args.corpus, args.emit_gaps, args.intent_mode == "paraphrase")
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
