#!/usr/bin/env python3
"""Run repeated primitive provider-fleet cycles.

This wraps the plan -> execute -> measure loop for multi-provider primitive
candidate generation. It never promotes truth; each cycle uses the batch-loop
runner, which extracts candidate JSONL and writes ledgers.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    PRIMITIVE_FACTORY_FLEET_RUNS_DIR,
    PRIMITIVE_FACTORY_PROVIDER_FLEET_LANES,
    REPO_ROOT,
)
from scripts.plan_primitive_provider_fleet import (  # noqa: E402
    _default_shards_path,
    build_plan,
    write_plan,
)

DEFAULT_STOP_FILE = _resource("data") / "dev-intel" / "primitive_factory" / "STOP"


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _safe_label(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-") or "fleet"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path}: expected JSON object")
    return value


def _filtered_lanes(*, only_lanes: list[str], exclude_lanes: list[str]) -> list[dict[str, Any]]:
    lanes = [dict(row) for row in PRIMITIVE_FACTORY_PROVIDER_FLEET_LANES]
    only = set(only_lanes)
    exclude = set(exclude_lanes)
    if only:
        lanes = [lane for lane in lanes if str(lane.get("lane_id") or "") in only]
    if exclude:
        lanes = [lane for lane in lanes if str(lane.get("lane_id") or "") not in exclude]
    if not lanes:
        raise AssertionError("provider fleet lane filters removed every lane")
    return lanes


def _default_run_label(*, only_lanes: list[str], exclude_lanes: list[str]) -> str:
    if only_lanes:
        return _safe_label("only-" + "-".join(sorted(only_lanes)))
    if exclude_lanes:
        return _safe_label("exclude-" + "-".join(sorted(exclude_lanes)))
    return "all-lanes"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _manifest_path_for_lane(run_date: str, target_profile: str, provider: str, model: str, mode: str) -> Path:
    safe_model = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in model).strip("-") or "model"
    return _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR) / run_date / f"{target_profile}_{provider}_{safe_model}_{mode}" / "manifest.json"


def _run_lane(lane: dict[str, Any], *, cycle_dir: Path, dry_run: bool) -> dict[str, Any]:
    command = str(lane["dry_run_command"] if dry_run else lane["live_command"])
    log_path = cycle_dir / f"{lane['lane_id']}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with log_path.open("w", encoding="utf-8") as log:
        proc = subprocess.Popen(
            shlex.split(command),
            cwd=REPO_ROOT,
            stdout=log,
            stderr=subprocess.STDOUT,
            text=True,
        )
        returncode = proc.wait()
    elapsed = round(time.time() - started, 3)
    manifest_path = _manifest_path_for_lane(
        str(lane["run_date"]) if lane.get("run_date") else "",
        str(lane.get("target_profile") or ""),
        str(lane["provider"]),
        str(lane["model"]),
        str(lane["mode"]),
    )
    return {
        "lane_id": lane["lane_id"],
        "provider": lane["provider"],
        "model": lane["model"],
        "mode": lane["mode"],
        "start_offset": lane["start_offset"],
        "end_offset_exclusive": lane["end_offset_exclusive"],
        "planned_shards": lane["planned_shards"],
        "command": command,
        "log_path": _rel(log_path),
        "returncode": returncode,
        "duration_seconds": elapsed,
        "batch_manifest_path": _rel(manifest_path) if manifest_path.exists() else "",
        "batch_manifest": _read_json(manifest_path) if manifest_path.exists() else {},
        "candidate": True,
        "serves_truth": False,
    }


def run_loop(
    *,
    run_date: str,
    target_profile: str,
    scale: int,
    max_cycles: int,
    sleep_seconds: float,
    stop_file: Path,
    dry_run: bool,
    max_tokens: int,
    only_lanes: list[str],
    exclude_lanes: list[str],
    run_label: str,
) -> dict[str, Any]:
    if scale <= 0:
        raise AssertionError("scale must be positive")
    if max_cycles < 0:
        raise AssertionError("max_cycles must be >= 0")
    shards_path = _default_shards_path(run_date, target_profile)
    batch_runs_root = _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR)
    label = _safe_label(run_label or _default_run_label(only_lanes=only_lanes, exclude_lanes=exclude_lanes))
    run_root = _resource(PRIMITIVE_FACTORY_FLEET_RUNS_DIR) / run_date / label
    loop_started = time.time()
    cycles: list[dict[str, Any]] = []
    cycle_index = 0
    fleet_lanes = _filtered_lanes(only_lanes=only_lanes, exclude_lanes=exclude_lanes)

    while True:
        if stop_file.exists():
            break
        if max_cycles and cycle_index >= max_cycles:
            break
        cycle_index += 1
        cycle_dir = run_root / f"cycle_{cycle_index:04d}"
        plan = build_plan(
            run_date=run_date,
            target_profile=target_profile,
            shards_path=shards_path,
            batch_runs_root=batch_runs_root,
            start_offset=0,
            scale=scale,
            max_tokens=max_tokens,
            include_dry_run_intervals=False,
            fleet_lanes=fleet_lanes,
        )
        for lane in plan["lanes"]:
            lane["run_date"] = run_date
            lane["target_profile"] = target_profile
        paths = write_plan(plan, run_root)
        cycle_started = time.time()
        lane_results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=max(1, len(plan["lanes"]))) as pool:
            futures = [
                pool.submit(_run_lane, lane, cycle_dir=cycle_dir, dry_run=dry_run)
                for lane in plan["lanes"]
            ]
            for future in as_completed(futures):
                lane_results.append(future.result())
        lane_results.sort(key=lambda row: str(row.get("lane_id") or ""))
        cycle_elapsed = round(time.time() - cycle_started, 3)
        cycle = {
            "cycle_index": cycle_index,
            "plan_path": paths.get("plan_path", ""),
            "commands_path": paths.get("commands_path", ""),
            "scale": scale,
            "dry_run": dry_run,
            "lane_results": lane_results,
            "returncode_max": max((int(row["returncode"]) for row in lane_results), default=0),
            "duration_seconds": cycle_elapsed,
            "created_at": _now_utc(),
            "candidate": True,
            "serves_truth": False,
        }
        _write_json(cycle_dir / "cycle_manifest.json", cycle)
        cycles.append(cycle)
        if any(int(row["returncode"]) != 0 for row in lane_results):
            break
        if sleep_seconds > 0 and not stop_file.exists():
            time.sleep(sleep_seconds)

    manifest = {
        "record_type": "primitive_provider_fleet_loop_manifest",
        "run_date": run_date,
        "target_profile": target_profile,
        "scale": scale,
        "run_label": label,
        "run_root": _rel(run_root),
        "only_lanes": only_lanes,
        "exclude_lanes": exclude_lanes,
        "max_cycles": max_cycles,
        "completed_cycles": len(cycles),
        "stop_file": _rel(stop_file),
        "stop_file_present": stop_file.exists(),
        "dry_run": dry_run,
        "duration_seconds": round(time.time() - loop_started, 3),
        "cycles": cycles,
        "candidate": True,
        "serves_truth": False,
        "created_at": _now_utc(),
    }
    _write_json(run_root / "loop_manifest.json", manifest)
    return manifest


def _self_test() -> int:
    stop_file = _resource("this-file-should-not-exist-for-primitive-provider-loop-self-test")
    ok = (
        not stop_file.exists()
        and LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS >= 65536
        and _default_run_label(only_lanes=["a"], exclude_lanes=[]) == "only-a"
        and _default_run_label(only_lanes=[], exclude_lanes=["b"]) == "exclude-b"
    )
    print("PASS - primitive provider fleet loop wiring is candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--target-profile", choices=["5k", "20k"], default="20k")
    parser.add_argument("--scale", type=int, default=1)
    parser.add_argument("--max-cycles", type=int, default=1, help="0 means loop until stop file or failure.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--stop-file", default=str(DEFAULT_STOP_FILE))
    parser.add_argument("--max-tokens", type=int, default=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS)
    parser.add_argument("--only-lane", action="append", default=[])
    parser.add_argument("--exclude-lane", action="append", default=[])
    parser.add_argument("--run-label", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    try:
        manifest = run_loop(
            run_date=args.date,
            target_profile=args.target_profile,
            scale=args.scale,
            max_cycles=args.max_cycles,
            sleep_seconds=args.sleep_seconds,
            stop_file=Path(args.stop_file),
            dry_run=args.dry_run,
            max_tokens=args.max_tokens,
            only_lanes=list(args.only_lane or []),
            exclude_lanes=list(args.exclude_lane or []),
            run_label=args.run_label,
        )
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if not any(cycle["returncode_max"] for cycle in manifest["cycles"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
