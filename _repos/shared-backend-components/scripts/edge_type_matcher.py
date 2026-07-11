#!/usr/bin/env python3
"""scripts.edge_type_matcher — the intelligent edge matcher that lifts near-disconnected EXACT edge
connectivity (~10% raw-string equality) to a MEASURED, several-fold-higher TYPE-AWARE connectivity, factored
as ONE reusable module. The type-aware ceiling is corpus-dependent and is EMITTED, never asserted — run
``--connectivity`` for the live figure (roughly ~0.6–0.8 on the current verified corpus). It is deliberately
NOT the ~99% that ``bench_intelligent_composition``'s loose "any shared token" proxy reports: that proxy
over-matches; this matcher applies a strict Jaccard floor, so its honest number is lower — and trustworthy
(see the DISCLOSURE note below).

The measured crux of the composition thesis (bench_intelligent_composition, demo_solver_route_composition):
two primitives chain only when a producer's ``output_edge`` satisfies the next consumer's ``input_edge``. Under
RAW STRING EQUALITY that almost never happens — the edge namespace is ~4,400 free-text snowflakes
("NormalizedRecord" vs "NormalizedRecordBatch", "graph" vs "AdjacencyGraph") — so the route graph is nearly
disconnected (~10% input-satisfiability). The lever is NOT a bigger cache; it is a smart MATCHER that decides
type-compatibility instead of string-identity. This module is that matcher, and it is deliberately factored so
every composer/benchmark can import the SAME decision (today each reimplements its own).

Two reused levers combine into one type-compatibility verdict (strongest tier wins):

  * EXACT      — raw ``output_edge`` string == ``input_edge`` string (today's baseline; tier 0, highest trust).
  * CANONICAL  — ``canonicalize_edge(output) == canonicalize_edge(input)`` after folding BOTH edges onto the
                 shared canonical namespace (``scripts.build_edge_type_retrofit.canonicalize_edge`` — THE
                 normalizer, single-sourced; it lands on the curated ``build_canonical_edge_type_vocabulary``
                 type ids: graph→AdjacencyGraph, Row→RecordBatch). A canonical match onto a CURATED type is
                 higher-confidence than onto an ad-hoc fold. Tier 1.
  * TOKEN      — significant TYPE-TOKEN overlap (camelCase/compound split, noise-word stripped) above a Jaccard
                 floor. This is the fuzzy lever that catches type-variants the canonical fold keeps apart —
                 'NormalizedRecordBatch' vs 'NormalizedRecord' fold to different ids but share {normalized,
                 record}. Stricter than the "any shared token" proxy in bench (which over-matches). Tier 2.

DISCLOSURE — read the tiers, not just the single number: the combined type connectivity is DOMINATED by the
fuzzy TOKEN tier, the WEAKEST-confidence lever (edges sharing >= the Jaccard floor of significant tokens);
the higher-trust canonical-vocabulary fold alone is much lower. ``connectivity_report`` therefore breaks out
exact/canonical/token/type separately AND emits ``token_share_of_type`` (the COMPUTED token/type fraction,
typically the large majority) — so the single lift number reads as CANDIDATE type-COMPATIBILITY, never
verified type-equality.

ADDITIONAL higher-REACH lanes (REUSED wholesale from ``scripts.edge_representations`` — the multi-representation
portfolio; NOT reimplemented here, and deliberately NOT folded into the ``type`` union above, which stays
exact∪canonical∪token so ``exact``/``canonical``/``token``/``type`` behave EXACTLY as before). They are separate,
selectable lanes a composer reaches for when it needs more REACH at lower precision:

  * FAMILY     — the DOMINANT recurring type-token (``edge_representations.build_family_index``): many surface
                 variants collapse onto ONE family, reaching variants the canonical fold / token overlap keep
                 apart. MEDIUM confidence, higher REACH — it over-groups some same-domain edges. Score ~0.75
                 (single-sourced from ``edge_representations._REP_SCORE``).
  * EMBEDDING  — a DETERMINISTIC char-trigram hashed-vector cosine (``edge_representations.embedding`` + ``_cos``
                 at the ``_EMBED_COS_FLOOR``): an offline, reproducible SEMANTIC proxy (no model, no network). The
                 weakest/lowest-precision lane — a cross-check, not a verdict. Score ~0.45.

This makes the matcher the SINGLE source of ALL edge-compatibility methods
(exact | canonical | token | type | family | embedding) so composers pick the confidence↔reach they need.

Public API (all pure, deterministic, offline — no network/LLM/RNG/wall-clock in the matching path):
  build_producer_index(cards)                          -> a producer index (by exact / canonical / token / family)
  match(input_edge, index, *, limit=None)              -> ranked list of producer primitive_ids (exact first)
  match_hits(input_edge, index, *, limit=None)         -> the same, as hit dicts (tier, score, signature layer)
  producers(input_edge, index, *, method="type")       -> producer ids under ONE lane (exact|canonical|token|type|
                                                          family|embedding) — the single source of every method
  connectivity(input_edges, index, *, method="type")   -> fraction of inputs with >=1 producer (the lever metric)
  connectivity_report(cards)                           -> exact vs canonical vs token vs type (+ family/embedding
                                                          reach lanes), measured honestly

BOUNDARY LAW: this is a MATCHER — every hit is a CANDIDATE suggestion (candidate=true / serves_truth=false).
Matching two edges never promotes a primitive; a producer becomes served truth only through its own proofs+gates.

    PYTHONPATH=. python3 scripts/edge_type_matcher.py --self-test
    PYTHONPATH=. python3 scripts/edge_type_matcher.py --connectivity [--corpus 0]   # 0 = FULL corpus
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── self-bootstrap via the repo-paths sentinel (BEFORE any scripts.*/src.* import) ──
_here = Path(__file__).resolve()
_sbc = next((p for p in _here.parents if (p / "scripts" / "_repo_paths.py").exists()), _here.parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from collections import defaultdict  # noqa: E402
from typing import Any, Iterable, Optional  # noqa: E402

from scripts._jsonl import read_jsonl_tolerant  # noqa: E402  (mandated helper)
from scripts._repo_paths import resource as _resource  # noqa: E402
from scripts._time import now_iso  # noqa: E402  (mandated helper; report metadata only, never in the index)
from scripts.build_edge_type_retrofit import canonicalize_edge  # noqa: E402  THE normalizer — never reimplemented
from scripts import build_canonical_edge_type_vocabulary as _vocab  # noqa: E402  curated canonical type set
from scripts import primitive_onion  # noqa: E402  ~50-token signature layer per hit (vs ~750 for the full card)

#: every emitted row/record is a candidate signal, never truth (a matcher cannot promote).
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

#: curated canonical type ids (RawGraphInput, EdgeList, AdjacencyGraph, …) — single-sourced from the vocabulary
#: builder. A canonical match onto one of THESE is higher-confidence than onto an ad-hoc CamelCase fold.
_CURATED_TYPES: frozenset[str] = frozenset(_vocab._all_types().keys())

#: canonicalize_edge maps blank/unparseable edges to this catch-all; it is NOT a real type, so it must never
#: create a canonical match (else every un-typeable edge would falsely match every other one).
_UNTYPED_CANON: frozenset[str] = frozenset({"Unknown", ""})

# ── type-token extraction (the fuzzy lever) ──
#: structural/container words that carry no composable payload TYPE. A tokenizer tuning set (kept local +
#: documented, not a cross-module constant); mirrors the proxy noise set in bench_intelligent_composition so the
#: two token views agree on what "significant" means.
_NOISE_TOKENS: frozenset[str] = frozenset((
    "policy", "pack", "batch", "intent", "signal", "report", "data", "config", "context",
    "options", "the", "and", "for", "with",
))
_MIN_TOKEN_LEN = 4  # keep 4+-char words; shorter tokens (id, of, to, js) are too generic to type-match on.
_TOKEN_RE = re.compile(r"[a-z]{%d,}" % _MIN_TOKEN_LEN)
#: a TOKEN match needs the two edges' significant-token sets to overlap at least this much (Jaccard). 0.5 is
#: STRICTER than bench's "any shared token" proxy (which over-matches into a ~99% upper bound) yet still catches
#: type-variants (NormalizedRecordBatch↔NormalizedRecord share every significant token → 1.0).
TOKEN_JACCARD_FLOOR = 0.5

# ── match tiers: lower rank == stronger/more-trusted match; each tier carries a confidence score. ──
_TIER_EXACT, _TIER_CANONICAL, _TIER_TOKEN = 0, 1, 2
_TIER_NAMES: dict[int, str] = {_TIER_EXACT: "exact", _TIER_CANONICAL: "canonical", _TIER_TOKEN: "token"}
_SCORE_EXACT = 1.0
#: all canonical matches of one query fold to the SAME canonical id (curated or not, uniformly), so a
#: curated/ad-hoc score split could never reorder them within a query — one canonical score is honest.
#: Curated-ness is still surfaced as an informational flag on each hit for downstream confidence use.
_SCORE_CANONICAL = 0.9
#: the embedding lane scans ALL distinct output edges (no arbitrary cap) — tractable because their vectors are
#: precomputed ONCE per index (``_output_embeddings``) and the per-query scan is a cheap dot-product over the
#: stored matrix, not a re-embed per candidate. (Was a 4000-prefix cap that made everything alphabetically later
#: invisible to semantic match; the precompute removes both the blindspot and the reason for a cap.)
#: BENCHMARK-ONLY bound: the all-inputs embedding CONNECTIVITY SWEEP is O(inputs x outputs); ``connectivity_report``
#: ESTIMATES it over a deterministic, LOGGED input sample of this size (recorded as embedding_connectivity_sampled_
#: inputs). This is NOT a runtime cap — a single ``producers(method="embedding")`` query scans every output; only
#: the all-inputs measurement is sampled (per the "no silent caps — log what was dropped" law).
_EMBED_CONNECTIVITY_SAMPLE = 200
#: every compatibility lane the matcher offers — the FIRST four (exact/canonical/token/type) behave exactly as
#: before; family/embedding are ADDITIONAL higher-reach lanes REUSED from edge_representations (see the module
#: docstring). ``type`` remains the exact∪canonical∪token union and does NOT include family/embedding.
_METHODS: tuple[str, ...] = ("exact", "canonical", "token", "type", "family", "embedding")


def _type_tokens(edge: Any) -> frozenset[str]:
    """Significant TYPE tokens of an edge: split camelCase + compound ('+'/':' delimiters), keep 4+-char words,
    drop noise. 'VideoArtifact+ClipRangePolicy' -> {video, artifact, clip, range}."""
    spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", str(edge)).replace("+", " ").replace(":", " ")
    return frozenset(t for t in _TOKEN_RE.findall(spaced.lower()) if t not in _NOISE_TOKENS)


def _canon(edge: Any) -> Optional[str]:
    """Fold an edge onto the shared canonical namespace, or None when no REAL type can be produced (blank /
    unparseable / the 'Unknown' catch-all). Wraps the single-source canonicalize_edge; never reimplements it."""
    if not isinstance(edge, str) or not edge.strip():
        return None
    c = canonicalize_edge(edge)
    if not isinstance(c, str) or c in _UNTYPED_CANON:
        return None
    return c


def _fold_family(edge: Any, family_index: dict[str, str]) -> str:
    """Fold ``edge`` onto its FAMILY (dominant recurring type token) using the SAME ``family_index`` the producers
    were bucketed under — so a query INPUT edge and the producer OUTPUT edges it should reach share ONE family
    namespace. A corpus edge is a direct O(1) lookup; a NOVEL edge (never seen at index-build time) is folded ONCE
    into the index's own edge universe (``family_index.keys()``) via the reused ``build_family_index``, so an
    arbitrary query still resolves consistently. Reuses ``edge_representations``; never reimplements the fold."""
    e = str(edge or "").strip()
    if not e:
        return ""
    if e in family_index:
        return family_index[e]
    from scripts import edge_representations as _edge_representations  # noqa: PLC0415  lazy: sidestep the cycle
    return _edge_representations.build_family_index([*family_index.keys(), e]).get(e, "")


def _readiness_rank(readiness: Any) -> int:
    """Map a readiness label ('R3_contract_known') to its stage number (3); unknown -> 0. Higher == more ready."""
    m = re.match(r"[Rr](\d+)", str(readiness or ""))
    return int(m.group(1)) if m else 0


def _rank_key(pid: str, meta_by_id: dict[str, dict]) -> tuple[float, int, str]:
    """Stable producer ordering: highest quality first, then most-ready, then id (deterministic tiebreak). This is
    the WITHIN-bucket order stored in the index so the best producer is first."""
    m = meta_by_id.get(pid, {})
    return (-float(m.get("quality", 0) or 0), -int(m.get("readiness_rank", 0) or 0), str(pid))


def build_producer_index(cards: Iterable[dict]) -> dict[str, Any]:
    """Index a corpus by what each primitive PRODUCES, keyed four ways so match() answers in O(candidates):
    by raw ``output_edge`` (exact), by canonical type id (canonicalize_edge fold), by significant type token, and
    by dominant-type FAMILY (``edge_representations.build_family_index`` over the corpus's inputs+outputs). The
    family index of every corpus edge is stored so ``producers()`` can fold a query input edge the SAME way.

    Generalizes ``check_primitive_composability.build_type_index`` from boolean produces:/consumes: facts to
    producer-id LISTS. Every id list is sorted deterministically (quality desc, readiness desc, id) so the best
    producer is first and two builds are byte-identical. A card with no ``primitive_id`` or no ``output_edge`` is
    skipped; a duplicate id keeps the first (stable). No timestamp/RNG here — the index is pure over the cards."""
    by_exact: dict[str, list[str]] = defaultdict(list)
    by_canon: dict[str, list[str]] = defaultdict(list)
    by_token: dict[str, list[str]] = defaultdict(list)
    meta_by_id: dict[str, dict[str, Any]] = {}
    card_by_id: dict[str, dict] = {}
    #: the FAMILY universe — every distinct input AND output edge in the corpus. build_family_index folds each
    #: onto a dominant-type family; collecting BOTH sides (not just outputs) lets producers() fold a query INPUT
    #: edge into the SAME family namespace as the producer OUTPUT edges (mirrors edge_representations.connectivity,
    #: which also builds its family index over inputs+outputs). build_family_index de-dups edge strings, so
    #: collecting from every card — including dup-pid / output-less ones — is safe and deterministic.
    family_universe: list[str] = []

    for card in cards:
        pid = card.get("primitive_id")
        inp = card.get("input_edge")
        inp = inp.strip() if isinstance(inp, str) else ""
        out = card.get("output_edge")
        out = out.strip() if isinstance(out, str) else ""
        if inp:
            family_universe.append(inp)
        if out:
            family_universe.append(out)
        if not pid or pid in meta_by_id:
            continue
        if not out:
            continue
        canon = _canon(out)
        tokens = sorted(_type_tokens(out))
        meta_by_id[pid] = {
            "output_edge": out,
            "canonical": canon,
            "tokens": tokens,
            "quality": float(card.get("quality_score") or 0),
            "readiness_rank": _readiness_rank(card.get("readiness")),
        }
        card_by_id[pid] = card
        by_exact[out].append(pid)
        if canon is not None:
            by_canon[canon].append(pid)
        for t in tokens:
            by_token[t].append(pid)

    # FAMILY lane (REUSED from edge_representations — never reimplemented): fold every corpus edge onto its
    # dominant-type family, then bucket producers by the family of their OUTPUT edge. Lazy import to sidestep the
    # module cycle (edge_representations lazily imports THIS module's canonicalize_edge). build_family_index only
    # reads type_tokens (no canonicalize call), so this never re-enters edge_type_matcher.
    from scripts import edge_representations as _edge_representations  # noqa: PLC0415  lazy: sidestep the cycle
    family_index = _edge_representations.build_family_index(family_universe)
    by_family: dict[str, list[str]] = defaultdict(list)
    for pid, meta in meta_by_id.items():
        fam = _edge_representations.family(meta["output_edge"], family_index)
        meta["family"] = fam                       # surface each producer's family for downstream confidence use
        if fam:
            by_family[fam].append(pid)

    def _ranked(d: dict[str, list[str]]) -> dict[str, list[str]]:
        return {k: sorted(v, key=lambda pid: _rank_key(pid, meta_by_id)) for k, v in sorted(d.items())}

    return {
        "record_type": "edge_type_producer_index",
        "producers_by_exact": _ranked(by_exact),
        "producers_by_canonical": _ranked(by_canon),
        "producers_by_token": _ranked(by_token),
        "producers_by_family": _ranked(by_family),
        # the family fold of EVERY corpus edge (inputs+outputs), stored so producers() can fold a query the SAME
        # way; sorted so the stored key order is fully deterministic regardless of card iteration order.
        "family_index": dict(sorted(family_index.items())),
        "meta_by_id": dict(sorted(meta_by_id.items())),
        "card_by_id": card_by_id,
        "card_count": len(card_by_id),
        "distinct_output_edges": len(by_exact),
        "distinct_canonical_types": len(by_canon),
        "distinct_families": len(by_family),
        "curated_type_count": len(_CURATED_TYPES),
        **BOUNDARY,
    }


def _output_embeddings(index: dict[str, Any]) -> dict[str, tuple]:
    """Embeddings of EVERY distinct output edge, computed ONCE and cached on the index. This is what lets the
    embedding lane be UNCAPPED: the per-query scan becomes a cheap cosine over these stored vectors instead of
    re-embedding every candidate on every query (the old cost that forced a 4000-prefix cap). Reuses
    ``edge_representations.embedding`` wholesale — deterministic, offline, no model/network. Non-embedding
    callers never trigger it (lazy), so they pay nothing."""
    cache = index.get("_output_embeddings_cache")
    if cache is None:
        from scripts import edge_representations as _edge_representations  # noqa: PLC0415  lazy: sidestep cycle
        cache = {out: _edge_representations.embedding(out) for out in index["producers_by_exact"]}
        index["_output_embeddings_cache"] = cache
    return cache


def _match_map(input_edge: Any, index: dict[str, Any]) -> dict[str, tuple[int, float]]:
    """Best (tier, score) per candidate producer whose output is TYPE-COMPATIBLE with ``input_edge`` — the union
    of the three levers, strongest tier per producer kept."""
    best: dict[str, tuple[int, float]] = {}

    def _offer(pid: str, tier: int, score: float) -> None:
        cur = best.get(pid)
        if cur is None or (tier, -score) < (cur[0], -cur[1]):
            best[pid] = (tier, score)

    # tier 0 — exact raw-string equality
    for pid in index["producers_by_exact"].get(str(input_edge or "").strip(), []):
        _offer(pid, _TIER_EXACT, _SCORE_EXACT)

    # tier 1 — canonical type equality (fold both edges onto the shared namespace)
    canon = _canon(input_edge)
    if canon is not None:
        for pid in index["producers_by_canonical"].get(canon, []):
            _offer(pid, _TIER_CANONICAL, _SCORE_CANONICAL)

    # tier 2 — significant type-token overlap above the Jaccard floor
    in_tokens = _type_tokens(input_edge)
    if in_tokens:
        meta = index["meta_by_id"]
        tok_index = index["producers_by_token"]
        candidates: set[str] = set()
        for t in in_tokens:
            candidates.update(tok_index.get(t, []))
        for pid in candidates:
            ptoks = set(meta.get(pid, {}).get("tokens", []))
            if not ptoks:
                continue
            jac = len(in_tokens & ptoks) / len(in_tokens | ptoks)
            if jac >= TOKEN_JACCARD_FLOOR:
                _offer(pid, _TIER_TOKEN, round(jac, 6))
    return best


def match_hits(input_edge: Any, index: dict[str, Any], *, limit: Optional[int] = None) -> list[dict[str, Any]]:
    """Ranked candidate producers for ``input_edge`` as hit dicts. Ranking: exact before canonical before token,
    then higher score, then higher producer quality/readiness, then id (deterministic). Each hit carries the
    producer's ~signature layer (primitive_onion.signature — id+title+edges, ~50 tokens) not the whole card, and
    is stamped candidate/serves_truth=false (a suggestion, never a promotion)."""
    best = _match_map(input_edge, index)
    meta = index["meta_by_id"]
    cards = index["card_by_id"]
    ranked = sorted(
        best.items(),
        key=lambda kv: (
            kv[1][0],                                              # tier (exact<canonical<token)
            -kv[1][1],                                             # score desc
            -float(meta.get(kv[0], {}).get("quality", 0) or 0),   # producer quality desc
            -int(meta.get(kv[0], {}).get("readiness_rank", 0) or 0),
            str(kv[0]),                                            # id — final deterministic tiebreak
        ),
    )
    in_canon = _canon(input_edge)
    hits = [{
        "record_type": "edge_type_match_hit",
        "primitive_id": pid,
        "matched_via": _TIER_NAMES[tier],
        "match_tier": tier,
        "score": score,
        "input_edge": input_edge,
        "input_canonical_type": in_canon,
        "producer_output_edge": meta.get(pid, {}).get("output_edge"),
        "producer_canonical_type": meta.get(pid, {}).get("canonical"),
        # informational confidence signal (a fold onto a CURATED vocabulary type is more trustworthy); not a
        # ranking input — see _SCORE_CANONICAL. Lets a downstream consumer weight hits without re-deriving it.
        "producer_canonical_is_curated": meta.get(pid, {}).get("canonical") in _CURATED_TYPES,
        "signature": primitive_onion.signature(cards.get(pid, {})),
        **BOUNDARY,
    } for pid, (tier, score) in ranked]
    return hits[:limit] if limit is not None else hits


def match(input_edge: Any, index: dict[str, Any], *, limit: Optional[int] = None) -> list[str]:
    """THE matcher: a ranked list of producer primitive_ids whose ``output_edge`` is TYPE-COMPATIBLE with
    ``input_edge`` (exact first, then canonical, then token). Candidate suggestions only — never a truth claim."""
    return [h["primitive_id"] for h in match_hits(input_edge, index, limit=limit)]


def producers(input_edge: Any, index: dict[str, Any], *, method: str = "type") -> list[str]:
    """Producer ids that satisfy ``input_edge`` under ONE matcher lane — the portfolio the benchmarks race:
    'exact' (raw equality, today's floor), 'canonical' (vocabulary fold), 'token' (type-token overlap), 'type'
    (all three combined = match()), and the two ADDITIONAL higher-reach lanes REUSED from edge_representations:
    'family' (fold onto the dominant-type family — medium confidence, folds surface variants) and 'embedding'
    (deterministic char-trigram cosine >= the floor — a semantic proxy, lowest precision). family/embedding are
    NOT part of the 'type' union. Deterministically ordered (best producer first)."""
    if method == "type":
        return match(input_edge, index)
    ids: list[str]
    if method == "exact":
        ids = list(index["producers_by_exact"].get(str(input_edge or "").strip(), []))
    elif method == "canonical":
        canon = _canon(input_edge)
        ids = list(index["producers_by_canonical"].get(canon, [])) if canon is not None else []
    elif method == "token":
        in_tokens = _type_tokens(input_edge)
        meta = index["meta_by_id"]
        candidates: set[str] = set()
        for t in in_tokens:
            candidates.update(index["producers_by_token"].get(t, []))
        ids = [pid for pid in candidates
               if (pt := set(meta.get(pid, {}).get("tokens", [])))
               and len(in_tokens & pt) / len(in_tokens | pt) >= TOKEN_JACCARD_FLOOR]
    elif method == "family":
        # fold the query edge onto its family the SAME way the producers were bucketed (edge_representations),
        # then return every producer whose OUTPUT-edge family matches. Higher REACH: surface variants collapse.
        q_family = _fold_family(input_edge, index["family_index"])
        ids = list(index["producers_by_family"].get(q_family, [])) if q_family else []
    elif method == "embedding":
        # deterministic SEMANTIC proxy: producers whose output-edge embedding cosine to the query clears the
        # floor. Scans ALL distinct output edges (no cap) against vectors precomputed ONCE per index
        # (_output_embeddings) — reuses edge_representations' embedding + cosine wholesale; no model, no
        # network, reproducible.
        q = str(input_edge or "").strip()
        if not q:
            ids = []
        else:
            from scripts import edge_representations as _edge_representations  # noqa: PLC0415  lazy: cycle
            q_emb = _edge_representations.embedding(q)
            floor = _edge_representations._EMBED_COS_FLOOR
            by_exact = index["producers_by_exact"]
            ids = []
            for out, out_emb in _output_embeddings(index).items():
                if _edge_representations._cos(q_emb, out_emb) >= floor:
                    ids.extend(by_exact[out])
    else:
        raise ValueError(f"unknown method {method!r}; methods are {_METHODS}")
    meta = index["meta_by_id"]
    seen: set[str] = set()
    uniq = [p for p in ids if not (p in seen or seen.add(p))]
    return sorted(uniq, key=lambda pid: _rank_key(pid, meta))


def connectivity(input_edges: Iterable[Any], index: dict[str, Any], *, method: str = "type") -> float:
    """Fraction of ``input_edges`` for which SOME producer exists under ``method`` — the direct connectivity
    lever (bench's input_satisfiability). connectivity('type') >> connectivity('exact') is the whole thesis."""
    inputs = list(input_edges)
    if not inputs:
        return 0.0
    hit = sum(1 for e in inputs if producers(e, index, method=method))
    return round(hit / len(inputs), 6)


CORPUS = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"


def connectivity_report(cards: list[dict]) -> dict[str, Any]:
    """Measure exact vs canonical vs token vs type connectivity over a real corpus — the honest floor↔ceiling
    the proxy benchmark could not report (it used token overlap for the whole 'type' number). ALSO reports the
    two ADDITIONAL higher-reach lanes (family, embedding) so the whole exact < canonical < token < family/
    embedding picture is one call — but those two are separate reach lanes, NOT part of the 'type' union."""
    idx = build_producer_index(cards)
    inputs = sorted({str(c.get("input_edge") or "").strip()
                     for c in cards if str(c.get("input_edge") or "").strip()})
    c_exact = connectivity(inputs, idx, method="exact")
    c_canon = connectivity(inputs, idx, method="canonical")
    c_token = connectivity(inputs, idx, method="token")
    c_type = connectivity(inputs, idx, method="type")
    # ADDITIONAL higher-REACH / lower-PRECISION lanes — measured on the same inputs, reported alongside but NOT
    # folded into the 'type' union above (so 'type' stays exact∪canonical∪token, unchanged).
    c_family = connectivity(inputs, idx, method="family")
    # embedding connectivity is O(inputs x outputs) to SWEEP; estimate over a deterministic (strided), LOGGED
    # input sample so the report stays fast. Runtime queries scan every output uncapped — only this all-inputs
    # measurement is sampled (single-source _EMBED_CONNECTIVITY_SAMPLE; sample size recorded below).
    if len(inputs) > _EMBED_CONNECTIVITY_SAMPLE:
        _stride = len(inputs) // _EMBED_CONNECTIVITY_SAMPLE
        embed_inputs = inputs[::_stride][:_EMBED_CONNECTIVITY_SAMPLE]
    else:
        embed_inputs = inputs
    c_embedding = connectivity(embed_inputs, idx, method="embedding")
    from scripts import edge_representations as _edge_representations  # noqa: PLC0415  lazy: single-source scores
    return {
        "record_type": "edge_type_matcher_connectivity",
        "generated_at": now_iso(),
        "cards_indexed": idx["card_count"],
        "distinct_inputs": len(inputs),
        "distinct_output_edges": idx["distinct_output_edges"],
        # the embedding lane scans ALL distinct outputs per query (uncapped); the all-inputs SWEEP was estimated
        # over this many inputs (== distinct_inputs when <= _EMBED_CONNECTIVITY_SAMPLE) — logged, never silent.
        "embedding_connectivity_sampled_inputs": len(embed_inputs),
        "connectivity_exact": c_exact,
        "connectivity_canonical": c_canon,
        "connectivity_token": c_token,
        "connectivity_type": c_type,
        "connectivity_family": c_family,
        "connectivity_embedding": c_embedding,
        # labelled confidence per lane, single-sourced (no magic literals): exact/canonical from the local tier
        # scores, family/embedding from edge_representations._REP_SCORE — so the confidence↔reach tradeoff is READ.
        "method_confidence": {"exact": _SCORE_EXACT, "canonical": _SCORE_CANONICAL,
                              "family": _edge_representations._REP_SCORE["family"],
                              "embedding": _edge_representations._REP_SCORE["embedding"]},
        "lift_type_over_exact": round(c_type / c_exact, 2) if c_exact else None,
        # What fraction of the combined type connectivity the fuzzy TOKEN tier alone accounts for — COMPUTED
        # from the measured tiers (never hand-typed), so the disclosure that the lift is token-dominated is
        # data-driven. type is the UNION of the tiers, so this is in [0, 1] (typically the large majority).
        "token_share_of_type": round(c_token / c_type, 3) if c_type else None,
        "note": ("exact = raw-string equality (today's ~10% baseline); type = canonical-vocabulary fold "
                 "(canonicalize_edge) + significant type-token overlap. The combined 'type' number is "
                 "DOMINATED by the fuzzy token tier (see token_share_of_type) — the weakest-confidence lever "
                 "— so read it as CANDIDATE type-compatibility, not verified type-equality; the canonical "
                 "fold alone (connectivity_canonical) is the higher-trust subset. Measured here, not "
                 "asserted. This is a candidate signal (serves_truth=false)."),
        "reach_note": ("connectivity_family and connectivity_embedding are ADDITIONAL, higher-REACH / "
                       "lower-PRECISION candidate lanes — NOT part of the 'type' union (which stays "
                       "exact∪canonical∪token). family folds surface variants onto a dominant-type family "
                       "(MEDIUM confidence — it over-groups some same-domain edges); embedding is a "
                       "DETERMINISTIC char-trigram semantic proxy (the weakest lane, a cross-check). A composer "
                       "picks the lane by the confidence/reach it needs (see method_confidence); both stay "
                       "candidate signals (serves_truth=false)."),
        **BOUNDARY,
    }


def _load_cards(limit: int) -> list[dict]:
    if not CORPUS.exists():
        return []
    cards = [c for c in read_jsonl_tolerant(CORPUS) if c.get("primitive_id")]
    return cards[:limit] if limit and limit < len(cards) else cards


def _run_connectivity(corpus: int) -> int:
    cards = _load_cards(corpus)
    if not cards:
        print(f"no corpus cards at {CORPUS} (factory scratch may be gitignored on this checkout)")
        return 1
    report = connectivity_report(cards)
    print(json.dumps({k: report[k] for k in (
        "cards_indexed", "distinct_inputs", "connectivity_exact", "connectivity_canonical",
        "connectivity_token", "connectivity_type", "connectivity_family", "connectivity_embedding",
        "token_share_of_type", "lift_type_over_exact", "method_confidence")}, indent=2))
    print(f"\n  {report['note']}")
    print(f"\n  {report['reach_note']}")
    return 0


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []

    def card(pid: str, inp: str, out: str, *, quality: int = 50, readiness: str = "R2_edge_known") -> dict:
        return {"primitive_id": pid, "input_edge": inp, "output_edge": out,
                "title": f"{inp} -> {out}", "kind": "route.primitive",
                "quality_score": quality, "readiness": readiness, "candidate": True, "serves_truth": False}

    # Synthetic corpus. p:exact_adj produces AdjacencyGraph exactly; p:variant_rec produces NormalizedRecord (a
    # token-variant of NormalizedRecordBatch); two EdgeList producers of differing quality test within-tier rank;
    # p:exact_ab (low quality) vs p:tok_ab (HIGH quality, token-only) makes tier outrank quality; p:graph_cap
    # matches 'graph' by BOTH canonical and token so the stronger (canonical) tier must be the one recorded.
    cards = [
        card("p:exact_adj", "RawGraphInput", "AdjacencyGraph"),
        card("p:variant_rec", "ParsedDoc", "NormalizedRecord"),
        card("p:report", "SchemeMap", "AuthValidationReport"),
        # same readiness + an id ordering that would REVERSE the desired result, so ONLY quality can rank
        # p:edge_zz_hi first — isolates the quality sort key (id 'aa' < 'zz' would otherwise win the tiebreak).
        card("p:edge_zz_hi", "RawGraphInput", "EdgeList", quality=90, readiness="R2_edge_known"),
        card("p:edge_aa_lo", "RawGraphInput", "EdgeList", quality=40, readiness="R2_edge_known"),
        card("p:exact_ab", "Seed", "AlphaBeta", quality=10),
        card("p:tok_ab", "Seed", "BetaAlpha", quality=95),
        card("p:graph_cap", "Seed", "Graph", quality=60),
    ]
    idx = build_producer_index(cards)

    # 1) EXACT match is found and ranks first — and tier BEATS quality: a perfect-overlap token match with far
    #    higher quality still ranks BELOW the exact match. (Guards against tier being dropped from the ranking.)
    m_adj = match("AdjacencyGraph", idx)
    checks.append(("exact match is found and ranks first", bool(m_adj) and m_adj[0] == "p:exact_adj"))
    m_ab = match("AlphaBeta", idx)
    checks.append(("exact ranks above a higher-quality token match (tier outranks quality)",
                   bool(m_ab) and m_ab[0] == "p:exact_ab" and "p:tok_ab" in m_ab))

    # within a tier, the higher-quality producer ranks first (both EdgeList producers are exact matches).
    m_edge = match("EdgeList", idx)
    checks.append(("within-tier ranking prefers the higher-quality producer",
                   m_edge[:2] == ["p:edge_zz_hi", "p:edge_aa_lo"]))

    # canonical BEATS token per producer: p:graph_cap matches 'graph' by canonical (tier1) AND token (tier2);
    # it must be recorded as the STRONGER canonical tier. (Guards against the tier tie-break being inverted.)
    g_hits = {h["primitive_id"]: h["matched_via"] for h in match_hits("graph", idx)}
    checks.append(("canonical outranks token for a producer that matches both",
                   g_hits.get("p:graph_cap") == "canonical"))

    # 2) TYPE-VARIANT matches under TYPE but NOT exact — and NOT via canonical equality either (the ids differ),
    #    proving it is the TOKEN-overlap lever that closes the ~10%→~99% gap.
    checks.append(("type-variant 'NormalizedRecordBatch' has NO exact producer",
                   producers("NormalizedRecordBatch", idx, method="exact") == []))
    checks.append(("type-variant is NOT a canonical-equality match (canon ids differ)",
                   producers("NormalizedRecordBatch", idx, method="canonical") == []))
    checks.append(("type-variant DOES match under type (token overlap) -> the NormalizedRecord producer",
                   "p:variant_rec" in match("NormalizedRecordBatch", idx)))

    # canonicalize_edge folds a synonym onto the curated namespace: 'graph' -> AdjacencyGraph (canonical, not exact).
    checks.append(("synonym 'graph' canonical-matches the AdjacencyGraph producer (vocab fold), not exact",
                   "p:exact_adj" in producers("graph", idx, method="canonical")
                   and producers("graph", idx, method="exact") == []))

    # 3) an UNRELATED edge matches nothing under any lever.
    checks.append(("unrelated edge 'QuantumFluxCapacitor' matches nothing",
                   match("QuantumFluxCapacitor", idx) == []
                   and producers("QuantumFluxCapacitor", idx, method="token") == []))

    # a PARTIAL token overlap BELOW the Jaccard floor must NOT match — 'AlphaGamma' shares only {alpha} with the
    # 'AlphaBeta' producers (Jaccard 1/3 < 0.5). Guards the floor: dropping it to 0 would over-match this.
    checks.append(("sub-floor token overlap does not match (guards the Jaccard floor against over-matching)",
                   match("AlphaGamma", idx) == [] and producers("AlphaGamma", idx, method="token") == []))

    # 4) CONNECTIVITY(type) > CONNECTIVITY(exact) on the synthetic corpus (the headline lever).
    probe = ["AdjacencyGraph", "graph", "NormalizedRecordBatch", "QuantumFluxCapacitor"]
    c_exact = connectivity(probe, idx, method="exact")
    c_type = connectivity(probe, idx, method="type")
    checks.append((f"connectivity(type)={c_type} > connectivity(exact)={c_exact}", c_type > c_exact))

    # 5) hits are candidate suggestions only, and read as a compact signature layer (not the whole card).
    #    Collection stays CRASH-SAFE: a mutation that makes the matcher return nothing (e.g. _match_map -> {})
    #    yields empty hit lists, so every check below must degrade to a clean FAIL (via .get()/bool guards)
    #    rather than an IndexError that aborts collection before any [ok]/[FAIL] diagnostic is printed.
    hits = match_hits("AdjacencyGraph", idx)
    checks.append(("match_hits returns a non-empty ranked hit for an exact-match query "
                   "(a silently-empty matcher is caught here, not by a crash)", bool(hits)))
    top = hits[0] if hits else {}
    checks.append(("match hits are candidate/serves_truth=false (a matcher never promotes)",
                   bool(hits) and all(h["serves_truth"] is False and h["candidate"] is True for h in hits)))
    checks.append(("each hit carries the ~signature layer (id+title+edges), not the whole card",
                   "primitive_id" in top.get("signature", {})
                   and set(top.get("signature", {})) <= {"primitive_id", "title", "input_edge", "output_edge"}))
    checks.append(("hit records the tier it matched on", top.get("matched_via") == "exact"))
    adj_hits = match_hits("AdjacencyGraph", idx)
    ab_hits = match_hits("AlphaBeta", idx)
    checks.append(("hit surfaces curated-ness of the producer's canonical type (AdjacencyGraph curated, AlphaBeta not)",
                   bool(adj_hits) and adj_hits[0].get("producer_canonical_is_curated") is True
                   and bool(ab_hits) and ab_hits[0].get("producer_canonical_is_curated") is False))

    # 6) DETERMINISM gate: build twice -> byte-identical index; match twice -> identical.
    idx2 = build_producer_index(cards)
    checks.append(("build_producer_index is deterministic (byte-identical)",
                   json.dumps(idx, sort_keys=True, default=str) == json.dumps(idx2, sort_keys=True, default=str)))
    checks.append(("match is deterministic", match("EdgeList", idx) == match("EdgeList", idx2)))

    # a duplicate primitive_id keeps the FIRST card (stable dedup) so the index is well-defined + deterministic.
    dup_idx = build_producer_index([card("p:dup", "In", "FirstWinsOutput"),
                                    card("p:dup", "In", "SecondIgnoredOutput")])
    checks.append(("duplicate primitive_id keeps the first card (stable dedup)",
                   dup_idx["card_count"] == 1
                   and dup_idx["meta_by_id"]["p:dup"]["output_edge"] == "FirstWinsOutput"))

    # 7) MUTATION gate: corrupt the exact producer's output_edge -> its hit MUST disappear (test is not vacuous).
    mutated = [dict(c) for c in cards]
    for c in mutated:
        if c["primitive_id"] == "p:exact_adj":
            c["output_edge"] = "ZzzGarbageUnrelatedOutputEdge"
    idx_mut = build_producer_index(mutated)
    checks.append(("mutation: corrupting the producer's output_edge removes it from the AdjacencyGraph match",
                   "p:exact_adj" in match("AdjacencyGraph", idx)
                   and "p:exact_adj" not in match("AdjacencyGraph", idx_mut)))

    # 8) namespace reuse: the matcher folds onto the CURATED canonical-edge-type vocabulary.
    checks.append(("reuses the curated canonical vocabulary (EdgeList/AdjacencyGraph are curated types)",
                   "EdgeList" in _CURATED_TYPES and "AdjacencyGraph" in _CURATED_TYPES
                   and idx["curated_type_count"] == len(_CURATED_TYPES)))

    # 9) DISCLOSURE gate: connectivity_report breaks the tiers out honestly so the single 'type' number is
    #    never over-read. type is the UNION of exact/canonical/token, so EVERY tier's connectivity <= type
    #    (a real invariant a mis-wired report would violate), and token_share_of_type is the COMPUTED
    #    token/type fraction (never hand-typed) that quantifies the token-tier domination.
    rep = connectivity_report(cards)
    tiers_bounded = (rep["connectivity_exact"] <= rep["connectivity_type"]
                     and rep["connectivity_canonical"] <= rep["connectivity_type"]
                     and rep["connectivity_token"] <= rep["connectivity_type"])
    share_ok = (rep["token_share_of_type"] is None if not rep["connectivity_type"]
                else rep["token_share_of_type"] == round(rep["connectivity_token"] / rep["connectivity_type"], 3))
    checks.append(("connectivity_report bounds every tier by the type union AND emits a computed token_share_of_type",
                   tiers_bounded and share_ok))
    checks.append(("connectivity_report is a candidate signal (serves_truth=false)",
                   rep["serves_truth"] is False and rep["candidate"] is True))

    # 10) ADDITIONAL LANES (REUSED wholesale from edge_representations): FAMILY (medium-confidence surface-variant
    #     fold) and EMBEDDING (deterministic semantic proxy). A DEDICATED synthetic corpus sized so the family-token
    #     df lands inside build_family_index's [MIN_DF=3, 0.20*n] window: 3 producers sharing a 'normalized' family,
    #     2 surface-variant consumers, and enough padding (~42 distinct edges) that df['normalized']=5 <= hi=8.
    from scripts import edge_representations as _er  # noqa: PLC0415  single-source the labelled lane scores below
    fam_producers = [card("q:norm_rec", "Aardvark", "NormalizedRecord"),
                     card("q:norm_opp", "Barnacle", "NormalizedOpportunity"),
                     card("q:norm_feed", "Cephalopod", "NormalizedFeed")]
    fam_consumers = [card("q:cons_batch", "NormalizedRecordBatch", "TerminalOutputA"),
                     card("q:cons_prof", "NormalizedProfile", "TerminalOutputB")]
    fam_pad = [card(f"q:pad{i}", f"PadAlpha{i}", f"PadBeta{i}") for i in range(16)]
    fam_cards = fam_producers + fam_consumers + fam_pad
    fam_idx = build_producer_index(fam_cards)
    fam_inputs = sorted({c["input_edge"] for c in fam_cards})

    # (a) family connectivity >= canonical connectivity on this corpus (folding surface variants never LOWERS reach).
    cf_family = connectivity(fam_inputs, fam_idx, method="family")
    cf_canon = connectivity(fam_inputs, fam_idx, method="canonical")
    checks.append((f"family connectivity ({cf_family}) >= canonical connectivity ({cf_canon}) and is nonzero",
                   cf_family >= cf_canon and cf_family > 0))

    # (b) a SURFACE-VARIANT input that fails BOTH exact and canonical composes under FAMILY (folds to 'normalized').
    checks.append(("surface variant 'NormalizedRecordBatch' fails exact+canonical but composes under family",
                   producers("NormalizedRecordBatch", fam_idx, method="exact") == []
                   and producers("NormalizedRecordBatch", fam_idx, method="canonical") == []
                   and "q:norm_rec" in producers("NormalizedRecordBatch", fam_idx, method="family")))

    # a NOVEL edge (never in the corpus) still folds — exercises the on-the-fly family fallback (reused build_family_index).
    checks.append(("a novel edge folds to its family via the reused build_family_index fallback",
                   producers("NormalizedGizmo", fam_idx, method="family") != []))

    # (c) the EMBEDDING lane is DETERMINISTIC (same query -> identical producer ids) and finds the identical-output producer.
    emb1 = producers("NormalizedRecord", fam_idx, method="embedding")
    emb2 = producers("NormalizedRecord", fam_idx, method="embedding")
    checks.append(("embedding lane is deterministic and finds the same-output producer",
                   emb1 == emb2 and "q:norm_rec" in emb1))

    # (d) MUTATION gate for the NEW lanes — the tests are NOT vacuous: dissolving the shared family (corrupt the
    #     producers' outputs) removes the family match; corrupting one producer's output removes it from embedding.
    fam_break = [dict(c) for c in fam_cards]
    for c in fam_break:
        if c["primitive_id"] in {"q:norm_rec", "q:norm_opp", "q:norm_feed"}:
            c["output_edge"] = "ZzqxWobbleGadget" + c["primitive_id"]     # dissolve the 'normalized' family fold
    fam_break_idx = build_producer_index(fam_break)
    checks.append(("mutation: dissolving the family fold removes the family match (family lane is not vacuous)",
                   producers("NormalizedRecordBatch", fam_idx, method="family") != []
                   and producers("NormalizedRecordBatch", fam_break_idx, method="family") == []))
    emb_break = [dict(c) for c in fam_cards]
    for c in emb_break:
        if c["primitive_id"] == "q:norm_rec":
            c["output_edge"] = "ZzqxWobbleUnrelatedBlob"
    emb_break_idx = build_producer_index(emb_break)
    checks.append(("mutation: corrupting a producer's output removes it from the embedding match (embedding lane not vacuous)",
                   "q:norm_rec" in producers("NormalizedRecord", fam_idx, method="embedding")
                   and "q:norm_rec" not in producers("NormalizedRecord", emb_break_idx, method="embedding")))

    # (e) the lanes are REGISTERED, and connectivity_report surfaces both with single-sourced confidence labels.
    checks.append(("family + embedding are registered matcher methods (single source of ALL lanes)",
                   "family" in _METHODS and "embedding" in _METHODS))
    rep_fam = connectivity_report(fam_cards)
    checks.append(("connectivity_report reports the family + embedding reach lanes with single-sourced confidences",
                   "connectivity_family" in rep_fam and "connectivity_embedding" in rep_fam
                   and rep_fam["method_confidence"]["family"] == _er._REP_SCORE["family"]
                   and rep_fam["method_confidence"]["embedding"] == _er._REP_SCORE["embedding"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - edge_type_matcher: EXACT edge matching connects little; TYPE-aware matching "
          f"(canonicalize_edge fold onto the curated vocabulary + significant type-token overlap) connects far "
          f"more (synthetic connectivity {c_exact} -> {c_type}). match() returns ranked CANDIDATE producer ids "
          f"(exact first), reads each as a signature layer, and never promotes (serves_truth=false).")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--connectivity", action="store_true", help="measure exact vs type connectivity on the corpus")
    ap.add_argument("--corpus", type=int, default=0,
                    help="cap on cards loaded for --connectivity (0 = FULL corpus, the default; matches "
                         "edge_representations/primitive_orchestration)")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.connectivity:
        return _run_connectivity(args.corpus)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
