# Two services, one shared infrastructure plane (decision record)

> **Brand note (2026-05-29, locked — [[brand-architecture.md]]):** Service 2 below — the **Context Enrichment
> service / CEaaS** — is branded **Baltor.ai** (in prose: **Baltor**), with modules **Verify · Corpus ·
> Compress**. The company is **AI Done Right** (founding thesis: Context is Everything); **OpenHubForAI** (Service 1) keeps its
> name. "CEaaS" persists here and in code as the working/descriptive term for the same product.

**Decision (owner, 2026-05-29):** run **two separate products/platforms on two domains**, sharing
the **infrastructure plane** — clusters, K8s, worker pools, the engine, the component+corpus data
plane, tooling, governance. A lot of the compute and data is identical, so we share it: **one COGS,
two revenue lines.** The differentiation is the *surface*, the *buyer*, and the *billing* — not the
backend.

This is **not** one web app with a brand toggle (an earlier draft framed it that way — wrong). These
are two genuinely distinct services that happen to sit on the same substrate.

## The two services

### Service 1 — OpenHubForAI (build + monitor a pipeline)
*Build a governed pipeline and monitor it, with rules around input and output.* The seven-primitive
builder, the governed recipe, observability, the I/O gates. Buyer: builders / applied teams
assembling and operating AI pipelines. Domain: `openharnesshub.com`.

### Service 2 — Baltor.ai (the verified-context service)
A **content + corpus** service, not a pipeline builder. It:
- **compresses content and raises token efficiency** for users;
- **hosts content in three tiers — raw · compressed · hyper-efficient** — and lets users pull *or
  download* any tier;
- **serves the unique governed knowledge corpora + tools into open-ended agentic workflows** (Claude
  Code, MCP clients, any open agent loop) — so an agent gets token-dense, governed, cited context and
  tools dropped straight in.

Buyer: agent builders / platform teams / Claude Code users who want token-efficient, governed context
and tools inside their *own* agent — not a pipeline they operate on our surface. Brand: **Baltor.ai**
(`baltor.ai`, owned), modules **Verify · Corpus · Compress** — see [[brand-architecture.md]].
Full spec: [[context-enrichment-service.md]].

## One screen — the shared platform

```
   builders ──▶ ┌──────────────────────────┐   ┌──────────────────────────┐ ◀── agent devs
                │  OPEN HARNESS HUB         │   │ BALTOR                    │   (Claude Code,
                │  bounded                  │   │ unbounded                 │    Cursor, any
                │  • assemble DAG · run/trace│   │ • ingest content/corpora  │    MCP client)
                │  • registry · I/O rules   │   │ • tier: raw→compressed→   │
                │  • monitor + LIFT gate    │   │     hyper-efficient        │
                │                           │   │ • host / download          │
                │  sells: governed PIPELINES│   │ • 4 surfaces: MCP · llms.txt│
                │                           │   │     · skill · CLAUDE.md     │
                │                           │   │  sells: governed FUEL       │
                └────────────┬─────────────┘   └─────────────┬──────────────┘
                             │      two doors, one object     │
                             ▼                                ▼
                   ┌─────────────────────  THE JOIN  ─────────────────────┐
                   │  a governed Knowledge Corpus / tool — minted ONCE,    │
                   │  one provenance trail, one lift + fidelity score.     │
                   │  Wire it into a bounded pipeline, OR serve it to an    │
                   │  open agent. Every component is sellable through either│
                   │  door.                                                 │
                   └───────────────────────────┬──────────────────────────┘
                                                ▼
   ┌─────────────────────────  SHARED INFRASTRUCTURE PLANE  ──────────────────────────┐
   │  compute     K8s clusters · worker fleet · vLLM embed/inference · autoscaling     │
   │  engine      foundry (gap-mine + generate) · MEASUREMENT (lift + tier-fidelity)   │
   │  ingestion   connectors · source registry · normalization                        │
   │  storage     object store (raw) · pgvector (retrieval) · tiered-artifact store    │
   │  governance  provenance / AIBOM · citations · CDC / freshness · MCP plumbing      │
   │  billing     usage metering (per query · per GB · per refresh)                    │
   └──────────────────────────────────────────────────────────────────────────────────┘
```

The expensive parts are one set, shared. Only the two storefronts on top — and the consumption /
billing model — differ. The **join** is a single governed object consumed two ways.

## The shared infrastructure plane (the substrate both ride on)

| Shared (one source of truth, never forked) | Detail |
|---|---|
| **Compute** | K8s clusters, worker pools, GPU inference (vLLM), autoscaling |
| **Engine** | the recipe/foundry, model adapters, the lift/eval harness, CDC/freshness |
| **Data plane** | the component catalog + the governed corpora + the vector store (pgvector) |
| **Governance** | provenance, lineage, ID/hash discipline, signed attestations, promotion boundary |
| **Tooling / CI** | validate/build scripts, schemas, vocabularies, the seven-primitive grammar |

**Per-service (the thin top):** the front-end/surface, the service-specific API, the billing meter,
the brand/domain. OHH's surface is the builder + monitor; Baltor's surface is a content/corpus console
+ download + **MCP endpoints**. Both call the *same* engine and read the *same* data plane.

## Why share the infra (the whole point)

The expensive parts — the clusters, the workers, the corpora, the compression/eval engine, the
governance — are **identical cost centers** for both services. Compressing a corpus for a Baltor user
and compressing a corpus inside an OHH pipeline run the same `llmlingua-compress` /
`extractive-span-selector` / `memory/*` components on the same workers against the same store. Forking
that would double COGS for no benefit. Sharing it means a feature built for one service
(a better compressor, a fresher corpus, a new tool) is **instantly available to the other** — which
is exactly why the data plane must be **attribute-level, not column-level**
([[../codex/schema-extensibility.md]]): a facet added for Baltor is a row both services read, never a
column one service's loader knows about.

## Acquisition read

"One governed engine + corpora + compute, two proven GTMs (build-a-pipeline **and** enrich-any-agent)"
is a stronger story than either alone: the acquirer gets the context-layer substrate
([[context-layer-pmf.md]]) *and* two distinct distribution surfaces onto it, with shared COGS.

## Shipped this turn vs. next (honest)

**Shipped:** this decision record; the Baltor product spec ([[context-enrichment-service.md]]); the
schema-extensibility codex ([[../codex/schema-extensibility.md]]); **separate per-product front-end
folders** — `web/harness-hub/` and `web/baltor/`, each self-contained, with the backend
selecting the folder by `OH_PRODUCT` (`server.py`); both products live behind their own tunnels
(`scripts/serve_two_products.sh`); the backend service layer ([[../architecture/backend-services-and-platform.md]]).

> Note: an earlier draft shared one `web/` folder with a `products.js` brand toggle. That caused
> "confusion between the two product surfaces" and was **replaced** by the per-folder split above — the
> front-end is per-product; only the backend is shared.

**Next (deployment, not forks):** (a) the Baltor **content-tier pipeline** (raw→compressed→hyper-efficient,
hosted + downloadable) on the shared workers; (b) the Baltor **MCP serving endpoint** that drops the
governed corpora + tools into Claude Code / open agent loops; (c) the shared **K8s/worker** deployment
the two services share; (d) the Baltor **teal** sibling accent (a brand-scope within `dir-s` — same
typography, accent only; NOT a theme-direction change).
