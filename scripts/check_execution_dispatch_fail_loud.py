#!/usr/bin/env python3
"""scripts.check_execution_dispatch_fail_loud — PROOF: execution-dispatch routing is DERIVED from the
policy matrix (not a hardcoded backend set), and a backend with no declared local-drain executor FAILS
LOUD (an explicit unroutable_backend) instead of silently running on the function emulator.

This closes the flexibility gap the audit flagged: the selector single-sourced the BACKEND choice in
execution_backend_policy_matrix.json, but dispatch re-hardcoded _JOB_BACKENDS/_POOL_BACKENDS and routed
anything unrecognized to the function emulator (silent, wrong). Now both the routing and the fail-loud
case come from the same config. Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import inspect
import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.workers import execution_dispatch as D


def _self_test() -> int:
    fails: list[str] = []

    def ck(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    matrix = json.loads((_REPO / "architecture" / "execution_backend_policy_matrix.json").read_text())
    eq = matrix["candidate_local_equivalents"]

    # 1. routing is CONFIG-DERIVED, not a hardcoded set.
    ck("routing reads candidate_local_equivalents (config-derived)",
       "candidate_local_equivalents" in inspect.getsource(D._candidate_local_equivalents))
    ck("no hardcoded _JOB_BACKENDS/_POOL_BACKENDS sets remain in dispatch",
       not hasattr(D, "_JOB_BACKENDS") and not hasattr(D, "_POOL_BACKENDS"))

    # 2. every @candidate backend resolves to a routable local executor per the matrix (container-image
    #    emulator is intentionally NOT a durable-drain executor → unroutable is the correct answer).
    for b, equiv in eq.items():
        kind = D._executor_for_backend(b)
        if "container_image_emulator" in equiv:
            ck(f"{b} (→ {equiv}) has no durable-drain executor → unroutable (correct, fail loud)", kind is None)
        else:
            ck(f"{b} routes to a real drain executor ({equiv})", kind in ("function", "job", "pool"), str(kind))

    # 3. FAIL LOUD: an unknown backend returns unroutable_backend WITHOUT silently using the function emulator.
    r = D._route_and_drain("totally_unknown@v9", db="", capability="x")
    ck("unknown backend → unroutable_backend (fail loud; processed 0; no silent function-emulator run)",
       r["executor"] == "unroutable_backend" and r["processed"] == 0 and r.get("unroutable_backend") == "totally_unknown@v9")

    print(("PASS — " if not fails else "FAIL — ")
          + "check_execution_dispatch_fail_loud: the chosen backend's drain executor is DERIVED from "
            "execution_backend_policy_matrix (no hardcoded set); a backend with no declared local-drain executor "
            "fails loud (unroutable_backend) rather than silently running on the function emulator.")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(_self_test() if "--self-test" in sys.argv else 0)
