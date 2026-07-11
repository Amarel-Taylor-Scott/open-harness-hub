#!/usr/bin/env python3
"""Build a fast closeout report from database-first factory outputs."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from scripts._config import (
    EMBEDDING_COMMITTED_LOAD_AUDIT_FILENAME,
    PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC,
    PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
    PGVECTOR_LOAD_PLAN_SUMMARY_FIELD,
    PGVECTOR_LOAD_PLAN_SUMMARY_FLAG,
    PGVECTOR_LOAD_REJECTED_ROWS_METRIC,
    THEORY_PGVECTOR_LOAD_PLAN_DIST_DIR,
    dated_artifact_path,
)

SELF_TEST_DATE = "2026-05-26"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists():
        return {}
    value = json.loads(candidate.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _nested(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key)
    return default if current is None else current


def build_fast_factory_closeout_report(
    *,
    output: str | Path,
    run_id: str = "fast-factory-closeout",
    component_id_index: str | Path = "dist/catalog-component-ids.json",
    theory_batch_summary: str | Path | None = None,
    load_audit_summary: str | Path | None = None,
    governance_bridge_summary: str | Path | None = None,
    local_vector_worker_summary: str | Path | None = None,
    pgvector_load_plan_summary: str | Path | None = None,
    embedding_committed_load_audit: str | Path | None = None,
    local_postgres_smoke_plan: str | Path | None = None,
) -> dict[str, Any]:
    component_index = _read_json(component_id_index)
    theory = _read_json(theory_batch_summary)
    load_audit = _read_json(load_audit_summary)
    governance = _read_json(governance_bridge_summary)
    vector_worker = _read_json(local_vector_worker_summary)
    pgvector = _read_json(pgvector_load_plan_summary)
    committed_audit = _read_json(embedding_committed_load_audit)
    smoke = _read_json(local_postgres_smoke_plan)

    generated_candidates = int(_nested(theory, "row_counts", "normalized_object", default=0) or 0)
    unique_staged_rows = int(_nested(load_audit, "merge_report", "unique_total", default=0) or 0)
    review_tickets = int(_nested(theory, "row_counts", "review_ticket", default=0) or 0)
    embedding_planned = int(_nested(governance, "embedding", "planned_completion_rows", default=0) or 0)
    vector_ready = int(_nested(vector_worker, "vector_readiness", "ready_rows", default=0) or 0)
    pgvector_accepted = int(pgvector.get("accepted_rows", 0) or 0)
    pgvector_rejected = int(pgvector.get("rejected_rows", 0) or 0)
    committed_rows = _nested(committed_audit, "counts", "committed_object_embedding_rows")
    audit_status = str(committed_audit.get("audit_status") or "not_available")

    release_gate_needed = False
    release_gate_reasons: list[str] = []
    if not component_index:
        release_gate_needed = True
        release_gate_reasons.append("component_id_index_missing")
    if pgvector_rejected:
        release_gate_needed = True
        release_gate_reasons.append("pgvector_rejections_present")
    if _nested(load_audit, "preflight", "issue_count", default=0):
        release_gate_needed = True
        release_gate_reasons.append("load_preflight_issues_present")

    report = {
        "ok": bool(component_index) and generated_candidates >= 0,
        "run_id": run_id,
        "generated_at": _utc_now(),
        "speed_policy": {
            "mode": "database_first_incremental",
            "full_rebuild_required": release_gate_needed,
            "full_rebuild_reasons": release_gate_reasons,
            "recommended_validation": (
                "focused validation and selected page render"
                if not release_gate_needed
                else "full release validation before publication"
            ),
        },
        "public_component_definitions": {
            "component_id_index": str(component_id_index),
            "component_count": component_index.get("component_count"),
            "meaning": "public curated YAML definitions, not generated database component rows",
        },
        "database_first_metrics": {
            "generated_normalized_component_candidates": generated_candidates,
            "unique_staged_rows": unique_staged_rows,
            "candidate_load_sql": _nested(load_audit, "bulk_manifest", "load_sql", default=""),
            "review_tickets": review_tickets,
            "embedding_planned_rows": embedding_planned,
            "vector_ready_rows": vector_ready,
            PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC: pgvector_accepted,
            PGVECTOR_LOAD_REJECTED_ROWS_METRIC: pgvector_rejected,
            "committed_object_embedding_rows": committed_rows,
            "embedding_committed_audit_status": audit_status,
            "vector_search_product_ready": _nested(
                committed_audit,
                "readiness_decision",
                "vector_search_product_ready",
                default=False,
            ),
        },
        "local_postgres_smoke": {
            "available": bool(smoke),
            "command_count": len(smoke.get("commands", [])) if smoke else 0,
            "safe_to_apply_locally": _nested(smoke, "readiness", "safe_to_apply_locally", default=False),
            "summary": str(local_postgres_smoke_plan) if local_postgres_smoke_plan else "",
        },
        "inputs": {
            "theory_batch_summary": str(theory_batch_summary) if theory_batch_summary else "",
            "load_audit_summary": str(load_audit_summary) if load_audit_summary else "",
            "governance_bridge_summary": str(governance_bridge_summary) if governance_bridge_summary else "",
            "local_vector_worker_summary": str(local_vector_worker_summary) if local_vector_worker_summary else "",
            PGVECTOR_LOAD_PLAN_SUMMARY_FIELD: str(pgvector_load_plan_summary) if pgvector_load_plan_summary else "",
            "embedding_committed_load_audit": str(embedding_committed_load_audit) if embedding_committed_load_audit else "",
            "local_postgres_smoke_plan": str(local_postgres_smoke_plan) if local_postgres_smoke_plan else "",
        },
        "guardrails": [
            "Do not treat public YAML count as total component count.",
            "Do not treat staged JSONL as committed database state.",
            "Do not treat pgvector SQL as product-ready vector search until committed counts verify it.",
            "Use full validation and full page rebuilds as release gates, not the daily factory loop.",
        ],
    }
    _write_json(output, report)
    return report


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        result = build_fast_factory_closeout_report(
            output=Path(tmp) / "fast-closeout.json",
            run_id="self-test",
            theory_batch_summary="dist/theory-component-batch/2026-05-26/theory-component-batch-summary.json",
            load_audit_summary="dist/theory-component-batch-load-audit/2026-05-26/summary.json",
            governance_bridge_summary="dist/theory-batch-governance-bridge/2026-05-26/theory-batch-governance-bridge-summary.json",
            local_vector_worker_summary="dist/theory-local-hash-embedding-worker/2026-05-26/local-hash-embedding-worker-summary.json",
            pgvector_load_plan_summary=dated_artifact_path(
                THEORY_PGVECTOR_LOAD_PLAN_DIST_DIR,
                SELF_TEST_DATE,
                PGVECTOR_LOAD_PLAN_SUMMARY_FILENAME,
            ),
            embedding_committed_load_audit=dated_artifact_path(
                THEORY_PGVECTOR_LOAD_PLAN_DIST_DIR,
                SELF_TEST_DATE,
                EMBEDDING_COMMITTED_LOAD_AUDIT_FILENAME,
            ),
            local_postgres_smoke_plan="dist/theory-local-postgres-smoke/2026-05-26/theory-local-postgres-smoke-plan.json",
        )
        assert result["database_first_metrics"]["generated_normalized_component_candidates"] == 1000
        assert result["database_first_metrics"]["unique_staged_rows"] == 77083
        assert result["database_first_metrics"][PGVECTOR_LOAD_ACCEPTED_ROWS_METRIC] == 1000
        assert result["database_first_metrics"]["vector_search_product_ready"] is False
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", default="dist/fast-factory-closeout/summary.json")
    parser.add_argument("--run-id", default="fast-factory-closeout")
    parser.add_argument("--component-id-index", default="dist/catalog-component-ids.json")
    parser.add_argument("--theory-batch-summary")
    parser.add_argument("--load-audit-summary")
    parser.add_argument("--governance-bridge-summary")
    parser.add_argument("--local-vector-worker-summary")
    parser.add_argument(PGVECTOR_LOAD_PLAN_SUMMARY_FLAG)
    parser.add_argument("--embedding-committed-load-audit")
    parser.add_argument("--local-postgres-smoke-plan")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    result = build_fast_factory_closeout_report(
        output=args.output,
        run_id=args.run_id,
        component_id_index=args.component_id_index,
        theory_batch_summary=args.theory_batch_summary,
        load_audit_summary=args.load_audit_summary,
        governance_bridge_summary=args.governance_bridge_summary,
        local_vector_worker_summary=args.local_vector_worker_summary,
        pgvector_load_plan_summary=args.pgvector_load_plan_summary,
        embedding_committed_load_audit=args.embedding_committed_load_audit,
        local_postgres_smoke_plan=args.local_postgres_smoke_plan,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
