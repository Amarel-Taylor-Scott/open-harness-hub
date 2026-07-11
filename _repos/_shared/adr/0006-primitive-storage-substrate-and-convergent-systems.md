# ADR 0006 — Primitive storage/graph substrate & convergent external systems

## Status
Accepted (2026-07-04) as an **evaluation decision** (a spike target + intake), not a dependency adoption.

## Context
Owner asked to research up-and-coming systems: **Omnigraph** (ModernRelay), Loop/Expectation Engineering,
the Anthropic/Codex economic indices, parallel multi-agent graph enrichment, and hundreds-of-versions document
graphs — and to adopt what fits PMF. Earlier open question: where do primitives (especially very long ones)
live across DB + git + bucket. Assessed reuse-first + discovery≠trust.

## Decision
1. **Storage stays the 3-plane model, already largely built:** content-addressed object bucket (long bodies)
   + `LineageBundle`/`PromotionRecord` (lineage: parent/derive = fork, transform = remix, prior_version =
   supersede, rejected = variations) + Postgres/pgvector (rebuildable query index), joined by the canonical
   hash. No parallel git-based primitive store.
2. **Evaluate Omnigraph / Lance as a candidate UNIFYING substrate behind the registry port.** Omnigraph
   (MIT, Rust, Lance columnar on S3/R2, DataFusion, Cedar policy, MCP bridge, v0.8.0) delivers *git-style
   branching for parallel-agent enrichment* + content-addressed versioning + vector/graph/full-text in one
   engine on object storage — the exact 3-plane + parallel-factory shape, productized. It also answers the
   earlier "git-for-primitives without operating GitLab" question. **Decision: spike a bake-off** vs the
   current bucket+LineageBundle+pgvector assembly (multi-path law — race, don't switch on faith). Do NOT
   adopt a v0.8.0 dependency for the moat layer without receipts; at minimum it is a reference architecture
   and validation.
3. **Convergent framings are validators, adopt selectively.** Loop Engineering / the "Operator Loop Stack"
   (harness · loop contract · state · checker · human checkpoint), Expectation Constructs (ADR 0004), KARMA
   multi-agent KG enrichment, hybrid vector+graph memory, and immutable version graphs all map onto our
   existing CapabilityTask + LineageBundle + parallel-path factory + governed shared-context layer
   (`AIDONERIGHT-UNIVERSE` / dev-rules-context). Adopt their **vocabulary** for GTM; **ingest the Anthropic
   Economic Index (+ Codex research)** into the research-queue/gap-screen as a negative-space demand signal
   (its "economic primitives" — task complexity / autonomy / success — map to our two-axis lift gate +
   adaptation ladder).

## Consequences
A concrete build-vs-buy spike target (Omnigraph/Lance) for the primitive substrate; strong multi-source PMF
validation (the market is naming what we built); a new external demand signal for the research queue. No
dependency is adopted without a bake-off.

## Enforcement / links
`schemas/distillation/LineageBundle`, `PromotionRecord`; the registry port; `data/research-queue/`; ADR 0004
(Expectation Construct crosswalk). Sources: github.com/ModernRelay/omnigraph; anthropic.com/economic-index.
