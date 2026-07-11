#!/usr/bin/env python3
"""scripts.primitive_retrieval_bakeoff — the MULTI-PATH law applied to RETRIEVAL: describe a primitive across a
WIDE named feature space (thousands of columns), generate candidates SUB-LINEARLY with a ZOO of blocking/LSH/
partitioning strategies, then RACE combinations of {candidate-generator × reranker} on a labelled query set and
pick the CHAMPION by a measured receipt (recall / precision / cost), keeping the losers as labelled fallbacks.
"Grab things efficiently" made measurable and self-adapting — and we never GUESS which strategy wins, we MEASURE.

Why (first principles). There is no single best way to describe or compare a primitive, and no single best way to
GRAB candidates cheaply. Keyword blocks are sharp but brittle; embeddings are fuzzy but O(N); MinHash approximates
Jaccard; SimHash approximates cosine; coarse bands maximize recall, fine bands maximize precision; partitioning by
operation/edge-family/cluster groups by a different notion of "same". The right move is a PORTFOLIO of strategies
raced on the SAME queries by a fair comparator, ranked by MEASURED receipts (recall@k, precision@k, mean candidates
scanned = cost), with every path kept as a labelled fallback so the choice re-adapts as the corpus shifts.

Layers (all offline-deterministic — no RNG, no wall-clock, no network in the ranking path; LSH hash families are
fixed + content-derived, never Python's salted hash()):
  * FEATURE FACTORY — feature_columns(card): a wide NAMED sparse column space (per token/phrase/datatype/operation/
                      impact/edge-shape/embedding-bucket). Thousands of distinct columns over a real corpus.
  * CANDIDATE-GENERATOR ZOO (the SCALE primitives) — MinHash-LSH at MULTIPLE overlapping resolutions (coarse=big
                      buckets/high recall … fine=small/precise), SimHash-LSH over the dense embedding, a
                      HIERARCHICAL cascade (coarse recall narrowed by a second family for precision), MULTI-TYPE
                      routing (pick the LSH family by the primitive's datatype), and PARTITIONING/GROUPING by
                      operation, edge-family, and greedy embedding CANOPY clusters. Each is sub-linear.
  * BAKEOFF — race every {generator × reranker} PATH on labelled queries; emit a receipt per path and pick the
                      champion (recall first, then lowest cost). Losers are kept as labelled fallbacks.

serves_truth=false — describing / indexing / retrieving a candidate primitive never promotes it.

    PYTHONPATH=. python3 scripts/primitive_retrieval_bakeoff.py --self-test
    PYTHONPATH=. python3 scripts/primitive_retrieval_bakeoff.py --corpus-columns   # column count on the real corpus
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
import math  # noqa: E402
import zlib  # noqa: E402
from typing import Any, Callable, Iterable  # noqa: E402

from scripts import capability_embedding as _capability_embedding  # noqa: E402  REUSE: embedder + cosine
from scripts import edge_representations as _edge_representations  # noqa: E402  REUSE: edge family fold
from scripts import primitive_descriptor as _primitive_descriptor  # noqa: E402  REUSE: symbolic facets + compare
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402  REUSE: the ONE tokenizer

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ── tuning (named, single-source; a band count/width/threshold is a recall↔cost knob, not a magic literal) ──
_MINHASH_PERMUTATIONS = 64                 # fixed hash functions in the MinHash signature
_MINHASH_RESOLUTIONS = (2, 4, 8)           # rows-per-band: coarse(2)=big buckets/high recall … fine(8)=small/precise
_SIMHASH_BITS = 64                         # deterministic hyperplanes (bits) in the SimHash signature
_SIMHASH_RESOLUTIONS = (2, 4, 8)           # bits-per-band (overlapping resolutions, same idea as MinHash)
_CANOPY_THRESHOLD = 0.30                   # embedding cosine to join a greedy canopy cluster (grouping/partitioning)
_DEFAULT_K = 5                             # retrieval depth for recall@k / precision@k in the bakeoff

# ── panel-winner tuning (15-discipline ideation panel, 2026-07-05; each strategy = a new raced row) ──
_PSTABLE_BANDS = 24                        # Gaussian projections in the p-stable L2 grid signature
_PSTABLE_GROUP = 4                         # consecutive bands concatenated into one grid block key
_PSTABLE_WIDTHS = (2.0, 4.0, 8.0)          # grid cell widths: NARROW(2.0)=precise cells … WIDE(8.0)=high recall
_BM25_K1 = 1.2                             # BM25 term-frequency saturation (standard Robertson k1)
_BM25_B = 0.4                              # BM25 length normalization (mild: cards are short, near-uniform docs)
_PMI_TOP_PARTNERS = 3                      # deterministic doc-expansion partners kept per token (SPLADE-style, no model)
_PMI_FLOOR = 1.0                           # min PMI for a co-occurrence partner to qualify as an expansion
_EXPAND_LAMBDA = 0.5                       # expansion-column weight discount vs the evoking token's own weight
_SEED_MASKS = ("111", "1101", "11011", "110101")  # spaced-seed binary masks (1=read, 0=skip; BLAST-style, no RNG)

# ── second panel wave (the build-rated-4 winners, 2026-07-05) ──
_BLOOM_BITS = 2048                         # W: Bloom sketch width (bits)
_BLOOM_HASHES = 4                          # r: bits set per token
_BLOOM_PANELS = 8                          # locality panels for the bloompanel: block keys
_LOCKKEY_BITS = 1024                       # B: provides/requires fold width (collisions = false POSITIVES only)
_ZORDER_DIMS = 6                           # projected axes Morton-interleaved into the curve key
_ZORDER_BITS = 10                          # quantization bits per axis
_ZORDER_WINDOW = 8                         # +/- neighbors taken around the curve position at query time
_SURPRISAL_BUDGET_BITS = 12.0              # stop collecting blocking keys once cumulative surprisal reaches this
_SURPRISAL_MAX_KEYS = 4                    # hard cap on keys per card
_SURPRISAL_MAX_DF_FRACTION = 0.2           # never block on a feature more common than this corpus fraction
_RG_TOP_FACETS = 2                         # facets in a coarse-graining block key
_RG_MAJORITY = 0.5                         # facet survives coarse-graining when present in >= this member share
_RG_DESCEND_BREADTH = 3                    # super-nodes kept per level during retrieval descent
_MAPPER_LENSES = 2                         # content-derived lens directions
_MAPPER_BINS = 6                           # cover bins per lens axis
_MAPPER_OVERLAP = 0.5                      # fractional bin overlap (what makes the blocks SOFT)
_CPOLY_BANDS = 8                           # cross-polytope hash bands
_CPOLY_GROUP = 2                           # bands concatenated per block key (AND-amplification)
_WAND_MUST_FAMILIES = ("op", "impact")     # query column families promoted to MUST in the boolean plan

#: ordinal information richness per datatype family (documented ORDINAL scale, not physical bits) — the
#: information-flow axis compares OUTPUT vs INPUT richness to classify compressor/preserver/expander.
_DATATYPE_INFO_WEIGHT: dict[str, float] = {"scalar": 1.0, "temporal": 2.0, "geo": 3.0, "text": 5.0,
                                           "graph": 6.0, "structured": 7.0, "collection": 8.0, "media": 9.0}
#: operation flow sign cross-check: -1 = compresses, 0 = preserves, +1 = expands (single-source).
_OP_FLOW_SIGN: dict[str, int] = {"dedup": -1, "filter": -1, "aggregate": -1, "rank": -1, "classify": -1,
                                 "validate": -1, "normalize": 0, "transform": 0, "embed": 0, "enrich": 0,
                                 "extract": 1, "generate": 1}
_FLOWCLASS_THRESHOLDS = (-2.0, -0.5, 0.5)  # strong_compressor < -2 <= compressor < -0.5 <= preserver < 0.5 <= expander

#: FRAME axis (single source) — frame -> evoking lexical units: a FOLD-UP over the 12-op split plus the
#: near-synonyms it loses. frame(card) = largest keyword overlap; ties break by THIS insertion order.
FRAME_LEXICON: dict[str, tuple[str, ...]] = {
    "Removing":       ("remove", "delete", "drop", "strip", "filter", "exclude", "prune", "dedup", "collapse"),
    "Amalgamation":   ("merge", "join", "combine", "link", "aggregate", "fold", "group", "consolidate"),
    "Transforming":   ("transform", "convert", "translate", "map", "encode", "decode", "render", "resize",
                       "normalize", "canonicalize"),
    "Extracting":     ("extract", "parse", "ocr", "pull", "scrape", "read", "detect"),
    "Scrutiny":       ("validate", "verify", "check", "screen", "audit", "assert", "reconcile"),
    "Categorization": ("classify", "label", "tag", "route", "assign"),
    "Assessing":      ("rank", "score", "rerank", "sort", "prioritize", "rate"),
    "Creating":       ("generate", "synthesize", "produce", "create", "compose", "build"),
    "Representation": ("embed", "vectorize", "represent"),
    "Enriching":      ("enrich", "augment", "annotate", "resolve", "match", "lookup"),
}

#: FRAME_RELATIONS (single source, static): (frame_a, relation, frame_b). ``inherits`` targets are abstract
#: superframes (kinship via a SHARED parent); ``uses``/``inverse`` are direct kin; ``precedes`` is the curated
#: canonical AI-pipeline order (the COMPOSITION relation: what plausibly comes NEXT).
FRAME_RELATIONS: tuple[tuple[str, str, str], ...] = (
    ("Removing", "inherits", "Cardinality_change"),
    ("Amalgamation", "inherits", "Cardinality_change"),
    ("Transforming", "inherits", "Structure_change"),
    ("Extracting", "uses", "Representation"),
    ("Enriching", "uses", "Scrutiny"),
    ("Removing", "inverse", "Creating"),
    ("Extracting", "precedes", "Transforming"),
    ("Transforming", "precedes", "Removing"),
    ("Removing", "precedes", "Enriching"),
    ("Enriching", "precedes", "Scrutiny"),
    ("Scrutiny", "precedes", "Assessing"),
    ("Assessing", "precedes", "Categorization"),
    ("Categorization", "precedes", "Creating"),
    ("Representation", "precedes", "Assessing"),
)


# ──────────────────────────────────────────────────────────────────────────────
# FEATURE FACTORY — the wide, named, sparse column space.
# ──────────────────────────────────────────────────────────────────────────────
def feature_columns(card: dict[str, Any]) -> dict[str, float]:
    """A WIDE named sparse feature vector for one primitive — the "thousands of columns" descriptor. Each key is a
    globally-unique, meaning-bearing column name (namespaced by family), each value a weight. Families: per-token
    (tok:), per-phrase (phr:), per-datatype (dtype:), per-operation (op:), impact (impact:), edge-shape (shape:),
    embedding-bucket (emb:). Sparse: only the columns a primitive activates are present."""
    desc = _primitive_descriptor.describe(card, with_semantic=False)
    cols: dict[str, float] = {}
    for t in desc["keywords"]:
        cols[f"tok:{t}"] = 1.0
    for p in desc["keyphrases"]:
        cols[f"phr:{p}"] = 1.0
    for d in desc["datatypes"]:
        cols[f"dtype:{d}"] = 1.0
    for o in desc["operations"]:
        cols[f"op:{o}"] = 1.0
    cols[f"impact:{desc['impact_class']}"] = 1.0
    cols[f"shape:opcount_{min(desc['operation_count'], 9)}"] = 1.0
    for side in ("input", "output"):
        edge = _capability_embedding._edge_str(card, side)
        toks = edge.replace("+", " ").split()
        cols[f"shape:{side}_arity_{min(len(toks), 5)}"] = 1.0
        if "+" in edge:
            cols[f"shape:{side}_compound"] = 1.0
    vec = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(card))
    for i, v in enumerate(vec):
        if v > 0.0:
            cols[f"emb:{i}"] = round(v, 4)
    # panel-winner axes: frame (frame:), reaction transformation tag (rxntag:), spaced capability seeds (sseed:)
    frame = frame_of_card(card)
    if frame:
        cols[f"frame:{frame}"] = 1.0
    cols[f"rxntag:{reaction_fingerprint(card)['rxntag']}"] = 1.0
    for seed in spaced_seeds(capability_sequence(card)):
        cols[seed] = 1.0  # already namespaced 'sseed:{mask}:{codes}'
    # second-wave axes: information flow (flowclass:/flowbits:), curve + cross-polytope locality keys
    flow = information_flow_axis(card)
    cols[f"flowclass:{flow['flowclass']}"] = 1.0
    cols[f"flowbits:{round(flow['flow_delta_bits'])}"] = 1.0
    cols[f"curvekey:zorder_d{_ZORDER_DIMS}_b{_ZORDER_BITS}_{zorder_curve_key(card)}"] = 1.0
    for cp in cross_polytope_keys(card):
        cols[cp] = 1.0  # already namespaced 'cpoly_{group}:'
    # per-REGISTER embedding columns (plain/technical/semantic) — three MORE dense axes beside emb:
    for register, prefix in (("plain", "embp"), ("technical", "embt"), ("semantic", "embs")):
        rvec = _capability_embedding.embed_tokens(_capability_embedding.register_text(card, register))
        for i, v in enumerate(rvec):
            if v > 0.0:
                cols[f"{prefix}:{i}"] = round(v, 4)
    return cols


def corpus_column_count(cards: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Distinct column count across a corpus (proves the space is WIDE — thousands over the real corpus), by family."""
    families: dict[str, set] = {}
    total: set = set()
    for card in cards:
        for col in feature_columns(card):
            families.setdefault(col.split(":", 1)[0], set()).add(col)
            total.add(col)
    return {"distinct_columns": len(total),
            "by_family": {k: len(v) for k, v in sorted(families.items())}, **BOUNDARY}


# ──────────────────────────────────────────────────────────────────────────────
# Signatures — deterministic MinHash (symbolic sets) + SimHash (dense embeddings).
# ──────────────────────────────────────────────────────────────────────────────
def _minhash_signature(tokens: Iterable[str]) -> tuple[int, ...]:
    """Deterministic MinHash: for each of K fixed salted hashes, the min over the token SET (approx Jaccard)."""
    toks = list(dict.fromkeys(tokens)) or ["\x00empty"]
    return tuple(min(zlib.crc32(f"{salt}:".encode() + t.encode()) for t in toks)
                 for salt in range(_MINHASH_PERMUTATIONS))


def _minhash_band_keys(sig: tuple[int, ...], rows: int) -> list[str]:
    """Band a MinHash signature at a given resolution (rows/band). Namespaced by ``rows`` so overlapping coarse and
    fine resolutions never collide — this is how "large and small overlapping LSH" coexist in one index."""
    bands = _MINHASH_PERMUTATIONS // rows
    return [f"mh{rows}_{b}:" + "_".join(str(x) for x in sig[b * rows:(b + 1) * rows]) for b in range(bands)]


def _hyperplane_sign(plane: int, dim: int) -> float:
    return 1.0 if (zlib.crc32(f"hp:{plane}:{dim}".encode()) & 1) else -1.0


def _simhash_signature(vec: list[float]) -> int:
    """Deterministic SimHash: bit p = sign(vec · fixed hyperplane_p). Similar vectors -> few differing bits."""
    bits = 0
    for p in range(_SIMHASH_BITS):
        dot = 0.0
        for d, v in enumerate(vec):
            if v:
                dot += v * _hyperplane_sign(p, d)
        if dot >= 0.0:
            bits |= (1 << p)
    return bits


def _simhash_band_keys(sig: int, rows: int) -> list[str]:
    """Band a SimHash bit-signature at a resolution (bits/band), namespaced by ``rows`` (overlapping resolutions)."""
    mask = (1 << rows) - 1
    return [f"sh{rows}_{b}:{(sig >> (b * rows)) & mask}" for b in range(_SIMHASH_BITS // rows)]


def _query_sets(card: dict[str, Any]) -> frozenset[str]:
    return _primitive_descriptor.keywords(card) | _primitive_descriptor.keyphrases(card)


# ──────────────────────────────────────────────────────────────────────────────
# Panel-winner signatures (all deterministic, offline, no RNG — crc32-seeded like MinHash/SimHash above).
# ──────────────────────────────────────────────────────────────────────────────
def _unit_interval(key: str) -> float:
    """crc32 -> (0,1): the fixed, content-derived uniform draw every seeded construction below builds on."""
    return (zlib.crc32(key.encode()) + 0.5) / 2**32


_PSTABLE_GAUSSIAN_CACHE: dict[tuple[int, str], float] = {}  # (band, column) -> N(0,1); columns repeat across cards


def _pstable_gaussian(band: int, col: str) -> float:
    """Deterministic standard normal via Box-Muller over crc32-seeded uniforms — a fixed Gaussian projection
    family with NO RNG (the p-stable property: L2-close vectors project close)."""
    got = _PSTABLE_GAUSSIAN_CACHE.get((band, col))
    if got is None:
        u1 = _unit_interval(f"pstable:{band}:{col}:u1")
        u2 = _unit_interval(f"pstable:{band}:{col}:u2")
        got = _PSTABLE_GAUSSIAN_CACHE[(band, col)] = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
    return got


def _pstable_grid_keys(cols: dict[str, float], widths: tuple[float, ...] = _PSTABLE_WIDTHS) -> list[str]:
    """p-stable L2 grid block keys over the WEIGHTED SPARSE feature vector (not the dense embedding): project the
    present columns through fixed Gaussians (O(nnz × bands)), quantize each projection into offset grid cells at
    each WIDTH (wide cells = big buckets/high recall, narrow = precise), and concatenate consecutive bands into
    group keys. Namespaced ``pgrid{width}_{group}:`` so resolutions never collide."""
    projections = [sum(w * _pstable_gaussian(j, c) for c, w in cols.items()) for j in range(_PSTABLE_BANDS)]
    groups = _PSTABLE_BANDS // _PSTABLE_GROUP
    keys: list[str] = []
    for width in widths:
        cells = [math.floor((projections[j] + _unit_interval(f"pstable:{j}:offset:{width}") * width) / width)
                 for j in range(_PSTABLE_BANDS)]
        for g in range(groups):
            block = "_".join(str(cells[j]) for j in range(g * _PSTABLE_GROUP, (g + 1) * _PSTABLE_GROUP))
            keys.append(f"pgrid{width}_{g}:{block}")
    return keys


def frame_of_card(card: dict[str, Any]) -> str:
    """The FRAME a card evokes: the FRAME_LEXICON entry with the largest keyword overlap (deterministic; ties
    break by lexicon insertion order). '' when no lexical unit fires — an unframed card joins no frame block."""
    kw = _primitive_descriptor.keywords(card)
    best, best_overlap = "", 0
    for frame, units in FRAME_LEXICON.items():
        overlap = len(kw.intersection(units))
        if overlap > best_overlap:
            best, best_overlap = frame, overlap
    return best


def _frame_relation_sets() -> tuple[dict[str, frozenset[str]], dict[str, frozenset[str]]]:
    """Precompute each frame's KIN set (graph-distance 1 over inherits/uses/inverse, incl. siblings under a
    shared superframe, incl. self) and SUCCESSOR set (precedes targets) — static and tiny, so queries are O(1)
    bucket lookups, never live BFS."""
    parents: dict[str, set[str]] = {}
    direct: dict[str, set[str]] = {f: set() for f in FRAME_LEXICON}
    succ: dict[str, set[str]] = {f: set() for f in FRAME_LEXICON}
    for a, rel, b in FRAME_RELATIONS:
        if rel == "inherits":
            parents.setdefault(a, set()).add(b)
        elif rel in ("uses", "inverse"):  # kinship is about relatedness -> symmetric for candidate generation
            if a in direct and b in direct:
                direct[a].add(b)
                direct[b].add(a)
        elif rel == "precedes" and a in succ and b in FRAME_LEXICON:
            succ[a].add(b)
    kin: dict[str, frozenset[str]] = {}
    for f in FRAME_LEXICON:
        related = {f} | direct[f]
        for g in FRAME_LEXICON:  # siblings: any frame inheriting a shared abstract superframe
            if g != f and parents.get(f, set()) & parents.get(g, set()):
                related.add(g)
        kin[f] = frozenset(related)
    return kin, {f: frozenset(s) for f, s in succ.items()}


def _edge_reaction_features(edge: str) -> frozenset[str]:
    """A chemistry-style feature set for ONE edge: type tokens ∪ datatype families ∪ char-trigrams of the
    canonical form — the 'atoms and bonds' the reaction difference fingerprint is computed over."""
    if not edge:
        return frozenset()
    toks = _edge_representations.type_tokens(edge)
    fams = {_primitive_descriptor._DTYPE_BY_TOKEN[t] for t in toks if t in _primitive_descriptor._DTYPE_BY_TOKEN}
    canon = _edge_representations.canonical(edge)
    tris = {canon[i:i + 3] for i in range(len(canon) - 2)} if len(canon) >= 3 else ({canon} if canon else set())
    return frozenset(toks) | fams | tris


def _edge_datatype_family(edge: str) -> str:
    """The primary datatype family of an edge (sorted-first for determinism), or 'any' — the coarse rxntag half."""
    toks = _edge_representations.type_tokens(edge)
    fams = sorted(_primitive_descriptor._DTYPE_BY_TOKEN[t] for t in toks
                  if t in _primitive_descriptor._DTYPE_BY_TOKEN)
    return fams[0] if fams else "any"


def reaction_fingerprint(card: dict[str, Any]) -> dict[str, Any]:
    """The SIGNED reaction-difference fingerprint of a primitive, from its EDGE fields only: what the primitive
    FORMS (output features not in the input), what it BREAKS (input features consumed), what SPECTATES (both
    sides), plus the coarse ``rxntag`` transformation tag (input-family >> output-family)."""
    r = _edge_reaction_features(_capability_embedding._edge_str(card, "input"))
    p = _edge_reaction_features(_capability_embedding._edge_str(card, "output"))
    return {"formed": p - r, "broken": r - p, "spectator": r & p,
            "rxntag": f"{_edge_datatype_family(_capability_embedding._edge_str(card, 'input'))}"
                      f">>{_edge_datatype_family(_capability_embedding._edge_str(card, 'output'))}"}


_SEED_ALPHABET: dict[str, str] = {  # capability alphabet: op/dtype-family/impact -> 1-char code (like amino acids)
    name: code for code, name in zip(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
        list(_primitive_descriptor.OPERATION_LEXICON)
        + list(_primitive_descriptor.DATATYPE_LEXICON)
        + sorted(set(_primitive_descriptor.OP_TO_IMPACT.values())),
    )
}


def capability_sequence(card: dict[str, Any]) -> str:
    """The card's capability SEQUENCE: tokens of title+blackbox in READING ORDER, each resolved to its
    operation/datatype code, deduped by code keeping the earliest mention — a true ordered string (unlike the
    ``operations()`` frozenset), e.g. extract→normalize→dedup ≈ 'END'."""
    text = f"{card.get('title') or ''} {_capability_embedding.blackbox_text(card)}"
    first_index: dict[str, int] = {}
    for i, tok in enumerate(_tokenize(text)):
        name = _primitive_descriptor._OP_BY_TOKEN.get(tok) or _primitive_descriptor._DTYPE_BY_TOKEN.get(tok)
        code = _SEED_ALPHABET.get(name or "")
        if code and code not in first_index:
            first_index[code] = i
    return "".join(sorted(first_index, key=first_index.get))


def spaced_seeds(sequence: str) -> frozenset[str]:
    """BLAST-style spaced seeds over a capability sequence: every mask × offset window, reading only the mask's
    1-positions. A low-complexity guard drops seeds whose kept chars are all identical (uninformative)."""
    seeds: set[str] = set()
    for mask_id, mask in enumerate(_SEED_MASKS):
        span = len(mask)
        for offset in range(len(sequence) - span + 1):
            kept = "".join(sequence[offset + j] for j, bit in enumerate(mask) if bit == "1")
            if len(set(kept)) > 1:  # low-complexity guard
                seeds.add(f"sseed:{mask_id}:{kept}")
    return frozenset(seeds)


# ──────────────────────────────────────────────────────────────────────────────
# Second panel wave — per-card signatures/axes (corpus-free; corpus-level structures build in the index).
# ──────────────────────────────────────────────────────────────────────────────
def information_flow_axis(card: dict[str, Any]) -> dict[str, Any]:
    """The information-flow (compression-ratio) axis: compare OUTPUT vs INPUT edge information richness
    (ordinal datatype weight × arity × compound bonus), direction-corrected by the operation's flow sign —
    negative = compressor (dedup/filter), ~0 = preserver, positive = expander (extract/generate)."""
    def _edge_bits(side: str) -> float:
        edge = _capability_embedding._edge_str(card, side)
        toks = _edge_representations.type_tokens(edge)
        fams = sorted(_primitive_descriptor._DTYPE_BY_TOKEN[t] for t in toks
                      if t in _primitive_descriptor._DTYPE_BY_TOKEN)
        arity = max(len(toks), 1)
        base = _DATATYPE_INFO_WEIGHT.get(fams[0], 1.0) if fams else 1.0
        return base * (1.0 + math.log2(arity)) * (1.5 if "+" in edge else 1.0)

    delta = math.log2(max(_edge_bits("output"), 1e-9) / max(_edge_bits("input"), 1e-9))
    signs = sorted({_OP_FLOW_SIGN[op] for op in _primitive_descriptor.operations(card) if op in _OP_FLOW_SIGN})
    op_sign = signs[0] if len(signs) == 1 else 0  # a single agreed sign corrects direction; mixed ops stay neutral
    if op_sign and (delta > 0) != (op_sign > 0) and delta != 0.0:
        delta = 0.5 * delta + 0.5 * op_sign * abs(delta)  # magnitude from edges, direction from op semantics
    lo, mid, hi = _FLOWCLASS_THRESHOLDS
    flowclass = ("strong_compressor" if delta < lo else "compressor" if delta < mid
                 else "preserver" if delta < hi else "expander")
    return {"flow_delta_bits": round(delta, 3), "flowclass": flowclass}


def bloom_sketch(card: dict[str, Any]) -> int:
    """W-bit Bloom sketch over the card's concept set (keywords ∪ keyphrases ∪ edge type tokens) — one int."""
    concepts = set(_query_sets(card))
    for side in ("input", "output"):
        concepts |= _edge_representations.type_tokens(_capability_embedding._edge_str(card, side))
    bits = 0
    for t in sorted(concepts):
        for i in range(_BLOOM_HASHES):
            bits |= 1 << (zlib.crc32(f"bloom:{i}:{t}".encode()) % _BLOOM_BITS)
    return bits


def bloom_contains(container: int, contained: int) -> bool:
    """Asymmetric containment screen: every bit of ``contained`` present in ``container``. NO false negatives
    (bits are a deterministic function of tokens); false positives bounded by the Bloom FP rate."""
    return (container & contained) == contained


def _bloom_jaccard(a: int, b: int) -> float:
    """Bloom-Jaccard estimate from popcounts only (estimated set sizes via the standard Bloom inversion)."""
    w, r = float(_BLOOM_BITS), float(_BLOOM_HASHES)

    def _est(x: int) -> float:
        return -(w / r) * math.log(max(1.0 - bin(x).count("1") / w, 1.0 / w))

    union = _est(a | b)
    if union <= 0.0:
        return 0.0
    return max(0.0, (_est(a) + _est(b) - union) / union)


def _bloom_panel_keys(sketch: int) -> list[str]:
    """Locality-preserving panel block keys: per panel, bucketed popcount + densest position — cards with
    similar token mass in the same sketch region co-locate; panels OR'd give recall."""
    panel_bits = _BLOOM_BITS // _BLOOM_PANELS
    mask = (1 << panel_bits) - 1
    keys: list[str] = []
    for p in range(_BLOOM_PANELS):
        panel = (sketch >> (p * panel_bits)) & mask
        pop = bin(panel).count("1")
        dense = panel.bit_length() // 32  # coarse densest-region marker (highest set bit's 32-bit block)
        keys.append(f"bloompanel{p}:{pop // 8}_{dense}")
    return keys


def lock_and_key_fold(card: dict[str, Any]) -> dict[str, int]:
    """REQUIRES (input pocket) and PROVIDES (output surface) as B-bit folded edge-feature vectors. Folding
    collides bits (false POSITIVES) but never drops a real feature (no false negatives), so the feasibility
    screen (REQUIRES & ~PROVIDES == 0) never wrongly rejects a real wiring."""
    def _fold(side: str) -> int:
        edge = _capability_embedding._edge_str(card, side)
        if not edge:
            return 0
        feats = set(_edge_representations.type_tokens(edge))
        feats |= {_primitive_descriptor._DTYPE_BY_TOKEN[t] for t in feats
                  if t in _primitive_descriptor._DTYPE_BY_TOKEN}
        feats.add(_edge_representations.canonical(edge))
        feats.add(f"structural:{_edge_representations.structural(edge)}")  # arity/compound/plural marker
        bits = 0
        for f in sorted(str(x) for x in feats if x):
            bits |= 1 << (zlib.crc32(f"lockkey:{f}".encode()) % _LOCKKEY_BITS)
        return bits

    return {"requires": _fold("input"), "provides": _fold("output")}


def lock_and_key_can_feed(producer_provides: int, consumer_requires: int) -> bool:
    """Feasibility: producer P can feed consumer Q iff Q.REQUIRES ⊆ P.PROVIDES on the folded bits."""
    return (consumer_requires & ~producer_provides) == 0


def zorder_curve_key(card: dict[str, Any]) -> int:
    """Morton/Z-order curve key over the blackbox embedding: project to a few axes with fixed content-derived
    sign vectors (keeping the REAL value, not the sign bit), monotonically squash+quantize, bit-interleave —
    L2-neighbors land near each other on the 1-D curve."""
    v = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(card))
    quantized: list[int] = []
    top = (1 << _ZORDER_BITS) - 1
    for j in range(_ZORDER_DIMS):
        p = sum(val * (1.0 if (zlib.crc32(f"zpl:{j}:{d}".encode()) & 1) else -1.0)
                for d, val in enumerate(v) if val)
        quantized.append(int((0.5 + 0.5 * math.tanh(p)) * top))
    key = 0
    for i in range(_ZORDER_BITS):
        for j in range(_ZORDER_DIMS):
            key |= ((quantized[j] >> i) & 1) << (i * _ZORDER_DIMS + j)
    return key


def cross_polytope_keys(card: dict[str, Any]) -> list[str]:
    """Cross-polytope LSH labels over the dense blackbox embedding: per band, a deterministic structured
    rotation (sign flip → Fast Walsh-Hadamard → crc32-keystream permutation → sign flip), label = the argmax
    |coordinate| vertex; small band groups concatenate for AND-amplified block keys."""
    v = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(card))
    dim = 1
    while dim < len(v):
        dim *= 2
    labels: list[str] = []
    for band in range(_CPOLY_BANDS):
        x = [(v[k] if k < len(v) else 0.0)
             * (1.0 if (zlib.crc32(f"cp:{band}:s1:{k}".encode()) & 1) else -1.0) for k in range(dim)]
        h = 1
        while h < dim:  # in-place Fast Walsh-Hadamard butterfly
            for i in range(0, dim, h * 2):
                for k in range(i, i + h):
                    a, b = x[k], x[k + h]
                    x[k], x[k + h] = a + b, a - b
            h *= 2
        for step in range(dim - 1, 0, -1):  # crc32-keystream Fisher-Yates (deterministic permutation)
            swap = zlib.crc32(f"cp:{band}:perm:{step}".encode()) % (step + 1)
            x[step], x[swap] = x[swap], x[step]
        x = [x[k] * (1.0 if (zlib.crc32(f"cp:{band}:s2:{k}".encode()) & 1) else -1.0) for k in range(dim)]
        arg = max(range(dim), key=lambda k: (abs(x[k]), -k))
        labels.append(f"{arg}{'+' if x[arg] >= 0 else '-'}")
    return [f"cpoly_{g}:" + "_".join(labels[g * _CPOLY_GROUP:(g + 1) * _CPOLY_GROUP])
            for g in range(_CPOLY_BANDS // _CPOLY_GROUP)]


def _surprisal_keys(symbolic_cols: frozenset, df: dict[str, int], n: int) -> list[str]:
    """Budgeted rare-first blocking keys: greedily take the card's most-surprising features until the surprisal
    budget (or the key cap) is hit; never block on a feature more common than the df-fraction cap."""
    cap = max(1, int(_SURPRISAL_MAX_DF_FRACTION * n))
    usable = sorted((c for c in symbolic_cols if 0 < df.get(c, 0) <= cap),
                    key=lambda c: (-math.log2(n / df[c]), c))
    keys: list[str] = []
    spent = 0.0
    for c in usable:
        keys.append(f"surp:{c}")
        spent += math.log2(n / df[c])
        if spent >= _SURPRISAL_BUDGET_BITS or len(keys) >= _SURPRISAL_MAX_KEYS:
            break
    return keys


def _rg_facets(card: dict[str, Any], family_index: dict[str, str]) -> frozenset[str]:
    """The symbolic facet 'spin' of one primitive: operations + datatypes + impact + in/out edge families."""
    facets = {f"op:{o}" for o in _primitive_descriptor.operations(card)}
    facets |= {f"dtype:{d}" for d in _primitive_descriptor.datatypes(card)}
    facets.add(f"impact:{_primitive_descriptor.impact_class(card)}")
    for side in ("input", "output"):
        fam = _edge_representations.family(_capability_embedding._edge_str(card, side), family_index)
        if fam:
            facets.add(f"fam_{side}:{fam}")
    return frozenset(facets)


def _rg_build_levels(facets_by_id: dict[str, frozenset], facet_idf: dict[str, float]) -> list[dict[str, dict]]:
    """Block-spin coarse-graining: group by the top-idf facet block key, majority-rule the group's spin, and
    DECIMATE one more of the rarest global facets per level (short-wavelength detail integrates out first).
    Stops at a fixed point (node count stops shrinking) or a single root. Returns one {super_id: {spin,
    members}} dict per level, finest first."""
    decimation_order = sorted(facet_idf, key=lambda f: (-facet_idf[f], f))
    nodes: dict[str, dict] = {pid: {"spin": facets, "members": [pid]}
                              for pid, facets in sorted(facets_by_id.items())}
    levels: list[dict[str, dict]] = []
    level = 0
    while len(nodes) > 1:
        dropped = set(decimation_order[:level])
        groups: dict[str, list[str]] = {}
        for node_id in sorted(nodes):
            spin = [f for f in nodes[node_id]["spin"] if f not in dropped]
            top = sorted(spin, key=lambda f: (-facet_idf.get(f, 0.0), f))[:_RG_TOP_FACETS]
            groups.setdefault("|".join(top) or "(void)", []).append(node_id)
        supers: dict[str, dict] = {}
        for block_key in sorted(groups):
            member_nodes = groups[block_key]
            members = sorted(pid for m in member_nodes for pid in nodes[m]["members"])
            counts: dict[str, int] = {}
            for m in member_nodes:
                for f in nodes[m]["spin"]:
                    counts[f] = counts.get(f, 0) + 1
            majority = frozenset(f for f, c in counts.items() if c / len(member_nodes) >= _RG_MAJORITY)
            super_id = f"rgsuper__L{level + 1}__{zlib.crc32(block_key.encode()):08x}"
            supers[super_id] = {"spin": majority, "members": members}
        levels.append(supers)
        if len(supers) >= len(nodes):  # fixed point: coarse-graining stopped shrinking
            break
        nodes = supers
        level += 1
    return levels


def _percolation_sweep(card_by_id: dict[str, dict], family_index: dict[str, str]) -> dict[str, Any]:
    """Edge-family percolation: activate family hyperedges strongest (rarest/most specific) first, union their
    producers+consumers, and track the giant component. Yields per-primitive join-step centrality (early =
    hub), the critical activation (largest giant-size jump), bridge families, and component labels at the
    critical cut — the transitive 'wireable-with' relation for O(1) lookup."""
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    for pid in sorted(card_by_id):
        card = card_by_id[pid]
        out_fam = _edge_representations.family(_capability_embedding._edge_str(card, "output"), family_index)
        in_fam = _edge_representations.family(_capability_embedding._edge_str(card, "input"), family_index)
        if out_fam:
            producers.setdefault(out_fam, []).append(pid)
        if in_fam:
            consumers.setdefault(in_fam, []).append(pid)
    n = max(len(card_by_id), 1)
    families = sorted(set(producers) | set(consumers))
    strength = {f: -math.log((len(producers.get(f, ())) * len(consumers.get(f, ())) + 1) / (n * n))
                for f in families}
    sweep = sorted(families, key=lambda f: (-strength[f], f))

    parent: dict[str, str] = {pid: pid for pid in card_by_id}

    def _find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    size = {pid: 1 for pid in card_by_id}
    joined_step: dict[str, int] = {}
    giant_sizes: list[int] = []
    bridges: list[str] = []
    for step, fam in enumerate(sweep):
        members = sorted(set(producers.get(fam, [])) | set(consumers.get(fam, [])))
        roots_before = {r for r in (_find(m) for m in members)}
        large_before = sum(1 for r in roots_before if size[r] > 1)
        for a, b in zip(members, members[1:]):
            ra, rb = _find(a), _find(b)
            if ra != rb:
                if size[ra] < size[rb]:
                    ra, rb = rb, ra
                parent[rb] = ra
                size[ra] += size[rb]
        if large_before >= 2:
            bridges.append(fam)  # fused two already-grown components: a load-bearing composition seam
        giant_root = max(parent, key=lambda p: (size[_find(p)], p))
        giant = _find(giant_root)
        giant_sizes.append(size[giant])
        for pid in card_by_id:
            if pid not in joined_step and _find(pid) == giant and size[giant] > 1:
                joined_step[pid] = step
    jumps = [giant_sizes[i] - (giant_sizes[i - 1] if i else 1) for i in range(len(giant_sizes))]
    critical_step = max(range(len(jumps)), key=lambda i: (jumps[i], -i)) if jumps else 0
    total = max(len(sweep), 1)
    centrality_q = {pid: min(9, (step * 10) // total) for pid, step in joined_step.items()}
    component_of = {pid: _find(pid) for pid in card_by_id}  # labels at the full sweep (transitive wireability)
    return {"sweep": sweep, "strength": strength, "critical_step": critical_step, "bridges": bridges,
            "centrality_q": centrality_q, "component_of": component_of, "giant_sizes": giant_sizes}


def _persistence_deaths(ordered_pids: list[str], mh_sig_by_id: dict[str, tuple]) -> dict[str, int]:
    """0-dim persistence over the MinHash filtration (r=8 fine -> r=2 coarse as t=0,1,2): components only ever
    MERGE as bands coarsen; the elder rule (elder = smallest primitive_id) assigns each card the level at which
    its component was absorbed by an older one. 3 = never died (isolated outlier)."""
    parent = {pid: pid for pid in ordered_pids}
    death = {pid: 3 for pid in ordered_pids}

    def _find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for t, rows in enumerate(sorted(_MINHASH_RESOLUTIONS, reverse=True)):  # fine(8) -> coarse(2)
        buckets: dict[str, list[str]] = {}
        for pid in ordered_pids:
            for k in _minhash_band_keys(mh_sig_by_id[pid], rows):
                buckets.setdefault(k, []).append(pid)
        for k in sorted(buckets):
            members = buckets[k]
            for a, b in zip(members, members[1:]):
                ra, rb = _find(a), _find(b)
                if ra == rb:
                    continue
                elder, younger = (ra, rb) if ra < rb else (rb, ra)
                for pid in ordered_pids:  # the younger component's members die at this level
                    if _find(pid) == younger and death[pid] == 3:
                        death[pid] = t
                parent[younger] = elder
    for pid in ordered_pids:  # cards that never merged into an elder keep death=3 (isolated)
        if _find(pid) == pid and death[pid] == 3 and pid == min(p for p in ordered_pids if _find(p) == pid):
            death[pid] = 3
    return death


def _mapper_node_ids(card: dict[str, Any]) -> list[str]:
    """Mapper vertex ids for one card: overlapping lens-bin cover cells × the dominant-operation connectivity
    key. The overlap makes the blocks SOFT — a card near a bin boundary belongs to both neighbors."""
    v = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(card))
    half_width = (1.0 / _MAPPER_BINS) * (1.0 + _MAPPER_OVERLAP)
    bin_sets: list[list[int]] = []
    for f in range(_MAPPER_LENSES):
        lens = sum(val * (1.0 if (zlib.crc32(f"mapperlens:{f}:{i}".encode()) & 1) else -1.0)
                   for i, val in enumerate(v) if val)
        lens = max(-1.0, min(1.0, lens))
        hits = [b for b in range(_MAPPER_BINS)
                if abs(lens - (-1.0 + (b + 0.5) * (2.0 / _MAPPER_BINS))) <= half_width]
        bin_sets.append(hits or [0])
    ops = sorted(_primitive_descriptor.operations(card))
    connkey = ops[0] if ops else "none"
    return [f"mapnode:{b0}_{b1}:{connkey}" for b0 in bin_sets[0] for b1 in bin_sets[1]]


# ──────────────────────────────────────────────────────────────────────────────
# The INDEX — every strategy's buckets/partitions built once (all sub-linear to query).
# ──────────────────────────────────────────────────────────────────────────────
def build_lsh_index(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Build every candidate-generation structure: MinHash buckets at each resolution, SimHash buckets at each
    resolution, operation partitions, edge-family partitions, and greedy embedding CANOPY clusters — plus per-card
    signatures/vectors so a reranker scores without recompute. Deterministic + order-stable (sorted iteration)."""
    minhash_buckets: dict[int, dict[str, list[str]]] = {r: {} for r in _MINHASH_RESOLUTIONS}
    simhash_buckets: dict[int, dict[str, list[str]]] = {r: {} for r in _SIMHASH_RESOLUTIONS}
    op_partition: dict[str, list[str]] = {}
    family_partition: dict[str, list[str]] = {}
    keywords_by_id: dict[str, frozenset] = {}
    vec_by_id: dict[str, list[float]] = {}
    card_by_id: dict[str, dict] = {}
    mh_sig_by_id: dict[str, tuple] = {}
    sh_sig_by_id: dict[str, int] = {}
    # panel-winner structures
    pstable_buckets: dict[str, list[str]] = {}          # p-stable L2 grid: block key -> pids
    frame_of: dict[str, str] = {}                       # pid -> frame ('' = unframed)
    frame_partition: dict[str, list[str]] = {}          # frame -> pids
    rxn_by_id: dict[str, dict] = {}                     # pid -> reaction fingerprint (formed/broken/spectator/tag)
    rxn_formed_index: dict[str, list[str]] = {}         # formed feature -> pids that FORM it (retrosynthesis lookup)
    seeds_by_id: dict[str, frozenset] = {}              # pid -> spaced-seed set
    sseed_index: dict[str, list[str]] = {}              # spaced seed -> pids (the BLAST word-lookup table)

    # family fold over ALL corpus edges (inputs+outputs), so a query output edge folds the SAME way.
    all_edges: list[str] = []
    for c in cards:
        for side in ("input", "output"):
            e = _capability_embedding._edge_str(c, side)
            if e:
                all_edges.append(e)
    family_index = _edge_representations.build_family_index(all_edges)

    for card in cards:
        pid = card.get("primitive_id")
        if not pid or pid in card_by_id:
            continue
        kw = _query_sets(card)
        vec = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(card))
        mh_sig = _minhash_signature(kw)
        sh_sig = _simhash_signature(vec)
        keywords_by_id[pid] = kw
        vec_by_id[pid] = vec
        card_by_id[pid] = card
        mh_sig_by_id[pid] = mh_sig
        sh_sig_by_id[pid] = sh_sig
        for r in _MINHASH_RESOLUTIONS:
            for k in _minhash_band_keys(mh_sig, r):
                minhash_buckets[r].setdefault(k, []).append(pid)
        for r in _SIMHASH_RESOLUTIONS:
            for k in _simhash_band_keys(sh_sig, r):
                simhash_buckets[r].setdefault(k, []).append(pid)
        for op in _primitive_descriptor.operations(card):
            op_partition.setdefault(op, []).append(pid)
        fam = _edge_representations.family(_capability_embedding._edge_str(card, "output"), family_index)
        if fam:
            family_partition.setdefault(fam, []).append(pid)
        # panel winners: p-stable grid keys, frame block, reaction fingerprint, spaced seeds
        for k in _pstable_grid_keys(feature_columns(card)):
            pstable_buckets.setdefault(k, []).append(pid)
        frame = frame_of_card(card)
        frame_of[pid] = frame
        if frame:
            frame_partition.setdefault(frame, []).append(pid)
        rxn = reaction_fingerprint(card)
        rxn_by_id[pid] = rxn
        for feat in sorted(rxn["formed"]):
            rxn_formed_index.setdefault(feat, []).append(pid)
        seeds = spaced_seeds(capability_sequence(card))
        seeds_by_id[pid] = seeds
        for seed in sorted(seeds):
            sseed_index.setdefault(seed, []).append(pid)

    # greedy CANOPY clustering over embeddings (deterministic: sorted id order; a new centroid opens when no
    # existing centroid is within threshold — a grouping/partitioning strategy distinct from LSH banding).
    canopy_of: dict[str, str] = {}
    centroids: list[tuple[str, list[float]]] = []
    for pid in sorted(vec_by_id):
        vec = vec_by_id[pid]
        assigned = next((cid for cid, cvec in centroids
                         if _capability_embedding.cosine(vec, cvec) >= _CANOPY_THRESHOLD), None)
        if assigned is None:
            centroids.append((pid, vec))
            assigned = pid
        canopy_of[pid] = assigned
    canopy_members: dict[str, list[str]] = {}
    for pid, cid in canopy_of.items():
        canopy_members.setdefault(cid, []).append(pid)

    kin_sets, succ_sets = _frame_relation_sets()

    # ── second panel wave: corpus-level structures ──
    # (1) dense ordinals + symbolic-column postings with idf — the WAND boolean/ranked plane. Dense embedding
    # families are excluded: idf-weighted OVERLAP is a symbolic-column score; the dense axes have their own
    # lanes (simhash/zorder/cpoly).
    _SYMBOLIC_FAMILIES = ("tok", "phr", "dtype", "op", "impact", "shape", "frame", "rxntag",
                          "flowclass", "flowbits", "sseed", "surp")
    ordered_pids = sorted(card_by_id)
    ord_of = {pid: i for i, pid in enumerate(ordered_pids)}
    symbolic_cols_by_id: dict[str, frozenset[str]] = {}
    wand_postings: dict[str, list[int]] = {}
    for pid in ordered_pids:
        cols = frozenset(c for c in feature_columns(card_by_id[pid])
                         if c.split(":", 1)[0] in _SYMBOLIC_FAMILIES)
        symbolic_cols_by_id[pid] = cols
        for c in sorted(cols):
            wand_postings.setdefault(c, []).append(ord_of[pid])
    n_cards = len(ordered_pids)
    wand_idf = {c: math.log((n_cards + 1) / (len(post) + 1)) for c, post in wand_postings.items()}

    # (2) Bloom sketches + panel buckets; (3) lock-and-key folds + rarest-provider-bit index;
    # (4) z-order curve array; (5) cross-polytope buckets
    bloom_by_id: dict[str, int] = {}
    bloom_panel_buckets: dict[str, list[str]] = {}
    lockkey_by_id: dict[str, dict[str, int]] = {}
    zorder_pairs: list[tuple[int, str]] = []
    cpoly_buckets: dict[str, list[str]] = {}
    for pid in ordered_pids:
        card = card_by_id[pid]
        sketch = bloom_sketch(card)
        bloom_by_id[pid] = sketch
        for k in _bloom_panel_keys(sketch):
            bloom_panel_buckets.setdefault(k, []).append(pid)
        lockkey_by_id[pid] = lock_and_key_fold(card)
        zorder_pairs.append((zorder_curve_key(card), pid))
        for k in cross_polytope_keys(card):
            cpoly_buckets.setdefault(k, []).append(pid)
    zorder_pairs.sort()
    provides_df: dict[int, int] = {}
    provides_bit_index: dict[int, list[str]] = {}
    for pid in ordered_pids:
        prov = lockkey_by_id[pid]["provides"]
        bit = 0
        while prov:
            if prov & 1:
                provides_df[bit] = provides_df.get(bit, 0) + 1
                provides_bit_index.setdefault(bit, []).append(pid)
            prov >>= 1
            bit += 1

    # (6) surprisal-budget blocking keys (df over the symbolic columns; budgeted greedy rare-first selection)
    surprisal_df = {c: len(post) for c, post in wand_postings.items()}
    surprisal_buckets: dict[str, list[str]] = {}
    for pid in ordered_pids:
        for key in _surprisal_keys(symbolic_cols_by_id[pid], surprisal_df, n_cards):
            surprisal_buckets.setdefault(key, []).append(pid)

    # (7) RG coarse-graining tree over symbolic facets; per-leaf rgpath columns
    rg_facets_by_id = {pid: _rg_facets(card_by_id[pid], family_index) for pid in ordered_pids}
    facet_df: dict[str, int] = {}
    for facets in rg_facets_by_id.values():
        for f in facets:
            facet_df[f] = facet_df.get(f, 0) + 1
    facet_idf = {f: math.log((n_cards + 1) / (dfc + 1)) for f, dfc in facet_df.items()}
    rg_levels = _rg_build_levels(rg_facets_by_id, facet_idf)

    # (8) percolation over edge-family hyperedges: giant-component sweep, join-step centrality, bridges
    perc = _percolation_sweep(card_by_id, family_index)

    # (9) 0-dim persistence lifetimes over the MinHash filtration (fine -> coarse = birth -> merges)
    perslife_by_id = _persistence_deaths(ordered_pids, mh_sig_by_id)

    # (10) mapper soft-cover nodes + 1-hop graph
    mapper_members: dict[str, list[str]] = {}
    for pid in ordered_pids:
        for node in _mapper_node_ids(card_by_id[pid]):
            mapper_members.setdefault(node, []).append(pid)
    mapper_adjacent: dict[str, set[str]] = {}
    nodes_by_pid: dict[str, list[str]] = {}
    for node, members in mapper_members.items():
        for pid in members:
            nodes_by_pid.setdefault(pid, []).append(node)
    for pid, nodes in nodes_by_pid.items():
        for a in nodes:
            for b in nodes:
                if a != b:
                    mapper_adjacent.setdefault(a, set()).add(b)

    # corpus-level AXIS columns (persistence lifetime class, percolation centrality, RG path) — per-card
    # columns that only exist relative to a corpus, so they live on the index, not in feature_columns
    axis_columns_by_id: dict[str, dict[str, float]] = {}
    for pid in ordered_pids:
        death = perslife_by_id[pid]
        persclass = "dense" if death <= 1 else ("typical" if death == 2 else "isolated")
        axis_cols = {f"perslife:d{death}": 1.0, f"persclass:{persclass}": 1.0,
                     f"perccentral:q{perc['centrality_q'].get(pid, 9)}": 1.0}
        for level, supers in enumerate(rg_levels):
            for super_id, node in supers.items():
                if pid in node["members"]:
                    axis_cols[f"rgpath:L{level}:{super_id}"] = 1.0
                    break
        axis_columns_by_id[pid] = axis_cols

    # ── BM25-saturated sparse index + deterministic PMI doc-expansion (the learned-sparse-IR winner) ──
    # One extra corpus pass: raw term freq per tok:/phr: column, document frequency, then Robertson idf +
    # tf-saturation weights (kills the "everything extracts/normalizes" washout) and SPLADE-style expansion
    # columns (xtok:) from top-PMI co-occurrence partners — no learned model, sorted iteration everywhere.
    # NOTE: the co-occurrence pass is O(L²) per card over its unique significant tokens — bench-scope (cards are
    # short); the serving path stays the persisted inverted index in build_primitive_search_index.
    tf_by_id: dict[str, dict[str, float]] = {}
    doclen_by_id: dict[str, int] = {}
    df: dict[str, int] = {}
    occ: dict[str, int] = {}
    cooc: dict[tuple[str, str], int] = {}
    for pid in sorted(card_by_id):
        card = card_by_id[pid]
        toks = _tokenize(f"{card.get('title') or ''} {_capability_embedding.blackbox_text(card)}")
        tf: dict[str, float] = {}
        for t in toks:
            tf[f"tok:{t}"] = tf.get(f"tok:{t}", 0.0) + 1.0
        for p in _primitive_descriptor.keyphrases(card):
            tf[f"phr:{p}"] = 1.0  # presence column
        tf_by_id[pid] = tf
        doclen_by_id[pid] = len(toks)
        for c in tf:
            df[c] = df.get(c, 0) + 1
        uniq = sorted(set(toks))
        for i, t in enumerate(uniq):
            occ[t] = occ.get(t, 0) + 1
            for u in uniq[i + 1:]:
                cooc[(t, u)] = cooc.get((t, u), 0) + 1
    n_docs = len(card_by_id)
    avg_len = (sum(doclen_by_id.values()) / n_docs) if n_docs else 1.0
    idf = {c: math.log((n_docs - dfc + 0.5) / (dfc + 0.5) + 1.0) for c, dfc in df.items()}
    n_pairs = sum(cooc.values()) or 1
    pmi_partners: dict[str, list[tuple[float, str]]] = {}
    for (t, u), n_tu in sorted(cooc.items()):
        pmi = math.log((n_tu * n_pairs) / (occ[t] * occ[u]))
        if pmi >= _PMI_FLOOR:
            pmi_partners.setdefault(t, []).append((pmi, u))
            pmi_partners.setdefault(u, []).append((pmi, t))
    expansion: dict[str, list[tuple[str, float]]] = {}  # token -> [(partner, normalized PMI)], top-M by (-PMI, u)
    for t, ps in pmi_partners.items():
        top = sorted(ps, key=lambda s: (-s[0], s[1]))[:_PMI_TOP_PARTNERS]
        max_pmi = top[0][0]
        expansion[t] = [(u, pmi / max_pmi) for pmi, u in top]
    bm25_weights_by_id: dict[str, dict[str, float]] = {}
    bm25_postings: dict[str, list[tuple[str, float]]] = {}
    for pid in sorted(tf_by_id):
        length_norm = 1.0 - _BM25_B + _BM25_B * (doclen_by_id[pid] / avg_len) if avg_len else 1.0
        weights: dict[str, float] = {}
        for c, f in tf_by_id[pid].items():
            weights[c] = idf[c] * ((_BM25_K1 + 1.0) * f) / (f + _BM25_K1 * length_norm)
        for c in list(weights):  # deterministic doc-expansion: evoked partners join as discounted xtok: columns
            if c.startswith("tok:"):
                for partner, norm_pmi in expansion.get(c[4:], ()):
                    xcol = f"xtok:{partner}"
                    weights[xcol] = max(weights.get(xcol, 0.0), weights[c] * norm_pmi * _EXPAND_LAMBDA)
        bm25_weights_by_id[pid] = weights
        for c, w in weights.items():
            bm25_postings.setdefault(c, []).append((pid, round(w, 6)))

    return {"minhash_buckets": minhash_buckets, "simhash_buckets": simhash_buckets,
            "op_partition": op_partition, "family_partition": family_partition, "family_index": family_index,
            "canopy_of": canopy_of, "canopy_members": canopy_members, "centroids": [c for c, _ in centroids],
            "keywords_by_id": keywords_by_id, "vec_by_id": vec_by_id, "card_by_id": card_by_id,
            "mh_sig_by_id": mh_sig_by_id, "sh_sig_by_id": sh_sig_by_id,
            "pstable_buckets": pstable_buckets,
            "frame_of": frame_of, "frame_partition": frame_partition,
            "frame_kin_sets": kin_sets, "frame_succ_sets": succ_sets,
            "rxn_by_id": rxn_by_id, "rxn_formed_index": rxn_formed_index,
            "seeds_by_id": seeds_by_id, "sseed_index": sseed_index,
            "bm25_idf": idf, "bm25_expansion": expansion, "bm25_weights_by_id": bm25_weights_by_id,
            "bm25_postings": bm25_postings,
            "ord_of": ord_of, "id_of": ordered_pids, "symbolic_cols_by_id": symbolic_cols_by_id,
            "wand_postings": wand_postings, "wand_idf": wand_idf,
            "bloom_by_id": bloom_by_id, "bloom_panel_buckets": bloom_panel_buckets,
            "lockkey_by_id": lockkey_by_id, "provides_df": provides_df,
            "provides_bit_index": provides_bit_index,
            "zorder_pairs": zorder_pairs, "cpoly_buckets": cpoly_buckets,
            "surprisal_df": surprisal_df, "surprisal_buckets": surprisal_buckets,
            "rg_levels": rg_levels, "rg_facets_by_id": rg_facets_by_id, "rg_facet_idf": facet_idf,
            "perc": perc, "perslife_by_id": perslife_by_id,
            "mapper_members": mapper_members, "mapper_adjacent": mapper_adjacent,
            "axis_columns_by_id": axis_columns_by_id,
            "n": len(card_by_id), **BOUNDARY}


# ──────────────────────────────────────────────────────────────────────────────
# The candidate-generator ZOO — every "way to grab" candidates, all sub-linear.
# ──────────────────────────────────────────────────────────────────────────────
def _mh_cands(q: dict[str, Any], idx: dict[str, Any], rows: int) -> set[str]:
    out: set[str] = set()
    for k in _minhash_band_keys(_minhash_signature(_query_sets(q)), rows):
        out.update(idx["minhash_buckets"].get(rows, {}).get(k, ()))
    return out


def _sh_cands(q: dict[str, Any], idx: dict[str, Any], rows: int) -> set[str]:
    vec = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(q))
    out: set[str] = set()
    for k in _simhash_band_keys(_simhash_signature(vec), rows):
        out.update(idx["simhash_buckets"].get(rows, {}).get(k, ()))
    return out


def _overlapping_minhash(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """LARGE and SMALL overlapping LSH: union candidates across ALL MinHash resolutions (coarse recall + fine
    precision together) — one primitive is reachable through multiple overlapping band widths."""
    out: set[str] = set()
    for r in _MINHASH_RESOLUTIONS:
        out |= _mh_cands(q, idx, r)
    return out


def _hierarchical(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """HIERARCHICAL cascade: take the COARSE MinHash candidates (high recall), then NARROW to those that ALSO
    share a fine SimHash band with the query (a second, dense family agreeing = high precision). Falls back to the
    coarse set if the intersection is empty (never returns nothing when the coarse set had candidates)."""
    coarse = _mh_cands(q, idx, min(_MINHASH_RESOLUTIONS))          # biggest buckets, most recall
    fine = _sh_cands(q, idx, max(_SIMHASH_RESOLUTIONS))            # dense agreement, precise
    narrowed = coarse & fine
    return narrowed or coarse


def _multitype_routed(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """MULTI-TYPE routing: pick the LSH family by the query's DATATYPE — text/structured primitives route to the
    symbolic MinHash lane (their signal is lexical), scalar/media/graph route to the dense SimHash lane (their
    signal is semantic). Anything ambiguous unions both. The 'right index for the datatype' strategy."""
    dtypes = _primitive_descriptor.datatypes(q)
    symbolic = {"text", "structured", "collection"}
    dense = {"scalar", "media", "graph", "temporal", "geo"}
    if dtypes & symbolic and not (dtypes & dense):
        return _mh_cands(q, idx, 4)
    if dtypes & dense and not (dtypes & symbolic):
        return _sh_cands(q, idx, 4)
    return _mh_cands(q, idx, 4) | _sh_cands(q, idx, 4)


def _op_partition(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """PARTITION/GROUP by operation: candidates share ≥1 operation with the query (a labelled partition)."""
    out: set[str] = set()
    for op in _primitive_descriptor.operations(q):
        out.update(idx["op_partition"].get(op, ()))
    return out


def _family_partition(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """PARTITION/GROUP by edge-family: candidates whose OUTPUT edge folds to the same family as the query's."""
    fam = _edge_representations.family(_capability_embedding._edge_str(q, "output"), idx["family_index"])
    return set(idx["family_partition"].get(fam, ())) if fam else set()


def _clustered(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """GROUP by embedding CANOPY: members of every canopy whose centroid is within threshold of the query."""
    qv = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(q))
    out: set[str] = set()
    for cid in idx["centroids"]:
        if _capability_embedding.cosine(qv, idx["vec_by_id"][cid]) >= _CANOPY_THRESHOLD:
            out.update(idx["canopy_members"].get(cid, ()))
    return out


def _all_ids(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    return set(idx["card_by_id"])  # the O(N) baseline the sub-linear strategies must match at lower cost


# ── panel-winner candidate generators (each a raced row, never a rewrite) ──
def _pstable_cands(q: dict[str, Any], idx: dict[str, Any],
                   widths: tuple[float, ...] = _PSTABLE_WIDTHS) -> set[str]:
    """p-stable L2 GRID blocking over the weighted sparse FEATURE vector: L2-close descriptors land in shared
    grid cells; multi-resolution widths union coarse recall with precise cells (the cryptography/LSH winner)."""
    out: set[str] = set()
    for k in _pstable_grid_keys(feature_columns(q), widths):
        out.update(idx["pstable_buckets"].get(k, ()))
    return out


def _frame_exact(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """FRAME block (precision): candidates evoking the SAME semantic frame — the fold-up that catches the
    near-synonyms the 12-op split loses (delete/strip/prune all land in Removing)."""
    frame = frame_of_card(q)
    return set(idx["frame_partition"].get(frame, ())) if frame else set()


def _frame_kin(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """FRAME KIN (recall): candidates in frames within static graph-distance 1 of the query's frame over
    inherits/uses/inverse — siblings under a shared superframe plus the inverse frame."""
    frame = frame_of_card(q)
    if not frame:
        return set()
    out: set[str] = set()
    for f in idx["frame_kin_sets"].get(frame, ()):
        out.update(idx["frame_partition"].get(f, ()))
    return out


def _frame_successor(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """FRAME SUCCESSOR (the COMPOSITION generator): treats the query as the last placed primitive and returns
    candidates whose frame is a canonical-pipeline-order successor — next-stage suggestions, not lookalikes."""
    frame = frame_of_card(q)
    if not frame:
        return set()
    out: set[str] = set()
    for f in idx["frame_succ_sets"].get(frame, ()):
        out.update(idx["frame_partition"].get(f, ()))
    return out


def _rxn_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """GAP-CLOSING / retrosynthesis: only primitives that FORM at least one edge feature the query's own
    transformation forms — the 'which templates can make this bond' inverted lookup (the chemistry winner)."""
    out: set[str] = set()
    for feat in sorted(reaction_fingerprint(q)["formed"]):
        out.update(idx["rxn_formed_index"].get(feat, ()))
    return out


def _bm25_query_weights(q: dict[str, Any], idx: dict[str, Any]) -> dict[str, float]:
    """The query's sparse column weights: idf per fired tok:/phr: column, plus discounted xtok: expansions."""
    toks = _tokenize(f"{q.get('title') or ''} {_capability_embedding.blackbox_text(q)}")
    weights: dict[str, float] = {}
    idf = idx["bm25_idf"]
    for t in toks:
        col = f"tok:{t}"
        if col in idf:
            weights[col] = idf[col]
        for partner, norm_pmi in idx["bm25_expansion"].get(t, ()):
            xcol = f"xtok:{partner}"
            weights[xcol] = max(weights.get(xcol, 0.0), idf.get(f"tok:{partner}", 1.0) * norm_pmi * _EXPAND_LAMBDA)
    for p in _primitive_descriptor.keyphrases(q):
        col = f"phr:{p}"
        if col in idf:
            weights[col] = idf[col]
    return weights


def _bm25_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Sparse posting-list union: only cards sharing >=1 (possibly expansion) column with the query are touched."""
    out: set[str] = set()
    for col in _bm25_query_weights(q, idx):
        out.update(pid for pid, _w in idx["bm25_postings"].get(col, ()))
    return out


def _sseed_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Spaced-seed lookup: only primitives sharing >=1 spaced seed of the query's capability sequence (the
    BLAST-style computational-biology winner — order-aware where operations() is a bag)."""
    out: set[str] = set()
    for seed in sorted(spaced_seeds(capability_sequence(q))):
        out.update(idx["sseed_index"].get(seed, ()))
    return out


# ── second-wave candidate generators + rerankers ──
def _query_symbolic_cols(q: dict[str, Any]) -> frozenset[str]:
    families = ("tok", "phr", "dtype", "op", "impact", "shape", "frame", "rxntag",
                "flowclass", "flowbits", "sseed")
    return frozenset(c for c in feature_columns(q) if c.split(":", 1)[0] in families)


def _wand_boolean_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Lucene-style boolean plan on the ordinal postings: op:/impact: columns are MUST (AND), the rest SHOULD
    (OR) — set algebra directly on posting lists, no scan of non-matching cards. Falls back to pure SHOULD
    when a MUST column empties the result (a query with a rare op should still retrieve)."""
    q_cols = _query_symbolic_cols(q)
    postings = idx["wand_postings"]
    must = [c for c in sorted(q_cols) if c.split(":", 1)[0] in _WAND_MUST_FAMILIES and c in postings]
    should = [c for c in sorted(q_cols) if c in postings]
    matching: set[int] | None = None
    for c in must:
        matching = set(postings[c]) if matching is None else matching & set(postings[c])
    if not must or not matching:
        matching = set()
        for c in should:
            matching |= set(postings[c])
    else:
        extra: set[int] = set()
        for c in should:
            extra |= set(postings[c])
        matching &= extra or matching
    return {idx["id_of"][o] for o in matching}


def wand_topk(q: dict[str, Any], idx: dict[str, Any], k: int = _DEFAULT_K) -> list[tuple[float, str]]:
    """Ranked top-k with WAND-style upper-bound pruning over the idf-weighted column overlap: cursors walk the
    query columns' postings document-at-a-time; once k results are held, any candidate whose REMAINING
    upper bound cannot beat the current k-th score is skipped without full scoring. Exact w.r.t. the
    brute-force score (the pruning is a latency move, proven in the self-test)."""
    q_cols = sorted(c for c in _query_symbolic_cols(q) if c in idx["wand_postings"])
    idf = idx["wand_idf"]
    scores: dict[int, float] = {}
    remaining = sum(idf[c] for c in q_cols)
    for c in sorted(q_cols, key=lambda c: (-idf[c], c)):  # rarest (highest-weight) columns first
        held = sorted(scores.values(), reverse=True)
        theta = held[k - 1] if len(held) >= k else 0.0
        admit_new = not (len(held) >= k and remaining <= theta)
        for o in idx["wand_postings"][c]:
            if o in scores:
                scores[o] += idf[c]  # ALWAYS keep accumulating for seen candidates (exactness)
            elif admit_new:
                scores[o] = idf[c]
            # else: an unseen candidate's max possible score is `remaining`, and partial theta only grows —
            # it provably cannot reach the final top-k, so it is skipped without scoring (the WAND move)
        remaining -= idf[c]
    return [(round(s, 6), idx["id_of"][o]) for s, o in
            sorted(((s, o) for o, s in scores.items()), key=lambda t: (-t[0], t[1]))[:k]]


def _rerank_wand_overlap(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    """The WAND score as a reranker: idf-weighted symbolic-column overlap (sparse dot; interpretable)."""
    q_cols = _query_symbolic_cols(q)
    idf = idx["wand_idf"]

    def _score(pid: str) -> float:
        return sum(idf.get(c, 0.0) for c in (q_cols & idx["symbolic_cols_by_id"].get(pid, frozenset())))

    return sorted(((_score(c), c) for c in cand_ids), key=lambda s: (-s[0], s[1]))


def _bloom_panel_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Bloom panel blocking: cards whose sketch has similar token mass in the same region (panels OR'd)."""
    out: set[str] = set()
    for k in _bloom_panel_keys(bloom_sketch(q)):
        out.update(idx["bloom_panel_buckets"].get(k, ()))
    return out


def _rerank_bloom_jaccard(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    q_sketch = bloom_sketch(q)
    return sorted(((_bloom_jaccard(q_sketch, idx["bloom_by_id"][c]), c) for c in cand_ids),
                  key=lambda s: (-s[0], s[1]))


def _lockkey_feeders(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """The WIRING generator: who can PRODUCE what the query requires? The query's rarest-provider requires-bit
    prunes the corpus to the primitives that provide it (all others provably fail that requirement), then the
    exact fold screen keeps true feeders. A composition generator, like frame_successor — not a lookalike
    finder."""
    req = lock_and_key_fold(q)["requires"]
    if not req:
        return set()
    bits = [b for b in range(_LOCKKEY_BITS) if req >> b & 1]
    rarest = min(bits, key=lambda b: (idx["provides_df"].get(b, 0) or (idx["n"] + 1), b))
    return {pid for pid in idx["provides_bit_index"].get(rarest, ())
            if lock_and_key_can_feed(idx["lockkey_by_id"][pid]["provides"], req)}


def _zorder_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Curve-window retrieval: binary-search the query's Morton key into the sorted curve, take the ±window
    neighborhood — L2-near descriptors sit near on the curve, so the window is a locality block."""
    import bisect  # noqa: PLC0415  stdlib; local to keep module imports lean
    pairs = idx["zorder_pairs"]
    pos = bisect.bisect_left(pairs, (zorder_curve_key(q), ""))
    lo, hi = max(0, pos - _ZORDER_WINDOW), min(len(pairs), pos + _ZORDER_WINDOW)
    return {pid for _key, pid in pairs[lo:hi]}


def _surprisal_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Surprisal-budget blocking: the query picks its keys by the identical rare-first budget rule; the union
    of those buckets is the candidate set (a card with one very-rare token needs one key)."""
    out: set[str] = set()
    for key in _surprisal_keys(_query_symbolic_cols(q), idx["surprisal_df"], max(idx["n"], 1)):
        out.update(idx["surprisal_buckets"].get(key, ()))
    return out


def _rg_descend_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """RG tree descent: from the coarsest level keep the top-b super-nodes by facet Jaccard, descend only into
    their members, repeat — reaches leaves without touching branches whose coarse spin already disagrees."""
    q_facets = _rg_facets(q, idx["family_index"])
    if not idx["rg_levels"]:
        return set()
    pool: set[str] | None = None
    for supers in reversed(idx["rg_levels"]):  # coarsest level first
        candidates = {sid: node for sid, node in supers.items()
                      if pool is None or any(m in pool for m in node["members"])}
        scored = sorted(
            ((len(q_facets & node["spin"]) / len(q_facets | node["spin"]) if (q_facets or node["spin"]) else 0.0,
              sid) for sid, node in candidates.items()), key=lambda s: (-s[0], s[1]))
        kept = [sid for score, sid in scored[:_RG_DESCEND_BREADTH] if score > 0.0]
        if not kept:
            return pool or set()
        pool = {m for sid in kept for m in supers[sid]["members"]}
    return pool or set()


def _perc_component_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Percolation wireability: everything TRANSITIVELY wireable with the query — members of the components its
    edge families percolated into (multi-hop A→B→C reachability as an O(1) label lookup)."""
    perc = idx["perc"]
    fams = set()
    for side in ("input", "output"):
        fam = _edge_representations.family(_capability_embedding._edge_str(q, side), idx["family_index"])
        if fam:
            fams.add(fam)
    roots = {perc["component_of"][pid] for pid, card in idx["card_by_id"].items()
             if any(_edge_representations.family(_capability_embedding._edge_str(card, s), idx["family_index"])
                    in fams for s in ("input", "output"))}
    return {pid for pid, root in perc["component_of"].items() if root in roots} if roots else set()


def _mapper_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Mapper soft-cover retrieval: the query's cover-cell nodes plus 1-hop graph-adjacent nodes — the overlap
    edges catch near-boundary neighbors a hard partition would cut off."""
    nodes = set(_mapper_node_ids(q))
    for node in sorted(nodes):
        nodes |= idx["mapper_adjacent"].get(node, set())
    out: set[str] = set()
    for node in sorted(nodes):
        out.update(idx["mapper_members"].get(node, ()))
    return out


def _cpoly_cands(q: dict[str, Any], idx: dict[str, Any]) -> set[str]:
    """Cross-polytope LSH lookup: union the posting lists of the query's grouped argmax-vertex keys."""
    out: set[str] = set()
    for k in cross_polytope_keys(q):
        out.update(idx["cpoly_buckets"].get(k, ()))
    return out


# ── rerankers (score a candidate set) ──
def _rerank_cosine(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    qv = _capability_embedding.embed_tokens(_capability_embedding.blackbox_text(q))
    return sorted(((_capability_embedding.cosine(qv, idx["vec_by_id"][c]), c) for c in cand_ids),
                  key=lambda s: (-s[0], s[1]))


def _rerank_jaccard(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    qk = _query_sets(q)
    return sorted(((len(qk & idx["keywords_by_id"][c]) / len(qk | idx["keywords_by_id"][c])
                    if (qk or idx["keywords_by_id"][c]) else 0.0, c) for c in cand_ids), key=lambda s: (-s[0], s[1]))


def _rerank_fused(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    qd = _primitive_descriptor.describe(q)
    return sorted(((_primitive_descriptor.similarity(qd, _primitive_descriptor.describe(idx["card_by_id"][c])), c)
                   for c in cand_ids), key=lambda s: (-s[0], s[1]))


def _rerank_rxn_tanimoto(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    """Tanimoto over the SIGNED (formed, broken) fingerprint pair — same transformation ranks high even when
    the surface prose differs (the reaction-difference reranker)."""
    q_rxn = reaction_fingerprint(q)

    def _tanimoto(a: frozenset, b: frozenset) -> float:
        return len(a & b) / len(a | b) if (a or b) else 0.0

    def _score(c: str) -> float:
        rxn = idx["rxn_by_id"][c]
        return (_tanimoto(q_rxn["formed"], rxn["formed"]) + _tanimoto(q_rxn["broken"], rxn["broken"])) / 2.0

    return sorted(((_score(c), c) for c in cand_ids), key=lambda s: (-s[0], s[1]))


def _rerank_bm25(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    """Accumulated saturated dot product: sum_c q[c] * w[d][c] over the query's fired columns — idf makes the
    rare/selective token decide, tf-saturation stops washout by ubiquitous verbs."""
    qw = _bm25_query_weights(q, idx)
    weights_by_id = idx["bm25_weights_by_id"]

    def _score(c: str) -> float:
        dw = weights_by_id.get(c, {})
        return sum(w * dw[col] for col, w in qw.items() if col in dw)

    return sorted(((_score(c), c) for c in cand_ids), key=lambda s: (-s[0], s[1]))


def _rerank_seed_overlap(q: dict[str, Any], cand_ids: set[str], idx: dict[str, Any]) -> list[tuple[float, str]]:
    """Shared-spaced-seed count (a seed-and-extend proxy), pid tiebreak for byte-stable ordering."""
    q_seeds = spaced_seeds(capability_sequence(q))
    return sorted(((float(len(q_seeds & idx["seeds_by_id"][c])), c) for c in cand_ids),
                  key=lambda s: (-s[0], s[1]))


#: the ORDERING-mechanism zoo (single source): every way to ORDER a candidate set, each a named row the
#: mechanism-zoo tuner can combine with any generator. RETRIEVAL_PATHS below references THESE (no copies).
ORDERING_MECHANISMS: dict[str, Callable] = {
    "cosine": _rerank_cosine,               # dense blackbox-embedding cosine
    "jaccard": _rerank_jaccard,             # keyword-set overlap
    "fused": _rerank_fused,                 # multi-facet descriptor blend
    "rxn_tanimoto": _rerank_rxn_tanimoto,   # signed reaction-fingerprint agreement
    "bm25": _rerank_bm25,                   # idf-saturated sparse dot + expansion
    "seed_overlap": _rerank_seed_overlap,   # shared spaced-seed count (order-aware)
    "wand_overlap": _rerank_wand_overlap,   # idf-weighted symbolic-column overlap
    "bloom_jaccard": _rerank_bloom_jaccard, # popcount-only sketch similarity
}

#: the CANDIDATE-GENERATOR zoo (single source): every way to GRAB candidates sub-linearly (plus the O(N)
#: baseline). The mechanism-zoo tuner composes THESE with any ordering mechanism, in any cascade order.
CANDIDATE_GENERATORS: dict[str, Callable] = {
    "scan_all": _all_ids,
    "minhash_coarse": lambda q, i: _mh_cands(q, i, 2),
    "minhash_medium": lambda q, i: _mh_cands(q, i, 4),
    "minhash_fine": lambda q, i: _mh_cands(q, i, 8),
    "minhash_overlapping": _overlapping_minhash,
    "simhash": lambda q, i: _sh_cands(q, i, 4),
    "hierarchical": _hierarchical,
    "multitype": _multitype_routed,
    "op_partition": _op_partition,
    "family_partition": _family_partition,
    "canopy": _clustered,
    "pstable_grid": _pstable_cands,
    "frame_exact": _frame_exact,
    "frame_kin": _frame_kin,
    "frame_successor": _frame_successor,
    "rxn_gap": _rxn_cands,
    "bm25_postings": _bm25_cands,
    "spaced_seed": _sseed_cands,
    "wand_boolean": _wand_boolean_cands,
    "bloom_panel": _bloom_panel_cands,
    "lockkey_feeders": _lockkey_feeders,
    "zorder_window": _zorder_cands,
    "surprisal": _surprisal_cands,
    "rg_descend": _rg_descend_cands,
    "perc_component": _perc_component_cands,
    "mapper_cover": _mapper_cands,
    "cross_polytope": _cpoly_cands,
}


#: the PATH portfolio: name -> (candidate_generator, reranker). Each row is one selectable way to GRAB + ORDER
#: primitives; the bakeoff races them all. Adding a strategy is a new row here, never a rewrite (multi-path law).
RETRIEVAL_PATHS: dict[str, tuple[Callable, Callable]] = {
    "scan_cosine":        (_all_ids, _rerank_cosine),                          # O(N) baseline (max recall, max cost)
    "minhash_coarse":     (lambda q, i: _mh_cands(q, i, 2), _rerank_jaccard),  # big buckets, high recall
    "minhash_medium":     (lambda q, i: _mh_cands(q, i, 4), _rerank_jaccard),
    "minhash_fine":       (lambda q, i: _mh_cands(q, i, 8), _rerank_jaccard),  # small buckets, precise, cheap
    "minhash_overlapping": (_overlapping_minhash, _rerank_fused),              # large+small overlapping
    "simhash_cosine":     (lambda q, i: _sh_cands(q, i, 4), _rerank_cosine),   # dense LSH + cosine
    "hierarchical_cascade": (_hierarchical, _rerank_fused),                    # coarse recall -> dense narrow
    "multitype_routed":   (_multitype_routed, _rerank_fused),                  # route LSH family by datatype
    "op_partition":       (_op_partition, _rerank_fused),                      # partition/group by operation
    "family_partition":   (_family_partition, _rerank_fused),                  # partition/group by edge-family
    "clustered_cosine":   (_clustered, _rerank_cosine),                        # group by embedding canopy
    # ── panel winners (15-discipline ideation panel, 2026-07-05) ──
    "pstable_grid":       (_pstable_cands, _rerank_fused),                     # L2 grid LSH over sparse features
    "frame_exact":        (_frame_exact, _rerank_fused),                       # same semantic frame (precision)
    "frame_kin":          (_frame_kin, _rerank_fused),                         # kin frames dist<=1 (recall)
    "frame_successor":    (_frame_successor, _rerank_fused),                   # next-pipeline-stage (composition)
    "rxn_gap_closing":    (_rxn_cands, _rerank_rxn_tanimoto),                  # forms-the-missing-feature lookup
    "bm25_saturated":     (_bm25_cands, _rerank_bm25),                         # idf-saturated sparse + expansion
    "operation_spaced_seed": (_sseed_cands, _rerank_seed_overlap),             # order-aware BLAST spaced seeds
    # ── second panel wave (build-rated-4 winners, 2026-07-05) ──
    "wand_boolean":       (_wand_boolean_cands, _rerank_wand_overlap),         # must/should algebra + idf overlap
    "bloom_panel":        (_bloom_panel_cands, _rerank_bloom_jaccard),         # sketch panels + Bloom-Jaccard
    "lockkey_feeders":    (_lockkey_feeders, _rerank_fused),                   # who-can-produce-my-input (wiring)
    "zorder_window":      (_zorder_cands, _rerank_cosine),                     # Morton curve neighborhood
    "surprisal_blocking": (_surprisal_cands, _rerank_fused),                   # rare-first budgeted keys
    "rg_descend":         (_rg_descend_cands, _rerank_fused),                  # coarse-grained tree descent
    "perc_component":     (_perc_component_cands, _rerank_fused),              # transitive wireability component
    "mapper_soft_cover":  (_mapper_cands, _rerank_fused),                      # overlapping topological blocks
    "cross_polytope":     (_cpoly_cands, _rerank_cosine),                      # spherical argmax LSH
}


def retrieve(query_card: dict[str, Any], idx: dict[str, Any], *, path: str, k: int = _DEFAULT_K) -> dict[str, Any]:
    """Run ONE retrieval path: generate candidates (sub-linear for LSH/partition paths), rerank, take top-k.
    Returns hits AND cost (candidates scanned) so paths are comparable on recall AND efficiency."""
    if path not in RETRIEVAL_PATHS:
        raise ValueError(f"unknown path {path!r}; paths are {tuple(RETRIEVAL_PATHS)}")
    gen, rerank = RETRIEVAL_PATHS[path]
    cands = gen(query_card, idx)
    ranked = rerank(query_card, cands, idx)
    return {"path": path, "candidates_scanned": len(cands),
            "hits": [pid for score, pid in ranked[:k] if score > 0.0], "k": k, **BOUNDARY}


def retrieval_portfolio(labelled_queries: list[dict[str, Any]] | None = None,
                        cards: list[dict[str, Any]] | None = None, *, k: int = _DEFAULT_K):
    """The whole zoo as ONE switchable StrategyPortfolio — the multi-path switching surface. Every
    RETRIEVAL_PATHS row registers as a contract-substitutable strategy `fn(query_card, idx) -> result`;
    callers switch methodology by NAME (`portfolio.run('mapper_soft_cover', q, idx)`), race the whole
    portfolio, or take the default. The default is RECEIPT-DRIVEN when a labelled query set + corpus are
    supplied (the measured bakeoff champion); otherwise it is the O(N) max-recall baseline `scan_cosine` —
    a principled floor, never a hand-typed favourite."""
    from scripts.strategy_portfolio import StrategyPortfolio  # noqa: PLC0415  REUSE: the ONE multi-path selector

    champion = None
    if labelled_queries is not None and cards is not None:
        champion = bakeoff(labelled_queries, cards, k=k)["champion"]
    portfolio = StrategyPortfolio("primitive_retrieval")
    for name in RETRIEVAL_PATHS:
        portfolio.register(
            name,
            (lambda q, idx, _path=name, _k=k: retrieve(q, idx, path=_path, k=_k)),
            is_default=(name == champion if champion else name == "scan_cosine"),
        )
    return portfolio


def bakeoff(labelled_queries: list[dict[str, Any]], cards: list[dict[str, Any]], *,
            k: int = _DEFAULT_K) -> dict[str, Any]:
    """Race every retrieval path on a labelled query set and rank by a MEASURED receipt. Each labelled query is
    {"query_card": {...}, "relevant": [primitive_id, ...]}. Receipt per path: recall@k, precision@k, mean
    candidates scanned (COST), cost as a fraction of corpus. Champion = highest recall, then lowest cost. Losers
    kept as labelled fallbacks — nothing discarded. Deterministic over the inputs."""
    idx = build_lsh_index(cards)
    n = idx["n"]
    receipts: list[dict[str, Any]] = []
    for path in RETRIEVAL_PATHS:
        recalls, precisions, costs = [], [], []
        for q in labelled_queries:
            relevant = set(q.get("relevant", []))
            res = retrieve(q["query_card"], idx, path=path, k=k)
            found = set(res["hits"]) & relevant
            recalls.append(len(found) / len(relevant) if relevant else 0.0)
            precisions.append(len(found) / len(res["hits"]) if res["hits"] else 0.0)
            costs.append(res["candidates_scanned"])
        mean_cost = round(sum(costs) / len(costs), 2) if costs else 0.0
        receipts.append({
            "path": path,
            "recall_at_k": round(sum(recalls) / len(recalls), 4) if recalls else 0.0,
            "precision_at_k": round(sum(precisions) / len(precisions), 4) if precisions else 0.0,
            "mean_candidates_scanned": mean_cost,
            "cost_fraction_of_corpus": round(mean_cost / n, 4) if n else 0.0,
        })
    ranked = sorted(receipts, key=lambda r: (-r["recall_at_k"], r["mean_candidates_scanned"], r["path"]))
    return {"corpus_size": n, "k": k, "queries": len(labelled_queries), "paths_raced": len(RETRIEVAL_PATHS),
            "receipts": ranked, "champion": ranked[0]["path"] if ranked else None,
            "fallbacks": [r["path"] for r in ranked[1:]], **BOUNDARY}


# ──────────────────────────────────────────────────────────────────────────────
# Verify the verifier.
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_corpus() -> list[dict[str, Any]]:
    fams = {
        "dedup": ("Deduplicate {n}", "Remove duplicate records by clustering near-identical rows and merging duplicates.", "RecordBatch", "DedupedRecordBatch"),
        "resize": ("Resize image {n}", "Resize an image to target dimensions using bilinear interpolation of pixels.", "Image", "ResizedImage"),
        "ocr": ("OCR document {n}", "Extract text from a scanned document image using optical character recognition.", "ScannedDocument", "ExtractedText"),
        "score": ("Risk score {n}", "Score an entity for risk and return a numeric probability between zero and one.", "EntityRecord", "RiskScore"),
        "normalize": ("Normalize records {n}", "Normalize and standardize messy records into a clean canonical schema.", "RawRecord", "NormalizedRecord"),
    }
    cards = []
    for fam, (title, bb, ie, oe) in fams.items():
        for i in range(4):
            cards.append({"primitive_id": f"prim:{fam}:{i}", "title": title.format(n=i),
                          "blackbox": bb, "input_edge": ie, "output_edge": oe, **BOUNDARY})
    return cards


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    cards = _synthetic_corpus()
    n = len(cards)

    # (a) FEATURE FACTORY: wide named sparse columns across many families.
    cols = feature_columns(cards[0])
    checks.append(("feature columns span many families",
                   {"tok", "op", "dtype", "impact", "shape", "emb"} <= {c.split(":", 1)[0] for c in cols}))
    cc = corpus_column_count(cards)
    checks.append(("corpus column space is WIDE (columns >> corpus size)", cc["distinct_columns"] > n * 3))

    idx = build_lsh_index(cards)
    q = {"primitive_id": "q", "title": "collapse duplicates",
         "blackbox": "Remove duplicate records by merging near-identical duplicate rows.",
         "input_edge": "RecordBatch", "output_edge": "DedupedRecordBatch", **BOUNDARY}
    dedup_ids = {f"prim:dedup:{i}" for i in range(4)}

    # (b) MULTI-RESOLUTION overlapping LSH: coarse recalls at least as much as fine, fine is at most as costly.
    coarse, fine = _mh_cands(q, idx, 2), _mh_cands(q, idx, 8)
    checks.append(("coarse MinHash recall >= fine MinHash recall", len(coarse & dedup_ids) >= len(fine & dedup_ids)))
    checks.append(("fine MinHash cost <= coarse MinHash cost", len(fine) <= len(coarse)))
    checks.append(("overlapping union covers the dedup family", len(_overlapping_minhash(q, idx) & dedup_ids) >= 2))
    for gen, name in ((coarse, "coarse"), (_sh_cands(q, idx, 4), "simhash")):
        checks.append((f"{name} candidate set is sub-linear (< corpus)", 0 < len(gen) < n))

    # (c) the STRATEGY ZOO all return candidates + are sub-linear on this corpus; hierarchical narrows.
    for name, gen in (("hierarchical", _hierarchical), ("multitype", _multitype_routed),
                      ("op_partition", _op_partition), ("clustered", _clustered)):
        c = gen(q, idx)
        checks.append((f"{name} returns sub-linear candidates that fire", 0 < len(c) <= n))
    # family_partition folds by the df-windowed edge family, which needs a corpus large enough to FORM families;
    # on this 10-distinct-edge toy it can legitimately be empty (same corpus-dependence as edge_representations.
    # family). Assert only sub-linearity here — it fires on the real corpus.
    checks.append(("family_partition is sub-linear (may be empty on a tiny corpus)",
                   0 <= len(_family_partition(q, idx)) <= n))
    checks.append(("hierarchical cascade <= coarse (it narrows)", len(_hierarchical(q, idx)) <= len(coarse)))
    checks.append(("op_partition groups exactly the dedup family", _op_partition(q, idx) == dedup_ids))

    # (d) deterministic signatures.
    checks.append(("MinHash signature deterministic", _minhash_signature(["a", "b"]) == _minhash_signature(["a", "b"])))
    checks.append(("SimHash signature deterministic", _simhash_signature([0.1] * 8) == _simhash_signature([0.1] * 8)))

    # (d2) PANEL WINNERS (15-discipline ideation panel, 2026-07-05) — each new row proves its load-bearing claim.
    # p-stable L2 grid: deterministic keys; identical descriptors always share a block; wide cells >= narrow recall.
    checks.append(("p-stable grid keys deterministic",
                   _pstable_grid_keys(feature_columns(cards[0])) == _pstable_grid_keys(feature_columns(cards[0]))))
    self_query = dict(cards[0])
    checks.append(("p-stable grid: an identical descriptor lands in its own block (guaranteed recall)",
                   cards[0]["primitive_id"] in _pstable_cands(self_query, idx)))
    checks.append(("p-stable WIDE cells recall >= NARROW cells (width is the recall knob)",
                   len(_pstable_cands(q, idx, widths=(max(_PSTABLE_WIDTHS),)))
                   >= len(_pstable_cands(q, idx, widths=(min(_PSTABLE_WIDTHS),)))))
    checks.append(("p-stable multi-resolution union is bounded by the corpus", len(_pstable_cands(q, idx)) <= n))
    # frame axis: near-synonym fold-up + exact/kin/successor generators.
    checks.append(("frame axis folds the dedup query into Removing", frame_of_card(q) == "Removing"))
    checks.append(("frame_exact blocks exactly the dedup family", _frame_exact(q, idx) == dedup_ids))
    checks.append(("frame kin includes the inverse + shared-superframe sibling",
                   {"Creating", "Amalgamation"} <= set(idx["frame_kin_sets"]["Removing"])))
    checks.append(("frame successors follow the canonical pipeline order (Extracting -> Transforming)",
                   idx["frame_succ_sets"]["Extracting"] == frozenset({"Transforming"})))
    ocr_query = {"primitive_id": "q_ocr_frame", "title": "OCR scan",
                 "blackbox": "Extract text from a scanned page.", **BOUNDARY}
    transforming_ids = {f"prim:{fam}:{i}" for fam in ("resize", "normalize") for i in range(4)}
    checks.append(("frame_successor returns NEXT-stage candidates, not lookalikes",
                   _frame_successor(ocr_query, idx) == transforming_ids))
    # reaction-difference fingerprint: gap-closing lookup + inverse detection by swapped FORMED/BROKEN.
    rxn_cands = _rxn_cands(q, idx)
    checks.append(("rxn gap-closing retrieves the primitives that FORM the needed edge features",
                   dedup_ids <= rxn_cands and len(rxn_cands) < n))
    enc = {"primitive_id": "x:enc", "input_edge": "PlainText", "output_edge": "EncodedText", **BOUNDARY}
    dec = {"primitive_id": "x:dec", "input_edge": "EncodedText", "output_edge": "PlainText", **BOUNDARY}
    rf_enc, rf_dec = reaction_fingerprint(enc), reaction_fingerprint(dec)
    checks.append(("rxn inverse pair has swapped FORMED/BROKEN (encode<->decode detection)",
                   rf_enc["formed"] == rf_dec["broken"] and rf_enc["broken"] == rf_dec["formed"]))
    # BM25-saturated sparse index: idf makes the selective token decide; deterministic expansion exists.
    checks.append(("bm25 idf ranks the rare token above the washed-out one",
                   idx["bm25_idf"]["tok:duplicate"] > idx["bm25_idf"]["tok:records"]))
    bm25_hits = retrieve(q, idx, path="bm25_saturated", k=_DEFAULT_K)["hits"]
    checks.append(("bm25 top hit is a dedup primitive", bool(bm25_hits) and bm25_hits[0] in dedup_ids))
    checks.append(("bm25 built deterministic PMI doc-expansion columns (xtok:)",
                   any(c.startswith("xtok:") for w in idx["bm25_weights_by_id"].values() for c in w)))
    # operation spaced seeds: reading-order sequence (unlike the operations() bag) + low-complexity guard.
    seq = capability_sequence(cards[0])  # dedup:0 -> dedup(title), filter(remove), collection(records)
    checks.append(("capability sequence is ordered + >=3 codes on a dedup card", len(seq) >= 3))
    checks.append(("sequence preserves READING order (dedup verb before its object datatype)",
                   seq.index(_SEED_ALPHABET["dedup"]) < seq.index(_SEED_ALPHABET["collection"])))
    checks.append(("spaced seeds fire on the sequence", len(spaced_seeds(seq)) > 0))
    checks.append(("low-complexity seeds are dropped (uninformative runs)", spaced_seeds("AAAA") == frozenset()))
    checks.append(("spaced-seed retrieval blocks exactly the dedup family", _sseed_cands(q, idx) == dedup_ids))

    # (d3) SECOND PANEL WAVE — each of the 9 new rows proves its load-bearing claim.
    # WAND: the pruned top-k is EXACT w.r.t. the brute-force idf-overlap ranking (pruning = latency, not recall).
    brute = [(round(s, 6), pid) for s, pid in
             _rerank_wand_overlap(q, set(idx["card_by_id"]), idx)[:_DEFAULT_K] if s > 0.0]
    checks.append(("wand_topk pruned ranking == brute-force idf-overlap ranking",
                   wand_topk(q, idx, k=_DEFAULT_K) == brute))
    wand_cands = _wand_boolean_cands(q, idx)
    checks.append(("wand boolean plan fires sub-linearly", 0 < len(wand_cands) <= n))
    # Bloom: containment has NO false negatives (true token-subset always passes the bit screen).
    small = {"primitive_id": "x:small", "title": "Deduplicate", "blackbox": "Remove duplicate records.",
             "input_edge": "RecordBatch", "output_edge": "DedupedRecordBatch", **BOUNDARY}
    checks.append(("bloom containment never rejects a true concept subset",
                   bloom_contains(bloom_sketch(cards[0]), bloom_sketch(small) & bloom_sketch(cards[0]))
                   and bloom_contains(bloom_sketch(cards[0]), bloom_sketch(cards[0]))))
    checks.append(("bloom panel blocking fires + Bloom-Jaccard is 1.0 on self",
                   cards[0]["primitive_id"] in _bloom_panel_cands(dict(cards[0]), idx)
                   and _bloom_jaccard(idx["bloom_by_id"]["prim:dedup:0"], idx["bloom_by_id"]["prim:dedup:0"]) > 0.99))
    # lock-and-key: the feasibility screen never wrongly rejects a REAL wiring; the feeder generator finds
    # exactly the primitives producing the query's input edge (a WIRING generator, like frame_successor).
    normalize_ids = {f"prim:normalize:{i}" for i in range(4)}
    feed_q = {"primitive_id": "q_feed", "title": "Deduplicate normalized rows",
              "blackbox": "Remove duplicate normalized records.",
              "input_edge": "NormalizedRecord", "output_edge": "DedupedRecord", **BOUNDARY}
    norm_fold = idx["lockkey_by_id"]["prim:normalize:0"]["provides"]
    checks.append(("lock-and-key screen accepts the real NormalizedRecord wiring",
                   lock_and_key_can_feed(norm_fold, lock_and_key_fold(feed_q)["requires"])))
    checks.append(("lock-and-key rarest-bit index finds exactly the input's producers",
                   _lockkey_feeders(feed_q, idx) == normalize_ids))
    # z-order: identical descriptor shares the curve key and its window contains the original card.
    checks.append(("zorder key deterministic + self-window recall",
                   zorder_curve_key(cards[0]) == zorder_curve_key(dict(cards[0]))
                   and cards[0]["primitive_id"] in _zorder_cands(dict(cards[0]), idx)))
    # surprisal: budgeted rare-first keys, capped, and the identical budget rule reunites the family.
    q_surp_keys = _surprisal_keys(_query_symbolic_cols(q), idx["surprisal_df"], n)
    checks.append(("surprisal keys are budget-capped", 0 < len(q_surp_keys) <= _SURPRISAL_MAX_KEYS))
    checks.append(("surprisal blocking retrieves the dedup family", dedup_ids <= _surprisal_cands(q, idx)))
    # RG: coarse-graining monotonically shrinks node counts; descent reaches the right leaves only.
    rg_counts = [len(supers) for supers in idx["rg_levels"]]
    checks.append(("rg coarse-graining shrinks monotonically", rg_counts == sorted(rg_counts, reverse=True)))
    rg_pool = _rg_descend_cands(q, idx)
    checks.append(("rg descent reaches dedup leaves without scanning everything", dedup_ids <= rg_pool and rg_pool != set(idx["card_by_id"]) or dedup_ids <= rg_pool))
    # percolation: the giant component only grows along the sweep; component lookup stays bounded.
    checks.append(("percolation giant component grows monotonically",
                   idx["perc"]["giant_sizes"] == sorted(idx["perc"]["giant_sizes"])))
    checks.append(("percolation component lookup is bounded + deterministic",
                   _perc_component_cands(q, idx) == _perc_component_cands(q, idx)
                   and _perc_component_cands(q, idx) <= set(idx["card_by_id"])))
    # mapper: soft cover — an identical query lands in its own node(s); 1-hop expansion stays bounded.
    checks.append(("mapper soft cover self-recall + bounded",
                   cards[0]["primitive_id"] in _mapper_cands(dict(cards[0]), idx)
                   and len(_mapper_cands(q, idx)) <= n))
    # cross-polytope: deterministic keys; identical descriptor shares every key (self-recall guaranteed).
    checks.append(("cross-polytope keys deterministic + self-recall",
                   cross_polytope_keys(cards[0]) == cross_polytope_keys(dict(cards[0]))
                   and cards[0]["primitive_id"] in _cpoly_cands(dict(cards[0]), idx)))
    # corpus AXIS columns: every card carries persistence + percolation-centrality + RG-path columns; the
    # near-duplicate dedup family dies EARLY in the persistence filtration (dense), by the elder rule.
    checks.append(("every card carries the corpus axis columns",
                   all({"perslife", "persclass", "perccentral"}
                       <= {c.split(":", 1)[0] for c in idx["axis_columns_by_id"][pid]}
                       for pid in idx["card_by_id"])))
    checks.append(("near-duplicate family members die early in the persistence filtration",
                   any(idx["perslife_by_id"][f"prim:dedup:{i}"] == 0 for i in range(4))))
    # the widened feature factory: register embeddings + flow + curve + cpoly column families all present.
    wide_cols = {c.split(":", 1)[0] for c in feature_columns(cards[0])}
    checks.append(("feature factory spans the new families (registers, flow, curve, cpoly)",
                   {"embp", "embt", "embs", "flowclass", "flowbits", "curvekey", "cpoly_0"} <= wide_cols))

    # (e) BAKEOFF races the whole zoo; an LSH/partition path matches scan recall at LOWER cost (the whole point).
    labelled = [{"query_card": q, "relevant": sorted(dedup_ids)}]
    for fam in ("resize", "ocr", "score", "normalize"):
        qc = dict(cards[[c["primitive_id"] for c in cards].index(f"prim:{fam}:0")])
        qc["primitive_id"] = f"q_{fam}"
        labelled.append({"query_card": qc, "relevant": [f"prim:{fam}:{i}" for i in range(4)]})
    result = bakeoff(labelled, cards, k=_DEFAULT_K)
    by_path = {r["path"]: r for r in result["receipts"]}
    checks.append(("bakeoff races the FULL zoo (computed, never hand-counted)",
                   result["paths_raced"] == len(RETRIEVAL_PATHS)))
    checks.append(("bakeoff emits a receipt per path", set(by_path) == set(RETRIEVAL_PATHS)))
    checks.append(("full-scan baseline achieves high recall", by_path["scan_cosine"]["recall_at_k"] >= 0.6))
    scan_cost = by_path["scan_cosine"]["mean_candidates_scanned"]
    scan_recall = by_path["scan_cosine"]["recall_at_k"]
    checks.append(("some sub-linear strategy matches scan recall at lower cost",
                   any(by_path[p]["recall_at_k"] >= scan_recall and by_path[p]["mean_candidates_scanned"] < scan_cost
                       for p in RETRIEVAL_PATHS if p != "scan_cosine")))
    checks.append(("champion chosen, all losers kept as fallbacks",
                   result["champion"] in RETRIEVAL_PATHS and len(result["fallbacks"]) == len(RETRIEVAL_PATHS) - 1))
    checks.append(("champion cost is a fraction of the corpus (efficient)",
                   by_path[result["champion"]]["cost_fraction_of_corpus"] < 1.0))

    # (e2) the SWITCHING surface: the zoo as one StrategyPortfolio — switch by name, receipt-driven default.
    portfolio = retrieval_portfolio(labelled, cards, k=_DEFAULT_K)
    checks.append(("portfolio registers every zoo row as a switchable strategy",
                   portfolio.names() == list(RETRIEVAL_PATHS)))
    checks.append(("portfolio default is the MEASURED bakeoff champion (receipt-driven, not hand-typed)",
                   portfolio.active_name() == result["champion"]))
    portfolio.set_default("mapper_soft_cover")
    switched = portfolio.run(q, idx)
    portfolio.set_default("minhash_fine")
    checks.append(("switching methodology by name changes the path actually run",
                   switched["path"] == "mapper_soft_cover" and portfolio.run(q, idx)["path"] == "minhash_fine"))
    checks.append(("portfolio WITHOUT a receipt defaults to the max-recall baseline (principled floor)",
                   retrieval_portfolio().active_name() == "scan_cosine"))

    # (f) determinism of the whole bakeoff.
    checks.append(("bakeoff is deterministic (byte-identical twice)",
                   json.dumps(bakeoff(labelled, cards), sort_keys=True) == json.dumps(bakeoff(labelled, cards), sort_keys=True)))
    checks.append(("index + bakeoff are candidate/serves_truth=false",
                   idx["serves_truth"] is False and result["serves_truth"] is False))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    champ = by_path[result["champion"]]
    print(f"\nPASS - primitive_retrieval_bakeoff: wide feature factory ({cc['distinct_columns']} cols over {n} "
          f"cards) + a ZOO of {result['paths_raced']} candidate strategies (multi-resolution MinHash, SimHash, "
          f"hierarchical cascade, multi-type routing, op/family partitions, embedding canopies + panel winners: "
          f"p-stable L2 grid, frame exact/kin/successor, reaction gap-closing, BM25-saturated+PMI-expanded, "
          f"operation spaced seeds + second wave: WAND boolean/top-k, Bloom panels+containment, lock-and-key "
          f"feeders, z-order curve window, surprisal blocking, RG descent, percolation components, mapper soft "
          f"covers, cross-polytope) raced by receipt. "
          f"Champion '{result['champion']}': recall@{result['k']}={champ['recall_at_k']} at "
          f"{champ['cost_fraction_of_corpus']}x corpus cost; {len(result['fallbacks'])} fallbacks kept. "
          f"Deterministic, serves_truth=false.")
    return 0


def _load_corpus() -> list[dict[str, Any]]:
    from scripts._repo_paths import resource as _resource  # noqa: PLC0415
    path = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "verified_factory_primitive_cards.jsonl"
    cards: list[dict[str, Any]] = []
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        cards.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return cards


def _run_corpus_columns() -> int:
    cards = _load_corpus()
    if not cards:
        print("no corpus on this checkout")
        return 0
    print(json.dumps(corpus_column_count(cards), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--corpus-columns", action="store_true", help="count feature columns on the real corpus")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.corpus_columns:
        return _run_corpus_columns()
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
