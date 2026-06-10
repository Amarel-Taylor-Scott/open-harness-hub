#!/usr/bin/env python3
"""Summarize a source-surface factory execution across partitions and load gates."""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


ROW_FILES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "index_record": "index-records.jsonl",
    "review_ticket": "review-tickets.jsonl",
}


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


def _read_jsonl(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    candidate = Path(path)
    if not candidate.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(candidate.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{candidate}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _row_counts(row_dir: str | Path | None) -> dict[str, int]:
    if not row_dir:
        return {}
    base = Path(row_dir)
    return {family: _count_jsonl(base / filename) for family, filename in ROW_FILES.items()}


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _promotion_counts(load_plan: dict[str, Any]) -> dict[str, int]:
    summary = load_plan.get("promotion_summary") if isinstance(load_plan.get("promotion_summary"), dict) else {}
    return {
        "promotion_decisions": int(summary.get("promotion_decisions", 0) or 0),
        "hold": int(summary.get("hold", 0) or 0),
        "promote_candidate": int(summary.get("promote_candidate", 0) or 0),
        "review_before_promotion": int(summary.get("review_before_promotion", 0) or 0),
        "reject": int(summary.get("reject", 0) or 0),
        "promotion_review_tickets": int(summary.get("review_tickets", 0) or 0),
        "promotion_index_records": int(summary.get("index_records", 0) or 0),
    }


def _load_counts(load_plan: dict[str, Any]) -> dict[str, int]:
    bulk = load_plan.get("bulk_manifest") if isinstance(load_plan.get("bulk_manifest"), dict) else {}
    counts = bulk.get("counts") if isinstance(bulk.get("counts"), dict) else {}
    return {str(key): int(value) for key, value in sorted(counts.items()) if isinstance(value, int)}


def summarize_source_surface_execution(
    *,
    partitions_jsonl: str | Path,
    jobs_jsonl: str | Path | None = None,
    replay_records_jsonl: str | Path | None = None,
    row_dir: str | Path | None = None,
    load_plan_manifest: str | Path | None = None,
    catalog_id_index: str | Path | None = "dist/catalog-component-ids.json",
    output: str | Path | None = None,
    run_id: str = "source-surface-execution-summary",
) -> dict[str, Any]:
    partitions = _read_jsonl(partitions_jsonl)
    jobs = _read_jsonl(jobs_jsonl)
    replay_records = _read_jsonl(replay_records_jsonl)
    rows = _row_counts(row_dir)
    load_plan = _read_json(load_plan_manifest)
    catalog_index = _read_json(catalog_id_index)

    source_surface_ids = sorted({str(row.get("surface_id")) for row in partitions if row.get("surface_id")})
    by_surface: dict[str, dict[str, Any]] = {}
    for partition in partitions:
        surface_id = str(partition.get("surface_id") or "unknown")
        item = by_surface.setdefault(surface_id, {
            "partition_count": 0,
            "max_records": 0,
            "risk_tiers": {},
            "verticals": {},
            "expected_objects": {},
        })
        item["partition_count"] += 1
        item["max_records"] += int(partition.get("max_records", 0) or 0)
        risk = str(partition.get("risk_tier") or "unknown")
        item["risk_tiers"][risk] = item["risk_tiers"].get(risk, 0) + 1
        vertical = str(partition.get("vertical") or "unknown")
        item["verticals"][vertical] = item["verticals"].get(vertical, 0) + 1
        for expected in partition.get("expected_objects", []) or []:
            expected = str(expected)
            item["expected_objects"][expected] = item["expected_objects"].get(expected, 0) + 1

    preflight = load_plan.get("preflight_report") if isinstance(load_plan.get("preflight_report"), dict) else {}
    bulk = load_plan.get("bulk_manifest") if isinstance(load_plan.get("bulk_manifest"), dict) else {}
    generated_total = sum(rows.values())
    promotion = _promotion_counts(load_plan)
    total_review_tickets = int(rows.get("review_ticket", 0)) + promotion["promotion_review_tickets"]

    summary = {
        "run_id": run_id,
        "generated_at": _utc_now(),
        "catalog": {
            "component_id_index": str(catalog_id_index) if catalog_id_index else "",
            "manifest_count": catalog_index.get("component_count"),
            "meaning": "curated YAML components, not total generated object rows",
        },
        "source_surfaces": {
            "count": len(source_surface_ids),
            "ids": source_surface_ids,
            "by_surface": by_surface,
        },
        "partitions": {
            "count": len(partitions),
            "by_risk_tier": _count_by(partitions, "risk_tier"),
            "by_status": _count_by(partitions, "status"),
        },
        "jobs": {
            "count": len(jobs),
            "by_type": _count_by(jobs, "job_type"),
            "replay_records": len(replay_records),
            "replay_by_type": _count_by(replay_records, "job_type"),
        },
        "generated_rows": {
            "total": generated_total,
            "counts_by_family": rows,
            "row_dir": str(row_dir) if row_dir else "",
        },
        "promotion": promotion,
        "review": {
            "initial_review_tickets": int(rows.get("review_ticket", 0)),
            "promotion_review_tickets": promotion["promotion_review_tickets"],
            "total_review_tickets": total_review_tickets,
            "review_ticket_ratio_to_normalized_objects": (
                round(total_review_tickets / rows["normalized_object"], 4)
                if rows.get("normalized_object")
                else 0
            ),
        },
        "load_readiness": {
            "preflight_ok": bool(preflight.get("ok")),
            "preflight_issue_count": int(preflight.get("issue_count", 0) or 0),
            "bulk_ok": bool(bulk.get("ok")),
            "load_sql": bulk.get("load_sql", ""),
            "load_command": bulk.get("load_command", ""),
            "bulk_counts": _load_counts(load_plan),
        },
        "safety": {
            "source_bodies_fetched": False,
            "raw_private_data_stored": False,
            "insurance_scope_excluded": True,
            "publication_model": "metadata and generated candidates are held/reviewed before promotion",
        },
    }
    if output:
        _write_json(output, summary)
    return summary


def _self_test() -> int:
    base = Path("dist/source-surface-scan-partitions/seed")
    if not base.exists():
        raise FileNotFoundError("dist/source-surface-scan-partitions/seed is required for this self-test")
    summary = summarize_source_surface_execution(
        partitions_jsonl=base / "source-surface-scan-partitions.jsonl",
        jobs_jsonl=base / "jobs" / "public-source-scan-jobs.jsonl",
        replay_records_jsonl=base / "replay" / "job-run-records.jsonl",
        row_dir=base / "rows",
        load_plan_manifest=base / "load-plan" / "load-plan-manifest.json",
        run_id="self-test",
    )
    assert summary["partitions"]["count"] > 0
    assert summary["generated_rows"]["counts_by_family"]["normalized_object"] > 0
    assert summary["load_readiness"]["preflight_ok"] is True
    print(json.dumps({"ok": True, "normalized_objects": summary["generated_rows"]["counts_by_family"]["normalized_object"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize source-surface partition execution and load readiness.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--partitions-jsonl")
    parser.add_argument("--jobs-jsonl")
    parser.add_argument("--replay-records-jsonl")
    parser.add_argument("--row-dir")
    parser.add_argument("--load-plan-manifest")
    parser.add_argument("--catalog-id-index", default="dist/catalog-component-ids.json")
    parser.add_argument("--output")
    parser.add_argument("--run-id", default="source-surface-execution-summary")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.partitions_jsonl:
        parser.error("--partitions-jsonl is required unless --self-test is used")
    result = summarize_source_surface_execution(
        partitions_jsonl=args.partitions_jsonl,
        jobs_jsonl=args.jobs_jsonl,
        replay_records_jsonl=args.replay_records_jsonl,
        row_dir=args.row_dir,
        load_plan_manifest=args.load_plan_manifest,
        catalog_id_index=args.catalog_id_index,
        output=args.output,
        run_id=args.run_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
