#!/usr/bin/env python3
"""Emit a concrete Postgres/pgvector bootstrap plan.

The planner is intentionally side-effect free. It gives local, Render, or
managed-Postgres deployments the exact schema/load/count sequence without
requiring psql or Docker in CI.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from scripts._config import (
    DEFAULT_DATABASE_URL_ENV,
    DEFAULT_LOCAL_POSTGRES_DATABASE_URL,
    DEFAULT_POSTGRES_COMPOSE_FILE,
    DEFAULT_POSTGRES_COUNT_SQL,
    DEFAULT_POSTGRES_LOAD_SQL,
    DEFAULT_POSTGRES_SCHEMA_FILE,
    MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER,
    START_LOCAL_PGVECTOR_STEP,
)


def build_plan(
    *,
    target: str = "local_docker",
    database_url_env: str = DEFAULT_DATABASE_URL_ENV,
    compose_file: str = DEFAULT_POSTGRES_COMPOSE_FILE,
    schema_file: str = DEFAULT_POSTGRES_SCHEMA_FILE,
    load_sql: str = DEFAULT_POSTGRES_LOAD_SQL,
    count_sql: str = DEFAULT_POSTGRES_COUNT_SQL,
    output: str | None = None,
) -> dict[str, Any]:
    if target not in {"local_docker", "render", "managed_postgres"}:
        raise ValueError("target must be one of: local_docker, render, managed_postgres")

    prerequisites = ["Postgres 16 compatible database", "pgvector extension available", "psql client"]
    commands: list[dict[str, str]] = []
    if target == "local_docker":
        prerequisites.insert(0, "Docker with compose plugin")
        commands.append({
            "step": START_LOCAL_PGVECTOR_STEP,
            "command": f"docker compose -f {compose_file} up -d",
        })
        commands.append({
            "step": "set_database_url",
            "command": f'export {database_url_env}="{DEFAULT_LOCAL_POSTGRES_DATABASE_URL}"',
        })
    else:
        commands.append({
            "step": "set_database_url",
            "command": f'export {database_url_env}="{MANAGED_POSTGRES_PGVECTOR_URL_PLACEHOLDER}"',
        })

    commands.extend([
        {
            "step": "initialize_schema",
            "command": f'psql "${database_url_env}" -f {schema_file}',
        },
        {
            "step": "emit_loader_sql",
            "command": (
                "python3 -m scripts.db.factory_jsonl_to_postgres "
                "--source-records catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl "
                "--normalized-objects catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl "
                "--promotion-decisions catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl "
                f"--output {load_sql}"
            ),
        },
        {
            "step": "apply_loader_sql",
            "command": f'psql "${database_url_env}" -f {load_sql}',
        },
        {
            "step": "count_canonical_rows",
            "command": f'psql "${database_url_env}" -f {count_sql}',
        },
        {
            "step": "count_staged_rows",
            "command": (
                "python3 -m scripts.db.object_count_report "
                "--jsonl source_record=catalog/knowledge-packs/data/task-marketplace-archetype-patterns/source-records.jsonl "
                "--jsonl normalized_object=catalog/knowledge-packs/data/task-marketplace-archetype-patterns/archetype-patterns.jsonl "
                "--jsonl promotion_decision=catalog/knowledge-packs/data/promotion-index-delta-patterns/promotion-decisions.jsonl "
                "--output dist/reports/object-count-report.json"
            ),
        },
    ])

    plan = {
        "target": target,
        "database_url_env": database_url_env,
        "prerequisites": prerequisites,
        "files": {
            "compose_file": compose_file if target == "local_docker" else None,
            "schema_file": schema_file,
            "load_sql": load_sql,
            "count_sql": count_sql,
        },
        "commands": commands,
        "counting_policy": {
            "manifest_count": "curated YAML component definitions",
            "canonical_db_row_count": "Postgres rows across generated object tables",
            "staged_jsonl_row_count": "portable shard rows, not authoritative after load",
        },
    }
    if output:
        out = Path(output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return plan


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "plan.json"
        plan = build_plan(output=str(out))
        assert out.exists()
        assert plan["target"] == "local_docker"
        assert any(command["step"] == "initialize_schema" for command in plan["commands"])
        assert any(command["step"] == "count_canonical_rows" for command in plan["commands"])
        print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit a Postgres/pgvector bootstrap plan.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--target", default="local_docker", choices=["local_docker", "render", "managed_postgres"])
    parser.add_argument("--database-url-env", default=DEFAULT_DATABASE_URL_ENV)
    parser.add_argument("--compose-file", default=DEFAULT_POSTGRES_COMPOSE_FILE)
    parser.add_argument("--schema-file", default=DEFAULT_POSTGRES_SCHEMA_FILE)
    parser.add_argument("--load-sql", default=DEFAULT_POSTGRES_LOAD_SQL)
    parser.add_argument("--count-sql", default=DEFAULT_POSTGRES_COUNT_SQL)
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    plan = build_plan(
        target=args.target,
        database_url_env=args.database_url_env,
        compose_file=args.compose_file,
        schema_file=args.schema_file,
        load_sql=args.load_sql,
        count_sql=args.count_sql,
        output=args.output,
    )
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
