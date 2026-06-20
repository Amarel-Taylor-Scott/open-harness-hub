# Oracle-corpus & tooling map — the build/seed checklist for the commons

The concrete reference for the **verified-corpus commons** wedge ([[beat-contextual-positioning.md]]):
(a) the integration/ingestion tooling to *assemble* (not build), (b) the authoritative/oracle sources
worth wrapping, (c) what "verified" actually requires, and (d) the ranked seed checklist. Sources: the
owner's cited research (Fivetran/Airbyte docs, EUR-Lex/SEC/EU Open Data Directive, ILO/FATF/CSDDD, C2PA,
RAG-sentiment studies, Snowflake Marketplace). Feeds `data/source-registry.jsonl` (51 sources today) +
the foundry. Figures directional; re-confirm licenses/cadence before ingesting.

## A. Integration / ingestion tooling — ASSEMBLE, don't build (it's commoditized)
| Tool | Role | Fit | Agent/MCP? |
|---|---|---|---|
| **Fivetran** | managed ELT, 600+ connectors, auto schema/maintenance | enterprise SaaS/DB sources | — |
| **Airbyte** | OSS, large connector lib + CDK for custom/proprietary, native vector-DB | proprietary/regulatory sources | **Agent Engine + PyAirbyte MCP** (Claude Desktop/Cursor/Cline) ← *moving into our lane — watch* |
| **Unstructured.io** | PDF/HTML/Word → RAG-ready chunks | the doc-heavy oracle PDFs | — (wrap as a governed `parse` adapter) |
| **LlamaHub / LlamaIndex · Haystack** | framework-level ingestion/loaders | breadth of loaders | in-process |
| **Composio · Merge · MuleSoft** | agent-action / tool integration | the action side | yes |

**The wedge restated:** "poorly configured RAG hallucinates in up to ~40% of responses *even when the
underlying data is correct*" — plumbing alone doesn't make context trustworthy. We assemble the plumbing
and sell the **trust** layer on top.

## B. Oracle / authoritative sources — the corpora to seed
| Body / source | Domain | Format / API | License | Cadence | In SNOW/DBX mktplace? |
|---|---|---|---|---|---|
| **EUR-Lex** | all EU law (1951+) | JSON API + metadata | open (EU) | continuous | No (regulatory) |
| **EU Open Data Directive** high-value datasets | EU public data | APIs + bulk, machine-readable | free | varies | Partial |
| **SEC EDGAR** | US filings | programmatic API | public | continuous | Partial (financial) |
| US **Federal Register / regulations.gov / GovInfo / data.gov** | US regulation | APIs | public | continuous | Partial |
| **ILO** C029 / P029 / C105 + indicators + Measurement Guidelines | forced labor / migrant worker | treaty DB + docs | open | periodic | **No — our lane** |
| **US DOL / ILAB** remediation framework + lists | forced labor | docs | open | periodic | **No — our lane** |
| **FATF** 40 Recommendations | AML/CFT | docs/PDF | open | periodic | **No — our lane** |
| **EU FLR** (enforce **2027-12-14**) · **CSDDD** · **LkSG** · **EUDR** · **RED** · OECD DD · UNGP | supply-chain / ESG | EUR-Lex + agencies | open | fragmented | **No — our lane** |

**The opportunity is the FRAGMENTATION, not scarcity:** agri-food firms juggle LkSG + CSDDD + EUDR + RED
+ FLR across different authorities → conflicting requirements + double submissions. **Unifying,
reconciling, and keeping these current is the product.** 27.6M people in forced labor; only 60/183
countries ratified all three ILO conventions — acute negative space.

## C. What "verified" actually requires (provenance ≠ truth — our moat is the second job)
A genuinely verified corpus = **three jobs, and nobody sells all three together:**
1. **Provenance (signed origin)** — **C2PA** Content Credentials: a cryptographically signed manifest
   (claim + assertions + X.509 sig) + an **attestation registry** so any agent verifies a corpus *by hash*
   and sees *who certified it*. Becoming mandatory: **EU AI Act Art. 50, enforce 2026-08-02** (machine-readable
   AI-content disclosure). This is the "oracle signs the corpus" mechanism.
2. **Correctness (checked vs authoritative truth)** — provenance proves origin, NOT honesty (a bad actor
   can sign misleading content). This gap = our **adversarial verification vs authoritative sources + HITL.**
3. **Freshness (kept current)** — a **regulatory-diff feed** watching the sources for change.

## D. The ranked seed/build checklist (the commons)
1. **Oracle-signed corpora** — standards bodies / regulators / NGOs publish C2PA-signed into an attestation
   registry; pair every entry with the **AIBOM / EU-AI-Act** artifact buyers now legally need.
2. **Regulatory-diff freshness feed** — continuously watch EUR-Lex / FATF / ILO / FLR; **adversarially flag
   stale internal context.** Productize the wire-transfer-limit failure as the demo.
3. **Corpus-integrity / anti-poisoning** — detect when an internal doc contradicts the authoritative source
   (the 8/12 fake-policy attack, BadRAG/TrojanRAG) — security-meets-truth, no RAG vendor offers it.
4. **Under-served oracle corpora** — forced-labor/migrant-worker (ILO/DOL), food/water safety, customs —
   the social-impact lane the commercial marketplaces ignore; NGOs/agencies as signing publishers.
5. **Cross-source reconciliation + HITL** — when authorities conflict (agri-food double-submission),
   reconcile + escalate to a human — turning fragmentation into the value.

## D2. Ranked wedge shortlist — pick the beachhead
**Selection test (apply to any candidate domain):** authoritative truth (an oracle body) · changes
faster than anyone re-indexes · expensive to be wrong · fragmented/esoteric · an auditor on the other
side · absent from the data marketplaces — **plus** ease of landing the first oracle publisher.
**Meta-pattern:** *the best wedges are rules/lists that change faster than anyone re-indexes them, where
being stale is a **legal event**.* Sanctions is that pattern at its most extreme.

| Rank | Wedge (oracle bodies) | Cadence | Stale = | Auditor/buyer | Absent from mktpl | Ease to START |
|---|---|---|---|---|---|---|
| **1 ★ beachhead** | **Sanctions & export controls** (OFAC SDN, BIS EAR, EU consolidated, UN) | **several×/week** | **federal/criminal violation** | trade-compliance/legal (budget+fear) | yes | **highest — lists already PUBLIC + machine-readable; "publisher" = the gov feed, no relationship to land first** |
| 2 | Tax & transfer pricing (IRS, OECD BEPS, national + treaties) | constant | penalties | corporate tax (pays already) | yes | high (public, fragmented) |
| 3 | Pharma/GxP labeling & PV (FDA, EMA, ICH; DailyMed, Orange Book) | frequent | recall / patient-safety | QA/RA auditor | yes | med (some structured feeds) |
| 4 | Cyber/GRC controls mapping (NIST 800-53/CSF, ISO 27001, PCI-DSS, CMMC) | periodic | audit failure | CISO/GRC (funded) | yes | med (cross-walk = reconciliation value) |
| 5 | Privacy-law patchwork (GDPR, CCPA, US state sprawl) | fast | fines | DPO/legal (everyone needs it — horizontal) | partial | med |
| 6 | Government contracting (FAR/DFARS clauses) | frequent | False Claims Act | contracting/legal | yes | med (niche) |
| ✦ social-impact twin | **Immigration / work-authorization** (USCIS, DOL prevailing-wage/visa) | frequent | I-9/visa violation | employer compliance (budget) | yes | high — the **enterprise-paying twin of migrant-worker** protection: the commons + the cause fund each other |

**Beachhead = Sanctions & export controls.** It's the selection test at its extreme *and* the easiest
start: the authoritative lists (OFAC SDN/Consolidated, BIS Entity List, EU/UN) are **already published
machine-readable**, so the "first oracle publisher" is the government's existing feed — no signing
relationship to land before we add value (continuous freshness-diff + adversarial integrity + C2PA
provenance + ingest into Contextual/Snowflake/raw-pgvector/Claude Code). The demo writes itself: a
**stale sanctions list cited as current is a federal violation**, not an embarrassment — the
wire-transfer-limit failure with legal teeth. The social-impact twin (immigration/work-auth) connects
the mission (labor rights) to a budgeted compliance buyer.

## E. Distribution & the real frontier
The channel for "governed corpora served to agents" is the **data-cloud marketplaces** (Snowflake lists AP,
USA Today, CB Insights as AI-ready providers; Databricks/Google equivalents). They are the channel **and**
the real category competitor — so compete *within* the frontier on what they don't do: **oracle-verified,
adversarially-checked, esoteric/social-impact, capability-gap-closing, agent-neutral.** The buyer (per
Atlan's own tell): "invest in the knowledge base first when RAG returns confident-but-incorrect answers,
data has no ownership/certification, freshness is unknown, or you're regulated with auditability needs."

## Demand evidence (carry-through)
62% of enterprise RAG hit hallucination ≥ weekly · 58% update vector indexes monthly-or-less · a planted
fake policy was cited as authoritative in 8/12 cases · embedding models underperform up to **35%** on
financial-regulatory text vs general web — *why a curated verified domain corpus beats generic retrieval.*

---
*warrant: corroboration — the owner's cited multi-source research (Fivetran/Airbyte docs, EUR-Lex/SEC/EU
Open Data Directive, ILO/FATF/CSDDD/EUDR, C2PA + EU-AI-Act Art.50, Snowflake Marketplace, RAG-sentiment
studies). Re-confirm each source's license + cadence before ingesting into `data/source-registry.jsonl`.*
