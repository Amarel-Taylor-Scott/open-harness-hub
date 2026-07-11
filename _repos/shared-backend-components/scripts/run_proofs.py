#!/usr/bin/env python3
"""run_proofs — the HONEST proof-suite gate: actually RUN every registered proof's --self-test and exit non-zero on any red.

`flywheel_proof_modules.py` is only the registry (importing it is a no-op); THIS runs them. Concurrent (RUN_PROOFS_WORKERS,
default ~cpu). Prints PASS n/total + the RED list; exit code = number of failures (0 = all green). Use this — not
`python flywheel_proof_modules.py` — to verify the suite.

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_proofs.py            # run all
  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_proofs.py <substr>   # only proofs whose label/path contains <substr>
"""
from __future__ import annotations

import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(REPO) not in sys.path:                       # self-bootstrap: work regardless of CWD/PYTHONPATH (a gate must not
    sys.path.insert(0, str(REPO))                   # silently false-RED just because the caller forgot PYTHONPATH=.)
from scripts.flywheel_proof_modules import PROOF_MODULES  # noqa: E402
from scripts._repo_paths import pythonpath as _pythonpath, resource as _resource  # noqa: E402

_TIMEOUT = int(os.environ.get("RUN_PROOFS_TIMEOUT", "150"))
_WORKERS = int(os.environ.get("RUN_PROOFS_WORKERS", str(min(16, (os.cpu_count() or 4)))))
# repo root + every _repos/*/backend, so a proof that imports a MOVED package (src.<x> now under
# _repos/<x>/backend) still resolves it — single source: _repos/shared-backend-components/scripts/_repo_paths.py.
_PYTHONPATH = _pythonpath(".")


def _run_one(item: tuple) -> tuple:
    path, label = item
    # PROOF_MODULES stores location-stable root-relative paths (e.g. "scripts/check_x.py"); resolve to the REAL
    # on-disk location after the _repos/ migration (scripts/experiments/... are mapped in _moved_dirs.json) so the
    # runner finds the file whether it sits at root or under _repos/<owner>/. Absolute paths pass through untouched.
    real = path if os.path.isabs(path) else str(_resource(path))
    try:
        r = subprocess.run([sys.executable, real, "--self-test"], cwd=str(REPO), capture_output=True, text=True,
                           timeout=_TIMEOUT, env={**os.environ, "PYTHONPATH": _PYTHONPATH})
        ok = r.returncode == 0
        tail = (r.stdout or r.stderr or "").strip().splitlines()[-1:] or [""]
        return label, ok, tail[0][:120]
    except Exception as e:  # noqa: BLE001
        return label, False, f"{type(e).__name__}: {str(e)[:80]}"


def main(filt: str | None = None) -> int:
    items = [(p, l) for p, l in PROOF_MODULES if not filt or filt in p or filt in l]
    results = []
    with ThreadPoolExecutor(max_workers=_WORKERS) as ex:
        for label, ok, detail in ex.map(_run_one, items):
            results.append((label, ok, detail))
            if not ok:
                print(f"  RED  {label}: {detail}")
    red = [r for r in results if not r[1]]
    print(f"\nproofs: {len(results) - len(red)}/{len(results)} green" + (f" — {len(red)} RED" if red else " — ALL GREEN"))
    return len(red)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else None))
