#!/usr/bin/env python3
"""scripts.check_reprocess_security_policy_change — proof: security/governance changes are classified as
re-encryption or storage migration, NEVER as a needless semantic reprocess.

  * shared_row → database_per_tenant  → storage_migration_required (not semantic reprocess)
  * KMS key version bump              → reencrypt_required (not semantic reprocess)
  * retention policy change           → neither (content_hash unaffected)

CLI: python3 scripts/check_reprocess_security_policy_change.py --self-test
"""
from __future__ import annotations

import argparse

from scripts.pipeline_runtime.reprocess_planner import plan_for_security_policy_change
from scripts.security.tenant_catalog import TenantPolicy


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    base = TenantPolicy("acme", "shared_row")

    # isolation upgrade shared_row -> database_per_tenant
    upg = TenantPolicy("acme", "database_per_tenant", data_plane_ref="db-acme")
    p1 = plan_for_security_policy_change(base, upg)
    check("isolation upgrade triggers STORAGE MIGRATION", p1.storage_migration_required)
    check("isolation upgrade does NOT trigger a semantic reprocess", not p1.semantic_reprocess_required)
    check("isolation upgrade requires human approval", p1.requires_human_approval)
    check("isolation upgrade reason recorded",
          any("isolation_upgrade" in r for r in p1.reason_codes), str(p1.reason_codes))

    # KMS key rotation
    rot = TenantPolicy("acme", "shared_row", kms_key_version="2")
    p2 = plan_for_security_policy_change(base, rot)
    check("KMS key rotation triggers RE-ENCRYPTION", p2.reencrypt_required)
    check("KMS key rotation does NOT trigger a semantic reprocess", not p2.semantic_reprocess_required)
    check("KMS key rotation does NOT trigger storage migration", not p2.storage_migration_required)
    check("KMS rotation reason recorded", any("kms_key_rotation" in r for r in p2.reason_codes), str(p2.reason_codes))

    # retention policy change → no content change, no work
    ret = TenantPolicy("acme", "shared_row", retention_policy_id="retain-7y")
    p3 = plan_for_security_policy_change(base, ret)
    check("retention change → no semantic reprocess, no reencrypt, no migration",
          not (p3.semantic_reprocess_required or p3.reencrypt_required or p3.storage_migration_required),
          str(p3.as_dict()))
    check("retention change reason recorded", any("retention_change" in r for r in p3.reason_codes), str(p3.reason_codes))

    # no change at all
    p4 = plan_for_security_policy_change(base, TenantPolicy("acme", "shared_row"))
    check("identical policy → no work", p4.reason_codes == ["no_security_change"], str(p4.reason_codes))

    print(f"\n{'PASS — check_reprocess_security_policy_change: isolation upgrade = storage migration; key rotation = re-encryption; retention = no-op; never a needless semantic reprocess.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: security-policy change classification.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
