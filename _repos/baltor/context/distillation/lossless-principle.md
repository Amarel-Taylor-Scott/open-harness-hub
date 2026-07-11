# The lossless principle

## Purpose

State, in one place, the invariant the whole subsystem enforces, and show exactly how each clause is made
structural (impossible to violate) rather than merely promised.

## Owner

Standing law: `_repos/shared-backend-components/docs/codex/lossless-distillation.md`. Engine: `_repos/baltor/backend/src/baltor/distillation/lossless_store.py`.

## The law

> **Distillation is never replacement.** A distilled artifact may be smaller, cleaner, compressed,
> normalized, or optimized — but the *system* must retain raw input, normalized input, parsed/decomposed
> intermediates, **all source handles**, all held-out items, all rejected candidates, all model/tool traces,
> all transform configs, all version hashes, all receipts, and all rollback links.

- "Omitted from the served answer" ≠ deleted.
- "Held out" ≠ forgotten.
- "Rejected candidate" ≠ erased.
- "New deterministic rule" ≠ old LLM/consensus traces removed.
- "Superseded version" ≠ prior version deleted to make the new one look cleaner.

## How each clause is made structural

| Clause | Mechanism (where) |
|---|---|
| No destructive overwrite | `LosslessStore` is **append-only** + content-addressed (`dist:sha256:<hex>:<tenant>`); a different body yields a new id; an idempotent re-put returns the existing entry and mutates nothing. There is **no** `delete/remove/pop` API. |
| No hidden replacement | versions live under a stable `key`; `versions(key)` never shrinks; `set_current(key, id)` moves a **pointer** only — the prior version stays gettable. |
| No lossy truth promotion | `InformationRetentionReport.safe_to_promote` is False if any truth-bearing fact dropped a source handle, or any input vanished without being held-out/rejected/superseded. |
| No winner without lineage to losers | `LineageBundle.build` walks parents to raw/source; a reconciliation reaches BOTH winner and loser; held-out/rejected siblings are first-class layers, queryable forever. |
| No distillation without a rehydration path | `rehydrate(store, id, tenant)` returns `{raw, source, parents, held_out, rejected, receipts}`; `rehydrate_payload` returns the EXACT raw bytes. |
| Tenant-private lineage never goes global | `put_derived` raises `TenantBoundaryError` if a `global_public` entry would pull a `tenant_private` parent into its lineage; every read is tenant-checked (the id embeds the tenant). |
| Rollback always available, deletes nothing | `RollbackPlan` + `execute` move the active pointer only, assert the candidate is still present, and write a rollback receipt as a new lossless layer. |

## Contracts

`DistillationRun`, `LineageBundle`, `InformationRetentionReport`, `RehydrationReport`,
`PromotionRecord`, `RollbackPlan`.

## Inputs / Outputs

Inputs: any transform's input + output artifacts and its held-out/rejected/superseded lists. Outputs: a
`safe_to_promote` verdict and a complete, rehydratable lineage.

## Proofs

`check_lossless_distillation_contracts`, `check_lossless_artifact_store`,
`check_information_retention_report`, `check_lossless_distillation_redteam` (the adversarial proof that each
clause cannot be defeated).

## Commands

```bash
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_lossless_artifact_store.py --self-test
PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_lossless_distillation_redteam.py --self-test
```

## Limitations

The retention report is a **pure** verdict over the artifacts it is handed; it trusts the caller to pass the
real held-out/rejected lists. The apply-proofs are what guarantee the *real* flows pass those lists honestly.

## Next

Add `MonitoringSignal` (deferred) so a post-promotion handle-coverage or held-out-leak regression can trip
an automatic rollback — closing the loop from "provably lossless at promotion" to "stays lossless in
production".
