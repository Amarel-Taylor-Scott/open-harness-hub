#!/usr/bin/env python3
"""Emit index deltas from promotion-decision JSONL shards.

Promotion decisions are operational ranking signals. At million-object scale,
they should update quality, facet, and cost indexes incrementally instead of
forcing a full search rebuild.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:96].strip("-") or "promotion"


def _hash_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_json(value: Any) -> str:
    return _hash_text(json.dumps(value, sort_keys=True, ensure_ascii=False))


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records, _hash_text(raw)


def _decision_text(decision: dict[str, Any]) -> str:
    pieces = [
        str(decision.get("object_id", "")),
        str(decision.get("decision", "")),
        f"score {decision.get('score', '')}",
        " ".join(str(item) for item in decision.get("risk_flags", [])),
        " ".join(str(item) for item in decision.get("review_reasons", [])),
        " ".join(str(item) for item in decision.get("recommended_outputs", [])),
    ]
    return " ".join(piece for piece in pieces if piece).strip()


def _metadata(decision: dict[str, Any], partition_id: str, sequence: int) -> dict[str, Any]:
    return {
        "partition_id": partition_id,
        "sequence": sequence,
        "decision_id": decision.get("decision_id"),
        "source_record_id": decision.get("source_record_id"),
        "promotion_score": decision.get("score"),
        "promotion_decision": decision.get("decision"),
        "risk_flags": decision.get("risk_flags", []),
        "recommended_outputs": decision.get("recommended_outputs", []),
        "criteria": decision.get("criteria", {}),
    }


def _index_records(decision: dict[str, Any], partition_id: str, sequence: int) -> list[dict[str, Any]]:
    object_id = str(decision.get("object_id") or f"promotion-object/{sequence:08d}")
    subject_type = "promotion_decision"
    base = _slug(f"{partition_id}-{object_id}")
    criteria = decision.get("criteria") if isinstance(decision.get("criteria"), dict) else {}
    return [
        {
            "index_record_id": f"idx:{base}:quality",
            "index_kind": "quality",
            "subject_id": object_id,
            "subject_type": subject_type,
            "text": _decision_text(decision),
            "metadata": _metadata(decision, partition_id, sequence),
        },
        {
            "index_record_id": f"idx:{base}:facet",
            "index_kind": "facet",
            "subject_id": object_id,
            "subject_type": subject_type,
            "text": " ".join([
                str(decision.get("decision", "")),
                " ".join(str(item) for item in decision.get("risk_flags", [])),
                " ".join(str(item) for item in decision.get("recommended_outputs", [])),
            ]).strip(),
            "metadata": _metadata(decision, partition_id, sequence),
        },
        {
            "index_record_id": f"idx:{base}:cost",
            "index_kind": "cost",
            "subject_id": object_id,
            "subject_type": subject_type,
            "text": f"cost_savings={criteria.get('cost_savings', '')} economic_value={criteria.get('economic_value', '')} deployment_management_value={criteria.get('deployment_management_value', '')}",
            "metadata": _metadata(decision, partition_id, sequence),
        },
    ]


def emit_promotion_index_delta(
    *,
    input_path: str,
    partition_id: str,
    output_dir: str,
    run_id: str | None = None,
    source_surface_id: str = "",
    tenant_id: str = "",
) -> dict[str, Any]:
    source = Path(input_path)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    decisions, source_hash = _read_jsonl(source)
    created = _utc_now()
    run = run_id or time.strftime("run-%Y%m%d%H%M%S", time.gmtime())

    deltas: list[dict[str, Any]] = []
    decision_counts: dict[str, int] = {}
    for sequence, decision in enumerate(decisions, 1):
        decision_value = str(decision.get("decision") or "unknown")
        decision_counts[decision_value] = decision_counts.get(decision_value, 0) + 1
        for index_record in _index_records(decision, partition_id, sequence):
            payload_hash = _hash_json(index_record)
            index_kind = index_record["index_kind"]
            deltas.append({
                "delta_id": f"delta:{_slug(partition_id)}:{sequence:08d}:{index_kind}",
                "partition_id": partition_id,
                "run_id": run,
                "operation": "upsert",
                "index_record": index_record,
                "sequence": len(deltas) + 1,
                "created": created,
                "content_hash": payload_hash,
                "replay_policy": {
                    "idempotency_key": f"{partition_id}:{index_record['index_record_id']}",
                    "replace_subject": False,
                },
            })

    delta_path = out / "promotion-index-deltas.jsonl"
    manifest_path = out / "partition-manifest.json"
    delta_path.write_text(
        "\n".join(json.dumps(delta, sort_keys=True, ensure_ascii=False) for delta in deltas) + ("\n" if deltas else ""),
        encoding="utf-8",
    )
    manifest = {
        "partition_id": partition_id,
        "partition_kind": "index_records",
        "run_id": run,
        "source_surface_id": source_surface_id,
        "tenant_id": tenant_id,
        "object_count": len(decisions),
        "shard_paths": [str(source)],
        "index_delta_paths": [str(delta_path)],
        "schema_versions": {
            "partition_manifest": "schemas/partition-manifest.schema.json",
            "index_delta_record": "schemas/index-delta-record.schema.json",
            "promotion_decision": "schemas/promotion-decision.schema.json",
            "index_record": "schemas/index-record.schema.json",
        },
        "content_hash": source_hash,
        "created": created,
        "updated": created,
        "trust_boundary": "local",
        "privacy_summary": {
            "contains_pii": False,
            "redacted": True,
            "publication_allowed": True,
        },
        "quality_summary": {
            "promotion_decisions_read": len(decisions),
            "deltas_emitted": len(deltas),
            "index_kinds": ["quality", "facet", "cost"],
            "decision_counts": decision_counts,
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")
    return {
        "partition_manifest_path": str(manifest_path),
        "index_delta_path": str(delta_path),
        "partition_manifest": manifest,
        "deltas_emitted": len(deltas),
    }


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "promotion-decisions.jsonl"
        source.write_text(
            "\n".join([
                json.dumps({
                    "decision_id": "promotion/task-a",
                    "object_id": "task-archetype/a",
                    "source_record_id": "source/a",
                    "score": 72.5,
                    "max_score": 100,
                    "decision": "review_before_promotion",
                    "criteria": {"cost_savings": 2.5, "economic_value": 3.0, "deployment_management_value": 1.5},
                    "risk_flags": ["dedupe_review"],
                    "review_reasons": ["Needs merge review."],
                    "recommended_outputs": ["pipeline_candidate", "rubric_candidate"],
                }),
                json.dumps({
                    "decision_id": "promotion/task-b",
                    "object_id": "task-archetype/b",
                    "source_record_id": "source/b",
                    "score": 82.0,
                    "max_score": 100,
                    "decision": "promote_candidate",
                    "criteria": {"cost_savings": 3.0, "economic_value": 4.0, "deployment_management_value": 2.0},
                    "risk_flags": [],
                    "review_reasons": [],
                    "recommended_outputs": ["tool_or_harness_candidate"],
                }),
            ]) + "\n",
            encoding="utf-8",
        )
        result = emit_promotion_index_delta(
            input_path=str(source),
            partition_id="promotion/demo/000001",
            output_dir=str(base / "out"),
        )
        assert result["partition_manifest"]["object_count"] == 2
        assert result["deltas_emitted"] == 6
        print(json.dumps({
            "ok": True,
            "object_count": result["partition_manifest"]["object_count"],
            "deltas_emitted": result["deltas_emitted"],
            "decision_counts": result["partition_manifest"]["quality_summary"]["decision_counts"],
        }, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit index deltas from promotion-decision JSONL.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--partition-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--source-surface-id", default="")
    parser.add_argument("--tenant-id", default="")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    missing = [name for name in ("input", "partition_id", "output_dir") if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join("--" + name.replace("_", "-") for name in missing))
    result = emit_promotion_index_delta(
        input_path=args.input,
        partition_id=args.partition_id,
        output_dir=args.output_dir,
        run_id=args.run_id,
        source_surface_id=args.source_surface_id,
        tenant_id=args.tenant_id,
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
