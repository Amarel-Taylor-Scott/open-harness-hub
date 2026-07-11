#!/usr/bin/env python3
"""Build balanced benchmark suites from the AIDevExplorer 10k task corpus."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
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
DEFAULT_OUT_DIR = _resource(AIDEVEXPLORER_TASK_BENCHMARK_SUITES_DIR)


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


def _sha(value: Any, *, n: int = 12) -> str:
    text = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:n]


def _suite(tasks: list[dict[str, Any]], *, run_date: str, index: int) -> dict[str, Any]:
    families = sorted({str(task["task_family"]) for task in tasks})
    industries = sorted({str(task["industry"]) for task in tasks})
    audiences = sorted({str(task["audience"]) for task in tasks})
    task_ids = [str(task["id"]) for task in tasks]
    suite_id = f"aidevexplorer-suite-{run_date.replace('-', '')}-{index + 1:03d}-{_sha(task_ids)}"
    return {
        "record_type": "aidevexplorer_task_benchmark_suite",
        "suite_id": suite_id,
        "run_date": run_date,
        "suite_index": index + 1,
        "task_count": len(tasks),
        "task_ids": task_ids,
        "task_families": families,
        "industries": industries,
        "audiences": audiences,
        "baseline_runner": "generic_ai_coding_agent_without_primitive_search",
        "candidate_runner": "aidevexplorer_with_primitive_search_and_route_assembly",
        "measurement_plan": [
            "wall_clock_minutes",
            "prompt_tokens",
            "completion_tokens",
            "files_touched",
            "custom_code_lines",
            "primitive_hits",
            "primitive_groups_used",
            "test_pass_rate",
            "pitfalls_avoided",
            "rework_loops",
        ],
        "success_thresholds": {
            "target_token_reduction_percent": 30,
            "target_time_reduction_percent": 25,
            "must_use_primitive_or_group": True,
            "must_emit_tests_or_proof": True,
        },
        "artifact_outputs": [
            "baseline_run_receipts.jsonl",
            "aidevexplorer_run_receipts.jsonl",
            "suite_comparison_report.json",
            "pitfall_avoidance_report.jsonl",
        ],
        "candidate": True,
        "serves_truth": False,
    }


def build_suites(*, run_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    tasks = _read_jsonl(TASKS_PATH)
    if len(tasks) != AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_TARGET_ROWS:
        raise AssertionError("task corpus must be generated and validated before suite build")
    suites: list[dict[str, Any]] = []
    for index in range(AIDEVEXPLORER_TASK_BENCHMARK_SUITE_COUNT):
        start = index * AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE
        stop = start + AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE
        suites.append(_suite(tasks[start:stop], run_date=run_date, index=index))
    manifest = {
        "record_type": "aidevexplorer_task_benchmark_manifest",
        "run_date": run_date,
        "suite_count": len(suites),
        "tasks_per_suite": AIDEVEXPLORER_TASK_BENCHMARK_TASKS_PER_SUITE,
        "task_count": sum(int(suite["task_count"]) for suite in suites),
        "task_corpus_path": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
        "baseline_runner": "generic_ai_coding_agent_without_primitive_search",
        "candidate_runner": "aidevexplorer_with_primitive_search_and_route_assembly",
        "candidate": True,
        "serves_truth": False,
    }
    return suites, manifest


def write_suites(run_date: str, suites: list[dict[str, Any]], manifest: dict[str, Any], out_dir: Path) -> dict[str, str]:
    run_dir = out_dir / run_date
    run_dir.mkdir(parents=True, exist_ok=True)
    suites_path = run_dir / "suites.jsonl"
    manifest_path = run_dir / "manifest.json"
    suites_path.write_text(
        "".join(json.dumps(suite, sort_keys=True, separators=(",", ":")) + "\n" for suite in suites),
        encoding="utf-8",
    )
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "run_dir": str(run_dir.relative_to(REPO_ROOT)),
        "suites_path": str(suites_path.relative_to(REPO_ROOT)),
        "manifest_path": str(manifest_path.relative_to(REPO_ROOT)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        suites, manifest = build_suites(run_date=args.date)
        paths = {} if args.check_only else write_suites(args.date, suites, manifest, Path(args.out_dir))
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({**manifest, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
