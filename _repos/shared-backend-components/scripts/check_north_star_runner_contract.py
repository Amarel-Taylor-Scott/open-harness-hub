#!/usr/bin/env python3
"""scripts.check_north_star_runner_contract — proof: the DURABLE North Star runner contract is intact, so
continuation survives Claude exiting (resumable from repo state, not chat memory). Validates the North Star
prompt (forbids fake completion), the runner script (relaunch + STOP_REQUESTED + resume-state write +
soft-stop detector + safe --check), and the durable loop-state file (valid JSON, required keys).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_north_star_runner_contract.py --self-test
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
# The North Star continuous-builder prompt lives with the Baltor context after the _repos/ migration
# (it was git-deleted from _repos/dev-rules-context/prompts/). Repoint to its real home.
_PROMPT = _resource("_repos/baltor/context/baltor-north-star-continuous-builder.md")
_RUNNER = _resource("scripts/run_north_star_loop.sh")
_STATE = (_REPO / ".agent") / "north-star-loop-state.json"
_STATE_KEYS = {"north_star", "current_target", "next_command", "open_blockers", "proofs_green",
               "resume_instructions", "stop_allowed"}


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # North Star prompt — forbids fake completion, names the North Star + correctness invariant
    chk("North Star prompt exists", _PROMPT.exists())
    pt = _PROMPT.read_text() if _PROMPT.exists() else ""
    chk("prompt declares CONTINUOUS BUILD MODE / no voluntary stop", "CONTINUOUS BUILD MODE" in pt and "do not voluntarily stop" in pt.lower())
    chk("prompt forbids soft-stop ('GREEN means choose the next item')", "GREEN means" in pt)
    chk("prompt names the CFPB correctness invariant (10 business days / FAQ 30 held out)", "10 business days" in pt and "30 days" in pt)
    chk("prompt mandates the full offline demo target", "demo_offline_full_baltor.py" in pt)
    chk("prompt defines the STOP_REQUESTED escape hatch", "STOP_REQUESTED" in pt)
    chk("prompt requires durable loop state (resume from repo, not chat)", "north-star-loop-state.json" in pt)

    # Runner — durable relaunch contract
    chk("runner script exists", _RUNNER.exists())
    chk("runner is executable", _RUNNER.exists() and os.access(_RUNNER, os.X_OK))
    rt = _RUNNER.read_text() if _RUNNER.exists() else ""
    chk("runner relaunches in a loop (while true)", "while true" in rt)
    chk("runner honors STOP_REQUESTED", "STOP_REQUESTED" in rt and "STOP_FILE" in rt)
    chk("runner writes resume state on exit", "north-star-loop-state.json" in rt and "last_runner_exit_code" in rt)
    chk("runner has a soft-stop detector that relaunches", "soft-stop" in rt.lower() and "next tick" in rt)
    chk("runner bounds each cycle (timeout)", "timeout" in rt and "CYCLE_TIMEOUT" in rt)
    chk("runner has a safe --check mode (launches nothing)", "--check" in rt and "_check" in rt)

    # --check actually passes (and does NOT launch claude)
    p = subprocess.run([str(_RUNNER), "--check"], cwd=str(_REPO), capture_output=True, text=True, timeout=30)
    chk("runner --check passes (CONTRACT OK)", p.returncode == 0 and "CONTRACT OK" in p.stdout, (p.stdout + p.stderr)[-300:])

    # Durable loop state — valid + has the keys the resume contract needs
    chk("loop state file exists", _STATE.exists())
    if _STATE.exists():
        try:
            st = json.loads(_STATE.read_text())
            missing = _STATE_KEYS - set(st)
            chk("loop state has required resume keys", missing == set(), str(missing))
            chk("loop state stop_allowed is False by default", st.get("stop_allowed") is False)
        except json.JSONDecodeError as e:
            chk("loop state is valid JSON", False, str(e))

    # the startup-sequence status docs the prompt reads exist
    for d in ("current-state.md", "opportunities.md", "risks-and-gaps.md"):
        chk(f"docs/status/{d} present (startup reads it)", (_resource("docs") / "status" / d).exists())

    print(f"\n{'PASS — check_north_star_runner_contract: durable runner + North Star prompt + resume state are intact; continuation survives Claude exiting (resumable from repo state, owner stops via STOP_REQUESTED).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
