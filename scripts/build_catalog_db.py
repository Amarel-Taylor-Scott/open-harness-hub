#!/usr/bin/env python3
"""Build a derived SQLite database from the canonical YAML catalog.

YAML files in catalog/ remain the source of truth (git-tracked, PR-reviewable,
forkable, schema-validated). This script reads them and writes a derived
SQLite DB to dist/catalog.sqlite that supports:

- FTS5 full-text search across name + description + tags + industry + capability
- Adjacency table of related references (pattern -> implementing_pipelines,
  pipeline -> rule_packs / knowledge_packs / persona, etc.)
- Per-artifact JSON blob for full body retrieval

Embeddings are populated only if `sentence-transformers` is installed and the
OH_BUILD_EMBEDDINGS env var is set. Otherwise the DB ships without vectors;
FTS5 lexical search is the default.

Usage:
    python3 scripts/build_catalog_db.py
    OH_BUILD_EMBEDDINGS=1 python3 scripts/build_catalog_db.py   # with vectors
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Iterable

import yaml


REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "catalog"
DIST = REPO / "dist"
DB_PATH = DIST / "catalog.sqlite"


def iter_artifacts() -> Iterable[tuple[Path, dict]]:
    for p in sorted(CATALOG.rglob("*.yaml")):
        try:
            doc = yaml.safe_load(p.read_text())
        except Exception:
            continue
        if not isinstance(doc, dict) or not doc.get("id") or not doc.get("type"):
            continue
        yield p, doc


def harvest_refs(doc: dict) -> list[tuple[str, str]]:
    """Pull (rel, target_id) tuples for graph edges."""
    edges: list[tuple[str, str]] = []
    for field, rel in [
        ("implementing_pipelines", "implementing_pipeline"),
        ("implementing_processors", "implementing_processor"),
        ("related_patterns", "related_pattern"),
        ("rule_packs", "uses_rule_pack"),
        ("knowledge_packs", "uses_knowledge_pack"),
    ]:
        for tgt in doc.get(field, []) or []:
            if isinstance(tgt, str):
                edges.append((rel, tgt))
    # nested defaults
    defs = doc.get("defaults", {}) or {}
    for k, rel in [
        ("persona", "uses_persona"),
        ("model_adapter", "uses_adapter"),
    ]:
        v = defs.get(k)
        if isinstance(v, str):
            edges.append((rel, v))
    for k, rel in [
        ("rule_packs", "uses_rule_pack"),
        ("knowledge_packs", "uses_knowledge_pack"),
    ]:
        for v in defs.get(k, []) or []:
            if isinstance(v, str):
                edges.append((rel, v))
    # pipeline step refs
    for step in doc.get("steps", []) or []:
        ref = step.get("ref")
        if isinstance(ref, str):
            edges.append(("step_ref", ref))
    return edges


def main() -> int:
    DIST.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE artifacts (
        id            TEXT PRIMARY KEY,
        type          TEXT NOT NULL,
        version       TEXT,
        name          TEXT,
        description   TEXT,
        license       TEXT,
        lifecycle     TEXT,
        trust_boundary TEXT,
        industry      TEXT,
        capability    TEXT,
        modality      TEXT,
        tags          TEXT,
        path          TEXT,
        body_json     TEXT
    );
    CREATE INDEX idx_type ON artifacts(type);
    CREATE INDEX idx_lifecycle ON artifacts(lifecycle);

    CREATE VIRTUAL TABLE artifacts_fts USING fts5(
        id UNINDEXED,
        type UNINDEXED,
        name,
        description,
        tags,
        industry,
        capability,
        tokenize = 'porter unicode61 remove_diacritics 2'
    );

    CREATE TABLE edges (
        src_id   TEXT NOT NULL,
        rel      TEXT NOT NULL,
        dst_id   TEXT NOT NULL,
        PRIMARY KEY (src_id, rel, dst_id)
    );
    CREATE INDEX idx_edges_dst ON edges(dst_id);

    CREATE TABLE embeddings (
        artifact_id TEXT PRIMARY KEY,
        model       TEXT,
        dim         INTEGER,
        vector      BLOB
    );
    """)

    n = 0
    for path, doc in iter_artifacts():
        rel_path = str(path.relative_to(REPO))
        c.execute("""INSERT INTO artifacts (id, type, version, name, description, license, lifecycle, trust_boundary, industry, capability, modality, tags, path, body_json)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (doc["id"], doc["type"], doc.get("version"), doc.get("name"),
                   (doc.get("description") or "")[:5000] if isinstance(doc.get("description"), str) else "",
                   doc.get("license"), doc.get("lifecycle"), doc.get("trust_boundary"),
                   json.dumps(doc.get("industry") or []),
                   json.dumps(doc.get("capability") or []),
                   json.dumps(doc.get("modality") or []),
                   json.dumps(doc.get("tags") or []),
                   rel_path,
                   json.dumps(doc)))
        c.execute("INSERT INTO artifacts_fts (id, type, name, description, tags, industry, capability) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (doc["id"], doc["type"], doc.get("name") or "",
                   (doc.get("description") or "") if isinstance(doc.get("description"), str) else "",
                   " ".join(doc.get("tags") or []),
                   " ".join(doc.get("industry") or []),
                   " ".join(doc.get("capability") or [])))
        for rel, tgt in harvest_refs(doc):
            try:
                c.execute("INSERT OR IGNORE INTO edges (src_id, rel, dst_id) VALUES (?, ?, ?)",
                          (doc["id"], rel, tgt))
            except sqlite3.Error:
                pass
        n += 1

    if os.environ.get("OH_BUILD_EMBEDDINGS") == "1":
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            model_name = os.environ.get("OH_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            model = SentenceTransformer(model_name)
            rows = c.execute("SELECT id, name, description FROM artifacts").fetchall()
            texts = [f"{r[1]}\n\n{r[2] or ''}" for r in rows]
            vecs = model.encode(texts, show_progress_bar=True, batch_size=64, normalize_embeddings=True)
            for (aid, _, _), v in zip(rows, vecs):
                c.execute("INSERT INTO embeddings (artifact_id, model, dim, vector) VALUES (?, ?, ?, ?)",
                          (aid, model_name, int(v.shape[0]), v.tobytes()))
            print(f"embedded {len(rows)} artifacts with {model_name}")
        except ImportError:
            print("sentence-transformers not installed; skipping embeddings")
        except Exception as e:
            print(f"embedding step failed: {e}; continuing without vectors")

    conn.commit()
    conn.close()
    print(f"wrote {DB_PATH} with {n} artifacts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
