#!/usr/bin/env python3
"""Validate generated AIDevExplorer task benchmark suites."""
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

from scripts._config import (
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS,
    AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR,
    AIDEVEXPLORER_TASK_BENCHMARK_SUITE_COUNT,
    AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE,
    REPO_ROOT,
)

TASKS_PATH = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
DEFAULT_SUITES_DIR = _resource(AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR)


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
    manifest = _read_json(run_dir / "manifest.json")
    suites = _read_jsonl(run_dir / "suites.jsonl")
    if manifest.get("candidate") is not True or manifest.get("serves_truth") is not False:
        raise AssertionError("manifest must keep candidate=true and serves_truth=false")
    if len(suites) != AIDEVEXPLORER_TASK_BENCHMARK_SUITE_COUNT:
        raise AssertionError("unexpected suite count")
    if int(manifest.get("suite_count") or 0) != len(suites):
        raise AssertionError("manifest suite_count mismatch")

    all_suite_task_ids: list[str] = []
    for suite in suites:
        suite_id = str(suite.get("suite_id") or "")
        if not suite_id:
            raise AssertionError("each suite must declare suite_id")
        if suite.get("candidate") is not True or suite.get("serves_truth") is not False:
            raise AssertionError(f"{suite_id} must keep candidate=true and serves_truth=false")
        task_ids = suite.get("task_ids")
        if not isinstance(task_ids, list) or len(task_ids) != AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE:
            raise AssertionError(f"{suite_id} must contain configured tasks_per_suite")
        unknown = set(str(task_id) for task_id in task_ids) - known_task_ids
        if unknown:
            raise AssertionError(f"{suite_id} references unknown task ids")
        all_suite_task_ids.extend(str(task_id) for task_id in task_ids)
        measurements = set(suite.get("measurement_plan") or [])
        for measurement in ("wall_clock_minutes", "prompt_tokens", "primitive_groups_used", "pitfalls_avoided"):
            if measurement not in measurements:
                raise AssertionError(f"{suite_id} missing measurement {measurement}")
        thresholds = suite.get("success_thresholds")
        if not isinstance(thresholds, dict) or thresholds.get("must_use_primitive_or_group") is not True:
            raise AssertionError(f"{suite_id} must require primitive/group use")

    if len(all_suite_task_ids) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("suite task total must cover all 10k tasks")
    if len(all_suite_task_ids) != len(set(all_suite_task_ids)):
        raise AssertionError("suite tasks must not repeat")
    if set(all_suite_task_ids) != known_task_ids:
        raise AssertionError("suite tasks must cover every corpus task")

    return {
        "run_date": run_date,
        "suites": len(suites),
        "tasks": len(all_suite_task_ids),
        "tasks_per_suite": AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE,
        "candidate_boundary": "candidate=true; serves_truth=false",
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
