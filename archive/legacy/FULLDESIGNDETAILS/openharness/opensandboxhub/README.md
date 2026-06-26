# OpenSandboxHub.io — sandbox intelligence

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Isolated sandbox registry + risk/conformance (E2B · Daytona · agent-sandbox class): isolation class, egress policy, escape-test results. Discovery is not trust, applied to runtimes.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Renders a muted
  accent + a "Private preview" banner now; adopts its saturated `futureAccent` when opened.
- **open trigger:** a public sandbox directory enters the lane.
- **drawn from:** sandbox registries.
- **distinct from:** OpenEnvHub (the task world) — a sandbox is the ISOLATION the code runs inside.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenSandboxHub.io Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `opensandboxhub-main.jsx` + one accent + the `PORTFOLIO` entity —
nothing bespoke. It inherits the entire registry site from the shared kit: landing, browse
graph, entry detail with provenance/trust, the open-standards section, dashboard · installed ·
publish · keys · team · audit · billing · usage · settings · docs · pricing · cases, ⌘K, A/B
and tracking. The `access: 'private'` config flag is what renders the pre-launch banner.

## Custom config used
`standards` (the relevant open stack) · `trust(e)` (per-entry attestation rows) ·
`facets` (the kind partition) · `access: 'private'` + `openTrigger`. Kind: **Sandbox intelligence**.
