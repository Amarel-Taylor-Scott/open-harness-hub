from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


JOB_SEQUENCE = [
    ("source_discovery", "discover public source candidates"),
    ("source_snapshot", "capture source snapshot or archive pointer"),
    ("page_to_markdown", "convert captured source to markdown with spans"),
    ("source_ingest", "extract normalized objects from markdown"),
    ("entity_linking", "link publishers, jurisdictions, verticals, workflows, and rules"),
    ("fuzzy_dedupe", "cluster duplicate or near-duplicate extracted objects"),
    ("dedupe_index", "emit keyword, vector, graph, facet, freshness, and quality index records"),
    ("publish_review", "route high-risk or volatile outputs for curator review"),
]


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
    return "".join(cleaned).strip("-")[:72] or "unknown"


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.strip():
            value = json.loads(line)
            if isinstance(value, dict):
                rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _policy(blueprint: dict[str, Any], scan_policy: dict[str, Any], excluded_scopes: list[str]) -> dict[str, Any]:
    return {
        "trust_boundary": "external",
        "allowed_model_boundaries": scan_policy.get("allowed_model_boundaries", ["local", "hub"]),
        "redact_before_external_model": True,
        "max_usd": scan_policy.get("max_usd_per_blueprint", 2.0),
        "license_policy": blueprint.get("license_posture", "metadata_and_citation_first"),
        "privacy_boundary": blueprint.get("privacy_boundary", "public"),
        "trust_tier": blueprint.get("trust_tier", "public"),
        "excluded_scopes": sorted(set(excluded_scopes + list(blueprint.get("excluded_scope", []) or []))),
        "do_not_store_raw_private_data": True,
        "do_not_republish_source_body_without_license": True,
    }


def _job(
    *,
    blueprint: dict[str, Any],
    job_type: str,
    shard_id: str,
    sequence_index: int,
    tenant_id: str,
    parent_job_ids: list[str],
    scan_policy: dict[str, Any],
    excluded_scopes: list[str],
    now: str,
) -> dict[str, Any]:
    blueprint_id = str(blueprint.get("id", "blueprint"))
    job_id = f"job/public-source/{_safe_slug(blueprint_id)}/{sequence_index:02d}-{job_type}/{shard_id}"
    source_record_id = f"source/public-source-blueprint/{_safe_slug(blueprint_id)}"
    return {
        "job_id": job_id,
        "job_type": job_type,
        "tenant_id": tenant_id,
        "source_record_id": source_record_id,
        "parent_job_ids": parent_job_ids,
        "status": "queued",
        "inputs": {
            "blueprint_id": blueprint_id,
            "vertical": blueprint.get("vertical", ""),
            "title": blueprint.get("title", ""),
            "publisher_classes": blueprint.get("publisher_classes", []),
            "access_methods": blueprint.get("access_methods", []),
            "source_patterns": blueprint.get("source_patterns", []),
            "expected_objects": blueprint.get("expected_objects", []),
            "label_paths": blueprint.get("label_paths", []),
            "required_stages": blueprint.get("required_stages", []),
            "review_triggers": blueprint.get("review_triggers", []),
            "shard_id": shard_id,
            "cadence": scan_policy.get("cadence", "weekly"),
            "max_records": scan_policy.get("max_records_per_blueprint", 100),
            "expected_outputs": _expected_outputs(job_type),
        },
        "policy": _policy(blueprint, scan_policy, excluded_scopes),
        "outputs": {},
        "audit": {
            "worker_id": "",
            "worker_image": scan_policy.get("worker_image", "open-harness/object-factory-public-source:latest"),
            "git_commit": "",
            "prompt_version": "public-source-blueprint-job-emitter-v1",
            "retry_count": 0,
            "review_ticket_ids": [],
            "queued_at": now,
        },
    }


def _expected_outputs(job_type: str) -> list[str]:
    return {
        "source_discovery": ["source_record", "source_url", "license_notes", "next_cursor"],
        "source_snapshot": ["snapshot_pointer", "archive_url", "content_hash", "retrieved_at"],
        "page_to_markdown": ["markdown_pointer", "source_spans", "links", "conversion_warnings"],
        "source_ingest": ["normalized_object", "source_span_refs", "extraction_warnings"],
        "entity_linking": ["canonical_entity", "object_entity_ref", "unresolved_mentions"],
        "fuzzy_dedupe": ["dedupe_cluster", "duplicate_candidates"],
        "dedupe_index": ["index_record", "object_embedding", "label_assignment", "dimension_value"],
        "publish_review": ["review_ticket", "promotion_hold"],
    }.get(job_type, [])


def emit_public_source_scan_jobs(
    blueprints: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    tenant_id: str = "tenant-public-catalog",
    scan_policy: dict[str, Any] | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    scan_policy = scan_policy or {}
    excluded_scopes = excluded_scopes or ["insurance"]
    now = datetime.now(timezone.utc).isoformat()
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-public-source-jobs-"))
    jobs: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for blueprint in blueprints:
        blueprint_id = str(blueprint.get("id", "blueprint"))
        shard_seed = {
            "blueprint_id": blueprint_id,
            "source_patterns": blueprint.get("source_patterns", []),
            "access_methods": blueprint.get("access_methods", []),
            "cadence": scan_policy.get("cadence", "weekly"),
        }
        shard_id = f"shard/{_hash_json(shard_seed)[:16]}"
        parent_job_ids: list[str] = []
        blueprint_job_ids: list[str] = []
        for index, (job_type, _) in enumerate(JOB_SEQUENCE, 1):
            job = _job(
                blueprint=blueprint,
                job_type=job_type,
                shard_id=shard_id,
                sequence_index=index,
                tenant_id=tenant_id,
                parent_job_ids=parent_job_ids,
                scan_policy=scan_policy,
                excluded_scopes=excluded_scopes,
                now=now,
            )
            jobs.append(job)
            blueprint_job_ids.append(job["job_id"])
            parent_job_ids = [job["job_id"]]
        manifests.append(
            {
                "blueprint_id": blueprint_id,
                "vertical": blueprint.get("vertical", ""),
                "shard_id": shard_id,
                "cadence": scan_policy.get("cadence", "weekly"),
                "job_ids": blueprint_job_ids,
                "job_count": len(blueprint_job_ids),
                "expected_object_types": blueprint.get("expected_objects", []),
                "risk_tier": blueprint.get("risk_tier", "medium"),
                "review_triggers": blueprint.get("review_triggers", []),
            }
        )
    _write_jsonl(out_dir / "public-source-scan-jobs.jsonl", jobs)
    _write_jsonl(out_dir / "public-source-shard-manifests.jsonl", manifests)
    return {
        "output_dir": str(out_dir),
        "blueprint_count": len(blueprints),
        "job_count": len(jobs),
        "shard_count": len(manifests),
        "files": ["public-source-scan-jobs.jsonl", "public-source-shard-manifests.jsonl"],
        "job_counts_by_type": {job_type: sum(1 for job in jobs if job["job_type"] == job_type) for job_type, _ in JOB_SEQUENCE},
        "warnings": ["Jobs are blueprint-derived and do not include scraped source bodies or private data."],
    }


def _sample_blueprints() -> list[dict[str, Any]]:
    return [
        {
            "id": "labor-agency-fee-rule-blueprint",
            "title": "Labor agency fee rule",
            "vertical": "employment_agency.fee_rules",
            "publisher_classes": ["labor department"],
            "access_methods": ["official_web_page"],
            "source_patterns": ["agency fee rule pages"],
            "expected_objects": ["fee_rule_versioned_fact"],
            "label_paths": ["vertical.employment_agency.fee_rules"],
            "required_stages": ["source_governance", "archive_capture"],
            "risk_tier": "high",
            "review_triggers": ["worker-paid fee claim"],
            "excluded_scope": ["insurance"],
        }
    ]


def _self_test() -> None:
    result = emit_public_source_scan_jobs(_sample_blueprints(), scan_policy={"cadence": "daily"}, excluded_scopes=["insurance"])
    assert result["blueprint_count"] == 1
    assert result["job_count"] == len(JOB_SEQUENCE)
    jobs = _read_jsonl(Path(result["output_dir"]) / "public-source-scan-jobs.jsonl")
    assert jobs[0]["job_type"] == "source_discovery"
    assert jobs[-1]["job_type"] == "publish_review"
    assert jobs[-1]["parent_job_ids"] == [jobs[-2]["job_id"]]
    assert jobs[0]["policy"]["redact_before_external_model"] is True


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit queue-ready object-factory scan jobs from public source blueprints.")
    parser.add_argument("--blueprints-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--tenant-id", default="tenant-public-catalog")
    parser.add_argument("--cadence", default="weekly")
    parser.add_argument("--max-records-per-blueprint", type=int, default=100)
    parser.add_argument("--max-usd-per-blueprint", type=float, default=2.0)
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.blueprints_jsonl:
        parser.error("--blueprints-jsonl is required unless --self-test is used")
    scan_policy = {
        "cadence": args.cadence,
        "max_records_per_blueprint": args.max_records_per_blueprint,
        "max_usd_per_blueprint": args.max_usd_per_blueprint,
    }
    print(
        json.dumps(
            emit_public_source_scan_jobs(
                _read_jsonl(args.blueprints_jsonl),
                output_dir=args.output_dir,
                tenant_id=args.tenant_id,
                scan_policy=scan_policy,
                excluded_scopes=args.excluded_scopes,
            ),
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
