from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


JOB_SEQUENCE = [
    ("model_repo_discovery", "discover model repositories, collections, spaces, and model-tree links"),
    ("model_card_snapshot", "capture public model card metadata and immutable revision pointers"),
    ("model_metadata_parse", "parse pipeline tags, datasets, license, base model, evals, and paper links"),
    ("task_context_normalize", "normalize task shape, label schema, limitations, and replacement routes"),
    ("dataset_eval_linking", "link dataset cards, benchmark names, metrics, papers, and leaderboards"),
    ("entity_linking", "link publishers, models, datasets, tasks, domains, and organizations"),
    ("fuzzy_dedupe", "cluster duplicate or near-duplicate model-derived primitive candidates"),
    ("primitive_index", "emit keyword, vector, graph, facet, quality, and cost-route index records"),
    ("publish_review", "route high-risk, medical, legal, privacy, safety, or licensing-sensitive outputs"),
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
    return "".join(cleaned).strip("-")[:80] or "unknown"


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


def _risk_tier(signal: dict[str, Any]) -> str:
    if str(signal.get("review_priority", "")).lower() == "high":
        return "high"
    domains = {str(item) for item in signal.get("domain_signal", []) or []}
    if domains.intersection({"healthcare", "legal", "privacy", "security"}):
        return "high"
    return "medium"


def _policy(signal: dict[str, Any], scan_policy: dict[str, Any], excluded_scopes: list[str]) -> dict[str, Any]:
    return {
        "trust_boundary": "external",
        "allowed_model_boundaries": scan_policy.get("allowed_model_boundaries", ["local", "hub"]),
        "redact_before_external_model": True,
        "max_usd": scan_policy.get("max_usd_per_model_signal", 0.75),
        "license_policy": "metadata_and_citation_first",
        "privacy_boundary": "public_model_metadata_only",
        "trust_tier": "public",
        "excluded_scopes": sorted(set(excluded_scopes + list(signal.get("excluded_scopes", []) or []))),
        "do_not_download_weights": scan_policy.get("do_not_download_weights", True),
        "do_not_store_training_data": True,
        "do_not_republish_model_card_body_without_license": True,
        "route_high_impact_domains_to_review": True,
    }


def _expected_outputs(job_type: str) -> list[str]:
    return {
        "model_repo_discovery": ["model_repo_ref", "collection_ref", "space_ref", "next_cursor"],
        "model_card_snapshot": ["model_card_pointer", "revision", "content_hash", "retrieved_at"],
        "model_metadata_parse": ["pipeline_tag", "datasets", "base_model", "license", "eval_results", "paper_links"],
        "task_context_normalize": ["task_definition", "label_schema", "input_output_contract", "limitations"],
        "dataset_eval_linking": ["dataset_ref", "benchmark_ref", "metric_ref", "paper_ref"],
        "entity_linking": ["canonical_entity", "object_entity_ref", "unresolved_mentions"],
        "fuzzy_dedupe": ["dedupe_cluster", "duplicate_candidates"],
        "primitive_index": ["index_record", "object_embedding", "label_assignment", "dimension_value"],
        "publish_review": ["review_ticket", "promotion_hold"],
    }.get(job_type, [])


def _job(
    *,
    signal: dict[str, Any],
    job_type: str,
    shard_id: str,
    sequence_index: int,
    tenant_id: str,
    parent_job_ids: list[str],
    scan_policy: dict[str, Any],
    excluded_scopes: list[str],
    now: str,
) -> dict[str, Any]:
    signal_id = str(signal.get("id", "specialized-model-signal"))
    source_model_id = str(signal.get("source_model_id", signal_id))
    job_id = f"job/specialized-model-card/{_safe_slug(source_model_id)}/{sequence_index:02d}-{job_type}/{shard_id}"
    source_record_id = f"source/specialized-model-card/{_safe_slug(source_model_id)}"
    return {
        "job_id": job_id,
        "job_type": job_type,
        "tenant_id": tenant_id,
        "source_record_id": source_record_id,
        "parent_job_ids": parent_job_ids,
        "status": "queued",
        "inputs": {
            "signal_id": signal_id,
            "source_model_id": source_model_id,
            "publisher": signal.get("publisher", ""),
            "domain_signal": signal.get("domain_signal", []),
            "task_shape": signal.get("task_shape", ""),
            "training_context": signal.get("training_context", []),
            "eval_context": signal.get("eval_context", []),
            "labels_or_outputs": signal.get("labels_or_outputs", []),
            "reusable_primitives": signal.get("reusable_primitives", []),
            "replacement_routes": signal.get("replacement_routes", []),
            "review_priority": signal.get("review_priority", "medium"),
            "shard_id": shard_id,
            "cadence": scan_policy.get("cadence", "weekly"),
            "max_records": scan_policy.get("max_records_per_model_signal", 50),
            "expected_outputs": _expected_outputs(job_type),
        },
        "policy": _policy(signal, scan_policy, excluded_scopes),
        "outputs": {},
        "audit": {
            "worker_id": "",
            "worker_image": scan_policy.get("worker_image", "open-harness/object-factory-model-card:latest"),
            "git_commit": "",
            "prompt_version": "specialized-model-card-job-emitter-v1",
            "retry_count": 0,
            "review_ticket_ids": [],
            "queued_at": now,
        },
    }


def emit_specialized_model_card_scan_jobs(
    model_signals: list[dict[str, Any]],
    *,
    output_dir: str | Path | None = None,
    tenant_id: str = "tenant-public-catalog",
    scan_policy: dict[str, Any] | None = None,
    excluded_scopes: list[str] | None = None,
) -> dict[str, Any]:
    scan_policy = scan_policy or {}
    excluded_scopes = excluded_scopes or ["insurance"]
    now = datetime.now(timezone.utc).isoformat()
    out_dir = Path(output_dir) if output_dir else Path(tempfile.mkdtemp(prefix="ohh-model-card-jobs-"))
    jobs: list[dict[str, Any]] = []
    manifests: list[dict[str, Any]] = []
    for signal in model_signals:
        source_model_id = str(signal.get("source_model_id", signal.get("id", "model")))
        shard_seed = {
            "source_model_id": source_model_id,
            "publisher": signal.get("publisher", ""),
            "task_shape": signal.get("task_shape", ""),
            "cadence": scan_policy.get("cadence", "weekly"),
        }
        shard_id = f"shard/{_hash_json(shard_seed)[:16]}"
        parent_job_ids: list[str] = []
        signal_job_ids: list[str] = []
        for index, (job_type, _) in enumerate(JOB_SEQUENCE, 1):
            job = _job(
                signal=signal,
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
            signal_job_ids.append(job["job_id"])
            parent_job_ids = [job["job_id"]]
        manifests.append(
            {
                "signal_id": signal.get("id", ""),
                "source_model_id": source_model_id,
                "publisher": signal.get("publisher", ""),
                "task_shape": signal.get("task_shape", ""),
                "shard_id": shard_id,
                "cadence": scan_policy.get("cadence", "weekly"),
                "job_ids": signal_job_ids,
                "job_count": len(signal_job_ids),
                "risk_tier": _risk_tier(signal),
                "review_priority": signal.get("review_priority", "medium"),
                "expected_primitive_types": signal.get("reusable_primitives", []),
            }
        )
    _write_jsonl(out_dir / "specialized-model-card-scan-jobs.jsonl", jobs)
    _write_jsonl(out_dir / "specialized-model-card-shard-manifests.jsonl", manifests)
    return {
        "output_dir": str(out_dir),
        "model_signal_count": len(model_signals),
        "job_count": len(jobs),
        "shard_count": len(manifests),
        "files": ["specialized-model-card-scan-jobs.jsonl", "specialized-model-card-shard-manifests.jsonl"],
        "job_counts_by_type": {job_type: sum(1 for job in jobs if job["job_type"] == job_type) for job_type, _ in JOB_SEQUENCE},
        "warnings": ["Jobs are public-metadata-derived and do not download model weights or copy private training data."],
    }


def _sample_model_signals() -> list[dict[str, Any]]:
    return [
        {
            "id": "specialized-model-signal/prosus-finbert-financial-sentiment",
            "source_model_id": "ProsusAI/finbert",
            "publisher": "ProsusAI",
            "domain_signal": ["finance"],
            "task_shape": "financial-text-sentiment-classification",
            "labels_or_outputs": ["positive", "negative", "neutral"],
            "reusable_primitives": ["label_schema", "classification_evaluation_harness"],
            "review_priority": "medium",
            "excluded_scopes": ["insurance"],
        }
    ]


def _self_test() -> None:
    result = emit_specialized_model_card_scan_jobs(_sample_model_signals(), scan_policy={"cadence": "daily"}, excluded_scopes=["insurance"])
    assert result["model_signal_count"] == 1
    assert result["job_count"] == len(JOB_SEQUENCE)
    jobs = _read_jsonl(Path(result["output_dir"]) / "specialized-model-card-scan-jobs.jsonl")
    assert jobs[0]["job_type"] == "model_repo_discovery"
    assert jobs[-1]["job_type"] == "publish_review"
    assert jobs[-1]["parent_job_ids"] == [jobs[-2]["job_id"]]
    assert jobs[0]["policy"]["do_not_download_weights"] is True
    assert "insurance" in jobs[0]["policy"]["excluded_scopes"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit queue-ready object-factory scan jobs from specialized model signal rows.")
    parser.add_argument("--model-signals-jsonl")
    parser.add_argument("--output-dir")
    parser.add_argument("--tenant-id", default="tenant-public-catalog")
    parser.add_argument("--cadence", default="weekly")
    parser.add_argument("--max-records-per-model-signal", type=int, default=50)
    parser.add_argument("--max-usd-per-model-signal", type=float, default=0.75)
    parser.add_argument("--excluded-scopes", nargs="*", default=["insurance"])
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        _self_test()
        print("ok")
        return 0
    if not args.model_signals_jsonl:
        parser.error("--model-signals-jsonl is required unless --self-test is used")
    scan_policy = {
        "cadence": args.cadence,
        "max_records_per_model_signal": args.max_records_per_model_signal,
        "max_usd_per_model_signal": args.max_usd_per_model_signal,
        "do_not_download_weights": True,
    }
    print(
        json.dumps(
            emit_specialized_model_card_scan_jobs(
                _read_jsonl(args.model_signals_jsonl),
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
