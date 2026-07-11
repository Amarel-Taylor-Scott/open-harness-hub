#!/usr/bin/env python3
"""scripts.check_flywheel_subprocess_pythonpath — PROOF: the flywheel runs every proof subprocess with the
repo root on PYTHONPATH, so proofs that `import scripts.*`/`src.*` succeed even when the watchdog was launched
BARE (no `PYTHONPATH=.`). Guards the 2026-06-06 false-RED: the watchdog relaunched without PYTHONPATH reported
RED 164/305 purely because a fresh subprocess does not inherit the parent's sys.path insertion — only the
PYTHONPATH env var. The flywheel knows _REPO_ROOT and must inject it (see baltor_flywheel._proof_env).

Deterministic + offline: simulates a bare launch by removing PYTHONPATH for the duration, then runs an import
probe through the flywheel's own `_run`. Exit 0/1.
"""
from __future__ import annotations

import os
import sys

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from scripts import baltor_flywheel as fw


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # _proof_env always puts the repo root first on PYTHONPATH
    env = fw._proof_env()
    check("_proof_env puts repo root first on PYTHONPATH",
          env.get("PYTHONPATH", "").split(os.pathsep)[0] == fw._REPO_ROOT, env.get("PYTHONPATH", ""))

    # Simulate a BARE watchdog launch (no ambient PYTHONPATH) and run an import probe through `_run`.
    saved = os.environ.pop("PYTHONPATH", None)
    try:
        ok, last = fw._run(["-c", "import scripts.flywheel_proof_modules, "
                                  "src.baltor.workers.supervisor_store; print('IMPORTS_OK')"], 30)
        check("a src/scripts import probe SUCCEEDS via flywheel._run with no ambient PYTHONPATH",
              ok and "IMPORTS_OK" in last, f"ok={ok} last={last!r}")
        # And a representative real proof that imports scripts.* at top level passes the same way.
        ok2, last2 = fw._run(["scripts/check_artifact_type_registry.py", "--self-test"], 60)
        check("a real scripts-importing proof passes via _run with no ambient PYTHONPATH",
              ok2, f"ok={ok2} last={last2[:80]!r}")
    finally:
        if saved is not None:
            os.environ["PYTHONPATH"] = saved

    print("\n" + ("PASS — check_flywheel_subprocess_pythonpath: the flywheel injects the repo root into proof "
                  "subprocesses' PYTHONPATH; a bare-launched watchdog stays accurate (no false-RED from "
                  "missing PYTHONPATH)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_flywheel_subprocess_pythonpath.py --self-test")
    raise SystemExit(0)
