# OpenEndpointHub.io — endpoint due-diligence

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Governed due-diligence on LLM endpoints (free + low-cost + frontier) and gateways, with a data-class & jurisdiction eligibility profile: what data may I send where.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Renders a muted
  accent + a "Private preview" banner now; adopts its saturated `futureAccent` when opened.
- **open trigger:** a public governed-endpoint directory launches.
- **drawn from:** endpoint registries + free_endpoint_intel.
- **distinct from:** OpenMCPHub (MCP servers) — this is the model ENDPOINTS themselves + "what data may I send where".
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenEndpointHub.io Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openendpointhub-main.jsx` + one accent + the `PORTFOLIO` entity —
nothing bespoke. It inherits the entire registry site from the shared kit: landing, browse
graph, entry detail with provenance/trust, the open-standards section, dashboard · installed ·
publish · keys · team · audit · billing · usage · settings · docs · pricing · cases, ⌘K, A/B
and tracking. The `access: 'private'` config flag is what renders the pre-launch banner.

## Custom config used
`standards` (the relevant open stack) · `trust(e)` (per-entry attestation rows) ·
`facets` (the kind partition) · `access: 'private'` + `openTrigger`. Kind: **Endpoint due-diligence**.
