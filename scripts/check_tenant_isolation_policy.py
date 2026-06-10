#!/usr/bin/env python3
"""scripts.check_tenant_isolation_policy — proof: tenant isolation policy + store resolver enforce isolation.

Proves shared_row tenant-data writes require tenant_id, database_per_tenant rejects shared-table writes,
storage_account_per_tenant requires a tenant object store, the resolver returns different refs for isolated
tenants, and a cross-tenant write under database_per_tenant is rejected.

CLI: python3 scripts/check_tenant_isolation_policy.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.security.tenant_catalog import (CrossTenantWriteError, TenantPolicy, TenantStoreResolver,
                                             assert_isolated_write, policy_errors)


def _raises(fn) -> bool:
    try:
        fn(); return False
    except CrossTenantWriteError:
        return True


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    shared = TenantPolicy("acme", "shared_row")
    check("shared_row tenant-data write WITHOUT tenant_id is rejected",
          _raises(lambda: assert_isolated_write(shared, "shared:facts", {"x": 1}, logical_table="facts")))
    check("shared_row tenant-data write WITH tenant_id is allowed",
          not _raises(lambda: assert_isolated_write(shared, "shared:facts", {"tenant_id": "acme"}, logical_table="facts")))

    dbpt = TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme")
    check("database_per_tenant policy validates", policy_errors(dbpt) == [], str(policy_errors(dbpt)))
    check("database_per_tenant REJECTS a shared tenant-data table write",
          _raises(lambda: assert_isolated_write(dbpt, "shared:facts", {"tenant_id": "acme"}, logical_table="facts")))
    check("database_per_tenant ALLOWS its own isolated table write",
          not _raises(lambda: assert_isolated_write(dbpt, TenantStoreResolver(dbpt).table_ref("facts"),
                                                    {"tenant_id": "acme"}, logical_table="facts")))

    sapt_ok = TenantPolicy("acme", "storage_account_per_tenant", object_store_ref="store-acme")
    sapt_bad = TenantPolicy("acme", "storage_account_per_tenant", object_store_ref="shared-store")
    check("storage_account_per_tenant requires a tenant-specific object store",
          policy_errors(sapt_ok) == [] and policy_errors(sapt_bad) != [], str(policy_errors(sapt_bad)))

    a = TenantStoreResolver(TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme"))
    b = TenantStoreResolver(TenantPolicy("globex", "database_per_tenant", data_plane_ref="db-globex"))
    check("resolver returns DIFFERENT refs for isolated tenants",
          a.table_ref("facts") != b.table_ref("facts"), f"{a.table_ref('facts')} vs {b.table_ref('facts')}")

    check("NO cross-tenant write under database_per_tenant (ref encodes another tenant)",
          _raises(lambda: assert_isolated_write(dbpt, b.table_ref("facts"), {"tenant_id": "acme"}, logical_table="facts")))
    check("NO cross-tenant write (row tenant_id mismatches policy)",
          _raises(lambda: assert_isolated_write(dbpt, a.table_ref("facts"), {"tenant_id": "globex"}, logical_table="facts")))

    print(f"\n{'PASS — check_tenant_isolation_policy: isolation rules enforced (shared_row needs tenant_id; db_per_tenant rejects shared + cross-tenant writes; storage_account needs tenant store; resolver isolates).' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: tenant isolation policy + store resolver.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
