"""check_registry_search — proof for federated registry search (_repos/teleon/backend/src/teleon/registry/search.py).

Proves a DAG-builder can search ALL registries at once and do the three core jobs: BUILD / TROUBLESHOOT /
IMPROVE a capability. Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry.search import py_function_src_teleon_registry_search__build_capability, py_function_src_teleon_registry_search__improve, py_function_src_teleon_registry_search__search_all, py_function_src_teleon_registry_search__troubleshoot  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [{'ok' if ok else 'XX'}] {name}{(' — ' + detail) if detail else ''}")

    # federated search: one query hits multiple registries, each hit tagged with its registry
    hits = py_function_src_teleon_registry_search__search_all("weather")
    ck("federated search returns registry-tagged hits", len(hits) >= 1 and all("registry" in h for h in hits))
    ck("weather surfaces the weather portal", any("Weather" in h["name"] for h in hits), str(hits[:3]))

    # BUILD: ingredients grouped by registry
    b = py_function_src_teleon_registry_search__build_capability("address")
    ck("build groups ingredients by registry", isinstance(b["ingredients_by_registry"], dict) and b["ingredients_by_registry"])
    ck("build is a candidate DAG (governed)", b["candidate_dag"] is True and b["serves_truth"] is False)

    # TROUBLESHOOT: diagnostic registries; on-menu queried, off-menu honestly surfaced
    t = py_function_src_teleon_registry_search__troubleshoot("cve")
    ck("troubleshoot queries vulnerability_sources", "vulnerability_sources" in t["found"], str(list(t["found"])))
    ck("troubleshoot surfaces off-menu diagnostic registries", "failure_recovery" in t["relevant_not_yet_on_menu"])

    # IMPROVE: improvement registries surfaced (mostly off-menu today, honestly)
    im = py_function_src_teleon_registry_search__improve("extraction")
    ck("improve surfaces off-menu improvement registries", "equivalence" in im["relevant_not_yet_on_menu"])
    ck("improve is governed", im["serves_truth"] is False)

    if fails:
        print(f"\nFAIL - check_registry_search: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_registry_search: federated search across registries powers BUILD / TROUBLESHOOT / "
          f"IMPROVE; on-menu registries queried, off-menu honestly surfaced; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
