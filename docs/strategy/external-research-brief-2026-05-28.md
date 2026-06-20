<!--
  Transcribed from the owner's external research brief (2026-05-28).
  HALF-LIFE WARNING: regulatory facts here are VOLATILE BY DESIGN — that
  volatility is the thesis. Treat every dated fact as a snapshot, version it in
  metadata, re-verify on a cadence. "[verify]" = from model knowledge, not a
  confirmed 2026 source. Addenda: corpus-acquisition-grid-spec.md,
  gap-detection-screen-spec.md.
-->
# Open Harness Hub — External Research Brief (2026-05-28)

Three strategic sharpenings: (1) split the lift gate by **durability**
(transient vs structural); (2) lead with **governance as the product**, not the
lift bar; (3) treat **human / verified-publisher supply** as the wedge moat.

## 1. Two-axis gate — durability of lift is a first-class field

Today's gate asks only `lift_delta > 0`. Add **why** it lifts and **whether it
survives the next model**. New per-component schema fields:

- `lift_delta` (float) — `pipeline_score − bare_model_score` on a named eval.
- `lift_reason` (enum) — see `scripts/eval/reason_codes.py` (single source).
- `durability_class` (enum) — `transient | structural | mixed`.
- `decay_signal` (enum) — `none | watch | decaying` (set by re-benchmarking vs newer base models).
- `last_lift_eval` (date + base-model string).

`lift_reason` codes: `long_tail_fact`→transient, `esoteric_rule`→transient-leaning,
`volatile_fact`→structural-by-recency, `no_addressable_source`→structural,
`embodiment_required`→structural, `closed_channel_access`→structural,
`accountability_or_license`→structural, `deterministic_guarantee`→structural.

**Operational:** re-run lift each major base-model release; flip `decay_signal` when
`lift_delta` collapses. Report catalog health as **% structural vs % transient
lift**, not total count. Keep transient-component benchmark traces governed/private
— benchmarking them produces the demonstration data that closes them (the flywheel).

## 2. Wedge selection — durable-lift × pays × sourceable

Lead with **sanctions screening** (cleanest sourceable + mandated buyer + durable
via volatility/accountability). Second motion: **EU AI Act conformity
documentation** (governance-led). Demote CSDDD to a *provenance/versioning
showcase*, not flagship.

⚠ **CSDDD staleness (decision-critical):** Omnibus I rewrote CSDDD — Directive
**(EU) 2026/470**, OJ **26 Feb 2026**, in force **18 Mar 2026**: scope narrowed to
**>5,000 employees & >€1.5B turnover** (was 1,000 / €450M), transposition **26 Jul
2028**, application **26 Jul 2029**; mandatory transition plans removed; liability
reduced. **Any pre-Omnibus CSDDD component is now wrong** — the single best live demo
of why dated provenance + revocation/CDC is the product. Use it as the test fixture,
not the truth source.

**EU AI Act clock:** prohibited practices in force 2 Feb 2025; GPAI 2 Aug 2025;
high-risk **2 Aug 2026** — but a "Digital Omnibus" (~May 2026, not yet adopted)
proposes pushing high-risk to 2 Dec 2027 (Annex III) / 2 Aug 2028 (Annex II), so
treat high-risk dates as fluid. Penalties: €35M/7% (prohibited), €15M/3% (high-risk),
€7.5M/1.5% (bad info). Financial-services AI is explicitly high-risk (Annex III).

## 3. Addressable source surfaces (prioritize delta feeds → CDC)

OFAC SLS (REST; XML/CSV; **yearly delta files**; bulk distribution, you build the
match — that's the lift); EU Consolidated / UN / UK OFSI sanctions; EUR-Lex/Cellar
(CELEX/ELI as stable version identifiers); US eCFR; Federal Register API (daily);
regulations.gov; GLEIF (LEI, daily); WCO HS / UN Comtrade / WITS. **CDC pattern:**
store signed snapshot + normalized record (`source_url + retrieved_at +
source_version`) + diff vs prior + a rule that **revokes/flags** derived facts when
upstream changes. **Tier-4 boundary:** the freshest truth often lives where no
connector reaches (regulator social post, WhatsApp circular, scanned PDF) — the
connector there is a **human** (§6); don't imply automated tier-4 coverage.

## 4. Capability-lift benchmarks (anchor the gate externally)

**PRBench** (Scale) — Finance+Law, 182 experts, rubric incl. "Process Transparency
& Auditability"; top models <~0.40 on the hard subset (feature this).
**LegalBench**, **LawBench** ("a long way from usable"), **LegalAgentBench** (37
tools/300 tasks — agentic), **NitiBench** (Thai legal QA — directly validates RAG
chunking+citation lift), **CFinBench** (~60%). Register each as a benchmark object;
record `lift_delta` vs the relevant subset; re-run on each new base model → `decay_signal`.

## 5. Governance as the product (moat layer 2)

C2PA / Content Credentials (v2.3–2.4 Jan 2026; royalty-free, MIT tooling) — reuse
its manifest = assertions + X.509 signature + content-binding hash for *facts &
components* ("this fact, from this source, signed by this publisher, on this date").
Caveats: CA trust-list cost (~$289/yr/cert); metadata strippable → also store
provenance server-side. W3C **VC/DID** for verified-publisher identity. **SPDX** for
license. **ISO/IEC 42001** (certifiable AIMS; ~60–70% of EU AI Act mgmt obligations)
+ **NIST AI RMF**. Position OHH output as audit-ready evidence for **EU AI Act Art.
11** (technical docs), Art. 9 (risk mgmt), data governance, Art. 14 (human
oversight), Art. 72/73 (post-market + 15-day incident reporting). Adjacent
incumbents (Vanta, Holistic AI…) = partner surface AND threat; differentiate on
lift-admission + reusable cross-domain components + cross-cloud neutrality.

## 6. Human / verified-publisher supply (the tier-4 moat)

Make "verified publisher" first-class, not an upsell. Identity = VC/DID
(profession, license, jurisdiction); signed fact = C2PA manifest binding {claim,
citation, effective_date, jurisdiction, publisher DID, signature}; revocation/CDC
flips a fact to `superseded` with a successor pointer (CSDDD-Omnibus pattern).
Surface license/source/freshness/signer **per component in-product** — an invisible
moat doesn't sell. Monetization: verified-publisher accounts + managed ingestion.
For *transient* components keep expert demos private (don't feed the flywheel).

## 7. Interop & positioning

MCP now Linux-Foundation-governed (Agentic AI Foundation, Dec 2025); **official MCP
Registry** supports **subregistries** → position OHH as a governed, lift-gated MCP
subregistry. Build the MCP server against **spec RC 2026-07-28** (stateless core,
Extensions, Tasks, MCP Apps, OAuth `iss` per RFC 9207), pin the version. **Security
opening:** only 8.5% of registered MCP servers use OAuth, 15.4% fully opaque,
42,000+ exposed instances — a provenance-signed, scanned, lift-gated subregistry
answers this. (And: token-gate our own `/api/build` — DONE.) Add **A2A** behind MCP.

## 8. Competitive clock (the window is narrowing)

AWS Bedrock **AgentCore GA** (13 Oct 2025; framework-agnostic, multi-model incl.
non-AWS — erodes "they're locked-in"); AWS Marketplace adds **A2A + MCP listings**
(Nov 2025); AWS **Agent Registry preview** (Apr 2026; governed catalog of
agents/tools/MCP). Our defensible surface narrows to four things their registry does
NOT: (1) capability-lift admission bar, (2) provenance/signed-facts/CDC for
regulated domains, (3) true cross-cloud neutrality, (4) automated assembly.
Integrate (emit AgentCore bundles; be a subregistry), don't compete on infra.

## 9. Next actions

**Coding:** (1) add the §1 schema fields + re-benchmark/decay job; (2) OFAC SLS
connector + delta CDC, CSDDD pre/post-Omnibus as revocation fixture; (3) wire one
wedge benchmark (LegalBench/PRBench subset) into the gate; (4) C2PA manifests +
VC/DID + surface provenance in UI; (5) MCP server vs 2026-07-28 RC + subregistry;
token-gate `/api/build` [DONE]. **CEO:** lead with governance; re-pick wedge to
sanctions (primary) + EU-AI-Act docs (second); land one paid design partner on a
public yardstick; make verified-publisher + managed ingestion the supply story;
hold the two-axis gate on every new family.

## Sources (2026; verify — volatile by design)

CSDDD/Omnibus: EC pages, Directive (EU) 2026/470, DLA Piper/Arthur Cox/Deloitte.
EU AI Act/Digital Omnibus: ECCouncil, GAICC, euaicompass. OFAC SLS:
ofac.treasury.gov/sanctions-list-service. Benchmarks: PRBench (labs.scale.com),
LegalBench (arXiv 2308.11462), LawBench (2309.16289), LegalAgentBench (2412.17259),
NitiBench (2502.10868), CFinBench (2407.02301). C2PA: c2pa.org. ISO 42001/NIST: per
trainingcamp/eccouncil. MCP: modelcontextprotocol.io, NimbleBrain "State of MCP
Security" (Mar 2026). AWS: aws.amazon.com whats-new (Oct/Nov 2025, Apr 2026).
**[verify from model knowledge]:** EUR-Lex/Cellar, eCFR, Federal Register,
regulations.gov, GLEIF, WCO/Comtrade/WITS endpoints; EU/UN/UK list formats.
