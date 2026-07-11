#!/usr/bin/env python3
"""scripts.pipeline_runtime.isolation — per-tenant data isolation (the "never mix customer data" rule).

Some customers require their data NEVER share a table with another tenant's. `PipelineSpec.isolation`
selects the policy; this resolves it to a concrete store:
  * ``shared``        — one durable db; tenants separated by partition key + tenant-scoped rows/lanes.
  * ``per_tenant_db`` — each tenant gets its OWN db file (``<base>/tenants/<tenant>/durable.db``); no
    cross-tenant row can exist because the rows are in different files. (Maps to a per-tenant Postgres
    database / schema in production; encryption-at-rest is a property of that backend.)

`tenant_slug` sanitizes the id (no path traversal). Stores are cached per path so connections are reused.
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts.durable_store import DurableStore
from scripts.pipeline_runtime.store import PipelineLedger

_SAFE = re.compile(r"[^a-z0-9_-]+")
_STORE_CACHE: dict[str, DurableStore] = {}


def tenant_slug(tenant_id: str) -> str:
    """Path-safe tenant id (lowercased, only [a-z0-9_-]); never empty, never traverses."""
    s = _SAFE.sub("-", str(tenant_id).lower()).strip("-")
    return s or "default"


def db_for_tenant(tenant_id: str, *, base_dir: str, isolation: str = "shared") -> str:
    base = Path(base_dir)
    if isolation == "per_tenant_db":
        return str(base / "tenants" / tenant_slug(tenant_id) / "durable.db")
    return str(base / "durable.db")  # shared


def store_for_tenant(tenant_id: str, *, base_dir: str, isolation: str = "shared") -> DurableStore:
    path = db_for_tenant(tenant_id, base_dir=base_dir, isolation=isolation)
    if path not in _STORE_CACHE:
        _STORE_CACHE[path] = DurableStore(path)
    return _STORE_CACHE[path]


def resolve(spec, tenant_id: str, *, base_dir: str, shared_store: DurableStore | None = None):
    """Honor spec.isolation → (store, ledger, db_path). per_tenant_db ⇒ the tenant's own db file."""
    if getattr(spec, "isolation", "shared") == "per_tenant_db":
        store = store_for_tenant(tenant_id, base_dir=base_dir, isolation="per_tenant_db")
        return store, PipelineLedger(store), store.path
    store = shared_store or store_for_tenant(tenant_id, base_dir=base_dir, isolation="shared")
    return store, PipelineLedger(store), store.path
