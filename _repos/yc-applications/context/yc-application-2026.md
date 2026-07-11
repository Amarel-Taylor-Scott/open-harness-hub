# YC Application — AI Done Right (Baltor.ai) · 2026

**Status:** working draft, owner-ratifiable. **Date:** 2026-06-25.
**Purpose:** the actual YC application answers, synthesized from the canonical strategy set. This doc is the
**single application surface**; it references (does not duplicate) the depth docs and names the source inline.
Anything needing an owner decision (raise size, exact pricing, founder bio) is flagged `⟦OWNER⟧` and must not be
treated as decided.

> **Canonical inputs:** `docs/strategy/yc-master-current-state-business-plan-and-pitch.md` (master) ·
> `first-live-capability-sanctions-screening.md` (who needs it) · `competitive-landscape-2026.md` (competition+moat) ·
> `design-partner-pilot-program.md` (traction) · `founder-market-fit.md` (team) · `decisions-locked-2026.md` (decisions).
> Readiness scorecard: `data/dev-intel/yc-readiness.md` (recompute: `python3 scripts/yc_readiness.py --report`).

---

## Company

- **Name:** AI Done Right (parent) · paid product **Baltor.ai** · open funnel **OpenHubForAI.io**.
- **One-liner (LOCKED, verbatim):** *Models don't fail. Their context does.* — Baltor gives the AI agents you
  already run **verified, current, and provable** context. Pillars: **Verified · Current · Efficient · Provable.**
- **Live demo (ephemeral TryCloudflare — production uses real domains):** the landing hub links every surface;
  the **offline deterministic** demo runs with no cloud: `PYTHONPATH=. python3 scripts/demo_offline_full_baltor.py --self-test`.

---

## What are you making?

**Baltor is a governed Context Engine.** For each fact an agent will rely on, Baltor: **syncs** the source →
**versions + reconciles** conflicting sources (authority wins, losers held out) → **verifies** → **keeps fresh**
(CDC/revocation on volatile facts) → **compresses** → **serves**, with **lineage + a portable receipt on every
served fact**. Agents **PROPOSE** evidence; Baltor **DISPOSES** — model/agent/browser/memory output is *candidate
context, never truth*, and a candidate is never served until it crosses the promotion boundary.

Baltor is **powered by Teleon** (`teleon.dev`) — the runtime that selects *how* each step executes (cheapest-first,
deterministic-substitution), gates promotion on evidence, and meters cost. **OpenHubForAI.io** is the free open
funnel: one site, faceted browse over every hub + registry, where a developer builds the governed workflow that
consumes Baltor. One backend; the join is *one governed object, two doors*.

---

## Why now? (the earned insight)

Frontier models keep improving — which makes **context, not raw capability, the durable bottleneck and the durable
moat**. Every augmented AI workflow needs trustworthy data underneath it, and the "context layer" is being repriced
by consumption (Snowflake, MongoDB, Datadog, Cloudflare on agentic — public-tape estimates, labeled). The
forcing function is regulatory: the **EU AI Act** obligations landing **Aug 2026** make "which fact did the agent
use, and can you prove it?" a compliance requirement, not a nicety. The named infra winners sell *plumbing*; **none
ship enterprise governance — glossary, lineage, entity resolution, receipts.** That seam is the company.

---

## What's new / what do you understand that others don't?

Everyone is racing on *capability*. We bet on the **opposite durable thing**: the moat is **governed DATA +
provenance + freshness + portable receipts + the Determinism Factory** (every expensive bounded-agent resolution
distills *losslessly* into a cheaper deterministic rule/connector over time — so margins improve as the corpus
matures, and the moat compounds). We **verify and prove a fact *before* the agent uses it**, and we manage **fact
state with history** (what changed, when, why, by whose authority). Competitors index, retrieve, or store; none
*verify + package + prove* facts before use. Full map: `competitive-landscape-2026.md`.

---

## Who desperately needs this? (ICP + acute pain)

**Beachhead:** regulated context where a stale or contradictory fact = legal/financial risk — sanctions/OFAC
screening, export controls, vendor/KYC compliance, regulated procurement, legal ops. **Buyer:** the compliance /
BSA-AML / GRC / legal-ops owner whose facts carry legal weight and who **cannot defend "the model said so."**
Today they paper over it with manual review that doesn't scale and leaves no audit trail.

**First live capability:** OFAC SDN name screening — the deterministic verdict is the *one* governed
`serves_truth=true` output. **Starter vertical to win provably:** healthcare-**admin** provider-directory accuracy
(NPI validation, normalization, cross-source confidence, freshness) — synthetic/public data only, **not insurance,
not clinical**. Full: `first-live-capability-sanctions-screening.md`.

---

## How far along are you? (the honest technical truth)

**Pre-revenue, design-partner stage.** The asset is **not traction — it's a working, governed context engine that
already runs end-to-end, offline, deterministically, with the moat mechanics built in.** That is unusual for
pre-seed and it is what we lead with.

- **Deterministic proof gate:** **713 green** as a dated **2026-06-25** snapshot (computed, not hand-typed —
  recompute `PYTHONPATH=. python3 scripts/run_proofs.py`); a watchdog re-runs them continuously.
- **Flagship demo, runs offline:** the **CFPB correctness invariant** — Reg-E "10 business days" served; the 30-day
  FAQ and the narrative allegations **held out**; only the reconciled winner served, with its source authority and
  a receipt. Then **OFAC**: an always-green synthetic conformance test **plus a dated 2026-06-14 `--live` catch**
  against the real SDN list (a planted CLEAR-on-a-designated-entity claim caught + held out).
- **Real infra, switchable:** any task runs on local-emulator / subprocess / k8s / k8s-Job / Cloud Run / Lambda /
  Azure-Function — chosen by **policy + pricebook + health**, cloud-deferred-never-blocking; 30 swappable capability
  slots. Bring-your-own API endpoint or cloud function, governed.
- **Live surfaces:** branded sites for AI Done Right / Teleon / Baltor / AIDevObserver, the OpenHubForAI.io faceted
  browse, a documented Registry REST API, and per-surface BYO-key demos (all currently served over TryCloudflare).

---

## Business model

**Usage meters, not seats:** `source monitored → facts verified → context package served → downstream agent risk
reduced`. **Open-core:** a freezable verified snapshot pulled into an open OpenHubForAI.io harness is **free**; the
**live, kept-fresh** governed serving is **paid**. Ladder: design-partner pilot → Team → Business → Enterprise.
COGS lever: the Determinism Factory turns each expensive resolution into reusable cheap infrastructure. Exact
numbers ⟦OWNER⟧ — see `decisions-locked-2026.md` §B; structure is locked, the figures are owner-ratifiable.

---

## Team (founder-market fit)

Technical founder; **training-free / frozen-model + legal-AI** background — a grain that favors **structural,
deterministic, governance-first** methods, which is exactly this product's spine. The hardest-thing evidence is
citable in the repo: a governed engine that runs deterministically end-to-end, the 713-green proof discipline, and
the Determinism Factory. Personal specifics (employers, dates, shipped systems) are **⟦OWNER⟧** — drafted with
fill markers in `founder-market-fit.md`.

---

## How will you get users?

Founder-led outbound into the regulated-context beachhead + the **OpenHubForAI.io open-source developer funnel** +
**design-partner pilots**. Hook: *"We find the stale and weak facts your agent would otherwise cite."* The pilot
program (offer, target profile, 90-day plan, before/after report template) is program-ready — **no partner signed
yet**, stated plainly — in `design-partner-pilot-program.md`. Seed-readiness gates: 3 design partners, 1 paid
pilot, 1 exported package consumed by a customer's own agent/RAG, measured stale-fact catch + manual-review
reduction.

---

## Biggest risks (and why we survive them)

| Risk | Mitigation |
|---|---|
| No traction yet | lead with the working engine + the proof gate; the asset is the proof, not a logo wall; the design-partner program is built and ready to run |
| Frontier models "close the gap" | the moat is governed DATA + provenance + freshness + receipts, **not** capability — it strengthens as models improve |
| Data-gravity incumbents add governance | be the **agent-neutral, open governed assembler at the seam**; wrap their substrate, don't compete on storage; receipts travel across platforms |
| Regulated-domain liability | assurance-brand discipline — never claim "100% accurate"; review queues, signed publishers, held-out unverified facts, full audit trail |

---

## The ask

⟦OWNER⟧ raise size + use-of-funds (recommended buckets: connectors/source monitoring · worker orchestration ·
verified public context feeds · local+cloud deployment hardening · security/compliance baseline · design-partner
success + founder-led GTM). Recommended default + exactly what to confirm: `decisions-locked-2026.md` §B.

---

*Warrant: written on clear owner intent (the YC push). Grounded in the LOCKED brand, the master pitch doc, the
five supporting strategy docs, and the live proof gate (713 green, 2026-06-25). Pricing, raise size, TAM math, and
founder bio are flagged ⟦OWNER⟧ and are not treated as decided. serves_truth=false.*
