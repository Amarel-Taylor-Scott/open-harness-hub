#!/usr/bin/env python3
"""scripts.check_experiments_isolation — guard the skunkworks boundary (experiments can't break core).

The contract (experiments/README.md): the proven core may NEVER import `experiments/`, so a broken
experiment can never turn the flywheel red or break the live demo. Experiments MAY import the core +
emit onto the event bus. This proof: (1) no module in `baltor_flywheel.PROOF_MODULES` imports
`experiments`; (2) the contract files exist; (3) the template experiment actually runs + emits onto a
bus (experiments CAN use the bus). Offline, deterministic.

CLI:
    python3 _repos/shared-backend-components/scripts/check_experiments_isolation.py --self-test
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

#: an ACTUAL import statement for `experiments` (line-anchored — so the detector doesn't match its
#: own string literals, and string mentions of "import experiments" in comments/docs don't false-flag).
_IMPORTS_EXPERIMENTS = re.compile(r"^\s*(import experiments|from experiments)\b", re.MULTILINE)

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os

    _RR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _RR not in sys.path:
        sys.path.insert(0, _RR)

from scripts.baltor_flywheel import PROOF_MODULES

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_TEMPLATE = _resource("experiments") / "_template" / "experiment.py"


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # (1) ISOLATION: no proven (flywheel-watched) module imports experiments/
    offenders = []
    for path, label in PROOF_MODULES:
        p = _resource(path)
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        if _IMPORTS_EXPERIMENTS.search(src):
            offenders.append(label)
    check("no proven module imports experiments/ (skunkworks is isolated from the flywheel)",
          not offenders, str(offenders))

    # (2) the skunkworks contract files exist
    check("experiments/README.md exists", (_resource("experiments") / "README.md").exists())
    check("experiments/_template/experiment.py exists", _TEMPLATE.exists())
    check("a seed experiment exists (masfactory_context_swarm)",
          (_resource("experiments") / "masfactory_context_swarm" / "run.py").exists())

    # (3) the template experiment runs + emits onto the bus (experiments CAN use the core + bus)
    ok_run = False
    detail = ""
    try:
        out = subprocess.run([sys.executable, str(_TEMPLATE)], cwd=str(_REPO),
                             capture_output=True, text=True, timeout=30)
        ok_run = out.returncode == 0 and "component.started" in out.stdout
        detail = (out.stdout or out.stderr or "").strip()[-160:]
    except Exception as e:  # noqa: BLE001
        detail = f"{type(e).__name__}: {e}"
    check("template experiment runs + emits component.started onto a bus", ok_run, detail)

    print(f"\n{'all check_experiments_isolation self-tests passed (core never imports experiments/; contract files present; template emits onto the bus).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guard the skunkworks/experiments isolation boundary.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
