#!/usr/bin/env python3
"""Summarize catalog database-row promotion readiness.

This report answers one operational question: are the current database-exported
catalog rows safe to promote as the runtime source of truth while YAML remains
seed/export/review material?

The script is read-only. It consumes existing row reports where available and
does not connect to Postgres or mutate catalog manifests.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.db.catalog_db_export_staleness_gate import build_staleness_gate_report


DEFAULT_BRIDGE_DIR = _resource("dist") / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = _resource("dist") / "catalog-db-export-rows-smoke"
DEFAULT_SMOKE_DIR = _resource("dist") / "catalog-migration-smoke"
DEFAULT_OUTPUT = DEFAULT_SMOKE_DIR / "catalog-database-promotion-readiness.json"


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else None


def _coverage_ok(report: dict[str, Any] | None, key: str) -> bool:
    if not isinstance(report, dict):
        return False
    coverage = report.get(key)
    return isinstance(coverage, dict) and bool(coverage.get("ok"))


def _report_ok(report: dict[str, Any] | None) -> bool:
    return isinstance(report, dict) and bool(report.get("ok"))


def _warning_count(report: dict[str, Any] | None) -> int:
    if not isinstance(report, dict):
        return 0
    severity_counts = report.get("severity_counts")
    if not isinstance(severity_counts, dict):
        return 0
    return int(severity_counts.get("warning") or 0)


def _has_command_step(report: dict[str, Any] | None, step_name: str) -> bool:
    if not isinstance(report, dict):
        return False
    commands = report.get("commands")
    if not isinstance(commands, list):
        return False
    return any(isinstance(command, dict) and command.get("step") == step_name for command in commands)


def _load_execution_plan_ready(report: dict[str, Any] | None) -> bool:
    if not isinstance(report, dict):
        return False
    readiness = report.get("readiness")
    return isinstance(readiness, dict) and bool(readiness.get("load_ready"))


def build_promotion_readiness_report(
    *,
    bridge_dir: Path = DEFAULT_BRIDGE_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    smoke_dir: Path = DEFAULT_SMOKE_DIR,
    output: Path | None = DEFAULT_OUTPUT,
    allow_warnings: bool = True,
    advisory: bool = False,
) -> dict[str, Any]:
    manifest_plan_path = bridge_dir / "manifest-import-plan.json"
    load_execution_plan_path = bridge_dir / "postgres-load-execution-plan.json"
    bridge_integrity_path = bridge_dir / "catalog-row-integrity-report.json"
    bridge_schema_coverage_path = bridge_dir / "catalog-row-schema-coverage.json"
    export_plan_path = db_row_dir / "catalog-db-export-plan.json"
    db_integrity_path = db_row_dir / "catalog-row-integrity-report.json"
    parity_report_path = smoke_dir / "catalog-row-roundtrip-parity.json"
    staleness_output = smoke_dir / "catalog-db-export-staleness-gate.json"

    manifest_plan = read_json(manifest_plan_path)
    load_execution_plan = read_json(load_execution_plan_path)
    bridge_integrity = read_json(bridge_integrity_path)
    bridge_schema_coverage = read_json(bridge_schema_coverage_path)
    export_plan = read_json(export_plan_path)
    db_integrity = read_json(db_integrity_path)
    staleness = build_staleness_gate_report(
        seed_row_dir=bridge_dir,
        db_row_dir=db_row_dir,
        parity_report_path=parity_report_path,
        output=staleness_output,
        advisory=True,
    )

    bridge_integrity_ready = _report_ok(bridge_integrity) and (allow_warnings or _warning_count(bridge_integrity) == 0)
    db_integrity_ready = _report_ok(db_integrity) and (allow_warnings or _warning_count(db_integrity) == 0)
    checks = {
        "manifest_bridge_generated": _report_ok(manifest_plan),
        "seed_load_sql_coverage_ready": _coverage_ok(manifest_plan, "load_sql_coverage"),
        "load_execution_plan_ready": _load_execution_plan_ready(load_execution_plan),
        "post_load_catalog_view_probe_planned": _has_command_step(load_execution_plan, "probe_catalog_operational_views"),
        "seed_row_integrity_ready": bridge_integrity_ready,
        "seed_row_schema_coverage_ready": _report_ok(bridge_schema_coverage),
        "database_export_sql_coverage_ready": _coverage_ok(export_plan, "export_sql_coverage"),
        "database_export_row_integrity_ready": db_integrity_ready,
        "database_export_snapshot_fresh": bool(staleness.get("would_pass")),
    }
    missing_reports = [
        str(path)
        for path, report in [
            (manifest_plan_path, manifest_plan),
            (load_execution_plan_path, load_execution_plan),
            (bridge_integrity_path, bridge_integrity),
            (bridge_schema_coverage_path, bridge_schema_coverage),
            (export_plan_path, export_plan),
            (db_integrity_path, db_integrity),
            (parity_report_path, read_json(parity_report_path)),
        ]
        if report is None
    ]
    ready = all(checks.values()) and not missing_reports
    blocking_checks = [name for name, ok in checks.items() if not ok]

    report = {
        "ok": True if advisory else ready,
        "would_pass": ready,
        "status": "ready" if ready else "not_ready",
        "generated_at": utc_now(),
        "advisory": advisory,
        "allow_warnings": allow_warnings,
        "bridge_dir": str(bridge_dir),
        "db_row_dir": str(db_row_dir),
        "smoke_dir": str(smoke_dir),
        "checks": checks,
        "blocking_checks": blocking_checks,
        "missing_reports": missing_reports,
        "report_paths": {
            "manifest_plan": str(manifest_plan_path),
            "load_execution_plan": str(load_execution_plan_path),
            "bridge_integrity": str(bridge_integrity_path),
            "bridge_schema_coverage": str(bridge_schema_coverage_path),
            "database_export_plan": str(export_plan_path),
            "database_export_integrity": str(db_integrity_path),
            "roundtrip_parity": str(parity_report_path),
            "staleness_gate": str(staleness_output),
        },
        "row_counts": {
            "seed_components": (manifest_plan or {}).get("counts", {}).get("components") if isinstance((manifest_plan or {}).get("counts"), dict) else None,
            "seed_context_objects": (manifest_plan or {}).get("counts", {}).get("context_objects") if isinstance((manifest_plan or {}).get("counts"), dict) else None,
            "seed_context_mask_contracts": (manifest_plan or {}).get("counts", {}).get("context_mask_contracts") if isinstance((manifest_plan or {}).get("counts"), dict) else None,
            "seed_context_transformer_contracts": (manifest_plan or {}).get("counts", {}).get("context_transformer_contracts") if isinstance((manifest_plan or {}).get("counts"), dict) else None,
            "database_components": (db_integrity or {}).get("counts", {}).get("components") if isinstance((db_integrity or {}).get("counts"), dict) else None,
            "database_context_objects": (db_integrity or {}).get("counts", {}).get("context_objects") if isinstance((db_integrity or {}).get("counts"), dict) else None,
        },
        "staleness": {
            "status": staleness.get("status"),
            "would_pass": staleness.get("would_pass"),
            "mismatched_row_families": staleness.get("mismatched_row_families"),
            "severity_counts": staleness.get("severity_counts"),
        },
        "recommended_next_step": (
            "Promote database-exported rows as the operational catalog source; keep YAML as seed/export/review artifacts."
            if ready
            else (
                "Refresh database-exported rows from a local/staging Postgres load, rerun round-trip parity, "
                "then run this readiness report without --advisory."
            )
        ),
        "safety_notes": [
            "This report is read-only and does not connect to Postgres.",
            "It does not read or mutate catalog YAML files.",
            "Use --advisory inside dry-run smoke; omit --advisory for promotion or release gating.",
        ],
    }
    if output is not None:
        write_json(output, report)
    return report


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ohh-catalog-promotion-readiness-") as tmp:
        root = Path(tmp)
        bridge = root / "bridge"
        db = root / "db"
        smoke = root / "smoke"
        bridge.mkdir()
        db.mkdir()
        smoke.mkdir()
        (bridge / "manifest-import-plan.json").write_text(
            json.dumps({
                "ok": True,
                "counts": {"components": 1, "context_objects": 1, "context_mask_contracts": 0, "context_transformer_contracts": 0},
                "load_sql_coverage": {"ok": True},
            }),
            encoding="utf-8",
        )
        (bridge / "postgres-load-execution-plan.json").write_text(
            json.dumps({
                "readiness": {"load_ready": True},
                "commands": [
                    {"step": "probe_catalog_operational_views"},
                ],
            }),
            encoding="utf-8",
        )
        (bridge / "catalog-row-integrity-report.json").write_text(json.dumps({"ok": True, "severity_counts": {}}), encoding="utf-8")
        (bridge / "catalog-row-schema-coverage.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
        (db / "catalog-db-export-plan.json").write_text(json.dumps({"ok": True, "export_sql_coverage": {"ok": True}}), encoding="utf-8")
        (db / "catalog-row-integrity-report.json").write_text(json.dumps({"ok": True, "counts": {"components": 1, "context_objects": 1}, "severity_counts": {}}), encoding="utf-8")
        (smoke / "catalog-row-roundtrip-parity.json").write_text(json.dumps({"ok": True, "severity_counts": {}, "row_families": []}), encoding="utf-8")
        report = build_promotion_readiness_report(
            bridge_dir=bridge,
            db_row_dir=db,
            smoke_dir=smoke,
            output=None,
        )
        if not report["ok"] or not report["would_pass"] or report["blocking_checks"]:
            print(json.dumps(report, indent=2, sort_keys=True))
            return 1
    print(json.dumps({"ok": True, "self_test": "catalog_database_promotion_readiness"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize catalog database-row promotion readiness.")
    parser.add_argument("--bridge-dir", type=Path, default=DEFAULT_BRIDGE_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--smoke-dir", type=Path, default=DEFAULT_SMOKE_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fail-on-warning", action="store_true")
    parser.add_argument("--advisory", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_promotion_readiness_report(
        bridge_dir=args.bridge_dir,
        db_row_dir=args.db_row_dir,
        smoke_dir=args.smoke_dir,
        output=args.output,
        allow_warnings=not args.fail_on_warning,
        advisory=args.advisory,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
