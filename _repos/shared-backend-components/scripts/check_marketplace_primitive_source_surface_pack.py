#!/usr/bin/env python3
"""Validate marketplace and registry primitive source-surface seeds."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/marketplace-primitive-source-surfaces")
MANIFEST_PATH = PACK_DIR / "manifest.json"
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
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
        raise AssertionError(f"{path}: expected rows")
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


def _check_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be version-free: {value!r}")


def _require_edges(row: dict[str, Any], row_id: str) -> None:
    if not str(row.get("input_edge") or ""):
        raise AssertionError(f"{row_id} must declare input_edge")
    if not str(row.get("output_edge") or ""):
        raise AssertionError(f"{row_id} must declare output_edge")
    if "->" in str(row.get("input_edge")) or "->" in str(row.get("output_edge")):
        raise AssertionError(f"{row_id} must keep input_edge and output_edge separate")


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AssertionError("manifest must declare files")

    surfaces = _read_jsonl(PACK_DIR / str(files["source_surfaces"]))
    patterns = _read_jsonl(PACK_DIR / str(files["factory_patterns"]))
    examples = _read_jsonl(PACK_DIR / str(files["example_primitive_cards"]))
    extraction_policy = _read_json(PACK_DIR / str(files["extraction_policy"]))
    _require_candidate_boundary(extraction_policy, "extraction_policy")
    if extraction_policy.get("copy_code") is not False:
        raise AssertionError("extraction policy must forbid source-code copying")

    if len(surfaces) != 20:
        raise AssertionError(f"expected 20 marketplace source surfaces; got {len(surfaces)}")
    if len(patterns) != 8:
        raise AssertionError(f"expected 8 factory patterns; got {len(patterns)}")
    if len(examples) != 6:
        raise AssertionError(f"expected 6 example primitive cards; got {len(examples)}")
    if manifest.get("source_surface_count") != len(surfaces):
        raise AssertionError("manifest source_surface_count must match")

    surface_ids = {str(row.get("source_surface_id") or "") for row in surfaces}
    if "" in surface_ids or len(surface_ids) != len(surfaces):
        raise AssertionError("source surface ids must be unique")
    required_surfaces = {
        "market:mcp_registry",
        "market:apis_guru_openapi",
        "market:terraform_registry",
        "market:github_actions",
        "market:n8n_zapier_make_pipedream",
        "market:aws_serverless_application_repository",
        "market:artifacthub_helm",
        "market:operatorhub",
        "market:huggingface_replicate_model_hubs",
        "market:pypi_npm_dbt_airflow",
    }
    if required_surfaces - surface_ids:
        raise AssertionError(f"missing required surfaces: {sorted(required_surfaces - surface_ids)}")

    ranks = [int(row.get("rank") or 0) for row in surfaces]
    if ranks != list(range(1, len(surfaces) + 1)):
        raise AssertionError("source surface ranks must be contiguous")
    if [row["source_surface_id"] for row in surfaces[:3]] != [
        "market:mcp_registry",
        "market:apis_guru_openapi",
        "market:postman_api_network",
    ]:
        raise AssertionError("top marketplace surfaces should prioritize MCP and API contracts")

    for row in surfaces:
        row_id = str(row["source_surface_id"])
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "source_surface_id")
        _require_edges(row, row_id)
        _require_list(row, "runtime_targets", row_id)
        _require_list(row, "effects", row_id)
        _require_list(row, "candidate_outputs", row_id, min_len=4)
        _require_list(row, "proof_requirements", row_id, min_len=4)
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} source_refs should stay empty until verified")

    pattern_ids = {str(row.get("pattern_id") or "") for row in patterns}
    if "" in pattern_ids or len(pattern_ids) != len(patterns):
        raise AssertionError("factory pattern ids must be unique")
    for row in patterns:
        row_id = str(row["pattern_id"])
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "pattern_id")
        _require_edges(row, row_id)

    for row in examples:
        row_id = str(row["primitive_id"])
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "primitive_id")
        source_surface_id = str(row.get("source_surface_id") or "")
        if source_surface_id not in surface_ids:
            raise AssertionError(f"{row_id} references unknown source surface {source_surface_id!r}")
        _require_edges(row, row_id)
        _require_list(row, "effects", row_id)
        _require_list(row, "runtime_targets", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=4)

    return {
        "source_surfaces": len(surfaces),
        "factory_patterns": len(patterns),
        "example_primitive_cards": len(examples),
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
