# YC Owner-Ratification Proposals - 2026-06-14

Status: **A1, A2, A3 RATIFIED by the owner 2026-06-18** and applied. A1 — the portfolio applies led by
Baltor, all entities kept (final headline polish reserved to the owner). A2 — lead with BOTH counts
(all-components ⟦computed⟧ + action-ready ⟦computed⟧), clearly labeled. A3 — scope-dependent precedence
(a tenant's own doc wins for tenant-private facts; official sources win for public/regulated facts). The
prose below is the prepared proposal; the applied form lives in the YC docs + the unified authority-rank module.

## A1 - Applying Entity And One Sentence

Recommended primary applying entity: **Baltor**.

Recommended one-liner:

> Baltor continuously verifies your AI's context is correct - not just current -
> against authoritative sources, and proves it with a portable receipt.

Reasoning:

- Baltor is the customer-facing applied product.
- Teleon is the capability/runtime layer behind Baltor.
- AI Done Right is the parent brand and promise.
- Open*Hubs are discovery and ecosystem surfaces, not the applying entity.

Proposed application/doc treatment after ratification:

- Lead with Baltor and the one-liner above.
- Demote Teleon to "how the deterministic and LLM-assisted tools run."
- Demote AI Done Right to "parent company."
- Demote Open*Hubs to "open registries and lead-gen surface."
- Do not edit `architecture/brand.json` for this decision.

## A2 - Component-Count Scope

Owner decision needed: choose the scope to lead with, then wire the chosen value
as computed output rather than prose.

Recommended lead scope: **action-ready components**.

Reasoning:

- The YC pitch should emphasize what can be applied, composed, and governed now.
- The broader all-components scope is real catalog mass, but it is less direct as
  a buyer-facing readiness claim.
- The exact number must be emitted by `scripts/build_readme_stats.py` or a
  narrower generated counter, then referenced as `computed` in pitch docs.

Proposed application/doc treatment after ratification:

- Lead with the computed action-ready component count.
- Keep the all-components count as supporting catalog breadth when useful.
- Add/extend a count-drift gate before changing pitch prose.
- Never hand-type either count in the YC draft.

## A3 - Authority-rank-map unification (OPP-unify-authority-rank-maps; truth-precedence, owner-gated)

Surfaced 2026-06-18 by the multi-agent audit. There are three `source_type -> authority_rank` maps
(`src/baltor/contextops/reliability.py`, `.../source_discovery.py`, `src/baltor/graph/temporal/contracts.py`),
each previously commented as a "single source." They agree on the LOAD-BEARING precedence (source-of-law is the
unique top; source-of-law > official_agency > agency FAQ) — now ENFORCED across all three by the new
`check_authority_rank_core_precedence` gate — but they disagree on lower-tier VALUES and, for two pairs, ORDER:

- `tenant_document`: **15** (reliability — below an agency FAQ) vs **50** (discovery — above vendor docs/FAQ).
- `agency_faq` vs `vendor_doc`: reliability ranks FAQ above vendor docs; discovery ranks vendor docs above FAQ.
- scale offsets: `source_of_law` 95 vs 100, `primary_dataset` 70 vs 75, `agency_faq` 30 vs 20 vs 40, etc.

**Why this is owner-gated, not auto-fixed:** picking the unified numbers is a *truth-precedence* decision (does a
tenant's own document outrank a government FAQ? does a vendor doc outrank an agency FAQ?), which the change-
verification contract says is NEVER a unilateral single-agent call. The misleading "single source" comments have
been corrected to say the maps are not yet value-unified; the core precedence is gated; the threshold
`_OFFICIAL_MIN_RANK` is now derived (no hand-typed literal). What remains for the owner:

1. Decide the canonical `tenant_document` and `vendor_doc`-vs-`agency_faq` precedence (one ruling, recorded as warrant).
2. Then collapse the three maps to ONE shared `source_type -> rank` module imported by all three subsystems, record
   the prior per-map expected ranks in the proofs (lossless), and tighten `check_authority_rank_core_precedence`
   from core-chain-only to full-map equality once the values agree.

## Not Applied

These are not brand/content changes yet. This file is the owner-facing proposal
artifact required by `docs/goals/yc-readiness-loop.md`.
