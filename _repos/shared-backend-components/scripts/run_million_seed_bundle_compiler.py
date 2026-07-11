#!/usr/bin/env python3
"""Compile the 1M primitive seed bundle into candidate primitives by shard.

This is a deterministic, checkpointed lane for scale. It processes one JSONL
seed row into one candidate primitive row, then runs the existing extractor and
candidate verifier. It does not promote truth.
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
from scripts.verify_primitive_candidates import verify_candidates  # noqa: E402

BUNDLE_ROOT = (
    _resource("data")
    / "dev-intel"
    / "primitive_million_seed_bundle"
    / "common-software-primitive-seed-bundle-million"
)
DEFAULT_OUT_ROOT = _resource("data") / "dev-intel" / "primitive_factory" / "million_seed_compiler_runs"

SOURCE_SURFACE_REFS: dict[str, list[dict[str, str]]] = {
    "asyncapi_spec": [{"label": "AsyncAPI Specification", "url": "https://www.asyncapi.com/docs/reference/specification/latest"}],
    "benchmark_task": [{"label": "OpenML", "url": "https://www.openml.org/"}],
    "ci_workflow": [{"label": "GitHub Actions", "url": "https://docs.github.com/actions"}],
    "cloud_marketplace": [{"label": "AWS Marketplace", "url": "https://aws.amazon.com/marketplace"}],
    "github_action": [{"label": "GitHub Actions", "url": "https://docs.github.com/actions"}],
    "huggingface_model": [{"label": "Hugging Face Hub", "url": "https://huggingface.co/docs/hub/index"}],
    "integration_tests": [{"label": "pytest", "url": "https://docs.pytest.org/"}],
    "mcp_registry": [{"label": "Model Context Protocol", "url": "https://modelcontextprotocol.io/"}],
    "openapi_spec": [{"label": "OpenAPI Specification", "url": "https://spec.openapis.org/oas/latest.html"}],
    "package_docs": [{"label": "Python Packaging User Guide", "url": "https://packaging.python.org/"}],
    "repo_source": [{"label": "GitHub Docs", "url": "https://docs.github.com/repositories"}],
    "schema_standard": [{"label": "JSON Schema", "url": "https://json-schema.org/docs"}],
    "terraform_registry": [{"label": "Terraform Registry", "url": "https://registry.terraform.io/"}],
    "web_docs": [{"label": "Schema.org", "url": "https://schema.org/"}],
}
DEFAULT_SOURCE_REFS = [
    {"label": "OpenAPI Specification", "url": "https://spec.openapis.org/oas/latest.html"},
    {"label": "OpenTelemetry", "url": "https://opentelemetry.io/docs/"},
]

GROUP_SEED_KINDS = {"primitive_group", "route_portfolio"}


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


def _slug(value: Any, *, n: int = 120) -> str:
    text = str(value or "").strip().lower()
    chars = [char if char.isalnum() else "_" for char in text]
    compact = "_".join(part for part in "".join(chars).split("_") if part)
    return compact[:n] or "primitive_candidate"


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _read_jsonl(path: Path, *, limit: int = 0) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if limit and len(rows) >= limit:
            break
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected object")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _source_refs(seed: dict[str, Any]) -> list[dict[str, str]]:
    source_surface = str(seed.get("source_surface") or "")
    return SOURCE_SURFACE_REFS.get(source_surface, DEFAULT_SOURCE_REFS)


def _candidate_kind(seed: dict[str, Any]) -> str:
    return "primitive_group" if str(seed.get("kind") or "") in GROUP_SEED_KINDS else "primitive"


def _group_contract(seed: dict[str, Any], input_edge: str, output_edge: str) -> dict[str, Any]:
    group_contract = seed.get("group_contract") if isinstance(seed.get("group_contract"), dict) else {}
    hidden_edges = [str(edge) for edge in _as_list(group_contract.get("hidden_member_edges"))]
    if len(hidden_edges) < 3:
        family = _slug(seed.get("family"))
        hidden_edges = [
            f"{input_edge} -> {family}_validated_input",
            f"{family}_validated_input -> {family}_route_plan",
            f"{family}_route_plan -> {output_edge}",
        ]
    return {
        "visible_input": input_edge,
        "visible_output": output_edge,
        "hidden_member_edges": hidden_edges,
        "summary": f"Resolved from seed group contract for {seed.get('title') or seed.get('seed_id')}.",
    }


def candidate_from_seed(seed: dict[str, Any]) -> dict[str, Any]:
    seed_id = str(seed.get("seed_id") or seed.get("dedupe_key") or _sha(seed))
    input_edge = str(seed.get("input_edge") or "InputEnvelope+Policy")
    output_edge = str(seed.get("output_edge") or "OutputArtifact+Receipt")
    seed_kind = str(seed.get("kind") or "primitive")
    candidate_kind = _candidate_kind(seed)
    problem_solution = seed.get("problem_solution_core") if isinstance(seed.get("problem_solution_core"), dict) else {}
    title = str(seed.get("title") or seed_id)
    family = str(seed.get("family") or "common_software")
    proof_requirements = [str(item) for item in _as_list(seed.get("proof_requirements")) if str(item).strip()]
    for proof in ("source_ref_resolution", "contract_fixture_validation", "candidate_boundary_gate"):
        if proof not in proof_requirements:
            proof_requirements.append(proof)
    effects = [str(item) for item in _as_list(seed.get("effects")) if str(item).strip()] or ["artifact_write"]
    mutators = [str(item) for item in _as_list(seed.get("mutator_chain")) if str(item).strip()]
    if not mutators:
        mutators = ["input_envelope_wrapper", "output_wrapper", "schema_validator_inserter"]
    primitive_id = f"{'grp' if candidate_kind == 'primitive_group' else 'prim'}_{_slug(seed_id)}"
    row: dict[str, Any] = {
        "primitive_id": primitive_id,
        "kind": candidate_kind,
        "title": title,
        "input_edge": input_edge,
        "output_edge": output_edge,
        "contract": {
            "summary": str(problem_solution.get("solution") or f"{title}: {input_edge} -> {output_edge}."),
            "input": input_edge,
            "output": output_edge,
            "problem": str(problem_solution.get("problem") or ""),
            "fit_when": str(problem_solution.get("fit_when") or ""),
            "avoid_when": str(problem_solution.get("avoid_when") or ""),
            "errors": "; ".join(str(item) for item in _as_list(problem_solution.get("failure_modes"))) or "proof_failed",
        },
        "edge_contract": {
            "input_edge_description": f"Accepts {input_edge}.",
            "output_edge_description": f"Emits {output_edge}.",
            "preconditions": "Input satisfies declared schema, policy, and authority boundary.",
            "postconditions": "Candidate receipt records source seed, effects, proof requirements, and blockers.",
            "failure_modes": "; ".join(str(item) for item in _as_list(problem_solution.get("failure_modes"))) or "schema_drift",
            "composition_notes": "Compiled deterministically from one million-bundle seed row.",
        },
        "blackbox": str(problem_solution.get("solution") or f"Candidate {family} primitive for {title}."),
        "effects": effects,
        "source_refs": _source_refs(seed),
        "mutators": mutators,
        "proof_requirements": proof_requirements,
        "promotion_blockers": [
            "generated_seed_requires_source_review",
            "adapter_implementation_not_verified",
            "proof_receipts_missing",
        ],
        "dedupe_key": str(seed.get("dedupe_key") or primitive_id),
        "runtime_targets": [str(seed.get("runtime_shape") or "")],
        "seed_id": seed_id,
        "seed_kind": seed_kind,
        "family": family,
        "industry": str(seed.get("industry") or ""),
        "region": str(seed.get("region") or ""),
        "policy_overlay": str(seed.get("policy_overlay") or ""),
        "human_action_core": seed.get("human_action_core") if isinstance(seed.get("human_action_core"), dict) else {},
        "rank_features": seed.get("rank_features") if isinstance(seed.get("rank_features"), dict) else {},
        "candidate": True,
        "serves_truth": False,
    }
    if candidate_kind == "primitive_group":
        row["group_contract"] = _group_contract(seed, input_edge, output_edge)
    return row


def receipt_from_candidate(seed: dict[str, Any], candidate: dict[str, Any], shard_name: str) -> dict[str, Any]:
    return {
        "record_type": "primitive_factory_model_output",
        "output_id": f"pfmo:{_sha({'seed': seed.get('seed_id'), 'candidate': candidate})}",
        "shard_id": f"million_seed:{shard_name}:{seed.get('seed_id')}",
        "run_date": "million_seed_bundle_deterministic",
        "lane_id": "million_seed_bundle",
        "provider": "deterministic",
        "model": "million_seed_row_compiler",
        "prompt_field": "million_seed_row",
        "prompt_sha256": _sha(seed, n=64),
        "raw_candidate_target": 1,
        "useful_candidate_target": 1,
        "assistant_content": json.dumps(candidate, sort_keys=True, separators=(",", ":"), ensure_ascii=True),
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "finish_reason": "deterministic",
        "error": None,
        "status": "candidate_model_output",
        "source_seed_id": seed.get("seed_id"),
        "candidate": True,
        "serves_truth": False,
    }


def process_shard(*, shard_path: Path, out_dir: Path, limit: int, verify: bool, verify_date: str) -> dict[str, Any]:
    started = time.time()
    seeds = _read_jsonl(shard_path, limit=limit)
    receipts = [receipt_from_candidate(seed, candidate_from_seed(seed), shard_path.name) for seed in seeds]
    outputs_path = out_dir / "model_outputs.jsonl"
    _write_jsonl(outputs_path, receipts)
    extraction_manifest = extract_candidates(outputs_path, out_dir / "extracted")
    verification_manifest: dict[str, Any] = {}
    if verify:
        verification_manifest = verify_candidates(run_date=verify_date, out_dir=out_dir / "verified", source_root=out_dir)
    duration = round(time.time() - started, 3)
    included = int(extraction_manifest.get("accepted_count") or 0)
    manifest = {
        "record_type": "million_seed_shard_compile_manifest",
        "shard_path": _rel(shard_path),
        "out_dir": _rel(out_dir),
        "outputs_path": _rel(outputs_path),
        "selected_count": len(seeds),
        "generated_count": len(receipts),
        "tested_count": len(receipts),
        "included_count": included,
        "rejected_count": int(extraction_manifest.get("rejected_count") or 0),
        "verified_count": int(verification_manifest.get("verified_count") or 0),
        "verification_rejected_count": int(verification_manifest.get("rejected_count") or 0),
        "verification_duplicate_count": int(verification_manifest.get("duplicate_count") or 0),
        "duration_seconds": duration,
        "included_per_hour": round(included / duration * 3600, 2) if duration else 0,
        "verified_per_hour": round(int(verification_manifest.get("verified_count") or 0) / duration * 3600, 2) if duration else 0,
        "extraction_manifest": extraction_manifest,
        "verification_manifest": verification_manifest,
        "provider": "deterministic",
        "model": "million_seed_row_compiler",
        "candidate": True,
        "serves_truth": False,
    }
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def run(*, bundle_root: Path, out_root: Path, start_shard: int, shard_count: int, limit_per_shard: int, verify: bool) -> dict[str, Any]:
    run_started = time.time()
    shard_paths = sorted((bundle_root / "shards").glob("primitive_seed_shard_*.jsonl"))
    selected_paths = shard_paths[start_shard:start_shard + shard_count if shard_count > 0 else None]
    out_root.mkdir(parents=True, exist_ok=True)
    manifests: list[dict[str, Any]] = []
    for shard_path in selected_paths:
        shard_index = shard_path.stem.rsplit("_", 1)[-1]
        shard_out = out_root / f"shard_{shard_index}"
        verify_date = f"million-seed-{shard_index}"
        manifest = process_shard(
            shard_path=shard_path,
            out_dir=shard_out,
            limit=limit_per_shard,
            verify=verify,
            verify_date=verify_date,
        )
        manifests.append(manifest)
    duration = round(time.time() - run_started, 3)
    totals = {
        "shards_processed": len(manifests),
        "selected_count": sum(int(m.get("selected_count") or 0) for m in manifests),
        "generated_count": sum(int(m.get("generated_count") or 0) for m in manifests),
        "tested_count": sum(int(m.get("tested_count") or 0) for m in manifests),
        "included_count": sum(int(m.get("included_count") or 0) for m in manifests),
        "rejected_count": sum(int(m.get("rejected_count") or 0) for m in manifests),
        "verified_count": sum(int(m.get("verified_count") or 0) for m in manifests),
        "verification_rejected_count": sum(int(m.get("verification_rejected_count") or 0) for m in manifests),
        "verification_duplicate_count": sum(int(m.get("verification_duplicate_count") or 0) for m in manifests),
        "duration_seconds": duration,
    }
    totals["included_per_hour"] = round(totals["included_count"] / duration * 3600, 2) if duration else 0
    totals["verified_per_hour"] = round(totals["verified_count"] / duration * 3600, 2) if duration else 0
    run_manifest = {
        "record_type": "million_seed_bundle_compile_run_manifest",
        "created_at": _now(),
        "bundle_root": _rel(bundle_root),
        "out_root": _rel(out_root),
        "start_shard": start_shard,
        "shard_count": shard_count,
        "limit_per_shard": limit_per_shard,
        "verify": verify,
        "totals": totals,
        "shard_manifests": [_rel(Path(m["out_dir"]) / "manifest.json") for m in manifests],
        "candidate": True,
        "serves_truth": False,
    }
    (out_root / "manifest.json").write_text(json.dumps(run_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return run_manifest


def _self_test() -> int:
    sample = _read_jsonl(_resource("samples") / "sample_100.jsonl", limit=1)[0]
    candidate = candidate_from_seed(sample)
    ok = (
        candidate["candidate"] is True
        and candidate["serves_truth"] is False
        and candidate["kind"] in {"primitive", "primitive_group"}
        and bool(candidate["source_refs"])
        and isinstance(candidate["contract"], dict)
        and bool(candidate["proof_requirements"])
    )
    print("PASS - million seed compiler emits verifier-shaped primitive candidates." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", default=str(BUNDLE_ROOT))
    parser.add_argument("--out-root", default="")
    parser.add_argument("--start-shard", type=int, default=0)
    parser.add_argument("--shard-count", type=int, default=1)
    parser.add_argument("--limit-per-shard", type=int, default=0)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    out_root = Path(args.out_root) if args.out_root else _resource(f"million_seed_compile_{_now_slug()}")
    if not out_root.is_absolute():
        out_root = _resource(out_root)
    manifest = run(
        bundle_root=Path(args.bundle_root),
        out_root=out_root,
        start_shard=args.start_shard,
        shard_count=args.shard_count,
        limit_per_shard=args.limit_per_shard,
        verify=args.verify,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
