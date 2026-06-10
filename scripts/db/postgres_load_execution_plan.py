#!/usr/bin/env python3
"""Emit a side-effect-free Postgres load execution and audit plan."""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._config import (
    DEFAULT_DATABASE_URL_ENV,
    DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
    DEFAULT_POSTGRES_COMPOSE_FILE,
    DEFAULT_POSTGRES_COUNT_SQL,
    DEFAULT_POSTGRES_SCHEMA_FILE,
    MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER,
    START_LOCAL_PGVECTOR_STEP,
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _bulk_manifest(load_plan: dict[str, Any]) -> dict[str, Any]:
    bulk = load_plan.get("bulk_manifest")
    if not isinstance(bulk, dict):
        raise ValueError("load plan missing bulk_manifest")
    if not bulk.get("load_sql"):
        raise ValueError("load plan bulk_manifest missing load_sql")
    return bulk


def _catalog_manifest_bulk(load_plan: dict[str, Any], load_plan_manifest: str | Path) -> dict[str, Any] | None:
    files = load_plan.get("files")
    counts = load_plan.get("counts")
    if not isinstance(files, dict) or not isinstance(counts, dict) or not files.get("load_sql"):
        return None
    if "manifest_import_records" not in counts:
        return None
    return {
        "ok": bool(load_plan.get("ok")),
        "load_sql": files["load_sql"],
        "load_command": f"psql \"$DATABASE_URL\" -f {files['load_sql']}",
        "counts": {str(key): int(value) for key, value in counts.items() if isinstance(value, int)},
        "load_plan_kind": "catalog_manifest_bridge",
        "load_plan_manifest": str(load_plan_manifest),
    }


def _load_source(load_plan: dict[str, Any], load_plan_manifest: str | Path) -> tuple[str, dict[str, Any]]:
    catalog_bulk = _catalog_manifest_bulk(load_plan, load_plan_manifest)
    if catalog_bulk is not None:
        return "catalog_manifest_bridge", catalog_bulk
    return "bulk_manifest", _bulk_manifest(load_plan)


def _default_gate_report_path(load_plan_manifest: str | Path) -> Path:
    return Path(load_plan_manifest).parent / "migration-gate-report.json"


def _migration_gate_report(
    *,
    load_source_kind: str,
    load_plan_manifest: str | Path,
    migration_gate_report: str | Path | None,
) -> dict[str, Any]:
    if load_source_kind != "catalog_manifest_bridge":
        return {
            "required": False,
            "path": "",
            "present": False,
            "ok": None,
            "gate_status": "not_required",
            "issue_summary": {},
            "policy_allowances": {},
        }
    gate_path = Path(migration_gate_report) if migration_gate_report else _default_gate_report_path(load_plan_manifest)
    if not gate_path.exists():
        return {
            "required": True,
            "path": str(gate_path),
            "present": False,
            "ok": False,
            "gate_status": "missing",
            "issue_summary": {"errors": 1, "warnings": 0, "issues": 1},
            "policy_allowances": {},
        }
    gate = _read_json(gate_path)
    return {
        "required": True,
        "path": str(gate_path),
        "present": True,
        "ok": bool(gate.get("ok")),
        "gate_status": gate.get("gate_status", ""),
        "issue_summary": gate.get("issue_summary") if isinstance(gate.get("issue_summary"), dict) else {},
        "policy_allowances": gate.get("policy_allowances") if isinstance(gate.get("policy_allowances"), dict) else {},
    }


def _commands(
    *,
    load_source_kind: str,
    migration_gate: dict[str, Any],
    load_ready: bool,
    target: str,
    database_url_env: str,
    compose_file: str,
    schema_file: str,
    load_sql: str,
    count_sql: str,
    committed_counts_output: str,
    load_audit_output: str,
    load_plan_manifest: str,
    execution_summary: str,
    run_id: str,
) -> list[dict[str, str]]:
    commands: list[dict[str, str]] = []
    if target == "local_docker":
        commands.extend([
            {
                "step": START_LOCAL_PGVECTOR_STEP,
                "command": f"docker compose -f {compose_file} up -d",
            },
            {
                "step": "set_database_url",
                "command": f'export {database_url_env}="{DEFAULT_LOCAL_POSTGRES_DATABASE_URL}"',
            },
        ])
    else:
        commands.append({
            "step": "set_database_url",
            "command": f'export {database_url_env}="{MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER}"',
        })
    if load_source_kind == "catalog_manifest_bridge":
        allowances = migration_gate.get("policy_allowances") if isinstance(migration_gate.get("policy_allowances"), dict) else {}
        gate_path = migration_gate.get("path") or _default_gate_report_path(load_plan_manifest)
        row_dir = str(Path(load_plan_manifest).parent)
        commands.append({
            "step": "verify_manifest_migration_gate",
            "command": (
                "python3 scripts/db/catalog_manifest_migration_gate.py "
                f"--row-dir {row_dir} "
                f"--output {gate_path} "
                f"--allow-hold-count {int(allowances.get('hold', 0) or 0)} "
                f"--allow-review-count {int(allowances.get('review', 0) or 0)} "
                f"--allow-archive-seed-count {int(allowances.get('archive_seed', 0) or 0)}"
            ),
        })
    if not load_ready:
        commands.append({
            "step": "load_blocked_until_ready",
            "command": "Resolve readiness failures before applying schema or load SQL.",
        })
        return commands
    commands.extend([
        {
            "step": "initialize_schema",
            "command": f'psql "${database_url_env}" -f {schema_file}',
        },
        {
            "step": "apply_bulk_load",
            "command": f'psql "${database_url_env}" -f {load_sql}',
        },
    ])
    if load_source_kind == "catalog_manifest_bridge":
        commands.append({
            "step": "probe_catalog_operational_views",
            "command": (
                "python3 scripts/db/catalog_operational_view_probe.py "
                f'--database-url "${database_url_env}" '
                "--require-database "
                "--require-views"
            ),
        })
    commands.extend([
        {
            "step": "write_committed_counts_json",
            "command": (
                f'psql "${database_url_env}" -f {count_sql} '
                f"--csv | python3 scripts/db/psql_csv_to_count_json.py --output {committed_counts_output}"
            ),
        },
        {
            "step": "audit_staged_vs_committed",
            "command": (
                "python3 -m scripts.db.staged_vs_committed_load_audit "
                f"--load-plan-manifest {load_plan_manifest} "
                f"--committed-counts {committed_counts_output} "
                f"--execution-summary {execution_summary} "
                f"--output {load_audit_output} "
                f"--run-id {run_id}"
            ),
        },
    ])
    if load_source_kind == "catalog_manifest_bridge":
        row_export_dir = str(Path(load_plan_manifest).parent.parent / "catalog-db-export-rows")
        commands.append({
            "step": "plan_database_row_export_with_integrity_gate",
            "command": (
                "python3 scripts/db/catalog_db_export_plan.py "
                f"--row-dir {row_export_dir} "
                f"--sql-output {row_export_dir}/export-catalog-db-rows.sql "
                f"--output {row_export_dir}/catalog-db-export-plan.json "
                f"--integrity-report {row_export_dir}/catalog-row-integrity-report.json"
            ),
        })
    return commands


def build_postgres_load_execution_plan(
    *,
    load_plan_manifest: str | Path,
    execution_summary: str | Path = "",
    target: str = "local_docker",
    database_url_env: str = DEFAULT_DATABASE_URL_ENV,
    compose_file: str = DEFAULT_POSTGRES_COMPOSE_FILE,
    schema_file: str = DEFAULT_POSTGRES_SCHEMA_FILE,
    count_sql: str = DEFAULT_POSTGRES_COUNT_SQL,
    committed_counts_output: str = "dist/source-surface-scan-partitions/seed/committed-counts.json",
    load_audit_output: str = "dist/source-surface-scan-partitions/seed/load-audit-committed.json",
    migration_gate_report: str | Path | None = None,
    output: str | Path | None = None,
    run_id: str = "postgres-load-execution",
) -> dict[str, Any]:
    if target not in {"local_docker", "render", "managed_postgres"}:
        raise ValueError("target must be one of: local_docker, render, managed_postgres")
    load_plan = _read_json(load_plan_manifest)
    load_source_kind, bulk = _load_source(load_plan, load_plan_manifest)
    migration_gate = _migration_gate_report(
        load_source_kind=load_source_kind,
        load_plan_manifest=load_plan_manifest,
        migration_gate_report=migration_gate_report,
    )
    preflight = load_plan.get("preflight_report") if isinstance(load_plan.get("preflight_report"), dict) else {}
    load_sql = str(bulk["load_sql"])
    staged_counts = bulk.get("counts") if isinstance(bulk.get("counts"), dict) else {}
    preflight_ok = True if load_source_kind == "catalog_manifest_bridge" else bool(preflight.get("ok"))
    bulk_manifest_ok = bool(bulk.get("ok"))
    gate_ok = True if migration_gate["required"] is False else bool(migration_gate.get("ok"))
    load_ready = preflight_ok and bulk_manifest_ok and gate_ok
    plan = {
        "run_id": run_id,
        "generated_at": _utc_now(),
        "target": target,
        "load_source_kind": load_source_kind,
        "database_url_env": database_url_env,
        "load_plan_manifest": str(load_plan_manifest),
        "migration_gate_report": migration_gate["path"],
        "execution_summary": str(execution_summary) if execution_summary else "",
        "prerequisites": [
            "Postgres 16 compatible database",
            "pgvector extension available",
            "psql client",
            "DATABASE_URL scoped to the intended database before applying load_sql",
        ] + (["Docker with compose plugin"] if target == "local_docker" else []),
        "files": {
            "compose_file": compose_file if target == "local_docker" else "",
            "schema_file": schema_file,
            "load_sql": load_sql,
            "count_sql": count_sql,
            "committed_counts_output": committed_counts_output,
            "load_audit_output": load_audit_output,
        },
        "staged_counts": staged_counts,
        "readiness": {
            "load_ready": load_ready,
            "preflight_ok": preflight_ok,
            "preflight_issue_count": int(preflight.get("issue_count", 0) or 0),
            "bulk_manifest_ok": bulk_manifest_ok,
            "migration_gate_required": bool(migration_gate["required"]),
            "migration_gate_present": bool(migration_gate["present"]),
            "migration_gate_ok": gate_ok,
            "migration_gate_status": migration_gate["gate_status"],
            "migration_gate_issue_summary": migration_gate["issue_summary"],
            "expected_staged_total": sum(value for value in staged_counts.values() if isinstance(value, int)),
        },
        "commands": _commands(
            load_source_kind=load_source_kind,
            migration_gate=migration_gate,
            load_ready=load_ready,
            target=target,
            database_url_env=database_url_env,
            compose_file=compose_file,
            schema_file=schema_file,
            load_sql=load_sql,
            count_sql=count_sql,
            committed_counts_output=committed_counts_output,
            load_audit_output=load_audit_output,
            load_plan_manifest=str(load_plan_manifest),
            execution_summary=str(execution_summary) if execution_summary else "",
            run_id=run_id,
        ),
        "safety_notes": [
            "This planner is side-effect free; it does not start Docker, run psql, or mutate a database.",
            "Run commands only against an intended local or managed Postgres target.",
            "Catalog manifest bridge loads require a passing migration gate before applying load_sql.",
            "Catalog manifest bridge loads should run the read-only catalog operational view probe after applying load_sql.",
            "After a catalog bridge load, generate the database row export plan and run its integrity validation before row-backed consumers use exported rows.",
            "The final audit should be verified or mismatch; staged_only means committed counts were not supplied.",
        ],
    }
    if output:
        _write_json(output, plan)
    return plan


def _self_test() -> int:
    load_plan = Path("dist/source-surface-scan-partitions/seed/load-plan/load-plan-manifest.json")
    if not load_plan.exists():
        raise FileNotFoundError("dist/source-surface-scan-partitions/seed/load-plan/load-plan-manifest.json is required")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "plan.json"
        plan = build_postgres_load_execution_plan(load_plan_manifest=load_plan, output=out)
        assert out.exists()
        assert plan["readiness"]["preflight_ok"] is True
        assert plan["readiness"]["load_ready"] is True
        assert any(command["step"] == "apply_bulk_load" for command in plan["commands"])
        assert any(command["step"] == "audit_staged_vs_committed" for command in plan["commands"])
        catalog_plan = Path("dist/catalog-manifest-bridge/manifest-import-plan.json")
        catalog_gate = Path("dist/catalog-manifest-bridge/migration-gate-report.json")
        if catalog_plan.exists() and catalog_gate.exists():
            catalog = build_postgres_load_execution_plan(
                load_plan_manifest=catalog_plan,
                migration_gate_report=catalog_gate,
            )
            assert catalog["load_source_kind"] == "catalog_manifest_bridge"
            assert catalog["readiness"]["migration_gate_required"] is True
            assert catalog["readiness"]["migration_gate_ok"] is True
            assert catalog["readiness"]["load_ready"] is True
            assert any(command["step"] == "verify_manifest_migration_gate" for command in catalog["commands"])
            assert any(command["step"] == "probe_catalog_operational_views" for command in catalog["commands"])
    print(json.dumps({"ok": True, "command_count": len(plan["commands"])}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a Postgres load execution and audit plan.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--load-plan-manifest")
    parser.add_argument("--execution-summary", default="")
    parser.add_argument("--target", default="local_docker", choices=["local_docker", "render", "managed_postgres"])
    parser.add_argument("--database-url-env", default=DEFAULT_DATABASE_URL_ENV)
    parser.add_argument("--compose-file", default=DEFAULT_POSTGRES_COMPOSE_FILE)
    parser.add_argument("--schema-file", default=DEFAULT_POSTGRES_SCHEMA_FILE)
    parser.add_argument("--count-sql", default=DEFAULT_POSTGRES_COUNT_SQL)
    parser.add_argument("--committed-counts-output", default="dist/source-surface-scan-partitions/seed/committed-counts.json")
    parser.add_argument("--load-audit-output", default="dist/source-surface-scan-partitions/seed/load-audit-committed.json")
    parser.add_argument("--migration-gate-report")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="postgres-load-execution")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.load_plan_manifest:
        parser.error("--load-plan-manifest is required unless --self-test is used")
    result = build_postgres_load_execution_plan(
        load_plan_manifest=args.load_plan_manifest,
        execution_summary=args.execution_summary,
        target=args.target,
        database_url_env=args.database_url_env,
        compose_file=args.compose_file,
        schema_file=args.schema_file,
        count_sql=args.count_sql,
        committed_counts_output=args.committed_counts_output,
        load_audit_output=args.load_audit_output,
        migration_gate_report=args.migration_gate_report,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
