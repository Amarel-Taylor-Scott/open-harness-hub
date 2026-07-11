#!/usr/bin/env python3
"""Emit a side-effect-free local Postgres smoke plan for object governance."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
import sys
from typing import Any

ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts._config import (
    DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
    DEFAULT_POSTGRES_COMPOSE_FILE,
    DEFAULT_POSTGRES_SCHEMA_FILE,
    LOCAL_DOCKER_PGVECTOR_BACKEND,
    OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_PLAN_FILENAME,
    OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID,
    OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_SELF_TEST_RUN_ID,
    OBJECT_GOVERNANCE_OPERATIONAL_VIEWS,
    OBJECT_GOVERNANCE_PACKAGE_TABLES,
    OBJECT_GOVERNANCE_REQUIRED_FAMILIES,
    OBJECT_GOVERNANCE_SEED_LOAD_SQL,
    START_LOCAL_PGVECTOR_STEP,
    WAIT_FOR_PGVECTOR_HEALTH_STEP,
)
from scripts.db.object_governance_registry import (
    concrete_seed_coverage,
    package_seed_coverage,
    package_seed_coverage_errors,
)
from scripts.db.object_governance_view_probe import probe_object_governance_views


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _require_path(path: str | Path, label: str) -> str:
    candidate = Path(path)
    if not candidate.exists():
        raise FileNotFoundError(f"{label} not found: {candidate}")
    return str(candidate)


def _coverage_summary(coverage: dict[str, Any], missing_key: str) -> dict[str, Any]:
    missing_by_table = {
        table: table_report.get(missing_key) or []
        for table, table_report in sorted(coverage.items())
        if table_report.get(missing_key) or table_report.get("error")
    }
    return {
        "table_count": len(coverage),
        "row_count": sum(int(table_report.get("row_count", 0) or 0) for table_report in coverage.values()),
        "missing_by_table": missing_by_table,
        "complete": not missing_by_table,
    }


def build_object_governance_local_postgres_smoke_plan(
    *,
    output_dir: str | Path | None = None,
    run_id: str = OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID,
    compose_file: str = DEFAULT_POSTGRES_COMPOSE_FILE,
    schema_file: str = DEFAULT_POSTGRES_SCHEMA_FILE,
    seed_load_sql: str = OBJECT_GOVERNANCE_SEED_LOAD_SQL,
    database_url: str = DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
    require_existing_paths: bool = True,
) -> dict[str, Any]:
    """Build an operator-reviewed local Postgres smoke plan without mutating anything."""
    if require_existing_paths:
        _require_path(compose_file, "compose_file")
        _require_path(schema_file, "schema_file")
        _require_path(seed_load_sql, "seed_load_sql")

    family_coverage = package_seed_coverage()
    concrete_coverage = concrete_seed_coverage()
    coverage_errors = package_seed_coverage_errors()
    schema_probe = probe_object_governance_views(schema_sql=schema_file)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-object-governance-postgres-smoke-"))
    plan_output = out / OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_PLAN_FILENAME
    live_probe_output = out / "object-governance-view-probe.json"
    family_summary = _coverage_summary(family_coverage, "missing_required_families")
    concrete_summary = _coverage_summary(concrete_coverage, "missing_object_types")
    seed_coverage_ok = not coverage_errors
    schema_ready = bool(schema_probe.get("schema_ready"))
    safe_to_apply_locally = seed_coverage_ok and schema_ready
    psql_target = f'"{database_url}"'

    commands = [
        {
            "step": START_LOCAL_PGVECTOR_STEP,
            "command": f"docker compose -f {compose_file} up -d",
        },
        {
            "step": WAIT_FOR_PGVECTOR_HEALTH_STEP,
            "command": "docker exec openhubforai-postgres pg_isready -U openhubforai -d openhubforai",
        },
        {
            "step": "initialize_schema",
            "command": f"psql {psql_target} -f {schema_file}",
        },
        {
            "step": "apply_object_governance_seed_rows",
            "command": f"psql {psql_target} -f {seed_load_sql}",
        },
        {
            "step": "check_object_governance_seed_coverage",
            "command": "python3 scripts/db/object_governance_registry.py --check-seed-coverage",
        },
        {
            "step": "probe_object_governance_views",
            "command": (
                "python3 scripts/db/object_governance_view_probe.py "
                f"--database-url {psql_target} "
                "--require-database "
                "--require-views"
            ),
        },
        {
            "step": "write_object_governance_view_probe_json",
            "command": (
                "python3 scripts/db/object_governance_view_probe.py "
                f"--database-url {psql_target} "
                "--require-database "
                "--require-views "
                f"> {live_probe_output}"
            ),
        },
    ]
    result = {
        "ok": safe_to_apply_locally,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "target": f"{LOCAL_DOCKER_PGVECTOR_BACKEND}_object_governance_rows_and_views",
        "readiness": {
            "safe_to_apply_locally": safe_to_apply_locally,
            "seed_coverage_ok": seed_coverage_ok,
            "schema_ready": schema_ready,
            "family_seed": family_summary,
            "concrete_seed": concrete_summary,
            "expected_family_count": len(OBJECT_GOVERNANCE_REQUIRED_FAMILIES),
            "expected_table_count": len(OBJECT_GOVERNANCE_PACKAGE_TABLES),
            "expected_view_count": len(OBJECT_GOVERNANCE_OPERATIONAL_VIEWS),
            "coverage_errors": coverage_errors,
        },
        "files": {
            "compose_file": compose_file,
            "schema_file": schema_file,
            "seed_load_sql": seed_load_sql,
            "live_view_probe": str(live_probe_output),
            "summary": str(plan_output),
        },
        "views": list(OBJECT_GOVERNANCE_OPERATIONAL_VIEWS),
        "commands": commands,
        "safety_notes": [
            "This planner is side-effect free; it does not start Docker, run psql, or mutate Postgres.",
            "The emitted commands target the local development Postgres/pgvector container only.",
            "Review the database URL before running emitted commands; never point this plan at managed production databases.",
            "The governance JSONL files remain seed/export/review artifacts; loaded Postgres rows are the runtime source of truth.",
        ],
    }
    _write_json(plan_output, result)
    return result


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = build_object_governance_local_postgres_smoke_plan(
            output_dir=tmp,
            run_id=OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_SELF_TEST_RUN_ID,
        )
        assert result["ok"] is True
        assert result["readiness"]["seed_coverage_ok"] is True
        assert result["readiness"]["schema_ready"] is True
        assert result["readiness"]["family_seed"]["complete"] is True
        assert result["readiness"]["concrete_seed"]["complete"] is True
        assert len(result["commands"]) == 7
        assert any(row["step"] == "apply_object_governance_seed_rows" for row in result["commands"])
        assert Path(result["files"]["summary"]).exists()
    print(json.dumps({"ok": True, "command_count": len(result["commands"])}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default=OBJECT_GOVERNANCE_LOCAL_POSTGRES_SMOKE_RUN_ID)
    parser.add_argument("--compose-file", default=DEFAULT_POSTGRES_COMPOSE_FILE)
    parser.add_argument("--schema-file", default=DEFAULT_POSTGRES_SCHEMA_FILE)
    parser.add_argument("--seed-load-sql", default=OBJECT_GOVERNANCE_SEED_LOAD_SQL)
    parser.add_argument("--database-url", default=DEFAULT_LOCAL_POSTGRES_DATABASE_URL)
    parser.add_argument("--allow-missing-paths", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = build_object_governance_local_postgres_smoke_plan(
        output_dir=args.output_dir,
        run_id=args.run_id,
        compose_file=args.compose_file,
        schema_file=args.schema_file,
        seed_load_sql=args.seed_load_sql,
        database_url=args.database_url,
        require_existing_paths=not args.allow_missing_paths,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
