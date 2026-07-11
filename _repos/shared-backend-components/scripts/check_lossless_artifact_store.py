#!/usr/bin/env python3
"""scripts.check_lossless_artifact_store — proof: the lossless store never overwrites or deletes a layer.

Exercises ``src.baltor.distillation.lossless_store.LosslessStore`` against the lossless law:

* raw remains AFTER a decomposition writes derived facts over it;
* source remains AFTER a derived write;
* an old derived version remains AFTER a new version of the same key is written;
* ``set_current`` moves the active pointer WITHOUT deleting the prior version (it stays readable);
* ``rehydrate_payload`` round-trips the EXACT raw bytes;
* held-out + rejected entries remain queryable (omitted ≠ deleted);
* a ``tenant_private`` entry can NEVER appear in a ``global_public`` lineage (negative-tested);
* a cross-tenant ``get`` is rejected (negative-tested);
* the store is deterministic — the same body for the same tenant yields the same id (idempotent re-put).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_lossless_artifact_store.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.baltor.distillation.lossless_store import (  # noqa: E402
    GLOBAL_PUBLIC,
    TENANT_PRIVATE,
    LAYER_DERIVED,
    LAYER_RAW,
    LAYER_SOURCE,
    DistillationStoreError,
    LosslessStore,
    TenantBoundaryError,
)

_NOW = "2026-06-05T00:00:00Z"  # injected; never a clock read
_TENANT_A = "acme"
_TENANT_B = "globex"
_RAW_BYTES = b'{"native_id":"demo-1001","issue":"Incorrect information on your report","timely":"Yes"}'


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LosslessStore()

    # 1) ingest raw, then DECOMPOSE into derived facts. Raw must survive decomposition.
    raw = store.put_raw(_TENANT_A, key="cfpb/complaint/demo-1001", raw_bytes=_RAW_BYTES,
                        mime_type="application/json", now=_NOW)
    src = store.put_source(_TENANT_A, key="cfpb/complaint/demo-1001/normalized",
                           body={"native_id": "demo-1001", "fields": ["issue", "timely"]},
                           parent_ids=[raw.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001"], now=_NOW)
    fact = store.put_derived(_TENANT_A, key="cfpb/complaint/demo-1001/fact/timely",
                             body={"text": "Complaint demo-1001: timely response is Yes."},
                             parent_ids=[src.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001#timely"],
                             transform_type="decompose", transform_run_id="run-decompose-1", now=_NOW)
    check("raw remains after decomposition (still gettable)", store.get(raw.entry_id).layer == LAYER_RAW)
    check("source remains after a derived write", store.get(src.entry_id).layer == LAYER_SOURCE)
    check("derived fact written as a NEW layer (parents preserved)",
          fact.layer == LAYER_DERIVED and raw.entry_id not in (fact.entry_id,) and src.entry_id in fact.parent_ids)

    # 2) a NEW version of the SAME key must not delete the OLD version.
    pack_key = "cfpb/context_pack/regE"
    v1 = store.put_derived(_TENANT_A, key=pack_key, body={"answer": "10 business days", "version": 1},
                           parent_ids=[fact.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001#timely"],
                           transform_type="optimize", transform_run_id="run-opt-v1", role="baseline", now=_NOW)
    v2 = store.put_derived(_TENANT_A, key=pack_key, body={"answer": "10 business days", "version": 2, "compressed": True},
                           parent_ids=[v1.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001#timely"],
                           transform_type="optimize", transform_run_id="run-opt-v2", role="candidate", now=_NOW)
    vers = store.versions(pack_key, tenant=_TENANT_A)
    check("a new derived version keeps the old version (2 versions tracked)",
          len(vers) == 2 and {e.entry_id for e in vers} == {v1.entry_id, v2.entry_id})
    check("the old version is still individually readable after a new version",
          store.get(v1.entry_id).body["version"] == 1)

    # 3) current pointer moves WITHOUT deleting the prior version.
    check("default current pointer is the first version (v1)", store.current_id(pack_key, tenant=_TENANT_A) == v1.entry_id)
    prior = store.set_current(pack_key, v2.entry_id, tenant=_TENANT_A)
    check("set_current moves the active pointer to v2", store.current_id(pack_key, tenant=_TENANT_A) == v2.entry_id)
    check("set_current returns the PRIOR pointer id (it is not lost)", prior == v1.entry_id)
    check("the prior pointer's entry is NOT deleted (still gettable after pointer move)",
          store.has(v1.entry_id) and store.get(v1.entry_id).body["version"] == 1)
    check("versions list length unchanged after pointer move (nothing removed)",
          len(store.versions(pack_key, tenant=_TENANT_A)) == 2)

    # 4) payload_ref rehydrates the EXACT raw bytes (content-addressed, verified).
    got = store.rehydrate_payload(raw.payload_ref)
    check("rehydrate_payload round-trips the exact raw bytes", got == _RAW_BYTES)
    check("the raw entry stores only an opaque payload_ref, not the bytes",
          raw.payload_ref.startswith("objref:sha256:") and _RAW_BYTES not in str(raw.body).encode())

    # 5) held-out + rejected entries remain queryable (omitted ≠ deleted).
    held = store.put_derived(_TENANT_A, key="cfpb/complaint/demo-1001/allegation/s0",
                             body={"text": "They reported an account that is not mine."},
                             parent_ids=[src.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001#narrative.s0"],
                             transform_type="decompose", transform_run_id="run-decompose-1",
                             role="held_out", now=_NOW)
    rejected = store.put_derived(_TENANT_A, key=pack_key, body={"answer": "10 business days", "version": "cand-lossy"},
                                 parent_ids=[v1.entry_id], transform_type="optimize",
                                 transform_run_id="run-opt-v2", role="rejected", now=_NOW)
    # the winning pack records the held-out + rejected siblings (kept by id, never deleted).
    winner = store.put_derived(_TENANT_A, key=pack_key, body={"answer": "10 business days", "version": 3, "promoted": True},
                               parent_ids=[v2.entry_id], source_handles=["ctx://cfpb/complaint/demo-1001#timely"],
                               transform_type="promote", transform_run_id="run-promote-1", role="winner",
                               held_out_ids=[held.entry_id], rejected_ids=[rejected.entry_id], now=_NOW)
    check("held-out entry remains queryable by role", [e.entry_id for e in store.query(tenant=_TENANT_A, role="held_out")] == [held.entry_id])
    check("rejected entry remains queryable by role", [e.entry_id for e in store.query(tenant=_TENANT_A, role="rejected")] == [rejected.entry_id])
    check("the winner records held-out + rejected ids (kept, not deleted)",
          held.entry_id in winner.held_out_ids and rejected.entry_id in winner.rejected_ids)
    check("the recorded held-out + rejected ids still resolve in the store",
          store.has(winner.held_out_ids[0]) and store.has(winner.rejected_ids[0]))

    # 6) idempotent + deterministic: re-putting the SAME body for the SAME tenant returns the SAME id.
    raw_again = store.put_raw(_TENANT_A, key="cfpb/complaint/demo-1001", raw_bytes=_RAW_BYTES,
                              mime_type="application/json", now="2099-01-01T00:00:00Z")
    check("re-put of the same raw body is idempotent (same id, overwrites nothing)", raw_again.entry_id == raw.entry_id)
    fresh = LosslessStore()
    raw_fresh = fresh.put_raw(_TENANT_A, key="cfpb/complaint/demo-1001", raw_bytes=_RAW_BYTES,
                              mime_type="application/json", now=_NOW)
    check("id is reproducible from a clean store (deterministic, no clock/RNG)", raw_fresh.entry_id == raw.entry_id)

    # 7) NEGATIVE: a tenant_private parent cannot enter a global_public lineage.
    priv = store.put_source(_TENANT_A, key="tenantA/private/source", body={"secret": "internal"},
                            parent_ids=[raw.entry_id], scope=TENANT_PRIVATE, now=_NOW)
    boundary_caught = False
    try:
        store.put_derived(_TENANT_A, key="tenantA/public/pack", body={"public": True},
                          parent_ids=[priv.entry_id], scope=GLOBAL_PUBLIC, transform_type="promote", now=_NOW)
    except TenantBoundaryError:
        boundary_caught = True
    check("tenant_private parent CANNOT enter a global_public lineage (negative-tested)", boundary_caught)
    # a global_public layer over a global_public parent is allowed (public raw → public source → public pack).
    pub_raw = store.put_raw(_TENANT_A, key="tenantA/public/raw", raw_bytes=b'{"public":true}',
                            scope=GLOBAL_PUBLIC, now=_NOW)
    pub_src = store.put_source(_TENANT_A, key="tenantA/public/source", body={"public": True},
                               parent_ids=[pub_raw.entry_id], scope=GLOBAL_PUBLIC, now=_NOW)
    ok_pub = store.put_derived(_TENANT_A, key="tenantA/public/pack2", body={"public": True},
                               parent_ids=[pub_src.entry_id], scope=GLOBAL_PUBLIC, transform_type="promote", now=_NOW)
    check("a global_public layer over a global_public parent is allowed", ok_pub.scope == GLOBAL_PUBLIC)

    # 8) NEGATIVE: a cross-tenant get is rejected (tenant is part of the id identity).
    raw_b = store.put_raw(_TENANT_B, key="cfpb/complaint/demo-1001", raw_bytes=_RAW_BYTES, now=_NOW)
    check("same bytes under a different tenant is a DIFFERENT, isolated entry", raw_b.entry_id != raw.entry_id)
    cross_caught = False
    try:
        store.get(raw.entry_id, tenant=_TENANT_B)  # tenant B asking for tenant A's entry
    except TenantBoundaryError:
        cross_caught = True
    check("a cross-tenant get is rejected (negative-tested)", cross_caught)
    # tenant-scoped versions never leak across tenants.
    check("versions() is tenant-scoped (tenant B sees only its own)",
          [e.entry_id for e in store.versions("cfpb/complaint/demo-1001", tenant=_TENANT_B)] == [raw_b.entry_id])

    # 9) set_current of a non-version id is rejected (structural integrity).
    bad_pointer_caught = False
    try:
        store.set_current(pack_key, raw.entry_id, tenant=_TENANT_A)  # raw is not a version of pack_key
    except DistillationStoreError:
        bad_pointer_caught = True
    check("set_current rejects an id that is not a version of the key", bad_pointer_caught)

    ok = not fails
    print("\n" + ("PASS — check_lossless_artifact_store: the lossless store is append-only and tenant-scoped — "
                  "raw + source survive decomposition/derivation, old versions survive new ones, the current "
                  "pointer moves without deleting the prior version, payload_refs rehydrate exact bytes, held-out + "
                  "rejected stay queryable, tenant_private never enters a global_public lineage, and cross-tenant "
                  "reads are rejected." if ok else f"{len(fails)} FAILURES: {fails}"))
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: the lossless artifact store never overwrites/deletes a layer.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
