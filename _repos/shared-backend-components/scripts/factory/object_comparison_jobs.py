from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from itertools import combinations
from pathlib import Path
from typing import Any


def _hash_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_slug(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-")[:64] or "unknown"


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _tokens(record: dict[str, Any]) -> set[str]:
    body = record.get("body", {})
    text = " ".join(
        [
            str(record.get("object_id", "")),
            str(record.get("object_type", "")),
            str(record.get("title", "")),
            json.dumps(body, sort_keys=True, ensure_ascii=False) if isinstance(body, dict) else str(body),
        ]
    ).lower()
    return {token.strip(".,:;()[]{}\"'") for token in text.split() if len(token.strip(".,:;()[]{}\"'")) > 2}


def _block_key(record: dict[str, Any], fields: list[str]) -> str:
    parts = []
    body = record.get("body", {}) if isinstance(record.get("body"), dict) else {}
    for field in fields:
        value = record.get(field, body.get(field, ""))
        if isinstance(value, list):
            value = "|".join(sorted(str(item) for item in value))
        parts.append(str(value or "unknown"))
    return "::".join(parts)


def _pair_key(left_id: str, right_id: str) -> str:
    left, right = sorted([left_id, right_id])
    return f"{left}::{right}"


def _load_completed_pairs(checkpoint_path: str | Path | None) -> set[str]:
    if not checkpoint_path or not Path(checkpoint_path).exists():
        return set()
    completed = set()
    for row in _read_jsonl(checkpoint_path):
        if row.get("status") == "completed" and row.get("pair_key"):
            completed.add(str(row["pair_key"]))
        for pair_key in row.get("completed_pair_keys", []) or []:
            completed.add(str(pair_key))
    return completed


def _field_values(record: dict[str, Any], field: str) -> list[str]:
    body = record.get("body", {}) if isinstance(record.get("body"), dict) else {}
    metadata = record.get("comparison_metadata", {}) if isinstance(record.get("comparison_metadata"), dict) else {}
    value = record.get(field, body.get(field, metadata.get(field, "")))
    if isinstance(value, list):
        return sorted({str(item) for item in value if item not in (None, "")})
    if isinstance(value, dict):
        return [json.dumps(value, sort_keys=True, ensure_ascii=False)]
    if value in (None, ""):
        return ["unknown"]
    return [str(value)]


def _record_block_keys(record: dict[str, Any], fields: list[str], *, block_mode: str = "all") -> list[str]:
    if block_mode == "any":
        keys = []
        for field in fields:
            for value in _field_values(record, field)[:250]:
                keys.append(f"{field}={value}")
        return keys or ["unknown"]
    parts: list[list[str]] = []
    for field in fields:
        values = _field_values(record, field)
        if field in {"entity_ids", "label_paths", "stage_entities", "output_entities", "embedding_bucket"}:
            values = values[:25]
        parts.append(values or ["unknown"])
    keys = [""]
    for values in parts:
        keys = [f"{prefix}::{value}" if prefix else value for prefix in keys for value in values]
        if len(keys) > 250:
            keys = keys[:250]
    return keys or ["unknown"]


def enrich_records_for_comparison(
    records: list[dict[str, Any]],
    *,
    labels: list[dict[str, Any]] | None = None,
    dimensions: list[dict[str, Any]] | None = None,
    entity_refs: list[dict[str, Any]] | None = None,
    embeddings: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    enriched = [dict(record) for record in records]
    by_id = {str(record["object_id"]): record for record in enriched if record.get("object_id")}
    for record in by_id.values():
        record.setdefault("comparison_metadata", {})

    for label in labels or []:
        subject_id = str(label.get("subject_id", ""))
        record = by_id.get(subject_id)
        if not record:
            continue
        metadata = record["comparison_metadata"]
        metadata.setdefault("label_ids", []).append(str(label.get("label_id", "")))
        metadata.setdefault("label_paths", []).append(str(label.get("path") or label.get("label") or ""))
        metadata.setdefault("label_sets", []).append(str(label.get("label_set", "")))

    for dimension in dimensions or []:
        subject_id = str(dimension.get("subject_id", ""))
        record = by_id.get(subject_id)
        if not record:
            continue
        name = str(dimension.get("name", ""))
        value = dimension.get("value")
        metadata = record["comparison_metadata"]
        metadata.setdefault("dimension_names", []).append(name)
        if name:
            metadata[name] = value

    for ref in entity_refs or []:
        object_id = str(ref.get("object_id", ""))
        record = by_id.get(object_id)
        if not record:
            continue
        role = str(ref.get("role", "entity"))
        entity_id = str(ref.get("entity_id", ""))
        metadata = record["comparison_metadata"]
        metadata.setdefault("entity_ids", []).append(entity_id)
        metadata.setdefault(f"{role}_entities", []).append(entity_id)

    for embedding in embeddings or []:
        subject_id = str(embedding.get("subject_id", ""))
        record = by_id.get(subject_id)
        if not record:
            continue
        metadata = record["comparison_metadata"]
        embedding_metadata = embedding.get("metadata", {}) if isinstance(embedding.get("metadata"), dict) else {}
        metadata["embedding_ref"] = embedding.get("embedding_id", "")
        metadata["embedding_model"] = embedding.get("embedding_model", "")
        metadata["embedding_bucket"] = embedding_metadata.get("bucket", "")
        metadata["embedding_text_hash"] = embedding.get("text_hash", "")
        record["embedding_ref"] = embedding.get("embedding_id", "")

    for record in by_id.values():
        metadata = record["comparison_metadata"]
        for key, value in list(metadata.items()):
            if isinstance(value, list):
                metadata[key] = sorted({item for item in value if item})
    return enriched


def plan_comparison_job(
    records: list[dict[str, Any]],
    *,
    job_id: str | None = None,
    block_fields: list[str] | None = None,
    block_mode: str = "all",
    leaf_size: int = 500,
    checkpoint_path: str | Path | None = None,
) -> dict[str, Any]:
    block_fields = block_fields or ["object_type", "privacy_boundary"]
    if block_mode not in {"all", "any"}:
        raise ValueError("block_mode must be 'all' or 'any'")
    now = datetime.now(timezone.utc).isoformat()
    completed_pairs = _load_completed_pairs(checkpoint_path)
    record_by_id = {str(record["object_id"]): record for record in records if record.get("object_id")}
    job_id = job_id or f"comparison-job/{_hash_json(sorted(record_by_id))[:16]}"

    blocks: dict[str, list[str]] = {}
    for object_id, record in record_by_id.items():
        for block_key in _record_block_keys(record, block_fields, block_mode=block_mode):
            blocks.setdefault(block_key, []).append(object_id)

    block_rows: list[dict[str, Any]] = []
    leaf_rows: list[dict[str, Any]] = []
    skipped_pair_count = 0
    total_pair_count = 0
    planned_pairs: set[str] = set()
    skipped_pairs: set[str] = set()
    for block_key, object_ids in sorted(blocks.items()):
        object_ids = sorted(set(object_ids))
        pairs = []
        for left_id, right_id in combinations(object_ids, 2):
            pair_key = _pair_key(left_id, right_id)
            if pair_key in planned_pairs:
                continue
            total_pair_count += 1
            if pair_key in completed_pairs:
                if pair_key not in skipped_pairs:
                    skipped_pair_count += 1
                    skipped_pairs.add(pair_key)
                continue
            planned_pairs.add(pair_key)
            pairs.append({"pair_key": pair_key, "left_object_id": left_id, "right_object_id": right_id})
        block_id = f"{job_id}/block/{_safe_slug(block_key)}"
        block_rows.append(
            {
                "job_id": job_id,
                "block_id": block_id,
                "block_key": block_key,
                "block_fields": block_fields,
                "object_count": len(object_ids),
                "remaining_pair_count": len(pairs),
                "created_at": now,
            }
        )
        for leaf_index in range(0, len(pairs), max(1, leaf_size)):
            leaf_pairs = pairs[leaf_index : leaf_index + max(1, leaf_size)]
            leaf_rows.append(
                {
                    "job_id": job_id,
                    "leaf_id": f"{block_id}/leaf/{leaf_index // max(1, leaf_size):06d}",
                    "block_id": block_id,
                    "pair_count": len(leaf_pairs),
                    "pairs": leaf_pairs,
                    "status": "pending",
                    "created_at": now,
                }
            )
    return {
        "job": {
            "job_id": job_id,
            "created_at": now,
            "record_count": len(record_by_id),
            "block_fields": block_fields,
            "block_mode": block_mode,
            "leaf_size": leaf_size,
            "block_count": len(block_rows),
            "leaf_count": len(leaf_rows),
            "total_pair_count": total_pair_count,
            "skipped_completed_pair_count": skipped_pair_count,
            "remaining_pair_count": sum(row["pair_count"] for row in leaf_rows),
        },
        "blocks": block_rows,
        "leaves": leaf_rows,
    }


def compare_leaf(records: list[dict[str, Any]], leaf: dict[str, Any], *, threshold: float = 0.82) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    record_by_id = {str(record["object_id"]): record for record in records if record.get("object_id")}
    results: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    for pair in leaf.get("pairs", []):
        left = record_by_id.get(str(pair["left_object_id"]))
        right = record_by_id.get(str(pair["right_object_id"]))
        if not left or not right:
            continue
        left_tokens = _tokens(left)
        right_tokens = _tokens(right)
        union = left_tokens | right_tokens
        lexical_similarity = len(left_tokens & right_tokens) / len(union) if union else 0.0
        left_metadata = left.get("comparison_metadata", {}) if isinstance(left.get("comparison_metadata"), dict) else {}
        right_metadata = right.get("comparison_metadata", {}) if isinstance(right.get("comparison_metadata"), dict) else {}
        same_embedding_ref = bool(left_metadata.get("embedding_ref") and left_metadata.get("embedding_ref") == right_metadata.get("embedding_ref"))
        same_embedding_bucket = bool(left_metadata.get("embedding_bucket") and left_metadata.get("embedding_bucket") == right_metadata.get("embedding_bucket"))
        left_entities = set(left_metadata.get("entity_ids", []) or [])
        right_entities = set(right_metadata.get("entity_ids", []) or [])
        entity_union = left_entities | right_entities
        entity_overlap = len(left_entities & right_entities) / len(entity_union) if entity_union else 0.0
        score = max(lexical_similarity, entity_overlap, 0.72 if same_embedding_bucket else 0.0, 1.0 if same_embedding_ref else 0.0)
        decision = "possible_duplicate" if score >= threshold else "distinct"
        pair_key = str(pair["pair_key"])
        results.append(
            {
                "comparison_id": f"comparison/{hashlib.sha256(pair_key.encode('utf-8')).hexdigest()[:16]}",
                "job_id": leaf.get("job_id"),
                "leaf_id": leaf.get("leaf_id"),
                "pair_key": pair_key,
                "left_object_id": left["object_id"],
                "right_object_id": right["object_id"],
                "score": round(score, 6),
                "decision": decision,
                "features": {
                    "lexical_similarity": round(lexical_similarity, 6),
                    "entity_overlap": round(entity_overlap, 6),
                    "same_embedding_bucket": same_embedding_bucket,
                    "same_embedding_ref": same_embedding_ref,
                    "left_token_count": len(left_tokens),
                    "right_token_count": len(right_tokens),
                },
                "created_at": now,
            }
        )
        checkpoints.append(
            {
                "job_id": leaf.get("job_id"),
                "leaf_id": leaf.get("leaf_id"),
                "pair_key": pair_key,
                "status": "completed",
                "completed_at": now,
            }
        )
    return {
        "leaf_id": leaf.get("leaf_id"),
        "status": "completed",
        "comparison_results": results,
        "checkpoints": checkpoints,
    }


def write_job_plan(
    records: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    job_id: str | None = None,
    block_fields: list[str] | None = None,
    block_mode: str = "all",
    leaf_size: int = 500,
    checkpoint_path: str | Path | None = None,
    labels: list[dict[str, Any]] | None = None,
    dimensions: list[dict[str, Any]] | None = None,
    entity_refs: list[dict[str, Any]] | None = None,
    embeddings: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-comparison-job-"))
    enriched_records = enrich_records_for_comparison(
        records,
        labels=labels,
        dimensions=dimensions,
        entity_refs=entity_refs,
        embeddings=embeddings,
    )
    plan = plan_comparison_job(
        enriched_records,
        job_id=job_id,
        block_fields=block_fields,
        block_mode=block_mode,
        leaf_size=leaf_size,
        checkpoint_path=checkpoint_path,
    )
    _write_jsonl(out_dir / "comparison-jobs.jsonl", [plan["job"]])
    _write_jsonl(out_dir / "comparison-blocks.jsonl", plan["blocks"])
    _write_jsonl(out_dir / "comparison-leaves.jsonl", plan["leaves"])
    _write_jsonl(out_dir / "comparison-records.jsonl", enriched_records)
    return {
        "output_dir": str(out_dir),
        "job": plan["job"],
        "files": ["comparison-jobs.jsonl", "comparison-blocks.jsonl", "comparison-leaves.jsonl", "comparison-records.jsonl"],
    }


def _self_test() -> None:
    records = [
        {"object_id": "object/a", "object_type": "versioned_fact", "privacy_boundary": "public", "title": "OFW placement fee rule", "body": {"jurisdiction": "PH", "claim": "placement fee rule"}},
        {"object_id": "object/b", "object_type": "versioned_fact", "privacy_boundary": "public", "title": "OFW placement fee rule updated", "body": {"jurisdiction": "PH", "claim": "placement fee rules"}},
        {"object_id": "object/c", "object_type": "decision_gate", "privacy_boundary": "public", "title": "Deployment hold", "body": {"claim": "hold for review"}},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        labels = [
            {"label_id": "label/a", "subject_id": "object/a", "path": "jurisdiction.ph.ofw"},
            {"label_id": "label/b", "subject_id": "object/b", "path": "jurisdiction.ph.ofw"},
            {"label_id": "label/c", "subject_id": "object/c", "path": "workflow.deployment_hold"},
        ]
        dimensions = [
            {"dimension_id": "dimension/a", "subject_id": "object/a", "name": "embedding_bucket", "value": "bucket/ph/ofw"},
            {"dimension_id": "dimension/b", "subject_id": "object/b", "name": "embedding_bucket", "value": "bucket/ph/ofw"},
            {"dimension_id": "dimension/c", "subject_id": "object/c", "name": "embedding_bucket", "value": "bucket/hold"},
        ]
        entity_refs = [
            {"object_id": "object/a", "entity_id": "entity/ph", "role": "jurisdiction"},
            {"object_id": "object/b", "entity_id": "entity/ph", "role": "jurisdiction"},
            {"object_id": "object/c", "entity_id": "entity/hold", "role": "workflow"},
        ]
        embeddings = [
            {"embedding_id": "embedding/a", "subject_id": "object/a", "text_hash": "a", "metadata": {"bucket": "bucket/ph/ofw"}},
            {"embedding_id": "embedding/b", "subject_id": "object/b", "text_hash": "b", "metadata": {"bucket": "bucket/ph/ofw"}},
            {"embedding_id": "embedding/c", "subject_id": "object/c", "text_hash": "c", "metadata": {"bucket": "bucket/hold"}},
        ]
        result = write_job_plan(
            records,
            output_dir=tmp,
            leaf_size=1,
            block_fields=["object_type", "embedding_bucket", "entity_ids"],
            block_mode="any",
            labels=labels,
            dimensions=dimensions,
            entity_refs=entity_refs,
            embeddings=embeddings,
        )
        assert result["job"]["remaining_pair_count"] == 1
        leaves = _read_jsonl(Path(tmp) / "comparison-leaves.jsonl")
        enriched = _read_jsonl(Path(tmp) / "comparison-records.jsonl")
        compared = compare_leaf(enriched, leaves[0])
        assert compared["comparison_results"]
        assert compared["comparison_results"][0]["features"]["same_embedding_bucket"]
        assert compared["comparison_results"][0]["features"]["entity_overlap"] > 0
        _write_jsonl(Path(tmp) / "comparison-checkpoints.jsonl", compared["checkpoints"])
        resumed = write_job_plan(
            records,
            output_dir=Path(tmp) / "resume",
            leaf_size=1,
            checkpoint_path=Path(tmp) / "comparison-checkpoints.jsonl",
            block_fields=["object_type", "embedding_bucket", "entity_ids"],
            block_mode="any",
            labels=labels,
            dimensions=dimensions,
            entity_refs=entity_refs,
            embeddings=embeddings,
        )
        assert resumed["job"]["skipped_completed_pair_count"] == 1
        assert resumed["job"]["remaining_pair_count"] == 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan resumable blocked pairwise knowledge-object comparison jobs.")
    parser.add_argument("--records-jsonl")
    parser.add_argument("--labels-jsonl")
    parser.add_argument("--dimensions-jsonl")
    parser.add_argument("--entity-refs-jsonl")
    parser.add_argument("--embeddings-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--job-id")
    parser.add_argument("--block-fields", nargs="*", default=["object_type", "privacy_boundary"])
    parser.add_argument("--block-mode", choices=["all", "any"], default="all")
    parser.add_argument("--leaf-size", type=int, default=500)
    parser.add_argument("--checkpoint-path")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.records_jsonl:
        parser.error("--records-jsonl is required unless --self-test is used")
    records = _read_jsonl(args.records_jsonl)
    labels = _read_jsonl(args.labels_jsonl) if args.labels_jsonl else []
    dimensions = _read_jsonl(args.dimensions_jsonl) if args.dimensions_jsonl else []
    entity_refs = _read_jsonl(args.entity_refs_jsonl) if args.entity_refs_jsonl else []
    embeddings = _read_jsonl(args.embeddings_jsonl) if args.embeddings_jsonl else []
    print(
        json.dumps(
            write_job_plan(
                records,
                output_dir=args.output_dir,
                job_id=args.job_id,
                block_fields=args.block_fields,
                block_mode=args.block_mode,
                leaf_size=args.leaf_size,
                checkpoint_path=args.checkpoint_path,
                labels=labels,
                dimensions=dimensions,
                entity_refs=entity_refs,
                embeddings=embeddings,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
