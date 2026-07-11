#!/usr/bin/env python3
"""scripts.check_demo_esg_pipeline_no_hang — Phase-0 guard (C-MEM-2 preflight): the ESG demo's scoped
self-test completes well under a hard timeout and cannot hang the flywheel. It runs the demo's --self-test
as a real subprocess with a bounded wall-clock limit and asserts a clean, fast completion (not a hang).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_demo_esg_pipeline_no_hang.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
_HARD_TIMEOUT_S = 20   # the scoped self-test runs in ~0.1s; anything near this is a regression/hang


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    env = {**os.environ, "PYTHONPATH": _pythonpath(".")}
    t0 = time.time()
    hung = False
    try:
        p = subprocess.run([sys.executable, str(_resource("scripts/demo_esg_pipeline.py")), "--self-test"],
                           cwd=str(_REPO), env=env, capture_output=True, text=True, timeout=_HARD_TIMEOUT_S)
        elapsed = time.time() - t0
    except subprocess.TimeoutExpired:
        hung = True
        elapsed = time.time() - t0

    chk("ESG demo self-test did NOT hang (completed within hard timeout)", not hung, f"timed out at {_HARD_TIMEOUT_S}s")
    if not hung:
        chk("ESG demo self-test exited cleanly", p.returncode == 0, (p.stderr or "")[-300:])
        chk("ESG demo self-test is bounded/fast (scoped load, no full-catalog rglob)", elapsed < 10, f"{elapsed:.1f}s")
        chk("ESG demo self-test reports PASS", "PASS —" in (p.stdout or ""))

    print(f"\n{'PASS — check_demo_esg_pipeline_no_hang: the ESG demo self-test is bounded + offline and cannot stall the flywheel (scoped one-file load + simulate).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
