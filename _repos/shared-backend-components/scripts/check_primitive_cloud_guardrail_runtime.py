#!/usr/bin/env python3
"""Validate the cloud-agnostic guardrail primitive runtime seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-cloud-guardrail-runtime")
MANIFEST_PATH = PACK_DIR / "manifest.json"

FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)
ID_FIELDS = {
    "primitive_id",
    "adapter_id",
    "wrapper_id",
    "pack_id",
    "fixture_id",
}
ID_LIST_FIELDS = {
    "member_primitives",
    "required_primitives",
    "recommended_groups",
    "target_primitives",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"missing JSON file: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(value, dict):
            raise AssertionError(f"{path}:{line_number}: expected JSON object")
        rows.append(value)
    if not rows:
        raise AssertionError(f"{path}: expected at least one row")
    return rows


def _require_candidate_boundary(row: dict[str, Any], row_id: str) -> None:
    if row.get("candidate") is not True:
        raise AssertionError(f"{row_id} must keep candidate=true")
    if row.get("serves_truth") is not False:
        raise AssertionError(f"{row_id} must keep serves_truth=false")


def _require_list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def _require_edge_pair(row: dict[str, Any], row_id: str) -> None:
    if not str(row.get("input_edge") or ""):
        raise AssertionError(f"{row_id} must declare input_edge")
    if not str(row.get("output_edge") or ""):
        raise AssertionError(f"{row_id} must declare output_edge")
    if "->" in str(row.get("input_edge")) or "->" in str(row.get("output_edge")):
        raise AssertionError(f"{row_id} must keep input_edge and output_edge separate")


def _assert_version_free_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be stable and version-free: {value!r}")


def _check_id_fields(row: dict[str, Any], row_id: str) -> None:
    for field in ID_FIELDS:
        value = row.get(field)
        if isinstance(value, str):
            _assert_version_free_id(value, row_id, field)
    for field in ID_LIST_FIELDS:
        value = row.get(field)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _assert_version_free_id(item, row_id, field)


def _primary_ids(rows: list[dict[str, Any]], field: str) -> set[str]:
    ids = {str(row.get(field) or "") for row in rows}
    if "" in ids or len(ids) != len(rows):
        raise AssertionError(f"{field} values must be non-empty and unique")
    return ids


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AssertionError("manifest must declare files")

    primitives = _read_jsonl(PACK_DIR / str(files.get("guardrail_primitives")))
    groups = _read_jsonl(PACK_DIR / str(files.get("guardrail_groups")))
    adapters = _read_jsonl(PACK_DIR / str(files.get("provider_adapters")))
    wrappers = _read_jsonl(PACK_DIR / str(files.get("deployment_wrappers")))
    industry_packs = _read_jsonl(PACK_DIR / str(files.get("industry_guardrail_packs")))
    fixtures = _read_jsonl(PACK_DIR / str(files.get("benchmark_fixtures")))

    primitive_ids = _primary_ids(primitives, "primitive_id")
    group_ids = _primary_ids(groups, "primitive_id")
    adapter_ids = _primary_ids(adapters, "adapter_id")
    wrapper_ids = _primary_ids(wrappers, "wrapper_id")
    pack_ids = _primary_ids(industry_packs, "pack_id")
    fixture_ids = _primary_ids(fixtures, "fixture_id")
    all_ids = primitive_ids | group_ids | adapter_ids | wrapper_ids | pack_ids | fixture_ids
    if len(all_ids) != sum(len(ids) for ids in (primitive_ids, group_ids, adapter_ids, wrapper_ids, pack_ids, fixture_ids)):
        raise AssertionError("guardrail pack ids must be unique across row families")

    family_counts: dict[str, int] = {}
    required_families = {
        "prompt_input",
        "data_leak",
        "rag_source",
        "tool_call",
        "output",
        "policy_as_code",
        "audit_receipt",
    }
    required_primitives = {
        "guard:prompt.injection_detect",
        "guard:data.pii_redact",
        "guard:rag.source_allowlist",
        "guard:tool.external_side_effect_gate",
        "guard:output.schema_validate",
        "guard:policy.opa_eval",
        "guard:audit.decision_receipt_emit",
    }
    missing_required = sorted(required_primitives - primitive_ids)
    if missing_required:
        raise AssertionError(f"missing required guardrail primitives: {missing_required}")

    for row in primitives:
        row_id = str(row["primitive_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_edge_pair(row, row_id)
        family = str(row.get("family") or "")
        family_counts[family] = family_counts.get(family, 0) + 1
        if family not in required_families:
            raise AssertionError(f"{row_id} has unknown family {family!r}")
        if not isinstance(row.get("blackbox"), dict) or not str(row["blackbox"].get("does") or ""):
            raise AssertionError(f"{row_id} must declare blackbox.does")
        _require_list(row, "effects", row_id)
        _require_list(row, "runtime_targets", row_id, min_len=3)
        _require_list(row, "proof_requirements", row_id, min_len=4)

    missing_families = sorted(required_families - set(family_counts))
    if missing_families:
        raise AssertionError(f"missing guardrail families: {missing_families}")
    if family_counts["tool_call"] < 6:
        raise AssertionError("tool_call family should be the sharp wedge and have at least 6 primitives")

    for row in groups:
        row_id = str(row["primitive_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_edge_pair(row, row_id)
        for primitive_id in _require_list(row, "member_primitives", row_id, min_len=5):
            if primitive_id not in primitive_ids:
                raise AssertionError(f"{row_id} references unknown primitive {primitive_id!r}")
        _require_list(row, "runtime_targets", row_id, min_len=4)
        _require_list(row, "proof_requirements", row_id, min_len=5)

    required_adapters = {
        "adapter:aws.bedrock_apply_guardrail",
        "adapter:gcp.model_armor",
        "adapter:azure.ai_content_safety",
        "adapter:policy.opa",
        "adapter:policy.cedar",
        "adapter:local.deterministic_policy_engine",
    }
    if required_adapters - adapter_ids:
        raise AssertionError(f"missing provider adapters: {sorted(required_adapters - adapter_ids)}")
    for row in adapters:
        row_id = str(row["adapter_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_edge_pair(row, row_id)
        _require_list(row, "supported_families", row_id)
        _require_list(row, "effects", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=3)
        if row_id != "adapter:local.deterministic_policy_engine":
            if row.get("source_refs") != []:
                raise AssertionError(f"{row_id} source_refs should stay empty until verified")
            if row.get("source_evidence_status") != "unverified_intake_requires_source_ref_resolution":
                raise AssertionError(f"{row_id} must keep unverified source status")

    required_wrappers = {
        "deploy:guardrail.lambda_handler",
        "deploy:guardrail.cloud_run_container",
        "deploy:guardrail.azure_function",
        "deploy:guardrail.kubernetes_sidecar",
        "deploy:guardrail.knative_service",
        "deploy:guardrail.envoy_ext_authz_service",
        "deploy:guardrail.mcp_prehook",
        "deploy:guardrail.receipt_collector",
    }
    if required_wrappers - wrapper_ids:
        raise AssertionError(f"missing deployment wrappers: {sorted(required_wrappers - wrapper_ids)}")
    for row in wrappers:
        row_id = str(row["wrapper_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_edge_pair(row, row_id)
        _require_list(row, "runtime_targets", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=3)

    for row in industry_packs:
        row_id = str(row["pack_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        for group_id in _require_list(row, "recommended_groups", row_id):
            if group_id not in group_ids:
                raise AssertionError(f"{row_id} references unknown group {group_id!r}")
        for primitive_id in _require_list(row, "required_primitives", row_id, min_len=4):
            if primitive_id not in primitive_ids:
                raise AssertionError(f"{row_id} references unknown primitive {primitive_id!r}")
        _require_list(row, "human_review_triggers", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=3)

    for row in fixtures:
        row_id = str(row["fixture_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_edge_pair(row, row_id)
        for primitive_id in _require_list(row, "target_primitives", row_id):
            if primitive_id not in primitive_ids:
                raise AssertionError(f"{row_id} references unknown target primitive {primitive_id!r}")
        _require_list(row, "success_criteria", row_id, min_len=3)

    positioning = str(manifest.get("product_positioning") or "")
    if "cloud-agnostic" not in positioning or "agentic workflows" not in positioning:
        raise AssertionError("manifest must position the product as cloud-agnostic agentic workflow guardrails")

    return {
        "guardrail_primitives": len(primitives),
        "guardrail_groups": len(groups),
        "provider_adapters": len(adapters),
        "deployment_wrappers": len(wrappers),
        "industry_guardrail_packs": len(industry_packs),
        "benchmark_fixtures": len(fixtures),
        "candidate": True,
        "serves_truth": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run validation checks")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("expected --self-test")
    print(json.dumps(self_test(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
