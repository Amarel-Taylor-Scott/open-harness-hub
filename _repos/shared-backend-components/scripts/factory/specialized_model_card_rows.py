#!/usr/bin/env python3
"""Emit canonical row-family JSONL from specialized model-card scan jobs.

This bridges public model-card scan plans into the same loadable row families
used by the object factory. It uses model-card metadata and queue metadata only;
it does not download model weights, copy training data, or store private source
bodies.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any


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
    source_model_id = str(inputs.get("source_model_id") or "unknown-model")
    publisher = str(inputs.get("publisher") or "unknown")
    body = {
        "source_model_id": source_model_id,
        "publisher": publisher,
        "domain_signal": inputs.get("domain_signal", []),
        "task_shape": inputs.get("task_shape", ""),
        "training_context": inputs.get("training_context", []),
        "eval_context": inputs.get("eval_context", []),
        "labels_or_outputs": inputs.get("labels_or_outputs", []),
        "reusable_primitives": inputs.get("reusable_primitives", []),
        "replacement_routes": inputs.get("replacement_routes", []),
        "review_priority": inputs.get("review_priority", "medium"),
        "model_weights_downloaded": False,
        "training_data_stored": False,
        "source_body_stored": False,
    }
    return {
        "source_record_id": str(job.get("source_record_id") or f"source/specialized-model-card/{_safe_slug(source_model_id)}"),
        "source_type": "api_record",
        "source_url": f"https://huggingface.co/{source_model_id}" if "/" in source_model_id and "*" not in source_model_id else "",
        "archive_url": "",
        "publisher": publisher,
        "license": "source_specific",
        "trust_tier": str(policy.get("trust_tier") or "public"),
        "privacy_boundary": str(policy.get("privacy_boundary") or "public_model_metadata_only"),
        "freshness": "volatile",
        "retrieved_at": now,
        "effective_date": _date_today(),
        "content_hash": _hash_json(body),
        "language": "en",
        "jurisdiction": "",
        "body": body,
        "storage_ref": {
            "bucket": "not-captured",
            "key": f"specialized-model-cards/{_safe_slug(source_model_id)}",
            "media_type": "application/json",
            "size_bytes": 0,
        },
    }


def _entity(entity_type: str, name: str, *, source_record_id: str, description: str = "") -> dict[str, Any]:
    slug = _safe_slug(f"{entity_type}-{name}")
    return {
        "entity_id": f"entity/specialized-model-card/{slug}",
        "entity_type": entity_type,
        "canonical_name": name,
        "aliases": sorted({name, name.replace("_", " "), name.replace(".", " "), name.replace("/", " ")}),
        "identifiers": [{"scheme": "openhubforai_specialized_model_card", "value": hashlib.sha256(f"{entity_type}:{name}".encode()).hexdigest()[:20]}],
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
        "assigned_by": "specialized-model-card-row-emitter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "specialized_model_card_scan_jobs"},
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
        "assigned_by": "specialized-model-card-row-emitter",
        "assignment_method": "deterministic",
        "model_route_id": "",
        "provenance": {"source": "specialized_model_card_scan_jobs"},
        "review_status": "generated_candidate",
    }


def _object_id(source_model_id: str, primitive: str) -> str:
    return f"object/specialized-model-card/{_safe_slug(source_model_id)}/{_safe_slug(primitive)}"


def _embedding(object_id: str, text: str, bucket: str, now: str) -> dict[str, Any]:
    text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "embedding_id": f"embedding/{hashlib.sha256(f'{object_id}:{text_hash}'.encode()).hexdigest()[:20]}",
        "subject_id": object_id,
        "subject_type": "normalized_object",
        "embedding_model": "stub:deterministic-specialized-model-card-v1",
        "text_hash": text_hash,
        "text": text,
        "embedding": "",
        "metadata": {
            "bucket": bucket,
            "actual_embedding_required": True,
            "source": "specialized_model_card_rows",
        },
        "created_at": now,
    }


def _index_records(object_id: str, text: str, metadata: dict[str, Any], embedding_id: str, graph_edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for kind in ["keyword", "vector", "graph", "facet", "quality", "cost"]:
        rows.append({
            "index_record_id": f"index/{kind}/{_safe_slug(object_id)}",
            "index_kind": kind,
            "subject_id": object_id,
            "subject_type": "normalized_object",
            "text": text,
            "metadata": metadata,
            "embedding_model": "stub:deterministic-specialized-model-card-v1" if kind == "vector" else "",
            "embedding_ref": embedding_id if kind == "vector" else "",
            "graph_edges": graph_edges if kind == "graph" else [],
        })
    return rows


def _review_type(domain_signal: list[str], primitive: str) -> str:
    domains = {str(item) for item in domain_signal}
    if "privacy" in domains or "pii" in primitive:
        return "privacy"
    if "security" in domains or "safety" in primitive:
        return "safety"
    if "legal" in domains:
        return "legal"
    if "healthcare" in domains:
        return "domain_expert"
    return "curator"


def _priority(review_priority: str, domain_signal: list[str]) -> str:
    if str(review_priority).lower() == "high":
        return "high"
    if set(str(item) for item in domain_signal).intersection({"healthcare", "legal", "privacy", "security"}):
        return "high"
    return "medium"


def build_model_card_row_families(
    *,
    jobs: list[dict[str, Any]],
    excluded_scopes: list[str] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    now = _utc_now()
    excluded_scopes = excluded_scopes or ["insurance"]
    rows: dict[str, list[dict[str, Any]]] = {family: [] for family in FILE_NAMES}
    source_records: dict[str, dict[str, Any]] = {}
    entities: dict[str, dict[str, Any]] = {}
    refs: dict[tuple[str, str, str], dict[str, Any]] = {}

    normalize_jobs = [job for job in jobs if job.get("job_type") == "task_context_normalize"]
    for job in normalize_jobs:
        inputs = job.get("inputs") if isinstance(job.get("inputs"), dict) else {}
        source = _source_record(job, now)
        source_records[source["source_record_id"]] = source
        source_model_id = str(inputs.get("source_model_id") or "unknown-model")
        publisher = str(inputs.get("publisher") or "unknown")
        domain_signal = [str(item) for item in inputs.get("domain_signal", []) or []]
        task_shape = str(inputs.get("task_shape") or "specialized-model-task")
        training_context = [str(item) for item in inputs.get("training_context", []) or []]
        eval_context = [str(item) for item in inputs.get("eval_context", []) or []]
        labels_or_outputs = [str(item) for item in inputs.get("labels_or_outputs", []) or []]
        reusable_primitives = [str(item) for item in inputs.get("reusable_primitives", []) or ["task_definition", "label_schema"]]
        replacement_routes = [str(item) for item in inputs.get("replacement_routes", []) or []]
        review_priority = str(inputs.get("review_priority") or "medium")

        entity_candidates = [
            _entity("model", source_model_id, source_record_id=source["source_record_id"], description="Public specialized model or model-card source."),
            _entity("organization", publisher, source_record_id=source["source_record_id"], description="Model publisher or namespace."),
            _entity("workflow", task_shape, source_record_id=source["source_record_id"], description="Task shape derived from model-card metadata."),
        ]
        for domain in domain_signal:
            entity_candidates.append(_entity("concept", domain, source_record_id=source["source_record_id"], description="Domain signal derived from specialized model metadata."))
        for context in eval_context:
            entity_candidates.append(_entity("dataset" if "dataset" in context.lower() else "concept", context, source_record_id=source["source_record_id"], description="Evaluation or dataset context from model signal."))
        for entity in entity_candidates:
            entities.setdefault(entity["entity_id"], entity)
        linked_entity_ids = [entity["entity_id"] for entity in entity_candidates]

        for primitive in reusable_primitives:
            object_id = _object_id(source_model_id, primitive)
            content_body = {
                "source_model_id": source_model_id,
                "publisher": publisher,
                "task_shape": task_shape,
                "candidate_primitive": primitive,
                "domain_signal": domain_signal,
                "training_context": training_context,
                "eval_context": eval_context,
                "labels_or_outputs": labels_or_outputs,
                "replacement_routes": replacement_routes,
                "excluded_scopes": excluded_scopes,
                "model_weights_downloaded": False,
                "training_data_stored": False,
                "source_body_stored": False,
                "row_emission_method": "deterministic_specialized_model_card_jobs",
            }
            content_hash = _hash_json(content_body)
            dedupe_cluster_id = f"dedupe/specialized-model-card/{content_hash[:20]}"
            high_review = _priority(review_priority, domain_signal) == "high"
            rows["normalized_object"].append({
                "object_id": object_id,
                "object_type": "candidate_primitive",
                "source_record_id": source["source_record_id"],
                "title": f"{primitive.replace('_', ' ').title()} from {source_model_id}",
                "body": content_body,
                "canonical_entity_ids": linked_entity_ids,
                "dedupe_cluster_id": dedupe_cluster_id,
                "trust_tier": source["trust_tier"],
                "privacy_boundary": "public_model_metadata_only",
                "quality_status": "generated_candidate",
                "review_status": "pending_review" if high_review else "generated_candidate",
                "content_hash": content_hash,
                "effective_date": _date_today(),
                "retrieved_at": now,
                "provenance": {
                    "source_url": source["source_url"],
                    "archive_url": "",
                    "publisher": source["publisher"],
                    "license": source["license"],
                    "collected_by": "specialized-model-card-row-emitter",
                    "collection_method": "deterministic row emission from queued specialized model-card scan jobs",
                },
            })
            rows["dedupe_cluster"].append({
                "dedupe_cluster_id": dedupe_cluster_id,
                "canonical_object_id": object_id,
                "member_ids": [object_id],
                "status": "review_required" if high_review else "open",
                "methods": ["content_hash", "source_model_id", "task_shape", "candidate_primitive"],
                "scores": {"exact_id": True, "fuzzy_ratio": 1.0, "entity_overlap": 1.0},
                "merge_policy": "do_not_auto_merge_across_model_publishers",
                "review_reason": "Specialized model-card primitive is high-impact or safety-sensitive." if high_review else "",
            })
            for entity_id in linked_entity_ids:
                refs[(object_id, entity_id, "derived_from")] = {
                    "object_id": object_id,
                    "entity_id": entity_id,
                    "role": "derived_from",
                    "confidence": 0.86,
                }
            labels = [
                _label(object_id, task_shape, f"task_shape.{task_shape}"),
                _label(object_id, primitive, f"primitive.{primitive}", label_set="generated"),
                _label(object_id, "insurance_excluded", "scope.excluded.insurance", label_set="generated"),
            ]
            for domain in domain_signal:
                labels.append(_label(object_id, domain, f"domain.{domain}"))
            rows["label_assignment"].extend(labels)
            rows["dimension_value"].extend([
                _dimension(object_id, "training_context_count", len(training_context), "integer"),
                _dimension(object_id, "eval_context_count", len(eval_context), "integer"),
                _dimension(object_id, "label_or_output_count", len(labels_or_outputs), "integer"),
                _dimension(object_id, "replacement_route_count", len(replacement_routes), "integer"),
                _dimension(object_id, "model_weights_downloaded", False, "boolean"),
                _dimension(object_id, "excluded_scopes", excluded_scopes, "array"),
                _dimension(object_id, "publication_readiness", "needs_review" if high_review else "candidate", "category"),
            ])
            embedding_text = " ".join([
                source_model_id,
                publisher,
                task_shape,
                primitive,
                " ".join(domain_signal),
                " ".join(training_context),
                " ".join(eval_context),
                " ".join(labels_or_outputs),
                " ".join(replacement_routes),
            ]).strip()
            bucket = f"specialized-model-card/{_safe_slug(task_shape)}/{_safe_slug(primitive)}"
            embedding = _embedding(object_id, embedding_text, bucket, now)
            rows["object_embedding"].append(embedding)
            rows["index_record"].extend(_index_records(
                object_id,
                embedding_text,
                {
                    "source_model_id": source_model_id,
                    "publisher": publisher,
                    "task_shape": task_shape,
                    "candidate_primitive": primitive,
                    "domain_signal": domain_signal,
                    "labels_or_outputs": labels_or_outputs,
                    "embedding_bucket": bucket,
                    "excluded_scopes": excluded_scopes,
                    "cost_route_candidate": bool(replacement_routes),
                    "model_swap_value": "high",
                },
                embedding["embedding_id"],
                [
                    {"src_id": object_id, "dst_id": entity_id, "role": "linked_entity", "confidence": 0.84}
                    for entity_id in linked_entity_ids
                ],
            ))
            if high_review:
                rows["review_ticket"].append({
                    "review_ticket_id": f"review/{_safe_slug(object_id)}",
                    "object_id": object_id,
                    "source_record_id": source["source_record_id"],
                    "review_type": _review_type(domain_signal, primitive),
                    "reason": "Specialized model-card primitive touches a high-impact, safety, privacy, legal, or healthcare domain.",
                    "status": "open",
                    "priority": _priority(review_priority, domain_signal),
                    "assigned_to": "curator_queue",
                    "created_at": now,
                    "evidence": [{"type": "domain_signal", "values": domain_signal}, {"type": "review_priority", "value": review_priority}],
                })

    rows["source_record"] = sorted(source_records.values(), key=lambda row: row["source_record_id"])
    rows["canonical_entity"] = sorted(entities.values(), key=lambda row: row["entity_id"])
    rows["object_entity_ref"] = sorted(refs.values(), key=lambda row: (row["object_id"], row["entity_id"], row["role"]))
    return rows


def export_model_card_rows(
    *,
    jobs: list[dict[str, Any]],
    output_dir: str | Path | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    out = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-model-card-rows-"))
    rows = build_model_card_row_families(jobs=jobs, excluded_scopes=excluded_scopes)
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
            "Rows are generated from public model-card signal and scan-job metadata only.",
            "Model weights and private training data were not downloaded or stored.",
            "Insurance scope is excluded by default.",
        ],
    }


def _sample_jobs() -> list[dict[str, Any]]:
    return [{
        "job_id": "job/specialized-model-card/prosusai-finbert/04-task_context_normalize/shard/demo",
        "job_type": "task_context_normalize",
        "tenant_id": "tenant-public-catalog",
        "source_record_id": "source/specialized-model-card/prosusai-finbert",
        "inputs": {
            "source_model_id": "ProsusAI/finbert",
            "publisher": "ProsusAI",
            "domain_signal": ["finance"],
            "task_shape": "financial-text-sentiment-classification",
            "training_context": ["BERT further trained in finance domain", "Financial PhraseBank fine-tuning"],
            "eval_context": ["FinBERT paper"],
            "labels_or_outputs": ["positive", "negative", "neutral"],
            "reusable_primitives": ["financial sentiment label schema", "classification evaluation harness"],
            "replacement_routes": ["cheap text classifier", "prompted LLM with label schema"],
            "review_priority": "medium",
        },
        "policy": {"trust_tier": "public", "privacy_boundary": "public_model_metadata_only"},
    }]


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = export_model_card_rows(jobs=_sample_jobs(), output_dir=tmp)
        assert result["row_counts"]["source_record"] == 1
        assert result["row_counts"]["normalized_object"] == 2
        assert result["row_counts"]["index_record"] == 12
        assert result["row_counts"]["review_ticket"] == 0
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit canonical row-family JSONL from specialized model-card scan jobs.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--jobs-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.jobs_jsonl:
        parser.error("--jobs-jsonl is required unless --self-test is used")
    result = export_model_card_rows(
        jobs=_read_jsonl(args.jobs_jsonl),
        output_dir=args.output_dir,
        excluded_scopes=args.excluded_scopes,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
