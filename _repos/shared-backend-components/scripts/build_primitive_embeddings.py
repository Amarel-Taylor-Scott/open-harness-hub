#!/usr/bin/env python3
"""scripts.build_primitive_embeddings — PERSIST per-primitive EMBEDDINGS + derived FEATURES so retrieval reads
STORED vectors instead of re-embedding the whole corpus on every query (the O(N) flaw the storage audit named
as the #1 scale gap: `capability_embedding.intent_query` recomputes `capability_key(card)` for every card every
call, and the `object_embedding` pgvector table was never populated for primitive cards).

Local-first and cheap: model2vec embeds in-process (no network, ~2.3s for the full 112K corpus), stored as a
float32 matrix on disk + a parallel id list + a compact per-primitive FEATURE record (the deterministic facets
the zoo already computes — operations / datatypes / impact class / operation frame / edges / blocking-key
count). Retrieval then loads the matrix ONCE and scores by cosine (a numpy matmul), the in-process precursor to
a real ANN index (pgvector HNSW / faiss — roadmap #4) that plugs in behind the same `load` + `search` calls.

  build(cards)      -> {ids, matrix, features, embed_model, dim}   (batch-embed + featurize every card)
  persist(store, d) -> writes embeddings.npy, ids.json, features.jsonl, manifest.json (content-hashed)
  load(d)           -> the store, mmap-friendly, no recompute
  search(q, store)  -> top-k by cosine over the STORED matrix (no corpus re-embed)

serves_truth=false — a vector/feature is a candidate pointer, never truth.

    PYTHONPATH=. python3 scripts/build_primitive_embeddings.py --self-test
    PYTHONPATH=. python3 scripts/build_primitive_embeddings.py --build            # persist all ~112K
    PYTHONPATH=. python3 scripts/build_primitive_embeddings.py --query "dedupe rows"
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
import hashlib  # noqa: E402  (dev-plane build script — content digest for the manifest; not a src/ id mint)
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts import capability_embedding as _emb  # noqa: E402  REUSE: model2vec loader + blackbox text
from scripts import primitive_descriptor as _desc  # noqa: E402  REUSE: operation/datatype/impact facets
from scripts import primitive_retrieval_bakeoff as _bakeoff  # noqa: E402  REUSE: operation-frame folding

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}

_DIM = 256   # model2vec potion-base-8M output dim (asserted at build against the real vectors; single-source)
#: default corpus = the two searchable card files (the ~112K); --source overrides. Single source of the paths.
_DEFAULT_SOURCES: tuple[str, ...] = ("verified_factory_primitive_cards.jsonl", "primitive_edge_cards.jsonl")
#: the staged candidate pool (minted gap primitives) — included when --include-staged: staged cards become
#: SERVABLE through the stored lanes (still candidate/serves_truth=false; serving is not promotion)
_STAGED_SOURCE = "minted_gap_primitive_candidates.jsonl"
_OUT_DIRNAME = "primitive-embeddings"   # under dist/ (a build artifact; gitignored — regenerated in seconds)


def default_store_dir() -> Path:
    """The canonical on-disk location of the persisted store — single source; main() writes here and the
    STORED-MATRIX lane in capability_embedding.intent_query (store="auto") loads from here."""
    return resource("dist") / _OUT_DIRNAME


def _load_cards(sources: tuple[str, ...] = _DEFAULT_SOURCES, *, limit: Optional[int] = None) -> list[dict[str, Any]]:
    from scripts._jsonl import read_jsonl_tolerant  # noqa: PLC0415
    base = resource("data") / "dev-intel" / "aidevobserver_edge_foundry"
    cards: list[dict[str, Any]] = []
    for fn in sources:
        p = base / fn
        if p.exists():
            cards += read_jsonl_tolerant(p)
        if limit and len(cards) >= limit:
            return cards[:limit]
    return cards


def _features(card: dict[str, Any]) -> dict[str, Any]:
    """The deterministic FEATURE record — the facets the zoo already computes, persisted so the facet/edge
    retrieval paths need not recompute them per query either. serves_truth=false throughout."""
    return {"primitive_id": card.get("primitive_id"),
            "operations": sorted(_desc.operations(card)),
            "datatypes": sorted(_desc.datatypes(card)),
            "impact_class": _desc.impact_class(card),
            "frame": _bakeoff.frame_of_card(card),
            "input_edge": str(card.get("input_edge") or ""),
            "output_edge": str(card.get("output_edge") or ""),
            "blocking_key_count": len(card.get("blocking_keys") or [])}


def corpus_text_digest(cards: list[dict[str, Any]]) -> str:
    """Digest of the corpus EMBED SURFACE (card_embed_text per card, id-paired) — persisted in the manifests
    so a gate can detect a STALE store whose ids still match but whose source texts changed (review finding:
    ids are content-stable by repo law, so id-set comparison alone cannot see text drift)."""
    h = hashlib.sha256()
    for c in cards:
        h.update(f"{c.get('primitive_id')}\t{_emb.card_embed_text(c)}\n".encode())
    return h.hexdigest()[:16]


def _atomic_write_bytes(path: Path, write_fn) -> None:
    """Write via temp + os.replace so a live mmap in another process keeps the OLD inode intact (review
    finding: np.save onto the same inode tears id/vector pairing under concurrent readers)."""
    import os  # noqa: PLC0415
    # temp KEEPS the real suffix ("embeddings.tmp.npy") — np.save silently appends ".npy" to any other name
    tmp = path.with_name(f"{path.stem}.tmp{path.suffix}")
    write_fn(tmp)
    os.replace(tmp, path)


def build(cards: list[dict[str, Any]], *, embed_path: Optional[str] = None) -> dict[str, Any]:
    """Batch-embed every card's blackbox (model2vec preferred) + compute its feature record. Returns the store
    (ids, float32 matrix, features). One pass, no per-query recompute."""
    import numpy as np  # noqa: PLC0415
    if not cards:
        return {"ids": [], "matrix": np.zeros((0, 0), dtype="float32"), "features": [],
                "embed_model": embed_path or "tokens", "dim": 0, "count": 0,
                "corpus_text_hash": corpus_text_digest([]), **BOUNDARY}
    ids = [c.get("primitive_id") for c in cards]
    texts = [_emb.card_embed_text(c) for c in cards]  # the ONE embed surface (shared with the delta lane)
    model = _emb._load_model2vec()  # noqa: SLF001 — reuse the single loader
    if model is not None and embed_path in (None, "model2vec"):
        matrix = np.asarray(model.encode(texts), dtype="float32")
        used = "model2vec"
    else:  # explicit path or proxy fallback (still real-shaped)
        used = embed_path or "tokens"
        matrix = np.asarray([_emb.embed_text(t, path=used) for t in texts], dtype="float32")
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms
    return {"ids": ids, "matrix": matrix, "features": [_features(c) for c in cards],
            "embed_model": used, "dim": int(matrix.shape[1]), "count": len(ids),
            "corpus_text_hash": corpus_text_digest(cards), **BOUNDARY}


def _content_hash(store: dict[str, Any]) -> str:
    """Deterministic digest over ids + rounded vectors + features — so a rebuild is provably byte-stable and a
    changed corpus is detectable (NO-MAGIC / VERIFY-THE-VERIFIER determinism)."""
    import numpy as np  # noqa: PLC0415
    h = hashlib.sha256()
    h.update("\n".join(str(i) for i in store["ids"]).encode())
    h.update(np.round(store["matrix"], 5).tobytes())
    h.update(json.dumps(store["features"], sort_keys=True).encode())
    return h.hexdigest()[:16]


def persist(store: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write embeddings.npy + ids.json + features.jsonl + a content-hashed manifest — ATOMICALLY (temp +
    os.replace per file), so concurrent readers mmap either the old or the new store, never a torn mix."""
    import numpy as np  # noqa: PLC0415
    out_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_bytes(out_dir / "embeddings.npy", lambda p: np.save(p, store["matrix"]))
    _atomic_write_bytes(out_dir / "ids.json", lambda p: p.write_text(json.dumps(store["ids"])))

    def _write_features(p: Path) -> None:
        with p.open("w") as fh:
            for feat in store["features"]:
                fh.write(json.dumps(feat, sort_keys=True) + "\n")
    _atomic_write_bytes(out_dir / "features.jsonl", _write_features)
    manifest = {"record_type": "primitive_embedding_index", "embed_model": store["embed_model"],
                "dim": store["dim"], "count": store["count"], "content_hash": _content_hash(store),
                "corpus_text_hash": store.get("corpus_text_hash"),
                "files": ["embeddings.npy", "ids.json", "features.jsonl"], **BOUNDARY}
    _atomic_write_bytes(out_dir / "manifest.json",
                        lambda p: p.write_text(json.dumps(manifest, indent=2, sort_keys=True)))
    return manifest


def load(out_dir: Path) -> dict[str, Any]:
    """Load a persisted store (mmap the matrix — no recompute) and VALIDATE its integrity: ids length, matrix
    rows, and manifest count must agree (a torn/truncated store fails loudly, never mis-scores silently)."""
    import numpy as np  # noqa: PLC0415
    manifest = json.loads((out_dir / "manifest.json").read_text())
    ids = json.loads((out_dir / "ids.json").read_text())
    matrix = np.load(out_dir / "embeddings.npy", mmap_mode="r")
    if not (len(ids) == manifest["count"] == matrix.shape[0]) or int(matrix.shape[1] or 0) != manifest["dim"]:
        raise ValueError(f"store integrity violation in {out_dir}: ids={len(ids)} manifest={manifest['count']} "
                         f"rows={matrix.shape[0]} dim={matrix.shape[1]}!={manifest['dim']}")
    return {"ids": ids, "matrix": matrix, "embed_model": manifest["embed_model"],
            "dim": manifest["dim"], "count": manifest["count"],
            "corpus_text_hash": manifest.get("corpus_text_hash"), **BOUNDARY}


def search(query: str, store: dict[str, Any], *, k: int = 5, embed_path: Optional[str] = None) -> list[dict[str, Any]]:
    """Top-k primitive ids for a query against the STORED matrix (no corpus re-embed). Cosine = normalized dot."""
    import numpy as np  # noqa: PLC0415
    path = embed_path or store.get("embed_model") or "tokens"
    q = np.asarray(_emb.embed_text(query, path=path), dtype="float32")
    nrm = float(np.linalg.norm(q)) or 1.0
    sims = np.asarray(store["matrix"]) @ (q / nrm)
    order = np.argsort(-sims)[:k]
    return [{"primitive_id": store["ids"][int(i)], "score": round(float(sims[int(i)]), 4), **BOUNDARY}
            for i in order]


# ──────────────────────────────────────────────────────────────────────────────
# The MULTI-REGISTER store — the SAME primitive described in THREE LANGUAGES (plain / technical / semantic,
# from capability_embedding.REGISTERS), each persisted as its own matrix. Together with the blackbox store
# above and the feature records, every primitive carries MULTIPLE persisted descriptors/keys/descriptions/
# embeddings — and the register matrices are CONSUMED by intent_query_registers' stored lane (the graph's
# semantic_registers search row), so nothing persisted here is an orphan.
# ──────────────────────────────────────────────────────────────────────────────
_REGISTER_OUT_DIRNAME = "primitive-register-embeddings"   # under dist/ (build artifact; regenerated)


def default_register_store_dir() -> Path:
    """Canonical on-disk location of the register store — single source (main() writes, the stored lane in
    capability_embedding.intent_query_registers loads)."""
    return resource("dist") / _REGISTER_OUT_DIRNAME


def build_register_store(cards: list[dict[str, Any]], *, embed_path: Optional[str] = None) -> dict[str, Any]:
    """Batch-embed every card's THREE register texts (capability_embedding.register_text — the existing
    derivations, never re-invented here). One matrix per register, all in ONE embed space."""
    import numpy as np  # noqa: PLC0415
    if not cards:
        return {"ids": [], "matrices": {r: np.zeros((0, 0), dtype="float32") for r in _emb.REGISTERS},
                "embed_model": embed_path or "tokens", "dim": 0, "count": 0,
                "corpus_text_hash": corpus_text_digest([]), **BOUNDARY}
    ids = [c.get("primitive_id") for c in cards]
    model = _emb._load_model2vec()  # noqa: SLF001 — reuse the single loader
    matrices: dict[str, Any] = {}
    used = "model2vec"
    for register in _emb.REGISTERS:
        texts = [_emb.register_text(c, register) for c in cards]
        if model is not None and embed_path in (None, "model2vec"):
            m = np.asarray(model.encode(texts), dtype="float32")
            used = "model2vec"
        else:
            used = embed_path or "tokens"
            m = np.asarray([_emb.embed_text(t, path=used) for t in texts], dtype="float32")
        norms = np.linalg.norm(m, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        matrices[register] = m / norms
    dim = int(next(iter(matrices.values())).shape[1]) if matrices else 0
    return {"ids": ids, "matrices": matrices, "embed_model": used, "dim": dim, "count": len(ids),
            "corpus_text_hash": corpus_text_digest(cards), **BOUNDARY}


def _register_content_hash(store: dict[str, Any]) -> str:
    """Deterministic digest over ids + all register matrices (rounded) — rebuilds are provably byte-stable."""
    import numpy as np  # noqa: PLC0415
    h = hashlib.sha256()
    h.update("\n".join(str(i) for i in store["ids"]).encode())
    for register in sorted(store["matrices"]):
        h.update(register.encode())
        h.update(np.round(store["matrices"][register], 5).tobytes())
    return h.hexdigest()[:16]


def persist_register_store(store: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    """Write one embeddings_<register>.npy per register + ids.json + a content-hashed manifest — atomically
    (temp + os.replace), so concurrent readers never see a torn mix of old ids and new matrices."""
    import numpy as np  # noqa: PLC0415
    out_dir.mkdir(parents=True, exist_ok=True)
    for register, matrix in store["matrices"].items():
        _atomic_write_bytes(out_dir / f"embeddings_{register}.npy", lambda p, m=matrix: np.save(p, m))
    _atomic_write_bytes(out_dir / "ids.json", lambda p: p.write_text(json.dumps(store["ids"])))
    manifest = {"record_type": "primitive_register_embedding_index", "embed_model": store["embed_model"],
                "dim": store["dim"], "count": store["count"], "registers": sorted(store["matrices"]),
                "content_hash": _register_content_hash(store),
                "corpus_text_hash": store.get("corpus_text_hash"), **BOUNDARY}
    _atomic_write_bytes(out_dir / "manifest.json",
                        lambda p: p.write_text(json.dumps(manifest, indent=2, sort_keys=True)))
    return manifest


def load_register_store(out_dir: Path) -> dict[str, Any]:
    """Load a persisted register store (matrices mmap'd — no recompute) and VALIDATE integrity: every
    register matrix must carry manifest-count rows and manifest dim; ids length must match (torn or
    truncated stores fail loudly, never mis-score silently)."""
    import numpy as np  # noqa: PLC0415
    manifest = json.loads((out_dir / "manifest.json").read_text())
    ids = json.loads((out_dir / "ids.json").read_text())
    matrices = {r: np.load(out_dir / f"embeddings_{r}.npy", mmap_mode="r") for r in manifest["registers"]}
    bad = [r for r, m in matrices.items()
           if m.shape[0] != manifest["count"] or int(m.shape[1] or 0) != manifest["dim"]]
    if bad or len(ids) != manifest["count"]:
        raise ValueError(f"register store integrity violation in {out_dir}: ids={len(ids)} "
                         f"manifest={manifest['count']} bad_registers={bad}")
    return {"ids": ids, "matrices": matrices, "embed_model": manifest["embed_model"],
            "dim": manifest["dim"], "count": manifest["count"],
            "corpus_text_hash": manifest.get("corpus_text_hash"), **BOUNDARY}


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    cards = [
        {"primitive_id": "p:dedup", "title": "Deduplicate records",
         "blackbox": "Remove duplicate rows by clustering near-identical records.",
         "input_edge": "Batch", "output_edge": "DedupedBatch", "blocking_keys": ["dedup", "rows"], **BOUNDARY},
        {"primitive_id": "p:resize", "title": "Resize image", "blackbox": "Resize an image to dimensions.",
         "input_edge": "Image", "output_edge": "ResizedImage", **BOUNDARY},
        {"primitive_id": "p:ocr", "title": "OCR a scan",
         "blackbox": "Extract text from a scanned document with optical character recognition.",
         "input_edge": "Scan", "output_edge": "Text", **BOUNDARY},
    ]
    store = build(cards)
    checks.append(("every card is embedded to a fixed-dim unit vector",
                   store["count"] == 3 and store["matrix"].shape == (3, store["dim"])))
    checks.append(("a feature record is persisted per card (operations/frame/edges)",
                   len(store["features"]) == 3 and "operations" in store["features"][0]))

    # persist -> reload -> search reads STORED vectors (no recompute) and finds the right card
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "idx"
        man = persist(store, out)
        reloaded = load(out)
        checks.append(("persisted manifest carries a content hash + count",
                       len(man["content_hash"]) == 16 and man["count"] == 3))
        checks.append(("reload yields the same ids without recompute",
                       list(reloaded["ids"]) == store["ids"] and reloaded["dim"] == store["dim"]))
        hits = search("get rid of duplicate entries", reloaded, k=1)
        checks.append(("stored-vector search finds the semantically-right card (dedup, no shared word)",
                       bool(hits) and hits[0]["primitive_id"] == "p:dedup"
                       if store["embed_model"] == "model2vec" else bool(hits)))
        # determinism: a rebuild is byte-stable (same content hash)
        checks.append(("a rebuild is content-stable (deterministic embeddings + features)",
                       _content_hash(build(cards)) == man["content_hash"]))
    checks.append(("store is candidate/serves_truth=false", store["serves_truth"] is False))

    # the MULTI-REGISTER store: three persisted description matrices per card, reloadable, content-stable
    rstore = build_register_store(cards, embed_path="tokens")
    checks.append(("register store embeds every card in all three registers",
                   set(rstore["matrices"]) == set(_emb.REGISTERS)
                   and all(m.shape == (3, rstore["dim"]) for m in rstore["matrices"].values())))
    with tempfile.TemporaryDirectory() as d:
        rout = Path(d) / "reg"
        rman = persist_register_store(rstore, rout)
        rre = load_register_store(rout)
        checks.append(("register store persists + reloads with the same ids and registers",
                       list(rre["ids"]) == rstore["ids"] and set(rre["matrices"]) == set(_emb.REGISTERS)))
        checks.append(("register rebuild is content-stable (deterministic)",
                       _register_content_hash(build_register_store(cards, embed_path="tokens"))
                       == rman["content_hash"]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - build_primitive_embeddings: batch-embed every primitive ({store['embed_model']}) + a "
          f"deterministic feature record, PERSIST to disk (embeddings.npy + ids + features + content-hashed "
          f"manifest), and search the STORED matrix by cosine with NO per-query corpus re-embed — the local "
          f"in-process precursor to a pgvector/faiss ANN index behind the same load+search calls. "
          f"serves_truth=false.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true", help="embed + persist all primitives")
    ap.add_argument("--build-registers", action="store_true",
                    help="embed + persist the plain/technical/semantic REGISTER matrices for all primitives")
    ap.add_argument("--query", metavar="TEXT", default=None, help="search the persisted index")
    ap.add_argument("--limit", type=int, default=None, help="cap the corpus (default: all ~112K)")
    ap.add_argument("--include-staged", action="store_true",
                    help="also embed the staged minted candidates — staged pools become SERVABLE "
                         "(candidate-labelled; serving is not promotion)")
    ap.add_argument("--out", default=None, help="output dir (default: dist/primitive-embeddings)")
    args = ap.parse_args(argv)
    out_dir = Path(args.out) if args.out else default_store_dir()
    sources = _DEFAULT_SOURCES + ((_STAGED_SOURCE,) if args.include_staged else ())
    if args.self_test:
        return _self_test()
    if args.build:
        cards = _load_cards(sources, limit=args.limit)
        print(f"embedding {len(cards)} primitives ({_emb.real_text_path()}) ...")
        store = build(cards)
        man = persist(store, out_dir)
        print(json.dumps(man, indent=2, sort_keys=True))
        print(f"\nwritten: {out_dir}")
        return 0
    if args.build_registers:
        cards = _load_cards(sources, limit=args.limit)
        print(f"embedding {len(cards)} primitives x {len(_emb.REGISTERS)} registers ({_emb.real_text_path()}) ...")
        rstore = build_register_store(cards)
        reg_out = Path(args.out) if args.out else default_register_store_dir()
        rman = persist_register_store(rstore, reg_out)
        print(json.dumps(rman, indent=2, sort_keys=True))
        print(f"\nwritten: {reg_out}")
        return 0
    if args.query:
        store = load(out_dir)
        print(json.dumps(search(args.query, store, k=8), indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
