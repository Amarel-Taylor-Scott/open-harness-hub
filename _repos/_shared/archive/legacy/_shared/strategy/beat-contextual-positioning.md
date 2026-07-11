# Beating Contextual AI — profile + positioning

Companion to [[competitor-contextual-ai.md]] (the engine/Agent-Composer analysis). This is the
**go-to-market positioning**: who Contextual is, why a head-on RAG fight is unwinnable, and the durable
wedges. Sources are the owner's multi-source research thread (businesswire, Yahoo Finance, contextual.ai
docs, Snowflake, ILO/EU/SEC, RAG-sentiment studies) + [[competitor-contextual-ai.md]]; treat figures as
directional and re-confirm before external use.

## The crisp position
**"Verified, current, provable context — for the agent you already run."** Category = **context
assurance + governance, upstream of and adjacent to RAG** — not "better RAG agents." That sentence puts
us in a room Contextual isn't standing in, instead of a benchmark fight we lose.

## Company profile (Contextual AI)
- **Founded:** out of stealth **June 2023** (seed ~April 2023). Palo Alto → San Francisco / Mountain View.
- **Founders:** **Douwe Kiela** (CEO — pioneered RAG at Meta FAIR, 2020; ex-Head of Research, Hugging
  Face; Stanford adjunct) + **Amanpreet Singh** (CTO — research engineering lead, Hugging Face / Meta
  FAIR). *The founder literally co-invented the technique we'd be competing on.*
- **Funding (~$100M, two rounds):** **Seed $20M** led by Bain Capital Ventures (Lightspeed, Greycroft,
  SV Angel; angels incl. Elad Gil, Lip-Bu Tan, Sarah Guo, Amjad Masad, Nathan Benaich). **Series A $80M**
  led by Greycroft (Bain, Lightspeed); PitchBook est. ~$609M post-money. Strategic investors are the tell:
  **Bezos Expeditions, NVentures (Nvidia), HSBC Ventures, Snowflake Ventures**; Greycroft's Marcie Vu on
  the board.
- **Size:** ~**51–100** employees (Mountain View).
- **Products:** the **Contextual AI Platform** (RAG 2.0 — jointly-optimized retriever+generator, ~4×
  accuracy, sentence-level attributions + visual bounding boxes); the **Grounded Language Model (GLM)**
  (on Llama 3.3); an **instruction-following reranker**; **LMUnit** (eval, open-sourced Jul 2025); the
  no-code **Agent Composer** (launched Jan 2026); **Datastores** (managed per-tenant vector stores) +
  some curated **Global Datastores** (e.g. arXiv Materials Science). GA Jan 2025.
- **Customers:** **Qualcomm** (customer engineering), **HSBC**; document-heavy, regulated Fortune 500.
- **Startup programs:** **none** — venture-from-stealth with tier-1 VCs + strategic corporates. A
  different funding tier than an accelerator/credits play.

## Why head-on is the wrong goal
We will not out-RAG the person who invented RAG, with Nvidia + Bezos money and a benchmark-leading
fine-tuned grounding model. "Beat Contextual" must mean **own a job they structurally don't do, for a
buyer they don't serve, and sit *upstream* of them** — verify/govern the corpus, then feed it into
whatever retrieval stack the customer runs (turning the threat into a channel, and us into an
acquisition target rather than roadkill).

## The corpus question, settled
Contextual **does** manage corpora — both (a) **per-tenant managed vector stores** (the "Building
Database" step ingests *your* docs; connectors: Box/Confluence/Drive/OneDrive/SharePoint, MCP, scheduled
ingestion) and (b) a few **curated Global Datastores** (arXiv materials science behind the demo). So
"we host/manage corpora" is **not** a wedge — table stakes they own. **But the *kind* of corpus object
differs**, and that is the moat:
- **Not portable/neutral** — their store feeds *their* GLM. Ours is a governed, multi-tier
  (raw→compressed→hyper-efficient) artifact served into the customer's **own** agent (Claude Code/Codex)
  over MCP, no re-platforming.
- **Their "freshness" = sync, not verification** — scheduled ingestion keeps the store in step with the
  source; it never asks whether the *source itself* is stale or wrong. Ours = **adversarial verification
  against external authoritative sources + human-in-the-loop** ("is this corpus still true?").
- **Not a compliance artifact** — they give in-product citations; we emit a **portable, regulator-facing**
  audit trail (AIBOM/CycloneDX, EU-AI-Act docs, a measured-fidelity record).
- **No commons** — datastores are private, per-tenant, agent-bound. **No cross-tenant sharing, no
  oracle/government-publisher program, no corpus marketplace.**

## The three durable wedges (each cuts against their incentives, not just their backlog)
1. **Audit the corpus, not just ground the answer** — *context assurance* as a category. "Contextual
   makes the answer faithful to your documents. **We make sure your documents aren't wrong.**"
2. **Agent- and model-neutral; serve into the agent they already run** — verified, governed, token-
   efficient context into Claude Code/Codex/Cursor over MCP, *against* their GLM lock-in. They can't
   chase this without undermining their platform play.
3. **Make the artifact a compliance deliverable** — portable AIBOM/EU-AI-Act/measured-fidelity records
   for AML, GxP, customs, food/water safety. The deliverable is the provable audit trail, not the chat.

## Sit UPSTREAM — the real play (be the layer they buy FROM)
The strongest frame isn't "beat Contextual," it's **"be the verified-corpus layer Contextual and
everyone else buys from."** Three stances, all viable, none a head-on RAG fight:
1. **Supplier INTO their customers (primary).** Their customers ingest their *own* data and can't
   manufacture verified regulatory corpora. We push signed, current, verified corpora into the customer's
   Contextual datastore via the **same ingest API** (exactly how AP / CB Insights publish into Snowflake).
   They keep the answer faithful to the corpus; **we guarantee the corpus is right.** Rides their sales motion.
2. **Customer OF Contextual (de-risk).** For any end-user answering *we* do, run our verified corpora
   through *their* RAG/GLM rather than rebuild RAG 2.0. Buy the commodity (retrieval+generation), keep the
   value (verification+freshness+provenance). Kills the temptation to over-build what they're funded to win.
3. **Neutral arms-dealer above ALL RAG (long game).** The same verified corpus feeds Contextual,
   Snowflake, Databricks, raw pgvector, **and** Claude Code. Never pick which RAG wins — supply them all.
   The **verified-ore supplier**; profit from everyone's growth.

**Strategic logic in one line:** competing on RAG = losing; **sitting upstream = we win when they win,
and when anyone else wins.** **Moat (not the tech):** (a) oracle-publisher *relationships* (a regulator/NGO
signing our corpus isn't cloned overnight), (b) the operational muscle of adversarial verification + HITL,
(c) depth in domains they'd never prioritize. Guard: never let one platform's ingest API be the only
channel (that's why stance 3 exists).

## Orchestration is TABLE STAKES — the moat is orthogonal (+ the naming call)
**Factual correction — do NOT anchor here:** Contextual shipped **Agent Composer (Jan 2026)** — multi-step
reasoning, a tool library (plan / retrieve / ingest / act / eval / memory), guardrails, stateful context.
**They are building the harness/orchestration layer.** So "we have logic + actions, they only retrieve" is
**eroding** — it must NOT be the pitch. (Update from the Jan-2026 launch: Agent Composer ships a
**Task Execution** pre-built agent that *executes API write actions across enterprise systems*, plus
multi-tool orchestration, three build paths (pre-built / from-prompt / drag-drop canvas), and it's
**model-agnostic** — so even "we have actions, they don't" is eroding. Their actions stay curated and
grounding-centric inside their context layer; *general* automation is still Composio/Make/MCP — but do
NOT pitch "they only retrieve" or "we orchestrate, they don't." Build-UX + orchestration + actions are
now table stakes they have.)
**The durable moat is ORTHOGONAL to orchestration** — the two things they structurally won't match:
(1) **open / portable / low-end** (OHH for the devs they treat as a funnel), and (2) **verified context**
(Baltor checking the corpus vs authoritative truth). Orchestration is becoming commodity; *whose context is
provably correct* is not.

**Naming (the call): keep "OpenHubForAI" — do NOT rename to "Open Agent Hub."** The whole two-product
split depends on the harness-vs-agent line (OHH = the *bounded, governed harness*; Baltor serves verified
context *into* open agents); "Open Agent Hub" collapses it and drops us into the most crowded, commoditizing
category (LangGraph/CrewAI/AutoGPT). "Harness" is distinctive + precise for technical buyers (and "eval
harness"/"agent harness" are established terms — lineage, not liability). **But use "agent" in taglines /
positioning / SEO** for findability — distinctive name for the *what*, popular word for *discoverability*:
e.g. *"OpenHubForAI — governed agents you can actually trust"* / "the governance layer for agents."
Bridge term when "harness" needs a gloss: **"governed agents."** Reversible (brand is config).

## The demand is real (RAG-failure sentiment)
- **62%** of enterprise RAG deployments hit hallucination incidents **at least weekly**.
- **58%** update their vector indexes **monthly or less** (a bot recommended a wire-transfer limit a
  regulation had *lowered two weeks earlier* — the stale value still sat in a cached index).
- **Adversarial:** a planted fake policy "superseding" a real rule was retrieved + cited as authoritative
  in **8 of 12** cases (BadRAG / TrojanRAG poisoning); "inability to explain answers to auditors" is a
  named production gap.
These validate context-assurance + adversarial-verification + compliance-artifact directly.

## The real category competitor (not Contextual)
"Shared, governed corpora served to agents" isn't empty — it's the **hyperscaler data marketplaces**
(Snowflake Marketplace lists AP, USA Today, CB Insights as AI-ready providers; Databricks/Google/MSFT
similar). So don't pitch "a corpus marketplace" generically — late. **OHH's specific, open lane:**
- **Esoteric / social-impact / regulated domains the marketplaces ignore** — migrant-worker rights &
  forced labor (CSDDD, EU Forced-Labour Regulation enforce Dec 14 2027, ILO), food/water safety, customs.
- **Oracle publishers + adversarial verification** — governments/standards bodies publish; the corpus is
  continuously verified against external truth with provenance (C2PA/W3C-VC). Nobody runs this.
- **Capability-gap closing** — the foundry mines where corpora are missing and generates to fill them.
- **Model-agnostic serving into open agents**, outside any cloud perimeter, in tiered downloadable form.

## Build targets the research surfaced
- **Integration/ingestion:** Fivetran, **Airbyte** (Agent Engine + PyAirbyte MCP server — permission-aware
  data-for-agents), Unstructured.io, LlamaHub, Composio — wrap as governed connectors (we already have
  MCP Confluence/GitLab/Postgres seeds).
- **Oracle/authoritative sources (machine-readable, mandated):** EU Open Data Directive high-value
  datasets (APIs + bulk), **EUR-Lex** JSON API (all EU law back to 1951), **SEC EDGAR**, ILO conventions,
  FATF 40 Recommendations, EUDR/LkSG. Provenance: **C2PA** cryptographic content credentials.

## What to STOP doing
Don't benchmark retrieval/rerank against them; don't enter the multimodal-parsing arms race; don't call
ourselves "specialized RAG agents"; **don't build a GLM**. Each meets them where they're strongest.
Wrap their Component APIs (Parse/Rerank/GLM/LMUnit) as governed measured-lift adapters
([[competitor-contextual-ai.md]]); compete only on assurance + governance + the oracle/social-impact
corpus commons + agent-neutral serving.

---
*warrant: corroboration — the owner's cited multi-source research (businesswire, Yahoo Finance,
contextual.ai docs, Snowflake, ILO/EU/SEC, RAG-sentiment studies) + [[competitor-contextual-ai.md]]
(adversarially verified). Figures directional; re-confirm before external publication.*
