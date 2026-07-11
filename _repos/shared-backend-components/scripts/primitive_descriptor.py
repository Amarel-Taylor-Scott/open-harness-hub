#!/usr/bin/env python3
"""scripts.primitive_descriptor — describe & compare a primitive along a PRECISION↔RECALL SPECTRUM: engineered
SYMBOLIC dimensions (interpretable, blockable, exact) fused with SEMANTIC embeddings (fuzzy, nearest-neighbor),
so one descriptor can be compared by a coarse BLOCKING key, by feature OVERLAP, or by semantic NEAREST-NEIGHBOR —
whichever precision the task needs.

Why (first principles). A primitive should not have ONE representation. Interface matching (edges) wires; intent
matching (blackbox embedding) discovers; but neither captures the interpretable structure an agent reasons about:
what DATATYPES it touches, what OPERATIONS it performs, how many, and whether it impacts a SCALAR vs a structure/
collection/media. Those engineered dimensions are cheap, deterministic, and BLOCKABLE (great for candidate
generation and hard filters); embeddings are fuzzy and paraphrase-proof (great for recall). Fused, they give
"multiple ways to describe and compare, from blocking to semantic nearest-neighbor" in ONE place.

The comparison LADDER (strongest, highest-precision tier wins — mirrors edge_type_matcher's tiering):
    blocking → impact → operation → datatype → phrase → keyword → semantic
Each tier is a separate, selectable comparator; ``compare`` reports them ALL plus the strongest that fires, and
``similarity`` fuses them by single-source weights.

Reuse-first: SEMANTIC facets come from ``capability_embedding`` (the blackbox/intent embedder); KEYWORDS from the
shipped lexical ``build_primitive_search_index.tokenize`` (same stopwords as the search index); EDGE tokens from
``edge_representations``. The DATATYPE / OPERATION / IMPACT vocabularies are named, single-source lexicons here
(no magic literals in logic).

serves_truth=false — describing or comparing a candidate primitive never promotes it.

    PYTHONPATH=. python3 scripts/primitive_descriptor.py --self-test
    PYTHONPATH=. python3 scripts/primitive_descriptor.py --compare "dedupe records" "collapse duplicate rows"
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
from typing import Any, Iterable  # noqa: E402

from scripts import capability_embedding as _capability_embedding  # noqa: E402  REUSE: semantic facet + cosine
from scripts import edge_representations as _edge_representations  # noqa: E402  REUSE: edge type tokens
from scripts.build_primitive_search_index import tokenize as _tokenize  # noqa: E402  REUSE: keywords + stopwords

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# ──────────────────────────────────────────────────────────────────────────────
# Single-source lexicons — the engineered dimensions. NO magic literals in logic: extraction reads THESE maps.
# Each maps a signal TOKEN -> a canonical dimension value; reverse maps are built once for O(1) lookup.
# ──────────────────────────────────────────────────────────────────────────────
#: DATATYPE families — the kind of thing a primitive reads/writes. The "scalar vs other datatypes" axis lives
#: here: the ``scalar`` family is single values; everything else is text/structured/collection/media/graph/…
DATATYPE_LEXICON: dict[str, tuple[str, ...]] = {
    "scalar":     ("number", "numeric", "int", "integer", "float", "count", "score", "amount", "scalar",
                   "bool", "boolean", "flag", "ratio", "rate", "percentage", "probability", "value"),
    "text":       ("text", "string", "str", "name", "label", "token", "word", "sentence", "phrase", "caption"),
    "structured": ("record", "row", "object", "dict", "entity", "struct", "schema", "field", "document",
                   "doc", "json", "profile", "form", "invoice", "complaint"),
    "collection": ("batch", "list", "set", "array", "collection", "rows", "records", "items", "cluster",
                   "group", "table", "dataset", "corpus"),
    "media":      ("image", "photo", "picture", "audio", "video", "sound", "media", "scan", "frame", "pixel"),
    "graph":      ("graph", "tree", "node", "edge", "adjacency", "network", "path", "dag", "route"),
    "temporal":   ("date", "time", "timestamp", "datetime", "period", "duration", "interval"),
    "geo":        ("location", "coordinate", "geo", "address", "latitude", "longitude", "region"),
}
#: OPERATION kinds — what a primitive DOES, keyed by canonical operation -> signal verbs/nouns in the blackbox.
OPERATION_LEXICON: dict[str, tuple[str, ...]] = {
    "dedup":     ("dedup", "deduplicate", "duplicate", "duplicates", "collapse", "merge", "unique", "distinct"),
    "normalize": ("normalize", "canonicalize", "standardize", "clean", "cleanse", "format", "sanitize"),
    "filter":    ("filter", "screen", "select", "exclude", "remove", "drop", "prune", "block"),
    "extract":   ("extract", "parse", "ocr", "read", "pull", "scrape", "detect", "recognize", "identify"),
    "transform": ("transform", "convert", "map", "translate", "encode", "decode", "resize", "reshape", "render"),
    "aggregate": ("aggregate", "reduce", "sum", "count", "group", "rollup", "summarize", "fold", "tally"),
    "rank":      ("rank", "score", "rerank", "sort", "prioritize", "order", "weigh"),
    "embed":     ("embed", "embedding", "vectorize", "encode", "represent"),
    "classify":  ("classify", "label", "categorize", "tag", "route", "assign"),
    "validate":  ("validate", "verify", "check", "assert", "gate", "audit", "reconcile"),
    "enrich":    ("enrich", "augment", "annotate", "join", "link", "resolve", "match", "lookup"),
    "generate":  ("generate", "synthesize", "produce", "create", "compose", "build", "emit"),
}
#: OPERATION -> IMPACT class: what the operation does to the data's SHAPE. This is the "impact scalars vs other
#: datatypes" dimension expressed as a behavioural class (single-source; derived, not hand-typed per card).
OP_TO_IMPACT: dict[str, str] = {
    "dedup": "collection", "filter": "collection", "aggregate": "collection",   # change cardinality/membership
    "normalize": "structural", "transform": "structural", "enrich": "structural",  # change shape/fields
    "rank": "scalar", "score": "scalar", "classify": "scalar", "validate": "scalar",  # attach/produce a scalar
    "extract": "transform", "embed": "transform", "generate": "transform",       # produce a new representation
}

# reverse maps (token -> canonical), built once.
_DTYPE_BY_TOKEN: dict[str, str] = {tok: fam for fam, toks in DATATYPE_LEXICON.items() for tok in toks}
_OP_BY_TOKEN: dict[str, str] = {tok: op for op, toks in OPERATION_LEXICON.items() for tok in toks}

#: per-tier floors — a tier "fires" only above its floor (precision guard; single-source, no inline literals).
_TIER_FLOORS: dict[str, float] = {"keyword": 0.10, "phrase": 0.10, "datatype": 0.34, "operation": 0.34,
                                  "semantic": 0.30}
#: the ladder, HIGHEST-precision first — ``compare`` returns the strongest tier that fires in this order.
_TIER_ORDER: tuple[str, ...] = ("blocking", "impact", "operation", "datatype", "phrase", "keyword", "semantic")
#: fusion weights for the single blended score (single-source; interpretable dims carry real weight, semantic
#: adds recall). Need not sum to 1 — ``similarity`` normalizes by the weights actually present.
_FUSION_WEIGHTS: dict[str, float] = {"operation": 0.28, "datatype": 0.22, "impact": 0.10, "phrase": 0.12,
                                     "keyword": 0.10, "semantic": 0.18}


# ──────────────────────────────────────────────────────────────────────────────
# Symbolic facet extractors.
# ──────────────────────────────────────────────────────────────────────────────
def _card_text(card: dict[str, Any]) -> str:
    """title + blackbox — the natural-language surface the symbolic facets read."""
    return f"{card.get('title') or ''} {_capability_embedding.blackbox_text(card)}"


def keywords(card: dict[str, Any]) -> frozenset[str]:
    """Significant tokens from title + blackbox (shipped tokenizer: lowercased, min-len, stopwords removed)."""
    return frozenset(_tokenize(_card_text(card)))


def keyphrases(card: dict[str, Any]) -> frozenset[str]:
    """Significant adjacent-token BIGRAMS ("remove_duplicate", "scanned_document") — multi-word signal a single
    keyword loses. Deterministic; order within a pair preserved from the text."""
    toks = _tokenize(_card_text(card))
    return frozenset(f"{a}_{b}" for a, b in zip(toks, toks[1:]))


def _edge_tokens(card: dict[str, Any]) -> frozenset[str]:
    """Type tokens from both edges (reuses edge_representations) — a datatype/operation signal the prose misses."""
    out: set[str] = set()
    for side in ("input", "output"):
        out |= set(_edge_representations.type_tokens(_capability_embedding._edge_str(card, side)))
    return frozenset(t.lower() for t in out)


def datatypes(card: dict[str, Any]) -> frozenset[str]:
    """The DATATYPE families the primitive touches, from edge tokens + blackbox tokens matched to the lexicon."""
    signal = keywords(card) | _edge_tokens(card)
    return frozenset(_DTYPE_BY_TOKEN[t] for t in signal if t in _DTYPE_BY_TOKEN)


def operations(card: dict[str, Any]) -> frozenset[str]:
    """The OPERATION kinds the primitive performs, from blackbox + edge tokens matched to the lexicon."""
    signal = keywords(card) | _edge_tokens(card)
    return frozenset(_OP_BY_TOKEN[t] for t in signal if t in _OP_BY_TOKEN)


def impact_class(card: dict[str, Any]) -> str:
    """Does it impact a SCALAR vs another datatype? Derived from (a) the OUTPUT datatype family when known, else
    (b) the operation->impact map. Returns one of scalar|text|structured|collection|media|graph|transform|
    structural|unknown. The single "impact scalars vs other datatypes" verdict."""
    out_tokens = frozenset(t.lower() for t in _edge_representations.type_tokens(
        _capability_embedding._edge_str(card, "output")))
    out_families = [_DTYPE_BY_TOKEN[t] for t in out_tokens if t in _DTYPE_BY_TOKEN]
    if out_families:
        # scalar dominates when present (a scalar-producing op is the sharp, decision-relevant case)
        return "scalar" if "scalar" in out_families else sorted(out_families)[0]
    ops = operations(card)
    impacts = {OP_TO_IMPACT[o] for o in ops if o in OP_TO_IMPACT}
    if "scalar" in impacts:
        return "scalar"
    return sorted(impacts)[0] if impacts else "unknown"


def describe(card: dict[str, Any], *, with_semantic: bool = True) -> dict[str, Any]:
    """The full multi-facet descriptor: engineered SYMBOLIC dimensions + (optionally) the SEMANTIC embedding of
    the blackbox (intent). ``with_semantic=False`` skips the vector for a cheap symbolic-only descriptor."""
    ops = operations(card)
    desc: dict[str, Any] = {
        "primitive_id": card.get("primitive_id"),
        "keywords": sorted(keywords(card)),
        "keyphrases": sorted(keyphrases(card)),
        "datatypes": sorted(datatypes(card)),
        "operations": sorted(ops),
        "operation_count": len(ops),
        "impact_class": impact_class(card),
        **BOUNDARY,
    }
    if with_semantic:
        # the blackbox INTENT vector (offline proxy by default; real model when the caller selects it upstream).
        desc["semantic_blackbox"] = _capability_embedding.embed_text(
            _capability_embedding.blackbox_text(card), path=_capability_embedding.DEFAULT_TEXT_PATH)
    return desc


def blocking_keys(desc: dict[str, Any]) -> frozenset[str]:
    """Coarse candidate-generation buckets from the descriptor — an agent/index gathers candidates that share
    ANY block, then compares finely. Namespaced so buckets never collide across dimensions."""
    keys = {f"op:{o}" for o in desc.get("operations", [])}
    keys |= {f"dtype:{d}" for d in desc.get("datatypes", [])}
    keys.add(f"impact:{desc.get('impact_class', 'unknown')}")
    return frozenset(keys)


# ──────────────────────────────────────────────────────────────────────────────
# The comparison LADDER — blocking → … → semantic, strongest tier wins.
# ──────────────────────────────────────────────────────────────────────────────
def _jaccard(a: Iterable[str], b: Iterable[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0
    return len(sa & sb) / len(sa | sb)


def compare(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Compare two DESCRIPTORS at every rung of the ladder, returning each tier's score plus the strongest tier
    that FIRES (above its floor) — the interpretable, multi-way comparison. ``blocking`` and ``impact`` are
    boolean tiers (share ≥1 block / same impact class); the rest are similarities in [0,1]."""
    shared_blocks = blocking_keys(a) & blocking_keys(b)
    tiers: dict[str, float] = {
        "blocking": 1.0 if shared_blocks else 0.0,
        "impact": 1.0 if a.get("impact_class") == b.get("impact_class") != "unknown" else 0.0,
        "operation": _jaccard(a.get("operations", []), b.get("operations", [])),
        "datatype": _jaccard(a.get("datatypes", []), b.get("datatypes", [])),
        "phrase": _jaccard(a.get("keyphrases", []), b.get("keyphrases", [])),
        "keyword": _jaccard(a.get("keywords", []), b.get("keywords", [])),
        "semantic": _semantic_sim(a, b),
    }
    best_tier, best_score = "none", 0.0
    for tier in _TIER_ORDER:
        score = tiers[tier]
        floor = _TIER_FLOORS.get(tier, 0.0)  # blocking/impact have no floor (boolean 1.0 fires)
        if score > 0.0 and score >= floor:
            best_tier, best_score = tier, score
            break
    return {"tiers": {k: round(v, 6) for k, v in tiers.items()},
            "shared_blocks": sorted(shared_blocks),
            "best_tier": best_tier, "best_score": round(best_score, 6),
            "fused": round(similarity(a, b), 6), **BOUNDARY}


def _semantic_sim(a: dict[str, Any], b: dict[str, Any]) -> float:
    va, vb = a.get("semantic_blackbox"), b.get("semantic_blackbox")
    if not va or not vb:
        return 0.0
    return max(0.0, _capability_embedding.cosine(va, vb))


def similarity(a: dict[str, Any], b: dict[str, Any], *, weights: dict[str, float] = _FUSION_WEIGHTS) -> float:
    """A single blended similarity — weighted mean of the tier scores actually computable (normalized by the
    weights present), so symbolic and semantic evidence combine into one comparable number."""
    parts = {
        "operation": _jaccard(a.get("operations", []), b.get("operations", [])),
        "datatype": _jaccard(a.get("datatypes", []), b.get("datatypes", [])),
        "impact": 1.0 if a.get("impact_class") == b.get("impact_class") != "unknown" else 0.0,
        "phrase": _jaccard(a.get("keyphrases", []), b.get("keyphrases", [])),
        "keyword": _jaccard(a.get("keywords", []), b.get("keywords", [])),
        "semantic": _semantic_sim(a, b),
    }
    wsum = sum(weights.get(k, 0.0) for k in parts)
    if wsum <= 0.0:
        return 0.0
    return sum(weights.get(k, 0.0) * v for k, v in parts.items()) / wsum


#: which comparator a ``search`` call ranks by — the "multiple ways to compare" made a selectable method.
SEARCH_METHODS: tuple[str, ...] = ("blocking", "keyword", "phrase", "datatype", "operation", "impact",
                                   "semantic", "fused")


def search(query: dict[str, Any], cards: Iterable[dict[str, Any]], *, method: str = "fused",
           k: int = 10) -> list[dict[str, Any]]:
    """Rank ``cards`` against a query CARD by the chosen comparator (any rung of the ladder, or ``fused``) — one
    call, many comparison methods. Every hit is candidate/serves_truth=false with the tier breakdown. k<=0 = all."""
    if method not in SEARCH_METHODS:
        raise ValueError(f"unknown method {method!r}; methods are {SEARCH_METHODS}")
    q = describe(query)
    scored: list[tuple[float, dict[str, Any]]] = []
    for card in cards:
        d = describe(card)
        cmp = compare(q, d)
        score = cmp["fused"] if method == "fused" else cmp["tiers"].get(method, 0.0)
        if score <= 0.0:
            continue
        scored.append((score, {"primitive_id": card.get("primitive_id"), "method": method,
                               "score": round(score, 6), "best_tier": cmp["best_tier"],
                               "operations": d["operations"], "datatypes": d["datatypes"],
                               "impact_class": d["impact_class"], **BOUNDARY}))
    scored.sort(key=lambda s: (-s[0], str(s[1].get("primitive_id"))))
    ranked = [h for _, h in scored]
    return ranked if k <= 0 else ranked[:k]


# ──────────────────────────────────────────────────────────────────────────────
# Verify the verifier.
# ──────────────────────────────────────────────────────────────────────────────
def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    dedup = {"primitive_id": "prim:dedup", "title": "Deduplicate records",
             "blackbox": "Remove duplicate records by clustering near-identical rows and keeping one canonical row.",
             "input_edge": "RecordBatch", "output_edge": "DedupedRecordBatch", **BOUNDARY}
    dedup2 = {"primitive_id": "prim:collapse", "title": "Collapse duplicate rows",
              "blackbox": "Collapse duplicate rows in a dataset, merging near-identical records into one.",
              "input_edge": "RowBatch", "output_edge": "MergedRowBatch", **BOUNDARY}
    resize = {"primitive_id": "prim:resize", "title": "Resize image",
              "blackbox": "Resize an image to target dimensions using bilinear interpolation.",
              "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY}
    score = {"primitive_id": "prim:score", "title": "Risk score an entity",
             "blackbox": "Score an entity for risk and return a numeric probability between zero and one.",
             "input_edge": "EntityRecord", "output_edge": "RiskScore", **BOUNDARY}

    d_dedup, d_dedup2, d_resize, d_score = (describe(c) for c in (dedup, dedup2, resize, score))

    # (a) symbolic dims extract meaningfully
    checks.append(("dedup operation extracted", "dedup" in d_dedup["operations"]))
    checks.append(("collection datatype extracted for a batch primitive", "collection" in d_dedup["datatypes"]))
    checks.append(("keyphrases capture multi-word signal", any("duplicate" in p for p in d_dedup["keyphrases"])))
    checks.append(("operation_count reflects distinct ops", d_dedup["operation_count"] >= 1))

    # (b) the "impact scalars vs other datatypes" axis discriminates: a scoring primitive is scalar-impacting,
    #     a dedup primitive is collection-impacting.
    checks.append(("scoring primitive is scalar-impacting", d_score["impact_class"] == "scalar"))
    checks.append(("dedup primitive is NOT scalar-impacting", d_dedup["impact_class"] != "scalar"))

    # (c) blocking keys generate the right coarse buckets + two dedup variants SHARE a block, dedup vs resize DON'T
    checks.append(("dedup blocking keys include its operation", "op:dedup" in blocking_keys(d_dedup)))
    checks.append(("two dedup variants share a blocking key", bool(blocking_keys(d_dedup) & blocking_keys(d_dedup2))))
    checks.append(("dedup and resize share NO operation/impact block",
                   not ({b for b in blocking_keys(d_dedup) if b.startswith(("op:", "impact:"))}
                        & {b for b in blocking_keys(d_resize) if b.startswith(("op:", "impact:"))})))

    # (d) the LADDER: two dedup variants match at a HIGH-precision tier (operation/blocking), while dedup vs
    #     resize only ever reaches (at best) the weak semantic tier — the whole "blocking → semantic NN" point.
    cmp_near = compare(d_dedup, d_dedup2)
    cmp_far = compare(d_dedup, d_resize)
    checks.append(("near pair fires a high-precision tier (blocking/operation)",
                   cmp_near["best_tier"] in ("blocking", "operation", "impact", "datatype")))
    checks.append(("near pair fused > far pair fused (symbolic+semantic agree)", cmp_near["fused"] > cmp_far["fused"]))
    checks.append(("far pair never reaches a high-precision tier",
                   cmp_far["best_tier"] in ("keyword", "semantic", "none")))

    # (e) search by DIFFERENT methods all rank the true variant first over distractors (multiple ways, one call)
    corpus = [dedup2, resize, score]
    for method in ("operation", "datatype", "semantic", "fused"):
        hits = search(dedup, corpus, method=method, k=3)
        ok = bool(hits) and hits[0]["primitive_id"] == "prim:collapse"
        checks.append((f"search(method={method}) ranks the true dedup variant first", ok))

    # (f) determinism: same descriptor + corpus -> byte-identical ranking
    r1 = json.dumps(search(dedup, corpus, method="fused", k=3), sort_keys=True)
    r2 = json.dumps(search(dedup, corpus, method="fused", k=3), sort_keys=True)
    checks.append(("search is deterministic (byte-identical twice)", r1 == r2))

    # (g) candidate/serves_truth boundary carried through
    checks.append(("descriptors + hits are candidate/serves_truth=false",
                   d_dedup["candidate"] and d_dedup["serves_truth"] is False
                   and all(h["serves_truth"] is False for h in search(dedup, corpus, k=3))))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_descriptor: one primitive, MANY comparable facets — engineered symbolic dimensions "
          "(keywords, keyphrases, datatypes, operations, operation-count, scalar-vs-other impact) fused with the "
          "semantic blackbox embedding; a blocking→…→semantic ladder (strongest tier wins) + a fused score; search "
          "by any method. Blocking is sharp, semantic is paraphrase-proof, and they agree on near vs far. "
          "serves_truth=false.")
    return 0


def _run_compare(a_text: str, b_text: str) -> int:
    a = {"primitive_id": "a", "title": a_text, "blackbox": a_text, "input_edge": "", "output_edge": ""}
    b = {"primitive_id": "b", "title": b_text, "blackbox": b_text, "input_edge": "", "output_edge": ""}
    print(json.dumps(compare(describe(a), describe(b)), indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--compare", nargs=2, metavar=("A", "B"), help="compare two blackbox descriptions")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.compare:
        return _run_compare(args.compare[0], args.compare[1])
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
