# Design-Partner Pilot Program — AI Done Right / Baltor

> **PROGRAM READY · NO PARTNER SIGNED YET · PRE-REVENUE.**
> This is not a traction page. It is the *program-ready offer + pipeline* — the artifact whose job is to **land
> the first design partner**, honestly. There are **zero signed partners, zero paid pilots, and zero revenue**
> as of 2026-06-25. Nothing below is a customer logo, a testimonial, or a forecast presented as fact. Every
> pricing figure is a draft `⟦DECISION⟧` pending owner sign-off. Where a number describes the repo it is
> **computed and dated**, never hand-typed.

**Anchors (do not contradict):** `docs/strategy/yc-master-current-state-business-plan-and-pitch.md` (master —
§3.3 demo ladder, §4.2 pricing, §8 90-day plan) · `docs/strategy/brand-architecture.md` (brand, LOCKED) ·
`docs/strategy/first-live-capability-sanctions-screening.md` (first live capability) ·
`src/teleon/verticals/provider_directory.py` + `provider_sources.py` (starter vertical).

**Positioning (LOCKED):** *Models don't fail. Their context does.* — *Verified, current, and provable context
for the agents you already run.* Pillars: **Verified · Current · Efficient · Provable.** Stack: **Teleon**
(runtime engine) → **Baltor** (customer-facing governed context, powered by Teleon) → **OpenHubForAI registries** (free
developer funnel, `OpenHubForAI.io`).

---

## 1 · Status banner (read this first)

| Fact | State (2026-06-25) |
|---|---|
| Signed design partners | **0** |
| Paid pilots | **0** |
| Revenue | **$0 — pre-revenue** |
| What *is* real | a working, governed context engine that runs end-to-end, offline, deterministically |
| Deterministic proof gate | **dated snapshot** — recompute, never quote from memory: `PYTHONPATH=. python3 scripts/run_proofs.py` (713 green observed 2026-06-25) |

The asset we sell a pilot on is the **engine + the proofs + the before/after report it can produce**, not a
customer list. Leading with the engine and an honest "no partner yet" is the correct posture for this stage —
overclaiming is fatal to an assurance brand.

---

## 2 · The pilot offer

**Design-partner pilot — `$5k–$25k` fixed `⟦DECISION — ranges pending owner sign-off; see master §4.2⟧`.**
Duration **2–6 weeks**. Scope: **1 corpus, 1–2 authority feeds, one before/after report.** (Mirrors master
§4.2 exactly; the staging footprint is master §3.3 rung 2: managed Postgres + queue + object store + a small
worker pool + one authority feed, ~`$250–$1.5k/mo` infra.)

**What the partner gets**
- A **stale/weak-context audit** of their corpus: the facts their agent would otherwise cite that are stale,
  contradicted, unsourced, or low-confidence — each with a source handle and a portable receipt.
- A **governed context package** they can export and feed to **their own agent/RAG stack** (the join is one
  governed object, two doors — free freezable snapshot via OpenHubForAI registries, live serving via Baltor).
- A **before/after report** (§6) quantifying stale-fact catch, manual-review-hours reduced, and % of served
  facts carrying source + receipt.
- A reconciliation of contradictory authorities with **lineage to the losers** (nothing deleted — losing
  candidates are held out, not destroyed; lossless-distillation discipline).

**What we get (the trade — state it plainly to the partner)**
- The **reference** — the first nameable design partner and the right to describe the engagement (with their
  approval), which unblocks the next three conversations.
- The **data signal** — a real regulated corpus that sharpens connectors, the measured-lift admission gate, and
  the Determinism Factory (expensive resolution → cheap deterministic rule, losslessly).
- A **measured outcome** that becomes the deck's traction slide once it exists.

**Out of scope / honesty rails for the pilot:** synthetic or public metadata only — **no real PII, secrets, or
proprietary dumps**; **no insurance pipelines** (non-compete + repo law); served outputs follow `serves_truth`
discipline (directory/enrichment proposals are `serves_truth=false` CANDIDATES scored by confidence; only a
governed, sourced verdict like OFAC screening is `serves_truth=true`).

---

## 3 · Target partner profile + prospect types

**Beachhead / ICP:** regulated context where a **stale or contradictory fact = legal or financial risk** —
sanctions/OFAC, export controls, vendor/KYC compliance, regulated procurement, legal ops. **Starter vertical:**
healthcare-**ADMIN** provider-directory data (HealthLynked-shape), **synthetic/public only** — never insurance.

**Qualifying signals (a good design partner has all three):**
1. Runs an LLM agent / RAG workflow over a corpus where a wrong cited fact carries audit, legal, or money risk.
2. Already pays the pain in **manual review hours** ("an analyst re-checks what the agent says").
3. Has no audit trail — **cannot today prove which facts are safe to serve.**

**Company archetypes (illustrative ICP shapes — NOT claimed customers, no real logos):**

| Archetype | Why the context layer is their pain |
|---|---|
| Mid-market fintech / payments / neobank with a sanctions-or-KYC obligation, building an internal agent | sanctions lists + KYC facts go stale daily; a missed designation is a regulatory event |
| Export-controls / trade-compliance software vendor or an exporter's compliance team | entity/denied-party lists change; contradictory sources must be reconciled with lineage |
| Third-party / vendor-risk (TPRM) platform or risk team | vendor facts drift; "which record is current?" has no receipt today |
| Regulated procurement / GovTech procurement team | eligibility + debarment facts must be current and provable |
| Legal-ops / contract-intelligence team in a regulated enterprise | agents cite superseded clauses/policy; needs held-out + versioned facts |
| Healthcare-**admin** provider-directory data team (starter vertical) | directory rows go stale; `provider_directory.py` proposes `serves_truth=false` candidates with confidence + audit |

**Buyer persona (who signs):** Head/Chief Compliance Officer, Head of Financial Crime / Sanctions, VP Risk or
Third-Party Risk, or Head of Legal Ops — the person accountable when an agent cites a bad fact. **Champion (who
brings us in):** the engineering/ML lead building the RAG/agent who keeps hitting the stale-data wall.

**How to source the list (no cold-list purchase, no fabrication):**
- **Founder-led outbound** to the personas above in the beachhead segments — warm intros first, then targeted
  direct outreach.
- **The OpenHubForAI registries developer funnel (`OpenHubForAI.io`):** developers who adopt the open spec/SDK/harness and
  hit "my agent cites stale facts" **self-identify the company that needs Baltor.** The free funnel is the
  top-of-pipe; the pilot is the conversion.
- **Inbound from the demo:** the OFAC / CFPB correctness demo + a sample before/after report act as the lead
  magnet that earns the first call.

---

## 4 · The outbound motion + the hook

**Hook (use verbatim — master §5 slide 11):**
> **"We find the stale and weak facts your agent would otherwise cite."**

**Motion (founder-led, low-friction → paid):**
1. **Reach** the champion or buyer with the hook + one concrete artifact (the OFAC held-out-violation catch, or
   a CFPB "which authority wins" reconciliation). No deck on first touch.
2. **Free stale-fact audit (30–45 min):** run the engine over a **small sample of their public or synthetic
   corpus** (never their private data on first contact) and return a one-page mini-report — caught stale/weak
   facts, each with a source handle.
3. **Convert** the mini-report into the **paid design-partner pilot** (§2) on their real corpus, scoped to 1
   corpus + 1–2 authority feeds.
4. **Deliver** the full before/after report (§6) and the **exported governed package consumed by their own
   agent/RAG** — the single most important external proof point (master §8.2).

**Why the hook converts:** it names a pain the buyer already feels, it's **demonstrable in minutes** on public
data, and the deliverable (caught facts + receipts) is legible to a compliance buyer without an AI background.

---

## 5 · The 90-day pilot plan (maps to master §8)

| Phase | Weeks | Goal | Definition of done |
|---|---|---|---|
| **A — Pipeline** | 0–3 | Source the list; run free stale-fact audits | ≥3 audits delivered to qualified ICP prospects |
| **B — Land 3 design partners** | 2–6 | Convert audits → signed (paid or unpaid) design-partner agreements | **3 design partners** engaged with real corpora (master §8.1) |
| **C — 1 paid pilot** | 4–10 | One partner on the `$5k–$25k ⟦DECISION⟧` paid pilot | invoice issued; staging stood up (master §3.3 rung 2) |
| **D — Export + consume** | 8–12 | Export a governed package **consumed by the customer's own agent/RAG** | downstream system ingests the package (master §8.2) |
| **E — Quantify** | 10–13 | Produce the before/after report; it becomes the traction slide | report §6 filled with **measured** numbers |

Parallel, non-blocking: the **burst demo** (flip one worker lane to Cloud Run Job / KEDA on staging — master
§8.4) proves the multi-cloud/scalable story but is **not** a gate for landing the first partner. If outbound on
one segment stalls, switch segments rather than stop — the beachhead has five named shapes plus the starter
vertical.

---

## 6 · The before/after report template (the single most important external proof)

Fillable. Every cell is a placeholder until a real pilot produces a **measured** value — do **not** pre-fill
with aspirational numbers. Counts come from the run, not from prose.

```
BALTOR DESIGN-PARTNER PILOT — BEFORE / AFTER REPORT
Partner (archetype/segment): __________________________   Pilot dates: ____ → ____
Corpus: ____________________   Authority feed(s): ____________________   (synthetic/public only)
Engine commit + proof snapshot: ____________  (PYTHONPATH=. python3 scripts/run_proofs.py → ____ green, dated ____)

┌────────────────────────────────────────────────┬──────────────┬──────────────┬───────────┐
│ Metric                                          │ BEFORE       │ AFTER        │ Δ         │
├────────────────────────────────────────────────┼──────────────┼──────────────┼───────────┤
│ Stale / weak-context facts caught (count)       │ ____ unknown │ ____ flagged │ ____      │
│   — stale (out-of-date vs authority feed)       │ ____         │ ____         │ ____      │
│   — contradicted (conflicting authorities)      │ ____         │ ____         │ ____      │
│   — unsourced / low-confidence                  │ ____         │ ____         │ ____      │
│ Manual review hours per cycle                   │ ____ hrs     │ ____ hrs     │ ____% ↓   │
│ % of served facts with source handle + receipt  │ ____%        │ ____%        │ ____ pts  │
│ Facts reconciled with lineage to losers (held)  │ n/a          │ ____         │ —         │
│ Cost per 1,000 facts verified (if measured)     │ ____         │ ____         │ ____% ↓   │
└────────────────────────────────────────────────┴──────────────┴──────────────┴───────────┘

EXPORTED GOVERNED PACKAGE
  Package id / hash: ____________   Downstream consumer (agent/RAG): ____________
  Consumed successfully?  ☐ yes  ☐ no     Evidence / receipt path: ____________

ATTESTATION (honesty)
  ☐ Synthetic / public data only — no real PII, secrets, or proprietary dumps.
  ☐ No insurance corpus involved.
  ☐ serves_truth honored: candidates labeled serves_truth=false; only governed verdicts serves_truth=true.
  ☐ Every "AFTER" number is MEASURED from this run (no estimates presented as results).
  Partner sign-off: ____________   Date: ____
```

The four headline metrics — **stale/weak facts caught**, **manual-review hours reduced**, **% facts with
source + receipt**, and **an exported package consumed downstream** — are exactly the four the seed deck's
traction slide needs (master §5 slide 13). The report is the deliverable that converts an unsigned program into
a signed one.

---

## 7 · Success gates (seed-readiness — verbatim with master §8 / §5 slide 13)

The program is "done" — and the deck's traction slide becomes honest — when **all four** hold, each backed by an
artifact, not an assertion:

1. **3 design partners** engaged with real corpora.
2. **1 paid pilot** (invoice issued).
3. **1 exported governed package consumed by a real downstream agent/RAG stack** (evidence/receipt on file).
4. **Measured** stale-fact catch **and** manual-review reduction (a filled §6 report, not estimates).

Until then, this document is exactly what it says on the banner: **program ready, no partner signed yet,
pre-revenue.** That honesty is the feature — it is the artifact that lands the first one.

---

*Warrant: clear user intent (this request) to write the design-partner program doc; anchored to the LOCKED brand
and the master plan (§3.3 demo ladder, §4.2 pricing, §8 90-day plan), citing only file anchors verified to exist
on 2026-06-25; all pricing flagged `⟦DECISION⟧` (no unilateral pricing call), proof count presented as a
dated/recomputed snapshot (never a hardcoded magic number), and every honesty rail — pre-revenue, no signed
partner, no fabricated traction, synthetic/public only, no insurance, `serves_truth` framing — held explicitly.*
