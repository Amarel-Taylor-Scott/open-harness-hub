# Positioning v2 (canonical) — name · value prop · competitive stance

The single throughline that consolidates the strategy. Deep-dives feed this doc; don't duplicate them:
[[beat-contextual-positioning.md]] (competitor profile + wedges + upstream), [[competitor-contextual-ai.md]]
(the engine/Agent-Composer analysis), [[oracle-corpus-and-tooling-map.md]] (the commons + beachhead),
[[open-core-line-and-learn-from-contextual.md]] (free-vs-paid + learn-from), [[context-layer-pmf.md]],
[[two-services-shared-infrastructure.md]].

## The throughline (read this first)
**Don't position on "harness beats RAG."** Contextual is closing that gap (Agent Composer = orchestration,
multi-tool, a Task-Execution agent that does API *write* actions, model-agnostic, no-code builder — Jan
2026). **Orchestration / actions / build-UX are becoming table stakes.** The two things that stay *ours*,
orthogonal to whoever has the slickest orchestration:
1. **Open / portable / low-end** — Open Harness Hub for the devs Contextual treats as a funnel.
2. **Verified context, upstream** — the service that checks the *corpus* against authoritative truth, kept
   current, with provenance — feeding *any* agent, including Contextual itself.

**Sharpened (from Contextual's own docs, May 2026):** their actions are confirmed side-effecting
(webhook → send-email; "Task Execution" = API write actions), and they ship the *full* builder + governance
(RBAC, model-armor, observability) + model-agnostic. So **OHH cannot win as "a better builder"** — it would
lose to Agent Composer *and* the OSS builder crowd (LangGraph, Dify, n8n, Flowise). OHH's differentiation has
narrowed to **ONE** thing Contextual structurally won't be: **genuinely open** — real OSS, self-hostable,
free for the long tail, working with the agent the developer already runs (their "free trial + model-agnostic"
is an enterprise *funnel*, not an open product). **So: OHH = the open funnel + the consumption surface for
verified corpora (distribution + developer goodwill); CEaaS = the headline business. The product is the
verified FUEL, not the harness.**

**The wedge line (memorize):** *"They check your docs are CURRENT; we check your docs are RIGHT against the
source of truth."* Their compliance ("validate everything is current") = completeness + recency of the
*customer's own* docs — NOT tracking the external authority and flagging when internal context contradicts or
lags it. They ground in whatever corpus you supply; they do not verify it's correct against external truth,
keep external regulated corpora current as a product, offer oracle-signed shared corpora, or reconcile
conflicting authorities. **That one sentence is the whole business.**

**Confirmed at the source (their docs):** the shared "global datastores" are **demo-only** (read-only,
"Demo" badge, not for production); everything real is **customer-provided + per-tenant isolated** (connectors
/ upload / Documents API). So there is **no production shared corpus, no cross-customer sharing, no
marketplace, no oracle-publisher path** — the verified-corpus-commons gap is now *documented*, not inferred.
Their architecture even has an Enterprise-Knowledge layer at the bottom that **must be fed** with no shared-
corpus answer of their own — the exact slot we supply (strengthens the upstream + acquisition logic).

## Name + tagline (no rename)
**Open Harness Hub** (`openharnesshub.com`) — **the harness layer that powers trustworthy agents.**
Bridge to "agent" in language/SEO (*"Power your agents with governed harnesses"* / *"harnesses for agents
you can trust"*), never by renaming (that collapses the harness-vs-agent line the two-product split needs,
and drops us into the commoditizing agent category). The metaphor *is* the pitch: a harness reins in
powerful behavior → **governed agents you can trust.** (Own the full mark; "harness" alone collides with
Harness.io.) The verified-context product and the umbrella/company brand remain **open naming questions.**

## The two products (one governed object, two doors)
- **Open Harness Hub — the bounded, governed harness** (free/OSS funnel + low-end wedge). Assemble + monitor
  a governed pipeline of seven primitives; components admitted only on **measured lift**; **open, portable,
  works with the agent you already run** (Claude Code/Codex). *Value prop:* "the open, governed harness
  layer for agents — buildable, measurable, yours."
- **Context Enrichment / verified-context SaaS — the moat** (recurring). **Verified, current, provable
  context:** corpora cross-checked vs authoritative truth, freshness/CDC, C2PA provenance + oracle
  publishers, HITL on conflicts, compliance artifacts — served into any agent. *Value prop:* "Verified,
  current, provable context — for the agent you already run." (Name TBD.)
- **The join:** one governed corpus/tool, minted + scored once (lift + fidelity), consumed two ways — wired
  into a bounded harness, or served as fuel into an open agent.

## Competitive stance vs Contextual AI
- **Profile:** Kiela (RAG co-inventor) + Singh; ~$100M (Nvidia/Bezos/Snowflake/HSBC); ~51–100 ppl; Qualcomm
  + HSBC; **bring-your-own-data, per-tenant isolated, not trained on** (confirmed). Best-in-class engine +
  now a full agent platform.
- **Don't fight where they're strong (ALL confirmed):** RAG quality, orchestration, the grounded model, the
  no-code builder, **side-effecting actions (incl. API writes), governance (RBAC / model-armor / observability),
  and model-agnostic model choice.** Pitching against any of these loses — they have them.
- **Learn, don't rebuild:** adopt their eval rigor (RAG 2.0 / FACTS / the **LMUnit** pattern) + attribution
  conventions (makes us integrable *and* acquirable); **wrap** their Component APIs as governed adapters
  ([[competitor-contextual-ai.md]]).
- **Win where they structurally can't:** (1) **open/portable/low-end**, (2) **verified context** — they
  ground answers in the docs but **never check the docs are correct or current**; their "freshness" is
  web-search world knowledge + sync, *not* a regulated corpus kept current against its authority. **That
  gap is the business.** (3) **Sit UPSTREAM** — supply verified corpora into Contextual/Snowflake/Databricks/
  Claude Code; we win when anyone wins.
- **Beachhead:** sanctions & export controls (OFAC/BIS/EU) — the "rules that change faster than anyone
  re-indexes, where stale is a *legal event*" pattern at its extreme, and the easiest start (lists already
  public + machine-readable). [[oracle-corpus-and-tooling-map.md]].
- **Real acquirers:** the data clouds (Snowflake/Databricks), a hyperscaler, or a GRC incumbent — *not*
  primarily Contextual. The most *defensible* (upstream/verified) positioning is also the most *acquirable*.

## The crisp one-liners
- **Company:** "The open harness layer + verified context for trustworthy agents."
- **OHH:** "Power your agents with governed harnesses." (free, open, portable, measured.)
- **Verified-context SaaS:** "Verified, current, provable context — for the agent you already run." (the moat.)

## What we DON'T claim (honesty guards)
We don't claim to out-RAG Contextual, to have novel orchestration, or measured-lift we haven't run
(our measured-lift evidence is still thin — [[measured-lift-head-to-head.md]] is the harness to fix it).
Open = freezable (download it); paid = anything that must stay live/verified/provenanced
([[open-core-line-and-learn-from-contextual.md]]).

---
*warrant: user-intent — "update product positioning, value proposition, competitive stance" + the naming
resolution ("keep openharnesshub.com, use 'power your agents with the best harnesses' language");
corroboration — the prior verified deep-dives + the Agent Composer launch + the customer-provided-data confirmation.*
