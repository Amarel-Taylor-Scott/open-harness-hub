#!/usr/bin/env python3
"""Validate primitive problem-solution detail cards."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import json
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PACK_DIR = _resource("catalog/knowledge-packs/data/primitive-problem-solution-details")
OPPORTUNITY_DIR = _resource("catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings")
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


def _require_dict(row: dict[str, Any], field: str, row_id: str) -> dict[str, Any]:
    value = row.get(field)
    if not isinstance(value, dict) or not value:
        raise AssertionError(f"{row_id} must declare non-empty {field}")
    return value


def _check_id(value: str, row_id: str, field: str) -> None:
    if FORBIDDEN_ID_PATTERN.search(value):
        raise AssertionError(f"{row_id} field {field} must be version-free: {value!r}")


def self_test() -> dict[str, Any]:
    manifest = _read_json(MANIFEST_PATH)
    _require_candidate_boundary(manifest, "manifest")
    files = manifest.get("files")
    if not isinstance(files, dict):
        raise AssertionError("manifest must declare files")

    details = _read_jsonl(PACK_DIR / str(files["details"]))
    patterns = _read_jsonl(PACK_DIR / str(files["solution_patterns"]))
    template = _read_json(PACK_DIR / str(files["detail_template"]))
    opportunities = _read_jsonl(OPPORTUNITY_DIR / "primitive_opportunities_1000.jsonl")

    expected_detail_count = len(opportunities)
    if len(details) != expected_detail_count:
        raise AssertionError(f"expected {expected_detail_count} details; got {len(details)}")
    if manifest.get("detail_count") != len(details):
        raise AssertionError("manifest detail_count must match")
    if manifest.get("solution_pattern_count") != len(patterns):
        raise AssertionError("manifest solution_pattern_count must match")
    _require_candidate_boundary(template, "detail_template")

    opportunity_ids = {str(row["opportunity_id"]) for row in opportunities}
    detail_ids = {str(row.get("detail_id") or "") for row in details}
    if "" in detail_ids or len(detail_ids) != len(details):
        raise AssertionError("detail ids must be unique and non-empty")
    pattern_ids = {str(row.get("solution_pattern_id") or "") for row in patterns}
    if "" in pattern_ids or len(pattern_ids) != len(patterns):
        raise AssertionError("solution pattern ids must be unique and non-empty")

    for row in patterns:
        row_id = str(row["solution_pattern_id"])
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "solution_pattern_id")
        _require_list(row, "best_for_modules", row_id)
        _require_list(row, "route_steps", row_id, min_len=4)
        _require_list(row, "primary_receipts", row_id)

    linked_opportunities: set[str] = set()
    for row in details:
        row_id = str(row["detail_id"])
        _require_candidate_boundary(row, row_id)
        _check_id(row_id, row_id, "detail_id")
        opportunity_id = str(row.get("opportunity_id") or "")
        if opportunity_id not in opportunity_ids:
            raise AssertionError(f"{row_id} references unknown opportunity {opportunity_id!r}")
        linked_opportunities.add(opportunity_id)
        problem = _require_dict(row, "problem", row_id)
        solution = _require_dict(row, "solution", row_id)
        implementation = _require_dict(row, "implementation_notes", row_id)
        proof_plan = _require_dict(row, "proof_plan", row_id)
        example_io = _require_dict(row, "example_io", row_id)
        if str(solution.get("pattern_id") or "") not in pattern_ids:
            raise AssertionError(f"{row_id} references unknown solution pattern {solution.get('pattern_id')!r}")
        if not str(problem.get("statement") or ""):
            raise AssertionError(f"{row_id} problem.statement is required")
        _require_list(problem, "user_triggers", row_id, min_len=3)
        _require_list(problem, "stakes", row_id, min_len=3)
        _require_list(problem, "non_goals", row_id, min_len=3)
        _require_list(solution, "route_steps", row_id, min_len=4)
        _require_list(solution, "transformations", row_id, min_len=4)
        _require_list(solution, "runtime_targets", row_id, min_len=3)
        _require_list(solution, "source_surface_hints", row_id, min_len=3)
        _require_list(solution, "primary_receipts", row_id)
        _require_list(implementation, "base_components", row_id, min_len=4)
        _require_dict(implementation, "data_contract", row_id)
        _require_list(row, "acceptance_criteria", row_id, min_len=5)
        _require_list(proof_plan, "proof_requirements", row_id, min_len=4)
        _require_list(proof_plan, "minimum_fixtures", row_id, min_len=3)
        _require_list(row, "failure_modes", row_id, min_len=5)
        _require_list(row, "troubleshooting_hooks", row_id, min_len=5)
        _require_list(row, "negative_memory_queries", row_id, min_len=3)
        if not str(example_io.get("synthetic_input") or "") or not str(example_io.get("expected_output") or ""):
            raise AssertionError(f"{row_id} example_io must include synthetic_input and expected_output")
        if row.get("source_refs") != []:
            raise AssertionError(f"{row_id} source_refs should stay empty until verified")
        if row.get("source_evidence_status") != "curated_problem_solution_seed_needs_source_ref_resolution":
            raise AssertionError(f"{row_id} has wrong source_evidence_status")

    if linked_opportunities != opportunity_ids:
        raise AssertionError("every ranked opportunity should have exactly one detail card")

    return {
        "details": len(details),
        "solution_patterns": len(patterns),
        "linked_opportunities": len(linked_opportunities),
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
