# OpenReviewHub.io — review intelligence

The open registry of **reviews**: papers and repos (and models, agents, datasets)
scrutinised for **capability, verifiability and reproducibility**. The family thesis —
*discovery is not trust* — applied to artifacts: a claim is not a capability until it
reproduces. Sits alongside **OpenBenchmarkHub** (a benchmark is *evidence*; a review is
the *scrutiny* — claim-by-claim, re-run, signed).

## Open it
`OpenReviewHub.html` — open in a browser, no build step.

## How it's built (branded-house, config-only + one hook)
A new family member built the right way — **pure config on the shared kit**, no fork:

- `openreviewhub-main.jsx` — one `makeHub({…})` object + one accent (`#9d4edd` purple,
  distinct from every other hub). Inherits the entire registry site: landing, browse graph,
  entry detail, the "Built on open standards" section, per-entry provenance/trust blocks,
  dashboard · installed · publish · keys · team · audit · billing · usage · settings · docs ·
  pricing · cases, ⌘K, A/B and tracking. The entity + portfolio wiring lives in
  `shared/products.js` (`PORTFOLIO.ENTITIES.openReviewHub`), so the parent's Open Resources
  picks it up automatically.
- `orh-pages.jsx` — the one piece of review-specific substance, rendered through the shared
  hub's generic `entryExtra` hook: a **review report** on every entry — the artifact under
  review, an axis **scorecard** (capability · verifiability · reproducibility · robustness),
  a **claim → evidence → verdict** ledger, and a **method & scope** note (what was, and
  wasn't, tested). `ORH_DATA` holds the per-review substance.
- `orh.css` — styles for those review surfaces; composes shared tokens + `.oh-*` primitives
  only, accent set inline by the hub root.

## Custom config used
- `standards` — the reproducibility stack (ML Reproducibility Checklist, ACM Artifact
  badges, Sigstore, in-toto, CycloneDX AI-BOM, SemVer review cards).
- `trust(e)` — per-entry rows leading with the **Reproduced · re-run ✓** attestation and an
  honest `Scope · tested ≠ everything` row.
- `entryExtra(e)` — the review report (see `orh-pages.jsx`).
- `facets` — the kinds of artifact reviewed: Papers · Repos · Models · Agents · Datasets.

## Verdicts
Each claim and each review carries a verdict: **reproduced** (re-run, held),
**partial** (held within tolerance / minor gap) or **failed / concerns found** (claim did
not hold on the released materials). Honesty about scope is a feature, not a footnote.
