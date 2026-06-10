#!/usr/bin/env python3
"""scripts.check_memory_tenant_project_scoping — proof (NO CROSS-TENANT MEMORY LEAKAGE): every MemoryArtifact
carries tenant_id + project/container scope, and a search in tenant A NEVER returns tenant B's artifacts.

Negative-tested across the working providers (local + emulator): write into tenant A and tenant B (and across
two projects within a tenant), then assert:
  * every artifact carries the writing tenant_id + project + an external_source_handle that encodes that scope;
  * a search in tenant A returns ONLY tenant-A artifacts (B's are never visible) — the leak test;
  * a search in project P1 does not return project P2's artifacts (project isolation);
  * the external_source_handle is scoped to (tenant, project) so lineage cannot be confused across tenants.

CLI: python3 scripts/check_memory_tenant_project_scoping.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.adapters.memory.baltor_local import BaltorLocalMemoryProvider  # noqa: E402
from src.baltor.adapters.memory.supermemory_emulator import SupermemoryEmulatorProvider  # noqa: E402

_NOW = 1_700_000_000


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for label, factory in (("local", BaltorLocalMemoryProvider), ("emulator", SupermemoryEmulatorProvider)):
        p = factory()
        # same SECRET-flavored content written under two different tenants — must never cross.
        a = p.write({"tenant_id": "tenant_a", "project": "proj1",
                     "content": "ALPHA secret: account 111 flagged.", "now": _NOW})
        b = p.write({"tenant_id": "tenant_b", "project": "proj1",
                     "content": "BETA secret: account 222 flagged.", "now": _NOW})
        # a second project within tenant_a — must not bleed into proj1.
        a2 = p.write({"tenant_id": "tenant_a", "project": "proj2",
                      "content": "ALPHA proj2: account 333 flagged.", "now": _NOW + 1})

        check(f"{label}: artifact carries the writing tenant_id + project",
              a["tenant_id"] == "tenant_a" and a["project"] == "proj1" and
              b["tenant_id"] == "tenant_b" and b["project"] == "proj1")
        check(f"{label}: external_source_handle encodes the (tenant, project) scope",
              "tenant/tenant_a" in a["external_source_handle"] and "project/proj1" in a["external_source_handle"]
              and "tenant/tenant_b" in b["external_source_handle"])

        # THE LEAK TEST: search in tenant_a for a term present in BOTH tenants' content ("account ... flagged").
        res_a = p.search({"tenant_id": "tenant_a", "project": "proj1", "query": "account flagged"})
        handles_a = {r["external_source_handle"] for r in res_a["results"]}
        tenants_a = {r["tenant_id"] for r in res_a["results"]}
        check(f"{label}: tenant_a search returns ONLY tenant_a artifacts (no tenant_b leak)",
              tenants_a == {"tenant_a"} and b["external_source_handle"] not in handles_a,
              f"tenants_seen={tenants_a}")

        res_b = p.search({"tenant_id": "tenant_b", "project": "proj1", "query": "account flagged"})
        tenants_b = {r["tenant_id"] for r in res_b["results"]}
        check(f"{label}: tenant_b search returns ONLY tenant_b artifacts (no tenant_a leak)",
              tenants_b == {"tenant_b"} and a["external_source_handle"] not in
              {r["external_source_handle"] for r in res_b["results"]})

        # PROJECT isolation within a tenant.
        res_p1 = p.search({"tenant_id": "tenant_a", "project": "proj1", "query": "account flagged"})
        check(f"{label}: project proj1 search does NOT return proj2 artifacts",
              a2["external_source_handle"] not in {r["external_source_handle"] for r in res_p1["results"]})

        # profile is also scope-isolated.
        prof_a = p.profile({"tenant_id": "tenant_a", "project": "proj1", "now": _NOW + 2})
        prof_tenants = {e["tenant_id"] for e in prof_a["static"] + prof_a["dynamic"]}
        check(f"{label}: profile for tenant_a/proj1 contains only tenant_a/proj1 entries",
              prof_tenants in ({"tenant_a"}, set()) and
              all(e["project"] == "proj1" for e in prof_a["static"] + prof_a["dynamic"]))

        # querying a tenant that has written nothing returns empty (never another tenant's data).
        res_empty = p.search({"tenant_id": "tenant_unknown", "project": "proj1", "query": "account flagged"})
        check(f"{label}: unknown tenant search returns empty (no fallthrough to other tenants)",
              res_empty["results"] == [])

    print(f"\n{'PASS — check_memory_tenant_project_scoping: every MemoryArtifact carries tenant+project scope; searches/profiles are scope-isolated; a search in tenant A never returns tenant B (negative-tested); project isolation holds; unknown tenants get empty results.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Proof: memory artifacts are tenant+project scoped; no cross-tenant leak.")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return _self_test()
    ap.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
