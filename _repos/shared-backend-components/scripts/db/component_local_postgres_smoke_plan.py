#!/usr/bin/env python3
"""Emit a side-effect-free local Postgres smoke plan for component rows and vectors."""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
    DEFAULT_POSTGRES_COMPOSE_FILE,
    DEFAULT_POSTGRES_COUNT_SQL,
    DEFAULT_POSTGRES_SCHEMA_FILE,
    LOCAL_DOCKER_PGVECTOR_COMPONENT_TARGET,
    MODEL_OPS_DAILY_RUNS_DIST_DIR,
    PGVECTOR_LOAD_PLAN_SUBDIR,
    PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
    PGVECTOR_LOAD_PLAN_SUMMARY_FIELD,
    PGVECTOR_LOAD_PLAN_SUMMARY_FLAG,
    START_LOCAL_PGVECTOR_STEP,
    WAIT_FOR_PGVECTOR_HEALTH_STEP,
    dated_nested_artifact_path,
)

SELF_TEST_DATE = "2026-05-26"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _require_path(path: str | Path, label: str) -> str:
    candidate = Path(path)
    if not candidate.exists():
        raise FileNotFoundError(f"{label} not found: {candidate}")
    return str(candidate)


def build_component_local_postgres_smoke_plan(
    *,
    component_run_summary: str | Path,
    load_audit_summary: str | Path,
    pgvector_load_plan_summary: str | Path,
    embedding_execution_plan: str | Path,
    vector_readiness_summary: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = "component-local-postgres-smoke",
    compose_file: str = DEFAULT_POSTGRES_COMPOSE_FILE,
    schema_file: str = DEFAULT_POSTGRES_SCHEMA_FILE,
    count_sql: str = DEFAULT_POSTGRES_COUNT_SQL,
    database_url: str = DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
) -> dict[str, Any]:
    """Build an operator-reviewed local pgvector smoke plan without mutating anything."""
    run_summary = _read_json(component_run_summary)
    load_audit = _read_json(load_audit_summary)
    vector_load = _read_json(pgvector_load_plan_summary)
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-component-postgres-smoke-"))

    bulk = load_audit.get("bulk_manifest") if isinstance(load_audit.get("bulk_manifest"), dict) else {}
    candidate_load_sql = bulk.get("load_sql")
    if not candidate_load_sql:
        raise ValueError("load audit summary does not include bulk_manifest.load_sql")
    vector_load_sql = (vector_load.get("files") or {}).get("load_sql") if isinstance(vector_load.get("files"), dict) else ""
    if not vector_load_sql:
        raise ValueError("pgvector load plan summary does not include files.load_sql")
    load_plan_manifest = load_audit.get("load_plan_manifest")
    if not load_plan_manifest:
        raise ValueError("load audit summary does not include load_plan_manifest")

    _require_path(compose_file, "compose_file")
    _require_path(schema_file, "schema_file")
    _require_path(count_sql, "count_sql")
    _require_path(candidate_load_sql, "candidate_load_sql")
    _require_path(vector_load_sql, "vector_load_sql")
    _require_path(load_plan_manifest, "load_plan_manifest")
    _require_path(embedding_execution_plan, "embedding_execution_plan")
    _require_path(vector_readiness_summary, "vector_readiness_summary")

    committed_counts = out / "committed-counts.json"
    staged_audit = out / "staged-vs-committed-load-audit.json"
    embedding_audit = out / "embedding-committed-load-audit.json"
    plan_output = out / "component-local-postgres-smoke-plan.json"

    row_counts = run_summary.get("row_counts") if isinstance(run_summary.get("row_counts"), dict) else {}
    candidate_rows = int(row_counts.get("normalized_object", 0) or 0)
    unique_total = int((load_audit.get("merge_report") or {}).get("unique_total", 0) or 0)
    load_preflight = load_audit.get("preflight") if isinstance(load_audit.get("preflight"), dict) else {}
    vector_accepted_rows = int(vector_load.get("accepted_rows", 0) or 0)
    vector_rejected_rows = int(vector_load.get("rejected_rows", 0) or 0)
    safe_to_apply = (
        candidate_rows > 0
        and unique_total > 0
        and bool(load_preflight.get("ok"))
        and int(load_preflight.get("issue_count", 0) or 0) == 0
        and vector_accepted_rows > 0
        and vector_rejected_rows == 0
    )

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
            "step": "apply_component_candidate_rows",
            "command": f"psql {psql_target} -f {candidate_load_sql}",
        },
        {
            "step": "apply_component_embedding_vectors",
            "command": f"psql {psql_target} -f {vector_load_sql}",
        },
        {
            "step": "write_committed_counts_json",
            "command": f"psql {psql_target} -f {count_sql} --csv | python3 scripts/db/psql_csv_to_count_json.py --output {committed_counts}",
        },
        {
            "step": "audit_staged_candidate_load",
            "command": (
                "python3 -m scripts.db.staged_vs_committed_load_audit "
                f"--load-plan-manifest {load_plan_manifest} "
                f"--committed-counts {committed_counts} "
                f"--output {staged_audit} "
                f"--run-id {run_id}-staged-load"
            ),
        },
        {
            "step": "audit_embedding_committed_load",
            "command": (
                "python3 -m scripts.db.embedding_committed_load_audit "
                f"--embedding-execution-plan {embedding_execution_plan} "
                f"--vector-readiness-summary {vector_readiness_summary} "
                f"{PGVECTOR_LOAD_PLAN_SUMMARY_FLAG} {pgvector_load_plan_summary} "
                f"--committed-counts {committed_counts} "
                f"--output {embedding_audit} "
                f"--run-id {run_id}-embedding-load"
            ),
        },
    ]
    result = {
        "ok": safe_to_apply,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "target": LOCAL_DOCKER_PGVECTOR_COMPONENT_TARGET,
        "inputs": {
            "component_run_summary": str(component_run_summary),
            "load_audit_summary": str(load_audit_summary),
            PGVECTOR_LOAD_PLAN_SUMMARY_FIELD: str(pgvector_load_plan_summary),
            "embedding_execution_plan": str(embedding_execution_plan),
            "vector_readiness_summary": str(vector_readiness_summary),
        },
        "readiness": {
            "candidate_rows": candidate_rows,
            "unique_staged_rows": unique_total,
            "candidate_preflight_ok": bool(load_preflight.get("ok")),
            "candidate_preflight_issue_count": int(load_preflight.get("issue_count", 0) or 0),
            "vector_accepted_rows": vector_accepted_rows,
            "vector_rejected_rows": vector_rejected_rows,
            "safe_to_apply_locally": safe_to_apply,
        },
        "files": {
            "compose_file": compose_file,
            "schema_file": schema_file,
            "count_sql": count_sql,
            "candidate_load_sql": str(candidate_load_sql),
            "vector_load_sql": str(vector_load_sql),
            "load_plan": str(load_plan_manifest),
            "committed_counts": str(committed_counts),
            "staged_vs_committed_audit": str(staged_audit),
            "embedding_committed_load_audit": str(embedding_audit),
            "summary": str(plan_output),
        },
        "commands": commands,
        "safety_notes": [
            "This planner is side-effect free; it does not start Docker, run psql, or mutate Postgres.",
            "The emitted commands target the local development pgvector container only.",
            "Run the commands only after reviewing candidate row SQL, vector SQL, and the destination database URL.",
            "Promotion and tenant-visible vector search remain blocked until review queues and committed-count audits pass.",
        ],
    }
    _write_json(plan_output, result)
    return result


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = build_component_local_postgres_smoke_plan(
            component_run_summary="dist/model-ops-daily-runs/2026-05-26/model-ops-daily-run-summary.json",
            load_audit_summary="dist/model-ops-daily-runs/2026-05-26/load-audit/summary.json",
            pgvector_load_plan_summary=dated_nested_artifact_path(
                MODEL_OPS_DAILY_RUNS_DIST_DIR,
                SELF_TEST_DATE,
                PGVECTOR_LOAD_PLAN_SUBDIR,
                PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
            ),
            embedding_execution_plan="dist/model-ops-daily-runs/2026-05-26/embedding-plan/embedding-execution-plan.json",
            vector_readiness_summary="dist/model-ops-daily-runs/2026-05-26/local-hash-embedding-worker/vector-readiness/vector-readiness-summary.json",
            output_dir=tmp,
            run_id="self-test",
        )
        assert result["readiness"]["candidate_rows"] == 1000
        assert result["readiness"]["vector_accepted_rows"] == 1000
        assert result["readiness"]["safe_to_apply_locally"] is True
        assert len(result["commands"]) == 8
    print(json.dumps({"ok": True, "command_count": len(result["commands"])}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--component-run-summary")
    parser.add_argument("--load-audit-summary")
    parser.add_argument(PGVECTOR_LOAD_PLAN_SUMMARY_FLAG)
    parser.add_argument("--embedding-execution-plan")
    parser.add_argument("--vector-readiness-summary")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default="component-local-postgres-smoke")
    parser.add_argument("--compose-file", default=DEFAULT_POSTGRES_COMPOSE_FILE)
    parser.add_argument("--schema-file", default=DEFAULT_POSTGRES_SCHEMA_FILE)
    parser.add_argument("--count-sql", default=DEFAULT_POSTGRES_COUNT_SQL)
    parser.add_argument("--database-url", default=DEFAULT_LOCAL_POSTGRES_DATABASE_URL)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    required = [
        args.component_run_summary,
        args.load_audit_summary,
        args.pgvector_load_plan_summary,
        args.embedding_execution_plan,
        args.vector_readiness_summary,
    ]
    if not all(required):
        parser.error("component run, load audit, pgvector load, embedding plan, and vector readiness inputs are required unless --self-test is used")
    result = build_component_local_postgres_smoke_plan(
        component_run_summary=args.component_run_summary,
        load_audit_summary=args.load_audit_summary,
        pgvector_load_plan_summary=args.pgvector_load_plan_summary,
        embedding_execution_plan=args.embedding_execution_plan,
        vector_readiness_summary=args.vector_readiness_summary,
        output_dir=args.output_dir,
        run_id=args.run_id,
        compose_file=args.compose_file,
        schema_file=args.schema_file,
        count_sql=args.count_sql,
        database_url=args.database_url,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
