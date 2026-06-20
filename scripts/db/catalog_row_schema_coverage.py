#!/usr/bin/env python3
"""Verify catalog row families are covered by the canonical database schema.

This is a read-only contract check for the seed/export bridge:

* every expected JSONL row family has a file,
* every row family has a destination table in db/postgres/schema.sql,
* the generated load SQL references the row family and destination table, and
* bridge output counts line up with row files.

It does not connect to Postgres and it does not read live catalog YAML.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import re
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_integrity import ROW_FILES, read_jsonl


DEFAULT_ROW_DIR = REPO / "dist" / "catalog-manifest-bridge"
DEFAULT_SCHEMA = REPO / "db" / "postgres" / "schema.sql"
DEFAULT_OUTPUT = REPO / "dist" / "catalog-migration-smoke" / "catalog-row-schema-coverage.json"

ROW_FAMILY_TABLES = {
    "components": "component",
    "component_versions": "component_version",
    "component_industries": "component_industry",
    "component_capabilities": "component_capability",
    "component_modalities": "component_modality",
    "component_tags": "component_tag",
    "component_refs": "component_ref",
    "rubric_dimensions": "rubric_dimension",
    "context_objects": "context_object",
    "component_context_objects": "component_context_object",
    "context_mask_contracts": "context_mask_contract",
    "context_transformer_contracts": "context_transformer_contract",
    "manifest_import_batches": "manifest_import_batch",
    "manifest_import_records": "manifest_import_record",
}


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def schema_tables(schema_path: Path) -> set[str]:
    text = schema_path.read_text(encoding="utf-8")
    return set(re.findall(r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", text))


def load_sql_text(row_dir: Path) -> str:
    path = row_dir / "load-catalog-manifests.sql"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def manifest_plan_counts(row_dir: Path) -> dict[str, int]:
    path = row_dir / "manifest-import-plan.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    counts = value.get("counts")
    if not isinstance(counts, dict):
        return {}
    return {str(key): int(value) for key, value in counts.items() if isinstance(value, int)}


def build_schema_coverage_report(
    *,
    row_dir: Path = DEFAULT_ROW_DIR,
    schema_path: Path = DEFAULT_SCHEMA,
    output: Path | None = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    tables = schema_tables(schema_path)
    load_sql = load_sql_text(row_dir)
    plan_counts = manifest_plan_counts(row_dir)
    row_families: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []

    for row_family, filename in sorted(ROW_FILES.items()):
        table = ROW_FAMILY_TABLES.get(row_family)
        path = row_dir / filename
        row_count = len(read_jsonl(path)) if path.exists() else 0
        plan_count = plan_counts.get(row_family)
        entry = {
            "row_family": row_family,
            "file": str(path),
            "table": table,
            "file_exists": path.exists(),
            "row_count": row_count,
            "plan_count": plan_count,
            "schema_table_exists": table in tables if table else False,
            "load_sql_references_file": filename in load_sql,
            "load_sql_references_table": bool(table and re.search(rf"\bINSERT INTO\s+{re.escape(table)}\b", load_sql)),
        }
        row_families.append(entry)
        if not entry["file_exists"]:
            issues.append({"severity": "error", "code": "missing_row_file", "row_family": row_family, "file": str(path)})
        if not table:
            issues.append({"severity": "error", "code": "missing_row_family_table_mapping", "row_family": row_family})
        elif table not in tables:
            issues.append({"severity": "error", "code": "schema_table_missing", "row_family": row_family, "table": table})
        if not entry["load_sql_references_file"]:
            issues.append({"severity": "error", "code": "load_sql_missing_file_reference", "row_family": row_family, "file": filename})
        if not entry["load_sql_references_table"]:
            issues.append({"severity": "error", "code": "load_sql_missing_table_insert", "row_family": row_family, "table": table})
        if plan_count is not None and plan_count != row_count:
            issues.append({
                "severity": "error",
                "code": "manifest_plan_count_mismatch",
                "row_family": row_family,
                "plan_count": plan_count,
                "row_count": row_count,
            })

    unmapped = sorted(set(ROW_FILES) - set(ROW_FAMILY_TABLES))
    for row_family in unmapped:
        issues.append({"severity": "error", "code": "unmapped_row_family", "row_family": row_family})

    severity_counts = Counter(str(issue.get("severity") or "unknown") for issue in issues)
    report = {
        "ok": int(severity_counts.get("error", 0)) == 0,
        "generated_at": utc_now(),
        "row_dir": str(row_dir),
        "schema": str(schema_path),
        "row_family_count": len(row_families),
        "table_count": len(tables),
        "severity_counts": dict(sorted(severity_counts.items())),
        "row_families": row_families,
        "issues": issues,
        "notes": [
            "This report checks import/export row-family coverage only.",
            "It does not connect to Postgres and does not inspect catalog YAML.",
            "Use catalog_row_integrity.py for row-level foreign-key and duplicate checks.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ohh-row-schema-coverage-") as tmp:
        row_dir = Path(tmp)
        for row_family, filename in ROW_FILES.items():
            (row_dir / filename).write_text("{}\n", encoding="utf-8")
        files = "\n".join(filename for filename in ROW_FILES.values())
        inserts = "\n".join(f"INSERT INTO {table} DEFAULT VALUES;" for table in ROW_FAMILY_TABLES.values())
        (row_dir / "load-catalog-manifests.sql").write_text(files + "\n" + inserts + "\n", encoding="utf-8")
        (row_dir / "manifest-import-plan.json").write_text(
            json.dumps({"counts": {row_family: 1 for row_family in ROW_FILES}}),
            encoding="utf-8",
        )
        schema = row_dir / "schema.sql"
        schema.write_text(
            "\n".join(f"CREATE TABLE IF NOT EXISTS {table} (id text);" for table in ROW_FAMILY_TABLES.values()),
            encoding="utf-8",
        )
        report = build_schema_coverage_report(row_dir=row_dir, schema_path=schema, output=None)
        if not report["ok"]:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
    print("[self-test] catalog row schema coverage passed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify catalog row families are covered by the Postgres schema and load SQL.")
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_schema_coverage_report(row_dir=args.row_dir, schema_path=args.schema, output=args.output)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
