# Context Enrichment as a Service (CEaaS) — product spec

CEaaS is a **content + corpus** service, not a pipeline builder (that's Open Harness Hub — see
[[two-services-shared-infrastructure.md]]). You give it content (or use our unique governed corpora);
it makes that content **token-efficient, governed, and agent-ready**, hosts it in tiers, and serves it
straight into open-ended agentic workflows (Claude Code, MCP clients, any agent loop).

## The three content tiers

Every corpus/document is hosted in three tiers; a user pulls the tier their budget and task want, or
**downloads** it to run locally / air-gapped.

| Tier | What it is | Produced by (shared backend components) | When to use |
|---|---|---|---|
| **Raw** | the canonical, full-fidelity source, governed + cited | the connectors + source registry + normalization | audit, exact-quote, ground truth |
| **Compressed** | token-reduced, **lift-preserving** form | `summarize.llmlingua` (LLMLingua) · `extractive-span-selector` · chunkers | the default working form fed to a model |
| **Hyper-efficient** | maximally token-dense: distilled facts + cached prefixes for hot paths | `memory/*` (distilled · reflect) · `cache/*` (prompt-prefix · semantic · KV) | high-volume / latency-critical agent loops |

Each tier carries provenance back to **raw** — the hyper-efficient tier is never an unsourced claim;
it traces to the canonical source. Compression is admitted only where it **preserves measured lift**
(and we report the breakeven honestly — LLMLingua only pays off in a matched length/ratio/hardware
window).

## Token-efficiency metering (the product's headline metric)

For every corpus and tier CEaaS reports **tokens-in → tokens-out** and the **lift retained** at that
compression, measured by a *separate* evaluator (no component grades its own work). That number is
both the value prop ("4× fewer tokens, lift retained") and the **billing basis**: per query, per GB
hosted, per refresh — the consumption motion the context-layer market rewards
([[context-layer-pmf.md]]).

## Agentic serving — the open-ended workflow hook

The differentiator vs. a plain compression library: CEaaS **serves the governed corpora + tools into
agents**, not just files. Via **MCP endpoints** (built on the existing MCP bridge), a Claude Code user
or any agent loop gets:
- the **unique governed knowledge corpora** (primary-source, cited, CDC-fresh) as a retrievable tool;
- the governed **tools/processors** (the catalog's Actions) the agent can call;
- the tier negotiation (ask for compressed by default; hyper-efficient on hot paths; raw for audit).

So an open-ended agent doesn't carry a giant context or a stale dump — it pulls token-dense, governed,
cited context and tools on demand. That is the "analyst keeps only the few distilled pages on the desk"
model ([[../concepts/context-layer-and-the-desk.md]]) delivered *as a service to someone else's agent*.

## Built on the shared backend (reuse, not rebuild)

CEaaS adds **no new engine** — it's a surface + a meter + MCP endpoints over the same substrate OHH
uses: the compression/memory/cache components, the governed corpora, the connectors, the lift/eval
harness, the vector store, the workers. A better compressor or a fresher corpus shipped for OHH is
instantly a better CEaaS tier. This is why the data plane is attribute-level
([[../codex/schema-extensibility.md]]): a new tier metric (e.g. `token_savings_ratio`) is a
`dimension-record` both services read, never a per-service column.

## Governance (the moat, on every tier)

Provenance + lineage on raw → compressed → hyper-efficient; CDC freshness + revocation on the live
corpora; signed attestations on the hosted artifacts; self-hostable / air-gappable downloads (the Onyx
pattern). The compressed and hyper-efficient tiers are governed derivations, not lossy guesses — that's
what separates CEaaS from "run LLMLingua yourself."

## Status (honest)

Spec-level. The compression/memory/cache/connector **components are validated definitions** (lifecycle
experimental). Implementation work to make CEaaS real: the tier pipeline
(raw→compressed→hyper-efficient, hosted + downloadable) on the shared workers, the MCP serving
endpoint, and the token-efficiency meter. None of it forks the backend.
