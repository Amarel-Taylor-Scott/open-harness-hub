#!/usr/bin/env python3
"""Emit Postgres upsert SQL for factory JSONL outputs.

This is an offline bridge: JSONL remains the interchange/staging component,
while Postgres + pgvector is the canonical operational store. The script emits
SQL that can be reviewed, versioned, and applied by psql or a migration worker.
"""
from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def _sql_string(value: Any) -> str:
    if value is None:
        return "NULL"
    text = str(value)
    return "'" + text.replace("'", "''") + "'"


def _sql_json(value: Any) -> str:
    return _sql_string(json.dumps(value if value is not None else {}, sort_keys=True, ensure_ascii=False)) + "::jsonb"


def _sql_date(value: Any) -> str:
    return _sql_string(value) if value else "NULL"


def _stmt(table: str, columns: list[str], values: list[str], conflict: str, updates: list[str]) -> str:
    return (
        f"INSERT INTO {table} ({', '.join(columns)})\n"
        f"VALUES ({', '.join(values)})\n"
        f"ON CONFLICT ({conflict}) DO UPDATE SET\n  "
        + ",\n  ".join(updates)
        + ";\n"
    )


def _source_record(record: dict[str, Any]) -> str:
    columns = [
        "source_record_id", "source_url", "archive_url", "publisher", "license",
        "trust_tier", "privacy_boundary", "freshness", "retrieved_at",
        "effective_date", "content_hash", "body",
    ]
    values = [
        _sql_string(record.get("source_record_id")),
        _sql_string(record.get("source_url")),
        _sql_string(record.get("archive_url")),
        _sql_string(record.get("publisher")),
        _sql_string(record.get("license")),
        _sql_string(record.get("trust_tier")),
        _sql_string(record.get("privacy_boundary")),
        _sql_string(record.get("freshness")),
        _sql_date(record.get("retrieved_at")),
        _sql_date(record.get("effective_date")),
        _sql_string(record.get("content_hash")),
        _sql_json(record.get("body", {})),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("source_record", columns, values, "source_record_id", updates)


def _normalized_object(record: dict[str, Any]) -> str:
    columns = [
        "object_id", "object_type", "source_record_id", "title", "body",
        "trust_tier", "privacy_boundary", "quality_status", "review_status",
        "content_hash", "dedupe_cluster_id",
    ]
    values = [
        _sql_string(record.get("object_id")),
        _sql_string(record.get("object_type")),
        _sql_string(record.get("source_record_id")),
        _sql_string(record.get("title")),
        _sql_json(record.get("body", {})),
        _sql_string(record.get("trust_tier")),
        _sql_string(record.get("privacy_boundary")),
        _sql_string(record.get("quality_status")),
        _sql_string(record.get("review_status")),
        _sql_string(record.get("content_hash")),
        _sql_string(record.get("dedupe_cluster_id")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("normalized_object", columns, values, "object_id", updates)


def _entity(record: dict[str, Any]) -> str:
    columns = ["entity_id", "entity_type", "canonical_name", "aliases", "identifiers", "description", "confidence", "review_status"]
    values = [
        _sql_string(record.get("entity_id")),
        _sql_string(record.get("entity_type")),
        _sql_string(record.get("canonical_name")),
        _sql_json(record.get("aliases", [])),
        _sql_json(record.get("identifiers", [])),
        _sql_string(record.get("description")),
        str(record.get("confidence")) if record.get("confidence") is not None else "NULL",
        _sql_string(record.get("review_status")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("canonical_entity", columns, values, "entity_id", updates)


def _dedupe_cluster(record: dict[str, Any]) -> str:
    columns = ["dedupe_cluster_id", "canonical_object_id", "method", "threshold", "status"]
    values = [
        _sql_string(record.get("dedupe_cluster_id")),
        _sql_string(record.get("canonical_object_id")),
        _sql_string(",".join(record.get("methods", [])) if isinstance(record.get("methods"), list) else record.get("method")),
        _sql_json({"scores": record.get("scores", {}), "merge_policy": record.get("merge_policy", "")}),
        _sql_string(record.get("status")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("dedupe_cluster", columns, values, "dedupe_cluster_id", updates)


def _review_ticket(record: dict[str, Any]) -> str:
    columns = ["review_ticket_id", "object_id", "source_record_id", "review_type", "reason", "status", "created_at"]
    values = [
        _sql_string(record.get("review_ticket_id")),
        _sql_string(record.get("object_id")),
        _sql_string(record.get("source_record_id")),
        _sql_string(record.get("review_type")),
        _sql_string(record.get("reason")),
        _sql_string(record.get("status")),
        _sql_date(record.get("created_at")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("review_ticket", columns, values, "review_ticket_id", updates)


def _promotion_decision(record: dict[str, Any]) -> str:
    columns = [
        "decision_id", "object_id", "source_record_id", "score", "max_score",
        "decision", "criteria", "risk_flags", "review_reasons",
        "recommended_outputs", "created_at",
    ]
    values = [
        _sql_string(record.get("decision_id")),
        _sql_string(record.get("object_id")),
        _sql_string(record.get("source_record_id")),
        str(record.get("score", 0)),
        str(record.get("max_score", 100)),
        _sql_string(record.get("decision")),
        _sql_json(record.get("criteria", {})),
        _sql_json(record.get("risk_flags", [])),
        _sql_json(record.get("review_reasons", [])),
        _sql_json(record.get("recommended_outputs", [])),
        _sql_date(record.get("created_at")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("promotion_decision", columns, values, "decision_id", updates)


def _index_record(record: dict[str, Any]) -> str:
    columns = ["index_record_id", "index_kind", "subject_id", "subject_type", "text", "metadata", "embedding_model", "embedding_ref", "graph_edges"]
    values = [
        _sql_string(record.get("index_record_id")),
        _sql_string(record.get("index_kind")),
        _sql_string(record.get("subject_id")),
        _sql_string(record.get("subject_type")),
        _sql_string(record.get("text")),
        _sql_json(record.get("metadata", {})),
        _sql_string(record.get("embedding_model")),
        _sql_string(record.get("embedding_ref")),
        _sql_json(record.get("graph_edges", [])),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]] + ["updated_at=now()"]
    return _stmt("index_record", columns, values, "index_record_id", updates)


def _partition_manifest(record: dict[str, Any]) -> str:
    columns = [
        "partition_id", "partition_kind", "run_id", "source_surface_id", "tenant_id",
        "object_count", "shard_paths", "index_delta_paths", "schema_versions",
        "content_hash", "trust_boundary", "privacy_summary", "quality_summary",
        "created", "updated",
    ]
    values = [
        _sql_string(record.get("partition_id")),
        _sql_string(record.get("partition_kind")),
        _sql_string(record.get("run_id")),
        _sql_string(record.get("source_surface_id")),
        _sql_string(record.get("tenant_id")),
        str(record.get("object_count", 0)),
        _sql_json(record.get("shard_paths", [])),
        _sql_json(record.get("index_delta_paths", [])),
        _sql_json(record.get("schema_versions", {})),
        _sql_string(record.get("content_hash")),
        _sql_string(record.get("trust_boundary")),
        _sql_json(record.get("privacy_summary", {})),
        _sql_json(record.get("quality_summary", {})),
        _sql_date(record.get("created")),
        _sql_date(record.get("updated")),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("partition_manifest", columns, values, "partition_id", updates)


def _index_delta(record: dict[str, Any]) -> str:
    index_record = record.get("index_record") if isinstance(record.get("index_record"), dict) else {}
    columns = [
        "delta_id", "partition_id", "run_id", "operation", "index_record_id",
        "index_record", "sequence", "created", "content_hash", "replay_policy",
    ]
    values = [
        _sql_string(record.get("delta_id")),
        _sql_string(record.get("partition_id")),
        _sql_string(record.get("run_id")),
        _sql_string(record.get("operation")),
        _sql_string(index_record.get("index_record_id")),
        _sql_json(index_record),
        str(record.get("sequence", 0)),
        _sql_date(record.get("created")),
        _sql_string(record.get("content_hash")),
        _sql_json(record.get("replay_policy", {})),
    ]
    updates = [f"{col}=EXCLUDED.{col}" for col in columns[1:]]
    return _stmt("index_delta", columns, values, "delta_id", updates)


KIND_TO_EMITTER = {
    "source_record": _source_record,
    "normalized_object": _normalized_object,
    "entity": _entity,
    "dedupe_cluster": _dedupe_cluster,
    "review_ticket": _review_ticket,
    "promotion_decision": _promotion_decision,
    "index_record": _index_record,
    "index_delta": _index_delta,
}


def emit_sql(
    *,
    output_path: str,
    source_records: list[str] | None = None,
    normalized_objects: list[str] | None = None,
    entities: list[str] | None = None,
    dedupe_clusters: list[str] | None = None,
    review_tickets: list[str] | None = None,
    promotion_decisions: list[str] | None = None,
    index_records: list[str] | None = None,
    partition_manifests: list[str] | None = None,
    index_deltas: list[str] | None = None,
) -> dict[str, Any]:
    sections: list[tuple[str, list[str], Any]] = [
        ("source_record", source_records or [], _source_record),
        ("normalized_object", normalized_objects or [], _normalized_object),
        ("entity", entities or [], _entity),
        ("dedupe_cluster", dedupe_clusters or [], _dedupe_cluster),
        ("review_ticket", review_tickets or [], _review_ticket),
        ("promotion_decision", promotion_decisions or [], _promotion_decision),
        ("index_record", index_records or [], _index_record),
        ("partition_manifest", partition_manifests or [], _partition_manifest),
        ("index_delta", index_deltas or [], _index_delta),
    ]
    statements: list[str] = [
        "-- Generated by scripts/db/factory_jsonl_to_postgres.py",
        "BEGIN;",
    ]
    counts: dict[str, int] = {}
    for kind, paths, emitter in sections:
        counts[kind] = 0
        for raw_path in paths:
            path = Path(raw_path)
            if kind == "partition_manifest":
                records = [_read_json(path)]
            else:
                records = _read_jsonl(path)
            if records:
                statements.append(f"\n-- {kind}: {path}")
            for record in records:
                statements.append(emitter(record))
                counts[kind] += 1
    statements.append("COMMIT;\n")
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(statements), encoding="utf-8")
    return {"ok": True, "output_path": str(out), "counts": counts}


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "source.jsonl"
        source.write_text(json.dumps({
            "source_record_id": "source/demo/1",
            "source_type": "user_upload",
            "publisher": "synthetic",
            "license": "CC-BY-4.0",
            "retrieved_at": "2026-05-25T00:00:00Z",
            "body": {"task_family": "Demo"},
        }) + "\n", encoding="utf-8")
        obj = base / "objects.jsonl"
        obj.write_text(json.dumps({
            "object_id": "task/demo",
            "object_type": "task",
            "source_record_id": "source/demo/1",
            "title": "Demo task",
            "body": {"workflow_steps": ["Inspect"]},
            "provenance": {"source_url": "demo", "publisher": "synthetic", "license": "CC-BY-4.0"},
        }) + "\n", encoding="utf-8")
        out = base / "load.sql"
        result = emit_sql(output_path=str(out), source_records=[str(source)], normalized_objects=[str(obj)])
        assert out.exists()
        text = out.read_text(encoding="utf-8")
        assert "INSERT INTO source_record" in text
        assert "INSERT INTO normalized_object" in text
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit Postgres upsert SQL from factory JSONL outputs.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output", required=False)
    parser.add_argument("--source-records", nargs="*", default=[])
    parser.add_argument("--normalized-objects", nargs="*", default=[])
    parser.add_argument("--entities", nargs="*", default=[])
    parser.add_argument("--dedupe-clusters", nargs="*", default=[])
    parser.add_argument("--review-tickets", nargs="*", default=[])
    parser.add_argument("--promotion-decisions", nargs="*", default=[])
    parser.add_argument("--index-records", nargs="*", default=[])
    parser.add_argument("--partition-manifests", nargs="*", default=[])
    parser.add_argument("--index-deltas", nargs="*", default=[])
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.output:
        parser.error("--output is required")
    result = emit_sql(
        output_path=args.output,
        source_records=args.source_records,
        normalized_objects=args.normalized_objects,
        entities=args.entities,
        dedupe_clusters=args.dedupe_clusters,
        review_tickets=args.review_tickets,
        promotion_decisions=args.promotion_decisions,
        index_records=args.index_records,
        partition_manifests=args.partition_manifests,
        index_deltas=args.index_deltas,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
