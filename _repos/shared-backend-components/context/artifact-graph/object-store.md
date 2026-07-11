# Object Store — content-addressed `payload_ref` for large artifacts

**Section:** `object_store` (category: storage) · **Owner:** `scripts/runtime/object_store.py` (port + legacy
local stub) · **Adapter:** `_repos/baltor/backend/src/baltor/adapters/object_store/local_object_store.py` · **Proof:**
`scripts/check_object_store_payload_ref.py`.

## Why this exists

Large or raw payloads — original PDFs, OCR/Docling JSON, raw model responses, big context packs, trace
bundles — must **not** be inlined into the artifact JSON or rendered on the dashboard. Inlining them bloats
the ledger, leaks raw bytes into projections, and makes deduplication impossible. Instead, those bytes go to
the object store and the artifact ledger keeps only a small, content-addressed reference:

- `payload_ref` — the opaque handle (below)
- `content_hash` — `sha256:<hex>`
- `mime_type`
- `size_bytes`

The artifact thereby references the blob **by identity, not by value**. The ledger and dashboard never see
the bytes.

## The `payload_ref`

```
objref:sha256:<64-hex-sha256-of-bytes>:<tenant_id>
```

The ref is **content-addressed** (derived from `sha256(bytes)`) and **tenant-scoped** (the tenant is part of
the identity). Two consequences fall out for free:

- **Idempotent + deterministic.** The same bytes under the same tenant always produce the same ref — no
  clock, no RNG. Re-`put()`ting the same blob is a no-op and returns the same ref. A blob can be referenced
  from a clean store and resolve identically.
- **Opaque.** The ref carries a hash and a tenant, never payload bytes. An artifact that stores a
  `payload_ref` leaks nothing about the blob beyond its sha256 identity, and the ref is orders of magnitude
  smaller than the blob it points at.

## Interface

`LocalContentAddressedObjectStore` structurally satisfies `scripts.runtime.ports.ObjectStorePort`
(`put(tenant_id, data, *, mime_type) -> dict`, `get(ref) -> bytes`) and adds the artifact-graph guarantees:

| Method | Behaviour |
|---|---|
| `put(tenant_id, data, *, mime_type=…) -> dict` | Store bytes (or coerce str/JSON), return `{payload_ref, content_hash, mime_type, size_bytes}`. Content-addressed, idempotent. |
| `get(ref) -> bytes` | Resolve a ref to the exact stored bytes, **re-hashing on the way out**. Raises `CorruptObjectError` if the stored bytes no longer match the ref hash; `ForgedRefError` if the ref is malformed, unknown, or cross-tenant. |
| `exists(ref) -> bool` | True iff the ref is well-formed **and** resolves to a stored, tenant-scoped object. A malformed ref returns `False` (no raise). |
| `head(ref) -> dict` | Metadata only (`payload_ref, tenant_id, mime_type, content_hash, size_bytes`) — never the bytes. |
| `tenant_of(ref) -> str` | The tenant a ref is scoped to. |

### Read-time verification (the safety the artifact graph needs)

`get()` is not a dumb lookup. Every read **re-hashes the stored bytes** and compares against the hash
embedded in the ref:

- **Corruption / bit-rot / tamper** → stored bytes hash to something other than the ref hash →
  `CorruptObjectError`. A silently mutated blob can never masquerade as the original.
- **Forged ref** (right shape, a hash that was never stored) → `ForgedRefError`. A fabricated ref cannot
  smuggle arbitrary bytes out.
- **Cross-tenant ref** (tenant A's hash re-scoped to tenant B) → tenant B never stored those bytes →
  `ForgedRefError`. Tenants are isolated; re-scoping a ref does not grant access. If tenant B legitimately
  stores the same bytes, it gets its own isolated object under its own tenant key.

## Backend

The local adapter keeps an in-memory `dict` keyed by `(tenant_id, content_hash)` — deterministic and fully
offline (stdlib only). Because the interface is storage-agnostic, an S3/GCS/Azure adapter can replace it
without touching any caller: the `payload_ref` contract and the read-time verification are the same.

## Proof

```bash
PYTHONPATH=. python3 scripts/check_object_store_payload_ref.py --self-test
```

Stores a ~107 KB blob, asserts the ref is opaque and small, round-trips the exact bytes, confirms the same
blob yields the same ref from a clean store, simulates corruption and forged/cross-tenant refs (all
rejected), checks `exists()` across present/absent/malformed refs, and verifies tenant metadata is
preserved. The adapter is also asserted to satisfy `ObjectStorePort`.
