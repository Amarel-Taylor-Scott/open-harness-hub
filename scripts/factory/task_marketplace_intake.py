#!/usr/bin/env python3
"""Normalize task-marketplace metadata into reusable workflow primitives.

The intake is intentionally conservative: it expects metadata, aggregate task
descriptions, or user-provided exports. It does not preserve raw listing text,
worker/client identifiers, private messages, or platform-specific secrets.
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


PII_KEYS = {
    "client_name",
    "worker_name",
    "email",
    "phone",
    "address",
    "profile_url",
    "message",
    "messages",
    "conversation",
    "applicant",
    "applicants",
}


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value[:80].strip("-") or "task"


def _stable_hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: JSONL row must be an object")
        records.append(value)
    return records


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(json.dumps(record, sort_keys=True, ensure_ascii=False) for record in records)
    path.write_text(body + ("\n" if records else ""), encoding="utf-8")


def _body(record: dict[str, Any]) -> dict[str, Any]:
    value = record.get("body")
    if isinstance(value, dict):
        return value
    return record


def _privacy_findings(record: dict[str, Any]) -> list[str]:
    body = _body(record)
    findings = [f"pii_key:{key}" for key in sorted(PII_KEYS.intersection(body))]
    text = json.dumps(body, sort_keys=True, ensure_ascii=False)
    if re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", text, re.I):
        findings.append("pii_pattern:email")
    if re.search(r"\+?\d[\d\s().-]{8,}\d", text):
        findings.append("pii_pattern:phone")
    return findings


def _safe_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _source_record_id(record: dict[str, Any], sequence: int) -> str:
    value = record.get("source_record_id") or record.get("id")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return f"source/task-marketplace/{sequence:08d}"


def _task_title(record: dict[str, Any], sequence: int) -> str:
    body = _body(record)
    for key in ("task_family", "category", "title", "summary"):
        value = body.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return f"Task marketplace archetype {sequence:08d}"


def _task_object(
    record: dict[str, Any],
    sequence: int,
    retrieved_at: str,
) -> dict[str, Any]:
    body = _body(record)
    source_record_id = _source_record_id(record, sequence)
    title = _task_title(record, sequence)
    task_family = str(body.get("task_family") or title)
    skills = _safe_list(body.get("skills"))
    workflow_steps = _safe_list(body.get("workflow_steps"))
    acceptance_criteria = _safe_list(body.get("acceptance_criteria"))
    deliverables = _safe_list(body.get("deliverables"))
    risk_flags = _safe_list(body.get("risk_flags"))
    cost_signals = body.get("cost_signals") if isinstance(body.get("cost_signals"), dict) else {}
    source_url = str(record.get("source_url") or body.get("source_url") or "marketplace_metadata_or_user_export")
    publisher = str(record.get("publisher") or body.get("publisher") or "synthetic-marketplace-pattern")
    license_value = str(record.get("license") or body.get("license") or "derived-metadata-only")

    normalized_body = {
        "task_family": task_family,
        "marketplace_category": body.get("category", ""),
        "problem_statement": body.get("problem_statement", ""),
        "skills": skills,
        "workflow_steps": workflow_steps,
        "acceptance_criteria": acceptance_criteria,
        "deliverables": deliverables,
        "cost_signals": cost_signals,
        "human_in_loop": body.get("human_in_loop", True),
        "automation_opportunities": _safe_list(body.get("automation_opportunities")),
        "risk_flags": risk_flags,
        "privacy_policy": "No raw listing text, private messages, worker/client identities, contact details, or platform secrets are retained.",
    }
    object_id = f"task-archetype/{_slug(task_family)}"
    return {
        "object_id": object_id,
        "object_type": "task",
        "source_record_id": source_record_id,
        "title": title,
        "body": normalized_body,
        "canonical_entity_ids": [
            f"entity/source/{_slug(publisher)}",
            *[f"entity/skill/{_slug(skill)}" for skill in skills],
        ],
        "dedupe_cluster_id": f"dedupe/task-archetype/{_slug(task_family)}",
        "trust_tier": str(record.get("trust_tier") or "unverified_external_metadata"),
        "privacy_boundary": "metadata_only_no_pii",
        "quality_status": "candidate",
        "review_status": "review_required" if risk_flags or _privacy_findings(record) else "auto_candidate",
        "content_hash": _stable_hash(normalized_body),
        "retrieved_at": str(record.get("retrieved_at") or retrieved_at),
        "provenance": {
            "source_url": source_url,
            "publisher": publisher,
            "license": license_value,
            "collected_by": "Open Harness Hub task marketplace intake",
            "collection_method": str(record.get("source_type") or "metadata_or_user_export"),
        },
    }


def _entities_for(task: dict[str, Any]) -> list[dict[str, Any]]:
    body = task["body"]
    entities = [{
        "entity_id": task["canonical_entity_ids"][0],
        "entity_type": "source",
        "canonical_name": task["provenance"]["publisher"],
        "aliases": [],
        "description": "Task marketplace metadata or user-export source.",
        "source_record_ids": [task["source_record_id"]],
        "confidence": 0.7,
        "review_status": "review_required",
    }]
    for skill in body.get("skills", []):
        entities.append({
            "entity_id": f"entity/skill/{_slug(skill)}",
            "entity_type": "skill",
            "canonical_name": skill,
            "aliases": [],
            "description": f"Skill inferred from task marketplace archetype {task['title']}.",
            "source_record_ids": [task["source_record_id"]],
            "confidence": 0.75,
            "review_status": "candidate",
        })
    return entities


def _dedupe_cluster(task: dict[str, Any]) -> dict[str, Any]:
    return {
        "dedupe_cluster_id": task["dedupe_cluster_id"],
        "canonical_object_id": task["object_id"],
        "member_ids": [task["object_id"]],
        "status": "review_required",
        "methods": ["normalized_task_family_slug", "skill_overlap_seed"],
        "scores": {
            "exact_id": True,
            "fuzzy_ratio": 1.0,
            "entity_overlap": 1.0 if task.get("canonical_entity_ids") else 0.0,
        },
        "merge_policy": "Merge only archetypes with matching task_family and substantially overlapping skills, deliverables, and acceptance criteria.",
        "review_reason": "Marketplace task patterns can encode platform-specific or proprietary listing language; curator review required before promotion.",
    }


def _index_records(task: dict[str, Any]) -> list[dict[str, Any]]:
    body = task["body"]
    searchable = " ".join([
        task["title"],
        str(body.get("problem_statement", "")),
        " ".join(body.get("skills", [])),
        " ".join(body.get("workflow_steps", [])),
        " ".join(body.get("acceptance_criteria", [])),
        " ".join(body.get("deliverables", [])),
        " ".join(body.get("automation_opportunities", [])),
    ]).strip()
    meta = {
        "source_record_id": task["source_record_id"],
        "task_family": body.get("task_family"),
        "skills": body.get("skills", []),
        "privacy_boundary": task.get("privacy_boundary"),
        "quality_status": task.get("quality_status"),
    }
    return [
        {
            "index_record_id": f"idx:{_slug(task['object_id'])}:keyword",
            "index_kind": "keyword",
            "subject_id": task["object_id"],
            "subject_type": "normalized_object",
            "text": searchable,
            "metadata": meta,
        },
        {
            "index_record_id": f"idx:{_slug(task['object_id'])}:facet",
            "index_kind": "facet",
            "subject_id": task["object_id"],
            "subject_type": "normalized_object",
            "text": " ".join([str(body.get("marketplace_category", "")), *body.get("skills", [])]).strip(),
            "metadata": meta,
        },
    ]


def _review_tickets(task: dict[str, Any], findings: list[str]) -> list[dict[str, Any]]:
    reasons = [
        "Task marketplace archetypes require license/terms review before promotion.",
    ]
    if findings:
        reasons.append("Source metadata contained possible PII-like fields or patterns that were not retained.")
    if task["body"].get("risk_flags"):
        reasons.append("Risk flags require curator or domain expert review.")
    return [{
        "review_ticket_id": f"review/{_slug(task['object_id'])}",
        "object_id": task["object_id"],
        "source_record_id": task["source_record_id"],
        "review_type": "privacy" if findings else "curator",
        "reason": " ".join(reasons),
        "status": "open",
        "priority": "medium",
        "created_at": _utc_now(),
        "evidence": [
            {"kind": "privacy_findings", "value": findings},
            {"kind": "source_url", "value": task["provenance"]["source_url"]},
        ],
    }]


def normalize_task_marketplace_records(
    *,
    input_path: str,
    output_dir: str,
) -> dict[str, Any]:
    source = Path(input_path)
    out_dir = Path(output_dir)
    records = _read_jsonl(source)
    retrieved_at = _utc_now()

    tasks: list[dict[str, Any]] = []
    entities: dict[str, dict[str, Any]] = {}
    clusters: dict[str, dict[str, Any]] = {}
    indexes: list[dict[str, Any]] = []
    tickets: list[dict[str, Any]] = []
    privacy_findings_count = 0

    for sequence, record in enumerate(records, 1):
        findings = _privacy_findings(record)
        privacy_findings_count += len(findings)
        task = _task_object(record, sequence, retrieved_at)
        tasks.append(task)
        for entity in _entities_for(task):
            entities.setdefault(entity["entity_id"], entity)
        cluster = _dedupe_cluster(task)
        clusters.setdefault(cluster["dedupe_cluster_id"], cluster)
        indexes.extend(_index_records(task))
        tickets.extend(_review_tickets(task, findings))

    paths = {
        "normalized_objects": out_dir / "normalized-objects.jsonl",
        "entities": out_dir / "entities.jsonl",
        "dedupe_clusters": out_dir / "dedupe-clusters.jsonl",
        "index_records": out_dir / "index-records.jsonl",
        "review_tickets": out_dir / "review-tickets.jsonl",
    }
    _write_jsonl(paths["normalized_objects"], tasks)
    _write_jsonl(paths["entities"], list(entities.values()))
    _write_jsonl(paths["dedupe_clusters"], list(clusters.values()))
    _write_jsonl(paths["index_records"], indexes)
    _write_jsonl(paths["review_tickets"], tickets)
    summary = {
        "ok": True,
        "source_records": len(records),
        "normalized_objects": len(tasks),
        "entities": len(entities),
        "dedupe_clusters": len(clusters),
        "index_records": len(indexes),
        "review_tickets": len(tickets),
        "privacy_findings": privacy_findings_count,
        "paths": {key: str(path) for key, path in paths.items()},
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return summary


def _self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        source = base / "tasks.jsonl"
        source.write_text(
            "\n".join([
                json.dumps({
                    "source_record_id": "source/task-marketplace/synthetic-001",
                    "source_type": "user_upload",
                    "publisher": "synthetic-marketplace-pattern",
                    "license": "CC-BY-4.0",
                    "retrieved_at": "2026-05-25T00:00:00Z",
                    "body": {
                        "task_family": "Spreadsheet cleanup and deduplication",
                        "category": "data-operations",
                        "problem_statement": "A small business needs inconsistent spreadsheet rows normalized before import.",
                        "skills": ["spreadsheet cleanup", "deduplication", "data validation"],
                        "workflow_steps": ["Inspect columns", "Normalize formats", "Cluster likely duplicates", "Produce import-ready file"],
                        "acceptance_criteria": ["No contact details are retained in the primitive", "Duplicate decisions are explainable"],
                        "deliverables": ["cleaned table", "exception report"],
                        "automation_opportunities": ["schema inference", "fuzzy dedupe", "review ticket routing"],
                    },
                }),
                json.dumps({
                    "source_record_id": "source/task-marketplace/synthetic-002",
                    "source_type": "user_upload",
                    "publisher": "synthetic-marketplace-pattern",
                    "license": "CC-BY-4.0",
                    "retrieved_at": "2026-05-25T00:00:00Z",
                    "body": {
                        "task_family": "Local service quote comparison",
                        "category": "consumer-admin",
                        "problem_statement": "A requester needs comparable quotes summarized without exposing personal contact data.",
                        "skills": ["quote comparison", "requirements extraction", "vendor checklist"],
                        "workflow_steps": ["Extract requirements", "Normalize quote line items", "Flag missing terms", "Prepare comparison table"],
                        "acceptance_criteria": ["Sensitive contact fields are removed", "Unclear terms route to review"],
                        "deliverables": ["comparison table", "questions for vendors"],
                        "risk_flags": ["consumer_finance_or_contract_terms"],
                        "email": "synthetic@example.invalid",
                    },
                }),
            ]) + "\n",
            encoding="utf-8",
        )
        result = normalize_task_marketplace_records(input_path=str(source), output_dir=str(base / "out"))
        assert result["normalized_objects"] == 2
        assert result["index_records"] == 4
        assert result["review_tickets"] == 2
        assert result["privacy_findings"] >= 1
        print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize task marketplace metadata into reusable workflow primitives.")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--input")
    parser.add_argument("--output-dir")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.input or not args.output_dir:
        parser.error("--input and --output-dir are required")
    result = normalize_task_marketplace_records(input_path=args.input, output_dir=args.output_dir)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
