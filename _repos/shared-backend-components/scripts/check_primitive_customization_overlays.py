#!/usr/bin/env python3
"""Validate the primitive customization overlay seed pack."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-customization-overlays")
MANIFEST_PATH = PACK_DIR / "manifest.json"

ID_FIELDS = {
    "object_id",
    "overlay_id",
    "primitive_id",
    "mutator_id",
    "negative_memory_id",
    "base_primitive_ref",
    "maps_to",
    "applies_to",
}
FORBIDDEN_ID_PATTERN = re.compile(
    r"(@|(?:^|[:._-])v\d+(?:$|[:._-])|(?:^|[:._-])latest(?:$|[:._-])|20\d{2}[-_]\d{2})",
    re.IGNORECASE,
)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise AssertionError(f"missing JSON file: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path}: invalid JSON: {exc}") from exc
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


def _require_list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def _require_dict(row: dict[str, Any], field: str, row_id: str) -> dict[str, Any]:
    value = row.get(field)
    if not isinstance(value, dict) or not value:
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _require_candidate_boundary(row: dict[str, Any], row_id: str) -> None:
    if row.get("candidate") is not True:
        raise AssertionError(f"{row_id} must keep candidate=true")
    if row.get("serves_truth") is not False:
        raise AssertionError(f"{row_id} must keep serves_truth=false")


def _assert_version_free_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be stable and version-free: {value!r}")


def _check_id_fields(row: dict[str, Any], row_id: str) -> None:
    for field in ID_FIELDS:
        value = row.get(field)
        if isinstance(value, str):
            _assert_version_free_id(value, row_id, field)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    _assert_version_free_id(item, row_id, field)


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict) or not files:
        raise AssertionError("manifest must declare files")

    canonical = _read_jsonl(PACK_DIR / str(files.get("canonical_objects")))
    overlays = _read_jsonl(PACK_DIR / str(files.get("platform_overlays")))
    primitives = _read_jsonl(PACK_DIR / str(files.get("specialized_primitives")))
    mutators = _read_jsonl(PACK_DIR / str(files.get("specialization_mutators")))
    negative_memory = _read_jsonl(PACK_DIR / str(files.get("negative_memory")))

    object_ids = {str(row.get("object_id") or "") for row in canonical}
    overlay_ids = {str(row.get("overlay_id") or "") for row in overlays}
    primitive_ids = {str(row.get("primitive_id") or "") for row in primitives}
    mutator_ids = {str(row.get("mutator_id") or "") for row in mutators}
    negative_memory_ids = {str(row.get("negative_memory_id") or "") for row in negative_memory}

    all_ids = object_ids | overlay_ids | primitive_ids | mutator_ids | negative_memory_ids
    if "" in all_ids:
        raise AssertionError("every customization row must declare its primary id")
    if len(all_ids) != sum(len(ids) for ids in (object_ids, overlay_ids, primitive_ids, mutator_ids, negative_memory_ids)):
        raise AssertionError("customization overlay ids must be unique across row families")

    for row in canonical:
        row_id = str(row["object_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        _require_list(row, "identity_fields", row_id)
        _require_list(row, "required_fields", row_id)
        _require_list(row, "quality_rules", row_id)
        _require_list(row, "common_source_schemas", row_id)
        if not str(row.get("object_family") or ""):
            raise AssertionError(f"{row_id} must declare object_family")

    for row in overlays:
        row_id = str(row["overlay_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        maps_to = str(row.get("maps_to") or "")
        if maps_to not in object_ids:
            raise AssertionError(f"{row_id} maps_to unknown canonical object {maps_to!r}")
        _require_dict(row, "field_map", row_id)
        _require_list(row, "proof_fixtures", row_id)
        _require_list(row, "known_pitfalls", row_id)
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} should keep source_refs empty until verified")
        if row.get("source_evidence_status") != "unverified_intake_requires_source_ref_resolution":
            raise AssertionError(f"{row_id} must keep unverified intake source status")

    for row in mutators:
        row_id = str(row["mutator_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if row.get("deterministic") is not True:
            raise AssertionError(f"{row_id} must be deterministic glue")
        if "->" not in str(row.get("input_edge") or "") + "->" + str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must declare input and output edges")
        _require_list(row, "applies_to_layers", row_id)
        _require_list(row, "proof_requirements", row_id)

    for row in primitives:
        row_id = str(row["primitive_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        if not str(row.get("base_primitive_ref") or ""):
            raise AssertionError(f"{row_id} must declare base_primitive_ref")
        if not str(row.get("input_edge") or "") or not str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} must declare visible input_edge and output_edge")
        if "->" in str(row.get("input_edge") or "") or "->" in str(row.get("output_edge") or ""):
            raise AssertionError(f"{row_id} should keep input_edge and output_edge separate")
        for object_id in _require_list(row, "canonical_objects", row_id):
            if object_id not in object_ids:
                raise AssertionError(f"{row_id} references unknown canonical object {object_id!r}")
        for overlay_id in _require_list(row, "platform_overlays", row_id):
            if overlay_id not in overlay_ids:
                raise AssertionError(f"{row_id} references unknown overlay {overlay_id!r}")
        for mutator_id in _require_list(row, "mutators", row_id):
            if mutator_id not in mutator_ids:
                raise AssertionError(f"{row_id} references unknown mutator {mutator_id!r}")
        for memory_id in _require_list(row, "negative_memory_refs", row_id):
            if memory_id not in negative_memory_ids:
                raise AssertionError(f"{row_id} references unknown negative memory {memory_id!r}")
        specialization = _require_dict(row, "specialization", row_id)
        for field in ("platform", "industry", "business_object", "workflow", "runtime_shape"):
            if not str(specialization.get(field) or ""):
                raise AssertionError(f"{row_id} specialization must declare {field}")
        blackbox = _require_dict(row, "blackbox", row_id)
        if not str(blackbox.get("does") or ""):
            raise AssertionError(f"{row_id} blackbox must explain behavior")
        _require_list(row, "hidden_member_edges", row_id, min_len=3)
        _require_list(row, "effects", row_id)
        _require_list(row, "runtime_targets", row_id)
        _require_list(row, "proof_requirements", row_id, min_len=4)
        _require_list(row, "benchmark_hooks", row_id)
        if specialization["runtime_shape"] not in row["runtime_targets"]:
            raise AssertionError(f"{row_id} runtime_shape must be one of runtime_targets")
        if row.get("source_evidence_status") != "unverified_intake_requires_source_ref_resolution":
            raise AssertionError(f"{row_id} must keep unverified intake source status")

    for row in negative_memory:
        row_id = str(row["negative_memory_id"])
        _require_candidate_boundary(row, row_id)
        _check_id_fields(row, row_id)
        applies_to = str(row.get("applies_to") or "")
        if applies_to not in primitive_ids and applies_to not in overlay_ids:
            raise AssertionError(f"{row_id} applies_to unknown primitive or overlay {applies_to!r}")
        if not str(row.get("failure_pattern") or ""):
            raise AssertionError(f"{row_id} must declare failure_pattern")
        if not str(row.get("recommended_fix") or ""):
            raise AssertionError(f"{row_id} must declare recommended_fix")

    return {
        "canonical_objects": len(canonical),
        "platform_overlays": len(overlays),
        "specialized_primitives": len(primitives),
        "specialization_mutators": len(mutators),
        "negative_memory": len(negative_memory),
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
