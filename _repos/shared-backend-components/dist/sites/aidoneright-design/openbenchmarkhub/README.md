# OpenBenchmarkHub.io — benchmark intelligence

Benchmark cards, metrics and signed result records. A benchmark is evidence, not authority — a result cannot promote a candidate by itself.

## Open it
`OpenBenchmarkHub.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `openbenchmarkhub-main.jsx` + accent `#e0556a` + the `PORTFOLIO.ENTITIES`
entry in `shared/products.js`. Inherits the entire registry site from the shared kit:
landing, browse graph, entry detail with provenance/trust, the open-standards section, the
full account console (dashboard · installed · publish · keys · team · audit · billing · usage
· settings · docs · pricing · cases), ⌘K, A/B and tracking. See `README.md` → *makeHub* and
`HANDOFF.md §3.5` for the config shape + gated hooks.

- **kind:** Benchmark intelligence
- **distinct from:** OpenEnvHub (the task world) and OpenReviewHub (the scrutiny) — this is the score + suitability report
