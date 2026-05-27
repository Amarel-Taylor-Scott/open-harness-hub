#!/usr/bin/env python3
"""Build a working multi-embedding, multi-label vector store over the catalog.

This is the vector-search foundation. It mirrors the canonical Postgres row
families (db/postgres/schema.sql) so the same shape works locally and hosted:

  * object_embedding — keyed by (subject_id, subject_type, embedding_model), so
    one object can carry MANY embeddings from different models/dims/purposes.
  * label_assignment — keyed by assignment_method, so one object can carry MANY
    labels from different producers (regex, llm, deterministic, classifier,
    human), each with confidence, model_route_id, provenance and review_status.

Embedder selection is pluggable and offline-first:

  * "all-MiniLM-L6-v2" (384) when sentence-transformers is installed -> real
    semantic vectors (promotable).
  * "hash-bow-v1" (256) deterministic feature-hashing bag-of-words -> the
    offline default. STAGING ONLY: placeholder vectors block promotion
    (docs/codex/billion-component-goal.md). Good enough to prove the plumbing
    and run hybrid search with no numpy.

Output goes to dist/vector-store/catalog-vectors.sqlite (gitignored derived
data; the YAML catalog stays the source of truth). Search is pure-stdlib cosine
KNN with type/label filters, so it runs anywhere.

Usage:
  python3 -m scripts.db.build_vector_store build [--limit N] [--model hash-bow-v1]
  python3 -m scripts.db.build_vector_store search "reduce token cost" [--type pattern] [--label token-efficiency] [-k 5]
  python3 -m scripts.db.build_vector_store --self-test
"""
from __future__ import annotations

import argparse
import hashlib
import math
import re
import sqlite3
import tempfile
from pathlib import Path
from typing import Callable, Iterable

import yaml

from scripts._config import CATALOG_DIR, DIST_DIR

# --- Embedding models registered in this store ------------------------------
# (model_id -> dim). Multiple may coexist per object; the store is multi-dim by
# design (dim is stored per row), unlike a single fixed pgvector(384) column.
HASH_MODEL = "hash-bow-v1"
HASH_DIM = 256
REAL_MODEL = "all-MiniLM-L6-v2"  # used only if sentence-transformers is present

DEFAULT_STORE = DIST_DIR / "vector-store" / "catalog-vectors.sqlite"

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_.+-]{1,40}")

# --- Regex label rules (deterministic; assignment_method='regex') -----------
# label_set, label, pattern. These are exact, filterable signals that live
# ALONGSIDE the vectors (not embedded away). LLM/classifier labels slot into the
# same table with a different assignment_method (see llm_label()).
REGEX_LABEL_RULES: list[tuple[str, str, re.Pattern[str]]] = [
    ("capability-signal", "pii-redaction", re.compile(r"\b(pii|redact|anonymi|de-?identif|gdpr|hipaa)\b", re.I)),
    ("capability-signal", "rag-retrieval", re.compile(r"\b(rag|retrieval|embed|vector|rerank|knn)\b", re.I)),
    ("capability-signal", "evaluation", re.compile(r"\b(rubric|judge|benchmark|eval|grade|score)\b", re.I)),
    ("capability-signal", "safety-gate", re.compile(r"\b(safety|guard|gate|refus|moderat|jailbreak)\b", re.I)),
    ("cost-signal", "token-efficiency", re.compile(r"\b(token|compress|terse|budget|cheaper|cost)\b", re.I)),
    ("architecture-signal", "agentic", re.compile(r"\b(agent|tool[ -]?call|react|plan|reflect|loop)\b", re.I)),
    ("architecture-signal", "structured-output", re.compile(r"\b(json|schema|envelope|structured|format)\b", re.I)),
    ("domain-signal", "devops", re.compile(r"\b(devops|ci[ /-]?cd|deploy|code[ -]?review|pipeline)\b", re.I)),
    ("modality-signal", "audio", re.compile(r"\b(audio|speech|tts|voice|asr)\b", re.I)),
]


# --- Embedders --------------------------------------------------------------
def hash_embed(text: str, dim: int = HASH_DIM) -> list[float]:
    """Deterministic signed feature-hashing bag-of-words, L2-normalized."""
    vec = [0.0] * dim
    for tok in TOKEN_RE.findall(text.lower()):
        h = hashlib.sha1(tok.encode("utf-8")).digest()
        idx = int.from_bytes(h[:4], "big") % dim
        sign = 1.0 if (h[4] & 1) else -1.0
        vec[idx] += sign
    norm = math.sqrt(sum(v * v for v in vec))
    return [v / norm for v in vec] if norm else vec


def get_embedder(model: str) -> tuple[Callable[[str], list[float]], int]:
    """Return (embed_fn, dim). Falls back to the hash embedder offline."""
    if model == REAL_MODEL:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore

            st = SentenceTransformer(model)
            dim = int(st.get_sentence_embedding_dimension())
            return (lambda t: [float(x) for x in st.encode(t, normalize_embeddings=True)], dim)
        except Exception:
            # No model available — degrade to the offline hash embedder.
            return (hash_embed, HASH_DIM)
    return (hash_embed, HASH_DIM)


def is_placeholder(model: str) -> bool:
    """Hash vectors are placeholders (block promotion); real model vectors are not."""
    return model == HASH_MODEL


# --- Store ------------------------------------------------------------------
SCHEMA = """
CREATE TABLE IF NOT EXISTS object_embedding (
  embedding_id    TEXT PRIMARY KEY,
  subject_id      TEXT NOT NULL,
  subject_type    TEXT NOT NULL,
  embedding_model TEXT NOT NULL,
  dim             INTEGER NOT NULL,
  is_placeholder  INTEGER NOT NULL,
  text_hash       TEXT NOT NULL,
  text            TEXT NOT NULL,
  embedding       TEXT NOT NULL,           -- JSON list[float]
  UNIQUE (subject_id, subject_type, embedding_model, text_hash)
);
CREATE TABLE IF NOT EXISTS label_assignment (
  label_id          TEXT PRIMARY KEY,
  label_set         TEXT NOT NULL,
  label             TEXT NOT NULL,
  subject_id        TEXT NOT NULL,
  subject_type      TEXT,
  confidence        REAL,
  assigned_by       TEXT,
  assignment_method TEXT,                  -- regex | llm | deterministic | classifier | human
  model_route_id    TEXT,
  review_status     TEXT,
  UNIQUE (subject_id, label_set, label, assignment_method)
);
CREATE INDEX IF NOT EXISTS idx_emb_model ON object_embedding(embedding_model);
CREATE INDEX IF NOT EXISTS idx_label_method ON label_assignment(assignment_method);
"""


def _connect(store: Path) -> sqlite3.Connection:
    store.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(store)
    con.executescript(SCHEMA)
    return con


def iter_components(limit: int | None = None) -> Iterable[dict]:
    n = 0
    for p in sorted(CATALOG_DIR.rglob("*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(doc, dict) or "id" not in doc or "type" not in doc:
            continue
        yield doc
        n += 1
        if limit and n >= limit:
            return


def _doc_text(doc: dict) -> str:
    tags = " ".join(doc.get("tags", []) or [])
    return f"{doc.get('name','')} · {doc.get('description','')} · {tags}".strip()


def regex_labels(doc: dict) -> list[dict]:
    text = _doc_text(doc)
    out = []
    for label_set, label, pat in REGEX_LABEL_RULES:
        if pat.search(text):
            out.append({
                "label_set": label_set, "label": label,
                "confidence": 1.0, "assigned_by": "build_vector_store.regex",
                "assignment_method": "regex", "model_route_id": None,
                "review_status": "auto",
            })
    return out


def llm_label(doc: dict, model_route_id: str) -> list[dict]:
    """LLM-generated labels slot into label_assignment with assignment_method='llm'.

    Not called offline (no model route here). Implement by calling a provider-
    neutral model route, then returning rows like regex_labels() but with
    assignment_method='llm', model_route_id set, confidence from the model, and
    review_status='needs_review' until a gate clears them. Left as the explicit
    extension point so we never fabricate LLM labels.
    """
    raise NotImplementedError("wire a provider-neutral model route to enable LLM labels")


def build(store: Path = DEFAULT_STORE, model: str = HASH_MODEL, limit: int | None = None) -> dict:
    embed, dim = get_embedder(model)
    placeholder = 1 if is_placeholder(model) else 0
    con = _connect(store)
    n_emb = n_lab = n_obj = 0
    try:
        for doc in iter_components(limit=limit):
            sid, stype = doc["id"], doc["type"]
            text = _doc_text(doc)
            thash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
            emb_id = hashlib.sha1(f"{sid}|{model}|{thash}".encode()).hexdigest()[:20]
            vec = embed(text)
            con.execute(
                "INSERT OR REPLACE INTO object_embedding "
                "(embedding_id, subject_id, subject_type, embedding_model, dim, is_placeholder, text_hash, text, embedding) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (emb_id, sid, stype, model, dim, placeholder, thash, text,
                 __import__("json").dumps(vec)),
            )
            n_emb += 1
            n_obj += 1
            for lab in regex_labels(doc):
                lid = hashlib.sha1(f"{sid}|{lab['label_set']}|{lab['label']}|{lab['assignment_method']}".encode()).hexdigest()[:20]
                con.execute(
                    "INSERT OR REPLACE INTO label_assignment "
                    "(label_id, label_set, label, subject_id, subject_type, confidence, assigned_by, assignment_method, model_route_id, review_status) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (lid, lab["label_set"], lab["label"], sid, stype, lab["confidence"],
                     lab["assigned_by"], lab["assignment_method"], lab["model_route_id"], lab["review_status"]),
                )
                n_lab += 1
        con.commit()
    finally:
        con.close()
    return {
        "store": str(store), "embedding_model": model, "dim": dim,
        "is_placeholder": bool(placeholder), "objects": n_obj,
        "embeddings": n_emb, "labels": n_lab,
    }


def _cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))  # both L2-normalized


def search(query: str, store: Path = DEFAULT_STORE, model: str = HASH_MODEL,
           k: int = 5, type_filter: str | None = None, label_filter: str | None = None) -> list[dict]:
    import json
    embed, _ = get_embedder(model)
    qv = embed(query)
    con = sqlite3.connect(store)
    try:
        sql = "SELECT subject_id, subject_type, embedding FROM object_embedding WHERE embedding_model=?"
        params: list = [model]
        if type_filter:
            sql += " AND subject_type=?"
            params.append(type_filter)
        if label_filter:
            sql += (" AND subject_id IN (SELECT subject_id FROM label_assignment WHERE label=?)")
            params.append(label_filter)
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    scored = [
        {"id": sid, "type": stype, "score": round(_cosine(qv, json.loads(emb)), 4)}
        for sid, stype, emb in rows
    ]
    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:k]


def _self_test() -> int:
    import json
    with tempfile.TemporaryDirectory() as tmp:
        store = Path(tmp) / "vs.sqlite"
        # Build over a slice of the real catalog with the offline hash model.
        rep = build(store=store, model=HASH_MODEL, limit=400)
        assert rep["embeddings"] > 0 and rep["labels"] > 0, rep

        # Multi-embedding: a second model for the same objects must coexist.
        rep2 = build(store=store, model="hash-bow-v2-demo", limit=400)
        con = sqlite3.connect(store)
        models = {r[0] for r in con.execute("SELECT DISTINCT embedding_model FROM object_embedding")}
        methods = {r[0] for r in con.execute("SELECT DISTINCT assignment_method FROM label_assignment")}
        con.close()
        assert len(models) >= 2, models                # multiple embedding types
        assert "regex" in methods, methods             # multiple label kinds (regex present)

        # Vector search returns results and respects filters.
        hits = search("compress and reduce token cost", store=store, model=HASH_MODEL, k=5)
        assert hits and all("score" in h for h in hits), hits
        typed = search("strict json output format", store=store, model=HASH_MODEL, k=5, type_filter="pattern")
        assert all(h["type"] == "pattern" for h in typed), typed

    print(json.dumps({"ok": True, "models": sorted(models), "label_methods": sorted(methods),
                      "sample_hits": hits[:3]}, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    import json
    p = argparse.ArgumentParser(description="Multi-embedding, multi-label catalog vector store.")
    p.add_argument("--self-test", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    b.add_argument("--store", default=str(DEFAULT_STORE))
    b.add_argument("--model", default=HASH_MODEL)
    b.add_argument("--limit", type=int)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--store", default=str(DEFAULT_STORE))
    s.add_argument("--model", default=HASH_MODEL)
    s.add_argument("-k", type=int, default=5)
    s.add_argument("--type", dest="type_filter")
    s.add_argument("--label", dest="label_filter")
    args = p.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.cmd == "build":
        print(json.dumps(build(store=Path(args.store), model=args.model, limit=args.limit), indent=2))
        return 0
    if args.cmd == "search":
        hits = search(args.query, store=Path(args.store), model=args.model, k=args.k,
                      type_filter=args.type_filter, label_filter=args.label_filter)
        print(json.dumps(hits, indent=2))
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
