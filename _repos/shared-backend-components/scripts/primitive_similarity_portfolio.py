#!/usr/bin/env python3
"""scripts.primitive_similarity_portfolio — ONE flexible, single-source PORTFOLIO of primitive-similarity methods.

The registry has ~117k generated primitive cards. "Are these two primitives the same / near-duplicates / composable?"
is asked by many callers (dedupe, blocking, nearest-neighbour, composition search) and today each answers it with its
own ad-hoc lexical overlap. That is one narrow signal masquerading as THE answer. This module is the ADD-ONLY,
multi-path fix: a portfolio of *several* similarity methods (lexical, composability-edge-type, scalable MinHash-LSH,
structural-shape, and a reserved dense-embedding slot), each a row with an honest `status` (wired = runs offline
today, planned = reserved slot), plus ONE importable API — `similarity(a, b, method=...)`, `lsh_blocking(...)`,
`nearest(...)` — so callers pick the RIGHT signal instead of hardcoding one.

It does NOT edit the contract-locked matchers (mutator_registry / build_edge_type_retrofit / registry_search). It
IMPORTS `build_edge_type_retrofit.canonicalize_edge` (the composability-aware edge normalizer) and the retrieval
portfolio's `dim_compatible` guard, so the composability + dim rules stay single-source.

Laws honored: fully deterministic + offline (no network, no LLM, no wall-clock — a fixed literal DEFAULT_DATE; no
RNG — the parameter space is enumerated and pseudo-variety comes from stable string seeds like f"{i}:{token}", never
hash()). All emitted rows are candidate=true / serves_truth=false (a similarity SCORE is never a truth claim). CLI:
--self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.build_edge_type_retrofit import canonicalize_edge  # composability-aware edge normalizer (single source)

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "primitive-similarity-portfolio"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
# Fixed literal so the write path is deterministic (no wall-clock). Override with --date.
DEFAULT_DATE = "2026-07-03"

# MinHash permutation count for the similarity ESTIMATE lane (LSH blocking sizes its own signature via bands*rows).
# 128 keeps the Jaccard estimate tight while staying cheap; a named constant, never a bare literal in logic.
MINHASH_PERMUTATIONS = 128
# Any wired method must score two clearly-disjoint cards below this; the self-test enforces it.
LOW_SIMILARITY_CEILING = 0.34


# ── the method portfolio (rows; status is honest — wired runs offline today, planned is a reserved slot) ──
# (name, status, kind, when_wins, signal_field, notes)
METHODS: list[tuple[str, str, str, str, str, str]] = [
    ("lexical_jaccard", "wired", "lexical_token_set",
     "cheap surface dedupe; title/description word overlap",
     "title+blackbox.does",
     "Jaccard over the lowercased alnum token set of title + blackbox does; the honest surface floor"),
    ("edge_type_jaccard", "wired", "composability_edge_type",
     "'can these compose / do they consume+produce the same types?' — the COMPOSABILITY-aware signal",
     "canonicalize_edge(input_edge)+canonicalize_edge(output_edge)",
     "direction-tagged {in:T,out:T} Jaccard over canonical edge type_ids (via build_edge_type_retrofit), so a "
     "RecordBatch->RecordBatch pair scores above a RecordBatch->HashDigest pair"),
    ("minhash_lsh", "wired", "scalable_blocking",
     "near-dup detection over MILLIONS of rows without O(N^2) all-pairs",
     "title+blackbox.does",
     "real MinHash (min over stable string-seeded hashes, NEVER hash()) estimating lexical Jaccard; banded into "
     "buckets by lsh_blocking so only in-bucket pairs are ever compared"),
    ("structural_fingerprint", "wired", "shape_signature",
     "'same SHAPE?' — group primitives by arity/effect-class regardless of wording",
     "input/output arity + effect class + kind + contract key-set hash",
     "Jaccard over the structural feature set (in_arity, out_arity, kind, effect classes, contract key-set hash)"),
    ("embedding_cosine", "planned", "dense_semantic",
     "true semantic near-neighbour once a dense primitive vector plane is persisted",
     "dense primitive vector (active retrieval embedder)",
     "RESERVED slot — no dense primitive vectors are persisted yet; when wired it MUST gate on dim_compatible() "
     "from the retrieval portfolio so a dim mismatch surfaces instead of a silent 0.0"),
]

_WIRED_STATUS = "wired"


class MethodNotWiredError(RuntimeError):
    """Raised when a planned (reserved) similarity method is invoked before it is wired."""


# ── pure helpers (deterministic; string-seeded hashing only) ──
def _stable_hash(seed: str) -> int:
    """A stable 64-bit hash of a string. Uses sha256 (content-addressed, cross-run stable) — NEVER builtin hash()
    (which is process-salted / non-deterministic)."""
    return int.from_bytes(hashlib.sha256(seed.encode("utf-8")).digest()[:8], "big")


def _jaccard(a: set[str], b: set[str]) -> float:
    """Jaccard similarity in [0,1]. Two empty sets are defined identical (1.0); one empty is 0.0."""
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _card_id(card: dict[str, Any]) -> str:
    return str(card.get("primitive_id") or card.get("id") or card.get("slug") or card.get("title") or id(card))


def _lexical_tokens(card: dict[str, Any]) -> set[str]:
    parts = [str(card.get("title") or "")]
    bb = card.get("blackbox")
    if isinstance(bb, dict):
        parts.append(str(bb.get("does") or ""))
    elif isinstance(bb, str):
        parts.append(bb)
    return set(re.findall(r"[a-z0-9]+", " ".join(parts).lower()))


def _edge_strings(card: dict[str, Any]) -> tuple[str, str]:
    """(input_edge, output_edge) with a contract-dict fallback, always strings."""
    ie = card.get("input_edge")
    oe = card.get("output_edge")
    contract = card.get("contract")
    if not ie and isinstance(contract, dict):
        ie = contract.get("input")
    if not oe and isinstance(contract, dict):
        oe = contract.get("output")
    return (ie if isinstance(ie, str) else ""), (oe if isinstance(oe, str) else "")


def _edge_type_tokens(card: dict[str, Any]) -> set[str]:
    """Direction-tagged canonical edge type set: {in:<type_id>, out:<type_id>} — composability-aware."""
    ie, oe = _edge_strings(card)
    return {"in:" + canonicalize_edge(ie), "out:" + canonicalize_edge(oe)}


def _structural_tokens(card: dict[str, Any]) -> set[str]:
    """Shape signature as a feature set: input/output arity, kind, effect classes, contract key-set hash."""
    ie, oe = _edge_strings(card)
    in_arity = len([p for p in ie.split("+") if p.strip()]) if ie.strip() else 0
    out_arity = len([p for p in oe.split("+") if p.strip()]) if oe.strip() else 0
    toks: set[str] = {f"in_arity:{in_arity}", f"out_arity:{out_arity}", f"kind:{card.get('kind', '?')}"}
    effects = card.get("effects")
    if isinstance(effects, list) and effects:
        for e in effects:
            toks.add("effect:" + str(e).split(".")[0])  # fs.read -> fs (coarse effect CLASS)
    else:
        toks.add("effect:none")
    contract = card.get("contract")
    if isinstance(contract, dict):
        toks.add("keys:" + hashlib.sha256(repr(sorted(contract.keys())).encode("utf-8")).hexdigest()[:8])
    return toks


def _minhash_signature(tokens: set[str], n: int) -> tuple[int, ...]:
    """Real MinHash: for permutation i, take min over tokens of a stable string-seeded hash f"{i}:{token}".

    Two empty token sets share the sentinel signature (defined identical); an empty vs non-empty set almost never
    collides. Deterministic across runs (sha256, not builtin hash())."""
    if not tokens:
        return tuple([0] * n)
    return tuple(min(_stable_hash(f"{i}:{t}") for t in tokens) for i in range(n))


def _minhash_sim(a: dict[str, Any], b: dict[str, Any], n: int = MINHASH_PERMUTATIONS) -> float:
    sa = _minhash_signature(_lexical_tokens(a), n)
    sb = _minhash_signature(_lexical_tokens(b), n)
    return sum(1 for x, y in zip(sa, sb) if x == y) / float(n)


def _embedding_cosine(a: dict[str, Any], b: dict[str, Any]) -> float:
    """PLANNED (reserved) — never returns a silent number. Points at the dim-compat guard it must adopt when wired."""
    try:
        from scripts.build_retrieval_backend_portfolio import active_embedder, dim_compatible  # noqa: F401
        emb = active_embedder()
        detail = f"active embedder {emb.get('backend_id')} (dim {emb.get('dim')})"
    except Exception:  # pragma: no cover - resolver import is best-effort context only
        detail = "the active retrieval embedder"
    raise MethodNotWiredError(
        f"embedding_cosine is PLANNED: no dense primitive vectors are persisted for {detail}. When wired it MUST "
        "gate on dim_compatible() from the retrieval portfolio so a dim mismatch is surfaced, never a silent 0.0."
    )


# ── the importable API ──
_WIRED: dict[str, Callable[[dict[str, Any], dict[str, Any]], float]] = {
    "lexical_jaccard": lambda a, b: _jaccard(_lexical_tokens(a), _lexical_tokens(b)),
    "edge_type_jaccard": lambda a, b: _jaccard(_edge_type_tokens(a), _edge_type_tokens(b)),
    "minhash_lsh": _minhash_sim,
    "structural_fingerprint": lambda a, b: _jaccard(_structural_tokens(a), _structural_tokens(b)),
}
_PLANNED: dict[str, Callable[[dict[str, Any], dict[str, Any]], float]] = {
    "embedding_cosine": _embedding_cosine,
}


def wired_methods() -> list[str]:
    return [name for name, status, *_ in METHODS if status == _WIRED_STATUS]


def similarity(a: dict[str, Any], b: dict[str, Any], method: str = "edge_type_jaccard") -> float:
    """Similarity of two primitive cards in [0,1] under the chosen method. Identical cards -> 1.0, disjoint -> low.

    method: one of wired_methods() (lexical_jaccard, edge_type_jaccard, minhash_lsh, structural_fingerprint);
    'embedding_cosine' is a reserved slot and raises MethodNotWiredError until a dense plane exists."""
    if method in _PLANNED:
        return _PLANNED[method](a, b)
    if method not in _WIRED:
        raise ValueError(f"unknown similarity method {method!r}; wired={wired_methods()}, planned={list(_PLANNED)}")
    return _WIRED[method](a, b)


def lsh_blocking(cards: list[dict[str, Any]], bands: int = 16, rows: int = 4) -> dict[str, list[str]]:
    """MinHash-LSH banding: candidate near-dup buckets WITHOUT O(N^2) all-pairs.

    Signature length = bands*rows. Each card's signature is split into `bands` bands of `rows` rows; each band is
    hashed to a bucket key (band-index-tagged so different bands never alias). Two cards land in a shared bucket iff
    they agree on a whole band — near-duplicates collide (candidate pair), far pairs are pruned. Returns
    {bucket_key -> [card_id, ...]}. Only within-bucket pairs need a full similarity() call."""
    n = bands * rows
    buckets: dict[str, list[str]] = defaultdict(list)
    for card in cards:
        sig = _minhash_signature(_lexical_tokens(card), n)
        cid = _card_id(card)
        for b in range(bands):
            band = sig[b * rows:(b + 1) * rows]
            key = f"b{b}:" + hashlib.sha256(repr(band).encode("utf-8")).hexdigest()[:16]
            buckets[key].append(cid)
    return dict(buckets)


def candidate_pairs(cards: list[dict[str, Any]], bands: int = 16, rows: int = 4) -> set[tuple[str, str]]:
    """Deduplicated, order-normalized set of (id_a, id_b) pairs that co-occur in ANY LSH bucket."""
    pairs: set[tuple[str, str]] = set()
    for ids in lsh_blocking(cards, bands, rows).values():
        uniq = sorted(set(ids))
        for i in range(len(uniq)):
            for j in range(i + 1, len(uniq)):
                pairs.add((uniq[i], uniq[j]))
    return pairs


def nearest(query_card: dict[str, Any], corpus: list[dict[str, Any]], method: str = "edge_type_jaccard",
            k: int = 5) -> list[tuple[dict[str, Any], float]]:
    """Top-k most-similar cards to query_card under `method`, highest score first (ties broken by card id for
    determinism). Returns [(card, score), ...]."""
    scored = [(c, similarity(query_card, c, method)) for c in corpus]
    scored.sort(key=lambda t: (-t[1], _card_id(t[0])))
    return scored[:k]


# ── portfolio rows / write path (own shard file; no shared-JSONL write race) ──
def _method_rows() -> list[dict[str, Any]]:
    return [{"record_type": "primitive_similarity_method", "method_id": name, "status": status, "kind": kind,
             "when_wins": when, "signal_field": signal, "notes": notes, **BOUNDARY}
            for name, status, kind, when, signal, notes in METHODS]


def build_manifest(rows: list[dict[str, Any]], *, date: str) -> dict[str, Any]:
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    return {
        "record_type": "primitive_similarity_portfolio_manifest",
        "pack_id": "primitive-similarity-portfolio",
        "generator": "scripts/primitive_similarity_portfolio.py",
        "generated_utc": date,
        "method_count": len(rows),
        "wired_methods": sorted(r["method_id"] for r in rows if r["status"] == "wired"),
        "planned_methods": sorted(r["method_id"] for r in rows if r["status"] == "planned"),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    rows = _method_rows()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    (PACK_DIR / "methods.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(rows, date=date)
    (PACK_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


# ── self-test (pure, over an in-module fixture; no data file, no network) ──
def _fixture() -> dict[str, dict[str, Any]]:
    return {
        # identical pair (same content, different id) -> every wired method must return 1.0
        "ident_a": {"primitive_id": "prim:ident_a", "title": "normalize record batch", "kind": "py.fn",
                    "input_edge": "RecordBatch", "output_edge": "RecordBatch", "effects": ["fs.read"],
                    "contract": {"input": "RecordBatch", "output": "RecordBatch"},
                    "blackbox": {"does": "Normalize a batch of records into canonical rows."}},
        "ident_b": {"primitive_id": "prim:ident_b", "title": "normalize record batch", "kind": "py.fn",
                    "input_edge": "RecordBatch", "output_edge": "RecordBatch", "effects": ["fs.read"],
                    "contract": {"input": "RecordBatch", "output": "RecordBatch"},
                    "blackbox": {"does": "Normalize a batch of records into canonical rows."}},
        # disjoint from ident_a on every axis (words, edge types, arity, kind, effect)
        "disjoint": {"primitive_id": "prim:disjoint", "title": "render galaxy shader mesh", "kind": "py.class",
                     "input_edge": "AdjacencyGraph+VertexBuffer", "output_edge": "HashDigest+ProofReceipt",
                     "effects": ["network"], "contract": {"schema": "x", "shader": "y", "mesh": "z"},
                     "blackbox": {"does": "Rasterize procedural shader vertices onto a display buffer."}},
        # edge-type discrimination: two RecordBatch->RecordBatch vs one RecordBatch->HashDigest
        "rb_rb_1": {"primitive_id": "prim:rb_rb_1", "title": "batch pass one",
                    "input_edge": "RecordBatch", "output_edge": "RecordBatch",
                    "blackbox": {"does": "one"}},
        "rb_rb_2": {"primitive_id": "prim:rb_rb_2", "title": "batch pass two",
                    "input_edge": "RecordBatch", "output_edge": "RecordBatch",
                    "blackbox": {"does": "two"}},
        "rb_hash": {"primitive_id": "prim:rb_hash", "title": "batch to digest",
                    "input_edge": "RecordBatch", "output_edge": "HashDigest",
                    "blackbox": {"does": "hash"}},
        # LSH: two near-dups (identical lexical tokens) + one far card (disjoint tokens)
        "near_1": {"primitive_id": "prim:near_1", "title": "deduplicate customer contact records",
                   "blackbox": {"does": "Collapse duplicate customer contact records by fuzzy match on name and email."}},
        "near_2": {"primitive_id": "prim:near_2", "title": "deduplicate customer contact records",
                   "blackbox": {"does": "Collapse duplicate customer contact records by fuzzy match on name and email."}},
        "far": {"primitive_id": "prim:far", "title": "compile shader kernel",
                "blackbox": {"does": "Translate a fragment program into optimized gpu bytecode."}},
    }


def self_test() -> int:
    fx = _fixture()
    checks: list[tuple[str, bool]] = []

    # 1. every wired method returns a float in [0,1] on an arbitrary pair
    in_range = all(isinstance(similarity(fx["ident_a"], fx["disjoint"], m), float)
                   and 0.0 <= similarity(fx["ident_a"], fx["disjoint"], m) <= 1.0
                   for m in wired_methods())
    checks.append(("every wired method returns a float in [0,1]", in_range))

    # 2. identical cards -> exactly 1.0 for every wired method
    identical_one = all(similarity(fx["ident_a"], fx["ident_b"], m) == 1.0 for m in wired_methods())
    checks.append(("identical cards -> 1.0 for every wired method", identical_one))

    # 3. clearly-disjoint cards -> low for every wired method
    disjoint_low = all(similarity(fx["ident_a"], fx["disjoint"], m) < LOW_SIMILARITY_CEILING for m in wired_methods())
    checks.append((f"disjoint cards -> < {LOW_SIMILARITY_CEILING} for every wired method", disjoint_low))

    # 4. edge_type_jaccard rates RecordBatch->RecordBatch pair above a RecordBatch->HashDigest pair
    s_same = similarity(fx["rb_rb_1"], fx["rb_rb_2"], "edge_type_jaccard")
    s_diff = similarity(fx["rb_rb_1"], fx["rb_hash"], "edge_type_jaccard")
    checks.append(("edge_type_jaccard: RecordBatch->RecordBatch more similar than RecordBatch->HashDigest",
                   s_same == 1.0 and s_diff < s_same))

    # 5a. LSH puts near-dups in the SAME bucket
    buckets = lsh_blocking([fx["near_1"], fx["near_2"], fx["far"]], bands=16, rows=4)
    shared_near = any({"prim:near_1", "prim:near_2"}.issubset(set(ids)) for ids in buckets.values())
    checks.append(("LSH: near-duplicates land in a shared bucket", shared_near))

    # 5b. LSH PRUNES far pairs (the far card never co-occurs with a near-dup in any bucket)
    pairs = candidate_pairs([fx["near_1"], fx["near_2"], fx["far"]], bands=16, rows=4)
    far_pruned = ("prim:far", "prim:near_1") not in pairs and ("prim:far", "prim:near_2") not in pairs \
        and ("prim:near_1", "prim:far") not in pairs and ("prim:near_2", "prim:far") not in pairs
    checks.append(("LSH: far pairs are pruned (far never bucketed with a near-dup)",
                   far_pruned and ("prim:near_1", "prim:near_2") in pairs))

    # 6. nearest() ranks the identical card first
    ranked = nearest(fx["ident_a"], [fx["disjoint"], fx["ident_b"], fx["rb_hash"]], "lexical_jaccard", k=3)
    checks.append(("nearest() ranks the identical card first",
                   ranked and ranked[0][0]["primitive_id"] == "prim:ident_b" and ranked[0][1] == 1.0))

    # 7. planned method is a reserved slot that raises (never a silent number)
    planned_guards = False
    try:
        similarity(fx["ident_a"], fx["ident_b"], "embedding_cosine")
    except MethodNotWiredError:
        planned_guards = True
    checks.append(("planned embedding_cosine raises (reserved slot, no silent score)", planned_guards))

    # 8. boundary held on every emitted row (a score is never a truth claim)
    rows = _method_rows()
    checks.append(("boundary held (candidate=true / serves_truth=false on every method row)",
                   all(r["candidate"] is True and r["serves_truth"] is False for r in rows)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - primitive_similarity_portfolio:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - primitive_similarity_portfolio: portfolio of similarity methods "
          f"(wired={wired_methods()}, planned={[n for n, s, *_ in METHODS if s == 'planned']}) with one importable "
          "API — similarity()/lsh_blocking()/nearest(); identical->1.0, disjoint->low, LSH blocks near-dups and "
          "prunes far pairs, edge_type_jaccard is composability-aware.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=DEFAULT_DATE)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    manifest = write_pack(date=args.date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
