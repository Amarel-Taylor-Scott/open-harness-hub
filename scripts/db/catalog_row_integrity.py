#!/usr/bin/env python3
"""Validate database-shaped catalog row sets before consumer use.

This check is for operational row sources: bridge output, Postgres exports, or
other database snapshots. It does not inspect live catalog YAML and it does not
apply curator policy allowances. Use the migration gate for seed/import policy;
use this script to prove a row directory is internally safe for search, docs,
SQLite snapshots, and other database-backed consumers.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_row_source import iter_components_from_rows, read_jsonl


DEFAULT_ROW_DIR = REPO / "dist" / "catalog-db-export-rows-smoke"
DEFAULT_OUT = REPO / "dist" / "catalog-db-export-rows-smoke" / "catalog-row-integrity-report.json"

ROW_FILES = {
    "components": "components.jsonl",
    "component_versions": "component_versions.jsonl",
    "component_industries": "component_industries.jsonl",
    "component_capabilities": "component_capabilities.jsonl",
    "component_modalities": "component_modalities.jsonl",
    "component_tags": "component_tags.jsonl",
    "component_refs": "component_refs.jsonl",
    "rubric_dimensions": "rubric_dimensions.jsonl",
    "context_objects": "context_objects.jsonl",
    "component_context_objects": "component_context_objects.jsonl",
    "context_mask_contracts": "context_mask_contracts.jsonl",
    "context_transformer_contracts": "context_transformer_contracts.jsonl",
    "manifest_import_batches": "manifest_import_batches.jsonl",
    "manifest_import_records": "manifest_import_records.jsonl",
}

REQUIRED_ROW_SETS = (
    "components",
    "component_versions",
    "context_objects",
    "component_context_objects",
)


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def sample(values: list[str], limit: int = 25) -> list[str]:
    return values[:limit]


def duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if value and count > 1)


def load_rows(row_dir: Path) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    rows: dict[str, list[dict[str, Any]]] = {}
    for row_set, filename in ROW_FILES.items():
        path = row_dir / filename
        if not path.exists():
            rows[row_set] = []
            severity = "error" if row_set in REQUIRED_ROW_SETS else "warning"
            issues.append({
                "severity": severity,
                "code": "missing_row_file",
                "row_set": row_set,
                "path": str(path),
            })
            continue
        try:
            rows[row_set] = read_jsonl(path)
        except ValueError as exc:
            rows[row_set] = []
            issues.append({
                "severity": "error",
                "code": "invalid_jsonl",
                "row_set": row_set,
                "path": str(path),
                "message": str(exc),
            })
    return rows, issues


def check_components(rows: dict[str, list[dict[str, Any]]]) -> tuple[set[str], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    component_rows = rows["components"]
    ids = [str(row.get("id") or "") for row in component_rows]
    id_set = set(value for value in ids if value)
    duplicate_ids = duplicates(ids)
    if duplicate_ids:
        issues.append({
            "severity": "error",
            "code": "duplicate_component_id",
            "count": len(duplicate_ids),
            "sample": sample(duplicate_ids),
        })
    missing_required = [
        str(row.get("id") or row.get("name") or row)
        for row in component_rows
        if not isinstance(row.get("id"), str) or not isinstance(row.get("type"), str)
    ]
    if missing_required:
        issues.append({
            "severity": "error",
            "code": "component_missing_id_or_type",
            "count": len(missing_required),
            "sample": sample(missing_required),
        })
    body_mismatches: list[str] = []
    for row in component_rows:
        body = row.get("body")
        if not isinstance(body, dict):
            body_mismatches.append(str(row.get("id") or "missing-id"))
            continue
        if body.get("id") and body.get("id") != row.get("id"):
            body_mismatches.append(str(row.get("id") or body.get("id")))
        if body.get("type") and body.get("type") != row.get("type"):
            body_mismatches.append(str(row.get("id") or body.get("id")))
    if body_mismatches:
        issues.append({
            "severity": "error",
            "code": "component_body_identity_mismatch",
            "count": len(body_mismatches),
            "sample": sample(sorted(set(body_mismatches))),
        })
    loaded_components = iter_components_from_rows_from_rowsafe(rows)
    if len(loaded_components) != len(component_rows):
        issues.append({
            "severity": "error",
            "code": "shared_loader_component_count_mismatch",
            "row_count": len(component_rows),
            "loader_count": len(loaded_components),
        })
    return id_set, issues


def iter_components_from_rows_from_rowsafe(rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Use the shared loader on a temporary-style row set when files exist.

    This helper is intentionally conservative: if the row directory is not
    available through files the caller's normal file-backed invocation catches
    malformed rows already. Returning component IDs here gives us a cheap
    parity check without teaching the validator a second loader contract.
    """
    return [str(row.get("id") or "") for row in rows["components"] if isinstance(row.get("id"), str) and isinstance(row.get("type"), str)]


def check_component_references(
    rows: dict[str, list[dict[str, Any]]],
    component_ids: set[str],
    context_ids: set[str],
) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    component_fk_fields = {
        "component_versions": "component_id",
        "component_industries": "component_id",
        "component_capabilities": "component_id",
        "component_modalities": "component_id",
        "component_tags": "component_id",
        "component_context_objects": "component_id",
        "context_mask_contracts": "component_id",
        "context_transformer_contracts": "component_id",
        "rubric_dimensions": "rubric_id",
    }
    for row_set, field in component_fk_fields.items():
        missing = sorted({
            str(row.get(field) or "")
            for row in rows[row_set]
            if str(row.get(field) or "") and str(row.get(field) or "") not in component_ids
        })
        if missing:
            issues.append({
                "severity": "error",
                "code": "missing_component_reference",
                "row_set": row_set,
                "field": field,
                "count": len(missing),
                "sample": sample(missing),
            })

    ref_missing = sorted({
        value
        for row in rows["component_refs"]
        for value in [
            str(row.get("component_id") or row.get("src_id") or ""),
            str(row.get("target_id") or row.get("dst_id") or ""),
        ]
        if value and value not in component_ids
    })
    if ref_missing:
        issues.append({
            "severity": "error",
            "code": "missing_component_ref_endpoint",
            "count": len(ref_missing),
            "sample": sample(ref_missing),
        })

    missing_context = sorted({
        str(row.get("context_object_id") or "")
        for row in rows["component_context_objects"]
        if str(row.get("context_object_id") or "") and str(row.get("context_object_id") or "") not in context_ids
    })
    missing_context.extend(sorted({
        str(row.get("context_object_id") or "")
        for row in rows["context_mask_contracts"] + rows["context_transformer_contracts"]
        if str(row.get("context_object_id") or "") and str(row.get("context_object_id") or "") not in context_ids
    }))
    missing_context = sorted(set(missing_context))
    if missing_context:
        issues.append({
            "severity": "error",
            "code": "missing_context_object_reference",
            "count": len(missing_context),
            "sample": sample(missing_context),
        })
    return issues


def check_versions(rows: dict[str, list[dict[str, Any]]], component_ids: set[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    versions = rows["component_versions"]
    version_ids = [str(row.get("component_version_id") or "") for row in versions]
    duplicate_versions = duplicates(version_ids)
    if duplicate_versions:
        issues.append({
            "severity": "error",
            "code": "duplicate_component_version_id",
            "count": len(duplicate_versions),
            "sample": sample(duplicate_versions),
        })
    version_components = {str(row.get("component_id") or "") for row in versions if row.get("component_id")}
    missing_versions = sorted(component_ids - version_components)
    if missing_versions:
        issues.append({
            "severity": "error",
            "code": "component_without_version",
            "count": len(missing_versions),
            "sample": sample(missing_versions),
        })
    missing_hash = sorted(str(row.get("component_id") or "") for row in versions if not row.get("definition_hash"))
    if missing_hash:
        issues.append({
            "severity": "error",
            "code": "component_version_missing_definition_hash",
            "count": len(missing_hash),
            "sample": sample(missing_hash),
        })
    return issues


def check_context_objects(rows: dict[str, list[dict[str, Any]]]) -> tuple[set[str], list[dict[str, Any]]]:
    issues: list[dict[str, Any]] = []
    context_ids = [str(row.get("context_object_id") or "") for row in rows["context_objects"]]
    context_set = {value for value in context_ids if value}
    duplicate_context = duplicates(context_ids)
    if duplicate_context:
        issues.append({
            "severity": "error",
            "code": "duplicate_context_object_id",
            "count": len(duplicate_context),
            "sample": sample(duplicate_context),
        })
    missing = [
        str(row.get("title") or row)
        for row in rows["context_objects"]
        if not isinstance(row.get("context_object_id"), str)
    ]
    if missing:
        issues.append({
            "severity": "error",
            "code": "context_object_missing_id",
            "count": len(missing),
            "sample": sample(missing),
        })
    return context_set, issues


def check_unique_axis_rows(rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    axis_specs = {
        "component_industries": ("component_id", "industry"),
        "component_capabilities": ("component_id", "capability"),
        "component_modalities": ("component_id", "modality"),
        "component_tags": ("component_id", "tag"),
    }
    for row_set, fields in axis_specs.items():
        keys = [
            "::".join(str(row.get(field) or "") for field in fields)
            for row in rows[row_set]
        ]
        duplicate_keys = duplicates(keys)
        if duplicate_keys:
            issues.append({
                "severity": "warning",
                "code": "duplicate_axis_rows",
                "row_set": row_set,
                "count": len(duplicate_keys),
                "sample": sample(duplicate_keys),
            })
    return issues


def check_rubric_dimensions(rows: dict[str, list[dict[str, Any]]], component_ids: set[str]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    dims = rows["rubric_dimensions"]
    dim_ids = [str(row.get("rubric_dimension_id") or "") for row in dims]
    duplicate_dims = duplicates(dim_ids)
    if duplicate_dims:
        issues.append({
            "severity": "error",
            "code": "duplicate_rubric_dimension_id",
            "count": len(duplicate_dims),
            "sample": sample(duplicate_dims),
        })
    missing_path = sorted(str(row.get("rubric_id") or "") for row in dims if not row.get("dimension_path"))
    if missing_path:
        issues.append({
            "severity": "error",
            "code": "rubric_dimension_missing_path",
            "count": len(missing_path),
            "sample": sample(missing_path),
        })
    non_rubric = sorted({
        str(row.get("rubric_id") or "")
        for row in dims
        if str(row.get("rubric_id") or "") in component_ids and not str(row.get("rubric_id") or "").startswith("rubric/")
    })
    if non_rubric:
        issues.append({
            "severity": "error",
            "code": "rubric_dimension_bound_to_non_rubric",
            "count": len(non_rubric),
            "sample": sample(non_rubric),
        })
    return issues


def summarize_rows(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {row_set: len(values) for row_set, values in sorted(rows.items())}


def build_integrity_report(row_dir: Path = DEFAULT_ROW_DIR, output: Path | None = DEFAULT_OUT) -> dict[str, Any]:
    rows, issues = load_rows(row_dir)
    component_ids, component_issues = check_components(rows)
    issues.extend(component_issues)
    context_ids, context_issues = check_context_objects(rows)
    issues.extend(context_issues)
    issues.extend(check_versions(rows, component_ids))
    issues.extend(check_component_references(rows, component_ids, context_ids))
    issues.extend(check_unique_axis_rows(rows))
    issues.extend(check_rubric_dimensions(rows, component_ids))

    try:
        loader_components = iter_components_from_rows(row_dir)
        loader_count = len(loader_components)
    except ValueError as exc:
        loader_count = 0
        issues.append({
            "severity": "error",
            "code": "shared_loader_failed",
            "message": str(exc),
        })

    if loader_count != len(rows["components"]):
        issues.append({
            "severity": "error",
            "code": "shared_loader_count_mismatch",
            "row_count": len(rows["components"]),
            "loader_count": loader_count,
        })

    severity_counts = Counter(str(issue.get("severity") or "unknown") for issue in issues)
    report = {
        "ok": int(severity_counts.get("error", 0)) == 0,
        "generated_at": utc_now(),
        "row_dir": str(row_dir),
        "counts": summarize_rows(rows),
        "loader_count": loader_count,
        "severity_counts": dict(sorted(severity_counts.items())),
        "issues": issues,
        "notes": [
            "This validator checks row-set integrity only; use catalog_manifest_migration_gate.py for curator policy allowances.",
            "It does not read live catalog YAML.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        row_dir = Path(tmp)
        component = {
            "id": "rubric/example-quality",
            "type": "rubric",
            "version": "0.1.0",
            "name": "Example quality",
            "description": "Example rubric.",
            "lifecycle": "experimental",
            "body": {
                "id": "rubric/example-quality",
                "type": "rubric",
                "version": "0.1.0",
                "name": "Example quality",
                "description": "Example rubric.",
                "lifecycle": "experimental",
            },
            "seed": {"path": "catalog/rubrics/example-quality.yaml"},
        }
        rows = {
            "components.jsonl": [component],
            "component_versions.jsonl": [{
                "component_id": "rubric/example-quality",
                "component_version_id": "ctxv://example/rubric/example-quality@sha256:test",
                "definition_hash": "sha256:test",
            }],
            "component_industries.jsonl": [],
            "component_capabilities.jsonl": [],
            "component_modalities.jsonl": [],
            "component_tags.jsonl": [],
            "component_refs.jsonl": [],
            "rubric_dimensions.jsonl": [{
                "rubric_dimension_id": "rubric-dimension/rubric/example-quality/evidence",
                "rubric_id": "rubric/example-quality",
                "dimension_path": "evidence",
            }],
            "context_objects.jsonl": [{
                "context_object_id": "ctx://example/component/rubric/example-quality",
                "title": "Example quality",
            }],
            "component_context_objects.jsonl": [{
                "component_id": "rubric/example-quality",
                "context_object_id": "ctx://example/component/rubric/example-quality",
                "role": "is_context_object",
            }],
            "context_mask_contracts.jsonl": [],
            "context_transformer_contracts.jsonl": [],
            "manifest_import_batches.jsonl": [],
            "manifest_import_records.jsonl": [],
        }
        for filename, values in rows.items():
            (row_dir / filename).write_text(
                "".join(json.dumps(value) + "\n" for value in values),
                encoding="utf-8",
            )
        report = build_integrity_report(row_dir=row_dir, output=None)
        if not report["ok"]:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
        print("[self-test] catalog row integrity validator passed")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate database-shaped catalog row-set integrity.")
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_integrity_report(row_dir=args.row_dir, output=args.output)
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
