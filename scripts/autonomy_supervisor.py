#!/usr/bin/env python3
"""scripts.autonomy_supervisor — keep the persistent Kimi/GLM loops ALIVE forever (self-healing).

The spine that makes the system run WITHOUT Claude Code. Owns the cheap workhorse daemons and restarts any that
die (the Doctor at the process level):
  build  = scripts/build_loop.py --supervise   (Kimi/GLM edit code, proof-gated, commit-on-green)
  swarm  = scripts/bot_swarm.py  --supervise   (Kimi/GLM discover→interrogate→enrich → candidates)
A loop is (re)started only if it is not already alive (pgrep) and no STOP flag is set — so it cleanly takes over
when a bounded run exits, and never double-starts. Children run in their own session (survive a supervisor
restart). Honors .agent/AUTONOMY_STOP_REQUESTED.

  --self-test | --status | --supervise [--interval-sec N]
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOGDIR = REPO / "data" / "dev-intel"
STOP = REPO / ".agent" / "AUTONOMY_STOP_REQUESTED"

LOOPS = [
    {"name": "build", "grep": "build_loop.py --supervise", "script": "scripts/build_loop.py",
     "cmd": [sys.executable, "scripts/build_loop.py", "--supervise"], "log": "build_loop.log"},
    {"name": "swarm", "grep": "bot_swarm.py --supervise", "script": "scripts/bot_swarm.py",
     "cmd": [sys.executable, "scripts/bot_swarm.py", "--supervise"], "log": "bot_swarm.log"},
]


def _alive(grep: str) -> list[str]:
    r = subprocess.run(["pgrep", "-f", grep], capture_output=True, text=True)
    return [p for p in r.stdout.split() if p]


def _start(loop: dict) -> None:
    LOGDIR.mkdir(parents=True, exist_ok=True)
    log = open(LOGDIR / loop["log"], "a", encoding="utf-8")           # noqa: SIM115 — child keeps the handle
    env = {**os.environ, "PYTHONPATH": str(REPO) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    subprocess.Popen(loop["cmd"], cwd=REPO, stdout=log, stderr=log, env=env, start_new_session=True)


def status() -> None:
    print("=== autonomy supervisor status ===")
    for loop in LOOPS:
        pids = _alive(loop["grep"])
        print(f"  {loop['name']:6} {'ALIVE pid ' + pids[0] if pids else 'down'}")
    print(f"  stop flag: {'SET' if STOP.exists() else 'clear'}")


def supervise(interval: int) -> int:
    print(f"autonomy: supervising {[l['name'] for l in LOOPS]} (restart-on-death, every {interval}s). "
          f"Stop: touch {STOP.relative_to(REPO)}")
    while True:
        if STOP.exists():
            print("AUTONOMY_STOP_REQUESTED — supervisor halting (set the per-loop STOP flags to stop children).")
            return 0
        for loop in LOOPS:
            if not _alive(loop["grep"]):
                print(f"[autonomy] {loop['name']} down → starting")
                _start(loop)
        time.sleep(interval)


def self_test() -> int:
    assert len(LOOPS) >= 2 and all({"name", "grep", "cmd", "log"} <= set(l) for l in LOOPS)
    for loop in LOOPS:
        assert (REPO / loop["script"]).exists(), f"child script missing: {loop['script']}"
    # _alive returns a list and does not raise (pgrep present)
    assert isinstance(_alive("a-string-that-matches-nothing-xyz"), list)
    print("autonomy_supervisor self-test: OK (loops configured, child scripts present, liveness check works)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--status" in argv:
        status(); return 0
    if "--supervise" in argv:
        interval = int(argv[argv.index("--interval-sec") + 1]) if "--interval-sec" in argv else 20
        return supervise(interval)
    print("usage: autonomy_supervisor.py --self-test | --status | --supervise [--interval-sec N]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
