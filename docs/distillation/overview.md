# Lossless Distillation — subsystem overview

## Purpose

Make Baltor's top-level **lossless distillation law** (`docs/codex/lossless-distillation.md`) a *checkable
subsystem*: every transform Baltor performs — ingest, decompose, reconcile, optimize, promote — produces a
new derived layer **without ever overwriting or deleting** the raw input, the normalized source, the
intermediates, the held-out items, the rejected candidates, the lineage, the receipts, or the rollback
target. Distillation is never replacement; it is a new versioned layer over a fully-preserved history.

This subsystem turns the law from prose into code + proofs. The core (this pass) is: **contracts + store +
lineage + rehydration + rollback + retention report**, plus apply-proofs that the *existing* Baltor flows
(CFPB→consumption, the optimizer, ingest/decompose) already satisfy the law without being modified.

## Owner

`src/baltor/distillation/` (engine) + `scripts/check_*lossless*` and `scripts/check_distillation_*`,
`scripts/check_lineage_bundle_complete.py`, `scripts/check_information_retention_report.py` (proofs).
Standing law owner: `docs/codex/lossless-distillation.md`.

## Contracts

Six v1 schemas under `schemas/distillation/` (each with a passing `valid` example and a rejected
`invalid` example):

| Contract | Enforces |
|---|---|
| `DistillationRun.v1` | every transform records input+output ids/hashes, lineage (with source handles), all three preservation lists (omitted/held-out/rejected) present **even when empty**, `config_hash` **or** `rule_version`, and a `rollback_target`. |
| `LineageBundle.v1` | the backward lineage of an artifact: raw/source ids, handles, transform runs, receipts, held-out/rejected ids, prior versions, rollback targets. |
| `RehydrationReport.v1` | a rehydration reaches ≥1 source artifact and never crosses a tenant boundary. |
| `InformationRetentionReport.v1` | per-transform verdict: handle coverage, dropped handles, orphaned in/out, `safe_to_promote`. |
| `PromotionRecord.v1` | a promotion requires a `rollback_target_id` and keeps the prior version + rejected list. |
| `RollbackPlan.v1` | a pointer-only move (`deletes_artifacts=false`, `deletes_prior_responses=false`). |

## Inputs

Raw source bytes; normalized source artifacts; decomposed atomic facts and held-out narrative allegations;
reconciliation winners/losers; baseline + candidate context packs; the existing flows' real outputs.

## Outputs

Append-only, content-addressed, tenant-scoped layers in `LosslessStore` (`raw` / `source` / `derived`);
`LineageBundle`s; `RehydrationReport`-shaped walks; `InformationRetentionReport` verdicts; `RollbackPlan`s +
rollback receipts.

## Proofs

- `check_lossless_distillation_contracts` — the six schemas enforce the law at the contract layer.
- `check_lossless_artifact_store` — the store is append-only, tenant-scoped, pointer-moves-only.
- `check_lineage_bundle_complete` — every promoted artifact reaches raw + source + handles + run (and a
  reconciliation reaches BOTH winner and loser).
- `check_distillation_rehydration` — every derived artifact rehydrates to its source; no cross-tenant walk.
- `check_distillation_rollback` — rollback moves the pointer only and deletes nothing.
- `check_information_retention_report` — the retention verdict refuses every lossy transform.
- Apply-proofs (verify the existing flows, do NOT modify them):
  `check_cfpb_lossless_distillation`, `check_optimization_lossless_distillation`,
  `check_ingestion_decomposition_lossless`.
- Synthesis: `check_lossless_distillation_redteam` (every attack fails safely) +
  `check_lossless_distillation_full_stack` (the master transform matrix).

## Commands

```bash
PYTHONPATH=. python3 scripts/check_lossless_distillation_full_stack.py --self-test
PYTHONPATH=. python3 scripts/check_lossless_distillation_redteam.py --self-test
PYTHONPATH=. python3 scripts/check_lossless_distillation_contracts.py --self-test
```

## Limitations

This pass is the CORE only. **Deferred** (tracked as an opportunity): parallel candidate runs, shadow mode,
post-promotion monitoring signals, durable commands, the projection API, and the `/distillation` UI. The
apply-proofs VERIFY the existing runtime; they do not change it.

## Next

Promote the deferred opportunity (parallel/shadow/monitoring/durable-commands/API/UI) once the core lands in
the flywheel. Wire the synthesis proofs into `PROOF_MODULES` (see `registrations_needed`).
