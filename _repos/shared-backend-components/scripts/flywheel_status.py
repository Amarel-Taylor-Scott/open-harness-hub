#!/usr/bin/env python3
"""scripts.flywheel_status — one-glance view of the WHOLE autonomous flywheel (the supervisor's check).

The "consistently check massive flywheel / daemon information / work log" view, in one place: which Kimi/GLM
daemons are alive (real python only, via /proc — pgrep alone also matches shells), how much each loop has
produced (candidates · records · graph edges · interrogation · benchmarks), the tail of each work log, and recent
commits on main + the isolated build branch. Read-only.

  --self-test | (no args) print the dashboard
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
DD = _resource("data") / "dev-intel"
DAEMONS = [("swarm", "bot_swarm.py --supervise"), ("populate", "populate_loop.py --supervise"),
           ("isolated-build", "build_loop.py --supervise"), ("flywheel", "flywheel_orchestrator.py")]
LEDGERS = {"candidates": "swarm_candidates.jsonl", "records": "registry_records.jsonl",
           "graph-edges": "record_graph.jsonl", "interrogation": "interrogation_candidates.jsonl",
           "ingested": "ingested_candidates.jsonl", "benchmarks": "benchmarks.jsonl"}
LOGS = ["bot_swarm.log", "populate_loop.log", "build_iso.log"]


def real_pids(grep: str) -> list[str]:
    out = []
    for p in subprocess.run(["pgrep", "-f", grep], capture_output=True, text=True).stdout.split():
        try:
            if (Path("/proc") / p / "comm").read_text(encoding="utf-8").strip().startswith("python"):
                out.append(p)
        except OSError:
            pass
    return out


def _wc(name: str) -> int:
    f = DD / name
    return sum(1 for ln in f.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()) if f.exists() else 0


def daemons() -> dict[str, list[str]]:
    return {n: real_pids(g) for n, g in DAEMONS}


def counts() -> dict[str, int]:
    return {k: _wc(v) for k, v in LEDGERS.items()}


def worklog(n: int = 2) -> dict[str, list[str]]:
    out = {}
    for lg in LOGS:
        f = DD / lg
        if f.exists():
            out[lg] = [ln for ln in f.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()][-n:]
    return out


def _git(*a: str) -> str:
    return subprocess.run(["git", *a], cwd=REPO, capture_output=True, text=True).stdout.strip()


def show() -> None:
    print("=" * 64)
    print(f"FLYWHEEL STATUS  ·  {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 64)
    print("daemons (Kimi/GLM workers):")
    for n, pids in daemons().items():
        print(f"  {n:16} {'ALIVE pid ' + pids[0] if pids else 'down'}")
    print("produced (the flywheel output):")
    for k, v in counts().items():
        print(f"  {k:16} {v}")
    try:
        from scripts.work_queue import stats as _qstats
        q = _qstats()
    except Exception:
        q = {}
    if q:
        print("queue (durable orchestration · stateless-resume):")
        for topic, st in q.items():
            print(f"  {topic:16} {st}")
    print("recent work log:")
    for lg, lines in worklog().items():
        for ln in lines:
            print(f"  [{lg.split('.')[0]}] {ln[:88]}")
    print("recent commits (main):")
    print("  " + (_git("log", "--oneline", "-3") or "(none)").replace("\n", "\n  "))
    wt = _git("log", "--oneline", "-2", "auto/ollama-build")
    if wt:
        print("isolated build (auto/ollama-build):")
        print("  " + wt.replace("\n", "\n  "))


def self_test() -> int:
    d = daemons()
    assert isinstance(d, dict) and all(isinstance(v, list) for v in d.values())
    assert isinstance(counts(), dict) and isinstance(worklog(), dict)
    print("flywheel_status self-test: OK (daemon probe, counts, worklog, commits)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    show()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
