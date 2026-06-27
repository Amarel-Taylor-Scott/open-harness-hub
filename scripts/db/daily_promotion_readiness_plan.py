#!/usr/bin/env python3
"""Plan promotion/load readiness for a staged daily production run."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ in (None, "") and str(Path(__file__).resolve().parents[2]) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root, so scripts.* resolves when run bare

from scripts.security.skill_scanner import BLOCK_AT, SEVERITY_ORDER  # single-source severity (OUTPUT security gate)


ROW_FILES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "index_record": "index-records.jsonl",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(row)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _daily_summary_path(daily_run_dir: Path, run_summary: str | Path | None = None) -> Path:
    if run_summary:
        return Path(run_summary)
    candidates = [
        daily_run_dir / "daily-production-run-summary.json",
        daily_run_dir / "model-ops-daily-run-summary.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _merged_dir(daily_run_dir: Path) -> Path:
    return daily_run_dir / "load-audit" / "merged-jsonl"


def _load_rows(daily_run_dir: Path) -> dict[str, list[dict[str, Any]]]:
    root = _merged_dir(daily_run_dir)
    return {
        family: _read_jsonl(root / filename)
        for family, filename in ROW_FILES.items()
    }


def _body(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("body")
    return value if isinstance(value, dict) else {}


def _risk_tier(obj: dict[str, Any]) -> str:
    return str(_body(obj).get("risk_tier") or "medium")


def _security_open(obj: dict[str, Any]) -> bool:
    """OUTPUT GATE: True when the object carries an UNRESOLVED security finding at/above the block
    threshold (>=high). Such an object can be candidate-load-ready but must NOT become tenant-visible
    until the finding is resolved/quarantined. Severity is single-sourced from the SkillScannerPort.
    docs/security/mcp-and-skill-security.md."""
    sec = _body(obj).get("security_scan")
    if not isinstance(sec, dict):
        return False
    sev = str(sec.get("severity") or "none")
    if sev not in SEVERITY_ORDER:
        sev = "none"
    return SEVERITY_ORDER.index(sev) >= SEVERITY_ORDER.index(BLOCK_AT) and not bool(sec.get("resolved"))


def _embedding_pending(row: dict[str, Any] | None) -> bool:
    if not row:
        return True
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return bool(metadata.get("actual_embedding_required")) or not row.get("embedding")


def _object_readiness(
    *,
    obj: dict[str, Any],
    source_ids: set[str],
    dedupe_ids: set[str],
    review_by_object: dict[str, list[dict[str, Any]]],
    embedding_by_object: dict[str, dict[str, Any]],
    index_count_by_object: dict[str, int],
) -> dict[str, Any]:
    object_id = str(obj.get("object_id") or "")
    source_record_id = str(obj.get("source_record_id") or "")
    dedupe_cluster_id = str(obj.get("dedupe_cluster_id") or "")
    risk_tier = _risk_tier(obj)
    review_tickets = review_by_object.get(object_id, [])
    embedding = embedding_by_object.get(object_id)
    index_record_count = index_count_by_object.get(object_id, 0)
    structural_checks = {
        "has_object_id": bool(object_id),
        "has_source_record": bool(source_record_id and source_record_id in source_ids),
        "has_dedupe_cluster": bool(dedupe_cluster_id and dedupe_cluster_id in dedupe_ids),
        "has_content_hash": bool(obj.get("content_hash")),
        "has_index_records": index_record_count >= 5,
        "has_embedding_work_record": bool(embedding),
    }
    review_required = bool(review_tickets) or risk_tier in {"high", "critical", "regulated"} or obj.get("review_status") == "pending"
    embedding_required = _embedding_pending(embedding)
    security_open = _security_open(obj)
    candidate_load_ready = all(structural_checks.values())
    active_promotion_ready = candidate_load_ready and not review_required and not embedding_required and not security_open
    blockers: list[str] = []
    if not candidate_load_ready:
        blockers.extend(name for name, ok in structural_checks.items() if not ok)
    if review_required:
        blockers.append("review_required")
    if embedding_required:
        blockers.append("embedding_execution_required")
    if security_open:
        blockers.append("security_finding_open")
    return {
        "object_id": object_id,
        "title": obj.get("title"),
        "object_type": obj.get("object_type"),
        "risk_tier": risk_tier,
        "source_record_id": source_record_id,
        "dedupe_cluster_id": dedupe_cluster_id,
        "review_status": obj.get("review_status"),
        "quality_status": obj.get("quality_status"),
        "index_record_count": index_record_count,
        "review_ticket_count": len(review_tickets),
        "embedding_id": embedding.get("embedding_id") if embedding else "",
        "candidate_load_ready": candidate_load_ready,
        "active_promotion_ready": active_promotion_ready,
        "review_required": review_required,
        "embedding_execution_required": embedding_required,
        "security_finding_open": security_open,
        "structural_checks": structural_checks,
        "blockers": sorted(set(blockers)),
    }


def build_daily_promotion_readiness_plan(
    *,
    daily_run_dir: str | Path,
    output_dir: str | Path,
    run_summary: str | Path | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    daily_dir = Path(daily_run_dir)
    out = Path(output_dir)
    summary_path = _daily_summary_path(daily_dir, run_summary)
    summary = _read_json(summary_path)
    rows = _load_rows(daily_dir)
    source_ids = {str(row.get("source_record_id")) for row in rows["source_record"] if row.get("source_record_id")}
    dedupe_ids = {str(row.get("dedupe_cluster_id")) for row in rows["dedupe_cluster"] if row.get("dedupe_cluster_id")}
    review_by_object: dict[str, list[dict[str, Any]]] = {}
    for row in rows["review_ticket"]:
        object_id = str(row.get("object_id") or "")
        if object_id:
            review_by_object.setdefault(object_id, []).append(row)
    embedding_by_object = {
        str(row.get("subject_id")): row
        for row in rows["object_embedding"]
        if row.get("subject_id")
    }
    index_count_by_object: dict[str, int] = {}
    for row in rows["index_record"]:
        subject_id = str(row.get("subject_id") or "")
        if subject_id:
            index_count_by_object[subject_id] = index_count_by_object.get(subject_id, 0) + 1

    readiness_rows = [
        _object_readiness(
            obj=obj,
            source_ids=source_ids,
            dedupe_ids=dedupe_ids,
            review_by_object=review_by_object,
            embedding_by_object=embedding_by_object,
            index_count_by_object=index_count_by_object,
        )
        for obj in rows["normalized_object"]
    ]
    review_queue_rows = [
        {
            "object_id": row["object_id"],
            "risk_tier": row["risk_tier"],
            "review_ticket_count": row["review_ticket_count"],
            "blockers": row["blockers"],
            "recommended_queue": "human_review" if row["review_required"] else "embedding_execution",
        }
        for row in readiness_rows
        if row["review_required"] or row["embedding_execution_required"]
    ]
    counts = {
        "normalized_objects": len(readiness_rows),
        "candidate_load_ready": sum(1 for row in readiness_rows if row["candidate_load_ready"]),
        "active_promotion_ready": sum(1 for row in readiness_rows if row["active_promotion_ready"]),
        "review_required": sum(1 for row in readiness_rows if row["review_required"]),
        "embedding_execution_required": sum(1 for row in readiness_rows if row["embedding_execution_required"]),
        "structural_blocked": sum(1 for row in readiness_rows if not row["candidate_load_ready"]),
        "review_queue_rows": len(review_queue_rows),
    }
    decision = "candidate_load_ready_active_promotion_blocked"
    if counts["structural_blocked"]:
        decision = "fix_structural_load_blockers"
    elif counts["active_promotion_ready"]:
        decision = "promote_review_approved_subset"
    next_actions = [
        "Load staged rows into candidate tables with the emitted side-effect-free SQL after operator approval.",
        "Execute real embeddings for object_embedding rows before tenant-visible vector search.",
        "Resolve review tickets for high-risk rows before active component promotion.",
        "Run content approval and approved component promotion planners only on reviewed subsets.",
    ]

    out.mkdir(parents=True, exist_ok=True)
    readiness_path = out / "promotion-readiness.jsonl"
    review_queue_path = out / "promotion-review-queue.jsonl"
    _write_jsonl(readiness_path, readiness_rows)
    _write_jsonl(review_queue_path, review_queue_rows)
    report = {
        "ok": counts["structural_blocked"] == 0,
        "run_id": run_id or f"promotion-readiness-{summary.get('run_date', daily_dir.name)}",
        "generated_at": _utc_now(),
        "daily_run_dir": str(daily_dir),
        "daily_run_summary": str(summary_path),
        "daily_run": {
            "run_date": summary.get("run_date"),
            "target_count": summary.get("target_count"),
            "matrix": summary.get("matrix"),
            "showcase_count": summary.get("showcase_count"),
            "load_audit": summary.get("load_audit"),
        },
        "counts": counts,
        "decision": decision,
        "next_actions": next_actions,
        "files": {
            "promotion_readiness": str(readiness_path),
            "promotion_review_queue": str(review_queue_path),
            "summary": str(out / "daily-promotion-readiness-plan.json"),
        },
        "safety_notes": [
            "This planner does not promote active components or connect to Postgres.",
            "Candidate load readiness is separate from tenant-visible active promotion readiness.",
            "Rows with embedding stubs remain blocked from active vector-backed publication.",
            "Rows with review tickets remain blocked from active promotion until curator approval.",
        ],
    }
    _write_json(out / "daily-promotion-readiness-plan.json", report)
    return report


def _self_test() -> int:
    result = build_daily_promotion_readiness_plan(
        daily_run_dir="dist/daily-production-runs/2026-05-31",
        output_dir="dist/daily-promotion-readiness/self-test",
        run_id="self-test",
    )
    assert result["counts"]["normalized_objects"] == 5000
    assert result["counts"]["candidate_load_ready"] == 5000
    assert result["counts"]["embedding_execution_required"] == 5000
    assert result["counts"]["review_required"] == 2000
    assert result["counts"]["active_promotion_ready"] == 0
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--daily-run-dir")
    parser.add_argument("--run-summary")
    parser.add_argument("--output-dir", default="dist/daily-promotion-readiness")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.daily_run_dir:
        parser.error("--daily-run-dir is required unless --self-test is used")
    result = build_daily_promotion_readiness_plan(
        daily_run_dir=args.daily_run_dir,
        output_dir=args.output_dir,
        run_summary=args.run_summary,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
