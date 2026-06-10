# CFPB worked example — the existing flow is already lossless

## Purpose

Show the lossless law on a concrete, shipped flow: the CFPB Reg-E consumer-complaint path
(`scripts.runtime.consumption.run_cfpb_to_consumption`). This is an **apply-proof** — it RUNS the existing
flow and asserts the law over the *real* outputs. It does **not** build a new flow and does **not** modify
the runtime.

## Owner

Flow: `scripts/runtime/consumption.py` + `scripts/runtime/optimization.py` +
`scripts/ingest/decompose_structured.py`. Proof: `scripts/check_cfpb_lossless_distillation.py`.

## Contracts

`InformationRetentionReport.v1` (the verdict the proof feeds the real transform into),
`DistillationRun.v1` / `LineageBundle.v1` (the shapes the store-level proofs use for the same graph).

## Inputs

A raw CFPB complaint (structured scalar fields + a free-text `consumer_complaint_narrative`) and the Reg-E
context pack the shipped flow assembles.

## Outputs / what the proof asserts

- **Raw + source + every `#field` atomic fact survive.** `decompose_cfpb_complaint` turns each structured
  field into an atomic fact with an expandable `ctx://…#field` handle; re-decompose is deterministic (the
  prior parse is reproducible, not destroyed).
- **The answer stays exactly `"10 business days"`.** Reg E (the source-of-law) wins; the FAQ summary does
  not silently overwrite it. Every served fact carries a source handle (coverage = 100%).
- **FAQ-30 (the conflict loser) and the narrative allegations are HELD OUT, not served — but rehydratable.**
  Their source handles still resolve back to the source (`ctx://cfpb/faq…`, `ctx://cfpb/consumer-complaints…`).
- **The optimized (promoted) pack carries baseline lineage** — same `source_snapshot_hash` — and cites the
  optimization receipt; it did not appear from nowhere.
- **Rejected optimization candidates stay queryable**, each with its `reject` receipt; the **rollback
  target** (the un-mutated baseline pack/snapshot) is intact.
- **No source artifact is deleted** — every baseline id survives in {served, held-out, or the preserved
  baseline/rollback target}. A top-k view may *omit* lower-rank facts from the served pack; those facts
  survive in the baseline (omitted ≠ deleted).
- The real transform fed into `InformationRetentionReport` is **`safe_to_promote`** (coverage 100%, zero
  dropped handles, no orphaned inputs).

## Proofs

- `check_cfpb_lossless_distillation` — the assertions above, end to end.
- `check_lossless_distillation_full_stack` — includes the CFPB apply-proof summary in its evidence block.

## Commands

```bash
PYTHONPATH=. python3 scripts/check_cfpb_lossless_distillation.py --self-test
```

## Limitations

The example is a deterministic fixture (injected time, content-addressed ids); it exercises the law's shape,
not production volume. Live freshness/CDC and post-promotion monitoring are deferred.

## Next

Mirror this apply-proof for an LLM→deterministic-rule conversion (the law's clause that a distilled rule
never deletes the LLM/consensus/adjudication traces) once the rule-distillation path is wired.
