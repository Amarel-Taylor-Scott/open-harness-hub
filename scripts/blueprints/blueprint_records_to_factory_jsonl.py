from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.blueprints.local_sentence_demo import run_sentence_to_pipeline


FILE_NAMES = {
    "source_record": "source-records.jsonl",
    "normalized_object": "normalized-objects.jsonl",
    "canonical_entity": "canonical-entities.jsonl",
    "object_entity_ref": "object-entity-refs.jsonl",
    "dedupe_cluster": "dedupe-clusters.jsonl",
    "review_ticket": "review-tickets.jsonl",
    "index_record": "index-records.jsonl",
}


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


def _entity(entity_type: str, name: str, confidence: float = 0.8) -> dict[str, Any]:
    slug = _safe_slug(f"{entity_type}-{name}")
    return {
        "entity_id": f"entity/{slug}",
        "entity_type": entity_type,
        "canonical_name": name,
        "aliases": [],
        "identifiers": {},
        "description": f"Blueprint demo entity: {name}",
        "confidence": confidence,
        "review_status": "generated_candidate",
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def build_row_families(
    run_output: dict[str, Any],
    prompt: str = "",
    include_private_prompt: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    now = datetime.now(timezone.utc).isoformat()
    task_parse = run_output.get("task_parse", {})
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else _hash_json(task_parse)
    source_record_id = f"source/local-blueprint-run/{prompt_hash[:16]}"
    source_body: dict[str, Any] = {
        "prompt_hash": prompt_hash,
        "task_parse": task_parse,
        "simulate": run_output.get("simulate", True),
        "route_option_count": len(run_output.get("options", [])),
        "privacy_note": "Raw prompt omitted; prompt hash retained for tenant-private traceability.",
    }
    warnings = []
    if include_private_prompt:
        source_body["prompt"] = prompt
    elif prompt:
        warnings.append("Raw prompt text was not exported.")

    rows: dict[str, list[dict[str, Any]]] = {key: [] for key in FILE_NAMES}
    rows["source_record"].append(
        {
            "source_record_id": source_record_id,
            "source_url": "",
            "archive_url": "",
            "publisher": "local sentence-to-pipeline demo",
            "license": "tenant-private",
            "trust_tier": "user_private_source",
            "privacy_boundary": "tenant",
            "freshness": "volatile",
            "retrieved_at": now,
            "effective_date": "",
            "content_hash": _hash_json(source_body),
            "body": source_body,
        }
    )

    entity_by_id: dict[str, dict[str, Any]] = {}
    entity_refs: list[dict[str, Any]] = []
    base_entities = [
        _entity("task_type", str(task_parse.get("task_type", "general_pipeline_blueprint"))),
        _entity("risk_tier", str(task_parse.get("risk_tier", "standard"))),
    ]
    for modality in task_parse.get("modalities", []):
        base_entities.append(_entity("modality", str(modality), 0.9))
    for entity in base_entities:
        entity_by_id[entity["entity_id"]] = entity

    normalized_records = run_output.get("output_records", {}).get("normalized_objects", [])
    for record in normalized_records:
        object_id = str(record.get("object_id"))
        object_type = str(record.get("object_type", "blueprint_output_record"))
        body = dict(record)
        title = record.get("title") or f"{object_type.replace('_', ' ').title()} {record.get('route_name', '')}".strip()
        content_hash = _hash_json(body)
        dedupe_cluster_id = f"dedupe/blueprint/{object_type}/{content_hash[:16]}"
        review_status = str(record.get("review_status") or ("pending" if task_parse.get("risk_tier") in {"high", "regulated", "public_safety"} else "not_required"))
        rows["normalized_object"].append(
            {
                "object_id": object_id,
                "object_type": object_type,
                "source_record_id": source_record_id,
                "title": title,
                "body": body,
                "trust_tier": "generated_candidate",
                "privacy_boundary": "tenant",
                "quality_status": str(record.get("quality_status", "generated_candidate")),
                "review_status": review_status,
                "content_hash": content_hash,
                "dedupe_cluster_id": dedupe_cluster_id,
            }
        )
        rows["dedupe_cluster"].append(
            {
                "dedupe_cluster_id": dedupe_cluster_id,
                "canonical_object_id": object_id,
                "method": "object_type_content_hash",
                "threshold": {"exact_hash": True},
                "status": "generated_candidate",
                "created_at": now,
            }
        )
        for entity_id in entity_by_id:
            entity_refs.append(
                {
                    "object_id": object_id,
                    "entity_id": entity_id,
                    "role": "describes",
                    "confidence": 0.75,
                }
            )
        route_name = record.get("route_name")
        if route_name:
            entity = _entity("route_name", str(route_name), 0.9)
            entity_by_id[entity["entity_id"]] = entity
            entity_refs.append(
                {
                    "object_id": object_id,
                    "entity_id": entity["entity_id"],
                    "role": "route_option",
                    "confidence": 0.9,
                }
            )

        index_text = " ".join(
            [
                title,
                object_type,
                str(task_parse.get("task_type", "")),
                str(task_parse.get("risk_tier", "")),
                " ".join(str(item) for item in task_parse.get("modalities", [])),
                " ".join(str(item) for item in record.get("guardrails", [])),
            ]
        ).strip()
        for kind in ["keyword", "facet", "quality", "cost"]:
            rows["index_record"].append(
                {
                    "index_record_id": f"index/{kind}/{_safe_slug(object_id)}",
                    "index_kind": kind,
                    "subject_id": object_id,
                    "subject_type": object_type,
                    "text": index_text or title,
                    "metadata": {
                        "task_type": task_parse.get("task_type"),
                        "risk_tier": task_parse.get("risk_tier"),
                        "modalities": task_parse.get("modalities", []),
                        "route_name": record.get("route_name"),
                        "review_status": review_status,
                    },
                    "embedding_model": "",
                    "embedding_ref": "",
                    "graph_edges": [],
                }
            )

    rows["canonical_entity"] = sorted(entity_by_id.values(), key=lambda item: item["entity_id"])
    rows["object_entity_ref"] = entity_refs
    for ticket in run_output.get("output_records", {}).get("review_tickets", []):
        rows["review_ticket"].append(
            {
                "review_ticket_id": ticket.get("ticket_id", f"review/{prompt_hash[:16]}"),
                "object_id": "",
                "source_record_id": source_record_id,
                "review_type": ticket.get("queue", "domain_safety_review"),
                "reason": ticket.get("reason", "Generated blueprint requires review."),
                "status": "open",
                "created_at": now,
            }
        )
    for record in rows["normalized_object"]:
        if record["review_status"] == "pending" or record["object_type"] == "pricing_snapshot_stub":
            rows["review_ticket"].append(
                {
                    "review_ticket_id": f"review/{_safe_slug(record['object_id'])}",
                    "object_id": record["object_id"],
                    "source_record_id": source_record_id,
                    "review_type": "blueprint_output_review",
                    "reason": "Generated blueprint output requires review before publication, deployment, or live pricing use.",
                    "status": "open",
                    "created_at": now,
                }
            )
    if warnings:
        rows["source_record"][0]["body"]["warnings"] = warnings
    return rows


def export_run_output(
    run_output: dict[str, Any],
    prompt: str = "",
    output_dir: str | Path | None = None,
    include_private_prompt: bool = False,
) -> dict[str, Any]:
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-blueprint-records-"))
    rows = build_row_families(run_output, prompt=prompt, include_private_prompt=include_private_prompt)
    files = []
    row_family_paths = {}
    counts = {}
    for family, filename in FILE_NAMES.items():
        family_rows = rows.get(family, [])
        path = out_dir / filename
        _write_jsonl(path, family_rows)
        files.append(filename)
        row_family_paths[family] = str(path)
        counts[family] = len(family_rows)
    warnings = []
    if prompt and not include_private_prompt:
        warnings.append("Raw prompt text was not exported.")
    return {
        "output_dir": str(out_dir),
        "row_counts": counts,
        "files": files,
        "row_family_paths": row_family_paths,
        "warnings": warnings,
    }


def _self_test() -> None:
    prompt = "Build me a cheap LLM pipeline that intakes a photo plus description and classifies possible human exploitation."
    run_output = run_sentence_to_pipeline(prompt, cost_policy={"max_usd_per_1000_items": 5.0})
    with tempfile.TemporaryDirectory() as tmp:
        result = export_run_output(run_output, prompt=prompt, output_dir=tmp)
        assert result["row_counts"]["source_record"] == 1
        assert result["row_counts"]["normalized_object"] >= 4
        assert result["row_counts"]["canonical_entity"] >= 3
        assert result["row_counts"]["index_record"] >= result["row_counts"]["normalized_object"]
        assert (Path(tmp) / "normalized-objects.jsonl").exists()


def main() -> int:
    parser = argparse.ArgumentParser(description="Export local blueprint demo records to canonical JSONL row families.")
    parser.add_argument("prompt", nargs="?", default="")
    parser.add_argument("--output-dir")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--include-private-prompt", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.prompt:
        parser.error("prompt is required unless --self-test is used")
    run_output = run_sentence_to_pipeline(args.prompt)
    print(
        json.dumps(
            export_run_output(
                run_output,
                prompt=args.prompt,
                output_dir=args.output_dir,
                include_private_prompt=args.include_private_prompt,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
