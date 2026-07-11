#!/usr/bin/env python3
"""Run an end-to-end AIDevObserver primitive flywheel proof cycle.

This script ties together the operational pieces that matter for the primitive
database loop:

* optional multi-provider primitive candidate generation;
* ledger repair and monitor snapshots;
* real-world task-corpus checks;
* registry/search and IDE plan route pickup across a stratified task sample;
* observer/UI API self-tests;
* machine-readable run artifacts.

All outputs remain candidate evidence. Nothing here promotes primitive truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
    AIDEVOBSERVER_FLYWHEEL_RUNS_DIR,
    AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    REPO_ROOT,
)
from scripts.gemma_usage_monitor import build_snapshot as build_gemma_snapshot  # noqa: E402
from scripts.observer_local_service import ide_run_plan  # noqa: E402
from src.teleon.observer.registry_search import registry_search_response  # noqa: E402

DEFAULT_SAMPLE_SIZE = 20
DEFAULT_ROUTE_LIMIT = 8


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":"), ensure_ascii=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if isinstance(row, dict):
            rows.append(row)
    return rows


def _run_command(args: list[str], *, timeout: int = 600) -> dict[str, Any]:
    started = time.time()
    proc = subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    output = proc.stdout or ""
    return {
        "command": args,
        "returncode": proc.returncode,
        "duration_seconds": round(time.time() - started, 3),
        "output_tail": output[-6000:],
        "candidate": True,
        "serves_truth": False,
    }


def _select_stratified_tasks(tasks: list[dict[str, Any]], sample_size: int) -> list[dict[str, Any]]:
    by_family: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for task in tasks:
        by_family[str(task.get("task_family") or "unknown")].append(task)
    families = sorted(by_family)
    selected: list[dict[str, Any]] = []
    cursor = 0
    while len(selected) < sample_size and families:
        family = families[cursor % len(families)]
        bucket = by_family[family]
        if bucket:
            selected.append(bucket.pop(0))
        families = [item for item in families if by_family[item]]
        cursor += 1
    return selected


def _flatten_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, list):
        return " ".join(_flatten_text(item) for item in value)
    return str(value or "")


def _expected_terms(task: dict[str, Any]) -> set[str]:
    raw = [
        *(task.get("expected_primitives") or []),
        *(task.get("expected_primitive_groups") or []),
        str(task.get("expected_template") or ""),
        str(task.get("task_family") or ""),
    ]
    terms: set[str] = set()
    for item in raw:
        for part in str(item).replace("grp:", " ").replace("prim:", " ").replace("@candidate", " ").replace("@1", " ").replace(".", " ").replace("_", " ").replace("-", " ").split():
            if len(part) >= 4:
                terms.add(part.lower())
    return terms


def _hit_source_kind(hit: dict[str, Any]) -> str:
    card = hit.get("reuse_card") if isinstance(hit.get("reuse_card"), dict) else hit
    return str(card.get("source_kind") or hit.get("source_kind") or "")


def _component_source_kind(component: dict[str, Any]) -> str:
    return str(component.get("source_kind") or "")


def route_test_task(task: dict[str, Any], *, route_limit: int) -> dict[str, Any]:
    intent = str(task.get("intent") or "")
    started = time.time()
    status, registry_payload = registry_search_response(
        intent,
        None,
        route_limit,
        visibility_scope=AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    )
    registry_hits = registry_payload.get("hits") if isinstance(registry_payload.get("hits"), list) else []
    plan_status, plan = ide_run_plan({
        "task": intent,
        "planner_llm": False,
        "visibility_scope": AIDEVOBSERVER_VISIBILITY_SCOPE_PUBLIC,
    })
    selected_components = plan.get("selected_components") if isinstance(plan.get("selected_components"), list) else []
    selected_route_context = plan.get("selected_route_context") if isinstance(plan.get("selected_route_context"), list) else []
    workspace_files = plan.get("workspace_files") if isinstance(plan.get("workspace_files"), list) else []
    recipe = plan.get("recipe") if isinstance(plan.get("recipe"), dict) else {}
    route_quality = plan.get("route_quality") if isinstance(plan.get("route_quality"), dict) else {}
    expected = _expected_terms(task)
    observed_blob = " ".join([
        _flatten_text(registry_hits),
        _flatten_text(selected_components),
        _flatten_text(selected_route_context),
        _flatten_text(recipe),
    ]).lower()
    expected_matches = sorted(term for term in expected if term in observed_blob)
    all_components = selected_components + selected_route_context
    registry_source_kinds = sorted({_hit_source_kind(hit) for hit in registry_hits if _hit_source_kind(hit)})
    component_source_kinds = sorted({_component_source_kind(component) for component in all_components if _component_source_kind(component)})
    candidate_boundary_ok = (
        registry_payload.get("candidate") is True
        and registry_payload.get("serves_truth") is False
        and plan.get("candidate") is True
        and plan.get("serves_truth") is False
    )
    primitive_hits = len(registry_hits)
    route_records = int((plan.get("route_context") or {}).get("selected_route_records") or len(selected_route_context))
    selected_count = len(selected_components)
    workspace_proof_count = sum(
        1 for item in workspace_files
        if "test" in str(item.get("path") or "").lower()
        or "proof" in str(item.get("path") or "").lower()
        or "receipt" in str(item.get("path") or "").lower()
    )
    execution_mode = str(plan.get("execution_mode") or "")
    core_pass = (
        status == 200
        and plan_status == 200
        and candidate_boundary_ok
        and primitive_hits > 0
        and (route_records > 0 or selected_count > 0)
        and execution_mode != "noop"
    )
    return {
        "record_type": "aidevobserver_real_task_route_probe",
        "task_id": task.get("id"),
        "task_family": task.get("task_family"),
        "audience": task.get("audience"),
        "industry": task.get("industry"),
        "title": task.get("title"),
        "registry_status": status,
        "plan_status": plan_status,
        "primitive_hits": primitive_hits,
        "registry_source_kinds": registry_source_kinds,
        "operational_hits": sum(1 for hit in registry_hits if _hit_source_kind(hit) == "operational_primitive_registry"),
        "selected_components": selected_count,
        "route_records": route_records,
        "component_source_kinds": component_source_kinds,
        "execution_mode": execution_mode,
        "workspace_files": len(workspace_files),
        "workspace_proof_files": workspace_proof_count,
        "planner_model_calls": int((plan.get("planner_result") or {}).get("model_calls") or 0),
        "recipe_kind": recipe.get("kind") or recipe.get("record_type"),
        "route_quality": route_quality,
        "expected_match_terms": expected_matches,
        "expected_match_count": len(expected_matches),
        "candidate_boundary_ok": candidate_boundary_ok,
        "core_pass": core_pass,
        "duration_seconds": round(time.time() - started, 3),
        "candidate": True,
        "serves_truth": False,
    }


def _rate(count: int, total: int) -> float:
    return round(count / total, 4) if total else 0.0


def route_test_tasks(tasks: list[dict[str, Any]], *, sample_size: int, route_limit: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected = _select_stratified_tasks(tasks, sample_size)
    rows = [route_test_task(task, route_limit=route_limit) for task in selected]
    total = len(rows)
    summary = {
        "sample_size": total,
        "task_families": sorted({str(row.get("task_family")) for row in rows}),
        "core_pass_count": sum(1 for row in rows if row.get("core_pass")),
        "candidate_boundary_pass_count": sum(1 for row in rows if row.get("candidate_boundary_ok")),
        "registry_hit_pass_count": sum(1 for row in rows if int(row.get("primitive_hits") or 0) > 0),
        "route_pickup_pass_count": sum(1 for row in rows if int(row.get("route_records") or 0) > 0 or int(row.get("selected_components") or 0) > 0),
        "operational_hit_task_count": sum(1 for row in rows if int(row.get("operational_hits") or 0) > 0),
        "workspace_proof_task_count": sum(1 for row in rows if int(row.get("workspace_proof_files") or 0) > 0),
        "expected_match_task_count": sum(1 for row in rows if int(row.get("expected_match_count") or 0) > 0),
        "avg_duration_seconds": round(sum(float(row.get("duration_seconds") or 0) for row in rows) / total, 3) if total else 0,
        "candidate": True,
        "serves_truth": False,
    }
    summary["core_pass_rate"] = _rate(summary["core_pass_count"], total)
    summary["candidate_boundary_pass_rate"] = _rate(summary["candidate_boundary_pass_count"], total)
    summary["registry_hit_pass_rate"] = _rate(summary["registry_hit_pass_count"], total)
    summary["route_pickup_pass_rate"] = _rate(summary["route_pickup_pass_count"], total)
    summary["operational_hit_task_rate"] = _rate(summary["operational_hit_task_count"], total)
    summary["workspace_proof_task_rate"] = _rate(summary["workspace_proof_task_count"], total)
    summary["expected_match_task_rate"] = _rate(summary["expected_match_task_count"], total)
    return rows, summary


def _command_checks(*, include_observer_self_test: bool) -> list[list[str]]:
    checks = [
        ["python3", str(_resource("scripts/check_aidevexplorer_real_world_task_corpus.py"))],
        ["python3", str(_resource("scripts/check_aidevexplorer_task_benchmark_suites.py"))],
        ["python3", str(_resource("scripts/check_aidevobserver_operational_primitive_search.py"))],
        ["python3", str(_resource("scripts/primitive_route_fixture_verifier.py")), "--self-test"],
        ["python3", "-m", "unittest", "tests/unit/test_teleon_primitive_groups.py"],
    ]
    if include_observer_self_test:
        checks.append(["python3", str(_resource("scripts/observer_local_service.py")), "--self-test"])
    return checks


def run_cycle(
    *,
    run_date: str,
    sample_size: int,
    route_limit: int,
    out_dir: Path,
    run_generation: bool,
    generation_scale: int,
    include_observer_self_test: bool,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    tasks_path = _resource(AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH)
    tasks = _read_jsonl(tasks_path)
    before_snapshot = build_gemma_snapshot(run_date=run_date, include_processes=True, check_cdp_target=True)
    generation_result: dict[str, Any] | None = None
    if run_generation:
        generation_result = _run_command(
            [
                "python3",
                str(_resource("scripts/run_primitive_provider_fleet_loop.py")),
                "--date",
                run_date,
                "--target-profile",
                "20k",
                "--scale",
                str(generation_scale),
                "--max-cycles",
                "1",
                "--sleep-seconds",
                "0",
            ],
            timeout=3600,
        )
    repair_result = _run_command(["python3", str(_resource("scripts/repair_primitive_factory_batch_ledgers.py")), "--date", run_date], timeout=300)
    after_snapshot = build_gemma_snapshot(run_date=run_date, include_processes=True, check_cdp_target=True)
    check_results = [
        _run_command(command, timeout=900)
        for command in _command_checks(include_observer_self_test=include_observer_self_test)
    ]
    route_rows, route_summary = route_test_tasks(tasks, sample_size=sample_size, route_limit=route_limit)
    _write_jsonl(out_dir / "task_route_results.jsonl", route_rows)
    _write_json(out_dir / "before_monitor_snapshot.json", before_snapshot)
    _write_json(out_dir / "after_monitor_snapshot.json", after_snapshot)
    _write_json(out_dir / "check_results.json", {"checks": check_results, "candidate": True, "serves_truth": False})
    if generation_result is not None:
        _write_json(out_dir / "generation_result.json", generation_result)

    failed_checks = [row for row in check_results if int(row.get("returncode") or 0) != 0]
    before_all = before_snapshot.get("all_provider_totals", {})
    after_all = after_snapshot.get("all_provider_totals", {})
    before_gemma = (before_snapshot.get("gemma") or {}).get("totals", {})
    after_gemma = (after_snapshot.get("gemma") or {}).get("totals", {})
    manifest = {
        "record_type": "aidevobserver_flywheel_proof_run",
        "run_date": run_date,
        "created_at": _now_utc(),
        "out_dir": _rel(out_dir),
        "task_corpus_path": AIDEVEXPLORER_REAL_WORLD_TASK_CORPUS_PATH,
        "task_corpus_rows": len(tasks),
        "sample_size": sample_size,
        "route_limit": route_limit,
        "run_generation": run_generation,
        "generation_scale": generation_scale if run_generation else 0,
        "generation_returncode": generation_result.get("returncode") if generation_result else None,
        "repair_returncode": repair_result.get("returncode"),
        "check_count": len(check_results),
        "failed_check_count": len(failed_checks),
        "failed_checks": [row.get("command") for row in failed_checks],
        "route_summary": route_summary,
        "provider_delta": {
            "accepted_count": int(after_all.get("accepted_count") or 0) - int(before_all.get("accepted_count") or 0),
            "total_tokens": int((after_all.get("usage") or {}).get("total_tokens") or 0) - int((before_all.get("usage") or {}).get("total_tokens") or 0),
            "worker_error_count": int(after_all.get("worker_error_count") or 0) - int(before_all.get("worker_error_count") or 0),
        },
        "gemma_delta": {
            "accepted_count": int(after_gemma.get("accepted_count") or 0) - int(before_gemma.get("accepted_count") or 0),
            "total_tokens": int((after_gemma.get("usage") or {}).get("total_tokens") or 0) - int((before_gemma.get("usage") or {}).get("total_tokens") or 0),
            "worker_error_count": int(after_gemma.get("worker_error_count") or 0) - int(before_gemma.get("worker_error_count") or 0),
        },
        "pass": (
            not failed_checks
            and int(repair_result.get("returncode") or 0) == 0
            and (generation_result is None or int(generation_result.get("returncode") or 0) == 0)
            and float(route_summary.get("core_pass_rate") or 0) >= 0.9
            and float(route_summary.get("candidate_boundary_pass_rate") or 0) == 1.0
        ),
        "duration_seconds": round(time.time() - started, 3),
        "candidate": True,
        "serves_truth": False,
    }
    summary = [
        "# AIDevObserver Flywheel Proof Run",
        "",
        f"- run_date: `{run_date}`",
        f"- pass: `{manifest['pass']}`",
        f"- generation: `{run_generation}`",
        f"- provider accepted delta: `{manifest['provider_delta']['accepted_count']}`",
        f"- provider token delta: `{manifest['provider_delta']['total_tokens']}`",
        f"- route core pass rate: `{route_summary['core_pass_rate']}`",
        f"- route pickup pass rate: `{route_summary['route_pickup_pass_rate']}`",
        f"- operational-hit task rate: `{route_summary['operational_hit_task_rate']}`",
        f"- failed checks: `{manifest['failed_check_count']}`",
        "",
        "Outputs remain `candidate=true` and `serves_truth=false`.",
    ]
    (out_dir / "summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    _write_json(out_dir / "manifest.json", manifest)
    return manifest


def _self_test() -> int:
    rows = [
        {"id": "a", "task_family": "one"},
        {"id": "b", "task_family": "two"},
        {"id": "c", "task_family": "one"},
    ]
    selected = _select_stratified_tasks(rows, 2)
    ok = (
        len(selected) == 2
        and len({row["task_family"] for row in selected}) == 2
        and "validate" in _expected_terms({"expected_primitives": ["api.validate_json_schema"]})
    )
    print("PASS - AIDevObserver flywheel proof runner helpers are wired." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE)
    parser.add_argument("--route-limit", type=int, default=DEFAULT_ROUTE_LIMIT)
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--run-generation", action="store_true")
    parser.add_argument("--generation-scale", type=int, default=1)
    parser.add_argument("--skip-observer-self-test", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    out_dir = (
        Path(args.out_dir)
        if args.out_dir
        else _resource(AIDEVOBSERVER_FLYWHEEL_RUNS_DIR) / args.date / _stamp()
    )
    manifest = run_cycle(
        run_date=args.date,
        sample_size=max(1, args.sample_size),
        route_limit=max(1, args.route_limit),
        out_dir=out_dir if out_dir.is_absolute() else _resource(out_dir),
        run_generation=args.run_generation,
        generation_scale=max(1, args.generation_scale),
        include_observer_self_test=not args.skip_observer_self_test,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
