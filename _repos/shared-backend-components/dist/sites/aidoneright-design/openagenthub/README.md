# OpenAgentHub.io — agent-runtime registry

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. The runtimes that run agents — bounded adapters with declared loops, scopes and a run receipt per step.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Renders a muted
  accent + a "Private preview" banner now; adopts its saturated `futureAccent` when opened.
- **open trigger:** a public agent-runtime registry launches.
- **drawn from:** agent_runtime_catalog + teleon.
- **distinct from:** OpenSkillsHub (know-how) + OpenToolsHub (executables) — this is the RUNTIME an agent runs in.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenAgentHub.io.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openagenthub-main.jsx` + one accent + the `PORTFOLIO` entity —
nothing bespoke. It inherits the entire registry site from the shared kit: landing, browse
graph, entry detail with provenance/trust, the open-standards section, dashboard · installed ·
publish · keys · team · audit · billing · usage · settings · docs · pricing · cases, ⌘K, A/B
and tracking. The `access: 'private'` config flag is what renders the pre-launch banner.

## Custom config used
`standards` (the relevant open stack) · `trust(e)` (per-entry attestation rows) ·
`facets` (the kind partition) · `access: 'private'` + `openTrigger`. Kind: **Agent-runtime registry**.
