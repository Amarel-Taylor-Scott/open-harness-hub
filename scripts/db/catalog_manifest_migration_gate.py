#!/usr/bin/env python3
"""Gate catalog manifest row sets before promoting them into Postgres.

The bridge turns YAML manifests into database-shaped JSONL. This gate checks
that the generated rows are internally consistent and that any duplicate,
review, or archive recommendations have been explicitly accepted by the caller.

It is intentionally side-effect free: it does not connect to Postgres, mutate
catalog files, or apply the generated load SQL.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_manifest_bridge import build_bridge_plan

DEFAULT_ROW_DIR = REPO / "dist" / "catalog-manifest-bridge"
DEFAULT_OUT = REPO / "dist" / "catalog-manifest-bridge" / "migration-gate-report.json"
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


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
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


def _duplicates(values: list[str]) -> list[str]:
    counts = Counter(values)
    return sorted(value for value, count in counts.items() if value and count > 1)


def _sample(values: list[str], limit: int = 25) -> list[str]:
    return values[:limit]


def _load_rows(row_dir: Path) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    plan_path = row_dir / "manifest-import-plan.json"
    plan = _read_json(plan_path) if plan_path.exists() else {"counts": {}, "files": {}}
    rows = {name: _read_jsonl(row_dir / filename) for name, filename in ROW_FILES.items()}
    return plan, rows


def _check_counts(plan: dict[str, Any], rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    expected = plan.get("counts") if isinstance(plan.get("counts"), dict) else {}
    for name, loaded in sorted(rows.items()):
        if name not in expected:
            issues.append({
                "severity": "warning",
                "code": "missing_expected_count",
                "row_set": name,
                "message": "manifest-import-plan.json does not declare this row-set count.",
            })
            continue
        if int(expected[name]) != len(loaded):
            issues.append({
                "severity": "error",
                "code": "row_count_mismatch",
                "row_set": name,
                "expected": int(expected[name]),
                "actual": len(loaded),
            })
    return issues


def _check_identity(rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    component_ids = [str(row.get("id") or "") for row in rows["components"]]
    component_set = set(component_ids)
    context_ids = [str(row.get("context_object_id") or "") for row in rows["context_objects"]]
    context_set = set(context_ids)
    duplicate_components = _duplicates(component_ids)
    duplicate_context = _duplicates(context_ids)
    duplicate_mask_contracts = _duplicates(
        [str(row.get("mask_contract_id") or "") for row in rows["context_mask_contracts"]]
    )
    duplicate_transformer_contracts = _duplicates(
        [str(row.get("transformer_contract_id") or "") for row in rows["context_transformer_contracts"]]
    )
    if duplicate_components:
        issues.append({
            "severity": "error",
            "code": "duplicate_component_rows",
            "count": len(duplicate_components),
            "sample": _sample(duplicate_components),
        })
    if duplicate_context:
        issues.append({
            "severity": "error",
            "code": "duplicate_context_object_rows",
            "count": len(duplicate_context),
            "sample": _sample(duplicate_context),
        })
    if duplicate_mask_contracts:
        issues.append({
            "severity": "error",
            "code": "duplicate_context_mask_contract_rows",
            "count": len(duplicate_mask_contracts),
            "sample": _sample(duplicate_mask_contracts),
        })
    if duplicate_transformer_contracts:
        issues.append({
            "severity": "error",
            "code": "duplicate_context_transformer_contract_rows",
            "count": len(duplicate_transformer_contracts),
            "sample": _sample(duplicate_transformer_contracts),
        })

    component_fk_checks = {
        "component_versions": "component_id",
        "component_industries": "component_id",
        "component_capabilities": "component_id",
        "component_modalities": "component_id",
        "component_tags": "component_id",
        "rubric_dimensions": "rubric_id",
        "component_context_objects": "component_id",
    }
    for row_set, field in component_fk_checks.items():
        missing = sorted({
            str(row.get(field) or "")
            for row in rows[row_set]
            if str(row.get(field) or "") and str(row.get(field) or "") not in component_set
        })
        if missing:
            issues.append({
                "severity": "error",
                "code": "missing_component_reference",
                "row_set": row_set,
                "field": field,
                "count": len(missing),
                "sample": _sample(missing),
            })

    ref_missing = sorted({
        str(row.get(field) or "")
        for row in rows["component_refs"]
        for field in ("src_id", "dst_id")
        if str(row.get(field) or "") and str(row.get(field) or "") not in component_set
    })
    if ref_missing:
        issues.append({
            "severity": "error",
            "code": "missing_component_ref_target",
            "count": len(ref_missing),
            "sample": _sample(ref_missing),
        })

    binding_missing_context = sorted({
        str(row.get("context_object_id") or "")
        for row in rows["component_context_objects"]
        if str(row.get("context_object_id") or "") and str(row.get("context_object_id") or "") not in context_set
    })
    if binding_missing_context:
        issues.append({
            "severity": "error",
            "code": "missing_context_object_reference",
            "count": len(binding_missing_context),
            "sample": _sample(binding_missing_context),
        })

    for row_set, id_field in (
        ("context_mask_contracts", "mask_contract_id"),
        ("context_transformer_contracts", "transformer_contract_id"),
    ):
        missing_context = sorted({
            str(row.get("context_object_id") or "")
            for row in rows[row_set]
            if str(row.get("context_object_id") or "") and str(row.get("context_object_id") or "") not in context_set
        })
        if missing_context:
            issues.append({
                "severity": "error",
                "code": "missing_contract_context_object_reference",
                "row_set": row_set,
                "id_field": id_field,
                "count": len(missing_context),
                "sample": _sample(missing_context),
            })
        missing_component = sorted({
            str(row.get("component_id") or "")
            for row in rows[row_set]
            if str(row.get("component_id") or "") and str(row.get("component_id") or "") not in component_set
        })
        if missing_component:
            issues.append({
                "severity": "error",
                "code": "missing_contract_component_reference",
                "row_set": row_set,
                "id_field": id_field,
                "count": len(missing_component),
                "sample": _sample(missing_component),
            })

    return issues


def _policy_counts(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    records = rows["manifest_import_records"]
    actions = Counter(str(row.get("recommended_action") or "") for row in records)
    statuses = Counter(str(row.get("import_status") or "") for row in records)
    flags = Counter(
        str(flag)
        for row in records
        for flag in (row.get("rotted_context_flags") or [])
    )
    return {
        "actions": dict(sorted(actions.items())),
        "statuses": dict(sorted(statuses.items())),
        "flags": dict(sorted(flags.items())),
        "hold_paths": sorted(str(row.get("manifest_path") or "") for row in records if row.get("recommended_action") == "hold"),
        "review_paths_sample": _sample(sorted(str(row.get("manifest_path") or "") for row in records if row.get("recommended_action") == "review")),
        "archive_seed_paths_sample": _sample(sorted(str(row.get("manifest_path") or "") for row in records if row.get("recommended_action") == "archive_seed")),
    }


def _check_policy(
    rows: dict[str, list[dict[str, Any]]],
    *,
    allow_hold_count: int,
    allow_review_count: int,
    allow_archive_seed_count: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    counts = _policy_counts(rows)
    actions = counts["actions"]
    issues: list[dict[str, Any]] = []
    policy_limits = {
        "hold": allow_hold_count,
        "review": allow_review_count,
        "archive_seed": allow_archive_seed_count,
    }
    for action, allowed in policy_limits.items():
        actual = int(actions.get(action, 0))
        if actual > allowed:
            issues.append({
                "severity": "error",
                "code": "recommended_action_exceeds_allowance",
                "recommended_action": action,
                "actual": actual,
                "allowed": allowed,
                "message": "Pass an explicit allowance only after curator review.",
            })
    skipped_not_held = sorted(
        str(row.get("manifest_path") or "")
        for row in rows["manifest_import_records"]
        if row.get("import_status") == "skipped" and row.get("recommended_action") != "hold"
    )
    if skipped_not_held:
        issues.append({
            "severity": "error",
            "code": "skipped_manifest_not_held",
            "count": len(skipped_not_held),
            "sample": _sample(skipped_not_held),
        })
    return counts, issues


def build_migration_gate_report(
    *,
    row_dir: Path = DEFAULT_ROW_DIR,
    output: Path | None = DEFAULT_OUT,
    allow_hold_count: int = 0,
    allow_review_count: int = 0,
    allow_archive_seed_count: int = 0,
) -> dict[str, Any]:
    plan, rows = _load_rows(row_dir)
    issues: list[dict[str, Any]] = []
    issues.extend(_check_counts(plan, rows))
    issues.extend(_check_identity(rows))
    policy, policy_issues = _check_policy(
        rows,
        allow_hold_count=allow_hold_count,
        allow_review_count=allow_review_count,
        allow_archive_seed_count=allow_archive_seed_count,
    )
    issues.extend(policy_issues)
    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    counts = {name: len(loaded) for name, loaded in sorted(rows.items())}
    mapped_count = int(policy["statuses"].get("mapped", 0))
    report = {
        "ok": error_count == 0,
        "gate_status": "ready_for_load" if error_count == 0 else "blocked",
        "generated_at": _utc_now(),
        "row_dir": str(row_dir),
        "counts": counts,
        "policy_allowances": {
            "hold": allow_hold_count,
            "review": allow_review_count,
            "archive_seed": allow_archive_seed_count,
        },
        "policy": policy,
        "integrity": {
            "mapped_records_equal_components": mapped_count == counts.get("components", 0),
            "database_ready_candidate_count": counts.get("components", 0),
            "context_object_binding_count": counts.get("component_context_objects", 0),
        },
        "issue_summary": {
            "errors": error_count,
            "warnings": warning_count,
            "issues": len(issues),
        },
        "issues": issues,
        "load_sql": str(row_dir / "load-catalog-manifests.sql"),
        "safety_notes": [
            "This gate is side-effect free and does not connect to Postgres.",
            "Default policy fails closed for hold, review, and archive_seed recommendations.",
            "Catalog files remain seed/export artifacts and are not moved or deleted.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    sample = REPO / "catalog" / "rubrics" / "baltor-business-object-governance-quality.yaml"
    processor_sample = REPO / "catalog" / "processors" / "standardization" / "tabular-schema-canonicalizer.yaml"
    mask_processor_sample = REPO / "catalog" / "processors" / "redact" / "pii-text.yaml"
    if not sample.exists():
        raise FileNotFoundError(sample)
    if not processor_sample.exists():
        raise FileNotFoundError(processor_sample)
    if not mask_processor_sample.exists():
        raise FileNotFoundError(mask_processor_sample)
    with tempfile.TemporaryDirectory(prefix="ohh-manifest-gate-") as tmp:
        row_dir = Path(tmp) / "bridge"
        build_bridge_plan(paths=[sample, processor_sample, mask_processor_sample], output_dir=row_dir)
        report = build_migration_gate_report(row_dir=row_dir, output=Path(tmp) / "gate.json")
        assert report["ok"] is True
        assert report["gate_status"] == "ready_for_load"
        assert report["integrity"]["mapped_records_equal_components"] is True
        assert report["counts"]["context_mask_contracts"] == 1
        assert report["counts"]["context_transformer_contracts"] == 2
    print(json.dumps({"ok": True, "self_test": "catalog_manifest_migration_gate"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Gate catalog manifest database row sets before Postgres load.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--row-dir", type=Path, default=DEFAULT_ROW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-hold-count", type=int, default=0)
    parser.add_argument("--allow-review-count", type=int, default=0)
    parser.add_argument("--allow-archive-seed-count", type=int, default=0)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    report = build_migration_gate_report(
        row_dir=args.row_dir,
        output=args.output,
        allow_hold_count=args.allow_hold_count,
        allow_review_count=args.allow_review_count,
        allow_archive_seed_count=args.allow_archive_seed_count,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
