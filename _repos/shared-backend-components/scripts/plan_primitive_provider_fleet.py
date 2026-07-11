#!/usr/bin/env python3
"""Plan disjoint primitive-factory provider windows.

The planner writes commands for Gemma/Open WebUI, GLM/Ollama Cloud, and
Kimi/Ollama Cloud without calling any model. It reads existing batch ledgers,
allocates non-overlapping shard offsets, and keeps all output candidate-only.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    PRIMITIVE_FACTORY_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_FLEET_RUNS_DIR,
    PRIMITIVE_FACTORY_PROVIDER_FLEET_LANES,
    REPO_ROOT,
)

DEFAULT_TARGET_PROFILE = "20k"
DEFAULT_SCALE = 1
ACTIVE_BATCH_PROCESS_TERMS = ("scripts/run_primitive_factory_batch_loop.py", "run_primitive_factory_batch_loop.py")


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _safe_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value).strip("-") or "fleet"


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        raise AssertionError(f"missing JSONL file: {path}")
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_number}: invalid JSONL: {exc}") from exc
        if not isinstance(row, dict):
            raise AssertionError(f"{path}:{line_number}: expected object")
        rows.append(row)
    return rows


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _default_shards_path(run_date: str, target_profile: str) -> Path:
    base = PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR if target_profile == "20k" else PRIMITIVE_FACTORY_DAILY_SHARDS_DIR
    return _resource(base) / run_date / "shards.jsonl"


def _batch_root() -> Path:
    return _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR)


def _fleet_root() -> Path:
    return _resource(PRIMITIVE_FACTORY_FLEET_RUNS_DIR)


def _ledger_intervals(
    *,
    run_date: str,
    target_profile: str,
    batch_runs_root: Path,
    include_dry_run: bool,
) -> list[tuple[int, int]]:
    intervals: list[tuple[int, int]] = []
    for ledger in sorted((batch_runs_root / run_date).glob(f"{target_profile}_*/batch_ledger.jsonl")):
        for row in _read_jsonl(ledger):
            if str(row.get("target_profile") or "") != target_profile:
                continue
            if bool(row.get("dry_run")) and not include_dry_run:
                continue
            start = int(row.get("offset") or 0)
            length = int(row.get("limit") or row.get("selected_shards") or 0)
            if length > 0:
                intervals.append((start, start + length))
    return intervals


def _arg_value(parts: list[str], name: str, default: str = "") -> str:
    try:
        index = parts.index(name)
    except ValueError:
        return default
    if index + 1 >= len(parts):
        return default
    return parts[index + 1]


def _active_batch_process_rows(ps_text: str, *, run_date: str, target_profile: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in ps_text.splitlines():
        if not any(term in line for term in ACTIVE_BATCH_PROCESS_TERMS):
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            continue
        command_index = next(
            (index for index, part in enumerate(parts) if part.endswith("run_primitive_factory_batch_loop.py")),
            -1,
        )
        if command_index < 0:
            continue
        pid = parts[0] if parts and parts[0].isdigit() else ""
        args = parts[command_index:]
        if "--dry-run" in args:
            continue
        if _arg_value(args, "--date") != run_date:
            continue
        if _arg_value(args, "--target-profile") != target_profile:
            continue
        try:
            start = int(_arg_value(args, "--start-offset", "0") or 0)
            batch_size = int(_arg_value(args, "--batch-size", "0") or 0)
            max_batches = int(_arg_value(args, "--max-batches", "1") or 1)
        except ValueError:
            continue
        length = batch_size * max(1, max_batches)
        if length <= 0:
            continue
        rows.append({
            "pid": pid,
            "provider": _arg_value(args, "--provider"),
            "model": _arg_value(args, "--model"),
            "mode": _arg_value(args, "--mode"),
            "start_offset": start,
            "end_offset_exclusive": start + length,
            "planned_shards": length,
            "command": " ".join(args),
            "candidate": True,
            "serves_truth": False,
        })
    return rows


def _active_process_intervals(*, run_date: str, target_profile: str) -> list[tuple[int, int]]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "pid,etime,args"],
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
    except Exception:  # noqa: BLE001
        return []
    rows = _active_batch_process_rows(proc.stdout, run_date=run_date, target_profile=target_profile)
    return [
        (int(row["start_offset"]), int(row["end_offset_exclusive"]))
        for row in rows
    ]


def _merge_intervals(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[tuple[int, int]] = []
    for start, end in sorted(intervals):
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return merged


def _next_free_start(
    intervals: list[tuple[int, int]],
    *,
    desired_start: int,
    length: int,
    available_shards: int,
) -> int:
    if length <= 0:
        raise AssertionError("planned length must be positive")
    cursor = max(0, desired_start)
    for start, end in _merge_intervals(intervals):
        if cursor + length <= start:
            break
        if cursor < end and cursor + length > start:
            cursor = end
    if cursor + length > available_shards:
        raise AssertionError("not enough remaining shards for the provider fleet plan")
    return cursor


def _command(args: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in args)


def _batch_command(
    *,
    run_date: str,
    target_profile: str,
    shards_path: Path,
    lane: dict[str, Any],
    start_offset: int,
    batch_size: int,
    max_tokens: int,
    dry_run: bool,
) -> str:
    args = [
        "python3",
        str(_resource("scripts/run_primitive_factory_batch_loop.py")),
        "--date",
        run_date,
        "--target-profile",
        target_profile,
        "--shards",
        _rel(shards_path),
        "--provider",
        str(lane["provider"]),
        "--mode",
        str(lane["mode"]),
        "--model",
        str(lane["model"]),
        "--start-offset",
        str(start_offset),
        "--batch-size",
        str(batch_size),
        "--max-batches",
        str(int(lane["max_batches"])),
        "--workers",
        str(int(lane["workers"])),
        "--max-tokens",
        str(max_tokens),
        "--timeout",
        str(int(lane["timeout"])),
    ]
    if dry_run:
        args.append("--dry-run")
    return _command(args)


def build_plan(
    *,
    run_date: str,
    target_profile: str,
    shards_path: Path,
    batch_runs_root: Path,
    start_offset: int,
    scale: int,
    max_tokens: int,
    include_dry_run_intervals: bool,
    fleet_lanes: list[dict[str, Any]] | None = None,
    active_intervals: list[tuple[int, int]] | None = None,
) -> dict[str, Any]:
    if scale <= 0:
        raise AssertionError("scale must be positive")
    if max_tokens <= 0:
        raise AssertionError("max_tokens must be positive")
    shards = _read_jsonl(shards_path)
    ledger_intervals = _ledger_intervals(
        run_date=run_date,
        target_profile=target_profile,
        batch_runs_root=batch_runs_root,
        include_dry_run=include_dry_run_intervals,
    )
    live_active_intervals = (
        _active_process_intervals(run_date=run_date, target_profile=target_profile)
        if active_intervals is None
        else list(active_intervals)
    )
    intervals = ledger_intervals + live_active_intervals
    lanes = [dict(row) for row in (fleet_lanes or list(PRIMITIVE_FACTORY_PROVIDER_FLEET_LANES))]
    planned: list[dict[str, Any]] = []

    for lane in lanes:
        batch_size = int(lane["batch_size"]) * scale
        start = _next_free_start(
            intervals,
            desired_start=start_offset,
            length=batch_size * int(lane["max_batches"]),
            available_shards=len(shards),
        )
        end = start + batch_size * int(lane["max_batches"])
        intervals.append((start, end))
        planned.append({
            "lane_id": lane["lane_id"],
            "role": lane["role"],
            "provider": lane["provider"],
            "model": lane["model"],
            "mode": lane["mode"],
            "workers": lane["workers"],
            "batch_size": batch_size,
            "max_batches": lane["max_batches"],
            "start_offset": start,
            "end_offset_exclusive": end,
            "planned_shards": end - start,
            "max_tokens": max_tokens,
            "timeout": lane["timeout"],
            "live_command": _batch_command(
                run_date=run_date,
                target_profile=target_profile,
                shards_path=shards_path,
                lane=lane,
                start_offset=start,
                batch_size=batch_size,
                max_tokens=max_tokens,
                dry_run=False,
            ),
            "dry_run_command": _batch_command(
                run_date=run_date,
                target_profile=target_profile,
                shards_path=shards_path,
                lane=lane,
                start_offset=start,
                batch_size=batch_size,
                max_tokens=max_tokens,
                dry_run=True,
            ),
            "candidate": True,
            "serves_truth": False,
        })

    return {
        "record_type": "primitive_factory_provider_fleet_plan",
        "run_date": run_date,
        "target_profile": target_profile,
        "shards_path": _rel(shards_path),
        "available_shards": len(shards),
        "existing_used_intervals": [
            {"start_offset": start, "end_offset_exclusive": end}
            for start, end in _merge_intervals(ledger_intervals)
        ],
        "active_reserved_intervals": [
            {"start_offset": start, "end_offset_exclusive": end}
            for start, end in _merge_intervals(live_active_intervals)
        ],
        "scale": scale,
        "max_tokens": max_tokens,
        "token_policy": "high_ceiling; small caps are for explicit smoke tests only",
        "planner": "codex_orchestrator",
        "lanes": planned,
        "candidate": True,
        "serves_truth": False,
        "created_at": _now_utc(),
    }


def write_plan(plan: dict[str, Any], out_dir: Path) -> dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = _safe_name(str(plan["target_profile"]))
    plan_path = out_dir / f"{profile}_provider_fleet_plan.json"
    commands_path = out_dir / f"{profile}_provider_fleet_commands.sh"
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "",
        "# Candidate-only primitive factory commands. Review before running live.",
    ]
    for lane in plan["lanes"]:
        lines += ["", f"# {lane['lane_id']} - {lane['role']}", lane["live_command"]]
    commands_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _write_json(plan_path, plan)
    return {
        "plan_path": _rel(plan_path),
        "commands_path": _rel(commands_path),
    }


def _self_test() -> int:
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        shards_path = root / "shards.jsonl"
        shards_path.write_text(
            "".join(json.dumps({"shard_id": f"s{index}", "candidate": True, "serves_truth": False}) + "\n" for index in range(30)),
            encoding="utf-8",
        )
        ledger = root / "batches" / "2026-07-01" / "20k_test" / "batch_ledger.jsonl"
        ledger.parent.mkdir(parents=True)
        ledger.write_text(
            json.dumps({"target_profile": "20k", "offset": 0, "limit": 5, "dry_run": False}) + "\n"
            + json.dumps({"target_profile": "20k", "offset": 10, "limit": 2, "dry_run": False}) + "\n",
            encoding="utf-8",
        )
        ps_text = (
            "123 00:10 python3 scripts/run_primitive_factory_batch_loop.py "
            "--date 2026-07-01 --target-profile 20k --provider ollama --mode direct "
            "--model glm-5.2 --start-offset 8 --batch-size 2 --max-batches 1\n"
        )
        active_rows = _active_batch_process_rows(ps_text, run_date="2026-07-01", target_profile="20k")
        lanes = [
            {
                "lane_id": "a",
                "role": "candidate_writer",
                "provider": "openwebui",
                "model": "gemma-4-coding",
                "mode": "cdp",
                "workers": 1,
                "batch_size": 3,
                "max_batches": 1,
                "timeout": 30,
            },
            {
                "lane_id": "b",
                "role": "reviewer",
                "provider": "ollama",
                "model": "glm-5.2",
                "mode": "direct",
                "workers": 1,
                "batch_size": 2,
                "max_batches": 1,
                "timeout": 30,
            },
        ]
        plan = build_plan(
            run_date="2026-07-01",
            target_profile="20k",
            shards_path=shards_path,
            batch_runs_root=root / "batches",
            start_offset=0,
            scale=1,
            max_tokens=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
            include_dry_run_intervals=False,
            fleet_lanes=lanes,
            active_intervals=[],
        )
        active_gap_start = _next_free_start(
            [(0, 5), (8, 10), (10, 12)],
            desired_start=0,
            length=3,
            available_shards=30,
        )
        ok = (
            plan["lanes"][0]["start_offset"] == 5
            and plan["lanes"][1]["start_offset"] == 8
            and active_gap_start == 5
            and plan["max_tokens"] == LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS
            and plan["candidate"] is True
            and plan["serves_truth"] is False
            and active_rows
            and active_rows[0]["start_offset"] == 8
            and active_rows[0]["end_offset_exclusive"] == 10
        )
    print("PASS - primitive provider fleet planner allocates disjoint candidate-only windows." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", default=_today_utc())
    parser.add_argument("--target-profile", choices=["5k", "20k"], default=DEFAULT_TARGET_PROFILE)
    parser.add_argument("--shards", default="")
    parser.add_argument("--batch-runs-root", default="")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--start-offset", type=int, default=0)
    parser.add_argument("--scale", type=int, default=DEFAULT_SCALE)
    parser.add_argument("--max-tokens", type=int, default=LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS)
    parser.add_argument("--include-dry-run-intervals", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return _self_test()

    shards_path = Path(args.shards) if args.shards else _default_shards_path(args.date, args.target_profile)
    if not shards_path.is_absolute():
        shards_path = _resource(shards_path)
    batch_runs_root = Path(args.batch_runs_root) if args.batch_runs_root else _batch_root()
    if not batch_runs_root.is_absolute():
        batch_runs_root = _resource(batch_runs_root)
    out_dir = Path(args.out_dir) if args.out_dir else _fleet_root() / args.date
    if not out_dir.is_absolute():
        out_dir = _resource(out_dir)

    try:
        plan = build_plan(
            run_date=args.date,
            target_profile=args.target_profile,
            shards_path=shards_path,
            batch_runs_root=batch_runs_root,
            start_offset=args.start_offset,
            scale=args.scale,
            max_tokens=args.max_tokens,
            include_dry_run_intervals=args.include_dry_run_intervals,
        )
        paths = {} if args.check_only else write_plan(plan, out_dir)
    except AssertionError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(json.dumps({**plan, **paths}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
