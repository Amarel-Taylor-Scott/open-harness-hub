# Rehydration

## Purpose

Prove the law's hardest clause: **no distillation without a rehydration path.** Every derived artifact must
be walkable back to the exact source it was distilled from — and that walk must never cross a tenant
boundary.

## Owner

`src/baltor/distillation/rehydration.py` (uses `lineage.py` + `lossless_store.py`).

## Contracts

`RehydrationReport.v1` — a successful rehydration carries `rehydrated=true`, ≥1 `source_artifact_ids`, and
`crossed_tenant_boundary=false`; a failed one carries `rehydrated=false`, empty source ids, and a
`failure_reason`.

## Inputs

`rehydrate(store, artifact_id, tenant)` / `rehydrate_payload(store, artifact_id, tenant)`. The `tenant` is
**required** — there is no anonymous, cross-tenant rehydration.

## Outputs

`rehydrate` → `{artifact, raw, source, parents, held_out, rejected, receipts, bundle}` (the actual store
entries the artifact was distilled from). `rehydrate_payload` → the EXACT raw bytes, content-hash verified
on the way out of the object store.

## What rehydration guarantees

- An **atomic fact** rehydrates to its source `#field` record and its raw record.
- An **optimized pack** rehydrates to its baseline (reachable through `parents` / the lineage bundle) and
  all the way to raw + source.
- A **held-out FAQ-30** (a conflict loser) rehydrates to the source it was held out of **plus** the
  reconciliation receipt that held it — *omitted ≠ deleted*.
- A request for tenant B's artifact by a tenant-A caller raises `RehydrationError` (a `TenantBoundaryError`);
  each tenant rehydrates its own identical graph fine — **isolation, not breakage**.
- Rehydration is a pure projection of the store (no clock, no RNG) → deterministic.

## Proofs

- `check_distillation_rehydration` — all of the guarantees above, with negative tests for cross-tenant and
  empty-tenant requests.
- `check_lossless_distillation_full_stack` — rehydrates the output of every critical-path transform back to
  raw + source as part of the master matrix.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_distillation_rehydration.py --self-test
```

## Limitations

`rehydrate_payload` follows the nearest reachable raw `payload_ref`; an artifact whose lineage genuinely has
no raw layer (e.g. a synthetic seed) raises `RehydrationError` rather than fabricating bytes — by design.

## Next

A projection endpoint (deferred) `POST /api/distillation/rehydrate` returning a `RehydrationReport.v1` so
auditors can rehydrate any served artifact without shell access.
