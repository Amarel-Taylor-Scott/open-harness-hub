# Source / Pipeline / Artifact Version Ledger + Reprocessing Planner

Baltor's Context Engine produces components — from a raw `source_field` to a
served `context_pack` — and every one of them is versioned, lineaged, and
reprocessable. This document describes how a change is classified, how the run
fingerprint makes a re-run decidable, how reprocessing scope is computed, and
how the local SQLite ledger maps to production stores without changing the
contract.

The implementation lives in `scripts/pipeline_runtime/` (`source_graph.py`,
`versioning.py`, `reprocess_planner.py`, `artifact_ledger.py`,
`cfpb_artifacts.py`) and is held in place by nine self-tests, all green:

| Proof | Asserts |
|---|---|
| `check_artifact_type_registry.py` | the governed type registry holds its contract |
| `check_cfpb_source_graph_diff.py` | a content-hash diff scopes change to the artifact that changed |
| `check_pipeline_run_fingerprint.py` | the four-dimension fingerprint is idempotent / change-sensitive |
| `check_reprocess_source_change_scope.py` | a source change yields a minimal downstream plan |
| `check_reprocess_pipeline_change_scope.py` | a config change makes a new run; old outputs stay readable |
| `check_reprocess_security_policy_change.py` | security changes are re-encrypt / migrate, never reprocess |
| `check_tenant_isolation_policy.py` | the resolver enforces tenant isolation |
| `check_artifact_security_metadata.py` | every artifact carries a complete, separate security envelope |
| `check_cfpb_multi_grain_artifacts.py` | one record emits distinct, governed, lineaged types |

## Four kinds of change

The whole point of the version layer is that these are *different* changes with
*different* blast radii. Conflating them is what forces an organization to
re-run everything whenever anything moves.

- **Source change** — the underlying content changed. Detected by comparing two
  source graphs' `content_hash` values (`diff_source_graph`). Only the changed
  source artifacts and their downstream derived types need re-deriving.
- **Pipeline change** — the pipeline manifest (steps, gates, `artifact_policy`)
  changed. Detected by `pipeline_config_hash(spec)`. This produces a *new
  versioned run*; existing outputs are not touched until the new run succeeds.
- **Processor change** — a single `processor@version` changed (new code, prompt,
  model, or params). Only that processor's output types and their downstream
  need re-deriving. Every other grain is untouched.
- **Security change** — the tenant's isolation mode, residency, retention, or
  KMS key version changed. The *content* is identical, so this is never a
  semantic reprocess — it is re-encryption or storage migration. See
  `_repos/baltor/context/security/tenant-isolation-and-encryption.md`.

## The run fingerprint composes four independent hashes

`run_fingerprint()` (in `versioning.py`) builds a `RunFingerprint` from four
independent inputs, each its own hash:

- `source_snapshot_hash` — hash of the `{artifact_id: content_hash}` snapshot of
  the source graph.
- `pipeline_config_hash` — hash of the pipeline manifest (id/version, steps,
  gates, `artifact_policy`).
- `processor_set_hash` — hash of the sorted set of `ProcessorSpec.fingerprint()`
  values (each fingerprint covers code/prompt/model/params hashes).
- `security_policy_hash` — `TenantPolicy.security_policy_hash()` over isolation
  mode, residency, retention, PII policy, and KMS key ref + version.

`run_id` is `"run-" + sha(components)`, where `components()` includes only the
four hashes plus `tenant_id` and `isolation_mode`. **`trigger_id` is
deliberately excluded.** A re-trigger of identical source × pipeline ×
processors × security yields the *same* `run_id` — the run is idempotent, so a
duplicate event or a manual retry is a no-op rather than a redundant rebuild.
Change any one of the four dimensions and the `run_id` differs, which is exactly
a new versioned run that does not overwrite the old outputs.

## How reprocessing scope is computed

`reprocess_planner.py` computes the *minimal* set of work for a change and
classifies it into `semantic_reprocess_required` / `storage_migration_required`
/ `reencrypt_required`, with `affected_source_artifacts`,
`affected_derived_artifacts`, `steps_to_rerun`, `steps_to_skip`,
`requires_human_approval`, and `reason_codes`.

Three pieces drive the scope:

1. **The `DEPENDS_ON` artifact-type DAG** — each derived type declares the
   upstream types it consumes (e.g. `narrative_allegation` ← `sentence`;
   `conclusion` ← `atomic_fact` + `narrative_allegation`; `context_pack` ← the
   claim grains; `receipt` ← `context_pack`).
2. **Source → seed-type mapping** (`_seed_types_for_source`) — a changed
   `sentence` / `source_block` seeds `{sentence}`; a changed `source_field`
   seeds `{atomic_fact}` (plus `{entity_mention}` for `company`/`product`); a
   changed `source_record` seeds all derived types.
3. **Downstream closure** (`downstream_closure`) — transitively adds every
   derived type that consumes a seed.

So a single edited narrative sentence reruns
`sentence → narrative_allegation → emotion_signal → conclusion → context_pack →
receipt` but **not** the unrelated structured-field `atomic_fact`s; a changed
structured field reruns `atomic_fact → conclusion → context_pack → receipt` but
**not** the narrative grains. `plan_for_processor_change` uses the same closure
seeded from the `PRODUCER` map, so a new `emotion.lexicon@v2` reruns only
`emotion_signal` and its downstream.

## The supersession rule

A pipeline change does **not** delete or mutate the prior run's outputs.
`plan_for_pipeline_change` sets `requires_human_approval = False` precisely
because the old outputs are preserved and remain readable; the new run is
written under its own `run_id`. Only **after** the new run succeeds does
`ArtifactLedger.supersede_run(old_run_id, new_run_id)` stamp `superseded_by` on
the old `av_pipeline_runs` row and its `av_derived_artifacts`. Readers can
always see the last good outputs — there is never a window where a tenant is
served nothing because a rebuild is in flight.

## Local SQLite now, Postgres + object store + pgvector later

`ArtifactLedger` wraps an existing `DurableStore`, reusing its connection and
lock (no second database, no schema change to `DurableStore`). It adds only
additive `av_*` tables — `av_source_artifacts`, `av_derived_artifacts`,
`av_pipeline_specs`, `av_processor_specs`, `av_pipeline_runs`, `av_step_runs`,
`av_reprocessing_plans` — so the version layer cannot collide with the queue,
event, or run-ledger tables.

The row shapes are chosen so the same contract carries to production unchanged:

- the long JSON columns (`locator_json`, `metadata_json`, `security_json`,
  `source_artifact_ids_json`, `payload_json`, `citations_json`) become Postgres
  `JSONB` on long/EAV-style artifact tables;
- large `payload_json` blobs move to object storage, addressed by `content_hash`
  and resolved through `TenantStoreResolver.object_ref`;
- `embedding` artifacts land in pgvector;
- the `content_hash` identity, the four fingerprint dimensions, the lineage
  fields, and `superseded_by` semantics are all storage-independent.

**The ledger is the source of truth; the dashboard is a projection.** The read
methods (`list_source_artifacts`, `list_derived_artifacts`, `counts_by_type`,
`superseded_count`, `list_runs`, `recent_plans`) exist to feed the admin/ops
view — they never define state, only report it. Any UI count is derived from the
ledger, never hand-maintained.
