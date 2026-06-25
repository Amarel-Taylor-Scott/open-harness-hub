# OpenEnvHub.io — eval environments

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Verifiable agent eval environments + reward specs — the task world a candidate is run against, not the score it earns.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Renders a muted
  accent + a "Private preview" banner now; adopts its saturated `futureAccent` when opened.
- **open trigger:** a public agent eval-environment registry appears.
- **drawn from:** Environment + Reward Spine.
- **distinct from:** OpenBenchmarkHub (definitions + result records) — an environment is the TASK WORLD; the score is downstream.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenEnvHub.io Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openenvhub-main.jsx` + one accent + the `PORTFOLIO` entity —
nothing bespoke. It inherits the entire registry site from the shared kit: landing, browse
graph, entry detail with provenance/trust, the open-standards section, dashboard · installed ·
publish · keys · team · audit · billing · usage · settings · docs · pricing · cases, ⌘K, A/B
and tracking. The `access: 'private'` config flag is what renders the pre-launch banner.

## Custom config used
`standards` (the relevant open stack) · `trust(e)` (per-entry attestation rows) ·
`facets` (the kind partition) · `access: 'private'` + `openTrigger`. Kind: **Eval environments**.
