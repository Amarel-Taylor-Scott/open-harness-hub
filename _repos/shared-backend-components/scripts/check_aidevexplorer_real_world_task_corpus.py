#!/usr/bin/env python3
"""Validate the AIDevExplorer 10k real-world build-task corpus."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_MANIFEST_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_REQUIRED_TASK_FIELDS,
    AIDEVEXPLORER_TASK_AUDIENCES,
    REPO_ROOT,
)

TASKS_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
MANIFEST_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_MANIFEST_PATH)


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


def _list(row: dict[str, Any], field: str, row_id: str, *, min_len: int = 1) -> list[Any]:
    value = row.get(field)
    if not isinstance(value, list) or len(value) < min_len:
        raise AssertionError(f"{row_id} must declare {field} with at least {min_len} item(s)")
    return value


def self_test() -> dict[str, Any]:
    rows = _read_jsonl(TASKS_PATH)
    manifest = _read_json(MANIFEST_PATH)
    if len(rows) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError(
            f"task corpus has {len(rows)} rows; expected "
            f"{AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS}"
        )
    if int(manifest.get("row_count") or 0) != len(rows):
        raise AssertionError("manifest row_count must match task rows")
    if manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must keep serves_truth=false")

    required_fields = set(AIDEVEXPLORER_REQUIRED_TASK_FIELDS)
    allowed_audiences = set(AIDEVEXPLORER_TASK_AUDIENCES)
    ids: list[str] = []
    families: set[str] = set()
    industries: set[str] = set()
    audiences: set[str] = set()
    group_hint_count = 0

    for row in rows:
        row_id = str(row.get("id") or "")
        if not row_id:
            raise AssertionError("every row must declare id")
        ids.append(row_id)
        missing = sorted(field for field in required_fields if field not in row)
        if missing:
            raise AssertionError(f"{row_id} missing fields: {missing}")
        if row.get("source_kind") != "curated_public_codegen_use_case":
            raise AssertionError(f"{row_id} must be compatible with public use-case ingestion")
        if row.get("corpus_kind") != "aidevexplorer_real_world_build_task":
            raise AssertionError(f"{row_id} must declare corpus_kind")
        if row.get("serves_truth") is not False:
            raise AssertionError(f"{row_id} must keep serves_truth=false")
        if row.get("trust") != "candidate":
            raise AssertionError(f"{row_id} must keep trust=candidate")
        audience = str(row.get("audience") or "")
        if audience not in allowed_audiences:
            raise AssertionError(f"{row_id} has unknown audience {audience!r}")
        audiences.add(audience)
        families.add(str(row.get("task_family") or ""))
        industries.add(str(row.get("industry") or ""))
        _list(row, "expected_primitives", row_id, min_len=4)
        groups = _list(row, "expected_primitive_groups", row_id)
        if groups:
            group_hint_count += 1
        _list(row, "expected_deliverables", row_id, min_len=3)
        _list(row, "acceptance_criteria", row_id, min_len=4)
        _list(row, "observed_reinvention_patterns", row_id, min_len=4)
        _list(row, "common_pitfalls", row_id, min_len=3)
        hooks = row.get("aidevexplorer_eval_hooks")
        if not isinstance(hooks, dict):
            raise AssertionError(f"{row_id} must declare aidevexplorer_eval_hooks")
        measurements = set(hooks.get("measurements") or [])
        for measurement in ("wall_clock_minutes", "prompt_tokens", "primitive_groups_used", "pitfalls_avoided"):
            if measurement not in measurements:
                raise AssertionError(f"{row_id} eval hooks missing {measurement}")
        thresholds = hooks.get("success_thresholds")
        if not isinstance(thresholds, dict) or thresholds.get("must_use_primitive_or_group") is not True:
            raise AssertionError(f"{row_id} must require primitive/group use in success thresholds")

    if len(ids) != len(set(ids)):
        raise AssertionError("task ids must be unique")
    if audiences != allowed_audiences:
        raise AssertionError(f"audience coverage mismatch: {sorted(audiences)}")
    if len(families) < 15:
        raise AssertionError("task corpus should cover at least 15 task families")
    if len(industries) < 75:
        raise AssertionError("task corpus should cover at least 75 industries/contexts")
    if group_hint_count != len(rows):
        raise AssertionError("every task should carry primitive group hints")

    return {
        "rows": len(rows),
        "task_families": len(families),
        "industries": len(industries),
        "audiences": sorted(audiences),
        "group_hint_rows": group_hint_count,
        "source_kind": "curated_public_codegen_use_case",
        "corpus_kind": "aidevexplorer_real_world_build_task",
        "serves_truth": False,
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
