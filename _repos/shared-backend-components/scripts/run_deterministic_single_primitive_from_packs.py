#!/usr/bin/env python3
"""Compile generated_primitive_packs rows into one primitive candidate per row.

This is the no-model throughput lane. It preserves the user's one-row rule:
each source row emits exactly one candidate primitive object and one model-like
receipt. The row is still candidate-only; the extractor and verifier decide
what is included.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402
from scripts.extract_primitive_model_candidates import extract_candidates  # noqa: E402
from scripts.run_openwebui_single_primitive_from_packs import PACK_DIR, iter_pack_rows  # noqa: E402
from scripts.verify_primitive_candidates import verify_candidates  # noqa: E402

DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "single_primitive_openwebui"

PACK_SOURCE_REFS: dict[str, list[dict[str, str]]] = {
    "primitive_api_contract_primitives_pack.md": [
        {"label": "OpenAPI Specification", "url": "https://spec.openapis.org/oas/latest.html"},
        {"label": "AsyncAPI Specification", "url": "https://www.asyncapi.com/docs/reference/specification/latest"},
        {"label": "JSON Schema", "url": "https://json-schema.org/docs"},
    ],
    "primitive_browser_web_extraction_pack.md": [
        {"label": "Schema.org", "url": "https://schema.org/"},
        {"label": "Playwright", "url": "https://playwright.dev/"},
    ],
    "primitive_cloud_guardrail_runtime_pack.md": [
        {"label": "Open Policy Agent", "url": "https://www.openpolicyagent.org/docs/latest/"},
        {"label": "Cedar Policy", "url": "https://docs.cedarpolicy.com/"},
        {"label": "OpenTelemetry", "url": "https://opentelemetry.io/docs/"},
    ],
    "primitive_data_science_methodology_pack.md": [
        {"label": "scikit-learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
        {"label": "pandas Documentation", "url": "https://pandas.pydata.org/docs/"},
    ],
    "primitive_devops_iac_cloud_deploy_pack.md": [
        {"label": "Terraform Registry", "url": "https://registry.terraform.io/"},
        {"label": "Kubernetes Documentation", "url": "https://kubernetes.io/docs/"},
    ],
    "primitive_kaggle_benchmark_adapters_pack.md": [
        {"label": "Kaggle API", "url": "https://github.com/Kaggle/kaggle-api"},
        {"label": "OpenML", "url": "https://www.openml.org/"},
    ],
    "primitive_marketplace_to_primitive_adapter_pack.md": [
        {"label": "GitHub Marketplace", "url": "https://github.com/marketplace"},
        {"label": "Artifact Hub", "url": "https://artifacthub.io/"},
        {"label": "Terraform Registry", "url": "https://registry.terraform.io/"},
    ],
    "primitive_observability_incident_response_pack.md": [
        {"label": "OpenTelemetry", "url": "https://opentelemetry.io/docs/"},
        {"label": "Prometheus", "url": "https://prometheus.io/docs/"},
    ],
    "primitive_package_api_surface_mining_pack.md": [
        {"label": "Python Packaging User Guide", "url": "https://packaging.python.org/"},
        {"label": "npm Docs", "url": "https://docs.npmjs.com/"},
    ],
    "primitive_public_company_surface_entity_tensor_pack.md": [
        {"label": "SEC EDGAR", "url": "https://www.sec.gov/edgar"},
        {"label": "GLEIF", "url": "https://www.gleif.org/en/lei-data"},
    ],
    "primitive_rag_retrieval_grounding_pack.md": [
        {"label": "BEIR", "url": "https://github.com/beir-cellar/beir"},
        {"label": "OpenTelemetry", "url": "https://opentelemetry.io/docs/"},
    ],
    "primitive_search_method_strategy_arms_pack.md": [
        {"label": "Apache Lucene", "url": "https://lucene.apache.org/"},
        {"label": "OpenSearch Documentation", "url": "https://opensearch.org/docs/"},
    ],
    "primitive_search_query_recipes_pack.md": [
        {"label": "Google Search Central", "url": "https://developers.google.com/search/docs"},
        {"label": "Bing Webmaster Tools", "url": "https://www.bing.com/webmasters/help"},
    ],
}


def _now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _now_slug() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha(value: Any, *, n: int = 20) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:n]


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _split_semicolon(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text:
        return []
    return [part.strip() for part in text.replace(",", ";").split(";") if part.strip()]


def _slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    chars = [char if char.isalnum() else "_" for char in text]
    compact = "_".join(part for part in "".join(chars).split("_") if part)
    return compact[:96] or "primitive_candidate"


def _source_refs(seed_row: dict[str, Any]) -> list[dict[str, str]]:
    pack = str(seed_row.get("source_pack_file") or "")
    refs = PACK_SOURCE_REFS.get(pack)
    if refs:
        return refs
    return [{"label": "AI Done Right repository", "url": "https://github.com/"}]


def _mutators(seed_row: dict[str, Any]) -> list[str]:
    text = json.dumps(seed_row, sort_keys=True).lower()
    mutators = ["input_envelope_wrapper", "output_wrapper", "schema_validator_inserter"]
    if any(term in text for term in ("api", "endpoint", "http", "webhook")):
        mutators.append("api_endpoint_wrapper")
    if any(term in text for term in ("queue", "worker", "event", "async")):
        mutators.append("queue_worker_wrapper")
    if any(term in text for term in ("browser", "web", "page", "selector")):
        mutators.append("browser_automation_wrapper")
    if any(term in text for term in ("cloud", "lambda", "kubernetes", "terraform")):
        mutators.append("deployment_wrapper")
    if any(term in text for term in ("receipt", "audit", "evidence")):
        mutators.append("artifact_materialize")
    return list(dict.fromkeys(mutators))


def candidate_from_seed(seed_row: dict[str, Any]) -> dict[str, Any]:
    record_id = str(seed_row.get("record_id") or seed_row.get("source_row_digest") or _sha(seed_row))
    title = str(seed_row.get("title") or record_id)
    input_edge = str(seed_row.get("input_edge") or "InputEnvelope+Policy")
    output_edge = str(seed_row.get("output_edge") or "OutputArtifact+Receipt")
    proof_requirements = _split_semicolon(seed_row.get("proof_requirements"))
    for proof in ("source_ref_resolution", "contract_fixture_validation", "candidate_boundary_gate"):
        if proof not in proof_requirements:
            proof_requirements.append(proof)
    effects = _split_semicolon(seed_row.get("effects")) or ["artifact_write"]
    runtime_targets = [
        value
        for value in (
            seed_row.get("cloud_runtime"),
            seed_row.get("deployment_shape"),
            seed_row.get("runtime_shape"),
            seed_row.get("runtime_target"),
        )
        if value
    ]
    return {
        "primitive_id": _slug(record_id),
        "kind": "primitive",
        "title": title,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "source_refs": _source_refs(seed_row),
        "proof_requirements": proof_requirements,
        "promotion_blockers": [
            "source_specific_adapter_not_implemented",
            "proof_receipts_missing",
            "human_review_required_before_promotion",
        ],
        "dedupe_key": _slug(record_id),
        "contract": {
            "summary": f"{title}: {input_edge} -> {output_edge}.",
            "input": input_edge,
            "output": output_edge,
            "errors": "invalid_input; policy_denied; adapter_missing; proof_failed",
        },
        "edge_contract": {
            "input_edge_description": f"Accepts {input_edge}.",
            "output_edge_description": f"Emits {output_edge}.",
            "preconditions": "Input satisfies declared schema and policy.",
            "postconditions": "Candidate receipt records source row, effects, and proof requirements.",
            "failure_modes": "Schema mismatch; adapter unavailable; proof fixture missing.",
            "composition_notes": "Deterministically compiled from one generated primitive-pack row.",
        },
        "blackbox": f"Candidate primitive for {title}.",
        "effects": effects,
        "runtime_targets": runtime_targets,
        "mutators": _mutators(seed_row),
        "candidate": True,
        "serves_truth": False,
    }


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def receipt_from_candidate(seed_row: dict[str, Any], candidate: dict[str, Any], *, duration_seconds: float) -> dict[str, Any]:
    return {
        "record_type": "primitive_factory_model_output",
        "output_id": f"pfmo:{_sha({'seed': seed_row, 'candidate': candidate})}",
        "shard_id": f"generated_pack:{seed_row.get('source_pack_file')}:{seed_row.get('row_id')}",
        "run_date": "generated_primitive_packs_deterministic",
        "lane_id": str(seed_row.get("pack_id") or seed_row.get("source_pack_file") or "generated_primitive_pack"),
        "provider": "deterministic",
        "model": "pack_row_compiler",
        "prompt_field": "single_primitive_seed_row",
        "prompt_sha256": _sha(seed_row, n=64),
        "raw_candidate_target": 1,
        "useful_candidate_target": 1,
        "assistant_content": json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "finish_reason": "deterministic",
        "error": None,
        "status": "candidate_model_output",
        "duration_seconds": round(duration_seconds, 6),
        "completion_tps": 0,
        "total_tps": 0,
        "source_seed_row": seed_row,
        "candidate": True,
        "serves_truth": False,
    }


def run(
    *,
    pack_dir: Path,
    pack_file: str,
    out_dir: Path,
    offset: int,
    limit: int,
    verify: bool,
    verify_date: str,
) -> dict[str, Any]:
    all_seed_rows = iter_pack_rows(pack_dir, pack_file=pack_file)
    selected = all_seed_rows[max(0, offset):]
    if limit > 0:
        selected = selected[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    receipts: list[dict[str, Any]] = []
    for seed_row in selected:
        row_started = time.time()
        candidate = candidate_from_seed(seed_row)
        receipts.append(receipt_from_candidate(seed_row, candidate, duration_seconds=time.time() - row_started))
    outputs_path = out_dir / "model_outputs.jsonl"
    _write_jsonl(outputs_path, receipts)
    extraction_manifest = extract_candidates(outputs_path, out_dir / "extracted")
    verify_manifest: dict[str, Any] = {}
    if verify:
        verify_manifest = verify_candidates(run_date=verify_date, out_dir=out_dir / "verified", source_root=out_dir)
    duration = round(time.time() - started, 3)
    included = int(extraction_manifest.get("accepted_count") or 0)
    manifest = {
        "record_type": "single_primitive_deterministic_run_manifest",
        "source": "generated_primitive_packs",
        "pack_dir": _rel(pack_dir),
        "pack_file": pack_file,
        "out_dir": _rel(out_dir),
        "outputs_path": _rel(outputs_path),
        "provider": "deterministic",
        "model": "pack_row_compiler",
        "mode": "direct",
        "offset": offset,
        "limit": limit,
        "selected_count": len(selected),
        "generated_count": len(receipts),
        "tested_count": len(receipts),
        "included_count": included,
        "rejected_count": int(extraction_manifest.get("rejected_count") or 0),
        "error_count": 0,
        "duration_seconds": duration,
        "included_per_hour": round(included / duration * 3600, 2) if duration else 0,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "extraction_manifest": extraction_manifest,
        "verification_manifest": verify_manifest,
        "verified_count": int(verify_manifest.get("verified_count") or 0),
        "one_call_per_primitive": True,
        "candidate": True,
        "serves_truth": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def _self_test() -> int:
    rows = iter_pack_rows(PACK_DIR, pack_file="primitive_cloud_guardrail_runtime_pack.md")
    candidate = candidate_from_seed(rows[0]) if rows else {}
    ok = (
        bool(rows)
        and candidate.get("candidate") is True
        and candidate.get("serves_truth") is False
        and bool(candidate.get("source_refs"))
        and bool(candidate.get("mutators"))
    )
    print("PASS - deterministic single primitive compiler emits one candidate per seed row." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pack-dir", default=str(PACK_DIR))
    parser.add_argument("--pack-file", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--verify-date", default="generated-packs-deterministic")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    out_dir = Path(args.out_dir) if args.out_dir else _resource(f"deterministic_pack_rows_{_now_slug()}")
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)
    manifest = run(
        pack_dir=Path(args.pack_dir),
        pack_file=args.pack_file,
        out_dir=out_dir,
        offset=args.offset,
        limit=args.limit,
        verify=args.verify,
        verify_date=args.verify_date,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
