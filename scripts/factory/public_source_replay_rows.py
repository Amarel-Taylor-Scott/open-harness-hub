#!/usr/bin/env python3
"""Emit canonical row-family JSONL from replayed public-source jobs.

This is the first concrete bridge from queue/replay metadata to loadable row
families. It uses only public blueprint metadata and deterministic transforms;
it does not fetch source bodies or publish scraped content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]

FILE_NAMES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "label_assignment": "label-assignments.jsonl",
    "dimension_value": "dimension-values.jsonl",
    "object_embedding": "object-embeddings.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "index_record": "index-records.jsonl",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _date_today() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _safe_slug(value: str, limit: int = 96) -> str:
    cleaned: list[str] = []
    for ch in value.lower():
        if ch.isalnum():
            cleaned.append(ch)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-")[:limit] or "item"


def _read_jsonl(path: str | Path | None) -> list[dict[str, Any]]:
    if not path:
        return []
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _source_record(job: dict[str, Any], now: str) -> dict[str, Any]:
    inputs = job.get("inputs") if isinstance(job.get("inputs"), dict) else {}
    policy = job.get("policy") if isinstance(job.get("policy"), dict) else {}
    blueprint_id = str(inputs.get("blueprint_id") or "unknown-blueprint")
    body = {
        "blueprint_id": blueprint_id,
        "title": inputs.get("title", blueprint_id),
        "vertical": inputs.get("vertical", ""),
        "source_patterns": inputs.get("source_patterns", []),
        "publisher_classes": inputs.get("publisher_classes", []),
        "expected_objects": inputs.get("expected_objects", []),
        "required_stages": inputs.get("required_stages", []),
        "review_triggers": inputs.get("review_triggers", []),
        "source_body_stored": False,
        "raw_private_data_stored": False,
    }
    return {
        "source_record_id": str(job.get("source_record_id") or f"source/public-source-blueprint/{blueprint_id}"),
        "source_type": "api_record",
        "source_url": "",
        "archive_url": "",
        "publisher": "OpenHubForAI public-source blueprint catalog",
        "license": "CC-BY-4.0",
        "trust_tier": str(policy.get("trust_tier") or "official_or_public"),
        "privacy_boundary": str(policy.get("privacy_boundary") or "public"),
        "freshness": "volatile",
        "retrieved_at": now,
        "effective_date": _date_today(),
        "content_hash": _hash_json(body),
        "language": "en",
        "jurisdiction": "",
        "body": body,
        "storage_ref": {
            "bucket": "not-captured",
            "key": f"public-source-blueprints/{_safe_slug(blueprint_id)}",
            "media_type": "application/json",
            "size_bytes": 0,
        },
    }


def _entity(entity_type: str, name: str, *, source_record_id: str, description: str = "") -> dict[str, Any]:
    slug = _safe_slug(f"{entity_type}-{name}")
    return {
        "entity_id": f"entity/public-source/{slug}",
        "entity_type": entity_type,
        "canonical_name": name,
        "aliases": sorted({name, name.replace("_", " "), name.replace(".", " ")}),
        "identifiers": [{"scheme": "open_harness_public_source", "value": hashlib.sha256(f"{entity_type}:{name}".encode()).hexdigest()[:20]}],
        "description": description,
        "source_record_ids": [source_record_id],
        "confidence": 0.86,
        "review_status": "generated_candidate",
    }


def _label(subject_id: str, label: str, path: str, *, label_set: str = "hierarchical") -> dict[str, Any]:
    key = f"{subject_id}:{label_set}:{path}:{label}"
    return {
        "label_id": f"label/{hashlib.sha256(key.encode()).hexdigest()[:20]}",
        "label_set": label_set,
        "label": label,
        "path": path,
        "subject_id": subject_id,
        "subject_type": "normalized_object",
        "confidence": 0.84,
        "assigned_by": "public-source-replay-row-emitter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "public_source_job_replay"},
        "review_status": "generated_candidate",
    }


def _dimension(subject_id: str, name: str, value: Any, value_type: str, *, scale: str = "") -> dict[str, Any]:
    key = f"{subject_id}:{name}:{json.dumps(value, sort_keys=True, ensure_ascii=False)}"
    return {
        "dimension_id": f"dimension/{hashlib.sha256(key.encode()).hexdigest()[:20]}",
        "name": name,
        "subject_id": subject_id,
        "subject_type": "normalized_object",
        "value": value,
        "value_type": value_type,
        "scale": scale,
        "confidence": 0.82,
        "assigned_by": "public-source-replay-row-emitter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "public_source_job_replay"},
        "review_status": "generated_candidate",
    }


def _object_id(blueprint_id: str, expected_object: str) -> str:
    return f"object/public-source/{_safe_slug(blueprint_id)}/{_safe_slug(expected_object)}"


def _embedding(object_id: str, text: str, bucket: str, now: str) -> dict[str, Any]:
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "embedding_id": f"embedding/{hashlib.sha256(f'{object_id}:{text_hash}'.encode()).hexdigest()[:20]}",
        "subject_id": object_id,
        "subject_type": "normalized_object",
        "embedding_model": "stub:deterministic-public-source-v1",
        "text_hash": text_hash,
        "text": text,
        "embedding": "",
        "metadata": {
            "bucket": bucket,
            "actual_embedding_required": True,
            "source": "public_source_replay_rows",
        },
        "created_at": now,
    }


def _index_records(object_id: str, text: str, metadata: dict[str, Any], embedding_id: str, graph_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for kind in ["keyword", "vector", "graph", "facet", "quality"]:
        rows.append({
            "index_record_id": f"index/{kind}/{_safe_slug(object_id)}",
            "index_kind": kind,
            "subject_id": object_id,
            "subject_type": "normalized_object",
            "text": text,
            "metadata": metadata,
            "embedding_model": "stub:deterministic-public-source-v1" if kind == "vector" else "",
            "embedding_ref": embedding_id if kind == "vector" else "",
            "graph_edges": graph_edges if kind == "graph" else [],
        })
    return rows


def _jobs_by_id(jobs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(job.get("job_id")): job for job in jobs if job.get("job_id")}


def build_replay_row_families(
    *,
    job_run_records: list[dict[str, Any]],
    jobs: list[dict[str, Any]] | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    now = _utc_now()
    excluded_scopes = excluded_scopes or ["insurance"]
    original_jobs = _jobs_by_id(jobs or [])
    rows: dict[str, list[dict[str, Any]]] = {family: [] for family in FILE_NAMES}
    source_records: dict[str, dict[str, Any]] = {}
    entities: dict[str, dict[str, Any]] = {}
    refs: dict[tuple[str, str, str], dict[str, Any]] = {}

    ingest_runs = [record for record in job_run_records if record.get("job_type") == "source_ingest"]
    for run in ingest_runs:
        job = original_jobs.get(str(run.get("job_id")), {})
        inputs = job.get("inputs") if isinstance(job.get("inputs"), dict) else {}
        policy = job.get("policy") if isinstance(job.get("policy"), dict) else {}
        source = _source_record(job or {
            "source_record_id": run.get("source_record_id"),
            "inputs": {"blueprint_id": run.get("blueprint_id")},
            "policy": run.get("policy_summary", {}),
        }, now)
        source_records[source["source_record_id"]] = source

        blueprint_id = str(inputs.get("blueprint_id") or run.get("blueprint_id") or "unknown-blueprint")
        vertical = str(inputs.get("vertical") or "cross_industry.public_source")
        expected_objects = [str(item) for item in inputs.get("expected_objects", [])] or ["candidate_primitive"]
        required_stages = [str(item) for item in inputs.get("required_stages", [])]
        label_paths = [str(item) for item in inputs.get("label_paths", [])]
        review_triggers = [str(item) for item in inputs.get("review_triggers", [])]

        entity_candidates = [
            _entity("source", blueprint_id, source_record_id=source["source_record_id"], description="Public-source blueprint that generated candidate objects."),
            _entity("concept", vertical, source_record_id=source["source_record_id"], description="Vertical facet derived from public-source blueprint metadata."),
        ]
        for stage in required_stages:
            entity_candidates.append(_entity("workflow", stage, source_record_id=source["source_record_id"], description="Required object-factory stage."))
        for entity in entity_candidates:
            entities.setdefault(entity["entity_id"], entity)

        for expected_object in expected_objects:
            object_id = _object_id(blueprint_id, expected_object)
            content_body = {
                "blueprint_id": blueprint_id,
                "vertical": vertical,
                "candidate_primitive": expected_object,
                "required_stages": required_stages,
                "label_paths": label_paths,
                "review_triggers": review_triggers,
                "source_patterns": inputs.get("source_patterns", []),
                "excluded_scopes": excluded_scopes,
                "source_body_stored": False,
                "row_emission_method": "deterministic_public_source_replay",
            }
            content_hash = _hash_json(content_body)
            dedupe_cluster_id = f"dedupe/public-source/{content_hash[:20]}"
            linked_entity_ids = [entity["entity_id"] for entity in entity_candidates]
            rows["normalized_object"].append({
                "object_id": object_id,
                "object_type": "candidate_primitive",
                "source_record_id": source["source_record_id"],
                "title": f"{expected_object.replace('_', ' ').title()} from {blueprint_id}",
                "body": content_body,
                "canonical_entity_ids": linked_entity_ids,
                "dedupe_cluster_id": dedupe_cluster_id,
                "trust_tier": source["trust_tier"],
                "privacy_boundary": "public",
                "quality_status": "generated_candidate",
                "review_status": "pending_review" if review_triggers else "generated_candidate",
                "content_hash": content_hash,
                "effective_date": _date_today(),
                "retrieved_at": now,
                "provenance": {
                    "source_url": "",
                    "archive_url": "",
                    "publisher": source["publisher"],
                    "license": source["license"],
                    "collected_by": "public-source-replay-row-emitter",
                    "collection_method": "deterministic replay from queued public-source jobs",
                },
            })
            rows["dedupe_cluster"].append({
                "dedupe_cluster_id": dedupe_cluster_id,
                "canonical_object_id": object_id,
                "member_ids": [object_id],
                "status": "review_required" if review_triggers else "open",
                "methods": ["content_hash", "blueprint_id", "candidate_primitive"],
                "scores": {"exact_id": True, "fuzzy_ratio": 1.0, "entity_overlap": 1.0},
                "merge_policy": "do_not_auto_merge_across_publishers",
                "review_reason": "Public-source blueprint output requires curator review before promotion." if review_triggers else "",
            })
            for entity_id in linked_entity_ids:
                refs[(object_id, entity_id, "derived_from")] = {
                    "object_id": object_id,
                    "entity_id": entity_id,
                    "role": "derived_from",
                    "confidence": 0.86,
                }
            labels = [
                _label(object_id, vertical, f"vertical.{vertical}"),
                _label(object_id, expected_object, f"primitive.{expected_object}", label_set="generated"),
                _label(object_id, "insurance_excluded", "scope.excluded.insurance", label_set="generated"),
            ]
            for label_path in label_paths:
                labels.append(_label(object_id, label_path.split(".")[-1], label_path))
            rows["label_assignment"].extend(labels)

            rows["dimension_value"].extend([
                _dimension(object_id, "required_stage_count", len(required_stages), "integer"),
                _dimension(object_id, "review_trigger_count", len(review_triggers), "integer"),
                _dimension(object_id, "source_pattern_count", len(inputs.get("source_patterns", []) or []), "integer"),
                _dimension(object_id, "source_body_stored", False, "boolean"),
                _dimension(object_id, "excluded_scopes", excluded_scopes, "array"),
                _dimension(object_id, "publication_readiness", "needs_review" if review_triggers else "candidate", "category"),
            ])

            embedding_text = " ".join([
                blueprint_id,
                vertical,
                expected_object,
                " ".join(required_stages),
                " ".join(label_paths),
                " ".join(str(item) for item in inputs.get("source_patterns", []) or []),
            ]).strip()
            bucket = f"public-source/{_safe_slug(vertical)}/{_safe_slug(expected_object)}"
            embedding = _embedding(object_id, embedding_text, bucket, now)
            rows["object_embedding"].append(embedding)
            rows["index_record"].extend(_index_records(
                object_id,
                embedding_text,
                {
                    "blueprint_id": blueprint_id,
                    "vertical": vertical,
                    "candidate_primitive": expected_object,
                    "required_stages": required_stages,
                    "label_paths": label_paths,
                    "embedding_bucket": bucket,
                    "excluded_scopes": excluded_scopes,
                },
                embedding["embedding_id"],
                [
                    {"src_id": object_id, "dst_id": entity_id, "role": "linked_entity", "confidence": 0.84}
                    for entity_id in linked_entity_ids
                ],
            ))
            if review_triggers:
                rows["review_ticket"].append({
                    "review_ticket_id": f"review/{_safe_slug(object_id)}",
                    "object_id": object_id,
                    "source_record_id": source["source_record_id"],
                    "review_type": "curator",
                    "reason": "Public-source primitive has volatile or consumer-impacting review triggers.",
                    "status": "open",
                    "priority": "medium",
                    "assigned_to": "curator_queue",
                    "created_at": now,
                    "evidence": [{"type": "review_triggers", "values": review_triggers}],
                })

    rows["source_record"] = sorted(source_records.values(), key=lambda row: row["source_record_id"])
    rows["canonical_entity"] = sorted(entities.values(), key=lambda row: row["entity_id"])
    rows["object_entity_ref"] = sorted(refs.values(), key=lambda row: (row["object_id"], row["entity_id"], row["role"]))
    return rows


def export_replay_rows(
    *,
    job_run_records: list[dict[str, Any]],
    jobs: list[dict[str, Any]] | None = None,
    output_dir: str | Path | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-public-source-rows-"))
    rows = build_replay_row_families(job_run_records=job_run_records, jobs=jobs, excluded_scopes=excluded_scopes)
    row_family_paths: dict[str, str] = {}
    row_counts: dict[str, int] = {}
    for family, filename in FILE_NAMES.items():
        path = out / filename
        _write_jsonl(path, rows[family])
        row_family_paths[family] = str(path)
        row_counts[family] = len(rows[family])
    return {
        "output_dir": str(out),
        "row_counts": row_counts,
        "row_family_paths": row_family_paths,
        "warnings": [
            "Rows are generated from public blueprint and replay metadata only; source bodies were not fetched.",
            "Insurance scope is excluded by default.",
        ],
    }


def _sample_jobs() -> list[dict[str, Any]]:
    return [{
        "job_id": "job/public-source/demo/04-source_ingest/shard/demo",
        "job_type": "source_ingest",
        "tenant_id": "tenant-public-catalog",
        "source_record_id": "source/public-source-blueprint/demo",
        "inputs": {
            "blueprint_id": "demo-public-source-blueprint",
            "title": "Demo public source blueprint",
            "vertical": "construction.plumbing_hvac",
            "expected_objects": ["permit_requirement_fact", "inspection_checklist_item"],
            "required_stages": ["source_governance", "entity_linking", "index_record_emission"],
            "label_paths": ["vertical.construction.plumbing_hvac"],
            "review_triggers": ["fee or disclosure obligation"],
            "source_patterns": ["municipal permit page"],
        },
        "policy": {"trust_tier": "official_or_public", "privacy_boundary": "public"},
    }]


def _sample_runs() -> list[dict[str, Any]]:
    return [{
        "run_record_id": "run/demo/job-public-source-demo-source-ingest",
        "run_id": "demo",
        "job_id": "job/public-source/demo/04-source_ingest/shard/demo",
        "job_type": "source_ingest",
        "tenant_id": "tenant-public-catalog",
        "source_record_id": "source/public-source-blueprint/demo",
        "blueprint_id": "demo-public-source-blueprint",
    }]


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = export_replay_rows(job_run_records=_sample_runs(), jobs=_sample_jobs(), output_dir=tmp)
        assert result["row_counts"]["source_record"] == 1
        assert result["row_counts"]["normalized_object"] == 2
        assert result["row_counts"]["index_record"] == 10
        assert result["row_counts"]["review_ticket"] == 2
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit canonical row-family JSONL from public-source replay records.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--job-run-records-jsonl")
    parser.add_argument("--jobs-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.job_run_records_jsonl:
        parser.error("--job-run-records-jsonl is required unless --self-test is used")
    result = export_replay_rows(
        job_run_records=_read_jsonl(args.job_run_records_jsonl),
        jobs=_read_jsonl(args.jobs_jsonl),
        output_dir=args.output_dir,
        excluded_scopes=args.excluded_scopes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
