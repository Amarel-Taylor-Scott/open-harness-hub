# OpenToolsHub.io — open tool graph

A registry of governed, callable tools — typed, scoped, executable actions agents can invoke. Public listing is not public execution; access is gated.

## Open it
`OpenToolsHub.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `opentoolshub-main.jsx` + accent `#8f6f2f` + the `PORTFOLIO.ENTITIES`
entry in `shared/products.js`. Inherits the entire registry site from the shared kit:
landing, browse graph, entry detail with provenance/trust, the open-standards section, the
full account console (dashboard · installed · publish · keys · team · audit · billing · usage
· settings · docs · pricing · cases), ⌘K, A/B and tracking. See `README.md` → *makeHub* and
`HANDOFF.md §3.5` for the config shape + gated hooks.

- **kind:** Open tool graph
- **distinct from:** OpenSkillsHub (know-how) — a tool is a typed, executable action
