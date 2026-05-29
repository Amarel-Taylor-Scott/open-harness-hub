# Two services, one shared infrastructure plane (decision record)

**Decision (owner, 2026-05-29):** run **two separate products/platforms on two domains**, sharing
the **infrastructure plane** — clusters, K8s, worker pools, the engine, the component+corpus data
plane, tooling, governance. A lot of the compute and data is identical, so we share it: **one COGS,
two revenue lines.** The differentiation is the *surface*, the *buyer*, and the *billing* — not the
backend.

This is **not** one web app with a brand toggle (an earlier draft framed it that way — wrong). These
are two genuinely distinct services that happen to sit on the same substrate.

## The two services

### Service 1 — Open Harness Hub (build + monitor a pipeline)
*Build a governed pipeline and monitor it, with rules around input and output.* The seven-primitive
builder, the governed recipe, observability, the I/O gates. Buyer: builders / applied teams
assembling and operating AI pipelines. Domain: `openharnesshub.com`.

### Service 2 — Context Enrichment as a Service (CEaaS)
A **content + corpus** service, not a pipeline builder. It:
- **compresses content and raises token efficiency** for users;
- **hosts content in three tiers — raw · compressed · hyper-efficient** — and lets users pull *or
  download* any tier;
- **serves the unique governed knowledge corpora + tools into open-ended agentic workflows** (Claude
  Code, MCP clients, any open agent loop) — so an agent gets token-dense, governed, cited context and
  tools dropped straight in.

Buyer: agent builders / platform teams / Claude Code users who want token-efficient, governed context
and tools inside their *own* agent — not a pipeline they operate on our surface. Domain: a new one
(working brand **"Context Enrichment"**; distinctive marks for later: *Strata · Substrate · Carrel*).
Full spec: [[context-enrichment-service.md]].

## The shared infrastructure plane (the substrate both ride on)

| Shared (one source of truth, never forked) | Detail |
|---|---|
| **Compute** | K8s clusters, worker pools, GPU inference (vLLM), autoscaling |
| **Engine** | the recipe/foundry, model adapters, the lift/eval harness, CDC/freshness |
| **Data plane** | the component catalog + the governed corpora + the vector store (pgvector) |
| **Governance** | provenance, lineage, ID/hash discipline, signed attestations, promotion boundary |
| **Tooling / CI** | validate/build scripts, schemas, vocabularies, the seven-primitive grammar |

**Per-service (the thin top):** the front-end/surface, the service-specific API, the billing meter,
the brand/domain. OHH's surface is the builder + monitor; CEaaS's surface is a content/corpus console
+ download + **MCP endpoints**. Both call the *same* engine and read the *same* data plane.

## Why share the infra (the whole point)

The expensive parts — the clusters, the workers, the corpora, the compression/eval engine, the
governance — are **identical cost centers** for both services. Compressing a corpus for a CEaaS user
and compressing a corpus inside an OHH pipeline run the same `llmlingua-compress` /
`extractive-span-selector` / `memory/*` components on the same workers against the same store. Forking
that would double COGS for no benefit. Sharing it means a feature built for one service
(a better compressor, a fresher corpus, a new tool) is **instantly available to the other** — which
is exactly why the data plane must be **attribute-level, not column-level**
([[../codex/schema-extensibility.md]]): a facet added for CEaaS is a row both services read, never a
column one service's loader knows about.

## Acquisition read

"One governed engine + corpora + compute, two proven GTMs (build-a-pipeline **and** enrich-any-agent)"
is a stronger story than either alone: the acquirer gets the context-layer substrate
([[context-layer-pmf.md]]) *and* two distinct distribution surfaces onto it, with shared COGS.

## Shipped this turn vs. next (honest)

**Shipped:** this decision record; the CEaaS product spec ([[context-enrichment-service.md]]); the
schema-extensibility codex ([[../codex/schema-extensibility.md]]); `web/products.js` (two-product
config + host resolver — single source of truth for both brands); the `/context-enrichment` landing
surface (CEaaS's home, reusing the shared backend); a cross-link between the two services.

**Next (deployment, not forks):** (a) the CEaaS **content-tier pipeline** (raw→compressed→hyper-efficient,
hosted + downloadable) on the shared workers; (b) the CEaaS **MCP serving endpoint** that drops the
governed corpora + tools into Claude Code / open agent loops; (c) the shared **K8s/worker** deployment
the two services share; (d) rebrand the shared surface headers via `OHH.brand()` (touches ~17 files —
one reviewed pass, keep the live OHH surface green).
