#!/usr/bin/env python3
"""check_arch_flex — flexibility fixes from the loop's backlog: single-sourced tenant id + registry-driven search.

Two concrete loop proposals, implemented + locked: (1) the internal tenant id is single-sourced (no scattered literal
that drifts); (2) the grounded-search provider is SELECTED from _repos/shared-backend-components/architecture/search_provider_registry.json, not a
hardcoded 'wikipedia' default — a new active wired provider is auto-selectable. serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_arch_flex.py --self-test
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])


def _self_test() -> int:
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # (1) tenant id single-sourced
    from src.teleon.runtime.tenancy import py_const_src_teleon_runtime_tenancy__INTERNAL_TENANT_ID
    ck("INTERNAL_TENANT_ID is the one definition", py_const_src_teleon_runtime_tenancy__INTERNAL_TENANT_ID == "baltor-internal")
    out = subprocess.run(["grep", "-rl", '"baltor-internal"', "_repos/teleon/backend/src/teleon", "scripts", "--include=*.py"],
                         cwd=REPO, capture_output=True, text=True).stdout.strip().splitlines()
    leaked = [f for f in out if not f.endswith(("tenancy.py", "check_arch_flex.py"))]  # the constant def + this checker
    ck("no scattered hardcoded literal (only tenancy.py defines it)", not leaked, str(leaked))

    # (2) search provider registry-driven (not hardcoded)
    from src.teleon.dag.real_steps import _WIRED_SEARCH, _active_search_providers, default_search_provider, real_search
    dft = default_search_provider()
    active_ids = {p["provider_id"] for p in _active_search_providers()}
    ck("default search provider comes FROM the registry (an active provider)", dft in active_ids, dft)
    ck("default is a WIRED provider (cheapest active)", dft in _WIRED_SEARCH)
    ck("the registry has >=2 active grounded providers (wikipedia + federal_register)", {"wikipedia", "federal_register"} <= active_ids)
    try:
        real_search("x", provider="not_a_provider", limit=1)
        ck("an unwired provider raises honestly (no silent hardcoded fallback)", False)
    except ValueError:
        ck("an unwired provider raises honestly (no silent hardcoded fallback)", True)
    # adding an active+wired provider would auto-change the default -> the selector is registry-driven, not rigid
    ck("real_search signature is provider=None (registry-selected), not provider='wikipedia'",
       "provider: str | None = None" in (REPO / "_repos/teleon/backend/src/teleon/dag/real_steps.py").read_text())

    print("\n" + ("PASS - check_arch_flex: tenant id single-sourced; grounded-search provider registry-driven (not "
                  "hardcoded). Two loop proposals closed." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
