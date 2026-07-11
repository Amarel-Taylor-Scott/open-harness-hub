#!/usr/bin/env python3
"""Launch the primitive 2M goal supervisor as a user systemd service."""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = _resource("data") / "dev-intel" / "primitive_factory" / "2m_goal"
LOG_FILE = STATE_DIR / "primitive-2m-goal.log"
UNIT = "aidevobserver-primitive-2m-goal"
RUNNER = "scripts/run_primitive_2m_goal_loop.py"


def _python() -> str:
    return sys.executable or str(REPO / ".venv" / "bin" / "python3")


def _show_main_pid() -> int | None:
    proc = subprocess.run(
        ["systemctl", "--user", "show", UNIT, "--property=MainPID", "--value"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    value = proc.stdout.strip()
    if proc.returncode != 0 or not value or value == "0":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _active() -> bool:
    proc = subprocess.run(
        ["systemctl", "--user", "is-active", "--quiet", UNIT],
        cwd=REPO,
        check=False,
    )
    return proc.returncode == 0


def start(args: argparse.Namespace) -> int:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    if _active() and not args.replace:
        print(f"already running unit={UNIT}.service pid={_show_main_pid()} log={LOG_FILE.relative_to(REPO)}")
        return 0
    if args.replace:
        subprocess.run(["systemctl", "--user", "stop", UNIT], check=False)
    command = [
        _python(),
        RUNNER,
        "--target-verified",
        str(args.target_verified),
        "--date-prefix",
        args.date_prefix,
        "--interval-seconds",
        str(args.interval_seconds),
        "--max-ticks",
        "0",
        "--min-remaining-shards",
        str(args.min_remaining_shards),
    ]
    command.append("--continue-after-target" if args.continue_after_target else "--no-continue-after-target")
    command.append("--honor-stop-file" if args.honor_stop_file else "--no-honor-stop-file")
    if not args.enable_source_foundry:
        command.append("--no-enable-source-foundry")
    if args.source_every_tick:
        command.append("--source-every-tick")
    if args.gemma_recover_every_tick:
        command.append("--gemma-recover-every-tick")
    shell_cmd = " ".join(command) + f" >> {LOG_FILE} 2>&1"
    proc = subprocess.run(
        [
            "systemd-run",
            "--user",
            f"--unit={UNIT}",
            f"--working-directory={REPO}",
            "/bin/bash",
            "-lc",
            f"mkdir -p {STATE_DIR}; exec {shell_cmd}",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        return proc.returncode or 1
    for _ in range(20):
        pid = _show_main_pid()
        if pid:
            print(f"started unit={UNIT}.service pid={pid} log={LOG_FILE.relative_to(REPO)}")
            return 0
        time.sleep(0.25)
    print(f"started unit={UNIT}.service log={LOG_FILE.relative_to(REPO)}")
    return 0


def status() -> int:
    proc = subprocess.run(
        ["systemctl", "--user", "--no-pager", "status", f"{UNIT}.service"],
        cwd=REPO,
        text=True,
        check=False,
    )
    return proc.returncode


def stop() -> int:
    proc = subprocess.run(["systemctl", "--user", "stop", UNIT], cwd=REPO, check=False)
    return proc.returncode


def _self_test() -> int:
    ok = UNIT == "aidevobserver-primitive-2m-goal" and RUNNER.endswith("run_primitive_2m_goal_loop.py")
    print("PASS - primitive 2M goal launcher is wired." if ok else "FAIL")
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", nargs="?", choices=["start", "status", "stop"], default="start")
    parser.add_argument("--target-verified", type=int, default=2_000_000)
    parser.add_argument("--date-prefix", default="2026-07-01")
    parser.add_argument("--interval-seconds", type=float, default=120.0)
    parser.add_argument("--min-remaining-shards", type=int, default=75)
    parser.add_argument("--replace", action="store_true")
    parser.add_argument("--continue-after-target", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--honor-stop-file", action=argparse.BooleanOptionalAction, default=False)
    parser.add_argument("--enable-source-foundry", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--source-every-tick", action="store_true")
    parser.add_argument("--gemma-recover-every-tick", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.action == "status":
        return status()
    if args.action == "stop":
        return stop()
    return start(args)


if __name__ == "__main__":
    raise SystemExit(main())
