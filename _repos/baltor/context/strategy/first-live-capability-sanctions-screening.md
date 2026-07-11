# First Live Capability + "Who Needs It" — OFAC Sanctions Screening, Provider-Directory Starter Vertical

**Status:** canonical scope doc for the first live capability + the YC "who needs it" answer (additive).
**Date:** 2026-06-25. **Anchor:** `_repos/shared-backend-components/docs/strategy/yc-master-current-state-business-plan-and-pitch.md` (the
master positioning doc — when this doc and the master disagree, the master wins). This doc does **not**
re-open brand, pricing, or strategy; it names the buyer, the acute pain, and the wedge.

> **Positioning (from the anchor, used verbatim):** Parent **AI Done Right** (`aidoneright.dev`).
> Three layers: **Teleon** (`teleon.dev`) = the purpose-driven, eval-gated runtime SaaS (the engine);
> **Baltor** (`baltor.ai`) = the applied, customer-facing **governed context** product, *powered by Teleon*;
> **OpenHubForAI registries** (consolidating under `OpenHubForAI.io`) = the free open developer funnel.
> One-liner (LOCKED): *"Models don't fail. Their context does."* /
> *"Verified, current, and provable context for the agents you already run."*
> Pillars: **Verified · Current · Efficient · Provable.**
> Stage: **pre-revenue, design-partner stage.** The asset is a working governed context engine that runs
> offline + deterministically with the moat mechanics built in — **not traction.**

---

## 1 · The named ICP (who, exactly)

We sell to the person who is personally accountable when a wrong fact reaches a regulator, an auditor, or a
customer — **not** the person buying a faster model.

**Primary buyer / champion (the OFAC wedge):**
- **Title:** Head of Compliance · BSA/AML Officer · Sanctions Compliance Lead · Head of Regulatory
  Operations · GRC owner · Legal-Ops lead.
- **Company type:** a **regulated-context buyer** — fintech / payments / B2B marketplace / lender /
  procurement or vendor-risk team — that has started routing screening, KYC, vendor onboarding, or
  policy Q&A through an LLM agent or a RAG stack and now owns the blast radius when that agent is wrong.
- **Job to be done:** *"Before my agent acts on a fact, prove it is current, sourced, and safe to serve —
  and give me the audit trail when someone asks why."*

**Starter-vertical buyer (the provable first win — see §5):**
- **Title:** Director / VP of **Provider Data** · Directory Integrity · Data Operations · Master-Data lead.
- **Company type:** a **healthcare-administration data** company or provider-network operations team
  (administrative directory data only — name, NPI, specialty, practice, address, phone, website, status).
  The named design-partner / competition target that motivated this vertical is **HealthLynked**; treat it
  as a *design-partner target, not a closed customer* — we are pre-revenue.

These are the same buyer in two postures: someone whose **facts carry legal/financial/regulatory weight**
and who cannot defend "the model said so." We do **not** sell to teams whose only metric is model quality.
No named customers, logos, or traction are claimed anywhere in this doc.

---

## 2 · The acute pain (what breaks today)

The buyer has already adopted agents/RAG. The capability is fine; the **context underneath it rots**, and
three failures recur, in the buyer's own words:

- *"Our agents cite stale policy."* The fact was true last quarter; the list changed; nobody re-verified it.
- *"Our documents disagree."* Two sources say different things; the retriever returns whichever scores higher
  on cosine similarity, with no notion of which one has authority.
- *"We don't know which facts are safe to serve."* There is no boundary between a verified fact, an
  unverified candidate, and a narrative allegation — they all flow to the agent identically.

**The cost of a single stale or contradictory fact** in this buyer's world is not a bad demo — it is a
sanctions hit cleared as "OK," a regulator-facing answer citing superseded law, a vendor onboarded against
a designated entity, a directory that bills or routes to a provider who moved or went inactive. That is
**legal, financial, and regulatory exposure**, not UX polish.

**Why manual review doesn't scale.** Today the buyer papers over this with humans re-checking facts. That is
linear in volume, slow, inconsistent across reviewers, and reviewers tire exactly when volume spikes. Either
they review everything (cost explodes) or they sample (the miss they fear slips through).

**No audit trail.** When the regulator or the customer asks *"why did your system serve this?"*, the honest
answer today is a vector-similarity score. There is no source authority, no lineage, no receipt, no record
of what was held out and why. The buyer is exposed precisely at the moment they need to defend a decision.

---

## 3 · Trigger event + why now

- **Forcing function — the EU AI Act and its peers.** Obligations for high-risk and general-purpose AI
  systems are phasing in, and "the model decided" is not a compliant answer. Regulated buyers now need
  **provenance, data governance, and an audit trail on the facts their AI acts on** — a documentation
  burden they cannot satisfy with retrieval scores. This converts "nice to have" into a dated deadline.
- **Frontier models make context the durable bottleneck.** As raw capability keeps improving, the thing
  that stays broken is the **data underneath** — staleness, contradiction, missing provenance. A better
  model cannot know today's OFAC list or which of two conflicting documents has authority. So context, not
  capability, becomes the durable moat *and* the durable failure mode. (Anchor §3.)
- **The context layer is being repriced by consumption.** The public tape (SNOW/MDB/NET, per the anchor)
  validated a **consumption-priced context layer**: monitored sources → facts verified → packages served.
  A buyer can adopt a governed context layer **per-use, alongside the stack they already run**, instead of
  re-platforming. The wedge is buyable today without ripping anything out.

---

## 4 · The first live capability — OFAC SDN name screening

**Why this one first.** It is the most bounded, most deterministic capability in the portfolio (the cleanest
Teleon descent: an LLM guess collapses to a deterministic fuzzy-match against the *current signed* OFAC SDN
list); the authoritative source is public and already governed (`source_handle ctx://ofac/sdn`); it is a
**textbook durable gap** (the list changes daily — no model can ever hold it); and the verdict carries legal
weight, so provenance + receipt is non-negotiable. The SDN list is public, so there is **no real PII**.

**The wedge, precisely.** The buyer submits the names/entities their workflow wants to clear (counterparties,
vendors, customers) plus any internal "this entity is CLEAR / known-good" claims. The engine fetches the
**current signed SDN list**, content-hashes it, runs deterministic exact + fuzzy matching, and emits a
**verdict**: `designated` / `clear` / `near-match → review`.

**The crux that proves the whole thesis.** The screening **verdict is the ONE governed
`serves_truth=true` output** — a deterministic computation over a *signed authoritative source*, carrying a
portable **receipt** (list version + content hash + match lineage). It is **not an LLM opinion.** This is the
single legitimate place the system asserts truth. Everywhere else — LLM, agent, browser, and memory output —
stays `serves_truth=false` (candidate context, never served as truth). A borderline fuzzy near-match is never
auto-cleared; it routes to a `review_ticket`.

**The dated proof (honest framing).**
- **Always-green offline conformance:** a synthetic-fixture self-test fires on every run —
  `PYTHONPATH=. python3 _repos/shared-backend-components/scripts/ingest/sanctions_feed_live.py --self-test`.
- **A dated `--live` catch:** on **2026-06-14**, a real `--live` run fetched the production SDN list
  (content hash `e30f6077…`, `19,065`-row source; this dated run parsed a 5-row sample) and caught a
  **planted, synthetic** would-be violation — an internal claim asserting entity `OFAC-36` is CLEAR while
  the live list **designates it** (program `CUBA`). The bad claim was **held out of the served corpus**;
  `served_as_truth=false`. The clearing claim is the demo's adversarial **input**; the live fetch + hash are
  real. Receipt: `_repos/shared-backend-components/docs/strategy/evidence/ofac-live-run-2026-06-14.json`. This is a dated attestation, **not**
  a republication of the SDN feed.

This sits on the same governed engine as the flagship **CFPB correctness invariant** (Reg-E "10 business
days" served by authority; the 30-day FAQ and the narrative allegations **held out**; only the reconciled
winner served, with lineage + receipt) — so the buyer sees one engine, two regulated proofs.

---

## 5 · The starter vertical — "win one vertical provably"

**Depth before breadth.** One vertical must be proven, end-to-end, to a paying buyer before we widen. The
chosen vertical is **healthcare-administration provider-directory data** — administrative directory fields
only (name, NPI, specialty, practice, address, phone, website, status). **Synthetic / public metadata only;
no real PII.** The scope guard is explicit and enforced: this vertical **excludes insurance and excludes
clinical / PHI data** entirely.

**The concrete first win: provider-directory accuracy + freshness.** Keep a provider directory *current and
correct* with governance built in (`_repos/teleon/backend/src/teleon/verticals/provider_directory.py`):
- **NPI Luhn validation** (`validate_npi`) — reject structurally invalid identifiers before they propagate.
- **Normalization** of phone / address / text fields to a canonical form.
- **Match** — NPI-exact plus bounded fuzzy match (`match_records`).
- **Cross-source agreement confidence** (`field_confidence`) — authority × coverage across sources, not a
  single scrape.
- **Decision boundary** (`decide_action`) — high-confidence cross-source-agreed change → `auto_update`;
  conflict or low confidence → `human_review`; **no unsafe write**; honest-MISSING when unknown; full audit
  trail on every decision.
- **Batch + lifecycle** — `freshness_run`, `find_duplicates`, `detect_inactive`, `detect_movement`, and a
  `cost_per_1000` meter showing the governed path is **far cheaper than naive always-LLM + review-everything**
  (the directory resolution is itself a governed **recommendation**, `serves_truth=false` — confidence +
  receipt + review routing, never an unsourced assertion).

**Source descent (cheapest-first, governed)** — `_repos/teleon/backend/src/teleon/verticals/provider_sources.py`: free public
registries (NPI / CMS) → the buyer's **own browser** against the practice website / state board → paid
search → grounded search → stealth **last**. A field that free registries cover uses **no paid API**;
own-browser-before-paid; honest-offline when a rung is unavailable.

**Why directory, not something flashier.** It is a textbook Baltor(truth) + Teleon(efficiency) problem with a
named design-partner target, public/synthetic data, and a hard dollar metric (records kept correct per
dollar). It generalizes to *hundreds* of licensed/credentialed-entity directories — but we **prove this one
first** and resist the breadth temptation.

---

## 6 · Before / after — what the buyer actually sees

**Before (the buyer's stack today):**
- Directory rows and policy facts drift silently; the agent confidently cites a phone that moved, a provider
  who went inactive, a duplicate record, or a superseded rule.
- Every fact looks identical to the retriever — verified, unverified, and contradicted all score on cosine
  similarity with **no provenance and no authority**.
- Review is all-or-nothing: humans re-check everything (cost) or sample (risk). No audit trail when asked why.

**After (Baltor, powered by Teleon):**
- Every served fact carries a **confidence + source handles + a portable receipt + lineage**; contradicted,
  unverified, and held-out facts are visibly **held out**, not silently served.
- **High-confidence, cross-source-agreed** updates auto-apply; conflicts, low-confidence, and near-matches
  route to a **bounded human-review queue** — manual review shrinks to the fraction that genuinely needs a
  human, instead of the whole stream.
- The buyer exports a **governed context package** (the reconciled facts + lineage + receipts) that their
  **own agent / RAG / CRM consumes** — they keep their stack; we govern the facts before the agent uses them.

**What the design-partner pilot *measures* (these are the pilot's metrics, not claimed results):** stale /
weak facts caught before the agent could cite them; manual-review reduction (share auto-resolved at high
confidence); cost-per-1,000 records vs. always-LLM + review-everything; freshness lag; hallucinated-citation
rate driven toward zero. These become the before/after report — the single most important external proof
point on the path to seed (anchor §8).

**Engine state behind the demo (computed, dated — never a hardcoded fact):** the deterministic proof gate is
**⟦computed: 713 green, dated 2026-06-25 snapshot⟧**; recompute with
`PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_proofs.py`. The full offline demo runs with
`PYTHONPATH=. python3 _repos/shared-backend-components/scripts/demo_offline_full_baltor.py --self-test` — no cloud, no network LLM, no pip.

---

## 7 · Why they can't get this from incumbents

Enterprise search (Glean), RAG platforms, vector DBs (pgvector / Qdrant), and knowledge graphs are all
**retrieval-and-ranking** systems. They will faithfully return a stale, contradictory, or fabricated fact
with high similarity and **zero provenance** — because **verification is not their job.** Specifically, none
of them, on their own:

- **reconcile** conflicting sources by *authority* (Reg-E beats an FAQ; a signed list beats an internal memo);
- **hold out** unverified or contradicted facts from what the agent is allowed to serve;
- attach a **portable receipt + lineage** that survives across platforms and defends a decision to an auditor;
- track **freshness / CDC** on volatile facts so "true last quarter" doesn't get served as true today;
- compute a **deterministic verdict over a signed source** (the OFAC `serves_truth=true` output).

So we **wrap, not replace** them: pgvector/Qdrant, memory frameworks, parsers, and bounded agents become
**governed, measured-lift components** under one provenance + receipt contract (anchor §2.2). The buyer keeps
the stack they already run; Baltor governs the **facts** before the agent acts on them. The moat is the
**governed data + provenance + freshness + portable receipts + the Determinism Factory + the measured-lift
admission gate** — **not** "capability the next model can't reach" (anchor §7, risk row 2).

---

*Warrant: written on clear owner intent for the YC "who needs it" push, grounded in the master positioning
doc (`yc-master-current-state-business-plan-and-pitch.md`) and the live artifacts it cites — the OFAC
self-test + the dated 2026-06-14 `--live` receipt (`_repos/shared-backend-components/docs/strategy/evidence/ofac-live-run-2026-06-14.json`),
the provider-directory modules (`_repos/teleon/backend/src/teleon/verticals/provider_directory.py`, `provider_sources.py`), and the
deterministic proof gate (computed/dated, recompute `PYTHONPATH=. python3 _repos/shared-backend-components/scripts/run_proofs.py`). Pre-revenue;
no traction, customers, or logos are claimed; the OFAC verdict is the only `serves_truth=true` output;
synthetic/public data only; insurance and clinical scope are excluded by design. No brand, pricing, or
strategy decision was made here — those remain owned by the master doc and the owner.*
