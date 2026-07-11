#!/usr/bin/env python3
"""Emit reviewable pgvector load SQL from stored embedding vector rows."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    PGVECTOR_LOAD_PLAN_ACCEPTED_ROWS_FILENAME,
    PGVECTOR_LOAD_PLAN_REJECTED_ROWS_FILENAME,
    PGVECTOR_LOAD_PLAN_RUN_ID,
    PGVECTOR_LOAD_PLAN_SQL_FILENAME,
    PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
    pgvector_type,
)

# Canonical pgvector dimension is defined once in _repos/shared-backend-components/scripts/_config.py; do not
# re-type the number here (see _repos/shared-backend-components/docs/codex/no-magic-values.md).
DEFAULT_SCHEMA_DIMENSIONS = DEFAULT_EMBEDDING_DIMENSIONS


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


def _sql_string(value: Any) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _sql_json(value: Any) -> str:
    return _sql_string(json.dumps(value if value is not None else {}, sort_keys=True, ensure_ascii=False)) + "::jsonb"


def _sql_vector(vector: list[Any]) -> str:
    values: list[str] = []
    for value in vector:
        values.append(f"{float(value):.8f}".rstrip("0").rstrip(".") or "0")
    return _sql_string("[" + ",".join(values) + "]") + "::vector"


def _text_by_embedding_id(source_embedding_rows: str | Path | None) -> dict[str, str]:
    if not source_embedding_rows:
        return {}
    out: dict[str, str] = {}
    for row in _read_jsonl(source_embedding_rows):
        embedding_id = str(row.get("embedding_id") or "")
        if embedding_id:
            out[embedding_id] = str(row.get("text") or "")
    return out


def _embedding_insert(row: dict[str, Any], text: str) -> str:
    metadata = {
        "batch_id": row.get("batch_id"),
        "profile_id": row.get("profile_id"),
        "dimensions": row.get("dimensions"),
        "expected_dimensions": row.get("expected_dimensions"),
        "embedding_runtime": row.get("embedding_runtime"),
        "storage_backend": row.get("storage_backend"),
        "worker_id": row.get("worker_id"),
        "stored_at": row.get("stored_at"),
        "status": row.get("status"),
    }
    columns = [
        "embedding_id",
        "subject_id",
        "subject_type",
        "embedding_model",
        "text_hash",
        "text",
        "embedding",
        "metadata",
    ]
    values = [
        _sql_string(row.get("embedding_id")),
        _sql_string(row.get("subject_id")),
        _sql_string(row.get("subject_type")),
        _sql_string(row.get("embedding_model") or row.get("profile_id") or "unknown"),
        _sql_string(row.get("text_hash")),
        _sql_string(text),
        _sql_vector(row.get("vector") if isinstance(row.get("vector"), list) else []),
        _sql_json(metadata),
    ]
    updates = [
        "subject_id=EXCLUDED.subject_id",
        "subject_type=EXCLUDED.subject_type",
        "embedding_model=EXCLUDED.embedding_model",
        "text_hash=EXCLUDED.text_hash",
        "text=EXCLUDED.text",
        "embedding=EXCLUDED.embedding",
        "metadata=EXCLUDED.metadata",
    ]
    return (
        f"INSERT INTO object_embedding ({', '.join(columns)})\n"
        f"VALUES ({', '.join(values)})\n"
        "ON CONFLICT (embedding_id) DO UPDATE SET\n  "
        + ",\n  ".join(updates)
        + ";\n"
    )


def build_pgvector_embedding_load_plan(
    *,
    stored_vectors_jsonl: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = PGVECTOR_LOAD_PLAN_RUN_ID,
    source_embedding_rows_jsonl: str | Path | None = None,
    schema_dimensions: int = DEFAULT_SCHEMA_DIMENSIONS,
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-pgvector-embedding-load-"))
    stored_rows = _read_jsonl(stored_vectors_jsonl)
    text_lookup = _text_by_embedding_id(source_embedding_rows_jsonl)
    accepted_rows: list[dict[str, Any]] = []
    rejected_rows: list[dict[str, Any]] = []
    statements = [
        "-- Generated by scripts/db/pgvector_embedding_load_plan.py",
        "-- Review before applying to a live database.",
        "BEGIN;",
    ]

    for row in stored_rows:
        embedding_id = str(row.get("embedding_id") or "")
        vector = row.get("vector")
        dimensions = int(row.get("dimensions") or (len(vector) if isinstance(vector, list) else 0) or 0)
        text = text_lookup.get(embedding_id, "")
        issues: list[str] = []
        if not embedding_id:
            issues.append("missing_embedding_id")
        if not isinstance(vector, list) or not vector:
            issues.append("missing_vector")
        if dimensions != schema_dimensions:
            issues.append("dimension_mismatch_for_schema")
        if isinstance(vector, list) and len(vector) != dimensions:
            issues.append("vector_length_mismatch")
        if not text:
            issues.append("missing_source_text")
        if issues:
            rejected_rows.append({
                "embedding_id": embedding_id,
                "subject_id": row.get("subject_id"),
                "dimensions": dimensions,
                "schema_dimensions": schema_dimensions,
                "issues": issues,
            })
            continue
        accepted_rows.append({
            "embedding_id": embedding_id,
            "subject_id": row.get("subject_id"),
            "subject_type": row.get("subject_type"),
            "embedding_model": row.get("embedding_model") or row.get("profile_id") or "unknown",
            "text_hash": row.get("text_hash"),
            "dimensions": dimensions,
        })
        statements.append(_embedding_insert(row, text))

    statements.append("COMMIT;\n")
    sql_path = out / PGVECTOR_LOAD_PLAN_SQL_FILENAME
    accepted_path = out / PGVECTOR_LOAD_PLAN_ACCEPTED_ROWS_FILENAME
    rejected_path = out / PGVECTOR_LOAD_PLAN_REJECTED_ROWS_FILENAME
    summary_path = out / PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME
    sql_path.parent.mkdir(parents=True, exist_ok=True)
    sql_path.write_text("\n".join(statements), encoding="utf-8")
    _write_jsonl(accepted_path, accepted_rows)
    _write_jsonl(rejected_path, rejected_rows)
    summary = {
        "ok": bool(accepted_rows) and not rejected_rows,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "stored_vectors_jsonl": str(stored_vectors_jsonl),
        "source_embedding_rows_jsonl": str(source_embedding_rows_jsonl) if source_embedding_rows_jsonl else "",
        "schema_dimensions": schema_dimensions,
        "input_stored_vector_rows": len(stored_rows),
        "accepted_rows": len(accepted_rows),
        "rejected_rows": len(rejected_rows),
        "files": {
            "load_sql": str(sql_path),
            "accepted_rows": str(accepted_path),
            "rejected_rows": str(rejected_path),
            "summary": str(summary_path),
        },
        "commands": [
            {
                "step": "initialize_schema",
                "command": "psql \"$DATABASE_URL\" -f db/postgres/schema.sql",
            },
            {
                "step": "apply_embedding_load",
                "command": f"psql \"$DATABASE_URL\" -f {sql_path}",
            },
            {
                "step": "count_loaded_embeddings",
                "command": "psql \"$DATABASE_URL\" -c \"select embedding_model, count(*) from object_embedding group by embedding_model order by embedding_model;\"",
            },
        ],
        "safety_notes": [
            "This planner is side-effect free; it writes SQL but does not connect to Postgres.",
            f"Rows with dimensions that do not match the canonical {pgvector_type(schema_dimensions)} schema are rejected before SQL is emitted.",
            "Apply the SQL only against an intended database with pgvector enabled.",
        ],
    }
    _write_json(summary_path, summary)
    return summary


def _self_test() -> int:
    stored = _resource("dist/local-hash-embedding-worker/2026-05-31/stored-vector-rows.jsonl")
    source = _resource("dist/daily-production-runs/2026-05-31/load-audit/merged-jsonl/object-embeddings.jsonl")
    if not stored.exists() or not source.exists():
        raise FileNotFoundError("local hash embedding worker output and source embedding rows are required")
    with tempfile.TemporaryDirectory() as tmp:
        result = build_pgvector_embedding_load_plan(
            stored_vectors_jsonl=stored,
            source_embedding_rows_jsonl=source,
            output_dir=tmp,
            run_id=f"{PGVECTOR_LOAD_PLAN_RUN_ID}-self-test",
        )
        assert result["accepted_rows"] > 0
        assert result["rejected_rows"] == 0
        assert Path(result["files"]["load_sql"]).exists()
    print(json.dumps({
        "ok": True,
        "accepted_rows": result["accepted_rows"],
        "rejected_rows": result["rejected_rows"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit pgvector object_embedding load SQL from stored vector rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--stored-vectors-jsonl")
    parser.add_argument("--source-embedding-rows-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default=PGVECTOR_LOAD_PLAN_RUN_ID)
    parser.add_argument("--schema-dimensions", type=int, default=DEFAULT_SCHEMA_DIMENSIONS)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.stored_vectors_jsonl:
        parser.error("--stored-vectors-jsonl is required unless --self-test is used")
    result = build_pgvector_embedding_load_plan(
        stored_vectors_jsonl=args.stored_vectors_jsonl,
        source_embedding_rows_jsonl=args.source_embedding_rows_jsonl,
        output_dir=args.output_dir,
        run_id=args.run_id,
        schema_dimensions=args.schema_dimensions,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
