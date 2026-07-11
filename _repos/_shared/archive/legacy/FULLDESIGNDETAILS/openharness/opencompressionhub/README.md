# OpenCompressionHub.io — compression & budget intelligence

Context compression, token budgeting and fidelity benchmarks. Token reduction is not success unless answer-critical fidelity survives.

## Open it
`OpenCompressionHub Prototype.html` — open in a browser, no build step.

## How it's built (branded-house, config-only)
One `makeHub({…})` object in `opencompressionhub-main.jsx` + accent `#9bd61f` + the `PORTFOLIO.ENTITIES`
entry in `shared/products.js`. Inherits the entire registry site from the shared kit:
landing, browse graph, entry detail with provenance/trust, the open-standards section, the
full account console (dashboard · installed · publish · keys · team · audit · billing · usage
· settings · docs · pricing · cases), ⌘K, A/B and tracking. See `README.md` → *makeHub* and
`HANDOFF.md §3.5` for the config shape + gated hooks.

- **kind:** Compression & budget intelligence
- **distinct from:** OpenBenchmarkHub (scores) — this is the compression candidates + their fidelity tradeoff
