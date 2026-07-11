#!/usr/bin/env python3
"""Replay public-source object-factory jobs into resumable run records.

The public catalog should publish job plans and replay/audit metadata, not raw
scraped bodies. This module consumes queue-ready object-factory jobs and emits
deterministic run records, checkpoints, and partition manifests that later
workers can use for Postgres/pgvector bulk loads and idempotent resumes.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[2])
DEFAULT_OUT = _resource("dist") / "public-source-job-replay"


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _safe_slug(value: str) -> str:
    out = []
    for ch in value.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in {"/", "_", ".", " ", ":"}:
            out.append("-")
    return "-".join("".join(out).split("-"))[:96] or "item"


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected JSON object")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in records),
        encoding="utf-8",
    )


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False), encoding="utf-8")


def _load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"version": "0.1.0", "completed_job_ids": [], "job_hashes": {}}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected checkpoint object")
    value.setdefault("completed_job_ids", [])
    value.setdefault("job_hashes", {})
    return value


def _job_expected_row_families(job_type: str) -> list[str]:
    mapping = {
        "source_discovery": ["source_record"],
        "source_snapshot": ["source_record"],
        "page_to_markdown": ["source_record"],
        "source_ingest": ["normalized_object"],
        "entity_linking": ["canonical_entity", "object_entity_ref"],
        "fuzzy_dedupe": ["dedupe_cluster"],
        "dedupe_index": ["index_record", "object_embedding", "label_assignment", "dimension_value"],
        "publish_review": ["review_ticket"],
    }
    return mapping.get(job_type, ["worker_audit"])


def _run_record(job: dict[str, Any], *, run_id: str, worker_image: str, dry_run: bool) -> dict[str, Any]:
    inputs = job.get("inputs") if isinstance(job.get("inputs"), dict) else {}
    policy = job.get("policy") if isinstance(job.get("policy"), dict) else {}
    blueprint_id = str(inputs.get("blueprint_id") or "unknown-blueprint")
    job_type = str(job.get("job_type") or "unknown")
    row_families = _job_expected_row_families(job_type)
    return {
        "run_record_id": f"run/{run_id}/{_safe_slug(str(job.get('job_id', job_type)))}",
        "run_id": run_id,
        "job_id": job.get("job_id"),
        "job_type": job_type,
        "tenant_id": job.get("tenant_id"),
        "source_record_id": job.get("source_record_id"),
        "blueprint_id": blueprint_id,
        "shard_id": inputs.get("shard_id"),
        "status": "succeeded" if dry_run else "planned",
        "dry_run": dry_run,
        "input_hash": _hash_json(job),
        "expected_row_families": row_families,
        "output_pointers": {
            family: f"object-storage://public-source/{run_id}/{_safe_slug(blueprint_id)}/{family}.jsonl"
            for family in row_families
        },
        "policy_summary": {
            "trust_boundary": policy.get("trust_boundary"),
            "privacy_boundary": policy.get("privacy_boundary"),
            "redact_before_external_model": policy.get("redact_before_external_model"),
            "excluded_scopes": policy.get("excluded_scopes", []),
            "max_usd": policy.get("max_usd"),
        },
        "audit": {
            "worker_id": f"local-replay-{job_type}",
            "worker_image": worker_image,
            "started_at": _utc_now(),
            "finished_at": _utc_now(),
            "source_body_stored": False,
            "raw_private_data_stored": False,
        },
    }


def _manifest_for_family(
    *,
    run_id: str,
    family: str,
    records: list[dict[str, Any]],
    output_dir: Path,
) -> dict[str, Any]:
    shard_path = output_dir / "job-run-records.jsonl"
    kind_map = {
        "source_record": "source_objects",
        "normalized_object": "normalized_objects",
        "canonical_entity": "graph_edges",
        "object_entity_ref": "graph_edges",
        "dedupe_cluster": "graph_edges",
        "index_record": "index_records",
        "object_embedding": "embeddings",
        "label_assignment": "labels",
        "dimension_value": "dimensions",
        "review_ticket": "review_tickets",
    }
    blueprint_ids = sorted({str(r.get("blueprint_id")) for r in records if r.get("blueprint_id")})
    return {
        "partition_id": f"partition/{run_id}/{family}",
        "partition_kind": kind_map.get(family, "source_objects"),
        "run_id": run_id,
        "source_surface_id": ",".join(blueprint_ids[:8]),
        "tenant_id": records[0].get("tenant_id", "") if records else "",
        "object_count": len(records),
        "shard_paths": [str(shard_path.relative_to(ROOT)) if shard_path.is_relative_to(ROOT) else str(shard_path)],
        "index_delta_paths": [],
        "schema_versions": {
            "object_factory_job": "schemas/object-factory-job.schema.json",
            "partition_manifest": "schemas/partition-manifest.schema.json",
        },
        "content_hash": _hash_json(records),
        "created": _utc_now(),
        "updated": _utc_now(),
        "trust_boundary": "mixed",
        "privacy_summary": {
            "contains_pii": False,
            "redacted": True,
            "publication_allowed": True,
            "source_body_stored": False,
        },
        "quality_summary": {
            "job_count": len(records),
            "blueprint_count": len(blueprint_ids),
            "dry_run": all(r.get("dry_run") for r in records),
        },
    }


def replay_public_source_jobs(
    *,
    jobs: list[dict[str, Any]],
    output_dir: str | None = None,
    run_id: str | None = None,
    dry_run: bool = True,
    resume: bool = True,
    worker_image: str = "open-harness/local-public-source-replay:latest",
) -> dict[str, Any]:
    """Emit resumable run records and partition manifests for queued jobs."""
    run_id = run_id or f"public-source-replay-{time.strftime('%Y%m%d%H%M%S', time.gmtime())}"
    out = Path(output_dir) if output_dir else DEFAULT_OUT / run_id
    checkpoint_path = out / "checkpoint.json"
    checkpoint = _load_checkpoint(checkpoint_path) if resume else {"completed_job_ids": [], "job_hashes": {}}
    completed = set(str(v) for v in checkpoint.get("completed_job_ids", []))
    job_hashes = dict(checkpoint.get("job_hashes", {}))

    run_records: list[dict[str, Any]] = []
    skipped = 0
    for job in jobs:
        job_id = str(job.get("job_id") or "")
        if not job_id:
            raise ValueError("job missing job_id")
        current_hash = _hash_json(job)
        if resume and job_id in completed and job_hashes.get(job_id) == current_hash:
            skipped += 1
            continue
        run_records.append(_run_record(job, run_id=run_id, worker_image=worker_image, dry_run=dry_run))
        completed.add(job_id)
        job_hashes[job_id] = current_hash

    records_path = out / "job-run-records.jsonl"
    prior_run_records = _read_jsonl(records_path)
    prior_ids = {str(row.get("run_record_id")) for row in prior_run_records}
    new_run_records = [
        row for row in run_records
        if str(row.get("run_record_id")) not in prior_ids
    ]
    all_run_records = prior_run_records + new_run_records
    _write_jsonl(records_path, all_run_records)

    by_family: dict[str, list[dict[str, Any]]] = {}
    for record in all_run_records:
        for family in record.get("expected_row_families", []):
            by_family.setdefault(str(family), []).append(record)

    manifests = [
        _manifest_for_family(run_id=run_id, family=family, records=records, output_dir=out)
        for family, records in sorted(by_family.items())
    ]
    _write_jsonl(out / "partition-manifests.jsonl", manifests)
    for manifest in manifests:
        _write_json(out / _safe_slug(manifest["partition_id"]) / "partition-manifest.json", manifest)

    checkpoint = {
        "version": "0.1.0",
        "run_id": run_id,
        "updated": _utc_now(),
        "completed_job_ids": sorted(completed),
        "job_hashes": job_hashes,
        "output_dir": str(out),
    }
    _write_json(checkpoint_path, checkpoint)

    job_counts: dict[str, int] = {}
    for job in jobs:
        job_type = str(job.get("job_type") or "unknown")
        job_counts[job_type] = job_counts.get(job_type, 0) + 1

    return {
        "output_dir": str(out),
        "run_id": run_id,
        "input_job_count": len(jobs),
        "executed_job_count": len(run_records),
        "skipped_job_count": skipped,
        "partition_count": len(manifests),
        "job_counts_by_type": job_counts,
        "files": {
            "job_run_records": str(records_path),
            "partition_manifests": str(out / "partition-manifests.jsonl"),
            "checkpoint": str(checkpoint_path),
        },
        "warnings": [
            "dry_run replay emits execution metadata and output pointers only; it does not fetch source bodies",
        ] if dry_run else [],
    }


def _sample_jobs() -> list[dict[str, Any]]:
    base = {
        "tenant_id": "tenant-public-catalog",
        "source_record_id": "source/public-source-blueprint/demo",
        "status": "queued",
        "inputs": {
            "blueprint_id": "demo-source-blueprint",
            "shard_id": "shard/demo",
            "expected_objects": ["fact", "checklist_item"],
        },
        "policy": {
            "trust_boundary": "external",
            "privacy_boundary": "public",
            "redact_before_external_model": True,
            "excluded_scopes": ["insurance"],
            "max_usd": 1.0,
        },
    }
    return [
        {**base, "job_id": "job/demo/01-source_discovery", "job_type": "source_discovery"},
        {**base, "job_id": "job/demo/02-source_ingest", "job_type": "source_ingest", "parent_job_ids": ["job/demo/01-source_discovery"]},
        {**base, "job_id": "job/demo/03-publish_review", "job_type": "publish_review", "parent_job_ids": ["job/demo/02-source_ingest"]},
    ]


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        result = replay_public_source_jobs(jobs=_sample_jobs(), output_dir=tmp, run_id="self-test")
        assert result["input_job_count"] == 3
        assert result["executed_job_count"] == 3
        assert result["partition_count"] >= 3
        resumed = replay_public_source_jobs(jobs=_sample_jobs(), output_dir=tmp, run_id="self-test")
        assert resumed["skipped_job_count"] == 3
    print(json.dumps({"ok": True, "result": result}, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay queued public-source scan jobs into run records.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--jobs-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--run-id")
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--execute", action="store_true", help="Mark records planned instead of dry-run succeeded")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.jobs_jsonl:
        parser.error("--jobs-jsonl is required unless --self-test is used")
    result = replay_public_source_jobs(
        jobs=_read_jsonl(args.jobs_jsonl),
        output_dir=args.output_dir,
        run_id=args.run_id,
        dry_run=not args.execute,
        resume=not args.no_resume,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
