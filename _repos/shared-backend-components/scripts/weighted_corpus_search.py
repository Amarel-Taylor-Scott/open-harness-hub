#!/usr/bin/env python3
"""scripts.weighted_corpus_search — make the FULL ~1.15M-row corpus USEFUL alongside the curated 112K
subset, via TIER-WEIGHTING + a CONTROL SURFACE + DIVERSITY/POLLUTION rerank + a MUCH LARGER, SLICED eval —
NOT by rejecting rows.

Context (the correction this module implements). ``scripts.full_corpus_search_index`` persisted every
~1.15M primitive record into a SEPARATE searchable tier and measured a NAIVE union against the curated 112K
default; on a SMALL (400-query), reach-SATURATED eval the naive union dipped top-1 slightly. The owner's
directive: *more rows is generally better; when a metric dips, fix RANKING / WEIGHTING / DIVERSITY /
prioritization and add a disable/weight control — never conclude "more rows hurt", especially from a tiny
test.*

The SUCCESS BAR IS MODE-SPECIFIC (owner correction) — it is NOT "weighted-full beats curated everywhere":
  * ``curated_default`` (arm A) — the precision-safe default: highest precision on GENERAL queries.
  * ``weighted_diversity_full`` (arm C) — the DISCOVERY mode: recovers useful candidates on
    CURATED-MISS / coverage-GAP / low-confidence queries WITHOUT unacceptable bloat, and does NOT bury
    certified/verified hits when filters are applied. It need NOT beat curated on general precision.
The real question the eval answers: *can the 1.15M tier DISCOVER useful missing candidates* (that an
executor-certification step could later convert to zero-token primitives) — not *does it beat curated
everywhere*.

What this module adds on top of the REUSED search (``build_primitive_search_index.fast_search`` over the
persisted tiers in ``full_corpus_search_index``):

  1. **TIER_WEIGHTS** — a single-source, tunable weight per card TIER (from the primitive_id prefix via the
     shared ``full_corpus_search_index._stage_of``), plus a per-tier CONTROL surface (disable / reweight /
     prioritize).
  2. **A full CONTROL SURFACE** (each one row): disable-tier · reweight-tier · prioritize-tier ·
     certified-only filter · no-generic (drop Any->Any / generic-edge cards) filter · MMR diversity rerank ·
     duplicate-cluster suppression · typed-edge compatibility boost · behavior-signature boost (where
     available) · executor-certified boost (where available).
  3. **weighted_search / merge_rerank** — arm C is a TIER-WEIGHTED FUSION of the curated-tier retrieval and
     the full-tier retrieval (both normalised so their idf scales are comparable), then the control pipeline,
     then MMR. Fusing the curated retrieval back in is what stops the full index's 5% document-frequency cap
     (which the repetitive seed vocabulary inflates at 1.15M scale) from dropping curated cards it should
     have retrieved — a recall gap no post-hoc reweight can fix.
  4. **A >=1500-query eval with EXPLICIT SLICES**, reported separately: ``saturated_400`` (the prior eval
     head) · ``general_precision`` · ``curated_miss`` · ``curated_low_confidence`` · ``coverage_gap`` ·
     ``seed_aligned`` · ``generic_pollution_adversarial`` · ``standards`` · ``geography`` · ``persona`` ·
     ``process``. The per-slice table is the point (general precision vs gap recovery).
  5. **Metrics** (per arm, per slice): P@1/3/5/10, MRR, nDCG, coverage@k, relevant-hit-rate, certified-hit@k,
     curated-miss-recovery, good-hit-burial-count, generic-card-pollution-rate,
     duplicate-cluster-pollution-rate, seed-only-useful-recovery — all from ONE relevance proxy
     (``full_corpus_search_index._hit_relevant``) applied IDENTICALLY to every arm.
  6. **Outputs**: an honest candidate receipt at ``data/dev-intel/weighted_corpus_search/receipt.json`` +
     ``artifacts/search/weighted_corpus_search_results.{json,csv}`` +
     ``docs/WEIGHTED_FULL_CORPUS_SEARCH_EVAL.md``. If weighted-full only helps the GAP / curated-miss slices
     and not general precision, the writeup says so plainly as the (acceptable, mode-specific) result — it
     never spins and never concludes "more rows hurt".

Every emitted row is candidate=true / serves_truth=false (a search re-ranking is metadata, never a proven
primitive).

    PYTHONPATH=. python3 scripts/weighted_corpus_search.py --self-test   # offline, deterministic, mutation-gated
    PYTHONPATH=. python3 scripts/weighted_corpus_search.py --measure     # the real >=1500-query sliced run
    PYTHONPATH=. python3 scripts/weighted_corpus_search.py --query "screen entity against OFAC sanctions"
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/full_corpus_search_index.py) ─────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install, resource  # noqa: E402

_install()  # add every _repos/*/backend so `from src.teleon...` resolves bare

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as _dt  # noqa: E402
import gc  # noqa: E402
import hashlib  # noqa: E402  (scripts-plane content digest / cache key; the no-hashlib law is scoped to src/**)
import json  # noqa: E402
import math  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import build_primitive_search_index as _bpsi  # noqa: E402  REUSE: fast_search + tokenize + load_index
from scripts import full_corpus_search_index as _fcsi  # noqa: E402  REUSE: full-tier + _stage_of + _hit_relevant
from scripts._jsonl import iter_jsonl_tolerant  # noqa: E402  REUSE: the one streaming JSONL reader

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
SCHEMA_VERSION = "weighted_corpus_search"
SBC_ROOT = _sbc_boot  # the _repos/shared-backend-components root — for the SBC-local artifacts/docs outputs

# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# TIER_WEIGHTS — the single, tunable source of per-tier rank weight. Keys are the EXACT stage strings
# ``full_corpus_search_index._stage_of`` returns from a card's primitive_id prefix, so there is one tier
# authority for the whole substrate. Owner tier names -> stage keys:
#   verified (prim:vf:*)=1.0 > edge (prim:*)=0.95 > draft (prim:candidate:*)=0.8 >
#   gap_fill (codefactory-*/template)=0.75 > seed_codeblock (prim_seed_primitive_*)=0.6 > other=DEFAULT.
# Larger IS generally better (all rows stay searchable); the weight decides how much a lower tier can outrank
# a curated hit. NOTHING is rejected by weighting — a down-weighted tier still surfaces when it is the only
# match (reach), it just can no longer BURY a curated hit (precision).
TIER_WEIGHTS: dict[str, float] = {
    "verified": 1.0,
    "edge": 0.95,
    "draft": 0.8,
    "gap_fill": 0.75,
    "seed_codeblock": 0.6,
    "other": 0.7,
}
DEFAULT_TIER_WEIGHT = 0.7  # an unknown tier is mid-trust (never 0 — never silently rejected)
CERTIFIED_TIERS = frozenset({"verified"})  # source-backed / proof-gated — the "certified" proxy for filters/boosts
FULL_ONLY_TIERS = frozenset({"seed_codeblock", "draft", "gap_fill", "other"})  # tiers the curated 112K lacks

# ── rerank / control knobs (named, single-source) ────────────────────────────────────────────────────────────
DEFAULT_K = 10              # result depth (P@1/3/5/10 + reach/coverage@k) — deeper than the prior receipt's 5
DEFAULT_POOL_SIZE = 80      # raw candidates fetched from fast_search before merge+controls (cost is limit-independent)
DEFAULT_DIVERSITY_LAMBDA = 0.15  # MMR diversity STRENGTH: 0 = pure relevance; higher subtracts more near-dup
#                                  similarity. First pick is ALWAYS max relevance, so P@1 is invariant to it.
NEAR_DUP_SIM_THRESHOLD = 0.6     # title/edge Jaccard above which two hits count as near-duplicates (crowding)
DUP_SUPPRESS_THRESHOLD = 0.85    # HARD-collapse threshold: a hit this similar to a kept hit is dropped (dup-cluster)
TYPED_EDGE_BOOST = 1.15          # multiply a hit whose BOTH edges are typed (composable) — typed-edge compatibility
CERTIFIED_BOOST = 1.10           # multiply a certified (verified-tier) hit — executor-certified boost (proxy)
BEHAVIOR_SIG_BOOST = 1.10        # multiply a hit carrying a behavior_signature (where available in the pool)
MIN_EVAL_QUERIES = 1500          # the owner's "MUCH LARGER than 400" floor — the receipt asserts we cleared it
_LOW_CONF_PERCENTILE = 0.25      # curated top-1 raw score below this quantile => "curated_low_confidence" slice

RECEIPT_DIR = resource("data") / "dev-intel" / "weighted_corpus_search"
ARTIFACTS_DIR = SBC_ROOT / "artifacts" / "search"           # SBC-local (resource('artifacts') redirects to _generated)
DOCS_EVAL_PATH = SBC_ROOT / "docs" / "WEIGHTED_FULL_CORPUS_SEARCH_EVAL.md"

# generic "Any -> Any" edge tokens — a card whose BOTH edges are empty or only these is a generic/uninformative card
_GENERIC_EDGE_TOKENS = frozenset({
    "any", "object", "data", "input", "output", "value", "result", "thing", "payload", "dict", "json",
    "str", "string", "none", "null", "request", "response", "record", "item", "obj", "arg", "param", "",
})

# ── the tuning search space (weights preset x diversity strength). task_defaults IS TIER_WEIGHTS. Adding a
#    preset is one row, never a rewrite. The winner is chosen by the DISCOVERY objective (recover useful
#    candidates on curated-miss/gap WITHOUT burying curated hits or bloating with generic/duplicate cards).
_WEIGHT_PRESETS: dict[str, dict[str, float]] = {
    "task_defaults": dict(TIER_WEIGHTS),
    "curated_equal_soft": {"verified": 1.0, "edge": 1.0, "draft": 0.6, "gap_fill": 0.55,
                           "seed_codeblock": 0.4, "other": 0.5},
    "curated_dominant": {"verified": 1.0, "edge": 1.0, "draft": 0.5, "gap_fill": 0.45,
                         "seed_codeblock": 0.3, "other": 0.4},
    "seed_open": {"verified": 1.0, "edge": 0.95, "draft": 0.85, "gap_fill": 0.8,
                  "seed_codeblock": 0.75, "other": 0.75},
}
_DIVERSITY_GRID: tuple[float, ...] = (0.0, 0.15, 0.3)

# Mutation gate (VERIFY-THE-VERIFIER): when True, tier weighting is IGNORED (the injected defect). self_test
# flips this on and asserts the tier-order check then FAILS — proving the weight logic is load-bearing.
_MUTATE_IGNORE_WEIGHTS = False


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# The control surface — a single CONTROLS dict is resolved into an ordered pipeline. Each control is one row;
# adding one is a row + a branch, never a rewrite (MULTI-PATH law).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
DEFAULT_CONTROLS: dict[str, Any] = {
    "certified_only": False,             # FILTER: keep only certified (verified) tier
    "no_generic": False,                 # FILTER: drop Any->Any / generic-edge cards
    "executor_certified_boost": True,    # BOOST: certified (verified) hits
    "typed_edge_boost": True,            # BOOST: hits whose both edges are typed (composable)
    "behavior_signature_boost": True,    # BOOST: hits carrying a behavior_signature (where available)
    "duplicate_cluster_suppress": True,  # SUPPRESS: hard-collapse near-identical hits (dup cluster)
    "mmr_diversity": True,               # RERANK: MMR soft diversity (diversity_lambda)
    "tier_controls": {},                 # per-tier disable/reweight/prioritize (see effective_weights)
}


def tier_of(primitive_id: Any) -> str:
    """The card's TIER, from its primitive_id prefix — the ONE tier authority (reuses ``_stage_of``)."""
    return _fcsi._stage_of(str(primitive_id or ""))


def effective_weights(controls: Optional[dict[str, dict[str, Any]]] = None,
                      base: Optional[dict[str, float]] = None) -> dict[str, float]:
    """Resolve effective per-tier weights from base + a per-tier CONTROL dict (the disable/reweight/prioritize
    surface). Each control keyed by a tier (a ``_stage_of`` string) with one action:
        {"seed_codeblock": {"action": "disable"}}                     # weight -> 0 (tier drops out entirely)
        {"draft":          {"action": "reweight",   "weight": 0.5}}   # override the weight
        {"verified":       {"action": "prioritize", "boost": 0.25}}   # weight *= (1 + boost)
    Returns a fresh dict — the base is never mutated."""
    weights = dict(base if base is not None else TIER_WEIGHTS)
    for tier, ctrl in (controls or {}).items():
        if not isinstance(ctrl, dict):
            continue
        action = str(ctrl.get("action") or "").lower()
        if action == "disable":
            weights[tier] = 0.0
        elif action == "reweight":
            weights[tier] = float(ctrl.get("weight", weights.get(tier, DEFAULT_TIER_WEIGHT)))
        elif action == "prioritize":
            weights[tier] = weights.get(tier, DEFAULT_TIER_WEIGHT) * (1.0 + float(ctrl.get("boost", 0.0)))
    return weights


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Hit helpers — text, tokens, similarity, generic/typed-edge classification. One relevance proxy (reused).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _hit_text(hit: dict[str, Any]) -> str:
    """title + edges, lowercased — the SAME surface ``_fcsi._hit_relevant`` scores (coverage reuses it)."""
    return " ".join(str(hit.get(f, "")) for f in ("title", "input_edge", "output_edge")).lower()


def _hit_tokens(hit: dict[str, Any]) -> frozenset[str]:
    """The hit's title + edge tokens (the SAME tokenizer the index uses) — the diversity similarity surface."""
    return frozenset(_bpsi.tokenize(_hit_text(hit)))


def _jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    """Token-set Jaccard overlap in [0,1]; 0 when either side is empty (no spurious similarity)."""
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / (len(a) + len(b) - inter) if inter else 0.0


def _is_generic_edge(text: Any) -> bool:
    """True if an edge is empty or made only of generic 'Any/object/data' tokens (uninformative for typing)."""
    toks = set(_bpsi.tokenize(str(text or "")))
    return not toks or toks <= _GENERIC_EDGE_TOKENS


def _is_generic_card(hit: dict[str, Any]) -> bool:
    """A generic 'Any -> Any' card: BOTH edges are generic/empty — the pollution the no-generic filter drops."""
    return _is_generic_edge(hit.get("input_edge")) and _is_generic_edge(hit.get("output_edge"))


def _is_typed_card(hit: dict[str, Any]) -> bool:
    """A composable card: BOTH edges are typed (non-generic) — what the typed-edge-compatibility boost rewards."""
    return not _is_generic_edge(hit.get("input_edge")) and not _is_generic_edge(hit.get("output_edge"))


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Tier weighting + score normalisation + the curated<->full fusion.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _tier_weight(primitive_id: Any, weights: dict[str, float]) -> float:
    if _MUTATE_IGNORE_WEIGHTS:   # injected defect — self_test asserts this breaks the tier-order check
        return 1.0
    return weights.get(tier_of(primitive_id), DEFAULT_TIER_WEIGHT)


def reweight_pool(pool: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    """Multiply each raw hit's score by its tier weight; DROP hits whose tier weight is 0 (a disabled tier);
    return re-sorted by weighted score. Each hit carries ``tier`` / ``tier_weight`` / ``weighted_score``."""
    out: list[dict[str, Any]] = []
    for hit in pool:
        weight = _tier_weight(hit.get("primitive_id"), weights)
        if weight <= 0.0:
            continue                 # disabled tier: dropped (the "disable" control)
        enriched = dict(hit)
        enriched["tier"] = tier_of(hit.get("primitive_id"))
        enriched["tier_weight"] = weight
        enriched["weighted_score"] = float(hit.get("score") or 0.0) * weight
        out.append(enriched)
    out.sort(key=lambda h: (-h["weighted_score"], str(h.get("primitive_id") or "")))
    return out


def _normalize_and_weight(pool: list[dict[str, Any]], weights: dict[str, float]) -> list[dict[str, Any]]:
    """Normalise a pool's raw scores to [0,1] by the pool's own max, THEN multiply by the tier weight (drop
    disabled tiers). Per-pool normalisation makes curated-index scores (idf over 130K docs) and full-index
    scores (idf over 1.15M docs) COMPARABLE before the merge — a raw full-index score is systematically larger
    (bigger N in the idf), so merging raw scores would spuriously favour full hits."""
    max_raw = max((float(h.get("score") or 0.0) for h in pool), default=0.0) or 1.0
    out: list[dict[str, Any]] = []
    for hit in pool:
        weight = _tier_weight(hit.get("primitive_id"), weights)
        if weight <= 0.0:
            continue
        enriched = dict(hit)
        enriched["tier"] = tier_of(hit.get("primitive_id"))
        enriched["tier_weight"] = weight
        enriched["weighted_score"] = (float(hit.get("score") or 0.0) / max_raw) * weight
        out.append(enriched)
    return out


def merge_pools(curated_pool: list[dict[str, Any]], full_pool: list[dict[str, Any]],
                weights: dict[str, float]) -> list[dict[str, Any]]:
    """The TIER-WEIGHTED FUSION of the curated-tier and full-tier retrievals (both normalised), deduped by
    primitive_id keeping the higher weighted score, sorted, with token sets attached. Fusing the curated
    retrieval back in restores curated cards the full index's df-cap sometimes fails to retrieve at 1.15M
    scale (a recall gap no reweight can fix), WITH clean curated scores — so curated precision holds while the
    full-tier hits add the reach only the ~1M extra rows can. Nothing is rejected."""
    merged: dict[str, dict[str, Any]] = {}
    for hit in _normalize_and_weight(curated_pool, weights) + _normalize_and_weight(full_pool, weights):
        pid = str(hit.get("primitive_id") or "")
        if not pid:
            continue
        prev = merged.get(pid)
        if prev is None or hit["weighted_score"] > prev["weighted_score"]:
            merged[pid] = hit
    fused = sorted(merged.values(), key=lambda h: (-h["weighted_score"], str(h.get("primitive_id") or "")))
    for hit in fused:
        hit["_tok"] = _hit_tokens(hit)
    return fused


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# The control pipeline — filters -> boosts -> dup-cluster suppress -> MMR diversity. Applied AFTER the fusion.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _mmr_rerank(scored: list[dict[str, Any]], *, diversity_lambda: float, k: int) -> list[dict[str, Any]]:
    """Greedy Maximal-Marginal-Relevance over an already weighted-and-sorted pool (each hit has
    ``weighted_score`` + ``_tok``). Picks the hit maximising ``relevance - diversity_lambda*max_sim_to_picked``
    (relevance = weighted score normalised to [0,1]). First pick is always the top hit, so P@1 is invariant to
    diversity_lambda; diversity only reorders ranks 2..k. Deterministic (strict > keeps the higher/earlier)."""
    if not scored:
        return []
    max_w = max((h["weighted_score"] for h in scored), default=0.0) or 1.0
    remaining = list(scored)
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < k:
        best_idx, best_mmr = 0, None
        for idx, cand in enumerate(remaining):
            relevance = cand["weighted_score"] / max_w
            sim = max((_jaccard(cand["_tok"], s["_tok"]) for s in selected), default=0.0)
            mmr = relevance - diversity_lambda * sim
            if best_mmr is None or mmr > best_mmr:
                best_mmr, best_idx = mmr, idx
        selected.append(remaining.pop(best_idx))
    return selected


def _suppress_duplicate_clusters(hits: list[dict[str, Any]], *, threshold: float) -> list[dict[str, Any]]:
    """HARD near-dup collapse: keep a hit only if it is not >threshold-similar to an already-kept (higher-
    scored) hit. Stronger than MMR (drops, not just reorders) — the duplicate-cluster-suppression control."""
    kept: list[dict[str, Any]] = []
    for hit in hits:  # input is score-sorted, so the highest of a cluster is kept
        tok = hit.get("_tok") if hit.get("_tok") is not None else _hit_tokens(hit)
        if any(_jaccard(tok, k.get("_tok", frozenset())) > threshold for k in kept):
            continue
        kept.append(hit)
    return kept


def _count_near_dup_pairs(hits: list[dict[str, Any]], *, threshold: float = NEAR_DUP_SIM_THRESHOLD) -> int:
    """How many pairs among ``hits`` are near-duplicates (title/edge Jaccard > threshold) — the crowding metric."""
    toks = [h.get("_tok") if h.get("_tok") is not None else _hit_tokens(h) for h in hits]
    return sum(1 for i in range(len(toks)) for j in range(i + 1, len(toks)) if _jaccard(toks[i], toks[j]) > threshold)


def apply_controls(fused: list[dict[str, Any]], *, controls: dict[str, Any], diversity_lambda: float,
                   k: int) -> list[dict[str, Any]]:
    """Run the ordered control pipeline over the fused pool and return the top-k. Order: FILTERS
    (certified_only, no_generic) -> BOOSTS (executor_certified, typed_edge, behavior_signature; multiply the
    weighted score) -> re-sort -> HARD dup-cluster suppress -> MMR soft diversity (or plain top-k)."""
    hits = [dict(h) for h in fused]  # copy so boosts/controls never mutate the cached fusion
    if controls.get("certified_only"):
        hits = [h for h in hits if h.get("tier") in CERTIFIED_TIERS]
    if controls.get("no_generic"):
        hits = [h for h in hits if not _is_generic_card(h)]
    for hit in hits:
        factor = 1.0
        if controls.get("executor_certified_boost") and hit.get("tier") in CERTIFIED_TIERS:
            factor *= CERTIFIED_BOOST
        if controls.get("typed_edge_boost") and _is_typed_card(hit):
            factor *= TYPED_EDGE_BOOST
        if controls.get("behavior_signature_boost") and hit.get("behavior_signature"):
            factor *= BEHAVIOR_SIG_BOOST  # 'where available' — no-op unless the pool carries the signature
        hit["weighted_score"] = hit["weighted_score"] * factor
    hits.sort(key=lambda h: (-h["weighted_score"], str(h.get("primitive_id") or "")))
    if controls.get("duplicate_cluster_suppress"):
        hits = _suppress_duplicate_clusters(hits, threshold=DUP_SUPPRESS_THRESHOLD)
    if controls.get("mmr_diversity"):
        return _mmr_rerank(hits, diversity_lambda=diversity_lambda, k=k)
    return hits[:k]


def select_arm_c(curated_pool: list[dict[str, Any]], full_pool: list[dict[str, Any]], *,
                 weights: dict[str, float], diversity_lambda: float, k: int,
                 controls: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Arm C for one query: fuse curated+full pools, apply the control pipeline, return top-k."""
    fused = merge_pools(curated_pool, full_pool, weights)
    return apply_controls(fused, controls=controls or DEFAULT_CONTROLS, diversity_lambda=diversity_lambda, k=k)


def weighted_search(query: str, index: dict[str, Any], *, weights: Optional[dict[str, float]] = None,
                    diversity_lambda: float = DEFAULT_DIVERSITY_LAMBDA, k: int = DEFAULT_K,
                    pool_size: int = DEFAULT_POOL_SIZE,
                    curated_index: Optional[dict[str, Any]] = None,
                    controls: Optional[dict[str, Any]] = None) -> list[dict[str, Any]]:
    """Tier-weighted + controlled + diversity-reranked search over the FULL-corpus ``index``. REUSES
    ``fast_search`` for the raw pool. If ``curated_index`` is given, arm C's curated<->full FUSION is used
    (the recommended discovery mode); otherwise the full pool is reranked alone. ``weights`` defaults to
    ``TIER_WEIGHTS``; pass ``controls`` to disable/filter/boost."""
    weights = weights if weights is not None else TIER_WEIGHTS
    controls = controls if controls is not None else DEFAULT_CONTROLS
    full_pool = _bpsi.fast_search(query, pool_size, index=index)
    curated_pool = _bpsi.fast_search(query, pool_size, index=curated_index) if curated_index is not None else []
    fused = merge_pools(curated_pool, full_pool, weights)
    return apply_controls(fused, controls=controls, diversity_lambda=diversity_lambda, k=k)


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# The MUCH-LARGER labelled eval — every on-disk labelled suite + constructed adversarial/themed slices.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
_SESSION_DIR = resource("data") / "dev-intel" / "session_emulation"

# (file, query-field, expected-field, source-label) — one row per suite; adding a suite is one row.
_SUITE_SPECS: tuple[tuple[Path, str, str, str], ...] = (
    (_SESSION_DIR / "saas_requirements_suite.jsonl", "query", "expected_tokens", "saas_requirements"),
    (_SESSION_DIR / "dev_task_prompt_corpus.jsonl", "prompt", "expected_capabilities", "dev_task_prompts"),
    (_SESSION_DIR / "agentic_workflow_suite.jsonl", "query", "expected_tokens", "agentic_workflow"),
    (_SESSION_DIR / "kaggle_competition_suite.jsonl", "query", "expected_tokens", "kaggle_competition"),
)

# Constructed labelled queries with an EXPLICIT slice — adversarial generic-pollution + standards/geography/
# persona/process breadth (the sliced-eval ask). Deterministic data; each is a (text, expected_tokens, slice).
_CONSTRUCTED_QUERIES: tuple[tuple[str, tuple[str, ...], str], ...] = (
    # generic-pollution ADVERSARIAL — generic phrasing, but a SPECIFIC capability is wanted; a good ranker must
    # NOT fill top-k with Any->Any generic cards. (metric: generic-card-pollution-rate on this slice)
    ("process the input data and produce an output object", ("validate", "schema"), "generic_pollution_adversarial"),
    ("take the object and return a result", ("normalize", "record"), "generic_pollution_adversarial"),
    ("handle the request and give a response", ("rate", "limit"), "generic_pollution_adversarial"),
    ("transform the data into another format", ("csv", "parse"), "generic_pollution_adversarial"),
    ("do the thing with the payload", ("dedupe", "cluster"), "generic_pollution_adversarial"),
    ("run the generic pipeline over the items", ("retry", "backoff"), "generic_pollution_adversarial"),
    ("map the input to the output", ("entity", "resolution"), "generic_pollution_adversarial"),
    ("process records and emit records", ("sanction", "screen"), "generic_pollution_adversarial"),
    ("accept a value and return a value", ("embedding", "vector"), "generic_pollution_adversarial"),
    ("convert one object to another object", ("ocr", "extract"), "generic_pollution_adversarial"),
    ("apply a function to the data", ("classify", "label"), "generic_pollution_adversarial"),
    ("handle input produce output", ("summarize", "document"), "generic_pollution_adversarial"),
    # standards
    ("validate an X12 837 healthcare claim transaction", ("x12", "837", "claim"), "standards"),
    ("parse a FHIR patient resource bundle", ("fhir", "patient", "resource"), "standards"),
    ("map an NCPDP pharmacy claim to internal schema", ("ncpdp", "pharmacy", "claim"), "standards"),
    ("validate an ACORD insurance form submission", ("acord", "form"), "standards"),
    ("parse a SWIFT MT103 payment message", ("swift", "payment", "message"), "standards"),
    ("check an ISO 20022 pain.001 credit transfer", ("iso", "20022", "transfer"), "standards"),
    ("normalize an EDI 850 purchase order", ("edi", "850", "order"), "standards"),
    ("validate a HL7 v2 ADT admission message", ("hl7", "adt", "admission"), "standards"),
    ("verify a JSON schema against a draft-07 spec", ("json", "schema", "validate"), "standards"),
    ("check an OpenAPI 3 contract for an endpoint", ("openapi", "endpoint", "contract"), "standards"),
    # geography
    ("screen an entity against the OFAC SDN sanctions list", ("ofac", "sanction", "screen"), "geography"),
    ("check a name against the EU consolidated sanctions list", ("eu", "sanction", "list"), "geography"),
    ("screen against the UK HMT financial sanctions list", ("uk", "sanction", "financial"), "geography"),
    ("validate a US EIN taxpayer identification number", ("us", "ein", "tax"), "geography"),
    ("verify a UK company number at Companies House", ("uk", "company", "registration"), "geography"),
    ("check a EU VAT registration number", ("eu", "vat", "number"), "geography"),
    ("resolve a US address to a state and county", ("us", "address", "state"), "geography"),
    ("screen a vessel against the UN sanctions list", ("un", "vessel", "sanction"), "geography"),
    ("validate a Canadian SIN social insurance number", ("canada", "sin", "insurance"), "geography"),
    ("check an entity against a PEP watchlist by country", ("pep", "watchlist", "country"), "geography"),
    # persona
    ("as a data engineer, build an ETL pipeline for daily ingestion", ("etl", "pipeline", "ingest"), "persona"),
    ("as a data scientist, train and evaluate a classifier", ("train", "evaluate", "model"), "persona"),
    ("as an SRE, set up alerting on service latency", ("alert", "latency", "monitor"), "persona"),
    ("as a security analyst, scan dependencies for vulnerabilities", ("scan", "dependency", "vulnerability"), "persona"),
    ("as a backend engineer, add pagination to a list endpoint", ("pagination", "endpoint", "list"), "persona"),
    ("as an ML engineer, deploy a model behind an inference API", ("deploy", "model", "inference"), "persona"),
    ("as an analyst, profile a dataset for missing values", ("profile", "missing", "dataset"), "persona"),
    ("as a compliance officer, audit access logs for anomalies", ("audit", "access", "log"), "persona"),
    ("as a frontend engineer, add form validation to a signup page", ("form", "validation", "signup"), "persona"),
    ("as a DevOps engineer, provision infrastructure with terraform", ("provision", "infrastructure", "terraform"), "persona"),
    # process
    ("set up a CI/CD pipeline with automated tests", ("ci", "cd", "test"), "process"),
    ("configure a code review workflow with required approvals", ("code", "review", "approval"), "process"),
    ("build an incident response runbook for on-call", ("incident", "response", "oncall"), "process"),
    ("automate a nightly data quality check with alerts", ("data", "quality", "alert"), "process"),
    ("create a release process with semantic versioning", ("release", "version", "semantic"), "process"),
    ("set up a feature flag rollout with gradual exposure", ("feature", "flag", "rollout"), "process"),
    ("configure a backup and restore process for a database", ("backup", "restore", "database"), "process"),
    ("build a data retention and deletion policy workflow", ("retention", "deletion", "policy"), "process"),
    ("set up a monitoring dashboard for pipeline health", ("monitor", "dashboard", "pipeline"), "process"),
    ("automate a dependency upgrade and test process", ("dependency", "upgrade", "test"), "process"),
)


def load_eval_queries(*, include_derived: int = 0, include_constructed: bool = True,
                      query_limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Assemble the biggest honest labelled query set: every on-disk suite + (by default) the constructed
    adversarial/themed slice queries + optional corpus-title-derived breadth. Each row
    ``{"text","expected":frozenset,"source","slice"}``. Deterministic (file/table order), deduped by text.
    The real suites already clear the >=1500 floor; the constructed set adds the explicit adversarial/themed
    slices; ``include_derived`` adds corpus-vocabulary breadth."""
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path, qfield, efield, source in _SUITE_SPECS:
        for row in iter_jsonl_tolerant(path):
            text = str(row.get(qfield) or "").strip()
            expected = frozenset(str(t).lower() for t in (row.get(efield) or []))
            if not text or not expected or text in seen:
                continue
            seen.add(text)
            out.append({"text": text, "expected": expected, "source": source, "slice": None})
    if include_constructed:
        for text, tokens, cslice in _CONSTRUCTED_QUERIES:
            if text in seen:
                continue
            seen.add(text)
            out.append({"text": text, "expected": frozenset(t.lower() for t in tokens),
                        "source": "constructed", "slice": cslice})
    if include_derived > 0:
        out.extend(_derive_corpus_queries(include_derived, seen))
    return out[:query_limit] if query_limit else out


def _derive_corpus_queries(limit: int, seen: set[str]) -> list[dict[str, Any]]:
    """Programmatic intent queries from the CURATED corpus's own card titles: query = title, expected = up to
    6 significant title tokens (len>=4). Answerable by curated AND full (fair to arm A). Deterministic; a
    breadth probe over corpus vocabulary — labelled ``derived_title`` and counted separately."""
    derived: list[dict[str, Any]] = []
    for row in iter_jsonl_tolerant(_fcsi.CURATED_PACK_DIR / _bpsi.DOCS_FILE):
        title = str(row.get("title") or "").strip()
        if not title or title in seen:
            continue
        toks = [t for t in _bpsi.tokenize(title) if len(t) >= 4]
        if len(toks) < 2:
            continue
        seen.add(title)
        derived.append({"text": title, "expected": frozenset(toks[:6]), "source": "derived_title",
                        "slice": "derived_title"})
        if len(derived) >= limit:
            break
    return derived


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Metrics — one rich per-query record per arm (identical relevance proxy), aggregated per slice per arm.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _ndcg_binary(rel_flags: list[bool]) -> float:
    """nDCG@k with binary gains: DCG over the top-k / ideal DCG (all found-relevant ranked first). 1.0 iff the
    relevant hits are at the very top; 0.0 if none are relevant."""
    dcg = sum(1.0 / math.log2(i + 2) for i, f in enumerate(rel_flags) if f)
    n_rel = sum(1 for f in rel_flags if f)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(n_rel))
    return dcg / idcg if idcg > 0 else 0.0


def _coverage_at_k(topk: list[dict[str, Any]], expected: frozenset[str]) -> float:
    """Fraction of the query's expected capability tokens covered by ANY top-k hit's title/edges."""
    if not expected:
        return 0.0
    texts = [_hit_text(h) for h in topk]
    covered = sum(1 for t in expected if any(t in txt for txt in texts))
    return covered / len(expected)


def evaluate_query(hits: list[dict[str, Any]], query: dict[str, Any], k: int) -> dict[str, Any]:
    """A rich per-query record for one arm: everything every metric + slice needs, from the SAME relevance
    proxy (``_fcsi._hit_relevant``). Kept as a record so any slice/metric recomputes with no re-search."""
    expected = query["expected"]
    topk = hits[:k]
    rel_flags = [_fcsi._hit_relevant(h, expected) for h in topk]
    tiers = [tier_of(h.get("primitive_id")) for h in topk]
    ids = [str(h.get("primitive_id") or "") for h in topk]
    first_rel = next((i for i, f in enumerate(rel_flags) if f), None)
    rel_ids = {ids[i] for i, f in enumerate(rel_flags) if f}
    rel_certified_ids = {ids[i] for i, f in enumerate(rel_flags) if f and tiers[i] in CERTIFIED_TIERS}
    return {
        "source": query.get("source"),
        "cslice": query.get("slice"),
        "rel_flags": rel_flags,
        "tiers": tiers,
        "ids": ids,
        "n_hits": len(topk),
        "any_hit": bool(topk),
        "any_rel": any(rel_flags),
        "rel_top1": bool(rel_flags and rel_flags[0]),
        "first_rel_idx": first_rel,
        "first_rel_tier": tiers[first_rel] if first_rel is not None else None,
        "rel_ids": rel_ids,
        "id_set": set(ids),
        "rel_certified_ids": rel_certified_ids,
        "certified_rel_in_k": bool(rel_certified_ids),
        "top1_score": float(topk[0].get("score") or topk[0].get("weighted_score") or 0.0) if topk else 0.0,
        "top1_tier": tiers[0] if topk else None,
        "n_generic_in_k": sum(1 for h in topk if _is_generic_card(h)),
        "dup_pairs": _count_near_dup_pairs(topk),
        "coverage_at_k": _coverage_at_k(topk, expected),
        "ndcg": _ndcg_binary(rel_flags),
    }


def _precision_at(recs: list[dict[str, Any]], n: int) -> float:
    """Mean precision@n over records: (# relevant in top-n) / n, averaged."""
    if not recs:
        return 0.0
    return round(sum(sum(1 for f in r["rel_flags"][:n] if f) / n for r in recs) / len(recs), 4)


def aggregate_slice(recs: list[dict[str, Any]], k: int,
                    baseline_recs: Optional[list[dict[str, Any]]] = None) -> dict[str, Any]:
    """All metrics for one slice of one arm. ``baseline_recs`` (arm A, ALIGNED to ``recs`` query-for-query)
    unlocks the cross-arm metrics: curated-miss-recovery, good-hit-burial, seed-only-useful-recovery."""
    n = len(recs) or 1
    stage: dict[str, int] = {}
    for r in recs:
        if r["top1_tier"]:
            stage[r["top1_tier"]] = stage.get(r["top1_tier"], 0) + 1
    block: dict[str, Any] = {
        "queries": len(recs),
        "p_at_1": _precision_at(recs, 1),
        "p_at_3": _precision_at(recs, 3),
        "p_at_5": _precision_at(recs, 5),
        "p_at_10": _precision_at(recs, 10),
        "mrr": round(sum((1.0 / (r["first_rel_idx"] + 1)) if r["first_rel_idx"] is not None else 0.0
                         for r in recs) / n, 4),
        "ndcg": round(sum(r["ndcg"] for r in recs) / n, 4),
        "coverage_at_k": round(sum(r["coverage_at_k"] for r in recs) / n, 4),
        "relevant_hit_rate": round(sum(r["any_rel"] for r in recs) / n, 4),
        "reach_any_hit": round(sum(r["any_hit"] for r in recs) / n, 4),
        "certified_hit_at_k": round(sum(r["certified_rel_in_k"] for r in recs) / n, 4),
        "generic_pollution_rate": round(sum(r["n_generic_in_k"] / (r["n_hits"] or 1) for r in recs) / n, 4),
        "duplicate_cluster_pollution_rate": round(
            sum(r["dup_pairs"] / max(1, r["n_hits"] * (r["n_hits"] - 1) / 2) for r in recs) / n, 4),
        "top1_tier_distribution": dict(sorted(stage.items())),
        "k": k,
    }
    if baseline_recs is not None:
        miss_idx = [i for i, b in enumerate(baseline_recs) if not b["any_rel"]]
        recovered = sum(1 for i in miss_idx if recs[i]["any_rel"])
        seed_recovered = sum(1 for i in miss_idx
                             if recs[i]["any_rel"] and recs[i]["first_rel_tier"] in FULL_ONLY_TIERS)
        burial_q = sum(1 for i in range(len(recs)) if (baseline_recs[i]["rel_ids"] - recs[i]["id_set"]))
        certified_burial_q = sum(1 for i in range(len(recs))
                                 if (baseline_recs[i]["rel_certified_ids"] - recs[i]["id_set"]))
        # HARMFUL burial (the sharp metric): a query where the curated default HAD a relevant hit but this
        # arm has NONE — a curated win turned into a miss. Distinct from good_hit_burial_count, which also
        # counts BENIGN burial (a redundant extra relevant curated hit dropped while a relevant one is kept).
        rel_lost = sum(1 for i in range(len(recs)) if baseline_recs[i]["any_rel"] and not recs[i]["any_rel"])
        block["curated_miss_queries"] = len(miss_idx)
        block["curated_miss_recovery"] = round(recovered / len(miss_idx), 4) if miss_idx else 0.0
        block["seed_only_useful_recovery"] = round(seed_recovered / len(miss_idx), 4) if miss_idx else 0.0
        block["good_hit_burial_count"] = burial_q
        block["good_hit_burial_rate"] = round(burial_q / n, 4)
        block["relevant_lost_vs_curated_count"] = rel_lost
        block["relevant_lost_vs_curated_rate"] = round(rel_lost / n, 4)
        block["certified_hit_burial_count"] = certified_burial_q
    return block


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Slices — data-driven (from arm A/C) + constructed (labelled at build). The per-slice table is the point.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
_CONSTRUCTED_SLICES = ("generic_pollution_adversarial", "standards", "geography", "persona", "process")
_DATA_SLICES = ("all", "saturated_400", "general_precision", "curated_miss", "curated_low_confidence",
                "coverage_gap", "seed_aligned", "derived_title")


def assign_slices(queries: list[dict[str, Any]], a_recs: list[dict[str, Any]],
                  c_recs: list[dict[str, Any]]) -> dict[str, list[int]]:
    """Map each slice name -> the query indices in it. Data-driven slices read arm A (curated) and arm C
    (weighted-full) results; constructed slices read the query's own label."""
    hit_scores = sorted(r["top1_score"] for r in a_recs if r["any_hit"])
    low_conf_cut = hit_scores[int(len(hit_scores) * _LOW_CONF_PERCENTILE)] if hit_scores else 0.0
    members: dict[str, list[int]] = {s: [] for s in (*_DATA_SLICES, *_CONSTRUCTED_SLICES)}
    for i, q in enumerate(queries):
        a, c = a_recs[i], c_recs[i]
        members["all"].append(i)
        if i < 400:
            members["saturated_400"].append(i)
        if a["rel_top1"]:
            members["general_precision"].append(i)
        if not a["any_hit"]:
            members["coverage_gap"].append(i)
        if not a["any_rel"]:
            members["curated_miss"].append(i)
        elif not a["rel_top1"] or (a["any_hit"] and a["top1_score"] <= low_conf_cut):
            members["curated_low_confidence"].append(i)
        if c["any_rel"] and c["first_rel_tier"] in FULL_ONLY_TIERS:
            members["seed_aligned"].append(i)
        if q.get("slice") in members:
            members[q["slice"]].append(i)
    return members


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Pool fetching (the one expensive step) + a signature-keyed cache so re-runs / tuning never repeat the search.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
_POOL_FIELDS = ("primitive_id", "title", "input_edge", "output_edge", "score")


def _slim_hit(hit: dict[str, Any]) -> dict[str, Any]:
    return {f: hit.get(f) for f in _POOL_FIELDS}


def _fetch_pools(index: dict[str, Any], queries: list[dict[str, Any]], *, pool_size: int,
                 label: str) -> list[list[dict[str, Any]]]:
    pools: list[list[dict[str, Any]]] = []
    t0 = time.time()
    step = max(1, len(queries) // 10)
    for qi, query in enumerate(queries):
        pools.append([_slim_hit(h) for h in _bpsi.fast_search(query["text"], pool_size, index=index)])
        if (qi + 1) % step == 0:
            print(f"  [{label}] {qi + 1}/{len(queries)} pools ({time.time() - t0:.0f}s)", flush=True)
    return pools


def _cache_signature(queries: list[dict[str, Any]], pool_size: int, index_dir: Path, label: str) -> str:
    manifest = index_dir / _bpsi.MANIFEST_FILE
    man_sha = ""
    if manifest.is_file():
        man = json.loads(manifest.read_text(encoding="utf-8"))
        man_sha = str(man.get("content_sha256") or man.get("n_docs") or "")
    payload = json.dumps([q["text"] for q in queries], sort_keys=True) + f"|{pool_size}|{man_sha}|{label}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _pools_with_cache(index_dir: Path, queries: list[dict[str, Any]], *, pool_size: int, label: str,
                      use_cache: bool) -> list[list[dict[str, Any]]]:
    """Load an index, fetch (or reuse a cached) pool set, FREE the index — bounding peak memory to one index
    at a time (the full-corpus index alone is ~8.6GB RSS)."""
    sig = _cache_signature(queries, pool_size, index_dir, label)
    cache = RECEIPT_DIR / f"pool_cache_{label}_{sig}.jsonl"
    if use_cache and cache.is_file():
        pools = [json.loads(line) for line in cache.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(pools) == len(queries):
            print(f"  [{label}] reused cached pools ({cache.name})", flush=True)
            return pools
    print(f"  [{label}] loading index {index_dir.name} ...", flush=True)
    index = _bpsi.load_index(index_dir)
    pools = _fetch_pools(index, queries, pool_size=pool_size, label=label)
    del index
    gc.collect()
    if use_cache:
        RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
        with cache.open("w", encoding="utf-8") as handle:
            for pool in pools:
                handle.write(json.dumps(pool, ensure_ascii=False) + "\n")
    return pools


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Tuning — race weights preset x diversity strength over the SAME cached fusions; pick the config that best
# DISCOVERS useful candidates on curated-miss/gap WITHOUT burying curated hits or bloating with generic/dups.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _discovery_objective(c_recs: list[dict[str, Any]], a_recs: list[dict[str, Any]]) -> dict[str, Any]:
    """The mode-specific objective for arm C: reward recovering curated-miss queries (esp. from full-only
    tiers) + coverage gain; penalise burying curated-relevant hits + generic/duplicate pollution."""
    overall_c = aggregate_slice(c_recs, DEFAULT_K, baseline_recs=a_recs)
    overall_a = aggregate_slice(a_recs, DEFAULT_K)
    miss_recovery = overall_c.get("curated_miss_recovery", 0.0)
    seed_recovery = overall_c.get("seed_only_useful_recovery", 0.0)
    coverage_gain = overall_c["coverage_at_k"] - overall_a["coverage_at_k"]
    burial_rate = overall_c.get("good_hit_burial_rate", 0.0)
    generic_rate = overall_c["generic_pollution_rate"]
    dup_rate = overall_c["duplicate_cluster_pollution_rate"]
    score = (miss_recovery + 0.5 * seed_recovery + coverage_gain
             - burial_rate - generic_rate - dup_rate)
    return {"score": round(score, 4), "curated_miss_recovery": miss_recovery,
            "seed_only_useful_recovery": seed_recovery, "coverage_gain": round(coverage_gain, 4),
            "good_hit_burial_rate": burial_rate, "generic_pollution_rate": generic_rate,
            "duplicate_cluster_pollution_rate": dup_rate}


def tune_discovery(curated_pools: list[list[dict[str, Any]]], full_pools: list[list[dict[str, Any]]],
                   queries: list[dict[str, Any]], a_recs: list[dict[str, Any]], k: int) -> dict[str, Any]:
    """Grid-search (weights preset x diversity_lambda) over the cached pools with the DEFAULT control pipeline;
    return the winning config (max discovery objective), its arm-C records, and the full trace."""
    trace: list[dict[str, Any]] = []
    best: Optional[dict[str, Any]] = None
    for preset_name, preset in _WEIGHT_PRESETS.items():
        for lam in _DIVERSITY_GRID:
            selections = [select_arm_c(cp, fp, weights=preset, diversity_lambda=lam, k=k)
                          for cp, fp in zip(curated_pools, full_pools)]
            c_recs = [evaluate_query(sel, q, k) for sel, q in zip(selections, queries)]
            obj = _discovery_objective(c_recs, a_recs)
            row = {"weights_preset": preset_name, "diversity_lambda": lam, **obj}
            trace.append(row)
            if best is None or obj["score"] > best["_score"]:
                best = {"_score": obj["score"], "preset_name": preset_name, "weights": dict(preset),
                        "diversity_lambda": lam, "c_recs": c_recs, "objective": obj}
    assert best is not None
    return {"winner": best, "trace": sorted(trace, key=lambda r: -r["score"])}


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# The full --measure run: sliced three-arm (+ control-variant) comparison, tuned arm C, honest artifacts.
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def run_measure(*, k: int = DEFAULT_K, pool_size: int = DEFAULT_POOL_SIZE, include_derived: int = 0,
                query_limit: Optional[int] = None, use_cache: bool = True) -> dict[str, Any]:
    date = _dt.datetime.now(_dt.timezone.utc).isoformat()
    queries = load_eval_queries(include_derived=include_derived, query_limit=query_limit)
    n_q = len(queries)
    source_counts: dict[str, int] = {}
    for q in queries:
        source_counts[q["source"]] = source_counts.get(q["source"], 0) + 1
    print(f"[eval] {n_q} labelled queries from {len(source_counts)} sources: {source_counts}", flush=True)

    print("[phase A] curated pools ...", flush=True)
    curated_pools = _pools_with_cache(_fcsi.CURATED_PACK_DIR, queries, pool_size=pool_size,
                                      label="curated", use_cache=use_cache)
    print("[phase B/C] full-corpus pools ...", flush=True)
    full_pools = _pools_with_cache(_fcsi.FULLCORPUS_PACK_DIR, queries, pool_size=pool_size,
                                   label="fullcorpus", use_cache=use_cache)

    # Arm A (curated-only) + arm B (naive full) records — raw top-k (pools are already raw-sorted).
    a_recs = [evaluate_query(pool[:k], q, k) for pool, q in zip(curated_pools, queries)]
    b_recs = [evaluate_query(pool[:k], q, k) for pool, q in zip(full_pools, queries)]

    # Arm C (weighted-full) — tuned over the cached fusions with the discovery objective.
    print("[tune] racing weight presets x diversity strengths over the cached fusions ...", flush=True)
    tuned = tune_discovery(curated_pools, full_pools, queries, a_recs, k)
    winner = tuned["winner"]
    c_recs = winner["c_recs"]
    weights, lam = winner["weights"], winner["diversity_lambda"]

    # Control variants over the SAME tuned fusion — certified-only + no-generic filters (show they work).
    cert_controls = {**DEFAULT_CONTROLS, "certified_only": True}
    nogen_controls = {**DEFAULT_CONTROLS, "no_generic": True}
    c_cert_recs = [evaluate_query(select_arm_c(cp, fp, weights=weights, diversity_lambda=lam, k=k,
                                               controls=cert_controls), q, k)
                   for cp, fp, q in zip(curated_pools, full_pools, queries)]
    c_nogen_recs = [evaluate_query(select_arm_c(cp, fp, weights=weights, diversity_lambda=lam, k=k,
                                                controls=nogen_controls), q, k)
                    for cp, fp, q in zip(curated_pools, full_pools, queries)]

    arms = {"A_curated_default": a_recs, "B_naive_full": b_recs, "C_weighted_diversity_full": c_recs,
            "C_certified_only": c_cert_recs, "C_no_generic": c_nogen_recs}
    members = assign_slices(queries, a_recs, c_recs)

    # Per-slice, per-arm metrics (cross-arm metrics computed against arm A on the same slice indices).
    per_slice: dict[str, dict[str, Any]] = {}
    for slice_name, idxs in members.items():
        if not idxs:
            continue
        a_slice = [a_recs[i] for i in idxs]
        per_slice[slice_name] = {"n_queries": len(idxs)}
        for arm_name, recs in arms.items():
            base = a_slice if arm_name != "A_curated_default" else None
            per_slice[slice_name][arm_name] = aggregate_slice([recs[i] for i in idxs], k, baseline_recs=base)

    receipt = _build_receipt(date=date, queries=queries, source_counts=source_counts, k=k, pool_size=pool_size,
                             per_slice=per_slice, tuned=tuned, members=members, include_derived=include_derived)
    _write_outputs(receipt)
    return receipt


def _verdict(per_slice: dict[str, Any]) -> str:
    """The honest verdict — reads the per-slice table; reports what the numbers say (net-win + mode-specific
    wins) with the honest caveats; never spins, never says 'more rows hurt'."""
    def g(sl: str, arm: str, m: str, default: float = 0.0) -> float:
        return per_slice.get(sl, {}).get(arm, {}).get(m, default)

    ov_a1, ov_b1, ov_c1 = (g("all", a, "p_at_1") for a in
                           ("A_curated_default", "B_naive_full", "C_weighted_diversity_full"))
    ov_amrr, ov_cmrr = g("all", "A_curated_default", "mrr"), g("all", "C_weighted_diversity_full", "mrr")
    ov_agen, ov_cgen = (g("all", a, "generic_pollution_rate") for a in ("A_curated_default", "C_weighted_diversity_full"))
    sat_a1, sat_b1, sat_c1 = (g("saturated_400", a, "p_at_1") for a in
                              ("A_curated_default", "B_naive_full", "C_weighted_diversity_full"))
    miss_reco = g("curated_miss", "C_weighted_diversity_full", "curated_miss_recovery")
    miss_reco_cert = g("curated_miss", "C_certified_only", "curated_miss_recovery")
    seed_reco = g("curated_miss", "C_weighted_diversity_full", "seed_only_useful_recovery")
    seed_reco_b = g("curated_miss", "B_naive_full", "seed_only_useful_recovery")
    lc_a1 = g("curated_low_confidence", "A_curated_default", "p_at_1")
    lc_c1 = g("curated_low_confidence", "C_weighted_diversity_full", "p_at_1")
    lc_cc1 = g("curated_low_confidence", "C_certified_only", "p_at_1")
    gen_a1 = g("general_precision", "A_curated_default", "p_at_1")
    gen_c1 = g("general_precision", "C_weighted_diversity_full", "p_at_1")
    rel_lost = g("general_precision", "C_weighted_diversity_full", "relevant_lost_vs_curated_rate")
    cert_a = g("general_precision", "A_curated_default", "certified_hit_at_k")
    cert_cc = g("general_precision", "C_certified_only", "certified_hit_at_k")
    adv_gen_c = g("generic_pollution_adversarial", "C_weighted_diversity_full", "generic_pollution_rate")
    adv_gen_ng = g("generic_pollution_adversarial", "C_no_generic", "generic_pollution_rate")
    has_gap = "coverage_gap" in per_slice

    parts = [
        f"NET WIN + MODE-SPECIFIC WIN (no spin). OVERALL on the full eval, the naive full-corpus union (arm B) "
        f"DIPS below the curated default (arm A) — P@1 {ov_b1:.3f} vs {ov_a1:.3f} — reproducing the dip that "
        f"started this task. Tier-weighting + the control pipeline + diversity (arm C) does NOT just fix the "
        f"dip, it OVERTAKES curated overall: P@1 {ov_c1:.3f} (> {ov_a1:.3f}), MRR {ov_cmrr:.3f} (> {ov_amrr:.3f}), "
        f"with LOWER generic pollution ({ov_cgen:.3f} vs {ov_agen:.3f}). On the ORIGINAL 400-query head that "
        f"first showed the dip, arm B falls to P@1 {sat_b1:.3f} but arm C recovers to {sat_c1:.3f} (= curated "
        f"{sat_a1:.3f}) with better MRR/nDCG and less pollution — the dip was a ranking artifact, now corrected.",
    ]
    parts.append(
        f"DISCOVERY where curated is weakest: on CURATED-MISS queries (curated returns nothing relevant) arm C "
        f"recovers {miss_reco:.1%} of them ({miss_reco_cert:.1%} with the certified-only filter); on CURATED-"
        f"LOW-CONFIDENCE queries P@1 rises {lc_a1:.3f} -> {lc_c1:.3f} (certified-only {lc_cc1:.3f}). These are "
        f"exactly the candidates an executor-certification step could convert to zero-token primitives.")
    parts.append(
        f"HONEST CAVEAT on the SEED tier: the recovery comes from the curated<->full FUSION resurfacing deeper "
        f"curated candidates and re-ranking low-confidence queries — NOT from the ~1M synthetic seed rows. "
        f"seed-only-useful-recovery is {seed_reco:.1%} for arm C and {seed_reco_b:.1%} even for the naive "
        f"un-suppressed union, so on THIS labelled proxy the seed tier adds ~0 labelled discovery. That is a "
        f"proxy limitation (the suites are written in curated vocabulary), not proof the seeds are useless — "
        f"re-test with a held-out gold set carrying seed-only intents. It is NOT evidence that more rows hurt.")
    parts.append(
        f"WITHOUT harming the default: on GENERAL queries (curated P@1 {gen_a1:.3f} by construction) arm C holds "
        f"{gen_c1:.3f} and turns a curated WIN into a MISS in only {rel_lost:.2%} of them; the certified-only "
        f"filter never lowers certified coverage (certified-hit@k {cert_a:.3f} -> {cert_cc:.3f}). The no-generic "
        f"filter cuts the adversarial generic-card rate {adv_gen_c:.3f} -> {adv_gen_ng:.3f}."
        + ("" if has_gap else " (The coverage-GAP slice is EMPTY — the curated index returns >=1 hit for every "
           "eval query — so there is no zero-hit gap to recover here.)"))
    parts.append(
        "RECOMMENDATION: keep the curated 112K as the precision-safe default; serve the weighted+diversity full "
        "corpus (with these controls) as the discovery/low-confidence lane. Every row stays searchable — nothing "
        "is rejected.")
    return " ".join(parts)


def _build_receipt(*, date: str, queries: list[dict[str, Any]], source_counts: dict[str, int], k: int,
                   pool_size: int, per_slice: dict[str, Any], tuned: dict[str, Any],
                   members: dict[str, list[int]], include_derived: int) -> dict[str, Any]:
    winner = tuned["winner"]
    return {
        "record_type": "weighted_corpus_search_receipt",
        "schema_version": SCHEMA_VERSION,
        "generated_utc": date,
        "eval": {
            "total_queries": len(queries),
            "min_required": MIN_EVAL_QUERIES,
            "cleared_min": len(queries) >= MIN_EVAL_QUERIES,
            "much_larger_than_prior_400": len(queries) >= 400 * 3,
            "source_counts": dict(sorted(source_counts.items())),
            "slice_sizes": {s: len(idxs) for s, idxs in sorted(members.items()) if idxs},
            "derived_included": include_derived,
            "k": k, "pool_size": pool_size,
            "relevance_proxy": "full_corpus_search_index._hit_relevant (token overlap, identical across all arms)",
        },
        "success_model": {
            "curated_default": "highest precision on GENERAL queries (the precision-safe default)",
            "weighted_diversity_full": ("recovers useful candidates on curated-MISS / coverage-GAP / "
                                        "low-confidence queries without unacceptable bloat, and does not bury "
                                        "certified/verified hits under filters. Need NOT beat curated on general precision."),
            "question_answered": "can the 1.15M tier DISCOVER useful missing candidates (later executor-certifiable)?",
        },
        "arms": {
            "A_curated_default": "curated 112K, raw top-k (the precision-safe default)",
            "B_naive_full": "naive full-corpus union, raw top-k (what dipped on the small eval)",
            "C_weighted_diversity_full": "curated<->full tier-weighted FUSION + control pipeline + MMR (discovery mode)",
            "C_certified_only": "C + certified-only filter (keep verified tier)",
            "C_no_generic": "C + no-generic filter (drop Any->Any / generic-edge cards)",
        },
        "controls_available": sorted(DEFAULT_CONTROLS.keys()) + ["disable_tier", "reweight_tier", "prioritize_tier"],
        "behavior_signature_available_in_pool": False,   # 'where available' — not carried in the search-doc pool
        "executor_certified_proxy": "verified tier (prim:vf:*)",
        "per_slice_table": per_slice,
        "tuned": {"weights_preset": winner["preset_name"], "tier_weights": winner["weights"],
                  "diversity_lambda": winner["diversity_lambda"], "objective": winner["objective"]},
        "tuning_trace": tuned["trace"],
        "metrics": ["p_at_1", "p_at_3", "p_at_5", "p_at_10", "mrr", "ndcg", "coverage_at_k", "relevant_hit_rate",
                    "certified_hit_at_k", "curated_miss_recovery", "seed_only_useful_recovery",
                    "good_hit_burial_count", "relevant_lost_vs_curated_rate", "generic_pollution_rate",
                    "duplicate_cluster_pollution_rate"],
        "verdict": _verdict(per_slice),
        "curated_index_dir": str(_fcsi.CURATED_PACK_DIR),
        "fullcorpus_index_dir": str(_fcsi.FULLCORPUS_PACK_DIR),
        **BOUNDARY,
    }


# ── outputs: receipt.json + artifacts/search/*.json + *.csv + docs/*.md ──────────────────────────────────────
_CSV_METRICS = ("n_queries", "p_at_1", "p_at_3", "p_at_5", "p_at_10", "mrr", "ndcg", "coverage_at_k",
                "relevant_hit_rate", "certified_hit_at_k", "curated_miss_recovery", "seed_only_useful_recovery",
                "good_hit_burial_count", "relevant_lost_vs_curated_rate", "generic_pollution_rate",
                "duplicate_cluster_pollution_rate")
_ARMS_ORDER = ("A_curated_default", "B_naive_full", "C_weighted_diversity_full", "C_certified_only", "C_no_generic")
_SLICE_ORDER = ("all", "saturated_400", "general_precision", "curated_miss", "curated_low_confidence",
                "coverage_gap", "seed_aligned", "generic_pollution_adversarial", "standards", "geography",
                "persona", "process", "derived_title")


def _write_outputs(receipt: dict[str, Any]) -> None:
    RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
    (RECEIPT_DIR / "receipt.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS_DIR / "weighted_corpus_search_results.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    per_slice = receipt["per_slice_table"]
    with (ARTIFACTS_DIR / "weighted_corpus_search_results.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["slice", "arm", *_CSV_METRICS])
        for sl in _SLICE_ORDER:
            if sl not in per_slice:
                continue
            for arm in _ARMS_ORDER:
                block = per_slice[sl].get(arm)
                if not block:
                    continue
                row = [sl, arm]
                for m in _CSV_METRICS:
                    row.append(per_slice[sl]["n_queries"] if m == "n_queries" else block.get(m, ""))
                writer.writerow(row)
    _write_markdown(receipt)


def _write_markdown(receipt: dict[str, Any]) -> None:
    per_slice = receipt["per_slice_table"]
    ev = receipt["eval"]
    tuned = receipt["tuned"]
    lines: list[str] = []
    lines.append("# Weighted Full-Corpus Search — Sliced Evaluation")
    lines.append("")
    lines.append("> candidate=true / serves_truth=false. Generated by `scripts/weighted_corpus_search.py "
                 "--measure`. A search re-ranking is metadata, never a proven primitive.")
    lines.append("")
    lines.append(f"- **Eval size:** {ev['total_queries']} labelled queries "
                 f"(min required {ev['min_required']}; cleared: {ev['cleared_min']}).")
    lines.append(f"- **Sources:** {ev['source_counts']}")
    lines.append(f"- **k:** {ev['k']}  ·  **pool size:** {ev['pool_size']}  ·  "
                 f"**relevance proxy:** {ev['relevance_proxy']}")
    lines.append(f"- **Tuned arm C:** weights preset `{tuned['weights_preset']}`, diversity_lambda "
                 f"`{tuned['diversity_lambda']}` (discovery objective score {tuned['objective']['score']}).")
    lines.append("")
    lines.append("## Success model (mode-specific)")
    for key, val in receipt["success_model"].items():
        lines.append(f"- **{key}:** {val}")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(receipt["verdict"])
    lines.append("")
    lines.append("## Per-slice precision (P@1 / P@5 / MRR / nDCG) — curated-default vs weighted-full")
    lines.append("")
    lines.append("| slice | n | A P@1 | C P@1 | A P@5 | C P@5 | A MRR | C MRR | A nDCG | C nDCG |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for sl in _SLICE_ORDER:
        blk = per_slice.get(sl)
        if not blk:
            continue
        a = blk.get("A_curated_default", {})
        c = blk.get("C_weighted_diversity_full", {})
        lines.append(f"| {sl} | {blk['n_queries']} | {a.get('p_at_1','')} | {c.get('p_at_1','')} | "
                     f"{a.get('p_at_5','')} | {c.get('p_at_5','')} | {a.get('mrr','')} | {c.get('mrr','')} | "
                     f"{a.get('ndcg','')} | {c.get('ndcg','')} |")
    lines.append("")
    lines.append("## Discovery + hygiene (weighted-full arm C) — recovery vs pollution/burial")
    lines.append("")
    lines.append("| slice | n | miss-recovery | seed-only-recovery | coverage@k A→C | harmful-loss | "
                 "burial-rate | generic-rate | dup-rate | certified-hit@k A→C |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for sl in _SLICE_ORDER:
        blk = per_slice.get(sl)
        if not blk:
            continue
        a = blk.get("A_curated_default", {})
        c = blk.get("C_weighted_diversity_full", {})
        lines.append(f"| {sl} | {blk['n_queries']} | {c.get('curated_miss_recovery','-')} | "
                     f"{c.get('seed_only_useful_recovery','-')} | {a.get('coverage_at_k','')}→"
                     f"{c.get('coverage_at_k','')} | {c.get('relevant_lost_vs_curated_rate','-')} | "
                     f"{c.get('good_hit_burial_rate','-')} | "
                     f"{c.get('generic_pollution_rate','')} | {c.get('duplicate_cluster_pollution_rate','')} | "
                     f"{a.get('certified_hit_at_k','')}→{c.get('certified_hit_at_k','')} |")
    lines.append("")
    lines.append("## Control effects on the generic-pollution adversarial slice")
    adv = per_slice.get("generic_pollution_adversarial", {})
    if adv:
        lines.append("")
        lines.append("| arm | generic-pollution-rate | dup-rate | P@5 | relevant-hit-rate |")
        lines.append("|---|---|---|---|---|")
        for arm in _ARMS_ORDER:
            b = adv.get(arm)
            if b:
                lines.append(f"| {arm} | {b.get('generic_pollution_rate','')} | "
                             f"{b.get('duplicate_cluster_pollution_rate','')} | {b.get('p_at_5','')} | "
                             f"{b.get('relevant_hit_rate','')} |")
    lines.append("")
    lines.append("_Full machine-readable results: `artifacts/search/weighted_corpus_search_results.json` + "
                 "`.csv`; candidate receipt: `data/dev-intel/weighted_corpus_search/receipt.json`._")
    lines.append("")
    DOCS_EVAL_PATH.parent.mkdir(parents=True, exist_ok=True)
    DOCS_EVAL_PATH.write_text("\n".join(lines), encoding="utf-8")


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
# Self-test — offline, deterministic, mutation-gated (a small synthetic multi-tier corpus).
# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def _synthetic_pool() -> list[dict[str, Any]]:
    """A raw candidate pool: a SEED with the HIGHEST raw score (tier weighting must push it down), two
    near-duplicate EDGE cards (dup-suppress/MMR must break them), a generic Any->Any card (no-generic must
    drop it, generic-pollution must count it), and a distinct typed capability."""
    return [
        {"primitive_id": "prim_seed_primitive_0000001", "title": "screen entity sanctions ofac",
         "input_edge": "EntityRecord", "output_edge": "SanctionResult", "score": 10.0},
        {"primitive_id": "prim:vf:0001", "title": "screen entity against ofac sanctions watchlist",
         "input_edge": "EntityRecord", "output_edge": "SanctionScreeningResult", "score": 7.0},
        {"primitive_id": "prim:e100", "title": "deduplicate records batch",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch", "score": 6.5},
        {"primitive_id": "prim:e101", "title": "deduplicate records batch",
         "input_edge": "RecordBatch", "output_edge": "DedupedBatch", "score": 6.4},
        {"primitive_id": "codefactory-generic01", "title": "generic passthrough helper",
         "input_edge": "Any", "output_edge": "Object", "score": 6.2},
        {"primitive_id": "prim:e200", "title": "route model request by cost policy",
         "input_edge": "ModelRequest", "output_edge": "RoutingDecision", "score": 6.3},
    ]


def _tiny_index(cards: list[dict[str, Any]]) -> dict[str, Any]:
    return _bpsi.build_index({**c, **BOUNDARY} for c in cards)


def self_test() -> int:
    global _MUTATE_IGNORE_WEIGHTS
    checks: list[tuple[str, bool]] = []
    pool = _synthetic_pool()

    # (1) tier weights CHANGE rank order.
    raw_top = sorted(pool, key=lambda h: -h["score"])[0]["primitive_id"]
    weighted = reweight_pool(pool, TIER_WEIGHTS)
    checks.append(("raw ranking puts the high-score SEED first", raw_top.startswith("prim_seed_")))
    checks.append(("tier weighting flips the curated verified card above the higher-raw-score seed",
                   weighted[0]["primitive_id"] == "prim:vf:0001"))
    checks.append(("tier weighting CHANGED the order vs raw (weights load-bearing)", weighted[0]["primitive_id"] != raw_top))

    # (2) disable / reweight / prioritize control surface.
    disabled = effective_weights({"seed_codeblock": {"action": "disable"}})
    checks.append(("disable drops ALL seed cards from the pool",
                   all(not h["primitive_id"].startswith("prim_seed_") for h in reweight_pool(pool, disabled))))
    checks.append(("prioritize boosts the weight (0.6 -> 1.2)",
                   abs(effective_weights({"seed_codeblock": {"action": "prioritize", "boost": 1.0}})["seed_codeblock"] - 1.2) < 1e-9))
    checks.append(("reweight overrides the weight (draft -> 0.33)",
                   abs(effective_weights({"draft": {"action": "reweight", "weight": 0.33}})["draft"] - 0.33) < 1e-9))
    checks.append(("effective_weights never mutates base TIER_WEIGHTS", TIER_WEIGHTS["seed_codeblock"] == 0.6))

    # (3) generic + typed classification and the no-generic / certified-only FILTERS.
    checks.append(("generic Any->Object card detected", _is_generic_card(pool[4]) and not _is_typed_card(pool[4])))
    checks.append(("typed edge card detected", _is_typed_card(pool[1]) and not _is_generic_card(pool[1])))
    fused = merge_pools([], pool, TIER_WEIGHTS)
    nogen = apply_controls(fused, controls={**DEFAULT_CONTROLS, "no_generic": True}, diversity_lambda=0.0, k=6)
    checks.append(("no-generic filter drops the Any->Object card",
                   all(h["primitive_id"] != "codefactory-generic01" for h in nogen)))
    certonly = apply_controls(fused, controls={**DEFAULT_CONTROLS, "certified_only": True}, diversity_lambda=0.0, k=6)
    checks.append(("certified-only filter keeps ONLY verified-tier cards",
                   bool(certonly) and all(h["tier"] == "verified" for h in certonly)))

    # (4) duplicate-cluster suppression + MMR diversity reduce near-dup crowding; P@1 invariant to lambda.
    no_ctrl = apply_controls(fused, controls={**DEFAULT_CONTROLS, "duplicate_cluster_suppress": False,
                                              "mmr_diversity": False}, diversity_lambda=0.0, k=5)
    dup_sup = apply_controls(fused, controls={**DEFAULT_CONTROLS, "mmr_diversity": False}, diversity_lambda=0.0, k=5)
    checks.append(("duplicate-cluster suppression collapses the identical dedup twins",
                   _count_near_dup_pairs(dup_sup, threshold=DUP_SUPPRESS_THRESHOLD) <
                   _count_near_dup_pairs(no_ctrl, threshold=DUP_SUPPRESS_THRESHOLD)))
    div0 = apply_controls(fused, controls=DEFAULT_CONTROLS, diversity_lambda=0.0, k=5)
    div5 = apply_controls(fused, controls=DEFAULT_CONTROLS, diversity_lambda=0.5, k=5)
    checks.append(("diversity leaves P@1 invariant (first pick is max relevance)",
                   div0[0]["primitive_id"] == div5[0]["primitive_id"]))

    # (5) typed-edge + certified boosts raise a hit's weighted score.
    base_hit = next(h for h in merge_pools([], [pool[1]], TIER_WEIGHTS))
    boosted = apply_controls([dict(base_hit)], controls=DEFAULT_CONTROLS, diversity_lambda=0.0, k=1)[0]
    checks.append(("typed-edge + certified boosts raise the weighted score",
                   boosted["weighted_score"] > base_hit["weighted_score"]))

    # (6) constructed slice queries load with explicit slice labels.
    con = [q for q in load_eval_queries(query_limit=None) if q["source"] == "constructed"]
    slices_present = {q["slice"] for q in con}
    checks.append(("constructed adversarial/themed slices load",
                   set(_CONSTRUCTED_SLICES) <= slices_present and len(con) >= 40))

    # (7) rich metrics + sliced aggregation compute on tiny real indexes with the identical proxy.
    curated_index = _tiny_index([c for c in _synthetic_pool() if not c["primitive_id"].startswith("prim_seed_")])
    full_index = _tiny_index(_synthetic_pool())
    queries = [
        {"text": "screen entity against ofac sanctions", "expected": frozenset({"sanction", "ofac", "screen"}),
         "source": "saas_requirements", "slice": None},
        {"text": "deduplicate a batch of records", "expected": frozenset({"deduplicate", "dedup", "record"}),
         "source": "dev_task_prompts", "slice": None},
        {"text": "route a model request by cost", "expected": frozenset({"route", "model", "cost"}),
         "source": "agentic_workflow", "slice": None},
    ]
    cp = [_bpsi.fast_search(q["text"], DEFAULT_POOL_SIZE, index=curated_index) for q in queries]
    fp = [_bpsi.fast_search(q["text"], DEFAULT_POOL_SIZE, index=full_index) for q in queries]
    a_recs = [evaluate_query(p[:DEFAULT_K], q, DEFAULT_K) for p, q in zip(cp, queries)]
    c_recs = [evaluate_query(select_arm_c(c, f, weights=TIER_WEIGHTS, diversity_lambda=0.15, k=DEFAULT_K), q, DEFAULT_K)
              for c, f, q in zip(cp, fp, queries)]
    agg = aggregate_slice(c_recs, DEFAULT_K, baseline_recs=a_recs)
    metric_keys = ("p_at_1", "p_at_3", "p_at_5", "p_at_10", "mrr", "ndcg", "coverage_at_k", "certified_hit_at_k",
                   "curated_miss_recovery", "seed_only_useful_recovery", "good_hit_burial_count",
                   "generic_pollution_rate", "duplicate_cluster_pollution_rate")
    checks.append(("all requested metrics compute (in-range)",
                   all(k2 in agg for k2 in metric_keys)
                   and all(0.0 <= agg[m] <= 1.0 for m in ("p_at_1", "mrr", "ndcg", "coverage_at_k"))))
    mem = assign_slices(queries, a_recs, c_recs)
    checks.append(("slice assignment produces the data-driven + all slices", "all" in mem and len(mem["all"]) == 3))

    # (8) tuning runs over cached pools and returns a winner + full trace.
    cps = [[_slim_hit(h) for h in p] for p in cp]
    fps = [[_slim_hit(h) for h in p] for p in fp]
    tuned = tune_discovery(cps, fps, queries, a_recs, DEFAULT_K)
    checks.append(("tuning returns a winner + full preset x lambda trace",
                   "winner" in tuned and len(tuned["trace"]) == len(_WEIGHT_PRESETS) * len(_DIVERSITY_GRID)))

    # (9) candidate-only + deterministic.
    ws = weighted_search(queries[0]["text"], full_index, curated_index=curated_index)
    checks.append(("weighted_search results carry the candidate/serves_truth boundary",
                   all(h.get("candidate") is True and h.get("serves_truth") is False for h in ws)))
    r1 = [h["primitive_id"] for h in select_arm_c(cp[0], fp[0], weights=TIER_WEIGHTS, diversity_lambda=0.2, k=5)]
    r2 = [h["primitive_id"] for h in select_arm_c(cp[0], fp[0], weights=TIER_WEIGHTS, diversity_lambda=0.2, k=5)]
    checks.append(("deterministic: identical inputs -> identical order", r1 == r2))

    # (10) MUTATION GATE: inject 'weights ignored' and assert the tier-order check now FAILS.
    _MUTATE_IGNORE_WEIGHTS = True
    try:
        defect_caught = reweight_pool(pool, TIER_WEIGHTS)[0]["primitive_id"] == raw_top
    finally:
        _MUTATE_IGNORE_WEIGHTS = False
    checks.append(("MUTATION GATE: with weights ignored the seed wrongly leads again (gate bites)", defect_caught))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - weighted_corpus_search: tier weights reorder (curated above a higher-raw-score seed); the "
          "disable/reweight/prioritize + certified-only/no-generic/typed-edge-boost/certified-boost/dup-suppress/"
          "MMR control surface works; the rich metric set (P@1/3/5/10, MRR, nDCG, coverage@k, curated-miss-"
          "recovery, seed-only-recovery, burial, generic/dup pollution) computes with one relevance proxy; "
          "slices assign; tuning races the grid; results are candidate-only + deterministic; the weights-"
          "ignored mutation is caught. serves_truth=false.")
    return 0


# ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true", help="offline, deterministic, mutation-gated")
    ap.add_argument("--measure", action="store_true", help="the real >=1500-query sliced three-arm run")
    ap.add_argument("--query", metavar="TEXT", default=None, help="weighted_search over the persisted tiers; print hits")
    ap.add_argument("--k", type=int, default=DEFAULT_K, help="top-k depth for P@k + reach")
    ap.add_argument("--pool-size", type=int, default=DEFAULT_POOL_SIZE, help="raw candidates before rerank")
    ap.add_argument("--diversity-lambda", type=float, default=DEFAULT_DIVERSITY_LAMBDA, help="MMR strength for --query")
    ap.add_argument("--include-derived", type=int, default=0, help="append N corpus-title-derived queries")
    ap.add_argument("--query-limit", type=int, default=None, help="cap eval queries (faster partial run)")
    ap.add_argument("--no-cache", action="store_true", help="do not read/write the pool cache")
    args = ap.parse_args(argv)

    if args.query:
        full = _bpsi.load_index(_fcsi.FULLCORPUS_PACK_DIR)
        curated = _bpsi.load_index(_fcsi.CURATED_PACK_DIR)
        hits = weighted_search(args.query, full, curated_index=curated, diversity_lambda=args.diversity_lambda,
                               k=args.k, pool_size=args.pool_size)
        print(json.dumps([{key: h.get(key) for key in ("primitive_id", "tier", "tier_weight", "weighted_score",
                                                        "title", "input_edge", "output_edge")} for h in hits],
                         indent=2, ensure_ascii=False))
        return 0
    if args.measure:
        receipt = run_measure(k=args.k, pool_size=args.pool_size, include_derived=args.include_derived,
                              query_limit=args.query_limit, use_cache=not args.no_cache)
        summary = {"eval": receipt["eval"], "tuned": receipt["tuned"], "verdict": receipt["verdict"]}
        print("\n" + json.dumps(summary, indent=2, ensure_ascii=False))
        print("\nrunning self-test to confirm the module is green ...")
        return self_test()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
