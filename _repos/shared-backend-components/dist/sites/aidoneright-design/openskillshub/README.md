# OpenSkillsHub.io — open skill graph

A shared graph of composable, evaluated agent skills — reusable, context-guided know-how. Discovery is not trust; similarity is not equivalence.

## Open it
`OpenSkillsHub.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openskillshub-main.jsx` + accent `#2f7d8f` + the `PORTFOLIO.ENTITIES`
entry in `shared/products.js`. Inherits the entire registry site from the shared kit:
landing, browse graph, entry detail with provenance/trust, the open-standards section, the
full account console (dashboard · installed · publish · keys · team · audit · billing · usage
· settings · docs · pricing · cases), ⌘K, A/B and tracking. See `README.md` → *makeHub* and
`HANDOFF.md §3.5` for the config shape + gated hooks.

- **kind:** Open skill graph
- **distinct from:** OpenToolsHub (executables) and OpenSkillToTool (skill→tool conversion) — a skill is open-ended know-how
