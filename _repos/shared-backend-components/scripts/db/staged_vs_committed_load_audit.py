#!/usr/bin/env python3
"""Compare staged bulk-load counts with committed Postgres count rows."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import csv
import json
import time
from pathlib import Path
from typing import Any


RELATION_TO_STAGED = {
    "source_record": "source_record",
    "normalized_object": "normalized_object",
    "canonical_entity": "canonical_entity",
    "object_entity_ref": "object_entity_ref",
    "dedupe_cluster": "dedupe_cluster",
    "review_ticket": "review_ticket",
    "promotion_decision": "promotion_decision",
    "index_record": "index_record",
    "object_embedding": "object_embedding",
    "label_assignment": "label_assignment",
    "dimension_value": "dimension_value",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: str | Path | None) -> Any:
    if not path:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_plan_counts(load_plan: dict[str, Any]) -> dict[str, int]:
    bulk = load_plan.get("bulk_manifest") if isinstance(load_plan.get("bulk_manifest"), dict) else {}
    counts = bulk.get("counts") if isinstance(bulk.get("counts"), dict) else {}
    return {str(key): int(value) for key, value in counts.items() if isinstance(value, int)}


def _count_jsonl_lines(path: str | Path | None) -> int | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return sum(1 for line in candidate.read_text(encoding="utf-8").splitlines() if line.strip())


def _committed_counts_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    committed: dict[str, int] = {}
    for row in rows:
        relation = str(row.get("relation_name") or row.get("relation") or row.get("table") or "")
        if not relation:
            continue
        count_value = row.get("row_count", row.get("count", row.get("rows")))
        try:
            committed[relation] = int(count_value)
        except (TypeError, ValueError):
            continue
    return committed


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


def _audit_rows(staged: dict[str, int], committed: dict[str, int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for relation, staged_key in sorted(RELATION_TO_STAGED.items()):
        expected = staged.get(staged_key, 0)
        actual = committed.get(relation)
        if actual is None:
            status = "not_verified"
            delta = None
        else:
            delta = actual - expected
            status = "match" if delta == 0 else "mismatch"
        rows.append({
            "relation_name": relation,
            "staged_family": staged_key,
            "expected_staged_count": expected,
            "committed_count": actual,
            "delta": delta,
            "status": status,
        })
    return rows


def audit_staged_vs_committed_load(
    *,
    load_plan_manifest: str | Path,
    committed_counts: str | Path | None = None,
    execution_summary: str | Path | None = None,
    output: str | Path | None = None,
    run_id: str = "staged-vs-committed-load-audit",
) -> dict[str, Any]:
    load_plan = _read_json(load_plan_manifest)
    if not isinstance(load_plan, dict):
        raise ValueError("load_plan_manifest must contain a JSON object")
    staged = _load_plan_counts(load_plan)
    committed = _committed_counts_from_rows(_read_count_rows(committed_counts))
    rows = _audit_rows(staged, committed)
    execution = _read_json(execution_summary) if execution_summary else {}
    if not isinstance(execution, dict):
        execution = {}
    preflight = load_plan.get("preflight_report") if isinstance(load_plan.get("preflight_report"), dict) else {}
    bulk = load_plan.get("bulk_manifest") if isinstance(load_plan.get("bulk_manifest"), dict) else {}
    statuses = {row["status"] for row in rows}
    if "mismatch" in statuses:
        audit_status = "mismatch"
    elif committed:
        audit_status = "verified"
    else:
        audit_status = "staged_only"
    report = {
        "run_id": run_id,
        "generated_at": _utc_now(),
        "audit_status": audit_status,
        "load_plan_manifest": str(load_plan_manifest),
        "committed_counts_input": str(committed_counts) if committed_counts else "",
        "execution_summary_input": str(execution_summary) if execution_summary else "",
        "summary": {
            "expected_staged_total": sum(staged.values()),
            "committed_total": sum(committed.values()) if committed else None,
            "relations_checked": len(rows),
            "matching_relations": sum(1 for row in rows if row["status"] == "match"),
            "mismatched_relations": sum(1 for row in rows if row["status"] == "mismatch"),
            "not_verified_relations": sum(1 for row in rows if row["status"] == "not_verified"),
        },
        "preflight": {
            "ok": bool(preflight.get("ok")),
            "issue_count": int(preflight.get("issue_count", 0) or 0),
        },
        "bulk_load": {
            "ok": bool(bulk.get("ok")),
            "load_sql": bulk.get("load_sql", ""),
            "load_command": bulk.get("load_command", ""),
        },
        "execution_summary": {
            "source_surface_count": (execution.get("source_surfaces") or {}).get("count"),
            "partition_count": (execution.get("partitions") or {}).get("count"),
            "generated_row_total": (execution.get("generated_rows") or {}).get("total"),
            "review_ticket_total": (execution.get("review") or {}).get("total_review_tickets"),
        },
        "relations": rows,
        "safety": {
            "raw_private_data_stored": False,
            "source_bodies_required_for_audit": False,
            "insurance_scope_excluded": True,
            "canonical_count_sql": "db/postgres/object_count_report.sql",
        },
    }
    if output:
        _write_json(output, report)
    return report


def _self_test() -> int:
    load_plan = _resource("dist/source-surface-scan-partitions/seed/load-plan/load-plan-manifest.json")
    if not load_plan.exists():
        raise FileNotFoundError("dist/source-surface-scan-partitions/seed/load-plan/load-plan-manifest.json is required")
    result = audit_staged_vs_committed_load(load_plan_manifest=load_plan)
    assert result["audit_status"] == "staged_only"
    assert result["summary"]["expected_staged_total"] > 0
    assert result["preflight"]["ok"] is True
    print(json.dumps({"ok": True, "audit_status": result["audit_status"], "expected_staged_total": result["summary"]["expected_staged_total"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare staged bulk-load counts with committed Postgres count rows.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--load-plan-manifest")
    parser.add_argument("--committed-counts")
    parser.add_argument("--execution-summary")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="staged-vs-committed-load-audit")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.load_plan_manifest:
        parser.error("--load-plan-manifest is required unless --self-test is used")
    result = audit_staged_vs_committed_load(
        load_plan_manifest=args.load_plan_manifest,
        committed_counts=args.committed_counts,
        execution_summary=args.execution_summary,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["audit_status"] != "mismatch" else 1


if __name__ == "__main__":
    raise SystemExit(main())
