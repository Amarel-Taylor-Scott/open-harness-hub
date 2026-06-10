# Baltor product language — naming transition

We are moving away from **"Oracle"** as Baltor product language.

## Why
"Oracle" implies omniscient truth. Baltor does not claim absolute truth — it **reconciles,
verifies, enhances, optimizes, and serves source-linked context** with lineage, freshness, policy,
and receipts. The honest framing is **context assurance / governance**, not omniscience.

## Preferred language
- **Baltor Context Engine** (the product)
- Baltor Context Fabric · Context Assurance Layer · Context Gateway · Context Pack Engine · Context Pipeline
- **Context Receipt** (not "oracle certificate") · **Context pack** (not "oracle answer")
- API naming: `context_*` (e.g. `context_for_ticket`, `context_verify`, `context_fetch`, `context_trace`, `context_receipt`) — not `oracle_*`.

## Deprecated (do not introduce in new UI/copy/metadata/routes/APIs)
- "Baltor Oracle", "Baltor Oracle Engine", "Automated Context Oracle", "Oracle Engine"
- `oracle_*` API names
- Route `oracle-hero.html` → **canonical is `context-engine-hero.html`**; the old route is kept only as a redirect stub.

## The ONE exception — keep the technical "oracle source" term
A blockchain/data-feed **"oracle"** = a *trusted external source of truth* (e.g. an "oracle
publisher", an "oracle source"). That is a legitimate, different meaning and is **retained** in
governance/strategy docs and `scripts/processors/assurance/*`. The retirement above targets the
*product name only*, not this data-governance term.

## Visual model (unchanged)
Source Systems → Reconciliation → Anti-Fragility → Enhancement → Optimization → Consumption,
with a universal **Continuous Verification + Adversarial Validation** rail beneath the pipeline.

## Status (2026-06-04)
- `web/baltor/` user-facing copy: Oracle-free (verified by grep).
- Route renamed: `context-engine-hero.html` canonical; `oracle-hero.html` is a redirect stub; 7 nav links repointed.
- Remaining tracked "oracle" usages in `docs/strategy/` + `scripts/processors/assurance/` are the *technical* "oracle source/publisher" term (retained, per the exception above).
