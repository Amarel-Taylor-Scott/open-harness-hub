# Verification Gate (C40) — the blocking gate between Enhancement and Optimization

Baltor's operating ladder is **governed improvement, not just speed**:

```
Source → Reconciliation → Anti-Fragility → Enhancement
   → [ VERIFICATION GATE ]      ← this doc (C40)
   → Optimization              (governed: candidate → measured lift → regression gate → promotion receipt)
   → [ REGRESSION GATE ]
   → Promotion / Consumption
   → Watchtower monitoring     (continuous fragile-fact reverification)
```

The principle:

> Enhancement can *add* value. Verification decides whether the value is *safe to promote*. Optimization may
> improve cost, latency, compression, retrieval, routing, ranking, or packaging — but it must **never silently
> change truth**, promote an allegation, leak tenant data, or hide a conflict.

So Optimization only ever consumes artifacts the gate marked **allow**; **hold_out** artifacts are retained
and may ride along as warnings, but never as verified truth.

## The component

`scripts/runtime/verification_gate.py` — `class VerificationGate` (declared owner in
`architecture/runtime_ownership.json`). It is a **decision + receipt maker**, never a mutator: `verify()`
produces a `VerificationReport`, `decide()` produces a `PromotionDecision` (`allow` | `hold_out`), and
`receipt()` produces a `VerificationReceipt` (content-addressed id, injected `created_at`) that explains every
decision. Canonical promotion happens downstream; the gate only judges. It reads governance from the single
source — `scripts/pipeline_runtime/artifact_types.py` — and schema validity through the runtime
`schema_validator`. It is fully deterministic and offline (time injected, no clock/RNG).

## The checks (per artifact)

| Check | Blocks promotion when… |
|---|---|
| `artifact_type_governed` | the type isn't in the governed registry |
| `source_handles_present` | a source-grounded artifact has no source handle |
| `content_hash_present` | no content hash |
| `artifact_schema_valid` | the declared payload schema fails validation |
| `allegation_not_promoted_as_fact` | a `narrative_allegation` claims `promotion_eligible=true` |
| `conclusion_support_present` | a `conclusion` cites no supporting artifacts |
| `conflict_absent_or_reconciled` | the artifact is in an unresolved/held-out conflict (the reconciler is the authority) |
| `fragile_fact_current_or_queued` | a fragile fact is stale **and** has no queued verification task |
| `tenant_isolation_preserved` | a `tenant_private` artifact is aimed at the `global_public`/`system_reference` scope |
| `model_output_grounded` | a model-dependent artifact lacks processor metadata or source traceability |

`decision = allow` iff there are no blocking violations **and** the type is promotable (`can_be_used_as_fact`
or legitimately `promotion_eligible`). Everything else is `hold_out`, with the reasons recorded on the receipt.

## CFPB worked example

- **Reg E "10 business days"** — `atomic_fact`, source-grounded, no open conflict → **allow**.
- **FAQ "30 days"** — once the reconciler holds it out (lower authority), the gate sees it in `held_out_ids` →
  **hold_out** (`conflict_absent_or_reconciled` fails). The reconciliation *winner* (Reg E 10) still passes.
- **Narrative allegation** ("they reported an account that isn't mine") → **hold_out** (not promotable as fact).

## What the gate does NOT do (it is graceful, not a rewrite)

- It does not mutate canonical truth or write to any store (projection-only; enforced by a proof).
- The **fragile-fact** check degrades gracefully until the Fact Watchtower lands: an artifact with no fragility
  metadata is treated as not-yet-stale; once the Watchtower (FACT-* / C41) sets `next_verify_at`/`ttl`, the
  same check enforces currency.
- The reconciler remains the conflict authority; the gate only reads its verdict.

Proof: `scripts/check_verification_gate.py` (the seven owner scenarios + tenant isolation, model grounding,
deterministic schema-valid receipts, projection-only). ADR: `docs/adr/0005-verification-gate-and-promotion-boundary.md`.
