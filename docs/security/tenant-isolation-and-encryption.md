# Tenant Isolation And Encryption

Baltor serves multiple tenants from one Context Engine, but a tenant's
components — facts, allegations, conclusions, embeddings, context packs,
receipts — must be physically isolated according to that tenant's policy, and
every artifact must carry a security envelope that is independent of its
content. This document describes the five isolation modes, the rules each
enforces, the single resolution point for store refs, and why key rotation and
isolation upgrades are never a semantic reprocess.

Implementation: `scripts/security/tenant_catalog.py`. Held in place by
`check_tenant_isolation_policy.py`, `check_artifact_security_metadata.py`, and
`check_reprocess_security_policy_change.py` (all green).

## The five isolation modes

`TenantPolicy.isolation_mode` is one of `ISOLATION_MODES`:

- **`shared_row`** — one logical table per artifact kind, every row tagged with
  `tenant_id`. The cheapest mode; isolation is enforced by the `tenant_id`
  predicate on every read and write.
- **`schema_per_tenant`** — a per-tenant schema; tables resolve to
  `schema:<tenant>:<table>`.
- **`database_per_tenant`** — a per-tenant database; tables resolve to
  `db:<tenant>:<table>` and must never resolve to a `shared:` table.
- **`storage_account_per_tenant`** — a per-tenant object store; relational rows
  are still tenant-scoped (`db:<tenant>:<table>`), but blobs resolve through the
  tenant's own `object_store_ref`.
- **`deployment_per_tenant`** — a fully dedicated deployment; the tenant has its
  own queue and data plane, and tables resolve to `deploy:<tenant>:<table>`.

The list of logical tables that hold tenant data — and therefore must obey these
rules — is `TENANT_DATA_TABLES` (`source_artifacts`, `derived_artifacts`,
`facts`, `allegations`, `conclusions`, `emotion_signals`, `context_packs`,
`receipts`, `embeddings`, `pipeline_runs`, `step_runs`).

## The isolation rules

`policy_errors(policy)` validates a policy; an empty list means valid. The
enforced rules:

- **`shared_row`** — `tenant_id` is required, and every write to a
  `TENANT_DATA_TABLES` table must carry `tenant_id` on the row.
- **`database_per_tenant`** — must *not* set `allow_cross_tenant_tables`, and the
  `data_plane_ref` must be tenant-specific. A write aimed at any `shared:` ref is
  rejected.
- **`storage_account_per_tenant`** — `object_store_ref` must be tenant-specific.
- **`deployment_per_tenant`** — both `queue_ref` and `data_plane_ref` must be
  tenant-specific.
- `allow_cross_tenant_tables` is only meaningful under `shared_row`; setting it
  in any other mode is an error.

`assert_isolated_write(policy, target_ref, row, logical_table=...)` guards every
write and raises `CrossTenantWriteError` when:

- a `TENANT_DATA_TABLES` row is missing `tenant_id`;
- a `database_per_tenant` tenant targets a `shared:` ref;
- the target ref encodes a *different* tenant than the policy
  (`schema:`/`db:`/`deploy:<other-tenant>:…`);
- the row's `tenant_id` does not match the policy's `tenant_id`.

## TenantStoreResolver — the single resolution point

There is no hardcoded global facts (or any other) table anywhere in the engine.
Every logical store/table name is resolved through `TenantStoreResolver`, which
maps a logical name to a concrete, isolation-correct ref for exactly one tenant:

- `table_ref(logical_table)` — applies the mode prefix (`shared:`, `schema:`,
  `db:`, `deploy:`) so two isolated tenants always resolve to different refs and
  an isolated tenant never resolves to a shared table;
- `object_ref(key)` — a tenant-owned store under `storage_account_per_tenant`,
  otherwise a tenant-prefixed key inside the shared store;
- `queue()` / `vector_ref(key)` — the tenant's queue and a tenant-scoped vector
  key.

Because resolution is centralized, isolation is a *provable* property: the proof
constructs two tenants and asserts their resolved refs never collide.

## The security envelope on every artifact

`security_metadata(policy, classification=…, pii=…, legal_hold=…)` produces the
envelope stamped on every artifact:

`tenant_id`, `classification`, `pii`, `encryption_mode` (`envelope`),
`kms_key_ref`, `kms_key_version`, `data_residency`, `retention_policy_id`,
`legal_hold`, and `access_policy_hash`. The required-non-empty subset is
`SECURITY_REQUIRED_KEYS`; `security_complete(meta)` verifies it.

**The envelope is separate from `content_hash`.** A source or derived artifact's
`content_hash` fingerprints the *content* only; the envelope lives in a separate
`security_json` field and is never folded into the content hash. This separation
is what makes the reprocessing classification correct: changing how an artifact
is *protected* must not look like changing what it *says*.

## Why key rotation and isolation upgrades are not reprocesses

`plan_for_security_policy_change` classifies security changes without ever
setting `semantic_reprocess_required`:

- **KMS key rotation** — `rotate_key(meta)` bumps `kms_key_version` and returns
  new security metadata; the caller must not touch `content_hash`. The planner
  sets `reencrypt_required = True`. The content is byte-for-byte identical, so
  this is re-encryption under the new key version, not a re-derivation.
- **Isolation upgrade** (e.g. `shared_row → database_per_tenant`) or a
  **residency change** — the planner sets `storage_migration_required = True`
  and `requires_human_approval = True`. The artifacts move to a new physical
  home; their content is unchanged.
- **Retention change** — records a `retention_change` reason code with no content
  change and no migration; it re-tags TTL/legal tiers only.

In every case `steps_to_skip` is the full set of derived types — no semantic
step reruns.

## Real KMS is a future swap

Locally there is no real KMS: `default_kms(tenant_id)` returns a fake
`kms://local/<tenant>/cmk` ref and `encryption_mode` is the contract value
`envelope`. The envelope already carries `kms_key_ref` + `kms_key_version`, so
swapping in a real KMS/HSM later is a backend change behind the same fields —
the artifact contract, the rotation semantics, and the reprocess classification
do not change.
