# Baltor Cloud Cost, Pricing, And Pro Forma Plan

As of 2026-05-31, Baltor should price and operate like context-control
infrastructure, not like a generic chat seat product. The economic unit is:

```text
source monitored -> facts verified -> context package served -> downstream agent risk reduced
```

The plan below uses current public pricing signals and should be refreshed before
any customer quote, fundraising deck, or production architecture commitment.

## Cost Model

### Local And Demo

The default demo should remain cheap and local:

- static frontend or showcase server;
- SQLite queue/run fallback;
- local file artifacts;
- optional Docker Compose Redis/Postgres;
- Ollama/OpenAI-compatible local model endpoint;
- hosted frontier models only for explicit frontier lanes.

Target monthly cost:

| Environment | Target cost | Notes |
|---|---:|---|
| Local solo dev | $0-$50 | laptop + optional API calls |
| Public demo | $25-$150 | static hosting, small VM/API, object storage |
| Design-partner staging | $250-$1,500 | managed Postgres, queue, object storage, observability, small worker pool |

### Kubernetes Control Plane

Kubernetes is justified once worker pools, queue depth, GPU nodes, isolation, and
batch orchestration matter. It is not required for the first website demo.

Current anchor prices:

- Amazon EKS standard Kubernetes version support is listed at `$0.10 per cluster
  per hour`; extended support is listed at `$0.60 per cluster per hour`
  ([AWS EKS pricing](https://aws.amazon.com/eks/pricing/)).
- GKE uses a `US$0.10/hour per cluster` management-fee basis in its pricing
  examples ([GKE pricing](https://cloud.google.com/kubernetes-engine/pricing)).

Implication:

| Cluster pattern | Monthly control-plane floor | Recommendation |
|---|---:|---|
| One shared staging/prod cluster | about $74/cluster before nodes | acceptable once workers matter |
| Separate cluster per tenant | multiplies quickly | avoid until enterprise isolation requires it |
| Old EKS versions | about 6x standard support cluster fee | enforce upgrade policy |

### Worker Compute

Use worker lanes with separate scaling and cost controls:

| Lane | Default runtime | Cost policy |
|---|---|---|
| CPU parse/chunk/extract | serverless jobs or small K8s CPU nodes | batch, scale to zero when possible |
| Research/browser | K8s/KEDA or Cloud Run jobs | cap concurrency per tenant and domain |
| Audit/trust | small CPU workers + occasional frontier calls | prioritize high-risk facts |
| Embedding | local GPU, managed embedding API, or batch CPU/GPU | batch by source version |
| Frontier verifier | OpenAI-compatible hosted API | rare, budgeted, ledgered |
| GPU enrichment | K8s GPU node pool or managed batch GPU | only when queue backlog justifies node spin-up |

KEDA is a good default for event-driven Kubernetes workers because it scales
containers based on event sources and includes scalers for SQS, Cloud Tasks,
Pub/Sub, storage queues, PostgreSQL, Redis lists, and other queues
([KEDA](https://keda.sh/)). Argo is the right fit for large bounded DAGs because
it is a container-native Kubernetes workflow engine for parallel jobs and DAGs
([Argo Workflows](https://argoproj.github.io/workflows/)).

### Model And Retrieval Costs

Current OpenAI public pricing shows why Baltor needs cheapest-first routing:

- GPT-5.5: `$5.00 / 1M` input tokens, `$0.50 / 1M` cached input tokens, and
  `$30.00 / 1M` output tokens.
- GPT-5.4 mini: `$0.75 / 1M` input tokens, `$0.075 / 1M` cached input tokens,
  and `$4.50 / 1M` output tokens.
- Web search tool: `$10.00 / 1k calls`; Batch API can save 50% for async work
  ([OpenAI pricing](https://openai.com/api/pricing/)).

Pinecone's public pricing page is useful as a vector/RAG cost benchmark: it
lists assistant storage at `$3/GB/mo`, embedding inference at `$0.08-$0.16/M`
tokens depending on model, reranking at `$2/1k` requests, and ingestion units at
`$0.0005` each for text ([Pinecone pricing](https://www.pinecone.io/pricing/)).

Baltor should therefore:

- prefer deterministic extraction and local small models for first-pass work;
- batch nonurgent frontier verification;
- exploit cached/prefix-token economics through canonical prompts;
- store per-run token, search, browser, embedding, and worker-second costs;
- expose estimated cost before a tenant launches a large corpus refresh.

## Pricing Architecture

Do not price only by user seat. Seats underprice the work Baltor performs and
hide the cost of search/model/worker-heavy verification.

Recommended meters:

| Meter | Why it matters |
|---|---|
| Monitored sources | maps to sync/version/diff workload |
| Documents/pages processed | maps to parse/chunk/embedding load |
| Facts under management | maps to lifecycle state and refresh burden |
| Verification jobs | maps to research/model/tool costs |
| Served context packages | maps to downstream production value |
| Premium public context feeds | maps to Baltor-owned leverage |
| Frontier/model overage | protects margin |

### Initial Tiers

| Tier | Price target | Included |
|---|---:|---|
| Design partner pilot | $5k-$25k fixed | 2-6 weeks, 1 corpus, 1-2 authority feeds, before/after report |
| Team | $1.5k-$3k/mo | small source set, local/light hosted verification, limited exports |
| Business | $6k-$15k/mo | scheduled sync, multi-source verification, package serving, audit exports |
| Enterprise | $40k+/yr minimum, often $75k-$250k ACV | private deployment, SSO, custom connectors, source policies, SLAs |

Usage overages should attach to:

- verified facts beyond tier;
- high-volume document processing;
- browser/search refresh jobs;
- frontier model calls;
- dedicated GPU/batch runs;
- private authority-feed maintenance.

## Competitor Map

The market is crowded, but Baltor can avoid sounding like a duplicate by owning
the verified-context control layer.

| Category | Examples | Their center | Baltor wedge |
|---|---|---|---|
| Enterprise search/work AI | Glean, Microsoft, Google | search, assistant UX, connectors | verify and package facts before agents use them |
| Enterprise RAG platforms | Contextual AI, Ragie, deepset/Haystack | retrieval, RAG agents, indexing | lifecycle-managed fact state, source adoption policy, provenance exports |
| Vector databases | Pinecone, Weaviate, Milvus, pgvector | retrieval substrate | upstream quality and refresh controls |
| Knowledge graphs | Neo4j, TigerGraph, Stardog | graph storage/query | operational worker loop that keeps graph facts current |
| GRC/compliance tools | ServiceNow GRC, Archer, Vanta/Drata | controls and evidence workflows | machine-readable context packages for agents |
| Web/source intelligence | Diffbot, Meltwater, AlphaSense, Perplexity Enterprise | external source search/monitoring | verified adoption into customer context with history |
| Internal AI platform teams | customer-built RAG/agent stacks | custom infrastructure | buy/partner for the hard source lifecycle layer |

The strongest position:

> Baltor keeps enterprise agent context verified, current, reconciled,
> traceable, and ready to serve.

## Pro Forma Scenarios

These are planning assumptions, not forecasts.

| Scenario | Month 12 | Month 24 | Month 36 |
|---|---:|---:|---:|
| Conservative ARR | $180k | $750k | $1.8M |
| Base ARR | $350k | $1.8M | $5.0M |
| Upside ARR | $750k | $4.0M | $12.0M |

Base-case customer mix:

| Period | Customers | ACV assumption | Notes |
|---|---:|---:|---|
| Month 12 | 3-6 | $50k-$75k | paid pilots convert to first annuals |
| Month 24 | 12-20 | $75k-$120k | compliance/procurement wedge repeats |
| Month 36 | 35-55 | $100k-$180k | expansion from sources/facts/packages |

Target gross margin:

- early pilots: 40%-60% because services and frontier calls are high;
- repeatable hosted product: 70%-80%;
- enterprise/private deployment: margin depends on support and connector work;
- public context feeds: highest-margin if reused across customers.

COGS rules:

- model/search/browser spend should stay below 10%-20% of recurring revenue;
- worker compute and storage should stay below 10% in steady state;
- implementation labor should be priced into pilots and enterprise onboarding;
- every expensive Hermes/OpenClaw discovery should produce a cheaper rule,
  query, connector, parser, or deterministic worker.

## Marketing And Sales Budget

First six months should stay founder-led and proof-heavy:

| Activity | Monthly budget | Goal |
|---|---:|---|
| Founder-led outbound | $0-$500 | 20-50 targeted accounts/week |
| Technical content | $0-$1,500 | publish demos, teardown posts, context-control essays |
| Design partner demos | $500-$2,000 | produce vertical-specific proof |
| CRM/email/domain/tools | $100-$500 | basic sales ops |
| Events/webinars | $0-$3,000 | only where compliance/procurement buyers are concentrated |

Do not spend heavily on broad paid ads before there is a repeatable vertical.
The first budget should buy proof: case studies, benchmark reports, demo
corpora, and credible security/provenance collateral.

## Fundraising Operating Plan

Raise seriously after at least one of these is true:

- one paid pilot has exported a package used by a real downstream agent/RAG
  system;
- three design partners have supplied real corpora;
- Baltor can quantify stale/weak facts caught and manual confirmations avoided;
- a repeatable compliance/vendor-risk demo closes meetings reliably.

Seed narrative:

1. Enterprise agents fail when their context is stale, weak, unverifiable, or not
   packaged for consumption.
2. Baltor is the control layer that continuously syncs, versions, verifies,
   reconciles, and serves context.
3. Open Harness Hub creates the open standards and developer funnel.
4. Context Is Everything owns the category narrative.
5. The moat is the worker/procedure loop: expensive nondeterministic resolution
   becomes deterministic infrastructure over time.

Use of funds:

- connectors and source monitoring;
- worker registry/orchestration;
- source trust and adoption policy;
- verified public context feeds;
- local/cloud deployment hardening;
- security baseline;
- design-partner success and founder-led GTM.

## Near-Term Actions

1. Add this cost model to the investor/customer diligence packet.
2. Build a simple cost calculator for `/admin-demo`: documents, facts, searches,
   model tier, package outputs.
3. Add run-level cost fields to worker outputs and ledger records.
4. Add tenant budget caps and lane-level concurrency limits.
5. Add a cloud provider matrix for AWS/GCP/Azure/local with serverless and K8s
   alternatives.
6. Refresh competitor and pricing links before every fundraising or sales push.
