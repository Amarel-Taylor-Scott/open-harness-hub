# Product, Market, and Monetization Brief

Open Harness Hub is a registry and generation platform for reusable AI pipeline
components. It helps users move from "I need an AI workflow" to a deployable,
priced, evaluated, and maintainable pipeline.

## The Problem

Most organizations do not need a generic chatbot. They need repeatable AI
systems that combine source retrieval, private data handling, rules, model
routing, tools, RAG, citations, evaluation, human review, deployment, and cost
controls.

Today, teams rebuild these pieces repeatedly. They also struggle to know which
model, tool, retrieval method, runtime, or safety gate to use. Generic agent
builders make users configure agents manually; model providers optimize for
model calls rather than reusable operational components.

## The Product

Open Harness Hub standardizes and indexes:

- harnesses, pipelines, tools, rule packs, and RAG packs;
- prompts, prompt templates, procedures, and question sets;
- evaluation rubrics, benchmarks, and deployment blueprints;
- model adapters and cost-routing policies;
- source surfaces, signed knowledge objects, and verified facts;
- trajectory fragments from solved prior work.

The SaaS version lets a user describe a task, hosting environment, privacy
boundary, budget, and quality target. It returns cheap, balanced, and
quality-first pipeline options with expected costs, risks, deployment files,
runtime choices, evals, and review gates.

## Positioning — the capability-lift bar (what makes this defensible)

**One sentence:** the only registry that admits a component *only if it measurably
lifts capability beyond a bare LLM*, keeps it source-governed, and composes it
into a costed, model-portable, deployable pipeline.

This is the core discipline, not a tagline. A component earns a place only when
`pipeline_score − bare_model_score > 0` on a real task. Everything a frontier
model already does well zero-shot is **out of scope by design**. That keeps the
catalog small where it should be and deep where it matters: the esoteric,
specialized, verifiable, fast-changing arenas where base models are weak and a
grounded, structured pipeline wins — which is exactly where buyers have budget
and where reuse compounds. See [`docs/codex/master-goal.md`](../codex/master-goal.md).

## Product-Market Fit Hypothesis

The strongest early users are teams that repeatedly build LLM workflows under
cost, compliance, privacy, or deployment constraints:

- AI consultants and agencies building client workflows;
- compliance, risk, AML, safety, and audit teams;
- SaaS companies adding AI features;
- operations teams converting procedures into AI-assisted checklists;
- public-sector and nonprofit teams with forms, policies, and eligibility
  workflows;
- developer-tool teams running long agentic coding or ingestion jobs;
- enterprises that need private, BYO-cloud, or tenant-isolated AI pipelines.

The buying trigger is usually one of:

- "We need an LLM workflow but do not know the architecture."
- "We need this cheaper than frontier-model-only prompting."
- "We need proof, citations, and review trails."
- "We need to swap models as pricing and capabilities change."
- "We need to deploy in our own environment."
- "We have hundreds of procedures to convert into AI workflows."

## Go-to-market: the wedge (start narrow, prove the lift)

A market is not a wedge. The sharpest beachhead is **compliance / risk / audit
teams in regulated, esoteric domains** (ESG/CSDDD, GxP, customs & trade,
sanctions/AML, food/water safety):

1. **The lift is largest and most provable here.** A bare model cannot reliably
   cite CSDDD articles, apply ILO forced-labor indicators across languages, or
   hold a deterministic review gate — the benchmark delta is obvious and
   defensible. This is the capability-lift bar at its strongest.
2. **They pay, and they need exactly what we uniquely offer:** proof, citations,
   provenance, review trails, signed facts, and revocation — not "ask the model."
3. **We already have the deepest assets here** (the live-tested ESG/CSDDD
   vertical, GxP/customs/sanctions seeds), so time-to-first-value is short.

Second motion: **AI consultants/agencies**, who build many client workflows and
buy reuse + costed blueprints + private registries. Land in regulated compliance,
expand to the agencies who serve them.

## Differentiation

Open Harness Hub is not just an agent builder. It focuses on reusable
components, source-governed knowledge objects, ratings, evals, cost-aware model
routing, deployment blueprints, trajectory reuse, and private registries — all
behind the capability-lift bar.

## Competitive landscape

| Category | Examples | How we differ |
|---|---|---|
| Prompt hubs + LLMOps eval/observability | LangChain Hub / LangSmith, Humanloop, Vellum, PromptLayer, Braintrust, Arize Phoenix | They manage *your* prompts/evals and observe runs; we supply *reusable, source-governed, benchmarked components* and compose them into costed, deployable pipelines. Often framework-coupled; we are framework- and provider-neutral. Complementary — we own the "which components, and do they lift capability" layer. |
| Visual agent / workflow builders | Dify, Flowise, Langflow, n8n | They make a user *configure* an agent on a blank canvas; we *retrieve and assemble* from a governed registry and return the cost, eval, and review shape. Build-tool vs. substrate + recommender. |
| Model/dataset registries | Hugging Face Hub | Closest "registry" analog, but it indexes *models & datasets*, not *operational pipeline components with capability-lift evals + costed blueprints*. We sit a layer above (and emit HF cards). |
| Provider agent platforms | OpenAI GPTs/Assistants, Bedrock Agents, Vertex Agent Builder, MCP registries | Provider-locked and model-call-centric. We are provider-neutral with an explicit model-swap matrix and a BYO-cloud deployment path. |
| Awesome-lists / prompt libraries | curated GitHub lists | Ungoverned, no eval, no cost, no provenance. We are the governed, benchmarked, deployable version — and our gate rejects the same material as filler. |

## The moat

Three compounding layers, defended against the obvious objection — *"won't a
better model just do all of this?"*:

1. **The capability-lift gate is anti-fragile to model progress.** Every
   component targets where models are *weak*. As models improve, the gate prunes
   anything they have absorbed, so the registry stays parked on the moving
   frontier of *what models still can't do reliably* (long-tail facts, esoteric
   rules, verifiable procedures, fast-changing regulation).
2. **Governance a raw model cannot supply:** provenance, licensing, signed
   verified facts, citations, review trails, revocation/CDC for volatile facts,
   and privacy boundaries that travel with the component. This is the buying
   trigger for the wedge and is orthogonal to model quality.
3. **The experience database:** which compositions actually work, at what cost,
   with which model — millions of components, fragments, evals, and deployment
   traces that make the next workflow faster and cheaper to assemble. Plus
   operational value independent of any model: portability/model-swap and
   one-command deployable blueprints.

## Sources & supply: governed ingestion (incl. OSS ecosystems)

Supply scales through **source surfaces**, not hand-authoring. Each surface is
license-filtered, normalized, fuzzy-deduped, attributed (`source_url` + author +
license), embedded, and routed to review when uncertain — then passed through the
capability-lift gate before anything is promoted.

- **OSS ecosystems (GitHub repos) are a source surface, not a new component
  type.** A repo is ingested as `source_kind: github_repo` and yields *instances*
  of existing types (a tool, adapter, or pattern) — only when it adds capability
  (model runtimes, agent frameworks, RAG/scraping engines, memory layers). General
  developer-education repos (learn-to-code lists, web frameworks) fail the bar and
  are not cataloged. This doubles as a monetization line (**managed ingestion**).
- Other surfaces: standards/regulatory corpora, public-sector procedures, Kaggle
  competition tasks (which double as the conversational builder's benchmark set).

## Monetization Channels (sequenced)

**First dollar (wedge):** Pro/Team subscriptions for a *private registry +
task-to-costed-blueprint*, plus paid **managed ingestion** of a customer's
procedure library or an OSS ecosystem into capability-lift components. These need
only the MVP, not a billion public rows.

**Expansion:** usage-based billing (source scans, embeddings, LLM polishing, eval
runs, browser workers, generated deployment bundles); private tenant registries;
verified-publisher accounts (agencies, standards bodies, governments, domain
experts); marketplace revenue share on premium components; API access to search,
recommendation, pricing, and pipeline-generation; cost/performance analytics.

**Enterprise:** BYO-cloud/VPC/air-gapped deployment packages; support, compliance
review, and custom benchmark packages.

### Pricing & packaging (illustrative anchors, validate against real runs)

| Tier | Who | Indicative price | Includes |
|---|---|---|---|
| **Free / OSS** | individuals, evaluation | $0 | public catalog, CLI, self-host, browse + emit (Croissant/MCP/HF/…), acquisition surface |
| **Pro** | solo builders, consultants | ~$29–49 / seat / mo | private workspace, task-to-blueprint, costed plans, hybrid search, monthly usage credits |
| **Team** | agencies, product teams | ~$199–499 / mo | private registry, more credits, eval + review scaffolding, collaboration, ratings/telemetry |
| **Enterprise** | regulated orgs | custom | private tenant index, BYO-cloud/VPC/air-gap, verified publishing, audit export, SSO, support, compliance packages |
| **Usage add-ons** | all paid | metered | source scans, embeddings, eval runs, media gen, managed ingestion jobs |

## Cost Advantage

The platform should reduce cost by:

- using rules, retrieval, and deterministic checks before model calls;
- routing low-risk work to local or cheap models;
- standardizing prompts and schemas to improve prefix-cache reuse;
- storing trajectory fragments from solved subproblems;
- reusing verified tool-call sequences and review gates;
- batching embeddings and warehouse exports;
- promoting only high-value objects into hot indexes;
- keeping raw snapshots in cheap object storage.

The long-term advantage is an experience database: millions of reusable
pipeline objects, fragments, examples, evals, and deployment traces that make
future workflows faster and cheaper to assemble.

## MVP

The first sellable product can be:

1. searchable private component registry;
2. task-to-pipeline recommendation;
3. cheap, balanced, and quality-first costed blueprints;
4. Postgres/pgvector storage;
5. Render or Cloud Run workers;
6. object storage for snapshots and shards;
7. exportable runtime, Terraform, and MCP bundle;
8. evaluation and review-ticket scaffolding.

The MVP does not need one million public objects. It needs a credible path for
generating, validating, indexing, and privately managing them — and a few dozen
*capability-lift* blueprints in the wedge domain that visibly beat a bare model.

### Where this stands today (reality anchor)

The product maps to the phases in [`master-goal.md`](../codex/master-goal.md): the
spec, schemas, ~530 curated components, the factory tooling, and the costed
hosting plan exist (P0); the running foundation — real embeddings, hybrid search,
the conversational builder — is the current build (P1–P3); the MVP above is P4.
Hosting starts ~$40–87/mo (Cloudflare Pages + Neon pgvector + Render worker + R2)
and scales to the billion tier only after the wedge is validated.

## Risks (with mitigations)

| Risk | Mitigation |
|---|---|
| Exposing strategic ideation before the product is ready | Keep deep strategy in-repo; ship the wedge product, not the manifesto. |
| Ingesting sources without licensing/provenance/privacy controls | Source-governance spine: license filter, attribution, review routing, synthetic/public metadata only. |
| Turning every generated row into a public file instead of using the DB | DB-backed rows + JSONL staging; the capability-lift gate culls filler (it already removed ~1,980 padded candidates). |
| Over-reliance on one model/provider | Provider-neutral adapters + model-swap matrix as a first-class feature. |
| Overbuilding infra before validating the buyer | Wedge-first; MVP is P4; hold the billion-tier infra until the wedge pays. |
| Weak evals making pipelines look safer than they are | Capability-lift bar *is* a benchmark delta; promotion blocked without real evals + review. |

## Near-Term Validation

Useful validation loops:

- build 20-50 high-value pipeline blueprints for real workflow categories
  (start in the wedge domain where the lift is provable);
- test cost estimates against actual runs;
- show consultants and ops teams the task-to-blueprint experience;
- measure how often retrieved components reduce design time;
- measure cache and prompt-standardization savings;
- run private ingestion on public procedure sources and OSS ecosystems;
- compare against generic agent builders and cloud agent platforms — on the
  capability-lift delta, not feature count.
