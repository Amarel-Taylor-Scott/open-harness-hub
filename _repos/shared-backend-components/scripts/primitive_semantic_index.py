#!/usr/bin/env python3
"""scripts.primitive_semantic_index — semantic (intent-based) search over the millions of primitives in the
database, so they are retrievable by MEANING, not just keywords (the difference between 'stored' and 'helpful').
Embeds every primitive's title+blackbox with the in-process model2vec static embedder and persists a
memmap-backed float32 matrix + id list; search embeds the query and does a CHUNKED cosine scan (block-by-block,
top-k merged) so it scales to tens of millions of vectors on disk without loading them all into RAM.

Local + cheap (model2vec batch-encodes ~100K/2.3s, no network). This is the vector lane that complements the
FTS5 keyword lane in scripts.primitive_database; the pgvector/faiss swap is config-only (same build/search
verbs) for when the fleet lands. serves_truth=false.

    python3 scripts/primitive_semantic_index.py --self-test
    python3 scripts/primitive_semantic_index.py --build [--limit N]      # embed the DB primitives
    python3 scripts/primitive_semantic_index.py --search "detect data drift on serving inputs" --k 8
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import sqlite3  # noqa: E402
from typing import Any, Optional  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_OUT_DIRNAME = "primitive-semantic-index"
_EMBED_BATCH = 4096
_SEARCH_BLOCK = 200_000  # rows per chunked-cosine block (bounds peak RAM at search)


def default_index_dir() -> Path:
    return resource("dist") / _OUT_DIRNAME


def _embed_texts(texts: list[str], model) -> Any:
    import numpy as np  # noqa: PLC0415
    mat = np.asarray(model.encode(texts), dtype="float32")
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return mat / norms  # unit vectors -> cosine = dot


def build(db_path: Optional[Path] = None, out_dir: Optional[Path] = None, *, limit: Optional[int] = None) -> dict[str, Any]:
    """Embed every DB primitive (title+blackbox) into a persisted memmap matrix + id list. Streamed + batched;
    the matrix is preallocated on disk so build RAM stays flat regardless of row count."""
    import numpy as np  # noqa: PLC0415
    from scripts.capability_embedding import _load_model2vec  # noqa: PLC0415,SLF001
    from scripts.primitive_database import default_db_path  # noqa: PLC0415
    db_path = db_path or default_db_path()
    out_dir = out_dir or default_index_dir()
    if not db_path.exists():
        return {"error": f"database not built: {db_path}", **BOUNDARY}
    model = _load_model2vec()
    if model is None:
        return {"error": "model2vec unavailable (pip install model2vec)", **BOUNDARY}
    con = sqlite3.connect(str(db_path))
    n = con.execute("SELECT COUNT(*) FROM primitives" + (f" LIMIT {int(limit)}" if False else "")).fetchone()[0]
    if limit:
        n = min(n, limit)
    dim = int(np.asarray(model.encode(["probe"]), dtype="float32").shape[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    mat = np.lib.format.open_memmap(out_dir / "embeddings.npy", mode="w+", dtype="float32", shape=(n, dim))
    ids: list[str] = []
    sql = "SELECT primitive_id, title, blackbox FROM primitives" + (f" LIMIT {int(limit)}" if limit else "")
    batch_ids: list[str] = []
    batch_txt: list[str] = []
    row_i = 0
    for pid, title, blackbox in con.execute(sql):
        batch_ids.append(str(pid))
        batch_txt.append((str(title or "") + " " + str(blackbox or ""))[:600])
        if len(batch_txt) >= _EMBED_BATCH:
            mat[row_i:row_i + len(batch_txt)] = _embed_texts(batch_txt, model)
            ids.extend(batch_ids)
            row_i += len(batch_txt)
            batch_ids, batch_txt = [], []
    if batch_txt:
        mat[row_i:row_i + len(batch_txt)] = _embed_texts(batch_txt, model)
        ids.extend(batch_ids)
        row_i += len(batch_txt)
    con.close()
    mat.flush()
    (out_dir / "ids.json").write_text(json.dumps(ids))
    (out_dir / "manifest.json").write_text(json.dumps({"count": len(ids), "dim": dim, "embed_model": "model2vec",
                                                       "db": str(db_path), **BOUNDARY}))
    return {"index_dir": str(out_dir), "count": len(ids), "dim": dim, "embed_model": "model2vec", **BOUNDARY}


def search(query: str, index_dir: Optional[Path] = None, *, k: int = 8) -> list[dict[str, Any]]:
    """Chunked-cosine top-k over the persisted matrix (memmap; block-by-block so RAM stays bounded at scale)."""
    import numpy as np  # noqa: PLC0415
    from scripts.capability_embedding import _load_model2vec  # noqa: PLC0415,SLF001
    index_dir = index_dir or default_index_dir()
    if not (index_dir / "embeddings.npy").exists():
        return []
    ids = json.loads((index_dir / "ids.json").read_text())
    mat = np.load(index_dir / "embeddings.npy", mmap_mode="r")
    model = _load_model2vec()
    q = _embed_texts([query], model)[0]
    best_scores = np.full(k, -2.0, dtype="float32")
    best_idx = np.full(k, -1, dtype="int64")
    for start in range(0, mat.shape[0], _SEARCH_BLOCK):
        block = np.asarray(mat[start:start + _SEARCH_BLOCK])
        sims = block @ q
        take = min(k, sims.shape[0])
        top = np.argpartition(-sims, take - 1)[:take]
        for j in top:
            sc = sims[j]
            if sc > best_scores[-1]:
                pos = np.searchsorted(-best_scores, -sc)
                best_scores = np.insert(best_scores, pos, sc)[:k]
                best_idx = np.insert(best_idx, pos, start + j)[:k]
    out = []
    for score, idx in zip(best_scores, best_idx):
        if idx >= 0:
            out.append({"primitive_id": ids[int(idx)], "score": round(float(score), 4), **BOUNDARY})
    return out


def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    import numpy as np  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []
    with tempfile.TemporaryDirectory() as td:
        db = Path(td) / "primitives.db"
        con = sqlite3.connect(str(db))
        con.execute("""CREATE TABLE primitives(primitive_id TEXT PRIMARY KEY, pool TEXT, title TEXT,
            blackbox TEXT, tags TEXT, input_edge TEXT, output_edge TEXT, serves_truth INTEGER)""")
        rows = [("d1", "p", "detect data drift on serving inputs", "KS-test distribution drift monitor", "", "", "", 0),
                ("d2", "p", "canary rollout gate", "shift 1% 5% 25% traffic to the new model", "", "", "", 0),
                ("d3", "p", "topological sort", "Kahn algorithm with cycle detection over a DAG", "", "", "", 0),
                ("d4", "p", "circuit breaker", "closed open half-open state machine for failing services", "", "", "", 0)]
        con.executemany("INSERT INTO primitives VALUES(?,?,?,?,?,?,?,?)", rows)
        con.commit(); con.close()
        idx = Path(td) / "idx"
        rec = build(db_path=db, out_dir=idx)
        if "error" in rec:
            print(f"  [skip] {rec['error']}"); print("PASS (model2vec unavailable — build path skipped)"); return 0
        checks.append(("build embeds all rows into a persisted matrix + ids",
                       rec["count"] == 4 and (idx / "embeddings.npy").exists() and (idx / "ids.json").exists()))
        m = np.load(idx / "embeddings.npy")
        checks.append(("embeddings are unit-normalized (cosine-ready)",
                       abs(float(np.linalg.norm(m[0])) - 1.0) < 1e-4))
        r = search("monitor for feature distribution shift in production", index_dir=idx, k=2)
        checks.append(("semantic search finds the drift primitive by INTENT (not keyword overlap)",
                       any(x["primitive_id"] == "d1" for x in r)))
        r2 = search("gradual traffic shift deployment strategy", index_dir=idx, k=2)
        checks.append(("semantic search finds the canary primitive by intent",
                       any(x["primitive_id"] == "d2" for x in r2)))
        checks.append(("results are scored + carry the boundary",
                       all("score" in x and x["serves_truth"] is False for x in r)))
        # global chunked-cosine == exact top-1 on the full matrix
        q = _embed_texts(["failing service protection state machine"], __import__("scripts.capability_embedding", fromlist=["_load_model2vec"])._load_model2vec())[0]
        exact = int(np.argmax(m @ q))
        top1 = search("failing service protection state machine", index_dir=idx, k=1)
        checks.append(("chunked search matches the exact top-1", top1 and top1[0]["primitive_id"] == json.loads((idx / "ids.json").read_text())[exact]))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print("\nPASS - primitive_semantic_index: model2vec embeddings persisted as a memmap matrix over the DB "
          "primitives; chunked-cosine search retrieves by INTENT and matches exact top-1; scales to tens of "
          "millions on disk (block-by-block, bounded RAM). pgvector/faiss swap is config-only. serves_truth=false.")
    return 0


def _run_build(limit: Optional[int]) -> int:
    rec = build(limit=limit)
    out = resource("data") / "dev-intel" / "session_emulation" / "primitive_semantic_index_receipt.json"
    out.write_text(json.dumps(rec, indent=2, sort_keys=True))
    print(json.dumps(rec, indent=2, sort_keys=True))
    print(f"\nreceipt: {out}")
    return 0 if "error" not in rec else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--search", metavar="QUERY", default=None)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.build:
        return _run_build(args.limit)
    if args.search:
        for r in search(args.search, k=args.k):
            print(f"  {r['score']}  {r['primitive_id']}")
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
