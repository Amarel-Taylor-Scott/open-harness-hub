#!/usr/bin/env python3
"""Export catalog YAML reader audit results as database seed rows.

The source audit distinguishes expected seed/export YAML readers from
operational consumers that should move to database row sources. This exporter
turns that audit into `catalog_reader_migration_candidate` rows so the migration
queue is trackable in the database.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
from scripts._repo_paths import resource as _resource
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db.catalog_yaml_reader_audit import audit_paths, default_paths

DEFAULT_SEED_DIR = _resource("db") / "seeds" / "catalog-reader-migration"
DEFAULT_SEED_FILE = DEFAULT_SEED_DIR / "catalog_reader_migration_candidate.jsonl"
DEFAULT_LOAD_SQL = DEFAULT_SEED_DIR / "load-catalog-reader-migration-candidates.sql"
DETECTED_BY = "scripts.db.catalog_yaml_reader_audit"

RECOMMENDED_ACTION_BY_CLASSIFICATION = {
    "seed_export_validation": "keep_seed_export",
    "seed_export_bridge": "keep_seed_export",
    "migration_infrastructure": "review",
    "row_backed_consumer": "keep_row_backed_fallback",
    "operational_migration_candidate": "migrate_to_catalog_row_source",
    "draft_generation": "keep_seed_export",
    "data_jsonl_utility": "review",
    "documentation_or_example": "review",
    "unknown_yaml_reader": "classify_reader",
}

MIGRATION_STATUS_BY_CLASSIFICATION = {
    "seed_export_validation": "not_required",
    "seed_export_bridge": "not_required",
    "migration_infrastructure": "review",
    "row_backed_consumer": "row_backed",
    "operational_migration_candidate": "candidate",
    "draft_generation": "not_required",
    "data_jsonl_utility": "review",
    "documentation_or_example": "not_required",
    "unknown_yaml_reader": "review",
}

PRIORITY_BY_CLASSIFICATION = {
    "operational_migration_candidate": 90,
    "unknown_yaml_reader": 80,
    "migration_infrastructure": 55,
    "data_jsonl_utility": 45,
    "row_backed_consumer": 30,
    "seed_export_bridge": 20,
    "seed_export_validation": 15,
    "draft_generation": 10,
    "documentation_or_example": 5,
}


def _reader_candidate_id(*, tenant_id: str, path: str) -> str:
    return f"catalog-reader-candidate://{tenant_id}/{quote(path, safe='')}"


def _source_kind(path: str) -> str:
    if path.startswith("scripts/"):
        return "script"
    if path.startswith("docs/"):
        return "doc"
    return "other"


def _owner_team(classification: str) -> str:
    if classification in {"operational_migration_candidate", "row_backed_consumer", "migration_infrastructure"}:
        return "platform-data"
    if classification in {"seed_export_validation", "seed_export_bridge", "draft_generation"}:
        return "catalog-curation"
    return "platform-architecture"


def _row_for_entry(*, tenant_id: str, entry: dict[str, Any]) -> dict[str, Any]:
    classification = str(entry["classification"])
    path = str(entry["path"])
    return {
        "reader_candidate_id": _reader_candidate_id(tenant_id=tenant_id, path=path),
        "tenant_id": tenant_id,
        "source_path": path,
        "source_kind": _source_kind(path),
        "classification": classification,
        "migration_status": MIGRATION_STATUS_BY_CLASSIFICATION[classification],
        "priority": PRIORITY_BY_CLASSIFICATION[classification],
        "recommended_action": RECOMMENDED_ACTION_BY_CLASSIFICATION[classification],
        "matches": entry.get("matches") or {},
        "samples": entry.get("samples") or [],
        "note": entry.get("note"),
        "owner_team": _owner_team(classification),
        "detected_by": DETECTED_BY,
        "body": {
            "audit_classification_note": entry.get("note"),
            "migration_rule": (
                "Operational readers should use catalog_row_source.py or a "
                "database-backed equivalent. Seed/export readers may remain "
                "file-backed by design."
            ),
        },
    }


def catalog_reader_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return deterministic catalog_reader_migration_candidate seed rows."""
    report = audit_paths(default_paths())
    rows = [_row_for_entry(tenant_id=tenant_id, entry=entry) for entry in report["entries"]]
    return sorted(rows, key=lambda row: (-int(row["priority"]), row["source_path"]))


def registry_summary(*, tenant_id: str = "seed") -> dict[str, Any]:
    """Return counts and rows for catalog reader migration registry export."""
    rows = catalog_reader_rows(tenant_id=tenant_id)
    by_classification = Counter(str(row["classification"]) for row in rows)
    by_status = Counter(str(row["migration_status"]) for row in rows)
    by_action = Counter(str(row["recommended_action"]) for row in rows)
    duplicate_keys = _duplicate_keys(rows)
    candidate_rows = [row for row in rows if row["migration_status"] in {"candidate", "review"}]
    return {
        "tenant_id": tenant_id,
        "row_count": len(rows),
        "migration_candidate_count": sum(1 for row in rows if row["migration_status"] == "candidate"),
        "review_count": sum(1 for row in rows if row["migration_status"] == "review"),
        "tracked_followup_count": len(candidate_rows),
        "duplicate_key_count": len(duplicate_keys),
        "duplicate_keys": duplicate_keys,
        "by_classification": dict(sorted(by_classification.items())),
        "by_migration_status": dict(sorted(by_status.items())),
        "by_recommended_action": dict(sorted(by_action.items())),
        "rows": rows,
    }


def _duplicate_keys(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str]] = set()
    duplicates: list[dict[str, str]] = []
    for row in rows:
        key = (row["tenant_id"], row["source_path"])
        if key in seen:
            duplicates.append({"tenant_id": key[0], "source_path": key[1]})
        seen.add(key)
    return duplicates


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Catalog Reader Migration Registry",
        "",
        f"- Tenant: `{summary['tenant_id']}`",
        f"- Rows: {summary['row_count']}",
        f"- Migration candidates: {summary['migration_candidate_count']}",
        f"- Review rows: {summary['review_count']}",
        f"- Duplicate keys: {summary['duplicate_key_count']}",
        "",
        "## By Classification",
        "",
    ]
    for classification, count in summary["by_classification"].items():
        lines.append(f"- {classification}: {count}")
    lines.extend(["", "## By Migration Status", ""])
    for status, count in summary["by_migration_status"].items():
        lines.append(f"- {status}: {count}")
    return "\n".join(lines) + "\n"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_load_sql(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    sql = """-- Load catalog reader migration candidate seed rows.
-- Review db/seeds/catalog-reader-migration/catalog_reader_migration_candidate.jsonl before loading.

BEGIN;

CREATE TEMP TABLE tmp_catalog_reader_migration_candidate_jsonl (
  body jsonb NOT NULL
);

\\copy tmp_catalog_reader_migration_candidate_jsonl(body) FROM 'db/seeds/catalog-reader-migration/catalog_reader_migration_candidate.jsonl' WITH (FORMAT text);

INSERT INTO catalog_reader_migration_candidate (
  reader_candidate_id,
  tenant_id,
  source_path,
  source_kind,
  classification,
  migration_status,
  priority,
  recommended_action,
  matches,
  samples,
  note,
  owner_team,
  detected_by,
  body
)
SELECT
  body->>'reader_candidate_id',
  body->>'tenant_id',
  body->>'source_path',
  body->>'source_kind',
  body->>'classification',
  body->>'migration_status',
  (body->>'priority')::integer,
  body->>'recommended_action',
  body->'matches',
  body->'samples',
  NULLIF(body->>'note', ''),
  NULLIF(body->>'owner_team', ''),
  body->>'detected_by',
  body->'body'
FROM tmp_catalog_reader_migration_candidate_jsonl
ON CONFLICT (tenant_id, source_path)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  classification = EXCLUDED.classification,
  migration_status = EXCLUDED.migration_status,
  priority = EXCLUDED.priority,
  recommended_action = EXCLUDED.recommended_action,
  matches = EXCLUDED.matches,
  samples = EXCLUDED.samples,
  note = EXCLUDED.note,
  owner_team = EXCLUDED.owner_team,
  detected_by = EXCLUDED.detected_by,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
"""
    path.write_text(sql, encoding="utf-8")
    return path


def write_default(summary: dict[str, Any]) -> None:
    DEFAULT_SEED_DIR.mkdir(parents=True, exist_ok=True)
    write_jsonl(DEFAULT_SEED_FILE, summary["rows"])
    write_load_sql(DEFAULT_LOAD_SQL)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", default="seed")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--rows-only", action="store_true")
    parser.add_argument("--write-default", action="store_true", help=f"Write {DEFAULT_SEED_DIR.relative_to(ROOT)}.")
    args = parser.parse_args()

    summary = registry_summary(tenant_id=args.tenant_id)
    if args.write_default:
        write_default(summary)
        print(str(DEFAULT_SEED_DIR.relative_to(ROOT)))
        return
    if args.rows_only:
        print(json.dumps(summary["rows"], indent=2, sort_keys=True, ensure_ascii=False))
        return
    if args.format == "markdown":
        print(render_markdown(summary), end="")
    else:
        payload = {key: value for key, value in summary.items() if key != "rows"}
        print(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
