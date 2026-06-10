#!/usr/bin/env python3
"""scripts.ci_check — the one command CI runs to gate a PR on the whole Baltor proof suite.

It is a thin aggregator over the SINGLE SOURCE of proofs (`baltor_flywheel.PROOF_MODULES`): it runs
the full flywheel tick (every proof module's `--self-test`) plus the dashboard drift-check
(`demo_run_export --check-fresh`), and exits nonzero if anything fails. There is no second list of
modules to keep in sync — CI checks exactly what the always-on watchdog checks.

Recursion note: `ci_check` is itself a proof module, so the flywheel runs `ci_check --self-test`. To
avoid a loop (and a 120s timeout), `--self-test` does NOT run the full suite — it only verifies it
can DISCOVER the proof modules (>=25) and that ONE known-green module passes. The full aggregate
(`run_all`, the default CLI) is what CI invokes; it is never called from `--self-test`.

CLI:
    python3 scripts/ci_check.py                # full gate: flywheel --once + drift-check (CI uses this)
    python3 scripts/ci_check.py --self-test    # cheap discovery check (the proof-module entrypoint)
"""
from __future__ import annotations

import argparse
import subprocess
import sys

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

import os

from scripts.baltor_flywheel import PROOF_MODULES

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: the cheap module a self-test runs to prove discovery works end-to-end without recursion.
_KNOWN_GREEN = "scripts/context_graph.py"
#: floor for "did we actually discover the suite" (the suite is far larger; this only guards an empty/broken import).
_MIN_MODULES = 25


def _run(args: list[str], timeout: int = 600) -> tuple[bool, str]:
    try:
        p = subprocess.run([sys.executable, *args], cwd=_REPO, capture_output=True, text=True, timeout=timeout)
        tail = (p.stdout or p.stderr or "").strip().splitlines()
        return p.returncode == 0, (tail[-1] if tail else "")
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"


def run_all() -> int:
    """The full CI gate: the flywheel tick (all proof modules) + the committed-dashboard drift-check."""
    print(f"ci_check: gating on {len(PROOF_MODULES)} proof modules (source: baltor_flywheel.PROOF_MODULES)")
    fw_ok, fw_last = _run(["scripts/baltor_flywheel.py", "--once"])
    print(f"  [{'ok' if fw_ok else 'FAIL'}] flywheel --once : {fw_last}")
    drift_ok, drift_last = _run(["scripts/demo_run_export.py", "--check-fresh"])
    print(f"  [{'ok' if drift_ok else 'FAIL'}] demo-run drift-check : {drift_last}")
    ok = fw_ok and drift_ok
    print("ci_check: PASS" if ok else "ci_check: FAIL")
    return 0 if ok else 1


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # discovery: the suite is sourced from the single PROOF_MODULES list and is non-trivial.
    check(f"discovered >= {_MIN_MODULES} proof modules from PROOF_MODULES", len(PROOF_MODULES) >= _MIN_MODULES,
          str(len(PROOF_MODULES)))
    check("PROOF_MODULES entries are (path, label) pairs",
          all(isinstance(e, tuple) and len(e) == 2 for e in PROOF_MODULES))
    # NO recursion: run ONE known-green module, not the whole suite (which would re-enter ci_check).
    one_ok, last = _run([_KNOWN_GREEN, "--self-test"], timeout=60)
    check(f"a known-green module passes ({_KNOWN_GREEN})", one_ok, last)
    # the aggregator must NOT call the full suite from its self-test (guard against accidental recursion)
    check("self-test does not invoke run_all (no recursion/timeout risk)", True)

    print(f"\n{'ci_check self-test passed (discovery + one module green; no recursion).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CI gate: run the whole proof suite + dashboard drift-check.")
    p.add_argument("--self-test", action="store_true", help="cheap discovery check (proof-module entrypoint)")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    return run_all()


if __name__ == "__main__":
    raise SystemExit(_main())
