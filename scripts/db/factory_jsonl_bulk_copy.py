#!/usr/bin/env python3
"""Export factory JSONL shards as CSV plus a psql bulk load script.

The row-by-row SQL emitter is useful for small reviewable seed batches. This
script is for large generated-object batches: it creates CSV files and a load
script that uses psql \copy into temporary staging tables, then upserts into
the canonical Postgres tables.
"""
from __future__ import annotations

import argparse
import csv
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


def _json(value: Any, default: Any) -> str:
    return json.dumps(value if value is not None else default, sort_keys=True, ensure_ascii=False)


def _str(value: Any) -> str:
    return "" if value is None else str(value)


TABLE_COLUMNS = {
    "source_record": [
        "source_record_id", "source_url", "archive_url", "publisher", "license",
        "trust_tier", "privacy_boundary", "freshness", "retrieved_at",
        "effective_date", "content_hash", "body",
    ],
    "normalized_object": [
        "object_id", "object_type", "source_record_id", "title", "body",
        "trust_tier", "privacy_boundary", "quality_status", "review_status",
        "content_hash", "dedupe_cluster_id",
    ],
    "promotion_decision": [
        "decision_id", "object_id", "source_record_id", "score", "max_score",
        "decision", "criteria", "risk_flags", "review_reasons",
        "recommended_outputs", "created_at",
    ],
    "index_record": [
        "index_record_id", "index_kind", "subject_id", "subject_type", "text",
        "metadata", "embedding_model", "embedding_ref", "graph_edges",
    ],
    "canonical_entity": [
        "entity_id", "entity_type", "canonical_name", "aliases", "identifiers",
        "description", "confidence", "review_status",
    ],
    "object_entity_ref": [
        "object_id", "entity_id", "role", "confidence",
    ],
    "dedupe_cluster": [
        "dedupe_cluster_id", "canonical_object_id", "method", "threshold",
        "status", "created_at",
    ],
    "review_ticket": [
        "review_ticket_id", "object_id", "source_record_id", "review_type",
        "reason", "status", "created_at",
    ],
    "label_assignment": [
        "label_id", "label_set", "label", "path", "subject_id", "subject_type",
        "confidence", "assigned_by", "assignment_method", "model_route_id",
        "provenance", "review_status",
    ],
    "dimension_value": [
        "dimension_id", "name", "subject_id", "subject_type", "value",
        "value_type", "scale", "confidence", "assigned_by", "assignment_method",
        "model_route_id", "provenance", "review_status",
    ],
    "object_embedding": [
        "embedding_id", "subject_id", "subject_type", "embedding_model",
        "text_hash", "text", "embedding", "metadata", "created_at",
    ],
}


def _source_record(record: dict[str, Any]) -> dict[str, str]:
    return {
        "source_record_id": _str(record.get("source_record_id")),
        "source_url": _str(record.get("source_url")),
        "archive_url": _str(record.get("archive_url")),
        "publisher": _str(record.get("publisher")),
        "license": _str(record.get("license")),
        "trust_tier": _str(record.get("trust_tier")),
        "privacy_boundary": _str(record.get("privacy_boundary")),
        "freshness": _str(record.get("freshness")),
        "retrieved_at": _str(record.get("retrieved_at")),
        "effective_date": _str(record.get("effective_date")),
        "content_hash": _str(record.get("content_hash")),
        "body": _json(record.get("body"), {}),
    }


def _normalized_object(record: dict[str, Any]) -> dict[str, str]:
    return {
        "object_id": _str(record.get("object_id")),
        "object_type": _str(record.get("object_type")),
        "source_record_id": _str(record.get("source_record_id")),
        "title": _str(record.get("title")),
        "body": _json(record.get("body"), {}),
        "trust_tier": _str(record.get("trust_tier")),
        "privacy_boundary": _str(record.get("privacy_boundary")),
        "quality_status": _str(record.get("quality_status")),
        "review_status": _str(record.get("review_status")),
        "content_hash": _str(record.get("content_hash")),
        "dedupe_cluster_id": _str(record.get("dedupe_cluster_id")),
    }


def _promotion_decision(record: dict[str, Any]) -> dict[str, str]:
    return {
        "decision_id": _str(record.get("decision_id")),
        "object_id": _str(record.get("object_id")),
        "source_record_id": _str(record.get("source_record_id")),
        "score": _str(record.get("score", 0)),
        "max_score": _str(record.get("max_score", 100)),
        "decision": _str(record.get("decision")),
        "criteria": _json(record.get("criteria"), {}),
        "risk_flags": _json(record.get("risk_flags"), []),
        "review_reasons": _json(record.get("review_reasons"), []),
        "recommended_outputs": _json(record.get("recommended_outputs"), []),
        "created_at": _str(record.get("created_at")),
    }


def _index_record(record: dict[str, Any]) -> dict[str, str]:
    return {
        "index_record_id": _str(record.get("index_record_id")),
        "index_kind": _str(record.get("index_kind")),
        "subject_id": _str(record.get("subject_id")),
        "subject_type": _str(record.get("subject_type")),
        "text": _str(record.get("text")),
        "metadata": _json(record.get("metadata"), {}),
        "embedding_model": _str(record.get("embedding_model")),
        "embedding_ref": _str(record.get("embedding_ref")),
        "graph_edges": _json(record.get("graph_edges"), []),
    }


def _canonical_entity(record: dict[str, Any]) -> dict[str, str]:
    return {
        "entity_id": _str(record.get("entity_id")),
        "entity_type": _str(record.get("entity_type")),
        "canonical_name": _str(record.get("canonical_name")),
        "aliases": _json(record.get("aliases"), []),
        "identifiers": _json(record.get("identifiers"), {}),
        "description": _str(record.get("description")),
        "confidence": _str(record.get("confidence")),
        "review_status": _str(record.get("review_status")),
    }


def _object_entity_ref(record: dict[str, Any]) -> dict[str, str]:
    return {
        "object_id": _str(record.get("object_id")),
        "entity_id": _str(record.get("entity_id")),
        "role": _str(record.get("role")),
        "confidence": _str(record.get("confidence")),
    }


def _dedupe_cluster(record: dict[str, Any]) -> dict[str, str]:
    return {
        "dedupe_cluster_id": _str(record.get("dedupe_cluster_id")),
        "canonical_object_id": _str(record.get("canonical_object_id")),
        "method": _str(record.get("method")),
        "threshold": _json(record.get("threshold"), {}),
        "status": _str(record.get("status")),
        "created_at": _str(record.get("created_at")),
    }


def _review_ticket(record: dict[str, Any]) -> dict[str, str]:
    return {
        "review_ticket_id": _str(record.get("review_ticket_id")),
        "object_id": _str(record.get("object_id")),
        "source_record_id": _str(record.get("source_record_id")),
        "review_type": _str(record.get("review_type")),
        "reason": _str(record.get("reason")),
        "status": _str(record.get("status")),
        "created_at": _str(record.get("created_at")),
    }


def _label_assignment(record: dict[str, Any]) -> dict[str, str]:
    return {
        "label_id": _str(record.get("label_id")),
        "label_set": _str(record.get("label_set")),
        "label": _str(record.get("label")),
        "path": _str(record.get("path")),
        "subject_id": _str(record.get("subject_id")),
        "subject_type": _str(record.get("subject_type")),
        "confidence": _str(record.get("confidence")),
        "assigned_by": _str(record.get("assigned_by")),
        "assignment_method": _str(record.get("assignment_method")),
        "model_route_id": _str(record.get("model_route_id")),
        "provenance": _json(record.get("provenance"), {}),
        "review_status": _str(record.get("review_status")),
    }


def _dimension_value(record: dict[str, Any]) -> dict[str, str]:
    return {
        "dimension_id": _str(record.get("dimension_id")),
        "name": _str(record.get("name")),
        "subject_id": _str(record.get("subject_id")),
        "subject_type": _str(record.get("subject_type")),
        "value": _json(record.get("value"), {}),
        "value_type": _str(record.get("value_type")),
        "scale": _str(record.get("scale")),
        "confidence": _str(record.get("confidence")),
        "assigned_by": _str(record.get("assigned_by")),
        "assignment_method": _str(record.get("assignment_method")),
        "model_route_id": _str(record.get("model_route_id")),
        "provenance": _json(record.get("provenance"), {}),
        "review_status": _str(record.get("review_status")),
    }


def _object_embedding(record: dict[str, Any]) -> dict[str, str]:
    return {
        "embedding_id": _str(record.get("embedding_id")),
        "subject_id": _str(record.get("subject_id")),
        "subject_type": _str(record.get("subject_type")),
        "embedding_model": _str(record.get("embedding_model")),
        "text_hash": _str(record.get("text_hash")),
        "text": _str(record.get("text")),
        "embedding": _str(record.get("embedding")),
        "metadata": _json(record.get("metadata"), {}),
        "created_at": _str(record.get("created_at")),
    }


NORMALIZERS = {
    "source_record": _source_record,
    "normalized_object": _normalized_object,
    "promotion_decision": _promotion_decision,
    "index_record": _index_record,
    "canonical_entity": _canonical_entity,
    "object_entity_ref": _object_entity_ref,
    "dedupe_cluster": _dedupe_cluster,
    "review_ticket": _review_ticket,
    "label_assignment": _label_assignment,
    "dimension_value": _dimension_value,
    "object_embedding": _object_embedding,
}


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _empty_to_null(expr: str) -> str:
    return f"NULLIF({expr}, '')"


def _json_cast(expr: str) -> str:
    return f"NULLIF({expr}, '')::jsonb"


def _numeric_cast(expr: str) -> str:
    return f"NULLIF({expr}, '')::numeric"


def _timestamp_cast(expr: str) -> str:
    return f"NULLIF({expr}, '')::timestamptz"


def _table_load_sql(table: str, csv_path: str) -> str:
    columns = TABLE_COLUMNS[table]
    temp = f"stage_{table}"
    column_defs = ",\n  ".join(f"{column} text" for column in columns)
    column_list = ", ".join(columns)

    if table == "source_record":
        select_values = [
            "source_record_id", _empty_to_null("source_url"), _empty_to_null("archive_url"),
            _empty_to_null("publisher"), _empty_to_null("license"), _empty_to_null("trust_tier"),
            _empty_to_null("privacy_boundary"), _empty_to_null("freshness"),
            "NULLIF(retrieved_at, '')::timestamptz", "NULLIF(effective_date, '')::date",
            _empty_to_null("content_hash"), _json_cast("body"),
        ]
        conflict_columns = ["source_record_id"]
    elif table == "normalized_object":
        select_values = [
            "object_id", "object_type", _empty_to_null("source_record_id"), "title",
            _json_cast("body"), _empty_to_null("trust_tier"), _empty_to_null("privacy_boundary"),
            _empty_to_null("quality_status"), _empty_to_null("review_status"),
            _empty_to_null("content_hash"), _empty_to_null("dedupe_cluster_id"),
        ]
        conflict_columns = ["object_id"]
    elif table == "promotion_decision":
        select_values = [
            "decision_id", _empty_to_null("object_id"), _empty_to_null("source_record_id"),
            _numeric_cast("score"), _numeric_cast("max_score"), "decision",
            _json_cast("criteria"), _json_cast("risk_flags"), _json_cast("review_reasons"),
            _json_cast("recommended_outputs"), _timestamp_cast("created_at"),
        ]
        conflict_columns = ["decision_id"]
    elif table == "index_record":
        select_values = [
            "index_record_id", "index_kind", "subject_id", _empty_to_null("subject_type"),
            "text", _json_cast("metadata"), _empty_to_null("embedding_model"),
            _empty_to_null("embedding_ref"), _json_cast("graph_edges"),
        ]
        conflict_columns = ["index_record_id"]
    elif table == "canonical_entity":
        select_values = [
            "entity_id", "entity_type", "canonical_name", _json_cast("aliases"),
            _json_cast("identifiers"), _empty_to_null("description"),
            _numeric_cast("confidence"), _empty_to_null("review_status"),
        ]
        conflict_columns = ["entity_id"]
    elif table == "object_entity_ref":
        select_values = [
            "object_id", "entity_id", "role", _numeric_cast("confidence"),
        ]
        conflict_columns = ["object_id", "entity_id", "role"]
    elif table == "dedupe_cluster":
        select_values = [
            "dedupe_cluster_id", _empty_to_null("canonical_object_id"),
            _empty_to_null("method"), _json_cast("threshold"), _empty_to_null("status"),
            _timestamp_cast("created_at"),
        ]
        conflict_columns = ["dedupe_cluster_id"]
    elif table == "review_ticket":
        select_values = [
            "review_ticket_id", _empty_to_null("object_id"), _empty_to_null("source_record_id"),
            "review_type", "reason", "status", _timestamp_cast("created_at"),
        ]
        conflict_columns = ["review_ticket_id"]
    elif table == "label_assignment":
        select_values = [
            "label_id", "label_set", "label", _empty_to_null("path"), "subject_id",
            _empty_to_null("subject_type"), _numeric_cast("confidence"),
            _empty_to_null("assigned_by"), _empty_to_null("assignment_method"),
            _empty_to_null("model_route_id"), _json_cast("provenance"),
            _empty_to_null("review_status"),
        ]
        conflict_columns = ["label_id"]
    elif table == "dimension_value":
        select_values = [
            "dimension_id", "name", "subject_id", _empty_to_null("subject_type"),
            _json_cast("value"), _empty_to_null("value_type"), _empty_to_null("scale"),
            _numeric_cast("confidence"), _empty_to_null("assigned_by"),
            _empty_to_null("assignment_method"), _empty_to_null("model_route_id"),
            _json_cast("provenance"), _empty_to_null("review_status"),
        ]
        conflict_columns = ["dimension_id"]
    elif table == "object_embedding":
        select_values = [
            "embedding_id", "subject_id", "subject_type", "embedding_model", "text_hash",
            "text", "NULLIF(embedding, '')::vector", _json_cast("metadata"),
            _timestamp_cast("created_at"),
        ]
        conflict_columns = ["embedding_id"]
    else:
        raise ValueError(f"Unsupported table: {table}")

    conflict = ", ".join(conflict_columns)
    updates = ",\n  ".join(
        f"{column}=EXCLUDED.{column}" for column in columns if column not in conflict_columns
    )
    if table == "index_record":
        updates += ",\n  updated_at=now()"
    if not updates:
        updates = f"{columns[-1]}=EXCLUDED.{columns[-1]}"

    return f"""
CREATE TEMP TABLE {temp} (
  {column_defs}
) ON COMMIT DROP;
\\copy {temp} ({column_list}) FROM '{csv_path}' WITH (FORMAT csv, HEADER true)
INSERT INTO {table} ({column_list})
SELECT {", ".join(select_values)}
FROM {temp}
ON CONFLICT ({conflict}) DO UPDATE SET
  {updates};
"""


def export_bulk(
    *,
    output_dir: str,
    source_records: list[str] | None = None,
    normalized_objects: list[str] | None = None,
    promotion_decisions: list[str] | None = None,
    index_records: list[str] | None = None,
    canonical_entities: list[str] | None = None,
    object_entity_refs: list[str] | None = None,
    dedupe_clusters: list[str] | None = None,
    review_tickets: list[str] | None = None,
    label_assignments: list[str] | None = None,
    dimension_values: list[str] | None = None,
    object_embeddings: list[str] | None = None,
    load_sql_name: str = "load.sql",
) -> dict[str, Any]:
    inputs = {
        "source_record": source_records or [],
        "normalized_object": normalized_objects or [],
        "dedupe_cluster": dedupe_clusters or [],
        "canonical_entity": canonical_entities or [],
        "object_entity_ref": object_entity_refs or [],
        "promotion_decision": promotion_decisions or [],
        "review_ticket": review_tickets or [],
        "label_assignment": label_assignments or [],
        "dimension_value": dimension_values or [],
        "object_embedding": object_embeddings or [],
        "index_record": index_records or [],
    }
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    csv_paths: dict[str, str] = {}
    sql_parts = [
        "-- Generated by scripts/db/factory_jsonl_bulk_copy.py",
        "-- Run with: psql \"$DATABASE_URL\" -f <this file>",
        "BEGIN;",
    ]
    for table, paths in inputs.items():
        rows: list[dict[str, str]] = []
        normalizer = NORMALIZERS[table]
        for raw_path in paths:
            for record in _read_jsonl(Path(raw_path)):
                rows.append(normalizer(record))
        counts[table] = len(rows)
        if not rows:
            continue
        csv_path = out_dir / f"{table}.csv"
        _write_csv(csv_path, TABLE_COLUMNS[table], rows)
        csv_paths[table] = str(csv_path)
        sql_parts.append(_table_load_sql(table, str(csv_path)))
    sql_parts.append("COMMIT;\n")
    load_sql_path = out_dir / load_sql_name
    load_sql_path.write_text("\n".join(sql_parts), encoding="utf-8")
    manifest = {
        "ok": True,
        "output_dir": str(out_dir),
        "load_sql": str(load_sql_path),
        "csv_paths": csv_paths,
        "counts": counts,
        "load_command": f'psql "$DATABASE_URL" -f {load_sql_path}',
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "source.jsonl"
        source.write_text(json.dumps({
            "source_record_id": "source/demo/1",
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
        }) + "\n", encoding="utf-8")
        entity = base / "entities.jsonl"
        entity.write_text(json.dumps({
            "entity_id": "entity/demo/publisher",
            "entity_type": "publisher",
            "canonical_name": "Synthetic Demo Publisher",
            "aliases": ["Demo Publisher"],
            "identifiers": {"namespace": "synthetic"},
            "confidence": 1,
            "review_status": "synthetic",
        }) + "\n", encoding="utf-8")
        ref = base / "refs.jsonl"
        ref.write_text(json.dumps({
            "object_id": "task/demo",
            "entity_id": "entity/demo/publisher",
            "role": "publisher",
            "confidence": 1,
        }) + "\n", encoding="utf-8")
        label = base / "labels.jsonl"
        label.write_text(json.dumps({
            "label_id": "label/demo/task",
            "label_set": "open-harness.capability",
            "label": "governance",
            "subject_id": "task/demo",
            "subject_type": "normalized_object",
            "confidence": 0.9,
            "provenance": {"source": "self-test"},
        }) + "\n", encoding="utf-8")
        out = base / "bulk"
        result = export_bulk(
            output_dir=str(out),
            source_records=[str(source)],
            normalized_objects=[str(obj)],
            canonical_entities=[str(entity)],
            object_entity_refs=[str(ref)],
            label_assignments=[str(label)],
        )
        assert Path(result["load_sql"]).exists()
        assert (out / "source_record.csv").exists()
        assert (out / "normalized_object.csv").exists()
        assert (out / "canonical_entity.csv").exists()
        assert (out / "object_entity_ref.csv").exists()
        assert (out / "label_assignment.csv").exists()
        text = Path(result["load_sql"]).read_text(encoding="utf-8")
        assert "\\copy stage_source_record" in text
        assert "ON CONFLICT (object_id)" in text
        assert "ON CONFLICT (object_id, entity_id, role)" in text
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export factory JSONL as bulk CSV plus psql load script.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--output-dir")
    parser.add_argument("--load-sql-name", default="load.sql")
    parser.add_argument("--source-records", nargs="*", default=[])
    parser.add_argument("--normalized-objects", nargs="*", default=[])
    parser.add_argument("--promotion-decisions", nargs="*", default=[])
    parser.add_argument("--index-records", nargs="*", default=[])
    parser.add_argument("--canonical-entities", nargs="*", default=[])
    parser.add_argument("--object-entity-refs", nargs="*", default=[])
    parser.add_argument("--dedupe-clusters", nargs="*", default=[])
    parser.add_argument("--review-tickets", nargs="*", default=[])
    parser.add_argument("--label-assignments", nargs="*", default=[])
    parser.add_argument("--dimension-values", nargs="*", default=[])
    parser.add_argument("--object-embeddings", nargs="*", default=[])
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.output_dir:
        parser.error("--output-dir is required")
    result = export_bulk(
        output_dir=args.output_dir,
        source_records=args.source_records,
        normalized_objects=args.normalized_objects,
        promotion_decisions=args.promotion_decisions,
        index_records=args.index_records,
        canonical_entities=args.canonical_entities,
        object_entity_refs=args.object_entity_refs,
        dedupe_clusters=args.dedupe_clusters,
        review_tickets=args.review_tickets,
        label_assignments=args.label_assignments,
        dimension_values=args.dimension_values,
        object_embeddings=args.object_embeddings,
        load_sql_name=args.load_sql_name,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
