#!/usr/bin/env python3
"""Emit a side-effect-free local pgvector embedding smoke execution plan."""
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
    LOCAL_DOCKER_PGVECTOR_BACKEND,
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_PLAN_FILENAME,
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID,
    LOCAL_PGVECTOR_EMBEDDING_SMOKE_SELF_TEST_RUN_ID,
    PGVECTOR_LOAD_PLAN_SUMMARY_FIELD,
    PGVECTOR_LOAD_PLAN_DIST_DIR,
    PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
    PGVECTOR_LOAD_PLAN_SUMMARY_FLAG,
    START_LOCAL_PGVECTOR_STEP,
    WAIT_FOR_PGVECTOR_HEALTH_STEP,
    dated_artifact_path,
)

SELF_TEST_DATE = "2026-05-31"


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


def build_local_pgvector_embedding_smoke_plan(
    *,
    pgvector_load_plan_summary: str | Path,
    embedding_execution_plan: str | Path,
    vector_readiness_summary: str | Path,
    output_dir: str | Path | None = None,
    run_id: str = LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID,
    compose_file: str = DEFAULT_POSTGRES_COMPOSE_FILE,
    schema_file: str = DEFAULT_POSTGRES_SCHEMA_FILE,
    count_sql: str = DEFAULT_POSTGRES_COUNT_SQL,
    database_url: str = DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
) -> dict[str, Any]:
    load_plan = _read_json(pgvector_load_plan_summary)
    load_sql = (load_plan.get("files") or {}).get("load_sql") if isinstance(load_plan.get("files"), dict) else ""
    if not load_sql:
        raise ValueError("pgvector load plan summary does not include files.load_sql")
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-local-pgvector-smoke-"))
    committed_counts = out / "committed-counts.json"
    audit_output = out / "embedding-committed-load-audit.json"
    plan_output = out / LOCAL_PGVECTOR_EMBEDDING_SMOKE_PLAN_FILENAME
    accepted_rows = int(load_plan.get("accepted_rows", 0) or 0)
    rejected_rows = int(load_plan.get("rejected_rows", 0) or 0)

    commands = [
        {
            "step": START_LOCAL_PGVECTOR_STEP,
            "command": f"docker compose -f {compose_file} up -d",
        },
        {
            "step": WAIT_FOR_PGVECTOR_HEALTH_STEP,
            "command": "docker exec open-harness-postgres pg_isready -U open_harness -d open_harness_hub",
        },
        {
            "step": "set_database_url",
            "command": f'export DATABASE_URL="{database_url}"',
        },
        {
            "step": "initialize_schema",
            "command": f'psql "$DATABASE_URL" -f {schema_file}',
        },
        {
            "step": "apply_embedding_load",
            "command": f'psql "$DATABASE_URL" -f {load_sql}',
        },
        {
            "step": "write_committed_counts_json",
            "command": f'psql "$DATABASE_URL" -f {count_sql} --csv | python3 scripts/db/psql_csv_to_count_json.py --output {committed_counts}',
        },
        {
            "step": "audit_embedding_committed_load",
            "command": (
                "python3 -m scripts.db.embedding_committed_load_audit "
                f"--embedding-execution-plan {embedding_execution_plan} "
                f"--vector-readiness-summary {vector_readiness_summary} "
                f"{PGVECTOR_LOAD_PLAN_SUMMARY_FLAG} {pgvector_load_plan_summary} "
                f"--committed-counts {committed_counts} "
                f"--output {audit_output} "
                f"--run-id {run_id}-committed-audit"
            ),
        },
    ]
    result = {
        "ok": accepted_rows > 0 and rejected_rows == 0,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "target": LOCAL_DOCKER_PGVECTOR_BACKEND,
        "inputs": {
            PGVECTOR_LOAD_PLAN_SUMMARY_FIELD: str(pgvector_load_plan_summary),
            "embedding_execution_plan": str(embedding_execution_plan),
            "vector_readiness_summary": str(vector_readiness_summary),
        },
        "readiness": {
            "accepted_load_rows": accepted_rows,
            "rejected_load_rows": rejected_rows,
            "safe_to_smoke_apply": accepted_rows > 0 and rejected_rows == 0,
        },
        "files": {
            "compose_file": compose_file,
            "schema_file": schema_file,
            "count_sql": count_sql,
            "load_sql": str(load_sql),
            "committed_counts": str(committed_counts),
            "embedding_committed_load_audit": str(audit_output),
            "summary": str(plan_output),
        },
        "commands": commands,
        "safety_notes": [
            "This planner is side-effect free; it does not start Docker, run psql, or mutate Postgres.",
            "The DATABASE_URL is a local development default and should not be reused for managed databases.",
            "Run commands only from a reviewed working tree and only against an intended local pgvector container.",
        ],
    }
    _write_json(plan_output, result)
    return result


def _self_test() -> int:
    load_plan = Path(dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, SELF_TEST_DATE, PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME))
    embedding_plan = Path("dist/daily-embedding-execution/2026-05-31/embedding-plan/embedding-execution-plan.json")
    readiness = Path("dist/local-hash-embedding-worker/2026-05-31/vector-readiness/vector-readiness-summary.json")
    if not load_plan.exists() or not embedding_plan.exists() or not readiness.exists():
        raise FileNotFoundError("pgvector load plan, embedding plan, and vector readiness summary are required")
    with tempfile.TemporaryDirectory() as tmp:
        result = build_local_pgvector_embedding_smoke_plan(
            pgvector_load_plan_summary=load_plan,
            embedding_execution_plan=embedding_plan,
            vector_readiness_summary=readiness,
            output_dir=tmp,
            run_id=LOCAL_PGVECTOR_EMBEDDING_SMOKE_SELF_TEST_RUN_ID,
        )
        assert result["readiness"]["accepted_load_rows"] > 0
        assert result["readiness"]["rejected_load_rows"] == 0
        assert any(row["step"] == "apply_embedding_load" for row in result["commands"])
        assert Path(result["files"]["summary"]).exists()
    print(json.dumps({
        "ok": True,
        "command_count": len(result["commands"]),
        "accepted_load_rows": result["readiness"]["accepted_load_rows"],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a local Docker pgvector embedding smoke execution plan.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(PGVECTOR_LOAD_PLAN_SUMMARY_FLAG)
    parser.add_argument("--embedding-execution-plan")
    parser.add_argument("--vector-readiness-summary")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id", default=LOCAL_PGVECTOR_EMBEDDING_SMOKE_RUN_ID)
    parser.add_argument("--compose-file", default=DEFAULT_POSTGRES_COMPOSE_FILE)
    parser.add_argument("--schema-file", default=DEFAULT_POSTGRES_SCHEMA_FILE)
    parser.add_argument("--count-sql", default=DEFAULT_POSTGRES_COUNT_SQL)
    parser.add_argument("--database-url", default=DEFAULT_LOCAL_POSTGRES_DATABASE_URL)
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.pgvector_load_plan_summary or not args.embedding_execution_plan or not args.vector_readiness_summary:
        parser.error("--pgvector-load-plan-summary, --embedding-execution-plan, and --vector-readiness-summary are required unless --self-test is used")
    result = build_local_pgvector_embedding_smoke_plan(
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
