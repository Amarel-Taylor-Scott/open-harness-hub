# Portfolio Guidance — Mission · Vision · Problem→Solution · PMF · Competitors

**Status:** Synthesized 2026-06-24 from the canonical strategy docs (does not supersede them). Architecture follows
the **owner-LOCKED June-2026 framing** in [teleon-baltor-openharnesshub-portfolio](./teleon-baltor-openharnesshub-portfolio.md)
and [teleon-naming-and-domain](./teleon-naming-and-domain.md). **All pricing, and any brand not already owned, are
PROPOSALS — owner-gated.** Where evidence is thin the docs say so; this guidance carries those caveats forward
(`serves_truth=false` for derived/representative figures).

---

## The one-sentence portfolio

**Parent brand: "AI Done Right" — tagline *"AI, done right."*** One holding company over three product layers plus a
developer-facing review surface:

```
AI Done Right  (umbrella IP · brands · standards · shared R&D/security/governance)
├── Teleon.dev   — runs your capability on the CHEAPEST bounded path that still passes   → governs EFFICIENCY
├── Baltor.ai    — managed, verified, provable context, powered by Teleon                → governs TRUTH
├── Open*Hubs    — the open STORE both products consume (context·tools·skills·harnesses·specs)
└── Review surface — rides along while a coding agent (Claude Code/Cursor/Codex) works, and reviews the result
```

**Moat split (LOCKED):** *Baltor governs what becomes **TRUE**; Teleon governs what becomes **EFFICIENT**.* Both
govern — different objects, never the same. **Dependency law (enforced):** `Baltor → Teleon → OpenHarnessHub`, never
the reverse.

---

## 1 · Teleon — the efficiency runtime

> **"Serverless runs code. Kubernetes runs workloads. Teleon runs purpose."**
> Category: *intent-native, eval-gated, self-adaptive compute.*

- **Mission / Vision** — Let anyone program a capability in **plain text** and have it auto-adapt to the
  cheapest **bounded** form that still meets their bar, and *stay* cheapest as models change. Teleon governs
  **EFFICIENCY** (the "descent brain").
- **Problem** — Unbounded frontier spend on tasks that don't need a frontier model, with **no proof** of which
  cheaper path is safe — and no way to keep that current as models ship weekly.
- **Solution** — A thin **control/metadata plane** that picks, governs, and *learns* the cheapest passing
  implementation of a capability (with receipts), while **compute runs on the customer's account (BYO)**. The moat
  is the accumulated descent brain, **not** the compute.
- **Product-Market Fit**
  - **Buyer:** AI-agent / agent-builder teams (sell them stable, receipt-backed **CapabilityTasks** they call
    *instead of burning tokens*); secondary: platform/eng teams bleeding on unpredictable frontier spend,
    especially regulated orgs.
  - **Wedge:** descend one capability to its cheapest bounded passing form, receipt-backed, BYO-compute.
  - **Monetization (PROPOSAL):** charge for governed selection + learning + receipts, **never compute**.
    Starter $0 → Team ~$249/mo → Enterprise custom; defensible axis = per-active-capability + a savings share.
  - **Honest state:** engine built + proof-gated; representative savings (≈47% extraction, ≈86% enrichment) hold
    until a live lane runs on real eval data; `go_live_ready=false` (known seams).
- **Competitors & difference** — GitHub Agent HQ/Copilot, Azure DevOps agents, GitLab Duo, Cursor background
  agents, Amazon Kiro/Q, Replit, Devin **store and run** code for agents; **none govern whether the resulting
  capability is correct, lifts, or is safe.** Naming-collision caution: avoid "deploy AI agents in minutes" /
  "Vercel for agents" (collides with the unrelated `teleon.ai`).

---

## 2 · Baltor — the managed governed-context product

> **"Baltor governs TRUTH."** · *"Baltor is powered by Teleon."* · framing: *"models don't fail — their context does."*

- **Mission / Vision** — A **governed context supply chain** for enterprise agents: company-/department-wide
  context that is **Verified · Current · Provable**, with a held-out-stale **receipt an examiner accepts**.
- **Problem** — AI workflows run on raw, stale, and contradictory context. In the launch vertical (compliance),
  a missed match = fine; a false-positive flood = analyst cost; and "we said clear" with no provable basis is
  indefensible.
- **Solution** — A **medallion pipeline**: **Bronze** raw sources → **Silver** verified claims → **Gold**
  task-ready context packs. Sharper than RAG: *most platforms keep your docs **current**; Baltor continuously
  verifies they are **correct** — cross-checked against authoritative sources, hunting contradictions before your
  agent cites them.*
- **Product-Market Fit**
  - **Buyer:** compliance/AML/BSA lead at a fintech/neobank/payments/crypto on-ramp (Series A–C) already running
    sanctions screening and bleeding on false positives + audit-defensibility; secondary: regulated legal-ops and
    engineering-workflow context (ticket/MR/repo/**review** packs).
  - **Wedge:** OFAC SDN **sanctions screening** — proven by a live run that caught a real would-be violation an
    internal doc had marked "clear." *The receipt is the closer.*
  - **Monetization (PROPOSAL):** design-partner pilot $5k–$25k → Business $6k–$15k/mo → Enterprise $40k+/yr;
    meter on monitored sources / facts-under-management / verification jobs.
- **Competitors & difference** — Screening incumbents (LexisNexis Bridger, ComplyAdvantage, Dow Jones,
  World-Check): don't out-*coverage* them — **win on the receipt + CDC freshness + "we caught your own stale
  clear."** Context-layer / memory / repo-intelligence watchlist (Contextual AI, Glean, Mem0, Zep, Letta,
  Greptile, Sourcegraph): *RAG retrieves chunks; memory remembers things; **Baltor decides which remembered
  things are safe, current, source-linked, and task-relevant** — and proves it.*

---

## 3 · Open*Hubs — the open store / ecosystem

> *"The open STORE both products consume."* · Governance law: **none is a truth authority; discovery is not trust.**

- **Mission / Vision** — A governed, **lift-gated** registry family + the seven-primitive grammar (Input ·
  Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output), stewarding the open **CapabilityTask Spec
  (CTS)**. A focused family, not one junk drawer: **OpenContextHub** (context), **OpenSkillsHub** (skill graph),
  **OpenToolsHub** (tool graph), **OpenHarnessHub** (the proof layer: harnesses/rubrics/eval packs).
- **Problem** — Teams rebuild the same pieces and can't tell which model/tool/retrieval/runtime/safety-gate to
  use, or whether a component actually **lifts** capability over the bare model.
- **Solution** — A public catalog where every component carries **measured lift on the buyer's own data**
  (`pipeline_score − bare_model_score > 0`, and **structural/durable**, not transient) plus governance
  chain-of-custody (provenance/AIBOM, signed publishers, CDC/revocation, lineage).
- **Product-Market Fit**
  - **User:** the open/portable/low-end **developer long tail** — working with the agent they already run
    (**Claude Code/Codex**). The hubs are the **funnel, not the revenue**.
  - **Monetization:** the export is a commodity (the funnel); recurring revenue is the two things an export can't
    freeze — the **live/governed layer** (code-executing components + dynamic corpora with CDC) and
    **build-on-demand**. Open-core: FREE OSS hubs (wedge) ↔ PAID governed layer (Baltor/Teleon, recurring).
- **Competitors & difference** — Packing CLIs (Repomix, gitingest, code2prompt), memory libs (Mem0, Zep, Letta),
  RAG frameworks (LlamaIndex, Onyx, LangChain, Haystack), enterprise context vendors (Glean, Snowflake Cortex,
  Atlan), hubs (LangChain Hub, Hugging Face, Dify/Flowise). **No camp has all four of:** separate-evaluator
  measured lift on *your* data · governance chain-of-custody · seven-primitive composability · two doors onto one
  governed object (bounded pipeline **or** fuel into your open agent). *Lead with measured-fidelity + governance —
  never "we compress" or "we have memory."*

---

## 4 · The Review Surface — for users of coding agents (Claude Code / Cursor / Codex)

> **"AI, done right" applied to AI-written code:** ride along **while** your agent codes, and review the result
> **after.** *(Working framing — a standalone brand is owner-gated; OpenReviewHub is the reserved registry surface.
> Today this is assembled from existing assets below, not a separate SaaS.)*

This is the **developer-facing front door to the Verification universe** — what a Claude Code user actually
touches. It has two moments, each backed by a real component already in the repo:

**A. WHILE reviewing (intra-session, as the agent edits)**
- **Structural change-audit** — `scripts/codegraph.py --audit <file|symbol>`: a unified, **weighted** code graph
  (file imports + symbol calls/inherits) that ranks the **strong connections** (importers/callers by call-sites ×
  resolution-confidence) plus the transitive blast radius, so you (or the agent) review what a change can break
  **before and after** the edit. Resolution is confident-only (ambiguous/builtin-shadow calls dropped + counted —
  no false hubs), so the ranking is trustworthy. Protocol: [codegraph-change-audit-protocol](../codex/codegraph-change-audit-protocol.md).
- **AI-usage observer (Teleon Observer — owner-gated/proposal)** — a thin layer that watches *how* the developer/
  agent uses AI in VS Code / Claude Code / Codex, pops up intra-session, and flags **reinvention and token waste**
  ("6 places you reinvented something already solved"; "this prompt has 320k unnecessary tokens"). Reviews AI
  **usage**, not code correctness. *"Grammarly / Datadog / a compiler-optimizer — for AI usage."*

**B. POST review (after the work / on the PR)**
- **Multi-agent diff/PR review** — `/code-review ultra` launches a deep, multi-agent cloud review of the current
  branch (or a GitHub PR); `/code-review` (low→high) reviews the working diff locally for correctness + reuse/
  simplification. User-triggered and billed.
- **Post-session review report** — the Observer's lead artifact: a session recap a developer reviews **for
  learning** (what was reinvented, wasted, or done well).
- **Governed review context (Baltor `review_pack`)** — a **Gold** task-ready context pack assembled for a specific
  ticket/merge so the reviewer (human or agent) cites **verified, source-linked** facts, not raw retrieval.

- **Mission / Vision** — Make the code your AI agent writes **correct** (Baltor/truth), **efficient** (Teleon/
  efficiency), and **well-understood** (codegraph blast-radius) — by default, in the tools developers already use.
- **Problem** — Coding agents ship large diffs fast; humans can't hold the blast radius in their head, can't see
  where the agent reinvented or wasted, and PR review happens too late. AI accelerates writing code far more than
  it accelerates **trusting** it.
- **Solution** — A two-moment review that is **in the loop while coding** (graph audit + usage observer) **and on
  the diff after** (multi-agent review + governed review packs) — one surface spanning both.
- **Product-Market Fit**
  - **User:** developers and teams using coding agents (Claude Code first; Cursor/Codex/MCP clients next) — the
    audience the rest of the portfolio already addresses ("works with the agent you already run").
  - **Wedge:** the **codegraph change-audit + `/code-review`** are live and free in-repo today (the
    foot-in-the-door); the Observer + governed `review_pack` are the paid/managed extension.
  - **Monetization (PROPOSAL):** free open audit/review CLI as the funnel → paid governed review context + usage
    optimization (Baltor/Teleon recurring) — the same open-core line as the hubs.
- **Competitors & difference** — PR-review/codebase-AI tools (Greptile, Sourcegraph, GitHub Copilot review, Cursor
  Bugbot, Graphite, Qodo): they review **code text**. This surface adds two things they don't unify: (1) a
  **trustworthy weighted blast-radius graph** purpose-built for "what else does this change touch," and (2)
  **governed truth + efficiency** behind the review (Baltor verifies the facts cited; Teleon flags the waste) —
  i.e. it reviews not just *the code* but *how the AI produced it* and *whether its context was true.* *Baltor
  should not compete as generic repo search or a generic coding agent* — the edge is the governance + the graph,
  not coverage.

---

## How to use this guidance

- **Pitch the pattern, lead with proof.** Across all four: lead with **measured fidelity + governance on the
  buyer's own data** and the **receipt**, never with "we compress" / "we have memory" / "we have coverage."
- **Keep the moat split crisp:** Baltor = TRUTH, Teleon = EFFICIENCY, Open*Hubs = discovery (not truth), Review =
  the developer front door to both.
- **Honesty is the brand.** Mark proposals as proposals, representative numbers as representative, and
  `serves_truth=false` for static derivations. That discipline *is* "AI, done right."

**Canonical sources:** [teleon-baltor-openharnesshub-portfolio](./teleon-baltor-openharnesshub-portfolio.md) ·
[teleon-naming-and-domain](./teleon-naming-and-domain.md) · [positioning-v2](./positioning-v2.md) ·
[competitive-landscape-2026](./competitive-landscape-2026.md) · [gtm-teleon-baltor-and-phased-launch-2026-06](./gtm-teleon-baltor-and-phased-launch-2026-06.md) ·
[baltor-adjacent-market-map](./baltor-adjacent-market-map.md) · [teleon-observer-ai-usage-layer](./teleon-observer-ai-usage-layer.md) ·
[capability-valleys](../concepts/capability-valleys.md) · review surface: [codegraph-change-audit-protocol](../codex/codegraph-change-audit-protocol.md).
