# Lossless Distillation — a Baltor top-level law

Adopted 2026-06-05 (owner directive). Sits alongside [Change Verification](change-verification-contract.md)
and [No Magic Values](no-magic-values.md) as a standing law for all Baltor work and every workflow prompt.

## The law

> **Distillation is never replacement. Distillation creates a new derived layer while preserving the
> raw layer, intermediate layers, lineage, alternatives, rejected candidates, and rollback path.**

It applies to every transform Baltor performs:

```text
raw source
  → normalized source artifact
  → parsed/decomposed objects
  → facts / allegations / conclusions
  → graph / vectors / conflicts / reconciliations
  → verified context pack
  → optimized context pack
  → consumed response
```

Every arrow creates a **new versioned artifact**, not an overwrite.

## Core invariant: lossless AT THE SYSTEM LEVEL

A distilled artifact may be smaller, cleaner, compressed, normalized, or optimized — but the system
must retain raw input, normalized input, parsed/decomposed intermediates, **all source handles**, all
held-out items, all rejected candidates, all model/tool traces, all transform configs, all version
hashes, all receipts, and all rollback links.

- "Omitted from the served answer" ≠ deleted.
- "Held out" ≠ forgotten.
- "Rejected candidate" ≠ erased.
- "New deterministic rule" ≠ old LLM/consensus traces removed.
- "Superseded version" ≠ prior version deleted to make the new one look cleaner.

No destructive overwrite · no irreversible compression · no hidden replacement · no lossy promotion of
truth-bearing facts · no single winner without lineage to the losers · no distillation without a
rehydration path. Compression may shrink the **text surface only** if answer-critical facts, source
handles, and held-out warnings survive. Tenant-private lineage never becomes global.

## Promotability test

Every derived artifact must be able to answer, or it is **not promotable**:
which raw/source artifact + exact source handle backs me · which transform/version/config/model/rule
created me · what was omitted or held out · which candidate versions competed · what was the previous
active version · how do I roll back · which proof says I am safe to serve.

## Operating rules

- **Side-by-side before promotion** — baseline and candidate run on the same source snapshot; outputs
  stored separately; diff report produced; promotion deletes neither.
- **Shadow mode for new rules** — a deterministic rule distilled from LLM/human behavior runs alongside
  the live path, recorded but not authoritative, until it passes promotion.
- **Monitor after promotion** — source-handle coverage, held-out-leak, stale-served, tenant-leak,
  rehydration-failure, shadow-mismatch, rollback count; red status can trigger rollback or hold-out.
- **Rollback always available** — every promotion carries a rollback plan; rollback moves the active
  pointer only and never deletes the promoted candidate or prior responses.

## The clause (carry verbatim in every workflow prompt)

> **LOSSLESS DISTILLATION CLAUSE:** Any distillation, decomposition, compression, optimization,
> reconciliation, promotion, or LLM-to-rule conversion must be lossless at the system level. Never
> overwrite or delete raw/source/intermediate artifacts. Every derived artifact must preserve source
> handles, lineage, transform config, version, receipts, held-out items, rejected candidates, and a
> rollback target. Run side-by-side before promotion, run shadow mode for new rules, monitor after
> promotion, and prove rehydration. Omitted means held out or excluded from a view, never erased.

## Already proven in pieces (extend, don't reinvent)

Atomic CFPB facts preserve exact `ctx://…#field` handles and allegations are held out (not erased);
the optimization suite keeps the baseline snapshot + rejected candidates and refuses unsafe promotion;
durable workers are idempotent/exactly-once; architecture guardrails block ungoverned frameworks. The
[lossless distillation workflow](../../prompts/baltor-lossless-distillation-parallel-runtime.md) makes
the law a first-class subsystem (DistillationRun, LineageBundle, rehydration, retention reports,
parallel/shadow runs, monitoring, rollback) with proofs.
