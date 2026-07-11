#!/usr/bin/env python3
"""Validate the primitive-throughput lane plan.

This is not a claim that the repo currently produces 20k verified primitives
per day. It proves that the lane plan is explicit enough to target that scale
with verified parameterized factories instead of one-off hand-written code.
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
    PRIMITIVE_THROUGHPUT_LANES_PATH,
    PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED,
    PRIMITIVE_THROUGHPUT_REQUIRED_PROOF_GATES,
    PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED,
    REPO_ROOT,
)

LANES_PATH = _resource(PRIMITIVE_THROUGHPUT_LANES_PATH)
CURATED_GROUPS_PATH = _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "curated_primitive_groups.jsonl"


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
    return rows


def _current_r4_group_count() -> int:
    if not CURATED_GROUPS_PATH.exists():
        return 0
    rows = _read_jsonl(CURATED_GROUPS_PATH)
    return sum(
        1
        for row in rows
        if row.get("kind") == "artifact.primitive_group"
        and str(row.get("readiness") or "").startswith("R4")
        and row.get("candidate") is True
        and row.get("serves_truth") is False
    )


def self_test() -> dict[str, Any]:
    rows = _read_jsonl(LANES_PATH)
    if not rows:
        raise AssertionError("primitive throughput lanes must not be empty")
    ids = [str(row.get("id") or "") for row in rows]
    if len(ids) != len(set(ids)):
        raise AssertionError("primitive throughput lane ids must be unique")

    required_gates = set(PRIMITIVE_THROUGHPUT_REQUIRED_PROOF_GATES)
    daily_total = 0
    for row in rows:
        lane_id = str(row.get("id") or "")
        target = int(row.get("daily_verified_target") or 0)
        daily_total += target
        if target <= 0:
            raise AssertionError(f"{lane_id} must declare positive daily_verified_target")
        if not row.get("verification_unit"):
            raise AssertionError(f"{lane_id} must declare verification_unit")
        if not row.get("deterministic_factory"):
            raise AssertionError(f"{lane_id} must declare deterministic_factory")
        if not row.get("source_evidence"):
            raise AssertionError(f"{lane_id} must declare source_evidence")
        if not row.get("example_group_edges"):
            raise AssertionError(f"{lane_id} must declare example_group_edges")
        if not row.get("surfaces"):
            raise AssertionError(f"{lane_id} must declare surfaces")
        gates = set(row.get("proof_gates") or [])
        missing = required_gates - gates
        if missing:
            raise AssertionError(f"{lane_id} missing proof gates: {sorted(missing)}")
        boundary = str(row.get("promotion_boundary") or "").lower()
        if "serves_truth" not in boundary and "candidate" not in boundary:
            raise AssertionError(f"{lane_id} promotion_boundary must mention candidate/serves_truth boundary")

    if daily_total < PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED:
        raise AssertionError(
            f"planned daily capacity {daily_total} is below minimum target "
            f"{PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED}"
        )
    if daily_total < PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED:
        raise AssertionError(
            f"planned daily capacity {daily_total} is below stretch target "
            f"{PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED}"
        )

    current_r4_groups = _current_r4_group_count()
    return {
        "lanes": len(rows),
        "planned_daily_verified_capacity": daily_total,
        "minimum_daily_target": PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED,
        "stretch_daily_target": PRIMITIVE_THROUGHPUT_STRETCH_DAILY_VERIFIED,
        "current_r4_curated_groups": current_r4_groups,
        "current_gap_to_minimum": max(0, PRIMITIVE_THROUGHPUT_MIN_DAILY_VERIFIED - current_r4_groups),
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
