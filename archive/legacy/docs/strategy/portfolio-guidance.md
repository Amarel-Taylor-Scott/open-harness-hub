# Portfolio Guidance — Mission · Vision · Problem→Solution · PMF · Competitors

**Status:** Synthesized 2026-06-24 from the canonical strategy docs (does not supersede them). Architecture follows
the **owner-LOCKED June-2026 framing** in [teleon-baltor-openharnesshub-portfolio](./teleon-baltor-openharnesshub-portfolio.md)
and [teleon-naming-and-domain](./teleon-naming-and-domain.md). **All pricing, and any brand not already owned, are
PROPOSALS — owner-gated.** Where evidence is thin the docs say so; this guidance carries those caveats forward
(`serves_truth=false` for derived/representative figures).

---

## The one-sentence portfolio

**Parent brand: "AI Done Right" — tagline *"AI, done right."*** One holding company over three product layers plus
AIDevObserver (the AI-usage session-review wedge):

```
AI Done Right  (umbrella IP · brands · standards · shared R&D/security/governance)
├── Teleon.dev   — runs your capability on the CHEAPEST bounded path that still passes   → governs EFFICIENCY
├── Baltor.ai    — managed, verified, provable context, powered by Teleon                → governs TRUTH
├── Open*Hubs    — the open STORE both products consume (context·tools·skills·harnesses·specs)
└── AIDevObserver — watches AI usage; reviews the SESSION (post) + helps intra-session (while)  → Teleon's wedge
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

## 4 · AIDevObserver — AI session review + intra-session helper (for Claude Code / Cursor / Codex users)

> **"Grammarly / Datadog / a compiler-optimizer — for AI usage."** It watches *how* you use AI, **saves the
> session**, lets you **review it for learning** (post), and **pops up during the session** (while) — *"this already
> exists," an adversarial question, a cheaper path, "this prompt has 320k unnecessary tokens."*

**This reviews your AI *usage / session*, not your code.** Code-correctness review (PR/diff bugs) is a separate
concern. The Observer is the **customer-facing wedge for the Teleon engine** — a thin front-end over the existing
descent + reinvention guardrail + the registry federation (grounding) + economics. Built: `src/teleon/observer/`
(`capture` · `session_store` · `review` · `router`) + `src/teleon/knowledge/`. `serves_truth=false`; local-first;
governed. Status: real engine + proofs; the live capture/SaaS front-ends are owner-gated.

- **Mission / Vision** — Teach developers (and their agents) to **use less unnecessary intelligence**: catch waste,
  reinvention, and footguns *grounded in a real index of what already exists*, in the tools devs already run.
- **Problem** — AI coding sessions silently burn tokens, **reinvent things that already exist**, and take footgun/
  adversarial paths — and the developer never sees it. The pain is in *how the AI is used*, invisible after the fact.
- **Solution** — One engine on a timeline, two moments:
  - **POST — session review (lead with this):** ingest the transcript/diff after a session, run the funnel in
    batch, emit a confidence-scored report a human triages — *"6 places you reinvented something solved,"* where
    tokens/time were wasted, debugging loops, missed shortcuts. No latency budget; no false-interrupt problem.
  - **WHILE — intra-session helper:** typed interventions surfaced live — reinvention ("PyMuPDF already does
    this"), an **adversarial question** ("are you sure a custom parser beats the library?"), a **cheaper path**, a
    **token optimization** (~96% cheaper) — governed by a **global interruption budget** + **graduated modes**
    (ambient → post-action → pre-action/block), so it helps without nagging. **Fail-open: degrades to silence,
    never obstruction.**
- **Product-Market Fit**
  - **User:** developers/teams using coding agents — **Claude Code** first (clean hook semantics), then Cursor /
    Codex / any client (via the gateway, zero client buy-in).
  - **Wedge:** the **post-session reviewer** — "paste a session / connect a repo, get a reinvention + waste
    report." Smallest, highest-adoption artifact; earns the precision + trust to later interject live.
  - **Trust ladder:** post-session report → ambient notices → enforced pre-action (the high-value endgame).
  - **Data residency (deal-lever):** Tier-1 judge + grounding run **on a local model + local registry** — *"your
    code physically cannot leave your VPC."*
  - **Monetization (PROPOSAL):** free/low-friction post-session report (funnel) → hosted SaaS + self-hosted VPC
    server with enforced pre-action guardrail (enterprise) — Teleon recurring.
- **Competitors & difference** — Anyone can build a hook or a prompt logger; LLM-observability tools (LangSmith,
  Helicone, PromptLayer) record calls but don't *judge reinvention* or *coach toward cheaper paths*. The two
  defensible parts are (1) the **grounded index** (the registry federation, kept fresh) that makes the "it already
  exists" call **precise instead of an LLM guess**, and (2) the **optimization memory** (`descent_attempt_store`)
  that learns winning paths from real session telemetry across runs. *Honest hard parts:* distribution + clean
  capture are harder than the AI; a wrong pre-action interrupt gets muted in a day (hence lead post-session); and
  don't build both Teleon **Compiler** and **Observer** at full depth before one is proven.

---

## How to use this guidance

- **Pitch the pattern, lead with proof.** Across all four: lead with **measured fidelity + governance on the
  buyer's own data** and the **receipt**, never with "we compress" / "we have memory" / "we have coverage."
- **Keep the moat split crisp:** Baltor = TRUTH, Teleon = EFFICIENCY, Open*Hubs = discovery (not truth), Teleon
  Observer = the AI-usage review/helper wedge in front of the Teleon engine (it reviews usage, not code).
- **Honesty is the brand.** Mark proposals as proposals, representative numbers as representative, and
  `serves_truth=false` for static derivations. That discipline *is* "AI, done right."

**Canonical sources:** [teleon-baltor-openharnesshub-portfolio](./teleon-baltor-openharnesshub-portfolio.md) ·
[teleon-naming-and-domain](./teleon-naming-and-domain.md) · [positioning-v2](./positioning-v2.md) ·
[competitive-landscape-2026](./competitive-landscape-2026.md) · [gtm-teleon-baltor-and-phased-launch-2026-06](./gtm-teleon-baltor-and-phased-launch-2026-06.md) ·
[baltor-adjacent-market-map](./baltor-adjacent-market-map.md) · Observer: [teleon-observer-ai-usage-layer](./teleon-observer-ai-usage-layer.md) ·
[capability-valleys](../concepts/capability-valleys.md).
