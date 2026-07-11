#!/usr/bin/env python3
"""Validate the opportunity-intelligence primitive guidance pack.

The pack is intentionally candidate-only. This checker proves the local source
map and primitive-group candidates are structured enough to feed the primitive
factory without pretending any row is promoted truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (
    OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH,
    OPPORTUNITY_INTELLIGENCE_GUIDANCE_PATH,
    OPPORTUNITY_INTELLIGENCE_MIN_GROUP_CANDIDATE_ROWS,
    OPPORTUNITY_INTELLIGENCE_MIN_SOURCE_MAP_ROWS,
    OPPORTUNITY_INTELLIGENCE_REQUIRED_PROOF_REQUIREMENTS,
    OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH,
    REPO_ROOT,
)

GUIDANCE_PATH = _resource(OPPORTUNITY_INTELLIGENCE_GUIDANCE_PATH)
SOURCE_MAP_PATH = _resource(OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH)
GROUP_CANDIDATES_PATH = _resource(OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
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
    return rows


def _require_text(row: dict[str, Any], field: str, row_id: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _require_list(row: dict[str, Any], field: str, row_id: str) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or not value:
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _validate_source_map(rows: list[dict[str, Any]]) -> set[str]:
    if len(rows) < OPPORTUNITY_INTELLIGENCE_MIN_SOURCE_MAP_ROWS:
        raise AssertionError(
            f"source map has {len(rows)} rows; expected at least "
            f"{OPPORTUNITY_INTELLIGENCE_MIN_SOURCE_MAP_ROWS}"
        )

    ids: list[str] = []
    for row in rows:
        source_id = _require_text(row, "id", "source map row")
        ids.append(source_id)
        url = _require_text(row, "url", source_id)
        if not url.startswith(("https://", "http://")):
            raise AssertionError(f"{source_id} url must be absolute HTTP(S)")
        _require_text(row, "title", source_id)
        _require_text(row, "source_type", source_id)
        _require_text(row, "authority", source_id)
        _require_text(row, "adapter_hint", source_id)
        _require_text(row, "scan_cadence", source_id)
        _require_list(row, "primitive_opportunities", source_id)
        _require_text(row, "proof_notes", source_id)
        _require_text(row, "license_policy_notes", source_id)
        _require_text(row, "as_of", source_id)

    if len(ids) != len(set(ids)):
        raise AssertionError("source map ids must be unique")
    return set(ids)


def _validate_group_candidates(rows: list[dict[str, Any]], source_ids: set[str]) -> set[str]:
    if len(rows) < OPPORTUNITY_INTELLIGENCE_MIN_GROUP_CANDIDATE_ROWS:
        raise AssertionError(
            f"group candidates have {len(rows)} rows; expected at least "
            f"{OPPORTUNITY_INTELLIGENCE_MIN_GROUP_CANDIDATE_ROWS}"
        )

    ids: list[str] = []
    referenced_sources: set[str] = set()
    required_proofs = set(OPPORTUNITY_INTELLIGENCE_REQUIRED_PROOF_REQUIREMENTS)

    for row in rows:
        primitive_id = _require_text(row, "primitive_id", "group candidate row")
        ids.append(primitive_id)
        if not primitive_id.startswith("grp:opportunity.") or not primitive_id.endswith("@candidate"):
            raise AssertionError(f"{primitive_id} must use grp:opportunity.*@candidate id pattern")
        if row.get("kind") != "artifact.primitive_group":
            raise AssertionError(f"{primitive_id} must use kind artifact.primitive_group")
        if row.get("candidate") is not True:
            raise AssertionError(f"{primitive_id} must keep candidate=true")
        if row.get("serves_truth") is not False:
            raise AssertionError(f"{primitive_id} must keep serves_truth=false")
        if not str(row.get("readiness") or "").startswith("R2"):
            raise AssertionError(f"{primitive_id} must remain an R2 source-backed candidate")

        input_edge = _require_text(row, "input_edge", primitive_id)
        output_edge = _require_text(row, "output_edge", primitive_id)
        contract = row.get("contract")
        if not isinstance(contract, dict):
            raise AssertionError(f"{primitive_id} must declare contract object")
        if contract.get("input") != input_edge or contract.get("output") != output_edge:
            raise AssertionError(f"{primitive_id} contract must mirror visible input/output edges")

        group_contract = row.get("group_contract")
        if not isinstance(group_contract, dict):
            raise AssertionError(f"{primitive_id} must declare group_contract object")
        if group_contract.get("visible_input_edge") != input_edge:
            raise AssertionError(f"{primitive_id} group visible_input_edge must match input_edge")
        if group_contract.get("visible_output_edge") != output_edge:
            raise AssertionError(f"{primitive_id} group visible_output_edge must match output_edge")
        hidden_edges = group_contract.get("hidden_member_edges")
        if not isinstance(hidden_edges, list) or len(hidden_edges) < 3:
            raise AssertionError(f"{primitive_id} must hide at least three member edges")

        blackbox = row.get("blackbox")
        if not isinstance(blackbox, dict) or not blackbox.get("does"):
            raise AssertionError(f"{primitive_id} must declare blackbox.does")
        _require_list(row, "effects", primitive_id)
        _require_list(row, "runtime_targets", primitive_id)
        _require_list(row, "edge_mutation_options", primitive_id)
        proof_requirements = set(_require_list(row, "proof_requirements", primitive_id))
        missing_proofs = required_proofs - proof_requirements
        if missing_proofs:
            raise AssertionError(f"{primitive_id} missing proof requirements: {sorted(missing_proofs)}")
        _require_list(row, "promotion_blockers", primitive_id)

        source_ref_ids = set(_require_list(row, "source_ref_ids", primitive_id))
        unknown_sources = source_ref_ids - source_ids
        if unknown_sources:
            raise AssertionError(f"{primitive_id} references unknown source ids: {sorted(unknown_sources)}")
        referenced_sources.update(str(source_id) for source_id in source_ref_ids)
        source_refs = _require_list(row, "source_refs", primitive_id)
        if len(source_refs) < len(source_ref_ids):
            raise AssertionError(f"{primitive_id} must include URL refs for source ids")

    if len(ids) != len(set(ids)):
        raise AssertionError("group candidate primitive_ids must be unique")
    return referenced_sources


def _validate_guidance_doc(source_rows: list[dict[str, Any]], group_rows: list[dict[str, Any]]) -> None:
    if not GUIDANCE_PATH.exists():
        raise AssertionError(f"missing guidance doc: {GUIDANCE_PATH}")
    text = GUIDANCE_PATH.read_text(encoding="utf-8")
    required_phrases = (
        "candidate=true",
        "serves_truth=false",
        "visible input edge",
        "hidden member edges",
        "opportunity-intelligence graph",
    )
    for phrase in required_phrases:
        if phrase not in text:
            raise AssertionError(f"guidance doc must mention {phrase!r}")

    source_url_count = sum(1 for row in source_rows if str(row.get("url") or "") in text)
    if source_url_count < OPPORTUNITY_INTELLIGENCE_MIN_SOURCE_MAP_ROWS // 2:
        raise AssertionError("guidance doc should cite a representative set of source-map URLs")

    candidate_id_count = sum(1 for row in group_rows if str(row.get("primitive_id") or "") in text)
    if candidate_id_count < 3:
        raise AssertionError("guidance doc should reference representative candidate group ids")


def self_test() -> dict[str, Any]:
    source_rows = _read_jsonl(SOURCE_MAP_PATH)
    group_rows = _read_jsonl(GROUP_CANDIDATES_PATH)
    source_ids = _validate_source_map(source_rows)
    referenced_sources = _validate_group_candidates(group_rows, source_ids)
    _validate_guidance_doc(source_rows, group_rows)
    return {
        "source_map_rows": len(source_rows),
        "group_candidate_rows": len(group_rows),
        "referenced_source_ids": len(referenced_sources),
        "candidate_boundary": "candidate=true; serves_truth=false",
        "guidance_path": OPPORTUNITY_INTELLIGENCE_GUIDANCE_PATH,
        "source_map_path": OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH,
        "group_candidates_path": OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH,
    }


def main() -> int:
    try:
        result = self_test()
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
