#!/usr/bin/env python3
"""Validate generated AIDevExplorer benchmark task decompositions."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME,
    AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR,
    AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT,
    REPO_ROOT,
)

TASKS_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
DEFAULT_SUITES_DIR = _resource(AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR)
REQUIRED_MEASUREMENT_FIELDS = {
    "prompt_tokens",
    "completion_tokens",
    "total_tokens",
    "primitive_component_tokens",
    "wall_clock_minutes",
    "test_pass_rate",
}


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


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


def self_test(*, run_date: str, suites_dir: Path) -> dict[str, Any]:
    tasks = _read_jsonl(TASKS_PATH)
    known_task_ids = {str(task["id"]) for task in tasks}
    if len(known_task_ids) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("task corpus must contain unique 10k task ids")

    run_dir = suites_dir / run_date
    manifest = _read_json(run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_MANIFEST_FILENAME)
    rows = _read_jsonl(run_dir / AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITIONS_FILENAME)
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("decomposition manifest must keep candidate=true and serves_truth=false")
    if manifest.get("estimate_only") is not True or manifest.get("actual_run_required") is not True:
        raise AssertionError("decomposition manifest must mark token plans as estimate-only")
    if int(manifest.get("row_count") or 0) != len(rows):
        raise AssertionError("decomposition manifest row_count mismatch")
    if len(rows) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("decomposition rows must cover the full task corpus")

    seen_task_ids: set[str] = set()
    lens_values: set[str] = set()
    for row in rows:
        task_id = str(row.get("task_id") or "")
        if task_id not in known_task_ids:
            raise AssertionError(f"decomposition references unknown task id: {task_id}")
        if task_id in seen_task_ids:
            raise AssertionError(f"duplicate decomposition task id: {task_id}")
        seen_task_ids.add(task_id)
        if row.get("candidate") is not True or row.get("serves_truth") is not False:
            raise AssertionError(f"{task_id}: row must keep candidate=true and serves_truth=false")
        if row.get("decomposition_ready") is not True:
            raise AssertionError(f"{task_id}: decomposition must be ready")
        if row.get("decomposition_blockers"):
            raise AssertionError(f"{task_id}: decomposition blockers must be empty")
        components = row.get("logical_components")
        if not isinstance(components, list) or len(components) < AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS:
            raise AssertionError(f"{task_id}: insufficient logical components")
        component_ids = row.get("component_ids")
        if not isinstance(component_ids, list) or len(component_ids) != len(components):
            raise AssertionError(f"{task_id}: component id count mismatch")
        for component in components:
            if not isinstance(component, dict):
                raise AssertionError(f"{task_id}: component must be an object")
            component_id = str(component.get("component_id") or "")
            if not component_id:
                raise AssertionError(f"{task_id}: component missing id")
            if component.get("candidate") is not True or component.get("serves_truth") is not False:
                raise AssertionError(f"{task_id}:{component_id}: component must keep candidate boundary")
            if not component.get("kind"):
                raise AssertionError(f"{task_id}:{component_id}: component missing kind")
            if not component.get("input_edge") or not component.get("output_edge"):
                raise AssertionError(f"{task_id}:{component_id}: component missing visible edge")
            if not component.get("proof_requirements"):
                raise AssertionError(f"{task_id}:{component_id}: component missing proof requirements")
            if int(component.get("estimated_tokens") or 0) <= 0:
                raise AssertionError(f"{task_id}:{component_id}: component missing token estimate")
        token_plan = row.get("token_usage_plan")
        if not isinstance(token_plan, dict):
            raise AssertionError(f"{task_id}: missing token usage plan")
        if token_plan.get("estimate_only") is not True or token_plan.get("actual_run_required") is not True:
            raise AssertionError(f"{task_id}: token plan must be estimate-only and require actual run")
        if token_plan.get("comparison_blockers"):
            raise AssertionError(f"{task_id}: token comparison blockers must be empty")
        savings = float(token_plan.get("estimated_savings_percent") or 0)
        if savings < AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT:
            raise AssertionError(f"{task_id}: estimated savings below target")
        attributed = token_plan.get("component_token_attribution")
        if not isinstance(attributed, list) or len(attributed) != len(components):
            raise AssertionError(f"{task_id}: component token attribution mismatch")
        measurements = set(row.get("measurement_fields") or [])
        if not REQUIRED_MEASUREMENT_FIELDS.issubset(measurements):
            raise AssertionError(f"{task_id}: missing required measurement fields")
        lens = str(row.get("benchmark_lens") or "")
        if not lens:
            raise AssertionError(f"{task_id}: missing benchmark lens")
        lens_values.add(lens)

    if seen_task_ids != known_task_ids:
        raise AssertionError("decomposition rows must exactly cover the task corpus")

    return {
        "run_date": run_date,
        "rows": len(rows),
        "benchmark_lenses": len(lens_values),
        "min_components": AIDEVEXPLORER_TASK_BENCHMARK_DECOMPOSITION_MIN_COMPONENTS,
        "token_savings_target_percent": AIDEVEXPLORER_TASK_BENCHMARK_TOKEN_SAVINGS_TARGET_PERCENT,
        "candidate_boundary": "candidate=true; serves_truth=false",
        "token_plans": "estimate_only; actual_run_required",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--suites-dir", default=str(DEFAULT_SUITES_DIR))
    args = parser.parse_args(argv)
    try:
        result = self_test(run_date=args.date, suites_dir=Path(args.suites_dir))
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
