#!/usr/bin/env python3
"""scripts.security.tenant_store_resolver — the single resolution point for every tenant-scoped write.

Thin front door over scripts.security.tenant_catalog: no processor opens a global artifact DB directly —
it resolves through ``resolve(policy)`` and guards every write with ``assert_isolated_write`` so isolation
(shared_row → … → deployment_per_tenant) is enforced uniformly.
"""
from __future__ import annotations

from scripts.security.tenant_catalog import (CrossTenantWriteError, TenantPolicy, TenantStoreResolver,
                                             assert_isolated_write, policy_errors)


def resolve(policy: TenantPolicy) -> TenantStoreResolver:
    errs = policy_errors(policy)
    if errs:
        raise CrossTenantWriteError(f"invalid tenant policy: {errs}")
    return TenantStoreResolver(policy)


def guarded_write_ref(policy: TenantPolicy, logical_table: str, row: dict) -> str:
    """Resolve the isolation-correct ref for a tenant-data write and assert it does not violate isolation."""
    ref = resolve(policy).table_ref(logical_table)
    assert_isolated_write(policy, ref, row, logical_table=logical_table)
    return ref


__all__ = ["resolve", "guarded_write_ref", "TenantPolicy", "TenantStoreResolver",
           "assert_isolated_write", "CrossTenantWriteError"]
