# YC readiness & prep (2026) — the single self-directing target

This is the **one objective** the loop steers toward. It is grounded in YC's actual 2026 criteria and Summer-2026
Requests-for-Startups (researched 2026-06-21, sources at the bottom), and it is **measured continuously** by
`scripts/yc_readiness.py` (the `yc` flywheel files the open gaps into the proposal backlog). Run it any time:

```bash
./loop yc          # the YC-readiness scorecard + the top gaps (the loop's marching orders)
./loop             # start everything + supervise (the single command)
```

> Status note: this doc is a synthesis/prep artifact. **Owner-gated decisions** (raise size, pricing, the locked
> one-liner) are listed as DECISIONS below — they are not decided here (change-verification law).

## 0. The one-liner (⟦OWNER: lock ONE⟧)

Candidate, product-first (from the YC-readiness handoff): **"Baltor continuously verifies your AI's context is
*correct* — not just current — against authoritative sources, and proves it with a portable receipt."** 5+ variants
compete across docs today; YC rewards a single matter-of-fact sentence ("we make X — like A, but B"). Lock one.

## 1. What we are (and why it is NOT a GPT wrapper)

A holding company (**AI Done Right**, `aidoneright.dev`) over three layers:
- **Baltor** (`baltor.ai`) — the governed **context engine**: ingest → reconcile → harden → enrich → compress → serve,
  with verification, provenance, freshness/CDC, and a **portable receipt**. *"We govern what becomes true, not just
  sign what happened."*
- **Teleon** (`teleon.dev`) — the thin **control plane** that descends each capability from the unbounded/inefficient
  default (frontier model on everything) to the most bounded/efficient path that still meets the requirement.
- **OpenHarnessHub** — the open ecosystem + CapabilityTask spec.

**Not a wrapper:** real layering enforced in code (dependency law Baltor→Teleon→OHH, plane separation, ports for every
backend). "AI is infrastructure, not a feature" — this is infrastructure.

## 2. YC S26 Requests-for-Startups — direct fit

- **RFS #4 "Software for Agents"** (machine-readable infrastructure for AI agents) → **Teleon** serves agents a
  deterministic, receipt-backed capability layer they call. Direct fit.
- **RFS #5 "The AI Operating System for companies"** (queryable, real-time operations layer) → **Baltor** governed
  context layer + capability catalog. Direct fit.
- **RFS #3 "Company Brain"** (centralize scattered knowledge) → adjacent (Baltor governs whether that knowledge is true).

## 3. YC 2026 criteria → how we answer

| YC cares about | Our answer | State |
|---|---|---|
| **Clarity** (one matter-of-fact sentence) | §0 candidate | ⟦owner: lock⟧ |
| **Insight / why-now** | EU AI Act full enforcement **Aug 2, 2026** (Art. 73: 72h incident reconstruction = portable receipts + lineage on a legal deadline) | strong |
| **Founder-market fit** | training-free / frozen-model + legal-AI background; PhD few-shot segmentation | ⟦owner: fill the story⟧ |
| **Who DESPERATELY needs this** | fintech/neobank/payments bleeding on sanctions/compliance screening (OFAC wedge) | named |
| **Proof of progress** (beats narrative) | working offline engine; **OFAC live receipt** (real SDN list, planted catch); CFPB correctness invariant; RuleArena +0.71 lift; 553 deterministic proofs | strong, real |
| **Working demo** | `dist/teleon-demos/showcase.html` — 3 capabilities descend unbounded→bounded, dual efficiency/safety control chart | built |
| **Competition / moat** | governance + verification + portable receipts + multi-domain catalog (vs Mem0/Zep memory, RAG vendors, gateways, Pramaana/Probably) | mapped |
| **The ask** | raise size + use-of-funds | ⟦owner: lock⟧ |
| **Traction** | pre-revenue, design-partner stage; **no signed partner yet** | the bottleneck |

## 4. Proof points — real vs representative (be honest)

**Real / reproducible today:** OFAC live sanctions catch (`data/live-receipts/ofac-sdn-live-2026-06-14-receipt.json`);
CFPB correctness invariant (`scripts/demo_offline_full_baltor.py --self-test`); deterministic rule distillation
(RuleArena +0.71 lift, lossless); 1,059 governed catalog components (admission = measured lift + provenance); durable
worker fleet + live supervisor scaling; multi-cloud execution-backend selection; 553 proofs on a ~10-min watchdog.

**Candidate / labeled seams (real backend deferred behind a port):** Postgres/pgvector, Temporal, Docling, Graphiti,
Langfuse, k8s, frontier models — working local equivalent + stub, wired when credentials arrive.

## 5. The scorecard (measured by `scripts/yc_readiness.py`)

Weighted dimensions, every one a real probe (a receipt that exists, a doc that exists, a gate that's green):
`proof_point`(3) · `working_demo`(3) · `traction_design_partner`(3) · `backends_green`(2) · `founder_market_fit`(2) ·
`who_needs_it`(2) · `not_a_wrapper`(2) · `clarity_one_liner`(2) · `competition_moat`(1) · `why_now_insight`(1) ·
`ask_deck`(1) · `rfs_alignment`(1) · `decisions_locked`(1). Ready bar = 0.85. Open gaps are filed into the
comfort-gated backlog automatically.

## 6. Ranked gaps (the marching orders — gaps are organizational, not technical)

1. **Traction — sign 1 design partner + a paid pilot** that exports a package consumed by *their* agent/RAG, with a
   before/after report (stale-context caught, manual-review reduced). The real 90-day bottleneck. ⟦owner GTM⟧
2. **Founder/team story** — fill section 1 of `docs/strategy/yc-application-draft-2026-06.md`. ⟦owner⟧
3. **Backends green** — keep the proof gates green (`./loop run`); the loop does this automatically.
4. **Owner decisions** — ratify raise size, pricing, and the one locked one-liner. ⟦owner⟧
5. **Deck polish** — name the EU AI Act forcing function explicitly on the "why now" slide; add the customer before/after
   traction slide once the pilot lands.

## Sources (web research 2026-06-21)
- [Apply to YC](https://www.ycombinator.com/apply) · [How to Apply (PG)](https://www.ycombinator.com/howtoapply)
- [YC reveals 15 Summer 2026 startup ideas (RFS)](https://urbangeekz.com/2026/05/y-combinator-reveals-15-startup-ideas-it-wants-founders-to-build-in-summer-2026/)
- [How to Apply to YC in 2026 (guide)](https://capwave.ai/blog/blog-how-to-apply-to-y-combinator) · [What YC is looking for in 2026](https://beststartup.us/what-startups-y-combinator-is-looking-for-in-2026/)
- [YC mock interview — the 5 questions](https://www.mergesociety.com/startup-stories/yc-startup)
