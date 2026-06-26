# Marketing & Messaging — AI Done Right

Canonical positioning and copy for the brand family. Source of truth for product/brand
*identity* is `shared/products.js`; this file is the human-readable messaging guide (use it
for site copy, sales decks, and onboarding). When a brand name/tagline changes, change it in
`products.js` first, then reconcile here.

---

## Company — AI Done Right
- **Mission / company line:** *AI, done right.*
- **Thesis:** *Models are commoditizing; trustworthy, governed AI capability is the moat — discovery is not trust.*
- **What it is:** an **AI platform company** / portfolio. A **house of brands** — governed
  products (the moat) on an open registry funnel (lead-gen). Legal entity: AI Done Right, Inc.
- **Architecture story (top → bottom):** governed **Products** you run (Baltor, Teleon) sit on
  top of an **Open network** — context, skills, tools, conversion, MCP, compression, benchmark,
  review and harness registries (9 live), plus a **private bench** (templates, endpoints, eval
  environments, sandboxes, agent runtimes, receipts, state) that opens as competitors appear.
- **Capability lifecycle spine (used in the parent diagram):**
  Purpose → Contract → Runtime selection → Candidate → Evidence → Eval-gated promotion / rollback.
- **How value flows (ports):**
  - Baltor → Teleon via `PurposeTaskProviderPort` (Teleon returns evidence / candidate / result, **never** Baltor's own truth/data).
  - Teleon → the open hubs (draws templates, skills & eval packs).

---

## Baltor.ai — paid context-assurance SaaS (the moat)
- **Tagline:** Context assurance for AI agents.
- **Primary hook (locked 2026-05-29):** *It's not the model. It's the context.*
- **Hero A/B variants (locked 2026-05-29; now A–I):** problem-framing (**A** “Context fails
  more often than models.” · **B** “It’s not the model. It’s the context.” · **F** “Stale context
  is a silent outage.”) · trust/proof (**C** “Context you can trust. Proof you can show.”) ·
  engine/process (**D** “Retrieval fetches it. Baltor verifies it.” · **E** “Reconciled, hardened,
  enhanced, optimized.” · **G** “Not retrieval. Context governance.” · **H** “Context hardening for
  AI agents.”) · category-bridge (**I** “Context engineering picks it. Baltor governs it.” — meets
  the 2026 search term, then pivots to governance; see `POSITIONING-AUDIT.md §1`).
  Run through the shared experiments engine (`baltor_hero`); see `EXPERIMENTS.md`.
- **Subhead variants (`baltor_subhead`):** A (default) · B “Harden your context…” · C “Catch stale,
  conflicting…” · D “Governed context — reconciled, hardened…” · **E** “The governed context layer
  for the agents you already run…” (adopts the recognized category noun).
- **Subhead:** Verified, current, and provable context for the agents you already run.
- **Brand soul (internal):** *Trust your context like Nome trusted Balto.*
- **Four pillars:** Verified · Current · Efficient · Provable.
- **One-liner:** Connect your sources or subscribe to verified corpora; Baltor keeps context
  correct, current and lean — and proves it — then serves it to any agent.
- **What makes it different (the wedge):** it’s **context governance**, not retrieval — a four-stage
  lifecycle (Reconciliation · Anti-Fragility · Enhancement · Optimization) with verification,
  provenance/proof, three tiers (raw → compressed → hyper-efficient), oracle-published **Verified
  corpora**, served into the agent you already run (agent- & model-neutral).
- **Framing rule — never call Baltor a “context engine”** (reads as RAG/retrieval). It governs the
  **context lifecycle**; lead with **context governance** / **context hardening** + the four named
  stages. The four buyer-facing stage names are **Reconciliation · Hardening · Enhancement ·
  Optimization** — “Hardening” is the buyer word; **“anti-fragility” is the internal/architecture
  label only** (parenthetical at most on surfaces). “Hardening” = making raw knowledge robust and
  trustworthy before agents read it.
- **Voice / lexicon — keep consistent:** say **lean / efficient**, never "compression" as a
  headline; **never** claim "100% accurate." Lead with verification, then provenance, then
  freshness, then efficiency.
- **Pricing (open-core boundary):**
  - **Free — $0 forever:** download raw & compressed tiers, community Verified corpora, 1 workspace/seat. *No live verified serving.*
  - **Pro — $39 / seat / mo:** live verified serving (`/serve`), freshness + reconciliation + human-in-the-loop, hosted hyper-efficient tier, usage analytics & compliance artifacts.
  - **Enterprise — custom:** oracle-publisher Commons access, SSO/SAML, EU residency, dedicated verification SLAs, AIBOM · EU AI Act dossiers.
  - **Rule:** the open spec, SDK & export are never rate-limited — only live governed serving is metered.
- **Signature product surfaces:** the context **engine** (animated 4-stage pipeline:
  Reconciliation · Anti-Fragility · Enhancement · Optimization), **Sources** + **Pipeline run**
  (live per-stage progress), **Verified corpora**, **Verify** (reconciliation queue with HITL),
  **Serve** console, Governance, Audit.

## Teleon.dev — purpose-driven runtime
- **Tagline:** Capabilities, not code. *Define the outcome. We prove the rest.*
- **Hero second-line A/B variants** (run through the shared experiments engine — cycle via the
  in-hero pill, force with `?exp=teleon_hero:B`, sticky per visitor): **A** “We prove the rest.” ·
  **B** “Skip the agent.” · **C** “We build the capability.” · **D** “We make it dependable.”
  (first line always “Define the outcome.”) See `EXPERIMENTS.md`.
- **One-liner:** Set the outcome and the guardrails; Teleon turns an unbounded agent task into a
  deterministic capability — it self-improves and adapts when it should, proves itself on real
  examples before anything ships, and runs at a fraction of the token cost of a full agent.
- **Positioning spine:** unbounded → deterministic · outcomes **and** guardrails defined ·
  self-improving / adapts only when appropriate · far cheaper than running a full agent each call.
- **Lifecycle (customer-facing):** Purpose → Success criteria + guardrails → Approach → Candidate
  → Evidence → Promote / roll back.
- **Three value props:** Outcomes and guardrails (you set goal + limits, Teleon finds the how) ·
  Unbounded → deterministic (open-ended task collapsed to a fixed, repeatable capability) ·
  Self-improving, far cheaper (re-proves itself as sources change, at a fraction of an agent's tokens).
- **Closing line:** Define capabilities. Not infrastructure.
- **Closing line:** Define capabilities. Not infrastructure.

## The open layer
- **OpenHarnessHub.io** — *Build & monitor governed pipelines.* Hero: **"Power your agents with
  governed harnesses."** Describe a task; OHH assembles a governed harness — vetted components
  and knowledge packs that measurably lift what your agent can do, mostly deterministic and
  freezable so you add capability without adding cost. Pricing: open spec free forever; vetted
  components, live knowledge corpora & build-on-demand are the subscription (Pro $39/seat/mo).
  - **Audience landings (`/for/*`):**
    - *Governments & standards bodies* — "Publish authoritative facts the world can cite."
    - *Pipeline builders* — "Tired of facts changing faster than your LLM?"
    - *Legal teams* — "Answers with citations a partner would sign off on."
    - *Regulators & auditors* — "Verify compliance with a complete auditable trail."
- **OpenContextHub.io** — the open registry of context packs the ecosystem builds on.
- **OpenSkillsHub.io** — a shared graph of composable, evaluated agent skills.
- **OpenToolsHub.io** — a registry of governed tools agents can call.
- **OpenSkillToTool.io** — converts governed skills into typed, callable tools (the bridge from OpenSkillsHub to OpenToolsHub). *Skills describe how; tools do.*
- **OpenMCPHub.io** — MCP server intelligence: registry, conformance, risk, install profiles. *Discovery is not trust.*
- **OpenCompressionHub.io** — compression & context-budget intelligence. *Token reduction is not success unless fidelity survives.*
- **OpenBenchmarkHub.io** — benchmark intelligence: cards, result records, suitability reports. *Evidence, not authority — a result cannot promote a candidate alone.*
- **OpenHarnessHub.io** — open harnesses & evals for agentic infrastructure.

All seven open `.io` hubs are prototype sites on the shared `makeHub` config; their domains are
**proposed/unverified** pending owner trademark/domain clearance.

---

## Naming & relationship rules (do not break)
- "AI Done Right" is the **only** company-level brand. Baltor and OpenHubForAI are
  **sister products** (peers) — neither is a parent. OHH appears on Baltor only as a quiet
  "sister product" footer link — **never** a switcher or a parent.
- Renaming any brand is a one-line edit in `products.js` (`name` / `wordmark`).
- Each brand owns exactly one accent (Baltor teal · Teleon violet · parent blue · OHH ember ·
  OpenContextHub green · OpenSkillsHub teal-blue · OpenToolsHub amber · OpenSkillToTool rose). Everything else
  (type, spacing, chrome, dark-mode) is identical across the family.
