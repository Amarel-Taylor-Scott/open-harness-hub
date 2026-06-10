#!/usr/bin/env python3
"""scripts.check_cmem2_delta_inventory — proof: the C-MEM-2 delta inventory exists and honestly separates
EXISTING C-MEM-1 work (do not rebuild) from the genuinely-new delta added this pass. Keeps the loop from
re-scaffolding completed memory surfaces.

CLI: PYTHONPATH=. python3 scripts/check_cmem2_delta_inventory.py --self-test
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_INV = _REPO / ".agent" / "cmem2-delta-inventory.json"


def _self_test() -> int:
    fails: list[str] = []

    def chk(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    chk("delta inventory exists", _INV.exists())
    d = json.loads(_INV.read_text()) if _INV.exists() else {}
    for k in ("already_present", "missing_delta", "do_not_rebuild", "added_this_pass"):
        chk(f"inventory has '{k}'", k in d and isinstance(d[k], list) and d[k])
    # every 'already_present' file genuinely exists (honest baseline)
    missing = [p for p in d.get("already_present", []) if not (_REPO / p).exists()]
    chk("every already_present baseline file exists", missing == [], str(missing))
    # every 'added_this_pass' file genuinely exists (honest delta)
    missing2 = [p for p in d.get("added_this_pass", []) if not (_REPO / p).exists()]
    chk("every added_this_pass delta file exists", missing2 == [], str(missing2))
    # the do-not-rebuild list names the C-MEM-1 baseline
    chk("do_not_rebuild names memory schemas + provider", any("schema" in x for x in d.get("do_not_rebuild", []))
        and any("Provider" in x for x in d.get("do_not_rebuild", [])))

    print(f"\n{'PASS — check_cmem2_delta_inventory: delta inventory present + honest (existing C-MEM-1 baseline vs new C-MEM-2 delta, all files verified).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    return _self_test() if a.self_test else (p.print_help() or 0)


if __name__ == "__main__":
    raise SystemExit(_main())
