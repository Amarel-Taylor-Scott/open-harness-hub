#!/usr/bin/env python3
"""Preflight relationship checks for generated-object JSONL shards.

This validates local shard consistency before a bulk load reaches Postgres.
It intentionally avoids database access so factory workers can run it in cheap
CI, queue workers, or local review loops.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _read_jsonl(path: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    source = Path(path)
    for line_no, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{source}:{line_no}: expected JSON object")
        value["_preflight_path"] = str(source)
        value["_preflight_line"] = line_no
        records.append(value)
    return records


def _load_many(paths: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        records.extend(_read_jsonl(path))
    return records


def _id_set(records: list[dict[str, Any]], field: str) -> set[str]:
    return {str(record[field]) for record in records if record.get(field)}


def _issue(record: dict[str, Any], field: str, value: Any, message: str) -> dict[str, Any]:
    return {
        "path": record.get("_preflight_path"),
        "line": record.get("_preflight_line"),
        "field": field,
        "value": value,
        "message": message,
    }


def preflight(
    *,
    source_records: list[str] | None = None,
    normalized_objects: list[str] | None = None,
    canonical_entities: list[str] | None = None,
    object_entity_refs: list[str] | None = None,
    dedupe_clusters: list[str] | None = None,
    review_tickets: list[str] | None = None,
    label_assignments: list[str] | None = None,
    dimension_values: list[str] | None = None,
    object_embeddings: list[str] | None = None,
) -> dict[str, Any]:
    sources = _load_many(source_records or [])
    objects = _load_many(normalized_objects or [])
    entities = _load_many(canonical_entities or [])
    refs = _load_many(object_entity_refs or [])
    clusters = _load_many(dedupe_clusters or [])
    tickets = _load_many(review_tickets or [])
    labels = _load_many(label_assignments or [])
    dimensions = _load_many(dimension_values or [])
    embeddings = _load_many(object_embeddings or [])

    source_ids = _id_set(sources, "source_record_id")
    object_ids = _id_set(objects, "object_id")
    entity_ids = _id_set(entities, "entity_id")
    cluster_ids = _id_set(clusters, "dedupe_cluster_id")

    issues: list[dict[str, Any]] = []

    for record in objects:
        source_id = record.get("source_record_id")
        if source_id and str(source_id) not in source_ids:
            issues.append(_issue(record, "source_record_id", source_id, "normalized object references a missing source_record"))
        cluster_id = record.get("dedupe_cluster_id")
        if cluster_id and str(cluster_id) not in cluster_ids:
            issues.append(_issue(record, "dedupe_cluster_id", cluster_id, "normalized object references a missing dedupe_cluster"))

    for record in clusters:
        object_id = record.get("canonical_object_id")
        if object_id and str(object_id) not in object_ids:
            issues.append(_issue(record, "canonical_object_id", object_id, "dedupe cluster references a missing normalized object"))

    for record in refs:
        object_id = record.get("object_id")
        entity_id = record.get("entity_id")
        if object_id and str(object_id) not in object_ids:
            issues.append(_issue(record, "object_id", object_id, "object_entity_ref references a missing normalized object"))
        if entity_id and str(entity_id) not in entity_ids:
            issues.append(_issue(record, "entity_id", entity_id, "object_entity_ref references a missing canonical entity"))

    for record in tickets:
        object_id = record.get("object_id")
        source_id = record.get("source_record_id")
        if object_id and str(object_id) not in object_ids:
            issues.append(_issue(record, "object_id", object_id, "review ticket references a missing normalized object"))
        if source_id and str(source_id) not in source_ids:
            issues.append(_issue(record, "source_record_id", source_id, "review ticket references a missing source_record"))

    for collection, id_field in ((labels, "label_id"), (dimensions, "dimension_id"), (embeddings, "embedding_id")):
        for record in collection:
            subject_id = record.get("subject_id")
            subject_type = record.get("subject_type")
            if subject_type in (None, "", "normalized_object") and subject_id and str(subject_id) not in object_ids:
                issues.append(_issue(record, "subject_id", subject_id, f"{id_field} references a missing normalized object"))

    counts = {
        "source_record": len(sources),
        "normalized_object": len(objects),
        "canonical_entity": len(entities),
        "object_entity_ref": len(refs),
        "dedupe_cluster": len(clusters),
        "review_ticket": len(tickets),
        "label_assignment": len(labels),
        "dimension_value": len(dimensions),
        "object_embedding": len(embeddings),
    }
    return {
        "ok": not issues,
        "counts": counts,
        "issue_count": len(issues),
        "issues": issues,
    }


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preflight generated-object JSONL relationships before Postgres bulk load.")
    parser.add_argument("--source-records", nargs="*", default=[])
    parser.add_argument("--normalized-objects", nargs="*", default=[])
    parser.add_argument("--canonical-entities", nargs="*", default=[])
    parser.add_argument("--object-entity-refs", nargs="*", default=[])
    parser.add_argument("--dedupe-clusters", nargs="*", default=[])
    parser.add_argument("--review-tickets", nargs="*", default=[])
    parser.add_argument("--label-assignments", nargs="*", default=[])
    parser.add_argument("--dimension-values", nargs="*", default=[])
    parser.add_argument("--object-embeddings", nargs="*", default=[])
    args = parser.parse_args(argv)
    result = preflight(
        source_records=args.source_records,
        normalized_objects=args.normalized_objects,
        canonical_entities=args.canonical_entities,
        object_entity_refs=args.object_entity_refs,
        dedupe_clusters=args.dedupe_clusters,
        review_tickets=args.review_tickets,
        label_assignments=args.label_assignments,
        dimension_values=args.dimension_values,
        object_embeddings=args.object_embeddings,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
