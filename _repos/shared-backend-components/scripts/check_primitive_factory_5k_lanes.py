#!/usr/bin/env python3
"""Validate the 5k/day primitive factory lane plan.

The lane file targets useful candidate throughput, not trusted truth. A row
only counts toward daily capacity if it can pass source, contract, proof-plan,
dedupe, and candidate-boundary gates.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import math
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (
    OPPORTUNITY_INTELLIGENCE_GROUP_CANDIDATES_PATH,
    OPPORTUNITY_INTELLIGENCE_SOURCE_MAP_PATH,
    PRIMITIVE_FACTORY_5K_LANES_PATH,
    PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
    PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
    PRIMITIVE_FACTORY_REQUIRED_MODEL_ROLES,
    PRIMITIVE_FACTORY_REQUIRED_USEFULNESS_GATES,
    PRIMITIVE_FACTORY_TARGET_DAILY_RAW,
    PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL,
    PRIMITIVE_THROUGHPUT_REQUIRED_PROOF_GATES,
    REPO_ROOT,
)

LANES_PATH = _resource(PRIMITIVE_FACTORY_5K_LANES_PATH)
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


def _text(row: dict[str, Any], field: str, row_id: str) -> str:
    value = row.get(field)
    if not isinstance(value, str) or not value.strip():
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _list(row: dict[str, Any], field: str, row_id: str) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or not value:
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _source_ids() -> set[str]:
    return {str(row.get("id")) for row in _read_jsonl(SOURCE_MAP_PATH)}


def _group_ids() -> set[str]:
    return {str(row.get("primitive_id")) for row in _read_jsonl(GROUP_CANDIDATES_PATH)}


def self_test() -> dict[str, Any]:
    rows = _read_jsonl(LANES_PATH)
    if not rows:
        raise AssertionError("5k primitive factory lanes must not be empty")

    known_source_ids = _source_ids()
    known_group_ids = _group_ids()
    required_roles = set(PRIMITIVE_FACTORY_REQUIRED_MODEL_ROLES)
    required_usefulness = set(PRIMITIVE_FACTORY_REQUIRED_USEFULNESS_GATES)
    required_proofs = set(PRIMITIVE_THROUGHPUT_REQUIRED_PROOF_GATES)

    lane_ids: list[str] = []
    raw_total = 0
    useful_total = 0
    weighted_group_outputs = 0.0
    weighted_outputs = 0.0
    source_ids_used: set[str] = set()
    group_ids_used: set[str] = set()

    for row in rows:
        lane_id = _text(row, "id", "lane row")
        lane_ids.append(lane_id)
        _text(row, "title", lane_id)
        _text(row, "target_candidate_level", lane_id)
        _text(row, "generator", lane_id)
        _text(row, "source_evidence", lane_id)
        _text(row, "rejection_policy", lane_id)

        raw_target = int(row.get("daily_raw_candidate_target") or 0)
        useful_target = int(row.get("daily_useful_candidate_target") or 0)
        if raw_target <= 0 or useful_target <= 0:
            raise AssertionError(f"{lane_id} must declare positive raw/useful targets")
        if raw_target < useful_target:
            raise AssertionError(f"{lane_id} raw target must be at least useful target")
        raw_total += raw_target
        useful_total += useful_target

        source_ref_ids = {str(source_id) for source_id in _list(row, "source_ref_ids", lane_id)}
        unknown_sources = source_ref_ids - known_source_ids
        if unknown_sources:
            raise AssertionError(f"{lane_id} references unknown source ids: {sorted(unknown_sources)}")
        source_ids_used.update(source_ref_ids)

        base_group_ids = {str(group_id) for group_id in _list(row, "base_group_ids", lane_id)}
        unknown_groups = base_group_ids - known_group_ids
        if unknown_groups:
            raise AssertionError(f"{lane_id} references unknown group ids: {sorted(unknown_groups)}")
        group_ids_used.update(base_group_ids)

        output_mix = row.get("output_mix")
        if not isinstance(output_mix, dict) or not output_mix:
            raise AssertionError(f"{lane_id} must declare output_mix")
        mix_sum = sum(float(value) for value in output_mix.values())
        if not math.isclose(mix_sum, 1.0, abs_tol=0.001):
            raise AssertionError(f"{lane_id} output_mix must sum to 1.0, got {mix_sum}")
        group_mix = float(output_mix.get("primitive_group_candidate") or 0.0)
        minimum_group_ratio = float(row.get("minimum_group_ratio") or 0.0)
        if group_mix < minimum_group_ratio:
            raise AssertionError(f"{lane_id} group output mix is below minimum_group_ratio")
        weighted_group_outputs += useful_target * group_mix
        weighted_outputs += useful_target

        roles = row.get("model_roles")
        if not isinstance(roles, dict):
            raise AssertionError(f"{lane_id} must declare model_roles object")
        missing_roles = required_roles - set(roles)
        if missing_roles:
            raise AssertionError(f"{lane_id} missing model roles: {sorted(missing_roles)}")
        if roles.get("kimi_candidate_writer") != PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER:
            raise AssertionError(f"{lane_id} must route candidate writing to Kimi")
        if roles.get("glm_contract_reviewer") != PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER:
            raise AssertionError(f"{lane_id} must route contract review to GLM")

        deterministic_validators = _list(row, "deterministic_validators", lane_id)
        if "candidate_boundary_gate" not in deterministic_validators:
            raise AssertionError(f"{lane_id} deterministic validators must include candidate_boundary_gate")

        usefulness_gates = set(_list(row, "usefulness_gates", lane_id))
        missing_usefulness = required_usefulness - usefulness_gates
        if missing_usefulness:
            raise AssertionError(f"{lane_id} missing usefulness gates: {sorted(missing_usefulness)}")

        proof_gates = set(_list(row, "proof_gates", lane_id))
        missing_proofs = required_proofs - proof_gates
        if missing_proofs:
            raise AssertionError(f"{lane_id} missing proof gates: {sorted(missing_proofs)}")

        _list(row, "example_visible_edges", lane_id)
        boundary = _text(row, "candidate_boundary", lane_id).lower()
        if "candidate=true" not in boundary or "serves_truth=false" not in boundary:
            raise AssertionError(f"{lane_id} must preserve candidate=true and serves_truth=false boundary")

    if len(lane_ids) != len(set(lane_ids)):
        raise AssertionError("5k primitive factory lane ids must be unique")
    if raw_total < PRIMITIVE_FACTORY_TARGET_DAILY_RAW:
        raise AssertionError(
            f"raw daily target {raw_total} is below configured target "
            f"{PRIMITIVE_FACTORY_TARGET_DAILY_RAW}"
        )
    if useful_total < PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL:
        raise AssertionError(
            f"useful daily target {useful_total} is below configured target "
            f"{PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL}"
        )

    weighted_group_ratio = weighted_group_outputs / weighted_outputs if weighted_outputs else 0.0
    if weighted_group_ratio < 0.7:
        raise AssertionError(f"weighted group ratio {weighted_group_ratio:.3f} is too low")

    return {
        "lanes": len(rows),
        "daily_raw_candidate_target": raw_total,
        "daily_useful_candidate_target": useful_total,
        "configured_daily_raw_target": PRIMITIVE_FACTORY_TARGET_DAILY_RAW,
        "configured_daily_useful_target": PRIMITIVE_FACTORY_TARGET_DAILY_USEFUL,
        "weighted_group_candidate_ratio": round(weighted_group_ratio, 3),
        "source_ids_used": len(source_ids_used),
        "base_group_ids_used": len(group_ids_used),
        "candidate_boundary": "candidate=true; serves_truth=false",
        "kimi_candidate_writer": PRIMITIVE_FACTORY_MODEL_KIMI_CANDIDATE_WRITER,
        "glm_contract_reviewer": PRIMITIVE_FACTORY_MODEL_GLM_CONTRACT_REVIEWER,
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
