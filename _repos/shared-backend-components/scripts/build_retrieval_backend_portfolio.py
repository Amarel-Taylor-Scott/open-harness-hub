#!/usr/bin/env python3
"""scripts.build_retrieval_backend_portfolio — ONE flexible, single-source portfolio for retrieval backends.

The embeddings red-team (2026-07-03) found the retrieval layer has FOUR disjoint embedding dims (64/256/384/768), the
stored primitive vectors (64-dim lexical hash) match none of the wired query-embedders, cosine silently returns 0.0
on dim mismatch, there is NO ANN index (brute-force seq scan), and the "named embedding profiles" are labels not
vectors. The fix is NOT "hardcode one embedder" — it is a PORTFOLIO with a single active default and a hard
dim-compatibility rule, so we resolve the mess without locking into one embedder / dim / index / reranker / search
method. New backends are rows here; flipping the active default is one field; everything else plugs in.

This module is BOTH the pack builder AND the importable RESOLVER (so it is not another declarative pack nobody joins
to): `resolve_active_backends()`, `active_embedder()`, `dim_compatible()`, `backends_of(kind)` are the single source
of truth the retrieval code should adopt. Status is honest: `wired` = runs today, `optional` = runs if a dep/daemon
is present, `planned` = not built. The active default MUST be `wired`. All rows candidate=true / serves_truth=false.
CLI: --self-test | --write [--date D].
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PACK_DIR = _resource("catalog") / "knowledge-packs" / "data" / "retrieval-backend-portfolio"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

# (id, model, dim, status, when_wins, cost, source_field, notes)
EMBEDDERS: list[tuple] = [
    ("lexical_hash_64", "deterministic-lexical-hash-v1", 64, "wired", "keyless offline floor; deterministic; exact-token overlap", "free", "edge_io+blackbox", "the ONLY vector actually persisted per primitive today; a signed bag-of-tokens, not learned semantics"),
    ("lexical_floor_256", "lexical-index-v1", 256, "wired", "component_search select_embedder('auto') default", "free", "edge_io", "what select_embedder returns today; 256-dim, disjoint from the 64-dim stored plane"),
    ("nomic_768", "nomic-embed-text", 768, "optional", "real local semantics when the Ollama daemon answers", "local-gpu", "edge_io", "advertised as 'the infra' but daemon-gated and NOT the vector currently searched"),
    ("minilm_384", "all-MiniLM-L6-v2", 384, "optional", "config default; runs only if sentence-transformers is installed", "cpu", "edge_io", "the DEFAULT_EMBEDDING_DIMENSIONS=384 config target; dep-gated"),
    ("bge_small_384", "bge-small-en-v1.5", 384, "planned", "stronger small dense embedder", "cpu", "edge_io", "named in config, not wired"),
    ("colbert_token", "colbert-v2", 128, "planned", "late-interaction multi-vector for high recall", "gpu", "edge_io+blackbox", "SOTA multi-vector; only defensible AFTER one single-vector index is proven"),
    ("splade_sparse", "splade-v3", 0, "planned", "learned sparse expansion", "gpu", "edge_io", "learned sparse; complements dense"),
]

# (id, backend, ann, scales_to, status, when_wins, notes)
INDEXES: list[tuple] = [
    ("mem_bruteforce", "in_memory", False, "~few thousand rows", "wired", "small corpora; the honest fallback", "_MemBackend returns the whole corpus and cosines each in Python — O(N), the cause of 15-23s/query at 113k"),
    ("pgvector_flat", "pgvector", False, "~tens of thousands", "optional", "pg present but no index built", "table has vector(dim) but NO CREATE INDEX -> sequential scan KNN"),
    ("pgvector_hnsw", "pgvector", True, "millions", "planned", "the FIX TARGET: real ANN over one embedding", "one CREATE INDEX USING hnsw (embedding vector_cosine_ops) turns dense search from O(N) to sublinear"),
    ("pgvector_ivfflat", "pgvector", True, "millions", "optional", "older ANN; on registry_records only", "one ivfflat DDL exists on a different table"),
    ("faiss_hnsw", "faiss", True, "hundreds of millions", "planned", "in-process ANN at very large scale", "no dep wired"),
]

# (id, model, status, when_wins, notes)
RERANKERS: list[tuple] = [
    ("lexical_bm25", "bm25-lite", "wired", "the only reranker that runs today", "LexicalReranker; 'auto' always returns this"),
    ("cross_encoder", "bge-reranker / sbert-crossencoder", "planned", "precision rerank of top-k after dense", "named in _MODEL_RERANKERS but NotWiredReranker raises; the correct next rung AFTER one dense index"),
    ("colbert_rerank", "colbert-v2", "planned", "late-interaction rerank", "not wired"),
    ("llm_judge_rerank", "bounded model", "planned", "peel-back rerank on ambiguous top-k only", "bounded, receipted; last resort"),
]

# (id, needs_embedder, needs_index, needs_reranker, status, when_wins)
SEARCH_METHODS: list[tuple] = [
    ("exact_edge", None, None, None, "wired", "the input/output edge matches a promoted route exactly"),
    ("blocking_lexical", "lexical_hash_64", "mem_bruteforce", "lexical_bm25", "wired", "keyword/label/contract-signature overlap (primitive_match blocking lanes) — the real hot path today"),
    ("edge_type_constrained", None, None, None, "planned", "prune to primitives whose input/output type_id is compatible (canonical-edge-type-vocabulary) — composability-aware retrieval"),
    ("dense_ann", "minilm_384", "pgvector_hnsw", "cross_encoder", "planned", "semantic recall at scale — needs ONE embedder + ONE ann index + ONE reranker, none wired together yet"),
    ("hybrid_rrf", "minilm_384", "pgvector_hnsw", "cross_encoder", "planned", "fuse lexical + dense (RRF) — only adds value when the dense leg is a DIFFERENT signal (today RRF fuses lexical+lexical)"),
    ("negative_memory_suppress", None, None, None, "planned", "demote known-failure classes before ranking"),
]

# SINGLE SOURCE of the active default per kind — the honest current reality. Change ONE field to switch; the checker
# forbids an active default that is not `wired`.
ACTIVE_DEFAULT: dict[str, str] = {
    "embedder": "lexical_hash_64",
    "index": "mem_bruteforce",
    "reranker": "lexical_bm25",
    "search_method": "blocking_lexical",
}


def _embedder_rows() -> list[dict[str, Any]]:
    return [{"record_type": "retrieval_embedder", "backend_id": i, "model": m, "dim": d, "status": s,
             "when_wins": w, "cost": c, "source_field": f, "notes": n,
             "is_active_default": i == ACTIVE_DEFAULT["embedder"], **BOUNDARY}
            for i, m, d, s, w, c, f, n in EMBEDDERS]


def _index_rows() -> list[dict[str, Any]]:
    return [{"record_type": "retrieval_index", "backend_id": i, "backend": b, "is_ann": a, "scales_to": sc,
             "status": s, "when_wins": w, "notes": n, "is_active_default": i == ACTIVE_DEFAULT["index"], **BOUNDARY}
            for i, b, a, sc, s, w, n in INDEXES]


def _reranker_rows() -> list[dict[str, Any]]:
    return [{"record_type": "retrieval_reranker", "backend_id": i, "model": m, "status": s, "when_wins": w,
             "notes": n, "is_active_default": i == ACTIVE_DEFAULT["reranker"], **BOUNDARY}
            for i, m, s, w, n in RERANKERS]


def _search_method_rows() -> list[dict[str, Any]]:
    return [{"record_type": "retrieval_search_method", "method_id": i, "needs_embedder": e, "needs_index": ix,
             "needs_reranker": r, "status": s, "when_wins": w,
             "is_active_default": i == ACTIVE_DEFAULT["search_method"], **BOUNDARY}
            for i, e, ix, r, s, w in SEARCH_METHODS]


def _dim_rule_rows() -> list[dict[str, Any]]:
    return [{
        "record_type": "retrieval_dim_compatibility_rule",
        "rule": "A query vector may only be cosine-compared against index vectors produced by the SAME embedder "
                "(same model + same dim). Matching across dims is forbidden. Cosine MUST raise / skip-with-reason on "
                "dim mismatch, never silently return 0.0 (a silent zero lets a dense plane lie green).",
        "active_embedder": ACTIVE_DEFAULT["embedder"],
        "active_dim": next(d for i, _m, d, *_ in EMBEDDERS if i == ACTIVE_DEFAULT["embedder"]),
        "known_disjoint_dims": sorted({d for _i, _m, d, *_ in EMBEDDERS if d}),
        "adoption": "src/teleon/retrieval (embedding_port/hybrid/pgvector_index/primitive_match) should import "
                    "resolve_active_backends() from this module and tag every stored vector + every query with the "
                    "active embedder_id+dim; a mismatch is a bug surfaced, not a silent 0.0.",
        **BOUNDARY,
    }]


JSONL_BUILDERS: dict[str, Callable[[], list[dict[str, Any]]]] = {
    "embedders.jsonl": _embedder_rows,
    "indexes.jsonl": _index_rows,
    "rerankers.jsonl": _reranker_rows,
    "search_methods.jsonl": _search_method_rows,
    "dim_compatibility_rule.jsonl": _dim_rule_rows,
}


# ── the importable RESOLVER (single source of truth; NOT a dead pack) ──
def backends_of(kind: str) -> list[dict[str, Any]]:
    return {"embedder": _embedder_rows, "index": _index_rows, "reranker": _reranker_rows,
            "search_method": _search_method_rows}[kind]()


def resolve_active_backends() -> dict[str, dict[str, Any]]:
    """The single source of truth for which retrieval backends are active TODAY. Retrieval code should import this."""
    out: dict[str, dict[str, Any]] = {}
    for kind in ("embedder", "index", "reranker", "search_method"):
        rows = backends_of(kind)
        key = "backend_id" if kind != "search_method" else "method_id"
        active = next((r for r in rows if r["is_active_default"]), None)
        out[kind] = active or {}
    return out


def active_embedder() -> dict[str, Any]:
    return resolve_active_backends()["embedder"]


def dim_compatible(dim_a: int, dim_b: int) -> bool:
    """True only if two vectors share a dimension — the guard that must replace silent-zero cosine."""
    return dim_a == dim_b and dim_a > 0


def build_pack() -> dict[str, list[dict[str, Any]]]:
    return {n: b() for n, b in JSONL_BUILDERS.items()}


def build_manifest(pack: dict[str, list[dict[str, Any]]], *, date: str) -> dict[str, Any]:
    rc = {n: len(r) for n, r in pack.items()}
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for n in sorted(pack) for r in pack[n])
    return {
        "record_type": "retrieval_backend_portfolio_manifest",
        "pack_id": "retrieval-backend-portfolio", "generator": "scripts/build_retrieval_backend_portfolio.py",
        "generated_utc": date, "row_counts": rc, "total_rows": sum(rc.values()),
        "embedder_count": len(pack["embedders.jsonl"]), "index_count": len(pack["indexes.jsonl"]),
        "active_defaults": ACTIVE_DEFAULT,
        "wired_embedders": sorted(r["backend_id"] for r in pack["embedders.jsonl"] if r["status"] == "wired"),
        "ann_indexes_wired": sorted(r["backend_id"] for r in pack["indexes.jsonl"] if r["is_ann"] and r["status"] == "wired"),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str) -> dict[str, Any]:
    pack = build_pack()
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    for n, rows in pack.items():
        (PACK_DIR / n).write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    manifest = build_manifest(pack, date=date)
    (PACK_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def self_test() -> int:
    pack = build_pack()
    ids = {k: {(r.get("backend_id") or r.get("method_id")) for r in v} for k, v in {
        "embedder": pack["embedders.jsonl"], "index": pack["indexes.jsonl"],
        "reranker": pack["rerankers.jsonl"], "search_method": pack["search_methods.jsonl"]}.items()}
    active = resolve_active_backends()
    checks = [
        ("every kind is a portfolio (>=3 options)", all(len(v) >= 3 for v in ids.values())),
        ("each active default exists", all(ACTIVE_DEFAULT[k] in ids[k] for k in ACTIVE_DEFAULT)),
        ("each active default is WIRED (not planned/optional)", all(
            active[k].get("status") == "wired" for k in ("embedder", "index", "reranker", "search_method"))),
        ("search_method backend refs resolve", all(
            (r["needs_embedder"] is None or r["needs_embedder"] in ids["embedder"])
            and (r["needs_index"] is None or r["needs_index"] in ids["index"])
            and (r["needs_reranker"] is None or r["needs_reranker"] in ids["reranker"])
            for r in pack["search_methods.jsonl"])),
        ("dim rule present + names the active dim + the disjoint dims", (lambda r: r["active_dim"] == 64 and set(r["known_disjoint_dims"]) >= {64, 256, 384, 768})(pack["dim_compatibility_rule.jsonl"][0])),
        ("dim_compatible guard works", dim_compatible(768, 768) and not dim_compatible(64, 768) and not dim_compatible(0, 0)),
        ("resolver returns a wired embedder importable as single source", active["embedder"].get("model") == "deterministic-lexical-hash-v1"),
        ("planned SOTA methods present but marked planned (flexible, not locked)", all(
            next(r for r in pack["search_methods.jsonl"] if r["method_id"] == m)["status"] == "planned"
            for m in ("dense_ann", "hybrid_rrf", "edge_type_constrained"))),
        ("no ANN index is wired yet (honest)", not any(r["is_ann"] and r["status"] == "wired" for r in pack["indexes.jsonl"])),
        ("boundary held", all(r["candidate"] is True and r["serves_truth"] is False for rows in pack.values() for r in rows)),
    ]
    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - retrieval_backend_portfolio:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - retrieval_backend_portfolio: portfolio of embedders/indexes/rerankers/search-methods with a "
          "single WIRED active default per kind, a hard dim-compat rule, and an importable resolver — flexible, "
          "not locked to one embedder/dim/index/method.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)
    if args.self_test and not args.write:
        return self_test()
    date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
    manifest = write_pack(date=date)
    print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
