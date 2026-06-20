# Marketing & Messaging — AI Done Right (founding thesis: ContextIsEverything)

Canonical positioning and copy for the brand family. Source of truth for product/brand
*identity* is `shared/products.js`; this file is the human-readable messaging guide (use it
for site copy, sales decks, and onboarding). When a brand name/tagline changes, change it in
`products.js` first, then reconcile here.

---

## Company — AI Done Right
- **Mission / company line:** *Context is Everything.*
- **Thesis:** *A model is only as good as the context it acts on.*
- **What it is:** a holding company / portfolio. A **house of brands** under one mission —
  not a single product. Legal entity: OpenHarness, Inc.
- **Architecture story (top → bottom):** governed **Products** you run (Baltor, Teleon) sit on
  top of **Open resources** — context, skills, tools and harness registries.
- **Capability lifecycle spine (used in the parent diagram):**
  Purpose → Contract → Runtime selection → Candidate → Evidence → Eval-gated promotion / rollback.
- **How value flows (ports):**
  - Baltor → Teleon via `PurposeTaskProviderPort` (Teleon returns evidence / candidate / result, **never** Baltor's own truth/data).
  - Teleon → the open hubs (draws templates, skills & eval packs).

---

## Baltor.ai — paid context-assurance SaaS (the moat)
- **Tagline:** Context assurance for AI agents.
- **Primary hook (locked 2026-05-29):** *It's not the model. It's the context.*
- **Hero A/B variants:**
  - **A** — "Context fails more **often than models.**"
  - **B** — "It's not the model. **It's the context.**"
  - **C** — "Context you can trust. **Proof you can show.**"
- **Subhead:** Verified, current, and provable context for the agents you already run.
- **Brand soul (internal):** *Trust your context like Nome trusted Balto.*
- **Four pillars:** Verified · Current · Efficient · Provable.
- **One-liner:** Connect your sources or subscribe to verified corpora; Baltor keeps context
  correct, current and lean — and proves it — then serves it to any agent.
- **What makes it different (the wedge):** lead with **verification** (correct, not just
  current), provenance/proof, three tiers (raw → compressed → hyper-efficient), oracle-published
  **Verified corpora**, and serving into the agent you already run (agent- & model-neutral).
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
- **Tagline:** Capabilities, not code. *Define the outcome. Not the code.*
- **One-liner:** Tell Teleon what you want and how you'll know it's right; it builds the
  capability, tests it on real examples, and ships only what passes — rolling back regressions.
- **Lifecycle (customer-facing):** Purpose → Success criteria → Approach → Candidate → Evidence
  → Promote / roll back.
- **Three value props:** Describe the outcome (no glue code) · It improves itself (adopts what
  works, no redeploy) · Proven before it ships (must clear your criteria; regressions auto-roll-back).
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

---

## Naming & relationship rules (do not break)
- "AI Done Right" is the **only** company-level brand. Baltor and Open Harness Hub are
  **sister products** (peers) — neither is a parent. OHH appears on Baltor only as a quiet
  "sister product" footer link — **never** a switcher or a parent.
- Renaming any brand is a one-line edit in `products.js` (`name` / `wordmark`).
- Each brand owns exactly one accent (Baltor teal · Teleon violet · parent blue · OHH ember ·
  OpenContextHub green · OpenSkillsHub teal-blue · OpenToolsHub amber). Everything else
  (type, spacing, chrome, dark-mode) is identical across the family.
