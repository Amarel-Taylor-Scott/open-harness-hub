# OpenTemplatesHub.io — template families

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Reusable schema · runtime · resource · API-UI · inference · PurposeTask starting shapes you instantiate. "Templates generate shapes; harnesses prove the outputs."

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Renders a muted
  accent + a "Private preview" banner now; adopts its saturated `futureAccent` when opened.
- **open trigger:** a public template / scaffold registry enters the lane.
- **drawn from:** Shared Template Registry.
- **distinct from:** OpenHarnessHub (a harness PROVES an output) — a template is the SHAPE you instantiate.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenTemplatesHub.io Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `opentemplateshub-main.jsx` + one accent + the `PORTFOLIO` entity —
nothing bespoke. It inherits the entire registry site from the shared kit: landing, browse
graph, entry detail with provenance/trust, the open-standards section, dashboard · installed ·
publish · keys · team · audit · billing · usage · settings · docs · pricing · cases, ⌘K, A/B
and tracking. The `access: 'private'` config flag is what renders the pre-launch banner.

## Custom config used
`standards` (the relevant open stack) · `trust(e)` (per-entry attestation rows) ·
`facets` (the kind partition) · `access: 'private'` + `openTrigger`. Kind: **Template families**.
