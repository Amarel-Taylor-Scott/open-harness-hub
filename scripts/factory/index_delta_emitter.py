#!/usr/bin/env python3
"""Emit partition manifests and append-only index deltas from JSONL objects.

The script is intentionally stdlib-only and deterministic. It gives the
million-object path a local primitive: high-volume JSONL shards can produce
replayable keyword/facet/vector-placeholder deltas without generating one docs
page per object.

CLI:
    python3 -m scripts.factory.index_delta_emitter --self-test
    python3 -m scripts.factory.index_delta_emitter \
        --input objects.jsonl --partition-id demo/000001 --output-dir dist/index-deltas/demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _stable_hash(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:80].strip("-") or "object"


def _read_jsonl(path: Path) -> tuple[list[dict[str, Any]], str]:
    raw = path.read_text(encoding="utf-8")
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        record = json.loads(line)
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{line_no}: JSONL row must be an object")
        records.append(record)
    return records, _stable_hash(raw)


def _subject_id(record: dict[str, Any], partition_id: str, sequence: int) -> str:
    for key in ("object_id", "id", "subject_id"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    text = str(record.get("text") or record.get("name") or record.get("title") or sequence)
    return f"partition-object/{_slug(partition_id)}-{sequence:08d}-{_slug(text)[:32]}"


def _record_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("name", "title", "text", "description", "summary", "question", "task"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())
    if not parts:
        parts.append(json.dumps(record, sort_keys=True, ensure_ascii=False))
    return "\n".join(parts)


def _metadata(record: dict[str, Any], partition_id: str, sequence: int) -> dict[str, Any]:
    keys = [
        "object_type",
        "source_record_id",
        "evidence_span_ids",
        "industry",
        "capability",
        "modality",
        "labels",
        "dimensions",
        "trust_boundary",
        "freshness",
        "license",
    ]
    meta = {key: record[key] for key in keys if key in record}
    meta["partition_id"] = partition_id
    meta["sequence"] = sequence
    return meta


def _index_record(
    *,
    record: dict[str, Any],
    partition_id: str,
    sequence: int,
    index_kind: str,
) -> dict[str, Any]:
    subject_id = _subject_id(record, partition_id, sequence)
    text = _record_text(record)
    return {
        "index_record_id": f"idx:{_slug(partition_id)}:{sequence:08d}:{index_kind}",
        "index_kind": index_kind,
        "subject_id": subject_id,
        "subject_type": record.get("object_type", "normalized_object"),
        "text": text,
        "metadata": _metadata(record, partition_id, sequence),
    }


def emit_index_delta(
    *,
    input_path: str,
    partition_id: str,
    output_dir: str,
    run_id: str | None = None,
    source_surface_id: str = "",
    tenant_id: str = "",
    emit: list[str] | None = None,
) -> dict[str, Any]:
    """Emit a partition manifest and JSONL index deltas from normalized objects."""
    source = Path(input_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = run_id or time.strftime("run-%Y%m%d%H%M%S", time.gmtime())
    kinds = emit or ["keyword", "facet", "freshness", "quality"]
    records, source_hash = _read_jsonl(source)
    created = _utc_now()

    delta_path = out_dir / "index-deltas.jsonl"
    manifest_path = out_dir / "partition-manifest.json"
    deltas: list[dict[str, Any]] = []
    for i, record in enumerate(records, 1):
        for kind in kinds:
            index_record = _index_record(
                record=record,
                partition_id=partition_id,
                sequence=i,
                index_kind=kind,
            )
            payload = json.dumps(index_record, sort_keys=True, ensure_ascii=False)
            deltas.append({
                "delta_id": f"delta:{_slug(partition_id)}:{i:08d}:{kind}",
                "partition_id": partition_id,
                "run_id": run,
                "operation": "upsert",
                "index_record": index_record,
                "sequence": len(deltas) + 1,
                "created": created,
                "content_hash": _stable_hash(payload),
                "replay_policy": {
                    "idempotency_key": f"{partition_id}:{index_record['index_record_id']}",
                    "replace_subject": False,
                },
            })

    delta_path.write_text(
        "\n".join(json.dumps(delta, sort_keys=True, ensure_ascii=False) for delta in deltas) + ("\n" if deltas else ""),
        encoding="utf-8",
    )
    manifest = {
        "partition_id": partition_id,
        "partition_kind": "normalized_objects",
        "run_id": run,
        "source_surface_id": source_surface_id,
        "tenant_id": tenant_id,
        "object_count": len(records),
        "shard_paths": [str(source)],
        "index_delta_paths": [str(delta_path)],
        "schema_versions": {
            "partition_manifest": "schemas/partition-manifest.schema.json",
            "index_delta_record": "schemas/index-delta-record.schema.json",
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
            "records_read": len(records),
            "deltas_emitted": len(deltas),
            "index_kinds": kinds,
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
        shard = base / "objects.jsonl"
        shard.write_text(
            "\n".join([
                json.dumps({
                    "object_id": "procedure/demo/check-source",
                    "object_type": "checklist_item",
                    "text": "Confirm source evidence exists before publication.",
                    "capability": ["verification"],
                    "labels": ["governance.evidence"],
                }),
                json.dumps({
                    "object_id": "question/demo/redaction",
                    "object_type": "review_question",
                    "text": "Has sensitive data been redacted before external model routing?",
                    "capability": ["safety_gating"],
                    "labels": ["privacy.redaction"],
                }),
            ]) + "\n",
            encoding="utf-8",
        )
        result = emit_index_delta(
            input_path=str(shard),
            partition_id="demo/local/000001",
            output_dir=str(base / "out"),
            emit=["keyword", "facet"],
        )
        assert result["partition_manifest"]["object_count"] == 2
        assert result["deltas_emitted"] == 4
        assert Path(result["index_delta_path"]).exists()
        print(json.dumps({
            "ok": True,
            "object_count": result["partition_manifest"]["object_count"],
            "deltas_emitted": result["deltas_emitted"],
        }, indent=2))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Emit partition manifests and index deltas from JSONL objects.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--partition-id")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--source-surface-id", default="")
    parser.add_argument("--tenant-id", default="")
    parser.add_argument("--emit", nargs="*", default=["keyword", "facet", "freshness", "quality"])
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    missing = [name for name in ("input", "partition_id", "output_dir") if getattr(args, name) is None]
    if missing:
        parser.error("missing required arguments: " + ", ".join("--" + m.replace("_", "-") for m in missing))
    result = emit_index_delta(
        input_path=args.input,
        partition_id=args.partition_id,
        output_dir=args.output_dir,
        run_id=args.run_id,
        source_surface_id=args.source_surface_id,
        tenant_id=args.tenant_id,
        emit=args.emit,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_main())

