# GTM — Teleon + Baltor first, phased public launch for everything else (2026-06-21)

Synthesis of three parallel surface reviews (Teleon, Baltor, all-surfaces launch-readiness). Lead with the two
ownable products; stage every other surface to go public in waves tied to press/marketing. Grounded in
`architecture/surface_map.json`, the go-live gate (`scripts/check_teleon_go_live_readiness.py`), and the live OFAC
receipt (`data/live-receipts/`). Brand/pricing/structure here are PROPOSALS — owner-gated per the change-verification contract.

## 0. The one-paragraph story
A holding brand (**AI Done Right**) over two products on one engine: **Baltor** makes an agent's context **Verified,
Current, Provable** ("models don't fail — their context does"); **Teleon** is the thin control plane that **descends**
any capability to the cheapest bounded version that still passes, receipt-backed, while compute runs on the customer's
own account. The shared beachhead is **regulated/compliance context**, where *provable + current + cheaper* is worth real money.

---

## 1. Teleon GTM
- **Wedge:** a thin control/metadata plane that picks + governs + *learns* the cheapest bounded version of a capability that still meets your bar (receipts), while compute runs on your account — the moat is the accumulated **descent brain**, not the compute.
- **ICP:** (primary) **AI-agent / agent-builder teams** — the Agent Capability Gateway is built + redteamed; sell *stable, receipt-backed CapabilityTasks they call instead of burning tokens.* (secondary) platform/eng teams bleeding on unpredictable frontier spend, especially in regulated orgs (BYO-account + receipts lands hardest there).
- **Pain / why-now:** unbounded frontier spend on tasks that don't need a frontier model, with no proof of which cheaper path is safe — and no way to keep that current as models change. Now: frontier cost is top-of-mind, edge inference makes BYO-compute trivial, and the market pays for *execution* but **nobody sells governed *selection + learning* with portable receipts.**
- **Proof today (all passing):** `demo_dashboard` (extraction 46.7% / enrichment ~86% measured savings); `check_teleon_example_descents`, `check_teleon_control_plane` (external run recorded into the brain without Teleon executing it → `guide_next` recommends the next move = the thin-plane thesis), `check_byo_compute` + `check_execution_provider_factory` (Cloudflare/K8s/serverless behind one port). The **honest** gate (`check_teleon_go_live_readiness`, `go_live_ready=False`) is itself a trust asset — show it.
- **Pricing (proposal):** charge for governed selection + learning + receipts, **never compute** (BYO). Starter $0 → Team ~$249/mo → Enterprise custom; defensible model = **per-active-capability + a value/savings share**, with eval/improvement-compute as the metered axis.
- **Biggest risk:** every headline number is "representative," not live — no customer has seen Teleon descend *their* task on *their* data yet. **Launch-gating fix:** wire ONE live lane (Ollama/Cloudflare Workers AI — already adapter-ready) against ONE real benchmark.

## 2. Baltor GTM
- **Wedge:** a governed context engine — Verified · Current · Provable context, with a **held-out-stale receipt an examiner accepts**. NOT "more lists."
- **ICP:** **Compliance / AML / BSA lead at a fintech, neobank, payments processor, or crypto on-ramp (Series A–C)** already running sanctions screening and bleeding on false positives + audit-defensibility. Secondary: regulated-enterprise legal-ops.
- **Pain / why-now:** screening is legally mandated; a missed match = fine, false-positive flood = analyst cost. They pay for **accuracy + a current list + an audit trail.** Now: the OFAC SDN list changes daily (a *structurally permanent* gap no model can close), agentic automation makes unverified context dangerous, and the "context layer" thesis is validated.
- **Proof today (passing):** the **live OFAC run that caught a real would-be violation** (`check_live_ofac_receipt` — a dated receipt; internal doc said "clear", the live SDN list said "listed" → held out); the end-to-end `verified_context_flow` (ingest → assurance → tier+serve, deterministic re-run). **This receipt is the closer.**
- **Pricing (proposal):** design-partner pilot **$5k–$25k** (2–6 wks, before/after report) → Business **$6k–$15k/mo** → Enterprise **$40k+/yr**; meter on monitored sources / facts-under-management / verification jobs.
- **Biggest risk:** leading on *coverage* loses to incumbents (LexisNexis Bridger, ComplyAdvantage, Dow Jones, World-Check). **Win on the receipt + CDC freshness + "we caught your own stale clear."** Launch-gating fixes: (a) promote the LIVE sanctions pipeline + demote the SYNTHETIC rigged-baseline harness (`scripts/wedge/*` — its "50% lift" is self-fulfilling; re-baseline against a real model, never put it in a deck); (b) render the receipt as the hero of the buyer-facing demo (today a 26-line stub).

## 3. Shared motion
**Proof-first, design-partner-led, compliance beachhead.** Both products converge on the regulated buyer: Baltor proves *the context is true + current* (the receipt); Teleon proves *we run it cheaper + bounded, on your infra, and it learns.* Sell them together to the same compliance/fintech ICP: "verified, current, provable context (Baltor), executed cheaply + governed on your own compute (Teleon)." Land with a **paid pilot** producing a before/after report; expand to the monthly governed layer.

---

## 4. Phased public-surface launch
Lead with the two ownable marks; stage everything else behind press/marketing beats. (Per the all-surfaces audit: "9 live" is mostly a roster flag over prototype shells on ephemeral tunnels — treat "live" as *owner-cleared to be public*, not *publicly served*.)

- **Wave 1 — the products.** `aidoneright.dev` (parent landing) + `baltor.ai` + `teleon.dev` + the `teleon-demos` proof page. Gate: the founding launch announcement + first design-partner outreach.
- **Wave 2 — the OSS ecosystem.** OpenHarnessHub (lead) + OpenContextHub/OpenSkillsHub/OpenToolsHub. Gate: an OSS/dev-community beat (Show HN / "open CapabilityTask spec" release), ~2–4 weeks after Wave 1, once the products are public.
- **Wave 3+ — remaining live hubs, then private-bench flips.** OpenBenchmark/MCP/Compression/Review/SkillToTool, then the 13 private hubs flipped `private→live` one at a time, each tied to its own press story (Routing → model-routing campaign; Receipt → provenance campaign). The `futureAccent` swap makes each a one-line, on-message launch.

### Per-wave gates
- **Wave 1 (highest bar):** resolve the **7 blocking go-live seams** (`check_teleon_go_live_readiness` → `True`): hosting deploy + container-e2e, live LLM adapters + live source/CDC, real eval data, Postgres/pgvector + DB-enforced promotion boundary, auth + per-tenant isolation. Finalize the **brand/trademark** (aidoneright.dev registration + `teleon` mark adjacency — owner-gated). Lead Baltor with the **live receipt**, not the synthetic harness.
- **Wave 2 (OSS):** real registry rows behind the Context/Skills/Tools hubs (the ~1.9KB shells → populated registries); OpenHarnessHub spec + harnesses + a contributor path; stable OSS hosting (off ephemeral tunnels); "discovery ≠ trust" copy on every hub.
- **Wave 3+ (per hub):** real content + an owner-cleared open-trigger before each `status: private→live` flip; update the roster in the SAME change so the family check stays green (no orphaned counts).

### Keeping private surfaces safe
Render private hubs as visible **"Coming soon"** cards (muted accent, **non-navigable** — drop the `url` while `status:'private'`); make `check_ai_done_right_surface_family.py` the single gate (`status:'live'` ⇒ a real, non-stub page); exclude `dist/sites/openharness-design/` (the internal design bundle) from every public deploy.

---

## 5. Are we positioned to review + improve ALL surfaces continuously? — Yes
The machinery exists and is proven: `surface_map.json` (every surface + wedge + comms), the **multi-model improvement loop** (reviews planes/wedges/business/design/presentation/integration/architecture with Kimi + GLM, resilient + perpetual), the **research radar** (competitors/market-gaps), the **panel review** board, and **plane separation** (dev research quarantined from product serving). This GTM's launch-gating fixes become the loop's near-term priorities; the loop keeps the surfaces improving + adapting over time against exactly these principles (flexibility, wedge, market fit, adaptability).

## 6. Honest state (what's real vs representative)
- Teleon engine: **built + 6/6 proof-gated**, `go_live_ready=False` (7 seams). Savings numbers: **representative** until one live lane runs on real eval data.
- Baltor: the **live OFAC receipt is real** (caught a real catch); EU/UN/BIS lists are seams; the synthetic lift harness must be re-baselined.
- Surfaces: products have real built UIs; most hubs are prototype shells on ephemeral tunnels — content-gated, not infra-gated.
