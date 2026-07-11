#!/usr/bin/env python3
"""Run the primitive factory until the verified aggregate reaches a target.

This is the durable repo-level goal runner for long horizons such as
2,000,000 useful primitive candidates. It supervises generation and verification
services, refreshes daily shard epochs, and writes receipts. It never promotes
model output to truth.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import (  # noqa: E402
    LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS,
    PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE,
    PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR,
    PRIMITIVE_FACTORY_BATCH_RUNS_DIR,
    REPO_ROOT,
)
from scripts.plan_primitive_provider_fleet import (  # noqa: E402
    _active_process_intervals,
    _ledger_intervals,
    _merge_intervals,
)

DEFAULT_TARGET_VERIFIED = 2_000_000
DEFAULT_STATE_DIR = _resource("data") / "dev-intel" / "primitive_factory" / "2m_goal"
DEFAULT_STOP_FILE = _resource("data") / "dev-intel" / "primitive_factory" / "2M_STOP"
DEFAULT_RUN_LABEL_GEMMA = "gemma-recovered"
DEFAULT_RUN_LABEL_OLLAMA = "glm-kimi"
GEMMA_LANE = "gemma_openwebui_cdp_candidate_writer"
PROVIDER_LOOP = "scripts/run_primitive_provider_fleet_loop.py"
VERIFICATION_LOOP = "scripts/run_primitive_verification_loop.py"
FAILED_SHARD_RETRY_LOOP = "scripts/run_primitive_failed_shard_retry_loop.py"
SHARD_BUILDER = "scripts/build_primitive_factory_5k_shards.py"
GEMMA_PROBE = "scripts/openwebui_cdp_client.py"
GEMMA_RECOVER = "scripts/openwebui_cdp_recover.py"
LINKABLE_CARD_PACKAGER = "scripts/package_linkable_primitive_cards.py"
SOURCE_FOUNDRY_STARTER = "scripts/start_aidevobserver_primitive_foundry_daemon.py"
MANAGED_HELPER_UNIT_RE = re.compile(
    r"^aidevobserver-primitive-2m-(gemma|ollama|verify|retry)-(.+)\.service$"
)


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _today_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _rel(path: Path) -> str:
    return str(path.relative_to(REPO_ROOT) if path.is_relative_to(REPO_ROOT) else path)


def _safe_unit(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-")
    return text[:180] or "primitive-goal"


def _python() -> str:
    return sys.executable or str(REPO_ROOT / ".venv" / "bin" / "python3")


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"_read_error": "invalid_json", "_path": _rel(path)}
    return value if isinstance(value, dict) else {"_read_error": "not_object", "_path": _rel(path)}


def _parse_utc_time(value: Any) -> dt.datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _gemma_pause_status() -> dict[str, Any]:
    pause_path = _resource(PRIMITIVE_FACTORY_GEMMA_PAUSE_FILE)
    payload = _read_json(pause_path)
    if not payload or payload.get("enabled") is False:
        return {"active": False, "pause_file": _rel(pause_path)}
    expires_at = _parse_utc_time(payload.get("expires_at_utc") or payload.get("expires_at"))
    now = dt.datetime.now(dt.timezone.utc)
    if expires_at and now >= expires_at:
        return {
            "active": False,
            "expired": True,
            "expires_at_utc": expires_at.isoformat(),
            "pause_file": _rel(pause_path),
            "candidate": True,
            "serves_truth": False,
        }
    return {
        "active": True,
        "expires_at_utc": expires_at.isoformat() if expires_at else "",
        "pause_file": _rel(pause_path),
        "reason": str(payload.get("reason") or "gemma_calls_paused"),
        "candidate": True,
        "serves_truth": False,
    }


def _json_from_stdout_tail(result: dict[str, Any]) -> dict[str, Any]:
    text = str(result.get("stdout_tail") or "").strip()
    if not text:
        return {}
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def _openwebui_probe_ok(result: dict[str, Any]) -> bool:
    if result.get("returncode") != 0:
        return False
    probe = _json_from_stdout_tail(result)
    chat = probe.get("chat") if isinstance(probe.get("chat"), dict) else {}
    return bool(chat.get("ok")) and int(chat.get("status") or 0) == 200


def _openwebui_recovery_ok(result: dict[str, Any]) -> bool:
    if result.get("returncode") != 0:
        return False
    recovery = _json_from_stdout_tail(result)
    smoke = recovery.get("smoke") if isinstance(recovery.get("smoke"), dict) else {}
    return bool(smoke.get("ok"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def _run(cmd: list[str], *, timeout: int = 120) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "status": "ok" if proc.returncode == 0 else "failed",
            "seconds": round(time.time() - started, 3),
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "candidate": True,
            "serves_truth": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": None,
            "status": "timeout",
            "seconds": round(time.time() - started, 3),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "candidate": True,
            "serves_truth": False,
        }


def _aggregate_verified() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    root = _resource("data") / "dev-intel" / "primitive_factory" / "verified_candidates"
    for path in sorted(root.glob("*/manifest.json")):
        manifest = _read_json(path)
        rows.append({
            "run_date": path.parent.name,
            "manifest_path": _rel(path),
            "verified_count": int(manifest.get("verified_count") or 0),
            "source_row_count": int(manifest.get("source_row_count") or 0),
            "duplicate_count": int(manifest.get("duplicate_count") or 0),
            "rejected_count": int(manifest.get("rejected_count") or 0),
            "candidate": manifest.get("candidate") is True or not manifest,
            "serves_truth": manifest.get("serves_truth") is True,
        })
    return {
        "verified_count": sum(row["verified_count"] for row in rows),
        "source_row_count": sum(row["source_row_count"] for row in rows),
        "duplicate_count": sum(row["duplicate_count"] for row in rows),
        "rejected_count": sum(row["rejected_count"] for row in rows),
        "run_count": len(rows),
        "runs": rows,
        "candidate": True,
        "serves_truth": False,
    }


def _state_path(state_dir: Path) -> Path:
    return state_dir / "state.json"


def _load_state(state_dir: Path, *, date_prefix: str) -> dict[str, Any]:
    state = _read_json(_state_path(state_dir))
    if not state:
        state = {
            "date_prefix": date_prefix,
            "epoch": 0,
            "active_run_date": date_prefix,
            "created_at": _utc_now(),
            "candidate": True,
            "serves_truth": False,
        }
    state.setdefault("date_prefix", date_prefix)
    state.setdefault("epoch", 0)
    state.setdefault("active_run_date", _run_date_for_epoch(str(state["date_prefix"]), int(state["epoch"])))
    state["candidate"] = True
    state["serves_truth"] = False
    return state


def _save_state(state_dir: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = _utc_now()
    state["candidate"] = True
    state["serves_truth"] = False
    _write_json(_state_path(state_dir), state)


def _run_date_for_epoch(prefix: str, epoch: int) -> str:
    return prefix if epoch <= 0 else f"{prefix}-g{epoch:04d}"


def _epoch_for_run_date(prefix: str, run_date: str) -> int | None:
    if run_date == prefix:
        return 0
    match = re.fullmatch(rf"{re.escape(prefix)}-g(\d{{4}})", run_date)
    if not match:
        return None
    return int(match.group(1))


def _shards_dir(run_date: str) -> Path:
    return _resource(PRIMITIVE_FACTORY_20K_DAILY_SHARDS_DIR) / run_date


def _shards_manifest(run_date: str) -> dict[str, Any]:
    return _read_json(_shards_dir(run_date) / "manifest.json")


def _ensure_shards(run_date: str) -> dict[str, Any]:
    manifest_path = _shards_dir(run_date) / "manifest.json"
    shards_path = _shards_dir(run_date) / "shards.jsonl"
    if manifest_path.exists() and shards_path.exists():
        return {"status": "exists", "manifest": _read_json(manifest_path), "candidate": True, "serves_truth": False}
    result = _run([
        _python(),
        SHARD_BUILDER,
        "--date",
        run_date,
        "--target-profile",
        "20k",
        "--shard-useful-target",
        "25",
    ], timeout=420)
    result["manifest"] = _read_json(manifest_path)
    return result


def _used_intervals(run_date: str, *, target_profile: str = "20k") -> list[tuple[int, int]]:
    batch_runs_root = _resource(PRIMITIVE_FACTORY_BATCH_RUNS_DIR)
    intervals = _ledger_intervals(
        run_date=run_date,
        target_profile=target_profile,
        batch_runs_root=batch_runs_root,
        include_dry_run=False,
    )
    intervals += _active_process_intervals(run_date=run_date, target_profile=target_profile)
    return _merge_intervals(intervals)


def _remaining_shards(run_date: str) -> dict[str, Any]:
    manifest = _shards_manifest(run_date)
    shard_count = int(manifest.get("shard_count") or 0)
    intervals = _used_intervals(run_date)
    used = sum(max(0, end - start) for start, end in intervals)
    return {
        "run_date": run_date,
        "shard_count": shard_count,
        "used_or_active_shards": used,
        "remaining_shards": max(0, shard_count - used),
        "used_intervals": [
            {"start_offset": start, "end_offset_exclusive": end}
            for start, end in intervals
        ],
        "candidate": True,
        "serves_truth": False,
    }


def _advance_epoch_if_needed(state: dict[str, Any], *, min_remaining: int) -> dict[str, Any]:
    run_date = str(state["active_run_date"])
    remaining = _remaining_shards(run_date)
    if int(remaining.get("shard_count") or 0) and int(remaining.get("remaining_shards") or 0) >= min_remaining:
        return {"advanced": False, "state": state, "remaining": remaining, "candidate": True, "serves_truth": False}
    state = dict(state)
    state["epoch"] = int(state.get("epoch") or 0) + 1
    state["active_run_date"] = _run_date_for_epoch(str(state["date_prefix"]), int(state["epoch"]))
    return {
        "advanced": True,
        "state": state,
        "previous_remaining": remaining,
        "candidate": True,
        "serves_truth": False,
    }


def _systemctl_show(unit: str) -> dict[str, str]:
    proc = subprocess.run(
        ["systemctl", "--user", "show", unit, "--property=ActiveState", "--property=SubState", "--property=MainPID", "--value"],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
    )
    values = [line.strip() for line in proc.stdout.splitlines()]
    return {
        "active_state": values[0] if len(values) > 0 else "",
        "sub_state": values[1] if len(values) > 1 else "",
        "main_pid": values[2] if len(values) > 2 else "",
        "returncode": str(proc.returncode),
    }


def _unit_active(unit: str) -> bool:
    info = _systemctl_show(unit)
    return info.get("active_state") == "active" and info.get("sub_state") in {"running", "start"}


def _start_unit(unit: str, command: list[str]) -> dict[str, Any]:
    if _unit_active(unit):
        return {
            "unit": unit,
            "action": "already_active",
            "systemctl": _systemctl_show(unit),
            "candidate": True,
            "serves_truth": False,
        }
    result = _run([
        "systemd-run",
        "--user",
        f"--unit={unit}",
        f"--working-directory={REPO_ROOT}",
        *command,
    ], timeout=30)
    result["unit"] = unit
    result["action"] = "started" if result.get("returncode") == 0 else "start_failed"
    result["systemctl"] = _systemctl_show(unit)
    return result


def _stop_unit(unit: str) -> dict[str, Any]:
    if not _unit_active(unit):
        return {"unit": unit, "action": "not_active", "candidate": True, "serves_truth": False}
    result = _run(["systemctl", "--user", "stop", unit], timeout=30)
    result["unit"] = unit
    result["action"] = "stopped" if result.get("returncode") == 0 else "stop_failed"
    return result


def _reset_failed_unit(unit: str) -> dict[str, Any]:
    result = _run(["systemctl", "--user", "reset-failed", unit], timeout=30)
    result["unit"] = unit
    result["action"] = "reset_failed" if result.get("returncode") == 0 else "reset_failed_failed"
    return result


def _parse_list_unit_line(line: str) -> dict[str, str] | None:
    columns = line.split(None, 4)
    if len(columns) < 4 or not columns[0].endswith(".service"):
        return None
    unit = columns[0]
    if unit == "UNIT" or not unit.startswith("aidevobserver-primitive-2m-"):
        return None
    return {
        "unit": unit,
        "load": columns[1],
        "active": columns[2],
        "sub": columns[3],
        "description": columns[4] if len(columns) > 4 else "",
    }


def _list_goal_units() -> dict[str, Any]:
    started = time.time()
    cmd = [
        "systemctl",
        "--user",
        "list-units",
        "aidevobserver-primitive-2m-*",
        "--all",
        "--no-pager",
        "--plain",
    ]
    try:
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
        status = "ok" if proc.returncode == 0 else "failed"
        stdout = proc.stdout
        stderr_tail = proc.stderr[-4000:]
        returncode = proc.returncode
        seconds = round(time.time() - started, 3)
    except subprocess.TimeoutExpired as exc:
        status = "timeout"
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr_tail = exc.stderr[-4000:] if isinstance(exc.stderr, str) else ""
        returncode = None
        seconds = round(time.time() - started, 3)
    units = []
    for line in stdout.splitlines():
        unit = _parse_list_unit_line(line.strip())
        if unit:
            units.append(unit)
    return {
        "cmd": cmd,
        "status": status,
        "returncode": returncode,
        "seconds": seconds,
        "unit_count": len(units),
        "units": units,
        "stderr_tail": stderr_tail,
        "candidate": True,
        "serves_truth": False,
    }


def _prune_stale_goal_units(state: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    if not args.enable_service_janitor:
        return {"enabled": False, "candidate": True, "serves_truth": False}
    active_epoch = int(state.get("epoch") or 0)
    prefix = str(state["date_prefix"])
    keep_recent_epochs = max(1, int(args.keep_recent_epochs))
    oldest_kept_epoch = max(0, active_epoch - keep_recent_epochs + 1)
    units = _list_goal_units()
    actions: list[dict[str, Any]] = []
    stale_units: list[dict[str, Any]] = []
    inspected = 0

    for unit_info in units.get("units", []):
        unit = str(unit_info.get("unit") or "")
        match = MANAGED_HELPER_UNIT_RE.fullmatch(unit)
        if not match:
            continue
        inspected += 1
        kind, safe_run_date = match.groups()
        # Current unit names are made from date-like run ids, so safe_run_date
        # maps back directly. Keep this explicit to avoid touching other units.
        epoch = _epoch_for_run_date(prefix, safe_run_date)
        if epoch is None:
            continue
        keep = oldest_kept_epoch <= epoch <= active_epoch
        if keep:
            continue
        stale_units.append({
            "unit": unit,
            "kind": kind,
            "run_date": safe_run_date,
            "epoch": epoch,
            "active_epoch": active_epoch,
            "oldest_kept_epoch": oldest_kept_epoch,
            "unit_state": unit_info,
        })

    def stale_priority(item: dict[str, Any]) -> tuple[int, int, str]:
        unit_state = item.get("unit_state") if isinstance(item.get("unit_state"), dict) else {}
        active = unit_state.get("active")
        if active == "active":
            group = 0
        elif active == "failed":
            group = 1
        else:
            group = 2
        return (group, int(item.get("epoch") or 0), str(item.get("unit") or ""))

    for stale_unit in sorted(stale_units, key=stale_priority)[:args.janitor_max_actions]:
        unit = str(stale_unit["unit"])
        unit_state = stale_unit.get("unit_state") if isinstance(stale_unit.get("unit_state"), dict) else {}
        if unit_state.get("active") == "active":
            action = _stop_unit(unit)
        elif unit_state.get("active") == "failed":
            action = _reset_failed_unit(unit)
        else:
            action = {
                "unit": unit,
                "action": "stale_inactive_observed",
                "candidate": True,
                "serves_truth": False,
            }
        action.update(stale_unit)
        actions.append(action)

    return {
        "enabled": True,
        "active_epoch": active_epoch,
        "oldest_kept_epoch": oldest_kept_epoch,
        "keep_recent_epochs": keep_recent_epochs,
        "listed_unit_count": units.get("unit_count", 0),
        "inspected_managed_helper_count": inspected,
        "stale_managed_helper_count": len(stale_units),
        "action_count": len(actions),
        "actions": actions,
        "list_units_status": units.get("status"),
        "candidate": True,
        "serves_truth": False,
    }


def _ensure_generation_services(run_date: str, args: argparse.Namespace, *, gemma_allowed: bool) -> list[dict[str, Any]]:
    safe_date = _safe_unit(run_date)
    actions: list[dict[str, Any]] = []
    gemma_unit = f"aidevobserver-primitive-2m-gemma-{safe_date}"
    ollama_unit = f"aidevobserver-primitive-2m-ollama-{safe_date}"
    verify_unit = f"aidevobserver-primitive-2m-verify-{safe_date}"
    retry_unit = f"aidevobserver-primitive-2m-retry-{safe_date}"
    if args.enable_gemma and gemma_allowed:
        actions.append(_start_unit(gemma_unit, [
            _python(),
            PROVIDER_LOOP,
            "--date",
            run_date,
            "--target-profile",
            "20k",
            "--scale",
            str(args.gemma_scale),
            "--max-cycles",
            "0",
            "--sleep-seconds",
            str(args.gemma_sleep_seconds),
            "--only-lane",
            GEMMA_LANE,
            "--run-label",
            DEFAULT_RUN_LABEL_GEMMA,
            "--max-tokens",
            str(LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS),
        ]))
    elif args.enable_gemma:
        if _unit_active(gemma_unit):
            action = _stop_unit(gemma_unit)
            action["reason"] = "openwebui_cdp_unavailable"
            actions.append(action)
        else:
            actions.append({
                "unit": gemma_unit,
                "action": "skipped",
                "reason": "openwebui_cdp_unavailable",
                "candidate": True,
                "serves_truth": False,
            })
        for unit_info in _list_goal_units().get("units", []):
            unit = str(unit_info.get("unit") or "")
            match = MANAGED_HELPER_UNIT_RE.fullmatch(unit)
            if not match or match.group(1) != "gemma" or unit == f"{gemma_unit}.service":
                continue
            if unit_info.get("active") == "active":
                action = _stop_unit(unit)
                action["reason"] = "openwebui_cdp_unavailable"
                actions.append(action)
    if args.enable_ollama:
        actions.append(_start_unit(ollama_unit, [
            _python(),
            PROVIDER_LOOP,
            "--date",
            run_date,
            "--target-profile",
            "20k",
            "--scale",
            str(args.ollama_scale),
            "--max-cycles",
            "0",
            "--sleep-seconds",
            str(args.ollama_sleep_seconds),
            "--exclude-lane",
            GEMMA_LANE,
            "--run-label",
            DEFAULT_RUN_LABEL_OLLAMA,
            "--max-tokens",
            str(LLM_HIGH_CEILING_MAX_OUTPUT_TOKENS),
        ]))
    if args.enable_verifier:
        actions.append(_start_unit(verify_unit, [
            _python(),
            VERIFICATION_LOOP,
            "--date",
            run_date,
            "--interval-seconds",
            str(args.verify_interval_seconds),
            "--max-ticks",
            "0",
        ]))
    if args.enable_failed_retry:
        actions.append(_start_unit(retry_unit, [
            _python(),
            FAILED_SHARD_RETRY_LOOP,
            "--date",
            run_date,
            "--interval-seconds",
            str(args.failed_retry_interval_seconds),
            "--max-ticks",
            "0",
            "--max-shards",
            str(args.failed_retry_max_shards),
        ]))
    return actions


def _ensure_source_foundry(args: argparse.Namespace) -> dict[str, Any]:
    if not args.enable_source_foundry:
        return {"enabled": False, "candidate": True, "serves_truth": False}
    command = [
        _python(),
        SOURCE_FOUNDRY_STARTER,
        "--interval",
        str(args.source_interval_seconds),
        "--max-ticks",
        "0",
        "--live-github",
        "--live-kaggle",
        "--live-rss-feeds",
        "--live-markdown-indexes",
    ]
    if args.replace_source_foundry:
        command.append("--replace")
    return _run(command, timeout=120)


def _package_linkable_cards(args: argparse.Namespace) -> dict[str, Any]:
    if not args.enable_linkable_packager:
        return {"enabled": False, "candidate": True, "serves_truth": False}
    return _run([
        _python(),
        LINKABLE_CARD_PACKAGER,
        "--prefix",
        args.date_prefix,
    ], timeout=args.linkable_packager_timeout)


def _recover_gemma_if_needed(args: argparse.Namespace) -> dict[str, Any]:
    if not args.recover_gemma:
        return {"enabled": False, "candidate": True, "serves_truth": False}
    pause = _gemma_pause_status()
    if pause.get("active"):
        return {
            "enabled": True,
            "available": False,
            "recovered": False,
            "skipped_due_to_pause": True,
            "pause": pause,
            "candidate": True,
            "serves_truth": False,
        }
    probe = _run([_python(), GEMMA_PROBE, "--probe", "--timeout", str(args.gemma_probe_timeout)], timeout=args.gemma_probe_timeout + 20)
    if _openwebui_probe_ok(probe):
        return {"enabled": True, "probe": probe, "available": True, "recovered": False, "candidate": True, "serves_truth": False}
    recover = _run([
        _python(),
        GEMMA_RECOVER,
        "--wait-seconds",
        "5",
        "--challenge-wait-seconds",
        "20",
    ], timeout=180)
    available = _openwebui_recovery_ok(recover)
    return {"enabled": True, "probe": probe, "recover": recover, "available": available, "recovered": available, "candidate": True, "serves_truth": False}


def run_tick(args: argparse.Namespace, *, state: dict[str, Any], tick_index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    started = time.time()
    aggregate_before = _aggregate_verified()
    advanced = _advance_epoch_if_needed(state, min_remaining=args.min_remaining_shards)
    state = advanced["state"]
    run_date = str(state["active_run_date"])
    shard_action = _ensure_shards(run_date)
    source_action = _ensure_source_foundry(args) if tick_index == 1 or args.source_every_tick else {"enabled": args.enable_source_foundry, "skipped_this_tick": True}
    linkable_packaging = _package_linkable_cards(args)
    should_recover_gemma = (
        tick_index == 1
        or args.gemma_recover_every_tick
        or state.get("gemma_cdp_available") is False
    )
    gemma_recovery = _recover_gemma_if_needed(args) if should_recover_gemma else {"enabled": args.recover_gemma, "skipped_this_tick": True}
    if gemma_recovery.get("skipped_this_tick"):
        gemma_allowed = bool(state.get("gemma_cdp_available", True))
    else:
        gemma_allowed = bool(gemma_recovery.get("available"))
        state["gemma_cdp_available"] = gemma_allowed
        state["gemma_cdp_checked_at"] = _utc_now()
        if gemma_recovery.get("skipped_due_to_pause"):
            pause = gemma_recovery.get("pause") if isinstance(gemma_recovery.get("pause"), dict) else {}
            state["gemma_paused_until_utc"] = str(pause.get("expires_at_utc") or "")
            state["gemma_pause_reason"] = str(pause.get("reason") or "")
    service_actions = _ensure_generation_services(run_date, args, gemma_allowed=gemma_allowed)
    janitor_actions = _prune_stale_goal_units(state, args)
    aggregate_after = _aggregate_verified()
    remaining = _remaining_shards(run_date)
    target_remaining = max(0, args.target_verified - int(aggregate_after.get("verified_count") or 0))
    tick = {
        "record_type": "primitive_2m_goal_tick",
        "tick_index": tick_index,
        "run_date": run_date,
        "started_at": dt.datetime.fromtimestamp(started, tz=dt.timezone.utc).replace(microsecond=0).isoformat(),
        "finished_at": _utc_now(),
        "seconds": round(time.time() - started, 3),
        "target_verified": args.target_verified,
        "target_remaining": target_remaining,
        "aggregate_before": aggregate_before,
        "aggregate_after": aggregate_after,
        "epoch_advance": advanced,
        "shard_action": shard_action,
        "remaining_shards": remaining,
        "source_action": source_action,
        "linkable_packaging": linkable_packaging,
        "gemma_recovery": gemma_recovery,
        "gemma_generation_allowed": gemma_allowed,
        "service_actions": service_actions,
        "janitor_actions": janitor_actions,
        "stop_file": _rel(args.stop_file),
        "stop_file_present": args.stop_file.exists(),
        "honor_stop_file": args.honor_stop_file,
        "stop_file_effective": args.honor_stop_file and args.stop_file.exists(),
        "continue_after_target": args.continue_after_target,
        "target_milestone_met": target_remaining == 0,
        "candidate": True,
        "serves_truth": False,
    }
    return state, tick


def _live_manifest(args: argparse.Namespace, *, ticks: list[dict[str, Any]], loop_started: float, running: bool) -> dict[str, Any]:
    aggregate = _aggregate_verified()
    return {
        "record_type": "primitive_2m_goal_loop_manifest",
        "target_verified": args.target_verified,
        "verified_count": int(aggregate.get("verified_count") or 0),
        "target_milestone_met": int(aggregate.get("verified_count") or 0) >= args.target_verified,
        "continue_after_target": args.continue_after_target,
        "honor_stop_file": args.honor_stop_file,
        "stop_file": _rel(args.stop_file),
        "stop_file_present": args.stop_file.exists(),
        "stop_file_effective": args.honor_stop_file and args.stop_file.exists(),
        "running": running,
        "state_path": _rel(_state_path(args.state_dir)),
        "latest_status_path": _rel(args.state_dir / "latest_status.json"),
        "ledger_path": _rel(args.state_dir / "goal_ledger.jsonl"),
        "completed_ticks_this_process": len(ticks),
        "duration_seconds": round(time.time() - loop_started, 3),
        "aggregate": aggregate,
        "candidate": True,
        "serves_truth": False,
        "updated_at": _utc_now(),
    }


def run_loop(args: argparse.Namespace) -> dict[str, Any]:
    args.state_dir.mkdir(parents=True, exist_ok=True)
    state = _load_state(args.state_dir, date_prefix=args.date_prefix)
    ticks: list[dict[str, Any]] = []
    loop_started = time.time()
    tick_index = 0
    while True:
        aggregate = _aggregate_verified()
        target_met_now = int(aggregate.get("verified_count") or 0) >= args.target_verified
        if target_met_now and not args.continue_after_target:
            break
        if args.honor_stop_file and args.stop_file.exists():
            break
        if args.max_ticks and tick_index >= args.max_ticks:
            break
        tick_index += 1
        state, tick = run_tick(args, state=state, tick_index=tick_index)
        _save_state(args.state_dir, state)
        _append_jsonl(args.state_dir / "goal_ledger.jsonl", tick)
        _write_json(args.state_dir / "latest_status.json", tick)
        ticks.append(tick)
        _write_json(args.state_dir / "loop_manifest.json", _live_manifest(args, ticks=ticks, loop_started=loop_started, running=True))
        if args.once:
            break
        if args.interval_seconds > 0:
            time.sleep(args.interval_seconds)
    manifest = _live_manifest(args, ticks=ticks, loop_started=loop_started, running=False)
    manifest["created_at"] = manifest.pop("updated_at")
    manifest["target_met"] = manifest["target_milestone_met"]
    _write_json(args.state_dir / "loop_manifest.json", manifest)
    return manifest


def _self_test() -> int:
    state = {"date_prefix": "2026-07-01", "epoch": 2}
    ok = (
        _run_date_for_epoch("2026-07-01", 0) == "2026-07-01"
        and _run_date_for_epoch("2026-07-01", 7) == "2026-07-01-g0007"
        and _epoch_for_run_date("2026-07-01", "2026-07-01") == 0
        and _epoch_for_run_date("2026-07-01", "2026-07-01-g0042") == 42
        and _epoch_for_run_date("2026-07-01", "2026-07-02") is None
        and _openwebui_probe_ok({"returncode": 0, "stdout_tail": json.dumps({"chat": {"ok": True, "status": 200}})})
        and not _openwebui_probe_ok({"returncode": 0, "stdout_tail": json.dumps({"chat": {"ok": False, "status": 403}})})
        and _safe_unit("2026-07-01-g0007") == "2026-07-01-g0007"
        and _safe_unit("gemma/recovered") == "gemma-recovered"
        and _parse_list_unit_line("aidevobserver-primitive-2m-gemma-2026-07-01.service loaded active running x")["active"] == "active"  # type: ignore[index]
        and isinstance(state, dict)
    )
    print("PASS - primitive 2M goal loop helpers are deterministic and candidate-only." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-verified", type=int, default=DEFAULT_TARGET_VERIFIED)
    parser.add_argument("--date-prefix", default=_today_utc())
    parser.add_argument("--state-dir", default=str(DEFAULT_STATE_DIR))
    parser.add_argument("--stop-file", default=str(DEFAULT_STOP_FILE))
    parser.add_argument("--interval-seconds", type=float, default=120.0)
    parser.add_argument("--max-ticks", type=int, default=0, help="0 means run until target/stop.")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--continue-after-target", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--honor-stop-file", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--min-remaining-shards", type=int, default=75)
    parser.add_argument("--enable-gemma", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-ollama", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-verifier", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-failed-retry", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-source-foundry", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--enable-linkable-packager", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--replace-source-foundry", action="store_true")
    parser.add_argument("--recover-gemma", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--source-every-tick", action="store_true")
    parser.add_argument("--gemma-recover-every-tick", action="store_true")
    parser.add_argument("--gemma-scale", type=int, default=1)
    parser.add_argument("--ollama-scale", type=int, default=2)
    parser.add_argument("--gemma-sleep-seconds", type=float, default=20.0)
    parser.add_argument("--ollama-sleep-seconds", type=float, default=30.0)
    parser.add_argument("--verify-interval-seconds", type=float, default=45.0)
    parser.add_argument("--failed-retry-interval-seconds", type=float, default=900.0)
    parser.add_argument("--failed-retry-max-shards", type=int, default=24)
    parser.add_argument("--enable-service-janitor", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--keep-recent-epochs", type=int, default=4)
    parser.add_argument("--janitor-max-actions", type=int, default=80)
    parser.add_argument("--source-interval-seconds", type=int, default=3600)
    parser.add_argument("--linkable-packager-timeout", type=int, default=180)
    parser.add_argument("--gemma-probe-timeout", type=int, default=90)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.target_verified <= 0:
        print("FAIL: --target-verified must be positive", file=sys.stderr)
        return 1
    args.state_dir = Path(args.state_dir)
    args.stop_file = Path(args.stop_file)
    if not args.state_dir.is_absolute():
        args.state_dir = _resource(args.state_dir)
    if not args.stop_file.is_absolute():
        args.stop_file = _resource(args.stop_file)
    manifest = run_loop(args)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest.get("target_met") or args.once or not args.stop_file.exists() else 1


if __name__ == "__main__":
    raise SystemExit(main())
