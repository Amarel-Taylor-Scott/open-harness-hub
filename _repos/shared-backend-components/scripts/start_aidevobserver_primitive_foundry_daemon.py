#!/usr/bin/env python3
"""Launch the AIDevObserver primitive-foundry daemon as a detached process."""
from __future__ import annotations

# ── substrate-root bootstrap (sentinel; mirrors scripts/capability_retrieval_mcp_server.py) ──────────────────
# Resolve the SUBSTRATE root (the dir that holds the `scripts` package) via the scripts/_repo_paths.py sentinel —
# NOT `.aidoneright-root`, which sits at the MONOREPO root (no `scripts/` package) and breaks `from scripts.*`/
# `from src.*` on a bare `python3 _repos/shared-backend-components/scripts/<f>.py` launch. install() then
# prepends every code root (repo root + each _repos/*/backend + shared-backend-components) so both resolve.
import sys
from pathlib import Path
_sbc = next((_p for _p in Path(__file__).resolve().parents if (_p / "scripts" / "_repo_paths.py").exists()), Path(__file__).resolve().parents[1])
if str(_sbc) not in sys.path:
    sys.path.insert(0, str(_sbc))
from scripts._repo_paths import install as _install  # noqa: E402
_install()
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STATE_DIR = _resource(".agent") / "aidevobserver"
PID_FILE = STATE_DIR / "primitive-foundry-daemon.pid"
LOG_FILE = STATE_DIR / "primitive-foundry-daemon.log"
SYSTEMD_UNIT = "aidevobserver-primitive-foundry"
DAEMON_SCRIPT = "scripts/aidevobserver_primitive_foundry_daemon.py"


def _pid_is_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_pid() -> int | None:
    try:
        value = PID_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _pid_cmdline(pid: int) -> list[str]:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return []
    return [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]


def _is_daemon_pid(pid: int) -> bool:
    cmdline = _pid_cmdline(pid)
    return any(part.endswith(DAEMON_SCRIPT) or part == DAEMON_SCRIPT for part in cmdline)


def _discover_daemon_pid() -> int | None:
    proc_root = Path("/proc")
    matches: list[int] = []
    try:
        entries = list(proc_root.iterdir())
    except OSError:
        entries = []
    for entry in entries:
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        if _pid_is_running(pid) and _is_daemon_pid(pid):
            matches.append(pid)
    ps_match = _discover_daemon_pid_with_ps()
    if ps_match:
        matches.append(ps_match)
    return max(matches) if matches else None


def _discover_daemon_pid_with_ps() -> int | None:
    proc = subprocess.run(
        ["ps", "-eo", "pid=", "-o", "args="],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    matches: list[int] = []
    for line in proc.stdout.splitlines():
        stripped = line.strip()
        if not stripped or DAEMON_SCRIPT not in stripped:
            continue
        pid_text, _, args = stripped.partition(" ")
        try:
            pid = int(pid_text)
        except ValueError:
            continue
        if pid == os.getpid() or "start_aidevobserver_primitive_foundry_daemon.py" in args:
            continue
        matches.append(pid)
    return max(matches) if matches else None


def _active_daemon_pid() -> int | None:
    pid = _read_pid()
    if pid and _pid_is_running(pid) and _is_daemon_pid(pid):
        return pid
    discovered = _discover_daemon_pid()
    if discovered:
        PID_FILE.write_text(f"{discovered}\n", encoding="utf-8")
    return discovered


def _daemon_cmd(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        DAEMON_SCRIPT,
        "--watch",
        "--interval",
        str(args.interval),
        "--max-ticks",
        str(args.max_ticks),
        "--search-scope-limit",
        str(args.search_scope_limit),
    ]
    if args.skip_multilingual_search_scopes:
        cmd.append("--skip-multilingual-search-scopes")
    if args.live_github:
        cmd.append("--live-github")
    if args.live_kaggle:
        cmd.append("--live-kaggle")
    if args.live_rss_feeds:
        cmd.append("--live-rss-feeds")
    if args.live_markdown_indexes:
        cmd.append("--live-markdown-indexes")
    if args.include_local_claude:
        cmd.append("--include-local-claude")
    if args.derive_local_reviews:
        cmd.append("--derive-local-reviews")
    if args.skip_observer_self_test:
        cmd.append("--skip-observer-self-test")
    return cmd


def _systemd_main_pid() -> int | None:
    proc = subprocess.run(
        ["systemctl", "--user", "show", SYSTEMD_UNIT, "--property=MainPID", "--value"],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        return None
    value = proc.stdout.strip()
    if not value or value == "0":
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _systemd_is_usable() -> bool:
    proc = subprocess.run(
        ["systemctl", "--user", "show-environment"],
        text=True,
        capture_output=True,
        check=False,
    )
    return proc.returncode == 0


def _start_with_systemd(args: argparse.Namespace) -> int:
    if not _systemd_is_usable():
        return 1
    existing = _systemd_main_pid()
    if existing and _pid_is_running(existing):
        if not args.replace:
            PID_FILE.write_text(f"{existing}\n", encoding="utf-8")
            print(f"already running pid={existing} unit={SYSTEMD_UNIT}.service log={LOG_FILE}")
            return 0
        subprocess.run(["systemctl", "--user", "stop", SYSTEMD_UNIT], check=False)

    shell_cmd = " ".join(_daemon_cmd(args)) + f" >> {LOG_FILE} 2>&1"
    proc = subprocess.run(
        [
            "systemd-run",
            "--user",
            f"--unit={SYSTEMD_UNIT}",
            "--collect",
            f"--working-directory={REPO}",
            "/bin/bash",
            "-lc",
            f"mkdir -p {STATE_DIR}; exec {shell_cmd}",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout)
        return proc.returncode or 1

    main_pid: int | None = None
    for _ in range(20):
        main_pid = _systemd_main_pid()
        if main_pid:
            break
        time.sleep(0.25)
    if not main_pid:
        sys.stderr.write("systemd unit started, but MainPID was not available.\n")
        return 1
    PID_FILE.write_text(f"{main_pid}\n", encoding="utf-8")
    print(f"started pid={main_pid} unit={SYSTEMD_UNIT}.service log={LOG_FILE}")
    return 0


def _start_with_process(args: argparse.Namespace) -> int:
    old_pid = _active_daemon_pid()
    if old_pid and _pid_is_running(old_pid) and _is_daemon_pid(old_pid):
        if not args.replace:
            print(f"already running pid={old_pid} log={LOG_FILE}")
            return 0
        os.kill(old_pid, signal.SIGTERM)

    log_handle = LOG_FILE.open("ab")
    proc = subprocess.Popen(
        _daemon_cmd(args),
        cwd=REPO,
        stdin=subprocess.DEVNULL,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    time.sleep(0.5)
    discovered = _discover_daemon_pid()
    if discovered:
        PID_FILE.write_text(f"{discovered}\n", encoding="utf-8")
        print(f"started pid={discovered} log={LOG_FILE}")
    elif _is_daemon_pid(proc.pid):
        PID_FILE.write_text(f"{proc.pid}\n", encoding="utf-8")
        print(f"started pid={proc.pid} log={LOG_FILE}")
    else:
        PID_FILE.write_text("", encoding="utf-8")
        print(f"started pid=unverified log={LOG_FILE}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Start the persistent primitive-foundry daemon.")
    parser.add_argument("--interval", type=int, default=3600)
    parser.add_argument("--max-ticks", type=int, default=0)
    parser.add_argument("--search-scope-limit", type=int, default=0)
    parser.add_argument("--skip-multilingual-search-scopes", action="store_true")
    parser.add_argument("--live-github", action="store_true")
    parser.add_argument("--live-kaggle", action="store_true")
    parser.add_argument("--live-rss-feeds", action="store_true")
    parser.add_argument("--live-markdown-indexes", action="store_true")
    parser.add_argument("--include-local-claude", action="store_true")
    parser.add_argument("--derive-local-reviews", action="store_true")
    parser.add_argument("--skip-observer-self-test", action="store_true")
    parser.add_argument("--replace", action="store_true", help="Terminate an existing daemon PID before starting.")
    parser.add_argument(
        "--method",
        choices=("auto", "systemd", "process"),
        default="auto",
        help="systemd is most durable in Codex; process is useful in ordinary shells.",
    )
    args = parser.parse_args(argv)

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    use_systemd = args.method == "systemd" or (args.method == "auto" and shutil.which("systemd-run"))
    if use_systemd:
        status = _start_with_systemd(args)
        if status == 0 or args.method == "systemd":
            return status
    return _start_with_process(args)


if __name__ == "__main__":
    raise SystemExit(main())
