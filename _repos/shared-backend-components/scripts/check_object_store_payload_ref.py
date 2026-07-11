#!/usr/bin/env python3
"""scripts.check_object_store_payload_ref — proof: the object store keeps LARGE artifacts out of the ledger.

A 100KB blob is stored via ``put()`` and referenced only by an opaque content-addressed ``payload_ref``
(``objref:sha256:<hex>:<tenant>``). ``get(ref)`` round-trips the EXACT bytes; the same blob always yields the
same ref (content-addressed, deterministic — no clock, no RNG); a corrupted store and a forged ref both FAIL
content-hash verification; ``exists()`` answers truthfully; tenant metadata is preserved and a cross-tenant
``get`` is rejected; and the ref is opaque — the raw blob never leaks into the ref or into the ledger dict.
The adapter also structurally satisfies the runtime ``ObjectStorePort`` Protocol.

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_object_store_payload_ref.py --self-test
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.runtime.ports import ObjectStorePort  # noqa: E402
from src.baltor.adapters.object_store.local_object_store import (  # noqa: E402
    CorruptObjectError,
    ForgedRefError,
    LocalContentAddressedObjectStore,
    _StoredObject,
    make_ref,
    parse_ref,
)

# A "large" artifact — the kind that must NEVER be inlined into the artifact JSON / dashboard.
_LARGE_BLOB = b"BALTOR-RAW-PAYLOAD-" * 5500  # ~107 KB of raw bytes (deterministic, no RNG)
_TENANT_A = "acme"
_TENANT_B = "globex"


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    store = LocalContentAddressedObjectStore()

    # 0) the adapter satisfies the runtime ObjectStorePort Protocol (put + get duck-typed).
    check("adapter structurally satisfies ObjectStorePort", isinstance(store, ObjectStorePort))

    # 1) a large artifact goes in via put() and is referenced ONLY by an opaque payload_ref.
    assert len(_LARGE_BLOB) > 100_000, "test fixture must be a genuinely large (>100KB) artifact"
    ledger = store.put(_TENANT_A, _LARGE_BLOB, mime_type="application/pdf")
    ref = ledger["payload_ref"]
    check("put returns a ledger dict with a payload_ref", "payload_ref" in ledger and isinstance(ref, str))
    check("payload_ref has the opaque content-addressed shape objref:sha256:<hex>:<tenant>",
          ref.startswith("objref:sha256:") and ref.endswith(f":{_TENANT_A}"))
    check("ledger records size + content_hash + mime (metadata, not the blob)",
          ledger.get("size_bytes") == len(_LARGE_BLOB)
          and ledger.get("content_hash", "").startswith("sha256:")
          and ledger.get("mime_type") == "application/pdf")

    # 2) NO raw blob leaks — neither the ref nor the ledger dict carries the payload bytes.
    blob_marker = b"BALTOR-RAW-PAYLOAD-"
    ref_has_blob = blob_marker in ref.encode("utf-8")
    ledger_has_blob = any(
        isinstance(v, (bytes, bytearray)) or (isinstance(v, str) and blob_marker.decode() in v)
        for v in ledger.values()
    )
    check("the payload_ref is opaque — the raw blob does not leak into the ref", not ref_has_blob)
    check("the ledger dict carries no raw blob bytes (only a ref + hash + size)", not ledger_has_blob)
    check("the payload_ref is far smaller than the blob it references", len(ref) < len(_LARGE_BLOB) // 100)

    # 3) get(ref) round-trips the EXACT bytes.
    got = store.get(ref)
    check("get(ref) round-trips the exact stored bytes", got == _LARGE_BLOB)
    check("get returns bytes", isinstance(got, bytes))

    # 4) content-addressed + deterministic: the SAME blob yields the SAME ref (idempotent re-put).
    ref2 = store.put(_TENANT_A, _LARGE_BLOB, mime_type="application/pdf")["payload_ref"]
    store2 = LocalContentAddressedObjectStore()  # a fresh store, never seeded with any prior state
    ref3 = store2.put(_TENANT_A, _LARGE_BLOB, mime_type="application/pdf")["payload_ref"]
    check("same blob → same payload_ref (content-addressed, idempotent)", ref == ref2)
    check("ref is reproducible from a clean store (deterministic, no clock/RNG)", ref == ref3)
    # a different blob must yield a different ref.
    other_ref = store.put(_TENANT_A, b"a different artifact entirely")["payload_ref"]
    check("different blob → different payload_ref", other_ref != ref)

    # 5) exists() works for present, absent, and malformed refs.
    check("exists() is True for a stored ref", store.exists(ref) is True)
    absent = make_ref("0" * 64, _TENANT_A)
    check("exists() is False for an unknown (well-formed) ref", store.exists(absent) is False)
    check("exists() is False for a malformed ref (does not raise)", store.exists("not-a-ref") is False)

    # 6) a CORRUPTED store fails content-hash verification on read (tamper / bit-rot caught).
    content_hash_hex, tenant_id = parse_ref(ref)
    store._store[(tenant_id, content_hash_hex)] = _StoredObject(  # simulate on-disk corruption
        data=b"tampered bytes that no longer match the ref hash",
        tenant_id=tenant_id,
        mime_type="application/pdf",
    )
    corrupt_caught = False
    try:
        store.get(ref)
    except CorruptObjectError:
        corrupt_caught = True
    check("a corrupted store fails content-hash verification on get()", corrupt_caught)

    # 7) a FORGED ref (right shape, hash that was never stored) is rejected — cannot smuggle bytes out.
    forged = make_ref("a" * 64, _TENANT_A)
    forged_caught = False
    try:
        store2.get(forged)  # store2 holds the real blob but not this hash
    except ForgedRefError:
        forged_caught = True
    check("a forged/unknown ref is rejected by get()", forged_caught)
    # a structurally invalid ref is also rejected.
    bad_shape_caught = False
    try:
        store2.get("objref:md5:deadbeef:acme")
    except ForgedRefError:
        bad_shape_caught = True
    check("a wrong-scheme ref is rejected by parse/get", bad_shape_caught)

    # 8) tenant metadata is preserved and a CROSS-TENANT get is rejected (scoping holds).
    fresh = LocalContentAddressedObjectStore()
    ref_a = fresh.put(_TENANT_A, _LARGE_BLOB, mime_type="application/pdf")["payload_ref"]
    head = fresh.head(ref_a)
    check("tenant metadata is preserved alongside the blob", head["tenant_id"] == _TENANT_A and head["mime_type"] == "application/pdf")
    check("head() returns metadata only — no blob bytes", "data" not in head and head["size_bytes"] == len(_LARGE_BLOB))
    # same bytes, different tenant → a DIFFERENT ref (tenant is part of the identity).
    ref_a_as_b = make_ref(parse_ref(ref_a)[0], _TENANT_B)  # forge tenant A's hash under tenant B
    check("tenant is part of the ref identity (A's ref != B's ref for the same bytes)", ref_a_as_b != ref_a)
    cross_tenant_caught = False
    try:
        fresh.get(ref_a_as_b)  # tenant B never stored these bytes → must NOT resolve A's blob
    except ForgedRefError:
        cross_tenant_caught = True
    check("a cross-tenant get is rejected (tenant B cannot read tenant A's blob via a re-scoped ref)",
          cross_tenant_caught)
    # and tenant B legitimately storing the same bytes is a separate, isolated object.
    ref_b = fresh.put(_TENANT_B, _LARGE_BLOB)["payload_ref"]
    check("tenant B can store the same bytes as its own isolated object", fresh.get(ref_b) == _LARGE_BLOB)
    check("tenant_of(ref) reports the scoping tenant", fresh.tenant_of(ref_b) == _TENANT_B)

    ok = not fails
    print(
        f"\n{'PASS — check_object_store_payload_ref: large artifacts go in via put() and are referenced by an opaque, content-addressed payload_ref; get() round-trips exact bytes and verifies the content hash (corruption + forged + cross-tenant refs all rejected); same blob → same ref deterministically; tenant metadata preserved; no raw blob leaks into the ref or ledger.' if ok else f'{len(fails)} FAILURES: {fails}'}"
    )
    return 0 if ok else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: content-addressed object store payload_ref (verified, tenant-scoped).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
