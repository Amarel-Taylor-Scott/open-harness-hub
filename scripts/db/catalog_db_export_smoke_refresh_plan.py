#!/usr/bin/env python3
"""Plan a refresh of database-exported smoke rows.

The migration smoke can validate an existing database-exported row snapshot, but
it intentionally does not connect to Postgres. When row parity shows the smoke
snapshot is stale, this planner emits the concrete command sequence required to
reload bridge rows into Postgres, export fresh row files, and verify parity.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import DEFAULT_DATABASE_URL_ENV
from scripts.db.catalog_row_integrity import ROW_FILES
from scripts.db.catalog_row_roundtrip_parity import compare_row_dirs, row_dir_fingerprint


DEFAULT_BRIDGE_DIR = REPO / "dist" / "catalog-manifest-bridge"
DEFAULT_DB_ROW_DIR = REPO / "dist" / "catalog-db-export-rows-smoke"
DEFAULT_OUTPUT = REPO / "dist" / "catalog-migration-smoke" / "catalog-db-export-smoke-refresh-plan.json"


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


def read_jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def row_counts(row_dir: Path) -> dict[str, int]:
    return {
        row_family: read_jsonl_count(row_dir / filename)
        for row_family, filename in sorted(ROW_FILES.items())
    }


def stale_summary(parity_report: dict[str, Any]) -> dict[str, Any]:
    mismatched = [
        row
        for row in parity_report.get("row_families", [])
        if isinstance(row, dict) and row.get("status") == "mismatched"
    ]
    return {
        "parity_ok": bool(parity_report.get("ok")),
        "severity_counts": parity_report.get("severity_counts") if isinstance(parity_report.get("severity_counts"), dict) else {},
        "mismatched_row_families": [str(row.get("row_family")) for row in mismatched],
        "mismatched_counts": {
            str(row.get("row_family")): {
                "seed_count": row.get("seed_count"),
                "db_count": row.get("db_count"),
                "missing_from_db": row.get("missing_from_db"),
                "extra_in_db": row.get("extra_in_db"),
            }
            for row in mismatched
        },
    }


def refresh_actions(summary: dict[str, Any]) -> list[dict[str, Any]]:
    mismatches = summary.get("mismatched_counts")
    if not isinstance(mismatches, dict):
        return []
    actions: list[dict[str, Any]] = []
    for row_family, counts in sorted(mismatches.items()):
        if not isinstance(counts, dict):
            continue
        seed_count = int(counts.get("seed_count") or 0)
        db_count = int(counts.get("db_count") or 0)
        missing_from_db = int(counts.get("missing_from_db") or 0)
        extra_in_db = int(counts.get("extra_in_db") or 0)
        if missing_from_db:
            action = "reload_seed_rows_then_export_database_rows"
        elif extra_in_db:
            action = "review_database_only_rows_before_promotion"
        elif seed_count != db_count:
            action = "reconcile_row_count_mismatch"
        else:
            action = "reconcile_content_mismatch"
        actions.append({
            "row_family": row_family,
            "seed_count": seed_count,
            "db_count": db_count,
            "missing_from_db": missing_from_db,
            "extra_in_db": extra_in_db,
            "recommended_action": action,
        })
    return actions


def _fingerprint_matches(parity_report: dict[str, Any], *, seed_row_dir: Path, db_row_dir: Path) -> bool:
    seed_fingerprint = parity_report.get("seed_row_fingerprint")
    db_fingerprint = parity_report.get("db_row_fingerprint")
    if not isinstance(seed_fingerprint, dict) or not isinstance(db_fingerprint, dict):
        return False
    return (
        seed_fingerprint.get("sha256") == row_dir_fingerprint(seed_row_dir).get("sha256")
        and db_fingerprint.get("sha256") == row_dir_fingerprint(db_row_dir).get("sha256")
    )


def build_refresh_plan(
    *,
    bridge_dir: Path = DEFAULT_BRIDGE_DIR,
    db_row_dir: Path = DEFAULT_DB_ROW_DIR,
    output: Path = DEFAULT_OUTPUT,
    database_url_env: str = DEFAULT_DATABASE_URL_ENV,
    parity_report_path: Path | None = None,
) -> dict[str, Any]:
    parity_path = parity_report_path or output.parent / "catalog-row-roundtrip-parity.json"
    parity_report = read_json(parity_path)
    parity_source = "existing_report"
    if parity_report is None:
        parity_report = compare_row_dirs(
            seed_row_dir=bridge_dir,
            db_row_dir=db_row_dir,
            output=parity_path,
        )
        parity_source = "generated_report"
    elif not _fingerprint_matches(parity_report, seed_row_dir=bridge_dir, db_row_dir=db_row_dir):
        parity_report = compare_row_dirs(
            seed_row_dir=bridge_dir,
            db_row_dir=db_row_dir,
            output=parity_path,
        )
        parity_source = "regenerated_stale_fingerprint"
    summary = stale_summary(parity_report)
    refresh_required = not summary["parity_ok"]
    load_sql = bridge_dir / "load-catalog-manifests.sql"
    migration_gate = bridge_dir / "migration-gate-report.json"
    export_sql = db_row_dir / "export-catalog-db-rows.sql"
    export_plan = db_row_dir / "catalog-db-export-plan.json"
    db_integrity = db_row_dir / "catalog-row-integrity-report.json"
    db_schema_coverage = db_row_dir / "catalog-row-schema-coverage.json"
    parity_output = output.parent / "catalog-row-roundtrip-parity.json"
    staleness_gate = output.parent / "catalog-db-export-staleness-gate.json"
    promotion_readiness = output.parent / "catalog-database-promotion-readiness.json"
    manifest_export_dir = output.parent / "manifest-export-from-database-rows"
    expected_seed_counts = row_counts(bridge_dir)

    commands = [
        {
            "step": "rebuild_bridge_rows",
            "command": (
                "python3 scripts/db/catalog_manifest_bridge.py "
                f"--output-dir {bridge_dir}"
            ),
        },
        {
            "step": "verify_manifest_migration_gate",
            "command": (
                "python3 scripts/db/catalog_manifest_migration_gate.py "
                f"--row-dir {bridge_dir} "
                f"--output {migration_gate} "
                "--allow-hold-count 4 "
                "--allow-review-count 743 "
                "--allow-archive-seed-count 0"
            ),
        },
        {
            "step": "initialize_schema",
            "command": f'psql "${database_url_env}" -f db/postgres/schema.sql',
        },
        {
            "step": "load_bridge_rows",
            "command": f'psql "${database_url_env}" -f {load_sql}',
        },
        {
            "step": "probe_catalog_operational_views",
            "command": (
                "python3 scripts/db/catalog_operational_view_probe.py "
                f'--database-url "${database_url_env}" '
                "--require-database "
                "--require-views"
            ),
        },
        {
            "step": "plan_database_row_export",
            "command": (
                "python3 scripts/db/catalog_db_export_plan.py "
                f"--row-dir {db_row_dir} "
                f"--sql-output {export_sql} "
                f"--output {export_plan} "
                f"--integrity-report {db_integrity}"
            ),
        },
        {
            "step": "export_database_rows",
            "command": f'psql "${database_url_env}" -f {export_sql}',
        },
        {
            "step": "validate_database_export_row_integrity",
            "command": (
                "python3 scripts/db/catalog_row_integrity.py "
                f"--row-dir {db_row_dir} "
                f"--output {db_integrity}"
            ),
        },
        {
            "step": "validate_database_export_schema_coverage",
            "command": (
                "python3 scripts/db/catalog_row_schema_coverage.py "
                f"--row-dir {db_row_dir} "
                f"--output {db_schema_coverage}"
            ),
        },
        {
            "step": "validate_roundtrip_parity",
            "command": (
                "python3 scripts/db/catalog_row_roundtrip_parity.py "
                f"--seed-row-dir {bridge_dir} "
                f"--db-row-dir {db_row_dir} "
                f"--output {parity_output}"
            ),
        },
        {
            "step": "gate_database_export_snapshot_freshness",
            "command": (
                "python3 scripts/db/catalog_db_export_staleness_gate.py "
                f"--seed-row-dir {bridge_dir} "
                f"--db-row-dir {db_row_dir} "
                f"--parity-report {parity_output} "
                f"--output {staleness_gate}"
            ),
        },
        {
            "step": "verify_database_promotion_readiness",
            "command": (
                "python3 scripts/db/catalog_database_promotion_readiness.py "
                f"--bridge-dir {bridge_dir} "
                f"--db-row-dir {db_row_dir} "
                f"--smoke-dir {output.parent} "
                f"--output {promotion_readiness}"
            ),
        },
        {
            "step": "export_review_manifests_from_database_rows",
            "command": (
                "python3 scripts/db/catalog_manifest_export_plan.py "
                f"--row-dir {db_row_dir} "
                f"--output-dir {manifest_export_dir}"
            ),
        },
    ]
    plan = {
        "ok": True,
        "generated_at": utc_now(),
        "refresh_required": refresh_required,
        "bridge_dir": str(bridge_dir),
        "db_row_dir": str(db_row_dir),
        "database_url_env": database_url_env,
        "parity_report": str(parity_path),
        "parity_source": parity_source,
        "parity_summary": summary,
        "expected_seed_row_counts": expected_seed_counts,
        "refresh_actions": refresh_actions(summary),
        "commands": commands,
        "safety_notes": [
            "This planner does not connect to Postgres and does not mutate catalog files.",
            "Run these commands only against an intended local or staging database.",
            "Repository YAML remains seed/export/review material; refreshed row files are database-export artifacts.",
            "The catalog operational view probe is read-only and should pass before exporting refreshed database rows.",
            "Hard staleness and promotion-readiness commands should pass before row-backed consumers treat database rows as operational truth.",
            "Generated manifest exports must stay outside catalog/ unless a curator intentionally reviews and applies them.",
        ],
    }
    write_json(output, plan)
    return plan


def run_self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="ohh-export-refresh-plan-") as tmp:
        root = Path(tmp)
        bridge = root / "bridge"
        db = root / "db"
        bridge.mkdir()
        db.mkdir()
        for filename in ROW_FILES.values():
            (bridge / filename).write_text("", encoding="utf-8")
            (db / filename).write_text("", encoding="utf-8")
        (bridge / "context_objects.jsonl").write_text(
            json.dumps({"context_object_id": "ctx://example/one"}, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        parity = root / "parity.json"
        parity.write_text(
            json.dumps({
                "ok": False,
                "severity_counts": {"error": 1},
                "row_families": [
                    {
                        "row_family": "context_objects",
                        "status": "mismatched",
                        "seed_count": 2,
                        "db_count": 1,
                        "missing_from_db": 1,
                        "extra_in_db": 0,
                    }
                ],
            }),
            encoding="utf-8",
        )
        report = build_refresh_plan(
            bridge_dir=bridge,
            db_row_dir=db,
            output=root / "refresh.json",
            parity_report_path=parity,
        )
        assert report["ok"]
        assert report["refresh_required"]
        assert any(command["step"] == "probe_catalog_operational_views" for command in report["commands"])
        assert any(command["step"] == "validate_roundtrip_parity" for command in report["commands"])
        assert any(command["step"] == "gate_database_export_snapshot_freshness" for command in report["commands"])
        assert any(command["step"] == "verify_database_promotion_readiness" for command in report["commands"])
        assert any(command["step"] == "export_review_manifests_from_database_rows" for command in report["commands"])
        assert report["refresh_actions"][0]["recommended_action"] == "reload_seed_rows_then_export_database_rows"
    print(json.dumps({"ok": True, "self_test": "catalog_db_export_smoke_refresh_plan"}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plan a refresh of database-exported smoke rows.")
    parser.add_argument("--bridge-dir", type=Path, default=DEFAULT_BRIDGE_DIR)
    parser.add_argument("--db-row-dir", type=Path, default=DEFAULT_DB_ROW_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--database-url-env", default=DEFAULT_DATABASE_URL_ENV)
    parser.add_argument("--parity-report", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return run_self_test()
    report = build_refresh_plan(
        bridge_dir=args.bridge_dir,
        db_row_dir=args.db_row_dir,
        output=args.output,
        database_url_env=args.database_url_env,
        parity_report_path=args.parity_report,
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
