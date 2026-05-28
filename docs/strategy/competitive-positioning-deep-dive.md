# Competitive Positioning Deep-Dive — Compete & Integrate

Extends [`competitive-swot.md`](competitive-swot.md). For each player: what it is,
where it's strong, **how we compete** (our wedge), and **how we integrate**
(interoperate, don't fight — be the capability-lift component layer behind their
canvas/agent/hub). Our durable edge across all three: a governed registry of
components admitted only if they **lift an LLM beyond what it can do alone**,
**automatically composed** into a costed, model-portable, deployable flow with
provenance — nobody serves that layer.

---

## 1. Automation / iPaaS — move data between apps

These are mature integration networks (thousands of app connectors). They are
**not** AI-reasoning systems; their "AI steps" are thin wrappers around a model
call with zero curated knowledge, evals, or capability-lift.

### Zapier (+ Zapier AI / Agents)
- **Strong:** ~7k app connectors, huge SMB distribution, dead-simple triggers.
- **Compete:** they have no knowledge objects, no capability-lift bar, no
  provenance/evals; an "AI step" hallucinates with no grounding. We supply the
  *reasoning quality* they lack — grounded, benchmarked, governed components.
- **Integrate:** publish OHH flows as a **Zapier app / webhook action** ("run
  this governed pipeline"); Zapier handles the app plumbing, we handle the
  AI-reasoning step. Emit our components via MCP so Zapier's agent layer can call them.

### IFTTT
- **Strong:** consumer simplicity, device/IoT triggers.
- **Compete:** consumer toy for AI work; irrelevant to regulated/技术 use cases —
  not a real competitor, a different market.
- **Integrate:** low priority; a webhook action only if demand appears.

### Make (Integromat)
- **Strong:** powerful visual iPaaS, branching/iteration, prosumer/agency base.
- **Compete:** same gap — plumbing, not grounded reasoning. Agencies on Make are
  exactly our second-motion buyer (they build many client workflows).
- **Integrate:** an HTTP/MCP module so a Make scenario calls an OHH-built
  pipeline; co-sell to Make agencies as the "AI brain" for their scenarios.

### n8n (the closest framing)
- **Strong:** dev-friendly, **self-hostable**, fair-code license, fast-growing
  AI-workflow nodes, strong OSS community.
- **Compete:** n8n is a *blank canvas* — the user wires nodes and picks models
  with no guidance, no curated components, no evals, no cost/provenance. We are
  the **substrate + recommender** that fills the canvas intelligently.
- **Integrate (highest-value iPaaS play):** ship an **n8n community node**
  ("Open Harness Hub: paste a task → get/Run a flow") and export OHH pipelines
  as n8n workflow JSON. n8n executes; we decide *what* to build and *why*. This
  is the "be the component brain behind the canvas" strategy made concrete.

**iPaaS verdict:** not competitors to displace — **distribution channels**. They
own execution + connectors; we own the AI-reasoning component layer. Win by
being the embeddable brain, reachable via MCP + per-platform nodes/actions.

---

## 2. Cloud agent platforms — run/ground a model in one cloud

Build + ground + deploy agents, locked to one cloud's models and billing.

### Google Vertex AI Agent Builder
- **Strong:** managed grounding (Vertex Search over *your* data), Gemini
  integration, enterprise GCP footprint.
- **Compete:** grounds on the customer's *own* uploaded data — **not** a curated,
  cross-domain, capability-lift registry with provenance + benchmarks; locked to
  Google models (no neutral model-swap); no cross-org reusable component market.
- **Integrate:** deploy OHH-generated pipelines *to* Vertex (emit a Vertex/Cloud
  Run deployment bundle); offer our registry as the component source that fills a
  Vertex agent's tool/knowledge slots.

### AWS Bedrock Agents
- **Strong:** Bedrock model choice, Knowledge Bases, AWS-native security/IAM,
  huge enterprise base.
- **Compete:** Knowledge Bases = *your* docs, not a governed lift-gated registry;
  components aren't portable off AWS; no capability-lift admission bar.
- **Integrate:** export OHH flows as Bedrock Agent action-groups + a Terraform
  bundle; be the BYO-cloud, provider-neutral layer customers use to avoid lock-in
  *across* Bedrock/Vertex/Azure.

### Azure AI Studio / Foundry
- **Strong:** OpenAI models, prompt flow, enterprise Microsoft channel.
- **Compete:** same single-cloud lock-in + your-data grounding; prompt flow is a
  builder, not a curated component market.
- **Integrate:** emit prompt-flow-compatible exports; position OHH as the neutral
  registry feeding any of the three clouds.

**Cloud-platform verdict:** they win deployment + enterprise trust *inside one
cloud*; we win **neutrality + a real component registry + capability-lift evals**.
Compete on portability and the governed registry; integrate as the
deploy-target and the component source. Never try to out-cloud a hyperscaler.

---

## 3. AI dev hubs & builders — frameworks, prompts, models

The nearest neighbors; overlap is real but partial.

### LangChain Hub + LangSmith
- **Strong:** dominant framework mindshare, a community **prompt** hub, strong
  eval/observability (LangSmith).
- **Compete:** LangChain Hub = prompts, not governed capability-lift components
  (no provenance, no lift bar, no costed composition); LangSmith evals *your*
  app, it doesn't supply *what components to use*. Framework-coupled.
- **Integrate:** export OHH components as LangChain tools/runnables; let
  LangSmith trace flows we assemble. We own "which components + do they lift,"
  they own framework + observability — complementary.

### Dify / Flowise
- **Strong:** polished visual LLM-app builders, OSS, self-hostable, growing fast.
- **Compete:** blank-canvas builders — the user still picks everything; no
  curated registry, no lift bar, no provenance, no cost/model-swap intelligence.
  We *recommend and assemble*; they *let you draw*.
- **Integrate:** export to Dify/Flowise app JSON; offer OHH as the component
  catalog their canvases pull from; co-exist as the "intelligent fill" layer.

### Hugging Face Hub
- **Strong:** the registry for **models & datasets**, massive community, Spaces.
- **Compete:** HF indexes models/datasets, **not operational pipeline components
  with capability-lift evals + costed blueprints**. We sit a layer above (and
  already emit HF model cards). Closest "registry" analog but a different object.
- **Integrate (highest-value hub play):** publish OHH as a **HF Space** (the
  showcase), emit HF-compatible cards, and pull permissively-licensed models as
  adapters. HF is distribution + model supply; we are the pipeline-component layer.

**Dev-hub verdict:** complement, don't fight — we own the **governed,
lift-gated, auto-composed component layer** none of them have. Integrate via
exporters (LangChain tools, Dify/Flowise JSON, HF Spaces/cards) so we ride their
distribution while owning the differentiated layer.

---

## The one-line strategy

Across all nine players the move is the same: **interoperate as the embeddable,
provider-neutral, capability-lift component brain** — reachable by MCP and
per-platform exporters — rather than rebuild their canvas, connectors, or cloud.
We compete only on the layer none of them serve (governed, benchmarked,
auto-composed components) and integrate everywhere else. Priority integrations:
**MCP server** (universal agent access) → **n8n node** + **HF Space** (OSS
distribution) → **Bedrock/Vertex deploy bundles** (enterprise) → **LangChain
tool export** (developer reach).
