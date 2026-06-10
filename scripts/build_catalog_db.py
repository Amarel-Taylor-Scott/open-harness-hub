#!/usr/bin/env python3
"""Build a portable SQLite search snapshot from catalog rows or seed files.

YAML files in catalog/ are git-tracked, PR-reviewable, forkable,
schema-validated seed/export artifacts. Hosted deployments should use Postgres
as operational truth. This script can read database-exported catalog row sets
or the legacy seed/export files and writes a portable SQLite snapshot to
dist/catalog.sqlite that supports:

- FTS5 full-text search across name + description + tags + industry + capability
- Adjacency table of related references (pattern -> implementing_pipelines,
  pipeline -> rule_packs / knowledge_packs / persona, etc.)
- Per-component JSON blob for full body retrieval

Embeddings are populated only if `sentence-transformers` is installed and the
OH_BUILD_EMBEDDINGS env var is set. Otherwise the snapshot ships without
vectors; FTS5 lexical search is the default.

Usage:
    python3 scripts/build_catalog_db.py
    python3 scripts/build_catalog_db.py --row-dir dist/catalog-db-export-rows
    OH_BUILD_EMBEDDINGS=1 python3 scripts/build_catalog_db.py   # with vectors
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO = Path(__file__).resolve().parent.parent
CATALOG = REPO / "catalog"
DIST = REPO / "dist"
DB_PATH = DIST / "catalog.sqlite"

if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_source import iter_components_from_rows, row_source_status


CatalogRecord = tuple[str | Path, dict[str, Any], list[tuple[str, str]]]


def iter_components() -> Iterable[tuple[Path, dict]]:
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


def path_label(path: str | Path) -> str:
    if isinstance(path, Path):
        try:
            return str(path.relative_to(REPO))
        except ValueError:
            return str(path)
    return path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a portable SQLite catalog snapshot from database rows or catalog YAML."
    )
    parser.add_argument(
        "--row-dir",
        default=os.environ.get("OH_CATALOG_ROW_DIR"),
        help="Read database-shaped JSONL row sets from this directory instead of walking catalog YAML.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DB_PATH,
        help="SQLite output path. Defaults to dist/catalog.sqlite.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    DIST.mkdir(exist_ok=True)
    db_path = args.output
    if not db_path.is_absolute():
        db_path = REPO / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    row_dir = Path(args.row_dir) if args.row_dir else None
    if row_dir is not None:
        records: Iterable[CatalogRecord] = (
            (component.source_path, component.manifest, component.refs)
            for component in iter_components_from_rows(row_dir)
        )
        source_label = f"database rows from {row_dir}"
    else:
        records = ((path, doc, harvest_refs(doc)) for path, doc in iter_components())
        source_label = "catalog YAML seed/export files"

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.executescript("""
    CREATE TABLE catalog_snapshot_metadata (
        key        TEXT PRIMARY KEY,
        value_json TEXT NOT NULL
    );

    CREATE TABLE components (
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
    CREATE INDEX idx_type ON components(type);
    CREATE INDEX idx_lifecycle ON components(lifecycle);

    CREATE VIRTUAL TABLE components_fts USING fts5(
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
        component_id TEXT PRIMARY KEY,
        model       TEXT,
        dim         INTEGER,
        vector      BLOB
    );
    """)
    metadata = {
        "source": {
            "kind": "database_rows" if row_dir is not None else "catalog_yaml_seed_export",
            "row_dir": str(row_dir) if row_dir is not None else "",
            "row_source_status": row_source_status(row_dir) if row_dir is not None else None,
        },
        "embeddings_requested": os.environ.get("OH_BUILD_EMBEDDINGS") == "1",
    }
    for key, value in metadata.items():
        c.execute(
            "INSERT INTO catalog_snapshot_metadata (key, value_json) VALUES (?, ?)",
            (key, json.dumps(value, sort_keys=True)),
        )

    n = 0
    duplicate_skips = 0
    for path, doc, refs in records:
        rel_path = path_label(path)
        try:
            c.execute("""INSERT INTO components (id, type, version, name, description, license, lifecycle, trust_boundary, industry, capability, modality, tags, path, body_json)
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
        except sqlite3.IntegrityError as exc:
            if "UNIQUE constraint failed: components.id" not in str(exc):
                raise
            duplicate_skips += 1
            continue
        c.execute("INSERT INTO components_fts (id, type, name, description, tags, industry, capability) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (doc["id"], doc["type"], doc.get("name") or "",
                   (doc.get("description") or "") if isinstance(doc.get("description"), str) else "",
                   " ".join(doc.get("tags") or []),
                   " ".join(doc.get("industry") or []),
                   " ".join(doc.get("capability") or [])))
        for rel, tgt in refs:
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
            rows = c.execute("SELECT id, name, description FROM components").fetchall()
            texts = [f"{r[1]}\n\n{r[2] or ''}" for r in rows]
            vecs = model.encode(texts, show_progress_bar=True, batch_size=64, normalize_embeddings=True)
            for (aid, _, _), v in zip(rows, vecs):
                c.execute("INSERT INTO embeddings (component_id, model, dim, vector) VALUES (?, ?, ?, ?)",
                          (aid, model_name, int(v.shape[0]), v.tobytes()))
            print(f"embedded {len(rows)} components with {model_name}")
        except ImportError:
            print("sentence-transformers not installed; skipping embeddings")
        except Exception as e:
            print(f"embedding step failed: {e}; continuing without vectors")

    conn.commit()
    conn.close()
    print(f"wrote {db_path} with {n} components from {source_label}")
    if duplicate_skips:
        print(f"skipped {duplicate_skips} duplicate component ids; use the migration gate for review/hold details")
    return 0


if __name__ == "__main__":
    sys.exit(main())
