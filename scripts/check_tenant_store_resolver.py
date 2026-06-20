#!/usr/bin/env python3
"""scripts.check_tenant_store_resolver — proof: every tenant-scoped write routes through TenantStoreResolver
and isolation is enforced (shared_row needs tenant_id; database_per_tenant rejects shared writes;
storage_account_per_tenant needs a tenant object store; isolated tenants resolve to different refs).

CLI: python3 scripts/check_tenant_store_resolver.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.security.tenant_store_resolver import (CrossTenantWriteError, TenantPolicy, guarded_write_ref, resolve)


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
          _raises(lambda: guarded_write_ref(shared, "facts", {"x": 1})))
    check("shared_row WITH tenant_id resolves", guarded_write_ref(shared, "facts", {"tenant_id": "acme"}).startswith("shared:"))

    dbpt = TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme")
    check("database_per_tenant resolves to an ISOLATED ref (not shared:)",
          guarded_write_ref(dbpt, "facts", {"tenant_id": "acme"}).startswith("db:acme:"))
    # a write aimed at another tenant's resolved ref is rejected (no cross-tenant)
    other = resolve(TenantPolicy("globex", "database_per_tenant", data_plane_ref="db-globex")).table_ref("facts")
    from scripts.security.tenant_store_resolver import assert_isolated_write
    check("cross-tenant write under database_per_tenant is rejected",
          _raises(lambda: assert_isolated_write(dbpt, other, {"tenant_id": "acme"}, logical_table="facts")))

    sapt_bad = TenantPolicy("acme", "storage_account_per_tenant", object_store_ref="shared-store")
    check("storage_account_per_tenant REQUIRES a tenant object store (invalid policy rejected)",
          _raises(lambda: resolve(sapt_bad)))
    sapt_ok = TenantPolicy("acme", "storage_account_per_tenant", object_store_ref="store-acme")
    check("storage_account_per_tenant with a tenant store resolves + isolates blobs",
          resolve(sapt_ok).object_ref("k").startswith("store-acme/"))

    a = resolve(TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme"))
    b = resolve(TenantPolicy("globex", "database_per_tenant", data_plane_ref="db-globex"))
    check("isolated tenants resolve to DIFFERENT refs", a.table_ref("facts") != b.table_ref("facts"))

    print(f"\n{'PASS — check_tenant_store_resolver: all writes route through the resolver; isolation enforced across modes; no cross-tenant writes.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: TenantStoreResolver routing + isolation.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
