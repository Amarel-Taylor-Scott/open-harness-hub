# OpenStateHub.io — agent state

**PRIVATE-FIRST candidate hub** — built on the shared kit, kept private until a competitor
enters the lane. Durable, governed working state for agents — memory, blackboard, graph — versioned with provenance and access scopes, kept auditable and reproducible.

## Status & release policy
- **status:** `private` (in `shared/products.js` → `PORTFOLIO.ENTITIES`). Muted accent +
  "Private preview" banner now; adopts its saturated `futureAccent` when opened — a one-line
  `status: 'private' → 'live'` flip (accent resolves automatically, banner disappears).
- **open trigger:** a public governed agent-state / memory registry launches.
- **drawn from:** persistent agent-state spine (blackboard · mem0 / letta / graphiti class).
- **distinct from:** OpenContextHub (governed TRUTH packs an agent reads) — this is the durable WORKING STATE an agent writes.
- discovery ≠ trust; never public without owner clearance.

## Open it
`OpenStateHub.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openstatehub-main.jsx` + one accent + the `PORTFOLIO` entity. Inherits the
entire registry site from the shared kit: landing, browse graph, entry detail with
provenance/trust, the open-standards section, the full account layer, ⌘K, A/B and tracking.
`access` is derived from `status`, so the pre-launch banner is automatic.

Kind: **State state**.
