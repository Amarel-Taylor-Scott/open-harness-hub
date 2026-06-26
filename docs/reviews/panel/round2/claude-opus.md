# Panel round 2 - claude-opus cross-critique

> serves_truth=false. Adversarial cross-review of the glm-5.2 + kimi-k2.7-code round-1 reviews.

## Where I AGREE (strong convergence - this is the signal)
All three seats, reading the code independently, reached the same core verdict, so it is unlikely to be any one
model's hallucination:
- **Sprawl vs the repo's OWN law.** GLM and Kimi both count the breadth (5 surfaces, ~198 registries, 584 gates,
  1750 modules, 3 scale goals) and call it a research project, not a startup. This is not an outside opinion - it
  is the repo's own foundational law #4 (`architecture/substrate_layers.json` -> DEPTH BEFORE BREADTH, gated by
  `scripts/proposal_backlog.py`) being violated. High confidence.
- **No paying customer.** All three cite the pre-revenue state (`docs/strategy/design-partner-pilot-program.md`:
  "NO PARTNER SIGNED YET"). High confidence.
- **Scaffolding + unwired backends are real, not stylistic.** Both external models independently cited the SAME
  files: empty `src/baltor/{processors,llm_gateway,security}/*/__init__.py`, the `CONTRACT STUB` supermemory
  adapters, the `RE-EXPORT SHIM` workers/purpose_tasks, and `_UnwiredCloudStore` (`src/teleon/storage/record_store.py`)
  + the SQLite-only fleet ledger. Two models converging on the same file paths makes this verifiable, not vibes.

## Where I DISAGREE / NUANCE (catching the board's blind spots)
- **GLM overstates "consolidate to ~100 proof gates."** The 717-self-test gate is the repo's strongest asset and
  the reason this much surface area has not rotted. The fix is PARALLELIZING it (it already supports `RUN_PROOFS_WORKERS`),
  not deleting gates. Cutting gates to move faster would remove the one thing keeping breadth honest.
- **"Empty dirs = pure dead weight" is partly wrong.** Some are the port/adapter SHAPE the same reviews praise
  (CTO lens: the port architecture is "exemplary"). The right move is consolidate-or-implement per the
  move-not-delete law, not a blind purge - an empty `__init__.py` that documents an intended port is cheaper than
  the reviewers imply, though the truly-orphaned ones should be archived.
- **The re-export shims are a FEATURE mid-migration, not just debt.** They are the lossless Baltor->Teleon
  extraction in progress (the dependency-law file tracks `migration_status`). They should be finished + removed,
  but they are not an accident.

## What the board MISSED
- **The cost-descent margin thesis has no per-run cost RECEIPT wired into the runtime** - all three discuss it
  abstractly, but none flag that `src/teleon/economics/vertical_proof.py` computes savings from fixture constants,
  so "80% cheaper" is not yet provable on a real invoice. That is the single missing artifact that would convert
  the CFO story from spreadsheet to evidence.

## REVISED TOP 3 (the board's highest-leverage actions, weighed)
1. **Enforce DEPTH BEFORE BREADTH: pick ONE vertical (provider-directory or document-extraction), freeze new
   surfaces/registries/hubs, and get one paying/actively-using customer.** Unanimous across all five lenses and all
   three seats. This is the decision everything else waits on - and it is an OWNER call, not an agent's.
2. **Make the chosen vertical production-real:** implement the Postgres-backed `DurableFleetLedger` /
   `PostgresRecordStore` (replace `_UnwiredCloudStore`) and a persisted object store, then finish + delete the
   Baltor->Teleon re-export shims for that vertical's path. Keep the proof gate; parallelize it.
3. **Wire a per-run cost receipt + metered billing for that ONE capability** (extend the evidence ledger;
   `scripts/billing_plane.py` exists but is unwired) so the cost-descent thesis shows up as a real margin number on
   a real invoice. Then take it to 3 customers.

Net: the architecture is ahead of demand. The board's signal is loud and convergent - stop widening, prove one
narrow thing with a real user, and let that drive the roadmap.
