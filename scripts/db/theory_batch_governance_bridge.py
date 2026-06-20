#!/usr/bin/env python3
"""Bridge a theory component batch into promotion and embedding governance plans."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

from scripts._config import DEFAULT_EMBEDDING_PROFILE_ID, embedding_model_profiles
from scripts.db.embedding_execution_plan import plan_embedding_execution
from scripts.db.vector_readiness_audit import audit_vector_readiness


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
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")


def _rows(merged_jsonl_dir: Path) -> dict[str, list[dict[str, Any]]]:
    return {family: _read_jsonl(merged_jsonl_dir / filename) for family, filename in ROW_FILES.items()}


def _body(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("body")
    return value if isinstance(value, dict) else {}


def _risk_tier(row: dict[str, Any]) -> str:
    return str(_body(row).get("risk_tier") or "medium")


def _embedding_pending(row: dict[str, Any] | None) -> bool:
    if not row:
        return True
    metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    return bool(metadata.get("actual_embedding_required")) or not row.get("embedding")


def _build_readiness_rows(rows: dict[str, list[dict[str, Any]]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, int]]:
    source_ids = {str(row.get("source_record_id")) for row in rows["source_record"] if row.get("source_record_id")}
    dedupe_ids = {str(row.get("dedupe_cluster_id")) for row in rows["dedupe_cluster"] if row.get("dedupe_cluster_id")}
    review_by_object: dict[str, list[dict[str, Any]]] = {}
    for ticket in rows["review_ticket"]:
        object_id = str(ticket.get("object_id") or "")
        if object_id:
            review_by_object.setdefault(object_id, []).append(ticket)
    embedding_by_object = {str(row.get("subject_id")): row for row in rows["object_embedding"] if row.get("subject_id")}
    index_count_by_object: dict[str, int] = {}
    for index_record in rows["index_record"]:
        subject_id = str(index_record.get("subject_id") or "")
        if subject_id:
            index_count_by_object[subject_id] = index_count_by_object.get(subject_id, 0) + 1

    readiness_rows: list[dict[str, Any]] = []
    review_queue_rows: list[dict[str, Any]] = []
    for obj in rows["normalized_object"]:
        object_id = str(obj.get("object_id") or "")
        source_record_id = str(obj.get("source_record_id") or "")
        dedupe_cluster_id = str(obj.get("dedupe_cluster_id") or "")
        risk_tier = _risk_tier(obj)
        tickets = review_by_object.get(object_id, [])
        embedding = embedding_by_object.get(object_id)
        index_count = index_count_by_object.get(object_id, 0)
        checks = {
            "has_object_id": bool(object_id),
            "has_source_record": bool(source_record_id and source_record_id in source_ids),
            "has_dedupe_cluster": bool(dedupe_cluster_id and dedupe_cluster_id in dedupe_ids),
            "has_content_hash": bool(obj.get("content_hash")),
            "has_index_records": index_count >= 5,
            "has_embedding_work_record": bool(embedding),
        }
        review_required = bool(tickets) or risk_tier in {"high", "critical", "regulated"} or obj.get("review_status") == "pending"
        embedding_required = _embedding_pending(embedding)
        candidate_load_ready = all(checks.values())
        active_promotion_ready = candidate_load_ready and not review_required and not embedding_required
        blockers: list[str] = []
        if not candidate_load_ready:
            blockers.extend(name for name, ok in checks.items() if not ok)
        if review_required:
            blockers.append("review_required")
        if embedding_required:
            blockers.append("embedding_execution_required")
        row = {
            "object_id": object_id,
            "title": obj.get("title"),
            "object_type": obj.get("object_type"),
            "risk_tier": risk_tier,
            "source_record_id": source_record_id,
            "dedupe_cluster_id": dedupe_cluster_id,
            "review_status": obj.get("review_status"),
            "quality_status": obj.get("quality_status"),
            "index_record_count": index_count,
            "review_ticket_count": len(tickets),
            "embedding_id": embedding.get("embedding_id") if embedding else "",
            "candidate_load_ready": candidate_load_ready,
            "active_promotion_ready": active_promotion_ready,
            "review_required": review_required,
            "embedding_execution_required": embedding_required,
            "structural_checks": checks,
            "blockers": sorted(set(blockers)),
        }
        readiness_rows.append(row)
        if review_required or embedding_required:
            review_queue_rows.append({
                "object_id": object_id,
                "risk_tier": risk_tier,
                "review_ticket_count": len(tickets),
                "blockers": row["blockers"],
                "recommended_queue": "human_review" if review_required else "embedding_execution",
            })
    counts = {
        "normalized_objects": len(readiness_rows),
        "candidate_load_ready": sum(1 for row in readiness_rows if row["candidate_load_ready"]),
        "active_promotion_ready": sum(1 for row in readiness_rows if row["active_promotion_ready"]),
        "review_required": sum(1 for row in readiness_rows if row["review_required"]),
        "embedding_execution_required": sum(1 for row in readiness_rows if row["embedding_execution_required"]),
        "structural_blocked": sum(1 for row in readiness_rows if not row["candidate_load_ready"]),
        "review_queue_rows": len(review_queue_rows),
    }
    return readiness_rows, review_queue_rows, counts


def build_theory_batch_governance_bridge(
    *,
    theory_batch_summary: str | Path,
    load_audit_summary: str | Path,
    output_dir: str | Path,
    run_id: str = "theory-batch-governance",
    default_profile: str = DEFAULT_EMBEDDING_PROFILE_ID,
    max_items_per_batch: int = 256,
    max_tokens_per_batch: int = 24000,
    stored_vectors_jsonl: str | Path | None = None,
) -> dict[str, Any]:
    out = Path(output_dir)
    theory_summary = _read_json(Path(theory_batch_summary))
    load_audit = _read_json(Path(load_audit_summary))
    merged_dir = Path(load_audit_summary).parent / "merged-jsonl"
    row_families = _rows(merged_dir)

    readiness_rows, review_queue_rows, promotion_counts = _build_readiness_rows(row_families)
    readiness_path = out / "promotion" / "promotion-readiness.jsonl"
    review_queue_path = out / "promotion" / "promotion-review-queue.jsonl"
    _write_jsonl(readiness_path, readiness_rows)
    _write_jsonl(review_queue_path, review_queue_rows)

    profile_path = out / "embedding" / "embedding-model-profiles.json"
    _write_json(profile_path, embedding_model_profiles(include_hosted_placeholder=True))
    embedding_plan = plan_embedding_execution(
        object_embeddings_jsonl=merged_dir / "object-embeddings.jsonl",
        output_dir=out / "embedding" / "embedding-plan",
        run_id=run_id,
        default_profile=default_profile,
        model_profiles_json=profile_path,
        max_items_per_batch=max_items_per_batch,
        max_tokens_per_batch=max_tokens_per_batch,
    )
    vector_readiness = audit_vector_readiness(
        completion_stubs_jsonl=embedding_plan["files"]["embedding_completion_stubs"],
        stored_vectors_jsonl=stored_vectors_jsonl,
        output_dir=out / "embedding" / "vector-readiness",
        run_id=f"{run_id}-vector-readiness",
    )

    decision = "ready_for_candidate_table_load"
    if promotion_counts["structural_blocked"]:
        decision = "fix_structural_load_blockers"
    elif promotion_counts["review_required"] and promotion_counts["embedding_execution_required"]:
        decision = "candidate_load_ready_review_and_embedding_required"
    elif promotion_counts["review_required"]:
        decision = "candidate_load_ready_review_required"
    elif promotion_counts["embedding_execution_required"]:
        decision = "candidate_load_ready_embedding_required"

    report = {
        "ok": promotion_counts["structural_blocked"] == 0 and bool(embedding_plan.get("ok")) and bool(vector_readiness.get("ok")),
        "run_id": run_id,
        "generated_at": _utc_now(),
        "theory_batch_summary": str(theory_batch_summary),
        "load_audit_summary": str(load_audit_summary),
        "merged_jsonl_dir": str(merged_dir),
        "theory_batch": {
            "theory_seed_count": theory_summary.get("theory_seed_count"),
            "seed_count": theory_summary.get("seed_count"),
            "high_risk_seed_count": theory_summary.get("high_risk_seed_count"),
            "row_counts": theory_summary.get("row_counts"),
        },
        "load_audit": {
            "audit_status": load_audit.get("audit_status"),
            "unique_total": load_audit.get("merge_report", {}).get("unique_total"),
            "duplicate_total": load_audit.get("merge_report", {}).get("duplicate_total"),
            "preflight": load_audit.get("preflight"),
            "load_sql": load_audit.get("bulk_manifest", {}).get("load_sql"),
        },
        "promotion": {
            "counts": promotion_counts,
            "decision": decision,
            "files": {
                "promotion_readiness": str(readiness_path),
                "promotion_review_queue": str(review_queue_path),
            },
        },
        "embedding": {
            "input_embedding_rows": embedding_plan.get("input_embedding_rows"),
            "planned_batch_count": embedding_plan.get("planned_batch_count"),
            "planned_completion_rows": embedding_plan.get("planned_completion_rows"),
            "cost_by_profile": embedding_plan.get("cost_by_profile"),
            "vector_readiness": {
                "planned_rows": vector_readiness.get("planned_rows"),
                "ready_rows": vector_readiness.get("ready_rows"),
                "missing_vector_rows": vector_readiness.get("missing_vector_rows"),
                "readiness_status": vector_readiness.get("readiness_status"),
            },
            "files": {
                "model_profiles": str(profile_path),
                "embedding_plan": embedding_plan["files"]["manifest"],
                "vector_readiness": vector_readiness["files"]["summary"],
            },
        },
        "next_actions": [
            "Apply staged load SQL to candidate tables only after operator approval.",
            "Run local embedding workers for planned embedding batches.",
            "Resolve high-risk review tickets before active component promotion.",
            "Rerun vector readiness and committed-load audits after vectors and candidate rows are written.",
        ],
        "safety_notes": [
            "This bridge does not call model providers, mutate Postgres, or promote active components.",
            "Candidate load readiness is distinct from tenant-visible active promotion readiness.",
            "Theory-derived high-risk rows remain review-gated even when structurally load-ready.",
        ],
        "files": {
            "summary": str(out / "theory-batch-governance-bridge-summary.json"),
        },
    }
    _write_json(out / "theory-batch-governance-bridge-summary.json", report)
    return report


def _self_test() -> int:
    result = build_theory_batch_governance_bridge(
        theory_batch_summary="dist/theory-component-batch/2026-05-26/theory-component-batch-summary.json",
        load_audit_summary="dist/theory-component-batch-load-audit/2026-05-26/summary.json",
        output_dir="dist/theory-batch-governance-bridge/self-test",
        run_id="self-test",
    )
    assert result["promotion"]["counts"]["normalized_objects"] == 1000
    assert result["promotion"]["counts"]["candidate_load_ready"] == 1000
    assert result["promotion"]["counts"]["active_promotion_ready"] == 0
    assert result["embedding"]["input_embedding_rows"] == 1000
    assert result["embedding"]["planned_completion_rows"] == 1000
    print("ok")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--theory-batch-summary")
    parser.add_argument("--load-audit-summary")
    parser.add_argument("--output-dir", default="dist/theory-batch-governance-bridge")
    parser.add_argument("--run-id", default="theory-batch-governance")
    parser.add_argument("--default-profile", default="local-bge-small-en")
    parser.add_argument("--max-items-per-batch", type=int, default=256)
    parser.add_argument("--max-tokens-per-batch", type=int, default=24000)
    parser.add_argument("--stored-vectors-jsonl")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.theory_batch_summary or not args.load_audit_summary:
        parser.error("--theory-batch-summary and --load-audit-summary are required unless --self-test is used")
    result = build_theory_batch_governance_bridge(
        theory_batch_summary=args.theory_batch_summary,
        load_audit_summary=args.load_audit_summary,
        output_dir=args.output_dir,
        run_id=args.run_id,
        default_profile=args.default_profile,
        max_items_per_batch=args.max_items_per_batch,
        max_tokens_per_batch=args.max_tokens_per_batch,
        stored_vectors_jsonl=args.stored_vectors_jsonl,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
