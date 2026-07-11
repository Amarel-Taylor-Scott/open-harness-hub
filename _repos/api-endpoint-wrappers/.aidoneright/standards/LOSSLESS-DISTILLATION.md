# Lossless Distillation — distillation is never replacement

> Portable standard for any AI Done Right project. Reference implementation:
> `docs/codex/lossless-distillation.md` + the `CLAUDE.md` "Lossless Distillation" section.

## The rule

> **Distillation is never replacement. Any distillation, decomposition, compression, optimization,
> reconciliation, promotion, or LLM-to-deterministic-rule conversion creates a new *versioned* derived
> layer while PRESERVING the raw layer, intermediate layers, lineage, source handles, held-out items,
> rejected candidates, model/tool traces, transform configs, version hashes, receipts, and a rollback
> target.**

The transform chain — raw source → normalized artifact → parsed objects → facts → graph/vectors →
verified pack → optimized pack → consumed response — makes each arrow a **new versioned artifact**,
never an overwrite.

Four equalities are load-bearing:

- "Omitted from the served answer" ≠ deleted.
- "Held out" ≠ forgotten.
- "Rejected candidate" ≠ erased.
- "Superseded version" ≠ prior version deleted to make the new one look cleaner.

## Why

The moat is governed, provenanced data. A destructive overwrite, an irreversible compression, or a lossy
promotion of a truth-bearing fact throws away the exact lineage that lets a derived artifact prove where it
came from and roll back. A winner with no lineage to the losers is unauditable. Compression may shrink the
**text surface only** if answer-critical facts, source handles, and held-out warnings survive. Tenant-private
lineage never becomes global.

## How it is enforced (promotability test)

Every derived artifact must be able to answer, or it is **not promotable**:

- Which raw/source artifact and exact source handle backs me?
- Which transform / version / config / model / rule created me?
- What was omitted or held out, and which candidate versions competed?
- What was the previous active version, and how do I roll back?
- Which proof says I am safe to serve?

Operating rules that produce those answers:

- **Side-by-side before promotion** — baseline and candidate run on the *same* source snapshot; outputs
  stored separately; a diff report is produced; promotion deletes neither.
- **Shadow mode for new rules** — a rule distilled from LLM/human behavior runs alongside the live path,
  recorded but not authoritative, until it passes promotion.
- **Monitor after promotion** — source-handle coverage, held-out-leak, stale-served, tenant-leak,
  rehydration-failure, shadow-mismatch, rollback count; a red signal can trigger rollback or hold-out.
- **Rollback always available** — every promotion carries a rollback plan; rollback moves the active
  pointer only and never deletes the promoted candidate or prior responses.
- **Carry the clause in every workflow prompt** so an autonomous loop cannot forget it.

## DO / DON'T

- DO write a new versioned layer for every transform; keep raw + intermediates + configs + traces on disk.
- DO preserve held-out, rejected, and superseded items — mark them, do not remove them.
- DO run baseline-vs-candidate side by side and shadow new rules before they become authoritative.
- DON'T overwrite or delete a raw/source/intermediate artifact to "clean up."
- DON'T promote a single winner with no lineage to the candidates it beat.
- DON'T let a compression drop an answer-critical fact, a source handle, or a held-out warning.
