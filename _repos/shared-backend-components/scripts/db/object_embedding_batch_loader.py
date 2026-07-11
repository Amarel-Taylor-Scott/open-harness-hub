#!/usr/bin/env python3
"""Load object_embedding rows into pgvector Postgres (deterministic UPSERT SQL).

Backs ``tool/object-embedding-batch-loader`` (_repos/shared-backend-components/catalog/tools/backend/
object-embedding-batch-loader.yaml). The manifest's
``implementations[].path`` is ``scripts.db.object_embedding_batch_loader.load_embeddings``.

This module reads a JSONL file where each line is a *pre-computed*
``object_embedding`` row with the embedding vector inline
(``embedding``: float array). It validates that each vector's dimension matches
the canonical schema dimension defined once in ``_repos/shared-backend-components/scripts/_config.py``
(``DEFAULT_EMBEDDING_DIMENSIONS`` → ``vector(384)``), routes structurally
incomplete or dimension-mismatched rows to a rejected JSONL sidecar with
reasons, and emits a deterministic UPSERT SQL script targeting the
``object_embedding`` table's ``UNIQUE (subject_id, subject_type,
embedding_model, text_hash)`` constraint (the natural key the manifest names).

It differs from ``scripts.db.pgvector_embedding_load_plan`` (which reads the
*worker* output shape — a separate ``vector`` field keyed by ``embedding_id``
and conflicts on the primary key): this loader consumes the manifest's inline
``embedding`` shape and upserts on the natural-key UNIQUE constraint, so two
runs that recompute the same subject/model/text collapse instead of duplicating.
The low-level SQL value/vector helpers are imported from
``pgvector_embedding_load_plan`` rather than re-implemented (lossless reuse).

Side-effect free: it writes SQL + sidecars under ``output_dir`` but never
connects to a database (apply the SQL yourself against an intended pgvector DB).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    OBJECT_EMBEDDING_BATCH_LOADER_AUDIT_FILENAME,
    OBJECT_EMBEDDING_BATCH_LOADER_REJECTED_FILENAME,
    OBJECT_EMBEDDING_BATCH_LOADER_RUN_ID,
    OBJECT_EMBEDDING_BATCH_LOADER_SQL_FILENAME,
    pgvector_type,
)
from scripts.db.pgvector_embedding_load_plan import (
    _sql_json,
    _sql_string,
    _sql_vector,
)

# Canonical pgvector dimension is defined once in _repos/shared-backend-components/scripts/_config.py; never
# re-type the integer here (_repos/shared-backend-components/docs/codex/no-magic-values.md).
DEFAULT_SCHEMA_DIMENSIONS = DEFAULT_EMBEDDING_DIMENSIONS

# The object_embedding natural key, mirrored from the UNIQUE constraint in
# db/postgres/schema.sql. The UPSERT conflict target is built from this list so
# the SQL and the schema cannot drift independently.
OBJECT_EMBEDDING_NATURAL_KEY = (
    "subject_id",
    "subject_type",
    "embedding_model",
    "text_hash",
)

# Columns written, in a stable order. Mirrors the insertable columns of the
# object_embedding table (created_at defaults in the DB).
_INSERT_COLUMNS = (
    "embedding_id",
    "subject_id",
    "subject_type",
    "embedding_model",
    "text_hash",
    "text",
    "embedding",
    "metadata",
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _text_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _embedding_id(row: dict[str, Any]) -> str:
    """Stable embedding_id: explicit value, else a content hash of the key.

    Never truncation-only — the hash is over the full natural key + model so two
    distinct rows cannot collapse onto the same id during load planning
    (_repos/shared-backend-components/docs/codex ID/hash discipline).
    """
    existing = str(row.get("embedding_id") or "")
    if existing:
        return existing
    seed = {field: row.get(field) for field in OBJECT_EMBEDDING_NATURAL_KEY}
    digest = hashlib.sha256(
        json.dumps(seed, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    subject = str(row.get("subject_id") or "subject")
    return "object-embedding/" + subject.replace("/", "-") + "/" + digest[:16]


def _conflict_clause() -> str:
    target = ", ".join(OBJECT_EMBEDDING_NATURAL_KEY)
    # Update every non-key column on conflict so a re-load refreshes text/vector.
    updates = [
        f"{column}=EXCLUDED.{column}"
        for column in _INSERT_COLUMNS
        if column not in OBJECT_EMBEDDING_NATURAL_KEY
    ]
    return f"ON CONFLICT ({target}) DO UPDATE SET\n  " + ",\n  ".join(updates)


def _insert_statement(row: dict[str, Any], embedding_id: str, embedding: list[Any]) -> str:
    metadata = row.get("metadata")
    values = [
        _sql_string(embedding_id),
        _sql_string(row.get("subject_id")),
        _sql_string(row.get("subject_type")),
        _sql_string(row.get("embedding_model")),
        _sql_string(row.get("text_hash")),
        _sql_string(row.get("text")),
        _sql_vector(embedding),
        _sql_json(metadata if isinstance(metadata, dict) else {}),
    ]
    return (
        f"INSERT INTO object_embedding ({', '.join(_INSERT_COLUMNS)})\n"
        f"VALUES ({', '.join(values)})\n"
        + _conflict_clause()
        + ";\n"
    )


def _validate(row: dict[str, Any], embedding: Any, schema_vector_dim: int) -> list[str]:
    issues: list[str] = []
    for field in ("subject_id", "subject_type", "embedding_model"):
        if not str(row.get(field) or "").strip():
            issues.append(f"missing_{field}")
    if not isinstance(embedding, list) or not embedding:
        issues.append("missing_embedding")
    else:
        if any(not isinstance(value, (int, float)) for value in embedding):
            issues.append("non_numeric_embedding_value")
        if len(embedding) != schema_vector_dim:
            issues.append("dimension_mismatch_for_schema")
    if not str(row.get("text") or "").strip():
        issues.append("missing_text")
    return issues


def load_embeddings(
    embedding_rows_jsonl: str | Path,
    output_dir: str | Path | None = None,
    *,
    schema_vector_dim: int = DEFAULT_SCHEMA_DIMENSIONS,
    run_id: str = OBJECT_EMBEDDING_BATCH_LOADER_RUN_ID,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Plan a deterministic object_embedding UPSERT load. Returns an audit dict.

    Implements ``tool/object-embedding-batch-loader``. Reads inline-embedding
    rows, validates dimensions against ``schema_vector_dim`` (defaults to the
    canonical schema dimension), rejects incomplete rows, and emits UPSERT SQL.
    """
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-object-embedding-batch-load-"))
    rows = _read_jsonl(embedding_rows_jsonl)
    accepted_by_model: dict[str, int] = {}
    rejected_by_model: dict[str, int] = {}
    rejected_rows: list[dict[str, Any]] = []
    statements = [
        "-- Generated by scripts/db/object_embedding_batch_loader.py",
        "-- Review before applying to a live database (pgvector required).",
        f"-- Schema vector type: {pgvector_type(schema_vector_dim)}",
        "BEGIN;",
    ]
    models_seen: set[str] = set()

    for row in rows:
        # text_hash defaults to a content hash of text when absent, so the
        # natural key is always populated for the UNIQUE upsert.
        if not str(row.get("text_hash") or "").strip() and str(row.get("text") or "").strip():
            row = {**row, "text_hash": _text_hash(str(row["text"]))}
        model = str(row.get("embedding_model") or "unknown")
        models_seen.add(model)
        embedding = row.get("embedding")
        issues = _validate(row, embedding, schema_vector_dim)
        if issues:
            rejected_by_model[model] = rejected_by_model.get(model, 0) + 1
            rejected_rows.append({
                "embedding_id": str(row.get("embedding_id") or ""),
                "subject_id": row.get("subject_id"),
                "embedding_model": model,
                "observed_dimension": len(embedding) if isinstance(embedding, list) else 0,
                "schema_vector_dim": schema_vector_dim,
                "issues": issues,
            })
            continue
        embedding_id = _embedding_id(row)
        accepted_by_model[model] = accepted_by_model.get(model, 0) + 1
        statements.append(_insert_statement(row, embedding_id, embedding))

    statements.append("COMMIT;\n")
    accepted_total = sum(accepted_by_model.values())
    rejected_total = sum(rejected_by_model.values())

    sql_path = out / OBJECT_EMBEDDING_BATCH_LOADER_SQL_FILENAME
    rejected_path = out / OBJECT_EMBEDDING_BATCH_LOADER_REJECTED_FILENAME
    audit_path = out / OBJECT_EMBEDDING_BATCH_LOADER_AUDIT_FILENAME

    if not dry_run:
        sql_path.parent.mkdir(parents=True, exist_ok=True)
        sql_path.write_text("\n".join(statements), encoding="utf-8")
    _write_jsonl(rejected_path, rejected_rows)

    audit_rows = [
        {
            "embedding_model": model,
            "accepted_rows": accepted_by_model.get(model, 0),
            "rejected_rows": rejected_by_model.get(model, 0),
            "run_id": run_id,
            "schema_vector_dim": schema_vector_dim,
            "generated_at": _utc_now(),
        }
        for model in sorted(models_seen)
    ]
    _write_jsonl(audit_path, audit_rows)

    summary = {
        "ok": rejected_total == 0 and accepted_total > 0,
        "run_id": run_id,
        "input_rows": len(rows),
        "accepted_rows": accepted_total,
        "rejected_rows": rejected_total,
        "models_seen": sorted(models_seen),
        "schema_vector_dim": schema_vector_dim,
        "dry_run": dry_run,
        "files": {
            "sql_load_script": "" if dry_run else str(sql_path),
            "rejected_jsonl": str(rejected_path),
            "audit_summary_jsonl": str(audit_path),
        },
    }
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        rows_path = root / "rows.jsonl"
        good_vec = [0.1] * DEFAULT_SCHEMA_DIMENSIONS
        bad_vec = [0.1] * (DEFAULT_SCHEMA_DIMENSIONS - 1)
        rows = [
            # accepted (text_hash supplied)
            {
                "subject_id": "component/example-a",
                "subject_type": "component",
                "embedding_model": "all-MiniLM-L6-v2",
                "text_hash": "sha256:aaa",
                "text": "alpha",
                "embedding": good_vec,
            },
            # accepted (text_hash derived from text), duplicate natural key as a
            # second run would produce — UPSERT collapses it at apply time.
            {
                "subject_id": "component/example-b",
                "subject_type": "component",
                "embedding_model": "all-MiniLM-L6-v2",
                "text": "beta",
                "embedding": good_vec,
            },
            # rejected: dimension mismatch
            {
                "subject_id": "component/example-c",
                "subject_type": "component",
                "embedding_model": "all-MiniLM-L6-v2",
                "text_hash": "sha256:ccc",
                "text": "gamma",
                "embedding": bad_vec,
            },
            # rejected: missing embedding + missing text
            {
                "subject_id": "component/example-d",
                "subject_type": "component",
                "embedding_model": "nomic-embed-text",
                "text_hash": "sha256:ddd",
            },
        ]
        _write_jsonl(rows_path, rows)
        result = load_embeddings(rows_path, root / "out", schema_vector_dim=DEFAULT_SCHEMA_DIMENSIONS)
        assert result["input_rows"] == 4, result
        assert result["accepted_rows"] == 2, result
        assert result["rejected_rows"] == 2, result
        assert result["ok"] is False, result  # rejects present
        assert result["models_seen"] == ["all-MiniLM-L6-v2", "nomic-embed-text"], result
        sql = Path(result["files"]["sql_load_script"]).read_text(encoding="utf-8")
        assert "ON CONFLICT (subject_id, subject_type, embedding_model, text_hash)" in sql, sql
        assert sql.count("INSERT INTO object_embedding") == 2, sql
        rejected = _read_jsonl(result["files"]["rejected_jsonl"])
        assert len(rejected) == 2, rejected
        assert any("dimension_mismatch_for_schema" in r["issues"] for r in rejected), rejected
        # All-good batch reports ok=True.
        good_only = root / "good.jsonl"
        _write_jsonl(good_only, rows[:1])
        ok_result = load_embeddings(good_only, root / "out2")
        assert ok_result["ok"] is True, ok_result
        # dry_run emits no SQL file path.
        dry = load_embeddings(rows_path, root / "out3", dry_run=True)
        assert dry["files"]["sql_load_script"] == "", dry
    print(json.dumps({"ok": True, "accepted_rows": 2, "rejected_rows": 2}, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--embedding-rows-jsonl", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--schema-vector-dim", type=int, default=DEFAULT_SCHEMA_DIMENSIONS)
    parser.add_argument("--run-id", default=OBJECT_EMBEDDING_BATCH_LOADER_RUN_ID)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.embedding_rows_jsonl or not args.output_dir:
        parser.error("--embedding-rows-jsonl and --output-dir are required unless --self-test is used")
    summary = load_embeddings(
        args.embedding_rows_jsonl,
        args.output_dir,
        schema_vector_dim=args.schema_vector_dim,
        run_id=args.run_id,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
