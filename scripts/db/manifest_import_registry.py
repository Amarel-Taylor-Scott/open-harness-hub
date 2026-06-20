#!/usr/bin/env python3
"""Export catalog manifest import records as database seed rows.

This is a narrow wrapper around `catalog_manifest_bridge.py` for the
`manifest_import_batch` and `manifest_import_record` tables. It makes YAML
manifest state reviewable as database records without moving or rewriting the
catalog files.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from collections import Counter
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_manifest_bridge import build_bridge_plan

DEFAULT_SEED_DIR = ROOT / "db" / "seeds" / "manifest-import"
DEFAULT_BATCH_SEED = DEFAULT_SEED_DIR / "manifest_import_batch.jsonl"
DEFAULT_RECORD_SEED = DEFAULT_SEED_DIR / "manifest_import_record.jsonl"
DEFAULT_LOAD_SQL = DEFAULT_SEED_DIR / "load-manifest-import-records.sql"
DEFAULT_BATCH_ID = "manifest-import-batch/repo-catalog-current"


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def manifest_import_rows(
    *,
    dated_review_days: int = 90,
    batch_id: str = DEFAULT_BATCH_ID,
) -> dict[str, Any]:
    """Return manifest_import_batch and manifest_import_record seed rows."""
    with tempfile.TemporaryDirectory(prefix="ohh-manifest-import-registry-") as tmp:
        report = build_bridge_plan(
            output_dir=Path(tmp),
            dated_review_days=dated_review_days,
            batch_id=batch_id,
        )
        batch_rows = _read_jsonl(Path(report["files"]["manifest_import_batches"]))
        record_rows = _read_jsonl(Path(report["files"]["manifest_import_records"]))
    return {
        "batch_rows": batch_rows,
        "record_rows": record_rows,
    }


def registry_summary(
    *,
    dated_review_days: int = 90,
    batch_id: str = DEFAULT_BATCH_ID,
) -> dict[str, Any]:
    """Return counts and rows for manifest import registry export."""
    rows = manifest_import_rows(dated_review_days=dated_review_days, batch_id=batch_id)
    batches = rows["batch_rows"]
    records = rows["record_rows"]
    by_status = Counter(str(row.get("import_status")) for row in records)
    by_action = Counter(str(row.get("recommended_action")) for row in records)
    by_type = Counter(str(row.get("component_type")) for row in records if row.get("component_type"))
    flagged = [row for row in records if row.get("rotted_context_flags")]
    duplicate_keys = _duplicate_record_keys(records)
    missing_hashes = [row["manifest_path"] for row in records if not row.get("manifest_hash")]
    return {
        "batch_id": batch_id,
        "dated_review_days": dated_review_days,
        "batch_count": len(batches),
        "record_count": len(records),
        "by_import_status": dict(sorted(by_status.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "by_component_type": dict(sorted(by_type.items())),
        "flagged_record_count": len(flagged),
        "duplicate_record_key_count": len(duplicate_keys),
        "duplicate_record_keys": duplicate_keys,
        "missing_manifest_hash_count": len(missing_hashes),
        "missing_manifest_hash_paths": missing_hashes[:50],
        "batch_rows": batches,
        "record_rows": records,
    }


def _duplicate_record_keys(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates: list[dict[str, str]] = []
    for row in rows:
        key = (str(row.get("manifest_import_batch_id")), str(row.get("manifest_path")))
        if key in seen:
            duplicates.append({
                "manifest_import_batch_id": key[0],
                "manifest_path": key[1],
            })
        seen.add(key)
    return duplicates


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Manifest Import Registry",
        "",
        f"- Batch id: `{summary['batch_id']}`",
        f"- Batches: {summary['batch_count']}",
        f"- Records: {summary['record_count']}",
        f"- Flagged records: {summary['flagged_record_count']}",
        f"- Duplicate record keys: {summary['duplicate_record_key_count']}",
        f"- Missing manifest hashes: {summary['missing_manifest_hash_count']}",
        "",
        "## By Import Status",
        "",
    ]
    for status, count in summary["by_import_status"].items():
        lines.append(f"- {status}: {count}")
    lines.extend(["", "## By Recommended Action", ""])
    for action, count in summary["by_recommended_action"].items():
        lines.append(f"- {action}: {count}")
    lines.extend(["", "## By Component Type", ""])
    for component_type, count in summary["by_component_type"].items():
        lines.append(f"- {component_type}: {count}")
    return "\n".join(lines) + "\n"


def write_load_sql(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sql = """-- Load manifest import seed rows.
-- Review db/seeds/manifest-import/*.jsonl before running this in a shared database.

BEGIN;

CREATE TEMP TABLE tmp_manifest_import_batch_jsonl (
  body jsonb NOT NULL
);

CREATE TEMP TABLE tmp_manifest_import_record_jsonl (
  body jsonb NOT NULL
);

\\copy tmp_manifest_import_batch_jsonl(body) FROM 'db/seeds/manifest-import/manifest_import_batch.jsonl' WITH (FORMAT text);
\\copy tmp_manifest_import_record_jsonl(body) FROM 'db/seeds/manifest-import/manifest_import_record.jsonl' WITH (FORMAT text);

INSERT INTO manifest_import_batch (
  manifest_import_batch_id,
  source_kind,
  source_ref,
  importer,
  import_mode,
  policy,
  summary
)
SELECT
  body->>'manifest_import_batch_id',
  body->>'source_kind',
  body->>'source_ref',
  body->>'importer',
  body->>'import_mode',
  body->'policy',
  body->'summary'
FROM tmp_manifest_import_batch_jsonl
ON CONFLICT (manifest_import_batch_id)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  source_ref = EXCLUDED.source_ref,
  importer = EXCLUDED.importer,
  import_mode = EXCLUDED.import_mode,
  policy = EXCLUDED.policy,
  summary = EXCLUDED.summary;

INSERT INTO manifest_import_record (
  manifest_import_record_id,
  manifest_import_batch_id,
  component_id,
  component_type,
  manifest_path,
  manifest_hash,
  manifest_updated,
  manifest_lifecycle,
  manifest_freshness,
  definition_source,
  import_status,
  recommended_action,
  rotted_context_flags,
  row_counts,
  source_ref,
  error_message
)
SELECT
  body->>'manifest_import_record_id',
  body->>'manifest_import_batch_id',
  NULLIF(body->>'component_id', ''),
  NULLIF(body->>'component_type', ''),
  body->>'manifest_path',
  body->>'manifest_hash',
  NULLIF(body->>'manifest_updated', '')::date,
  NULLIF(body->>'manifest_lifecycle', ''),
  NULLIF(body->>'manifest_freshness', ''),
  body->>'definition_source',
  body->>'import_status',
  body->>'recommended_action',
  body->'rotted_context_flags',
  body->'row_counts',
  NULLIF(body->>'source_ref', ''),
  NULLIF(body->>'error_message', '')
FROM tmp_manifest_import_record_jsonl
ON CONFLICT (manifest_import_batch_id, manifest_path)
DO UPDATE SET
  component_id = EXCLUDED.component_id,
  component_type = EXCLUDED.component_type,
  manifest_hash = EXCLUDED.manifest_hash,
  manifest_updated = EXCLUDED.manifest_updated,
  manifest_lifecycle = EXCLUDED.manifest_lifecycle,
  manifest_freshness = EXCLUDED.manifest_freshness,
  definition_source = EXCLUDED.definition_source,
  import_status = EXCLUDED.import_status,
  recommended_action = EXCLUDED.recommended_action,
  rotted_context_flags = EXCLUDED.rotted_context_flags,
  row_counts = EXCLUDED.row_counts,
  source_ref = EXCLUDED.source_ref,
  error_message = EXCLUDED.error_message;

COMMIT;
"""
    path.write_text(sql, encoding="utf-8")
    return path


def write_default(summary: dict[str, Any]) -> None:
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    _write_jsonl(DEFAULT_BATCH_SEED, summary["batch_rows"])
    _write_jsonl(DEFAULT_RECORD_SEED, summary["record_rows"])
    write_load_sql(DEFAULT_LOAD_SQL)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dated-review-days", type=int, default=90)
    parser.add_argument("--batch-id", default=DEFAULT_BATCH_ID)
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--rows-only", choices=("batch", "record"), help="Emit only one seed row set.")
    parser.add_argument("--write-default", action="store_true", help=f"Write {DEFAULT_SEED_DIR.relative_to(ROOT)}.")
    args = parser.parse_args()

    summary = registry_summary(dated_review_days=args.dated_review_days, batch_id=args.batch_id)
    if args.write_default:
        write_default(summary)
        print(str(DEFAULT_SEED_DIR.relative_to(ROOT)))
        return
    if args.rows_only == "batch":
        print(json.dumps(summary["batch_rows"], indent=2, sort_keys=True, ensure_ascii=False))
        return
    if args.rows_only == "record":
        print(json.dumps(summary["record_rows"], indent=2, sort_keys=True, ensure_ascii=False))
        return
    if args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        payload = {key: value for key, value in summary.items() if key not in {"batch_rows", "record_rows"}}
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
