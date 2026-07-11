#!/usr/bin/env python3
"""Merge daily component partitions into a deduped bulk-load audit package."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

from scripts.db.factory_jsonl_bulk_copy import export_bulk
from scripts.db.factory_jsonl_relationship_preflight import preflight
from scripts.db.staged_vs_committed_load_audit import audit_staged_vs_committed_load


ROW_FILES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "index_record": "index-records.jsonl",
}

PRIMARY_KEYS = {
    "source_record": ("source_record_id",),
    "normalized_object": ("object_id",),
    "canonical_entity": ("entity_id",),
    "object_entity_ref": ("object_id", "entity_id", "role"),
    "dedupe_cluster": ("dedupe_cluster_id",),
    "review_ticket": ("review_ticket_id",),
    "label_assignment": ("label_id",),
    "dimension_value": ("dimension_id",),
    "object_embedding": ("embedding_id",),
    "index_record": ("index_record_id",),
}

EXPORT_ARGS = {
    "source_record": "source_records",
    "normalized_object": "normalized_objects",
    "canonical_entity": "canonical_entities",
    "object_entity_ref": "object_entity_refs",
    "dedupe_cluster": "dedupe_clusters",
    "review_ticket": "review_tickets",
    "label_assignment": "label_assignments",
    "dimension_value": "dimension_values",
    "object_embedding": "object_embeddings",
    "index_record": "index_records",
}

PREFLIGHT_ARGS = {
    "source_record": "source_records",
    "normalized_object": "normalized_objects",
    "canonical_entity": "canonical_entities",
    "object_entity_ref": "object_entity_refs",
    "dedupe_cluster": "dedupe_clusters",
    "review_ticket": "review_tickets",
    "label_assignment": "label_assignments",
    "dimension_value": "dimension_values",
    "object_embedding": "object_embeddings",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
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


def _pk(table: str, row: dict[str, Any]) -> tuple[str, ...]:
    values = tuple(str(row.get(field, "")) for field in PRIMARY_KEYS[table])
    if any(not value for value in values):
        raise ValueError(f"{table} row missing primary key fields {PRIMARY_KEYS[table]}: {row}")
    return values


def _hash_rows(rows_by_table: dict[str, list[dict[str, Any]]]) -> str:
    digest = hashlib.sha256()
    for table in sorted(rows_by_table):
        digest.update(table.encode("utf-8"))
        for row in rows_by_table[table]:
            digest.update(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8"))
    return digest.hexdigest()


def _rows_dir(partition: Path) -> Path:
    candidate = partition / "rows"
    return candidate if candidate.exists() else partition


def _merge_partitions(partitions: list[Path]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    merged: dict[str, dict[tuple[str, ...], dict[str, Any]]] = {table: {} for table in ROW_FILES}
    raw_counts = {table: 0 for table in ROW_FILES}
    partition_summaries: list[dict[str, Any]] = []

    for partition in partitions:
        rows_dir = _rows_dir(partition)
        summary = {
            "partition": str(partition),
            "rows_dir": str(rows_dir),
            "raw_counts": {},
            "missing_files": [],
        }
        for table, filename in ROW_FILES.items():
            path = rows_dir / filename
            if not path.exists():
                summary["missing_files"].append(str(path))
                continue
            rows = _read_jsonl(path)
            summary["raw_counts"][table] = len(rows)
            raw_counts[table] += len(rows)
            for row in rows:
                merged[table][_pk(table, row)] = row
        partition_summaries.append(summary)

    merged_rows = {
        table: [rows[key] for key in sorted(rows)]
        for table, rows in merged.items()
    }
    unique_counts = {table: len(rows) for table, rows in merged_rows.items()}
    duplicate_counts = {
        table: raw_counts[table] - unique_counts.get(table, 0)
        for table in ROW_FILES
    }
    return merged_rows, {
        "partition_count": len(partitions),
        "partitions": partition_summaries,
        "raw_counts": raw_counts,
        "unique_counts": unique_counts,
        "duplicate_counts": duplicate_counts,
        "raw_total": sum(raw_counts.values()),
        "unique_total": sum(unique_counts.values()),
        "duplicate_total": sum(duplicate_counts.values()),
    }


def build_daily_partition_load_audit(
    *,
    partitions: list[str | Path],
    output_dir: str | Path,
    run_id: str = "daily-partition-load-audit",
) -> dict[str, Any]:
    out = Path(output_dir)
    partition_paths = [Path(partition) for partition in partitions]
    merged_rows, merge_report = _merge_partitions(partition_paths)

    merged_dir = out / "merged-jsonl"
    merged_paths: dict[str, str] = {}
    for table, rows in merged_rows.items():
        path = merged_dir / ROW_FILES[table]
        _write_jsonl(path, rows)
        merged_paths[table] = str(path)

    preflight_kwargs = {
        arg_name: [merged_paths[table]]
        for table, arg_name in PREFLIGHT_ARGS.items()
    }
    preflight_report = preflight(**preflight_kwargs)

    export_kwargs = {
        arg_name: [merged_paths[table]]
        for table, arg_name in EXPORT_ARGS.items()
    }
    bulk_manifest = export_bulk(output_dir=str(out / "bulk-copy"), **export_kwargs)

    load_plan_manifest = {
        "ok": bool(preflight_report.get("ok")) and bool(bulk_manifest.get("ok")),
        "run_id": run_id,
        "generated_at": _utc_now(),
        "partition_inputs": [str(path) for path in partition_paths],
        "merge_report": merge_report,
        "merged_jsonl_paths": merged_paths,
        "preflight_report": preflight_report,
        "bulk_manifest": bulk_manifest,
        "content_hash": _hash_rows(merged_rows),
        "safety": {
            "raw_private_data_stored": False,
            "source_bodies_required_for_audit": False,
            "insurance_scope_excluded": True,
            "load_sql_is_side_effect_free_until_operator_runs_psql": True,
        },
    }
    load_plan_path = out / "load-plan-manifest.json"
    _write_json(load_plan_path, load_plan_manifest)

    staged_audit = audit_staged_vs_committed_load(
        load_plan_manifest=load_plan_path,
        output=out / "staged-vs-committed-audit.json",
        run_id=run_id,
    )
    result = {
        "ok": load_plan_manifest["ok"] and staged_audit["audit_status"] == "staged_only",
        "run_id": run_id,
        "output_dir": str(out),
        "load_plan_manifest": str(load_plan_path),
        "staged_audit": str(out / "staged-vs-committed-audit.json"),
        "merge_report": merge_report,
        "preflight": {
            "ok": preflight_report.get("ok"),
            "issue_count": preflight_report.get("issue_count"),
        },
        "bulk_manifest": {
            "load_sql": bulk_manifest.get("load_sql"),
            "load_command": bulk_manifest.get("load_command"),
            "counts": bulk_manifest.get("counts"),
        },
        "audit_status": staged_audit["audit_status"],
    }
    _write_json(out / "summary.json", result)
    return result


def _self_test() -> int:
    partitions = [
        _resource("dist/daily-component-batch/2026-05-26"),
        _resource("dist/daily-component-batch/2026-05-27"),
    ]
    if not all(path.exists() for path in partitions):
        raise FileNotFoundError("daily component batch partitions for 2026-05-26 and 2026-05-27 are required")
    output_dir = _resource("dist/daily-component-batch-load-audit/self-test").absolute()
    result = build_daily_partition_load_audit(partitions=partitions, output_dir=output_dir, run_id="self-test")
    assert result["preflight"]["ok"] is True
    assert result["audit_status"] == "staged_only"
    assert result["merge_report"]["unique_counts"]["normalized_object"] == 2000
    assert result["merge_report"]["unique_counts"]["index_record"] == 10000
    print(json.dumps({"ok": True, "unique_total": result["merge_report"]["unique_total"]}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--partition", action="append", default=[], help="Daily partition directory. Repeat for multiple partitions.")
    parser.add_argument("--output-dir", default="dist/daily-component-batch-load-audit")
    parser.add_argument("--run-id", default="daily-partition-load-audit")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.partition:
        parser.error("--partition is required unless --self-test is used")
    result = build_daily_partition_load_audit(partitions=args.partition, output_dir=args.output_dir, run_id=args.run_id)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
