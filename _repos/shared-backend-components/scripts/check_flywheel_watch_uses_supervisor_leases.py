#!/usr/bin/env python3
"""scripts.check_flywheel_watch_uses_supervisor_leases — proof (OPP-supervisor-scaling-live): the REAL
`baltor_flywheel.py --watch` loop wires in durable supervisor coordination. Two checks:

  (1) code: the watch loop imports supervisor_watch and calls the leader-lease coordination step;
  (2) behavior: a bounded real subprocess writes a supervisor instance + leader lease + tick + singleton
      decision into a durable DB (i.e. the watch loop genuinely uses the leases, not just imports them).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_flywheel_watch_uses_supervisor_leases.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import pythonpath as _pythonpath  # noqa: E402
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    src = (_resource("scripts/baltor_flywheel.py")).read_text()
    chk("watch loop imports supervisor_watch", "supervisor_watch" in src)
    chk("watch loop wires the SupervisorStore", "SupervisorStore" in src)
    chk("watch CLI exposes supervisor flags", "--supervisor-db" in src and "--supervisor-only" in src and "--max-ticks" in src)
    chk("watch CLI exposes leader/shard ttl", "--leader-ttl" in src and "--shard-ttl" in src)

    # behavior: run a bounded real watch subprocess and verify it persisted coordination state
    tmp = tempfile.mkdtemp(prefix="baltor-watch-uses-")
    db = os.path.join(tmp, "sup.db")
    env = {**os.environ, "PYTHONPATH": _pythonpath(".")}
    proc = subprocess.run(
        [sys.executable, str(_resource("scripts/baltor_flywheel.py")), "--supervisor-only", "--supervisor-db", db,
         "--supervisor-id", "W", "--interval", "1", "--leader-ttl", "5", "--max-ticks", "2"],
        cwd=str(_REPO), env=env, capture_output=True, text=True, timeout=60)
    chk("bounded watch subprocess exited cleanly", proc.returncode == 0, proc.stderr[-300:])

    from src.baltor.workers.supervisor_store import SupervisorStore
    s = SupervisorStore(db)
    chk("watch registered a supervisor instance", s.instance("W") is not None)
    chk("watch recorded ticks", len(s.ticks(supervisor_id="W")) >= 1, str(len(s.ticks())))
    chk("watch held leadership (singleton decision recorded)", len(s.decisions(decision_type="singleton_proof_sweep")) >= 1)
    chk("watch claimed shards (tick recorded shard ownership)", any(t["shard_ids_json"] not in ("[]", "", None) for t in s.ticks()))
    s.close()

    print(f"\n{'PASS — check_flywheel_watch_uses_supervisor_leases: --watch wires + USES durable supervisor leases (real subprocess persisted instance/leader/tick/decision).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
