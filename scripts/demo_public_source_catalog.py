#!/usr/bin/env python3
"""Build a Baltor demo source catalog pack.

This does not download corpuses. It converts a curated public-source catalog into
source records, context objects, a source-selection matrix, a context pack, and a
receipt that can drive future corpus/repo demos.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from hashlib import sha256
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CATALOG = REPO_ROOT / "data" / "baltor-demo-source-catalog.json"
DEFAULT_OUT_DIR = REPO_ROOT / "site" / "baltor-demos" / "public-source-catalog"
PIPELINE_ID = "baltor.demo.public-source-catalog"
SOURCE_HANDLE_PREFIX = "ctx://baltor-demo/source-catalog"


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def stable_hash(payload: Any) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + sha256(body).hexdigest()


def slug(value: object) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "-" for ch in str(value or ""))
    return "-".join(part for part in text.split("-") if part)[:96] or "unknown"


def load_catalog(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError(f"Expected a list catalog at {path}")
    return [dict(item) for item in data if isinstance(item, dict)]


def handle(entry: dict[str, Any]) -> str:
    return f"{SOURCE_HANDLE_PREFIX}/{slug(entry.get('source_id') or entry.get('name'))}"


def source_record(entry: dict[str, Any], generated_at: str) -> dict[str, Any]:
    body = {
        "source_id": entry.get("source_id"),
        "name": entry.get("name"),
        "source_url": entry.get("source_url"),
        "api_url": entry.get("api_url"),
        "domain": entry.get("domain"),
        "demo_pack_type": entry.get("demo_pack_type"),
        "pipeline_fit": entry.get("pipeline_fit") or [],
        "safe_claims": entry.get("safe_claims") or [],
        "blocked_claims": entry.get("blocked_claims") or [],
        "caveats": entry.get("caveats") or [],
    }
    official = entry.get("source_role") in {"official_authority", "public_register"}
    return {
        "source_record_id": handle(entry),
        "source_type": entry.get("source_type") or "web_page",
        "source_url": entry.get("source_url"),
        "publisher": entry.get("publisher") or "unknown",
        "license": "Public source metadata catalog entry; verify source-specific terms before live ingestion",
        "source_role": entry.get("source_role") or "credible_secondary",
        "trust_tier": "official_or_primary" if official else "primary_or_reference",
        "trust_score": 0.85 if official else 0.68,
        "trust_signals": {
            "official_domain": official,
            "https": str(entry.get("source_url") or "").startswith("https://"),
            "canonical_url": entry.get("source_url"),
            "publisher_identity_present": bool(entry.get("publisher")),
            "updated_at_present": False,
        },
        "injection_risk": 0.08,
        "injection_flags": [],
        "privacy_boundary": "public",
        "freshness": "catalog_metadata_requires_live_cdc",
        "retrieved_at": generated_at,
        "effective_date": generated_at[:10],
        "content_hash": stable_hash(body),
        "language": "en",
        "jurisdiction": "US" if official else "global",
        "body": body,
    }


def context_object(entry: dict[str, Any], generated_at: str) -> dict[str, Any]:
    source_id = slug(entry.get("source_id") or entry.get("name"))
    source_handle = handle(entry)
    return {
        "kind": "baltor.context-object",
        "context_object_id": f"context-object/demo-source-{source_id}",
        "current_version_id": f"context-version/demo-source-{source_id}-{stable_hash(entry)[7:19]}",
        "source_system": "baltor_demo_source_catalog",
        "native_id": str(entry.get("source_id") or source_id),
        "source_url": entry.get("source_url"),
        "classification": "public",
        "object_type": "dataset" if entry.get("source_type") != "repository_file" else "repo",
        "title": str(entry.get("name") or source_id),
        "summary": (
            f"Public demo source candidate for {entry.get('domain')}; recommended pack type "
            f"{entry.get('demo_pack_type')}."
        ),
        "body": {
            "publisher": entry.get("publisher"),
            "domain": entry.get("domain"),
            "api_url": entry.get("api_url"),
            "demo_pack_type": entry.get("demo_pack_type"),
            "pipeline_fit": entry.get("pipeline_fit") or [],
            "safe_claims": entry.get("safe_claims") or [],
            "blocked_claims": entry.get("blocked_claims") or [],
            "caveats": entry.get("caveats") or [],
        },
        "facets": {
            "demo_source": {
                "domain": entry.get("domain"),
                "source_role": entry.get("source_role"),
                "pack_type": entry.get("demo_pack_type"),
            }
        },
        "five_w_one_h": {
            "who": {"actors": [str(entry.get("publisher") or "unknown publisher")], "audience": ["Baltor demo builders"]},
            "what": {"entities": [str(entry.get("name") or "")], "topics": entry.get("pipeline_fit") or []},
            "when": {"cataloged_at": generated_at},
            "where": {"digital_locations": [str(entry.get("source_url") or "")]},
            "why": {"goals": ["showcase full Baltor context pipeline"], "drivers": ["public source availability"]},
            "how": {"methods": ["source catalog normalization", "demo pack planning"]},
        },
        "source_handles": [source_handle],
        "evidence": [{"source_handle": source_handle, "selector_type": "DataPositionSelector", "selector": {"field": "source_id"}}],
        "provenance": {
            "wasDerivedFrom": [source_handle],
            "wasGeneratedBy": PIPELINE_ID,
            "generatedAtTime": generated_at,
            "wasAttributedTo": "baltor-demo-source-catalog-builder",
            "content_hash": stable_hash(entry),
            "pipeline_id": PIPELINE_ID,
        },
        "lineage": {"run_id": f"run-demo-source-catalog-{stable_hash(entry)[7:19]}", "job_name": PIPELINE_ID, "inputs": [source_handle]},
        "created_at": generated_at,
        "policy": {
            "derived_context": True,
            "promotion_allowed": True,
            "raw_source_dump_allowed": False,
            "requires_refresh": True,
            "source_scope_only": True,
            "block_global_memory_promotion": False,
            "acl_filter_applied": True,
            "prompt_injection_checked": False,
            "demo_only": True,
        },
    }


def build_matrix(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for entry in entries:
        fit = entry.get("pipeline_fit") or []
        matrix.append(
            {
                "source_id": entry.get("source_id"),
                "name": entry.get("name"),
                "domain": entry.get("domain"),
                "pack_type": entry.get("demo_pack_type"),
                "has_api": bool(entry.get("api_url")),
                "shows_source_records": "source_records" in fit or "source_discovery" in fit,
                "shows_codegraph": "CodeGraph" in fit or "RepoDirectory" in fit,
                "shows_docgraph": "DocGraph" in fit,
                "shows_orggraph": "OrgGraph_patch_owners" in fit,
                "shows_policy": any(term in fit for term in ("priority_policy", "policy_caveats")),
                "shows_receipt": "context_receipt" in fit,
                "blocked_claim_count": len(entry.get("blocked_claims") or []),
                "caveat_count": len(entry.get("caveats") or []),
            }
        )
    return matrix


def build_pack(entries: list[dict[str, Any]], objects: list[dict[str, Any]], matrix: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    source_handles = [source_handle for obj in objects for source_handle in obj["source_handles"]]
    domains = Counter(str(entry.get("domain") or "unknown") for entry in entries)
    pack_types = Counter(str(entry.get("demo_pack_type") or "custom") for entry in entries)
    return {
        "kind": "baltor.context-pack",
        "context_pack_id": f"context-pack/public-source-demo-catalog-{stable_hash(source_handles)[7:19]}",
        "pack_type": "custom",
        "task": "Plan public data and repo demos that showcase the full Baltor context pipeline.",
        "query": "Which public sources can demonstrate source records, graph context, verification policy, and context receipts?",
        "object_ids": [obj["context_object_id"] for obj in objects],
        "summary": (
            f"Cataloged {len(entries)} public demo source candidates across {len(domains)} domains. "
            "Use these to build separate corpus, security, finance, compliance, health, and CodeGraph demos."
        ),
        "claims": [
            {
                "claim": f"The demo catalog contains {len(entries)} public source candidates.",
                "evidence_type": "catalog_count",
                "source_handles": source_handles,
                "confidence": 1.0,
            },
            {
                "claim": f"The catalog covers {len(domains)} domains: {', '.join(sorted(domains))}.",
                "evidence_type": "catalog_field_aggregate",
                "source_handles": source_handles,
                "confidence": 0.95,
            },
            {
                "claim": f"The catalog contains {len(pack_types)} recommended pack types: {', '.join(sorted(pack_types))}.",
                "evidence_type": "catalog_field_aggregate",
                "source_handles": source_handles,
                "confidence": 0.95,
            },
        ],
        "risks": [
            {
                "risk": "Catalog metadata is not proof that a live endpoint is currently reachable or permitted for bulk use.",
                "severity": "medium",
                "control": "Run endpoint-specific health checks and terms review before live ingestion.",
            },
            {
                "risk": "Some sources contain unverified reports or allegations.",
                "severity": "high",
                "control": "Keep safe_claims and blocked_claims attached to every source and receipt.",
            },
            {
                "risk": "Public source APIs can have rate limits and changing schemas.",
                "severity": "medium",
                "control": "Use CDC, content hashes, source handles, and adapter-specific fetch caps.",
            },
        ],
        "facets": {
            "domains": dict(sorted(domains.items())),
            "pack_types": dict(sorted(pack_types.items())),
            "matrix": matrix,
        },
        "source_handles": source_handles,
        "trace_id": f"trace-public-source-catalog-{stable_hash(source_handles)[7:19]}",
        "token_budget": 2400,
        "token_count": 900,
        "policy": {
            "privacy_boundary": "public",
            "raw_source_dump_allowed": False,
            "live_fetch_required": False,
            "requires_source_specific_terms_review": True,
            "requires_reverification": True,
        },
        "created_at": generated_at,
    }


def build_receipt(pack: dict[str, Any], source_records: list[dict[str, Any]], generated_at: str) -> dict[str, Any]:
    return {
        "kind": "baltor.context-receipt",
        "receipt_id": "receipt-" + pack["context_pack_id"].split("/")[-1],
        "pack_id": pack["context_pack_id"],
        "generated_at": generated_at,
        "pipeline_id": PIPELINE_ID,
        "sources_used": [record["source_record_id"] for record in source_records],
        "claims_included": [claim["claim"] for claim in pack.get("claims", [])],
        "claims_excluded": [
            "Any claim that live endpoints were fetched successfully.",
            "Any source-specific factual claim not backed by that source's adapter.",
            "Any claim that public reports or allegations are verified truth.",
        ],
        "conflicts_disclosed": [],
        "policy_decision": {
            "decision": "allow_demo_catalog_pack",
            "reason": "public metadata catalog only; no raw live corpus ingest",
        },
        "retrieval_policy": {
            "live_fetch": False,
            "raw_dump_storage": False,
            "source_specific_terms_review_required": True,
        },
        "trace_id": pack["trace_id"],
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_summary(pack: dict[str, Any]) -> str:
    matrix = pack.get("facets", {}).get("matrix", [])
    lines = [
        "# Public Source Demo Catalog",
        "",
        pack["summary"],
        "",
        "## Demo Sources",
        "",
    ]
    for row in matrix:
        flags = []
        if row["shows_codegraph"]:
            flags.append("CodeGraph")
        if row["shows_docgraph"]:
            flags.append("DocGraph")
        if row["shows_orggraph"]:
            flags.append("OrgGraph")
        if row["shows_policy"]:
            flags.append("policy")
        if row["shows_receipt"]:
            flags.append("receipt")
        lines.append(f"- **{row['name']}**: `{row['pack_type']}` / `{row['domain']}` / {', '.join(flags) or 'source records'}")
    lines.extend(["", "## Claims", ""])
    for claim in pack.get("claims", []):
        lines.append(f"- {claim['claim']}")
    lines.extend(["", "## Risks", ""])
    for risk in pack.get("risks", []):
        lines.append(f"- **{risk['severity']}**: {risk['risk']}")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> dict[str, Any]:
    generated_at = now_iso()
    entries = load_catalog(args.catalog)
    source_records = [source_record(entry, generated_at) for entry in entries]
    objects = [context_object(entry, generated_at) for entry in entries]
    matrix = build_matrix(entries)
    pack = build_pack(entries, objects, matrix, generated_at)
    receipt = build_receipt(pack, source_records, generated_at)
    out_dir = args.out_dir
    write_json(out_dir / "source-records.json", source_records)
    write_json(out_dir / "context-objects.json", objects)
    write_json(out_dir / "demo-matrix.json", matrix)
    write_json(out_dir / "context-pack.json", pack)
    write_json(out_dir / "context-receipt.json", receipt)
    (out_dir / "README.md").write_text(markdown_summary(pack) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "source_count": len(entries),
        "out_dir": str(out_dir),
        "pack_id": pack["context_pack_id"],
        "trace_id": pack["trace_id"],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    result = run(parse_args(argv or sys.argv[1:]))
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
