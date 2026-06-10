#!/usr/bin/env python3
"""Export rotted-context archive candidates as database seed rows.

This bridges the non-destructive context storage audit to the
`context_archive_candidate` table. The emitted rows are review candidates only;
they do not approve moving, deleting, or rewriting any repository files.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit_context_storage import build_report

DEFAULT_SEED_DIR = ROOT / "db" / "seeds" / "archive-candidates"
DEFAULT_SEED_FILE = DEFAULT_SEED_DIR / "context_archive_candidate.jsonl"
DEFAULT_LOAD_SQL = DEFAULT_SEED_DIR / "load-context-archive-candidates.sql"
DETECTION_SOURCE = "scripts.audit_context_storage.rotted_context_candidates"
DETECTED_BY = "context-storage-audit"


def _source_kind(path: str) -> str:
    if path.startswith(".codex/prompts/"):
        return "repo_prompt"
    if path.startswith("docs/architecture/"):
        return "repo_architecture"
    if path.startswith("docs/codex/"):
        return "repo_codex"
    if path.startswith("docs/spec/"):
        return "repo_spec"
    if path.startswith("docs/strategy/"):
        return "repo_strategy"
    if path.startswith("docs/research/"):
        return "repo_research"
    if path.startswith("docs/howto/"):
        return "repo_howto"
    if path.startswith("docs/"):
        return "repo_doc"
    return "other"


def _source_hash(path: str) -> str | None:
    absolute = ROOT / path
    if not absolute.exists() or not absolute.is_file():
        return None
    digest = hashlib.sha256()
    with absolute.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _archive_candidate_id(*, tenant_id: str, path: str) -> str:
    return f"archive-candidate://{tenant_id}/{quote(path, safe='')}"


def archive_candidate_rows(*, tenant_id: str = "seed") -> list[dict[str, Any]]:
    """Return deterministic context_archive_candidate seed rows."""
    report = build_report(rotted_only=True)
    candidates = report["rotted_context_candidates"]["candidates"]
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        path = str(candidate["path"])
        rows.append(
            {
                "archive_candidate_id": _archive_candidate_id(tenant_id=tenant_id, path=path),
                "tenant_id": tenant_id,
                "source_path": path,
                "source_kind": _source_kind(path),
                "source_hash": _source_hash(path),
                "status": candidate["status"],
                "suggested_action": candidate["suggested_action"],
                "severity_score": candidate["severity_score"],
                "confidence": candidate["confidence"],
                "canonical_replacement_hint": candidate.get("canonical_replacement_hint"),
                "reasons": candidate["reasons"],
                "required_next_checks": candidate["required_next_checks"],
                "detected_by": DETECTED_BY,
                "detection_source": DETECTION_SOURCE,
                "body": {
                    "review_note": (
                        "Generated candidate. Verify references and add a "
                        "supersession note before any approved archive move."
                    ),
                    "audit_policy": report["rotted_context_candidates"]["archive_policy"],
                },
            }
        )
    return sorted(rows, key=lambda row: (-int(row["severity_score"]), row["source_path"]))


def registry_summary(*, tenant_id: str = "seed") -> dict[str, Any]:
    """Return counts and rows for archive candidate registry export."""
    rows = archive_candidate_rows(tenant_id=tenant_id)
    by_status: dict[str, int] = {}
    by_source_kind: dict[str, int] = {}
    by_suggested_action: dict[str, int] = {}
    severity_buckets = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    missing_hashes: list[str] = []
    duplicate_keys = _duplicate_keys(rows)
    for row in rows:
        by_status[row["status"]] = by_status.get(row["status"], 0) + 1
        by_source_kind[row["source_kind"]] = by_source_kind.get(row["source_kind"], 0) + 1
        by_suggested_action[row["suggested_action"]] = by_suggested_action.get(row["suggested_action"], 0) + 1
        if row["source_hash"] is None:
            missing_hashes.append(row["source_path"])
        score = int(row["severity_score"])
        if score >= 5:
            severity_buckets["critical"] += 1
        elif score >= 4:
            severity_buckets["high"] += 1
        elif score >= 3:
            severity_buckets["medium"] += 1
        else:
            severity_buckets["low"] += 1
    return {
        "tenant_id": tenant_id,
        "row_count": len(rows),
        "by_status": dict(sorted(by_status.items())),
        "by_source_kind": dict(sorted(by_source_kind.items())),
        "by_suggested_action": dict(sorted(by_suggested_action.items())),
        "severity_buckets": severity_buckets,
        "max_severity_score": max((int(row["severity_score"]) for row in rows), default=0),
        "duplicate_key_count": len(duplicate_keys),
        "duplicate_keys": duplicate_keys,
        "missing_source_hash_count": len(missing_hashes),
        "missing_source_hash_paths": missing_hashes[:50],
        "rows": rows,
    }


def _duplicate_keys(rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    duplicates: list[dict[str, str]] = []
    for row in rows:
        key = (row["tenant_id"], row["source_path"], row["detection_source"])
        if key in seen:
            duplicates.append({
                "tenant_id": row["tenant_id"],
                "source_path": row["source_path"],
                "detection_source": row["detection_source"],
            })
        seen.add(key)
    return duplicates


def render_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# Context Archive Candidate Registry",
        "",
        f"- Tenant: `{summary['tenant_id']}`",
        f"- Rows: {summary['row_count']}",
        f"- Duplicate keys: {summary['duplicate_key_count']}",
        f"- Missing source hashes: {summary['missing_source_hash_count']}",
        "",
        "## Severity",
        "",
    ]
    for bucket, count in summary["severity_buckets"].items():
        lines.append(f"- {bucket}: {count}")
    lines.append(f"- max severity score: {summary['max_severity_score']}")
    lines.extend(["", "## By Source Kind", ""])
    for source_kind, count in summary["by_source_kind"].items():
        lines.append(f"- {source_kind}: {count}")
    lines.extend(["", "## By Suggested Action", ""])
    for action, count in summary["by_suggested_action"].items():
        lines.append(f"- {action}: {count}")
    return "\n".join(lines) + "\n"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    return path


def write_load_sql(path: Path, *, seed_file: Path = DEFAULT_SEED_FILE) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    relative_seed = seed_file.relative_to(ROOT)
    sql = f"""-- Load context archive candidate seed rows.
-- Review {relative_seed} before running this in a shared database.

BEGIN;

CREATE TEMP TABLE tmp_context_archive_candidate_jsonl (
  body jsonb NOT NULL
);

\\copy tmp_context_archive_candidate_jsonl(body) FROM '{relative_seed}' WITH (FORMAT text);

INSERT INTO context_archive_candidate (
  archive_candidate_id,
  tenant_id,
  source_path,
  source_kind,
  source_hash,
  status,
  suggested_action,
  severity_score,
  confidence,
  canonical_replacement_hint,
  reasons,
  required_next_checks,
  detected_by,
  detection_source,
  body
)
SELECT
  body->>'archive_candidate_id',
  body->>'tenant_id',
  body->>'source_path',
  body->>'source_kind',
  NULLIF(body->>'source_hash', ''),
  body->>'status',
  body->>'suggested_action',
  (body->>'severity_score')::integer,
  body->>'confidence',
  NULLIF(body->>'canonical_replacement_hint', ''),
  body->'reasons',
  body->'required_next_checks',
  body->>'detected_by',
  body->>'detection_source',
  body->'body'
FROM tmp_context_archive_candidate_jsonl
ON CONFLICT (tenant_id, source_path, detection_source)
DO UPDATE SET
  source_kind = EXCLUDED.source_kind,
  source_hash = EXCLUDED.source_hash,
  status = EXCLUDED.status,
  suggested_action = EXCLUDED.suggested_action,
  severity_score = EXCLUDED.severity_score,
  confidence = EXCLUDED.confidence,
  canonical_replacement_hint = EXCLUDED.canonical_replacement_hint,
  reasons = EXCLUDED.reasons,
  required_next_checks = EXCLUDED.required_next_checks,
  detected_by = EXCLUDED.detected_by,
  body = EXCLUDED.body,
  updated_at = now();

COMMIT;
"""
    path.write_text(sql, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tenant-id", default="seed", help="Tenant id for seed rows.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--rows-only", action="store_true", help="Emit only context_archive_candidate rows.")
    parser.add_argument("--write-default", action="store_true", help=f"Write {DEFAULT_SEED_FILE.relative_to(ROOT)}.")
    parser.add_argument("--write-load-sql", action="store_true", help=f"Write {DEFAULT_LOAD_SQL.relative_to(ROOT)}.")
    args = parser.parse_args()

    summary = registry_summary(tenant_id=args.tenant_id)
    if args.write_default:
        write_jsonl(DEFAULT_SEED_FILE, summary["rows"])
        if args.write_load_sql:
            write_load_sql(DEFAULT_LOAD_SQL)
        print(str(DEFAULT_SEED_FILE.relative_to(ROOT)))
        return
    if args.write_load_sql:
        print(str(write_load_sql(DEFAULT_LOAD_SQL).relative_to(ROOT)))
        return

    payload: Any = summary["rows"] if args.rows_only else summary
    if args.format == "markdown" and not args.rows_only:
        print(render_markdown(summary), end="")
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
