<!--
  Transcribed from the owner's external research (2026-05-28). Addendum to
  external-research-brief-2026-05-28.md. Regulatory facts here are VOLATILE BY
  DESIGN — that volatility is the thesis. Treat every dated fact as a snapshot,
  version it in metadata, and re-verify on a cadence. First code increment lives
  in scripts/acquisition/cell_priority.py (§1–§2).
-->
# OHH Collection-Grid / Corpus-Acquisition Subsystem — Build Spec

**Premise:** if you ask an LLM what to collect, it returns the head of the
distribution — the things models already know. Closing the gap requires
*systematically collecting the negative space*: cells that are high-value and
under-covered. This subsystem is how OHH builds its own corpus aggregators
instead of being anchored to model priors.

## 0. One principle

> **Collect the negative space, not the head.** Cell selection is driven by
> *external importance signals + a measured coverage map*, never by what a model
> proposes. The grid is the search space; the capability-lift gate (lifted one
> level) is the value function that decides what to acquire next.

## 1. The dimensional grid (search space, not a plan)

A **cell** is the unit of acquisition:
`cell = (jurisdiction, industry, source_type, time_window, publisher_type, use_case)`

- **jurisdiction:** PH, ID, VN, NG, KE, … (ISO 3166 + sub-national where needed)
- **industry:** NACE/ISIC-aligned (labor, banking/AML, customs, GxP, food safety, …)
- **source_type:** primary regulator, gazette, court, standards body, secondary aggregator, trade press, social channel
- **time_window:** issuance date bucket (enables "fast-changing" targeting + CDC)
- **publisher_type:** government primary, government social, law firm/secondary, NGO/standards, expert
- **use_case:** screening, eligibility, classification, due-diligence, reporting, …

The full grid is combinatorially huge. **You cannot crawl it.** Everything below
is about searching it efficiently. → `scripts/acquisition/cell_priority.py:Cell`.

## 2. The value function (guided acquisition)

```
cell_priority =
      w1 * expected_lift      # how badly base models fail here (lift gate, lifted one level)
    + w2 * pays               # buyer budget / mandate in this cell
    + w3 * sourceable         # tier score: how reachable are authoritative sources (§6)
    + w4 * volatility         # regulatory-change velocity (more churn = more recency-based lift)
    - w5 * current_coverage   # how much we ALREADY hold (the negative-space term)
    - w6 * acquisition_cost   # crawl + parse + maintain effort
```

`expected_lift`, `volatility`, `pays` come from EXTERNAL signals, **not** an LLM.
`current_coverage` (from the coverage instrument, §7) is subtracted — that is what
forces the system toward empty cells. Re-score continuously; a fresh major
issuance jumps the queue. Implemented in `scripts/acquisition/cell_priority.py`.

**External importance signals (model-independent):** regulator issuance frequency;
enforcement actions / fines / FATF grey-black-list status / sanctions designations;
buyer demand + **query-miss logs** (questions the registry couldn't answer — the
purest negative-space signal); legislative trackers, gazette RSS, court dockets.

## 3. Agent roster (specialized "browser agents")

1. **Cell-Selector** — maintains the §2 priority queue; picks the next cell. *No LLM cell-invention.*
2. **Source-Discoverer** — finds authoritative publishers/endpoints; writes the per-cell source registry (§4).
3. **Harvester (browser/agent)** — pulls issuances (paginated lists, ASPX/JS forms, PDF repos, RSS). Tier-aware (§6).
4. **Normalizer + Dedup** — extracts {title, number, issuing body, effective_date, supersedes, body_text}; OCRs image-PDFs; LSH/SimHash dedup.
5. **Verifier** — confirms authenticity (domain, signature/seal); assigns confidence + tier; routes uncertain items to review.
6. **CDC-Monitor** — watches each source for changes; diffs, re-harvests, and **revokes/flags** downstream facts (the moat feature).
7. **Human-Router** — Tier-4 + low-confidence items → verified publisher/expert for signed capture.

## 4. Two-pass acquisition + per-cell source registry

```
source_registry[cell] = [
  { publisher, publisher_type, base_url, issuance_types[],
    access_method, format, has_delta_feed, cadence, tier, last_checked } ]
```
**Pass A** discovers *where* a cell's truth lives (once); **Pass B** harvests
repeatedly and cheaply against only registered sources (bounded, auditable).

## 5. Governance travels with every harvested fact

Every record carries: `source_url`, `retrieved_at`, `effective_date`,
`issuing_body`, `source_version/identifier` (CELEX/ELI for EU; circular number +
date for PH), `supersedes` pointer, license, and a signature (C2PA-style manifest;
verified-publisher facts also carry a W3C VC/DID signer). **A fact with no
provenance + date is not admitted.** An un-versioned corpus decays into the same
staleness as a model — the CDC/maintenance loop is the real recurring cost.

## 6. Tier-aware routing (where browser agents stop)

| Tier | Source shape | Agent | Notes |
|---|---|---|---|
| **1** | Clean API / delta feed (OFAC SLS, Federal Register API) | Harvester (direct) | Cheapest; near-solved. |
| **2** | Structured, no clean API (paginated lists, ASPX search, PDF repos — DOLE, BSP) | Harvester (browser) + Normalizer/OCR | Bulk of reachable tail; *dedicated per-source harvesters*, not generic crawl. |
| **3** | Unstructured but addressable (scanned-image PDFs, secondary aggregators) | Harvester + OCR + Verifier | Lossy; verify against primary. |
| **4** | Un-addressable / ephemeral (regulator Facebook/WhatsApp, oral practice, login-walled) | **Human-Router → verified publisher** | Browser agents do **not** close this. |

**Do not let the roadmap claim automated Tier-4 coverage.**

## 7. The coverage instrument (measure your negative space)

Maintain a **coverage matrix**: per cell, estimate `held_facts`, `freshness`
(median age vs issuance cadence), `completeness` (held vs discoverable issuances).
Derive `current_coverage` (feeds §2) + a **gap report** (high-importance ×
low-coverage = the build queue). Feed **query-miss logs** continuously — every
unanswered question is a labeled hole. Surface coverage per cell in-product
("PH labor: 94% of DOLE issuances since 2018, freshest 6 days").

## 8. Worked examples (real, 2026 — verify)

**Cell A — Philippines × Labor × DOLE.** Publishers: dole.gov.ph + bureau
subdomains (bwc, ils), regional offices; FOI portal; secondary aggregator
library.laborlaw.ph; law-firm alerts. Issuance types: Labor Advisories,
Department Orders, Joint Circulars — paginated PDFs across subdomains, amendment
suffixes ("DO 204 A-19" amends "204-19"). **Tier 2–3**, volatility medium, pays
medium, sourceable medium. Signal: practitioners already pay aggregators because
the primary is unusable → validated demand + competitive comparable.

**Cell B — Philippines × Financial-crime × BSP+AMLC.** Publishers: BSP
(Circulars + MORB/MORNBFI), AMLC, SEC, Insurance Commission; **Tier-4 channel:**
BSP posts "BSP UPDATE" announcements on its Facebook page. **Volatile-fact proof
(LLM-blind, harvester-certain):** *BSP Circular No. 1230 (27 Feb 2026)* doubled
the cash-withdrawal scrutiny threshold ₱500,000 → ₱1,000,000. Amendment chain
(CDC): AML Act RA 9160 → 9194 → 10167 → 10365 → 11521 (2021). **Tier 1→3→4**,
pays high, volatility high, sourceable mixed → exactly the profile to expand
first. The value function correctly ranks **Cell B above Cell A**
(asserted in `cell_priority` self-test).

## 9. Honest costs & risks

Combinatorial cost (prioritization is the whole game); **maintenance > acquisition**
(CDC/re-harvest/revocation is the recurring line item); **Tier-4 residual** never
closes via browser agents; **legal/ToS** — respect robots.txt/ToS, never breach
login-walled platforms, prefer official feeds; OCR/extraction error (verify +
tag confidence); **don't model-launder cell selection** (if an LLM is used in
selection at all, constrain it to *summarizing external signals*, never proposing
topics).

## 10. Next actions

**Coding agent:** (1) cell schema + value function as the acquisition queue, wire
query-miss logs from day one [`scripts/acquisition/cell_priority.py` — DONE for
§1–§2]; (2) Source-Discoverer → per-cell source registry, ship two reference
harvesters: Tier-1 (OFAC SLS delta) + Tier-2/3 (DOLE); (3) CDC-Monitor with BSP
1230 / CSDDD-Omnibus as revocation test fixtures; (4) coverage instrument,
surface per-cell coverage in-product; (5) Tier-4 Human-Router stubs minting
verified-publisher signing tasks.

**CEO agent:** (1) pick first 5–10 cells by `cell_priority` (start PH/ID ×
financial-crime/sanctions/customs); (2) use volatile-fact demos (BSP 1230,
CSDDD-Omnibus) as sales proof; (3) recruit verified publishers per top cell;
(4) position the coverage map itself as a buyer-facing trust artifact.

## Sources (2026; verify — volatile by design)

PH labor: dole.gov.ph, bwc/ils.dole.gov.ph, foi.gov.ph, library.laborlaw.ph,
Fragomen (Aug 2025). PH financial-crime: BSP (bsp.gov.ph; Circular 1230 via
Philippine Daily Inquirer 4 Mar 2026; RegulationsList.aspx), AMLC, BSP Facebook.
AML Act chain RA 9160/9194/10167/10365/11521 + FATF context. **[verify from model
knowledge]:** Federal Register API, EUR-Lex/Cellar (CELEX/ELI), eCFR API,
robots.txt/ToS specifics per site.
