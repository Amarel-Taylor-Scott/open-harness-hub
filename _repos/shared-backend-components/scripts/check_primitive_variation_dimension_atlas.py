#!/usr/bin/env python3
"""Validate the primitive variation dimension atlas seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-variation-dimension-atlas")
MANIFEST_PATH = PACK_DIR / "manifest.json"

FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)
ID_FIELDS = {
    "dimension_id",
    "family_id",
    "example_id",
    "role_id",
    "role_dimension_ref",
    "rule_id",
}
ID_LIST_FIELDS = {"dimension_refs", "preferred_dimension_refs"}


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


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AssertionError("manifest must declare files")

    dimensions = _read_jsonl(PACK_DIR / str(files.get("variation_dimensions")))
    examples = _read_jsonl(PACK_DIR / str(files.get("specialization_examples")))
    role_matrix = _read_jsonl(PACK_DIR / str(files.get("role_algorithm_matrix")))
    resolver_rules = _read_jsonl(PACK_DIR / str(files.get("resolver_rules")))
    grouped_yaml = (PACK_DIR / str(files.get("grouped_yaml"))).read_text(encoding="utf-8")
    schema_sql = (PACK_DIR / str(files.get("schema_additions_sql"))).read_text(encoding="utf-8")

    if len(dimensions) != 250:
        raise AssertionError(f"expected 250 dimensions; got {len(dimensions)}")
    if manifest.get("dimension_count") != len(dimensions):
        raise AssertionError("manifest dimension_count must match rows")
    if manifest.get("family_count") != 25:
        raise AssertionError("manifest family_count must be 25")
    if manifest.get("dimensions_per_family") != 10:
        raise AssertionError("manifest dimensions_per_family must be 10")

    dimension_ids = {str(row.get("dimension_id") or "") for row in dimensions}
    if "" in dimension_ids or len(dimension_ids) != len(dimensions):
        raise AssertionError("dimension_id values must be non-empty and unique")

    family_counts: dict[str, int] = {}
    required_dimensions = {
        "dim:core_computer_logic.predicate",
        "dim:core_computer_logic.filter",
        "dim:core_computer_logic.dedupe",
        "dim:algorithms_data_structures.two_pointers",
        "dim:algorithms_data_structures.sliding_window",
        "dim:algorithms_data_structures.prefix_sum",
        "dim:algorithms_data_structures.hash_lookup",
        "dim:algorithms_data_structures.binary_search",
        "dim:algorithms_data_structures.heap_priority_queue",
        "dim:algorithms_data_structures.tree_graph_traversal",
        "dim:algorithms_data_structures.dynamic_programming",
        "dim:algorithms_data_structures.cache_hashing",
        "dim:common_schema_interchange.json_schema",
        "dim:common_schema_interchange.openapi_schema",
        "dim:common_schema_interchange.fhir_resource",
        "dim:data_layout_storage_modeling.long_tidy_table",
        "dim:data_layout_storage_modeling.wide_feature_table",
        "dim:region_geography_localization_jurisdiction.country",
        "dim:legal_compliance_security_governance.owasp_web_risk",
        "dim:embedding_affinity_search_materialization.edge_io_embedding",
        "dim:variation_control_lattice.proof_backed_materialization",
    }
    missing_required = sorted(required_dimensions - dimension_ids)
    if missing_required:
        raise AssertionError(f"missing required variation dimensions: {missing_required}")

    for row in dimensions:
        row_id = str(row["dimension_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        family_id = str(row.get("family_id") or "")
        family_counts[family_id] = family_counts.get(family_id, 0) + 1
        for field in ("title", "dimension_kind", "variation_axis", "resolver_use", "materialization_policy"):
            if not str(row.get(field) or ""):
                raise AssertionError(f"{row_id} must declare {field}")
        _require_list(row, "values_seed", row_id, min_len=3)
        _require_list(row, "applies_to", row_id, min_len=4)
        _require_list(row, "proof_implications", row_id, min_len=3)
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} source_refs should stay empty until verified")
        if row.get("source_evidence_status") != "curated_dimension_seed_needs_source_ref_resolution":
            raise AssertionError(f"{row_id} has wrong source_evidence_status")

    if len(family_counts) != 25:
        raise AssertionError(f"expected 25 families; got {len(family_counts)}")
    bad_family_counts = {family: count for family, count in family_counts.items() if count != 10}
    if bad_family_counts:
        raise AssertionError(f"each family must have 10 dimensions: {bad_family_counts}")
    for family_id in family_counts:
        if family_id not in grouped_yaml:
            raise AssertionError(f"grouped YAML missing {family_id}")

    for row in examples:
        row_id = str(row.get("example_id") or "")
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if "->" not in str(row.get("base_edge") or ""):
            raise AssertionError(f"{row_id} must declare base_edge with ->")
        if "->" not in str(row.get("resolved_edge") or ""):
            raise AssertionError(f"{row_id} must declare resolved_edge with ->")
        for dimension_id in _require_list(row, "dimension_refs", row_id, min_len=4):
            if dimension_id not in dimension_ids:
                raise AssertionError(f"{row_id} references unknown dimension {dimension_id!r}")

    for row in role_matrix:
        row_id = str(row.get("role_id") or "")
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if row.get("role_dimension_ref") not in dimension_ids:
            raise AssertionError(f"{row_id} references unknown role dimension {row.get('role_dimension_ref')!r}")
        for dimension_id in _require_list(row, "preferred_dimension_refs", row_id, min_len=4):
            if dimension_id not in dimension_ids:
                raise AssertionError(f"{row_id} references unknown preferred dimension {dimension_id!r}")
        _require_list(row, "proof_style", row_id, min_len=3)

    for row in resolver_rules:
        row_id = str(row.get("rule_id") or "")
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if not str(row.get("input_edge") or "") or not str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must declare input_edge and output_edge")
        if not str(row.get("decision_policy") or ""):
            raise AssertionError(f"{row_id} must declare decision_policy")

    for required_table in ("variation_dimension", "primitive_overlay_binding", "resolved_specialized_primitive"):
        if required_table not in schema_sql:
            raise AssertionError(f"schema SQL missing {required_table}")

    return {
        "families": len(family_counts),
        "dimensions": len(dimensions),
        "specialization_examples": len(examples),
        "role_matrix_rows": len(role_matrix),
        "resolver_rules": len(resolver_rules),
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
