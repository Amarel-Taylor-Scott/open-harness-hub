#!/usr/bin/env python3
"""Audit planned, stored, load-planned, and committed embedding counts."""
from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    EMBEDDING_COMMITTED_LOAD_AUDIT_FILENAME,
    PGVECTOR_COMMITTED_COUNTS_FILENAME,
    PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC,
    PGVECTOR_LOAD_PLAN_DIST_DIR,
    PGVECTOR_LOAD_PLAN_SUMMARY_FIELD,
    PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
    PGVECTOR_LOAD_PLAN_SUMMARY_FLAG,
    PGVECTOR_LOAD_REJECTED_ROWS_METRIC,
    dated_artifact_path,
)

EXAMPLE_DATE = "YYYY-MM-DD"
SELF_TEST_DATE = "2026-05-31"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path | None) -> Any:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return json.loads(candidate.read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _count_jsonl(path: str | Path | None) -> int | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return sum(1 for line in candidate.read_text(encoding="utf-8").splitlines() if line.strip())


def _read_count_rows(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    if candidate.suffix.lower() == ".json":
        value = json.loads(candidate.read_text(encoding="utf-8"))
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
        if isinstance(value, dict) and isinstance(value.get("rows"), list):
            return [row for row in value["rows"] if isinstance(row, dict)]
        return []
    if candidate.suffix.lower() == ".jsonl":
        rows: list[dict[str, Any]] = []
        for line_no, line in enumerate(candidate.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"{candidate}:{line_no}: expected JSON object")
            rows.append(row)
        return rows
    if candidate.suffix.lower() == ".csv":
        with candidate.open(newline="", encoding="utf-8") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    return []


def _committed_object_embedding_count(path: str | Path | None) -> int | None:
    rows = _read_count_rows(path)
    if not rows:
        return None
    for row in rows:
        relation = str(row.get("relation_name") or row.get("relation") or row.get("table") or "")
        if relation != "object_embedding":
            continue
        count_value = row.get("row_count", row.get("count", row.get("rows")))
        try:
            return int(count_value)
        except (TypeError, ValueError):
            return None
    return None


def _status(expected: int | None, actual: int | None, *, strict: bool = True) -> str:
    if expected is None or actual is None:
        return "not_verified"
    if strict:
        return "match" if expected == actual else "mismatch"
    return "sufficient" if actual >= expected else "mismatch"


def audit_embedding_committed_load(
    *,
    embedding_execution_plan: str | Path,
    vector_readiness_summary: str | Path | None = None,
    pgvector_load_plan_summary: str | Path | None = None,
    committed_counts: str | Path | None = None,
    output: str | Path | None = None,
    run_id: str = "embedding-committed-load-audit",
) -> dict[str, Any]:
    embedding_plan = _read_json(embedding_execution_plan)
    if not isinstance(embedding_plan, dict):
        raise ValueError("embedding_execution_plan must contain a JSON object")
    readiness = _read_json(vector_readiness_summary)
    if not isinstance(readiness, dict):
        readiness = {}
    load_plan = _read_json(pgvector_load_plan_summary)
    if not isinstance(load_plan, dict):
        load_plan = {}

    planned_rows = int(embedding_plan.get("planned_completion_rows", 0) or 0)
    sampled_or_ready_rows = readiness.get("ready_rows")
    stored_rows = readiness.get("stored_rows")
    load_accepted_rows = load_plan.get("accepted_rows")
    load_rejected_rows = load_plan.get("rejected_rows")
    committed_rows = _committed_object_embedding_count(committed_counts)
    committed_input_status = "provided" if committed_rows is not None else "missing"

    checks = [
        {
            "check_id": "planned_rows_present",
            "expected": ">0",
            "actual": planned_rows,
            "status": "match" if planned_rows > 0 else "mismatch",
        },
        {
            "check_id": "stored_vectors_match_readiness_sample",
            "expected": sampled_or_ready_rows,
            "actual": stored_rows,
            "status": _status(sampled_or_ready_rows, stored_rows),
        },
        {
            "check_id": "pgvector_load_accepts_ready_rows",
            "expected": sampled_or_ready_rows,
            "actual": load_accepted_rows,
            "status": _status(sampled_or_ready_rows, load_accepted_rows),
        },
        {
            "check_id": "pgvector_load_has_no_rejections",
            "expected": 0,
            "actual": load_rejected_rows,
            "status": _status(0, load_rejected_rows),
        },
        {
            "check_id": "committed_rows_cover_load_plan",
            "expected": load_accepted_rows,
            "actual": committed_rows,
            "status": _status(load_accepted_rows, committed_rows, strict=False),
        },
    ]

    statuses = {row["status"] for row in checks}
    if "mismatch" in statuses:
        audit_status = "mismatch"
    elif committed_rows is None:
        audit_status = "load_planned_not_committed"
    elif "not_verified" in statuses:
        audit_status = "not_verified"
    else:
        audit_status = "verified"

    report = {
        "ok": audit_status in {"verified", "load_planned_not_committed"},
        "run_id": run_id,
        "generated_at": _utc_now(),
        "audit_status": audit_status,
        "inputs": {
            "embedding_execution_plan": str(embedding_execution_plan),
            "vector_readiness_summary": str(vector_readiness_summary) if vector_readiness_summary else "",
            PGVECTOR_LOAD_PLAN_SUMMARY_FIELD: str(pgvector_load_plan_summary) if pgvector_load_plan_summary else "",
            "committed_counts": str(committed_counts) if committed_counts else "",
        },
        "counts": {
            "planned_completion_rows": planned_rows,
            "vector_readiness_ready_rows": sampled_or_ready_rows,
            "vector_readiness_stored_rows": stored_rows,
            PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC: load_accepted_rows,
            PGVECTOR_LOAD_REJECTED_ROWS_METRIC: load_rejected_rows,
            "committed_object_embedding_rows": committed_rows,
        },
        "committed_input_status": committed_input_status,
        "checks": checks,
        "readiness_decision": {
            "vector_search_product_ready": audit_status == "verified",
            "reason": (
                "Committed Postgres object_embedding count covers the load plan."
                if audit_status == "verified"
                else "Postgres committed counts are missing or do not yet cover the load plan."
            ),
        },
        "operator_commands": [
            {
                "step": "write_committed_counts_json",
                "command": (
                    'psql "$DATABASE_URL" -f db/postgres/object_count_report.sql --csv '
                    "| python3 scripts/db/psql_csv_to_count_json.py "
                    f"--output {dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, EXAMPLE_DATE, PGVECTOR_COMMITTED_COUNTS_FILENAME)}"
                ),
            },
            {
                "step": "rerun_embedding_committed_audit",
                "command": (
                    "python3 -m scripts.db.embedding_committed_load_audit "
                    "--embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json "
                    "--vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json "
                    f"{PGVECTOR_LOAD_PLAN_SUMMARY_FLAG} "
                    f"{dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, EXAMPLE_DATE, PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME)} "
                    "--committed-counts "
                    f"{dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, EXAMPLE_DATE, PGVECTOR_COMMITTED_COUNTS_FILENAME)} "
                    "--output "
                    f"{dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, EXAMPLE_DATE, EMBEDDING_COMMITTED_LOAD_AUDIT_FILENAME)}"
                ),
            },
        ],
        "safety_notes": [
            "This audit is side-effect free and reads only summaries, count rows, and metadata.",
            "Vector search is not product-ready unless committed Postgres counts cover the load plan.",
            "A missing committed-count file is expected before an operator applies the SQL.",
        ],
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    embedding_plan = Path(f"dist/daily-embedding-execution/{SELF_TEST_DATE}/embedding-plan/embedding-execution-plan.json")
    readiness = Path(f"dist/local-hash-embedding-worker/{SELF_TEST_DATE}/vector-readiness/vector-readiness-summary.json")
    load_plan = Path(dated_artifact_path(PGVECTOR_LOAD_PLAN_DIST_DIR, SELF_TEST_DATE, PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME))
    if not embedding_plan.exists() or not readiness.exists() or not load_plan.exists():
        raise FileNotFoundError("embedding plan, vector readiness summary, and pgvector load plan summary are required")
    result = audit_embedding_committed_load(
        embedding_execution_plan=embedding_plan,
        vector_readiness_summary=readiness,
        pgvector_load_plan_summary=load_plan,
    )
    assert result["audit_status"] == "load_planned_not_committed"
    assert result["counts"][PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC] > 0
    assert result["readiness_decision"]["vector_search_product_ready"] is False
    print(json.dumps({
        "ok": True,
        "audit_status": result["audit_status"],
        "accepted_rows": result["counts"][PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC],
    }, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit planned, stored, load-planned, and committed embedding counts.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--embedding-execution-plan")
    parser.add_argument("--vector-readiness-summary")
    parser.add_argument(PGVECTOR_LOAD_PLAN_SUMMARY_FLAG)
    parser.add_argument("--committed-counts")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="embedding-committed-load-audit")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.embedding_execution_plan:
        parser.error("--embedding-execution-plan is required unless --self-test is used")
    result = audit_embedding_committed_load(
        embedding_execution_plan=args.embedding_execution_plan,
        vector_readiness_summary=args.vector_readiness_summary,
        pgvector_load_plan_summary=args.pgvector_load_plan_summary,
        committed_counts=args.committed_counts,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["audit_status"] != "mismatch" else 1


if __name__ == "__main__":
    raise SystemExit(main())
