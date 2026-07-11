# Competition & Moat — The Context Layer, 2026

> **Why this doc exists.** YC asks two questions every deck has to answer cleanly: *who else does this,
> and what stops them from crushing you?* This is the single consolidated answer. It does not re-derive
> positioning per pitch and it does not contradict the master doc
> (`docs/strategy/yc-master-current-state-business-plan-and-pitch.md`, §4.5 market / §5 slide 12 / §7
> risks) — it expands slide 12 into a defensible competition map and moat argument. Lineage:
> `archive/legacy/_repos/_shared/strategy/competitive-landscape-2026.md` (the prior "four camps" framing).

**Honesty header (hard rails).** We are **pre-revenue, design-partner stage** — no traction is claimed
here. Every market/valuation/ARR figure below is a **comparable-anchored ESTIMATE** taken off the public
tape or as vendor-reported; none is audited by us. Counts are **computed and dated**, never hardcoded
facts. This is a positioning document — `serves_truth=false`; it is not a Baltor-verified served fact and
must not be cited as one. No insurance examples; no `_reference/` material.

**Where this product sits.** Parent brand **AI Done Right**. **Teleon** is the runtime engine →
**Baltor** is the customer-facing governed-context product, *powered by Teleon* → **OpenHubForAI registries** (free
developer funnel under `OpenHubForAI.io`). The competitor below is the customer-facing layer, so the
column we defend is **Baltor's**. One-liner (LOCKED): *"Models don't fail. Their context does."* —
*"Verified, current, and provable context for the agents you already run."* Pillars: **Verified · Current
· Efficient · Provable.**

---

## 1 · The frame — "context layer" is now a priced category

Through 2025 the "context layer" was a thesis. In 2026 it is an **analyst-tracked, consumption-priced
category** — the public market is actively repricing the infrastructure under AI workloads on
*consumption*, not seats. The comparable anchors from the master doc (§4.5), labeled as **estimates** off
the public tape, not figures we audited:

| Public-tape anchor (ESTIMATE) | Reported signal | What it tells a YC partner |
|---|---|---|
| **SNOW** (Snowflake) | product rev ~$1.33B/qtr, ~+34% | the data substrate is repricing on consumption + agentic workloads |
| **MDB** (MongoDB) | ~$687.6M/qtr, ~+25% | operational data layer growing on the same axis |
| **DDOG** (Datadog) | ~+32% | observability/telemetry repriced by usage |
| **NET** (Cloudflare) | ~+34%, attributed to agentic | the edge layer is monetizing agent traffic |

The read: money is flowing to whoever sits **between the model and the data it needs**, billed by
consumption. But the named winners sell **infrastructure** (storage, search, compute) and the open-source
field gives **plumbing** (retrieval, memory). **Both lack the enterprise-governance seam** — glossary,
lineage, entity resolution, freshness, proof. That seam is the unoccupied middle, and it is consumption-
shaped (source monitored → facts verified → context package served), which matches how the tape is
already paying. Baltor's economic position is the **open, governed assembler at that seam**: we do not
out-RAG the infra incumbents — we **wrap** them (Qdrant / Mem0 / LLMLingua / Langfuse) as governed,
measured-lift components under one provenance + eval contract.

---

## 2 · Competition map (slide 12, expanded)

Each category below owns one real mechanism. None owns the governance seam: *verify + prove a fact before
an agent uses it, manage its state over its lifecycle, and hand the agent a portable receipt.*

| Category | Example players | What they do | What they DON'T do (the gap) |
|---|---|---|---|
| **Enterprise search / work assistant** | Glean (≈$7.2B val. / ≈$200M ARR, vendor-reported ESTIMATE), Microsoft 365 Copilot, Snowflake Cortex | Index the org's own corpus into a closed console + chat | No verify/prove **before** use, no portable receipt, no open/model-portable object, no separate-evaluator lift on *your* data — a destination app, not an assembler |
| **RAG platforms** | **Contextual AI** (*absorbed into Google DeepMind, May 2026*), Vectara, managed-RAG SaaS | Hosted retrieval + generation pipeline | No lifecycle fact-state with history, no proof-before-use, no portable receipts. The DeepMind absorption is the tell: **standalone managed RAG is a feature, not a durable company** |
| **Vector databases** | Qdrant, Pinecone, pgvector | Similarity search over embeddings | Retrieve *nearest*, not *true/current/authoritative*; no provenance, conflict reconciliation, or receipt — substrate we **wrap**, not a competitor on governance |
| **Knowledge graphs** | Graphiti, FalkorDB, Zep | Structured + (bi-)temporal relationships and fact state | Temporal ≠ verified: no authority reconciliation before serving, no measured-lift admission gate, no portable receipt |
| **GRC / compliance tooling** | Vanta, Drata, OneTrust, RSA Archer | Attest **org-level controls**, keep audit history of posture | Govern the *organization*, not the *agent's context object*; they don't verify or serve fact-level context at consumption time |
| **Source-intelligence vendors** | sanctions/PEP & screening-data feeds, OSINT/news-intelligence, regulatory feeds | Verified, current data inside **one** closed domain | Single-domain + closed; no agent-neutral packaging, no portable receipt, not composable across domains or models |
| **OSS memory / RAG frameworks** | Mem0, Letta, LangChain (+ LlamaIndex, Zep) | Agent memory lifecycle + retrieval plumbing + app scaffolding | Builder research is blunt: *"generally lack enterprise governance — no glossary, lineage, or entity resolution"*; no admission bar, no measured delta |

Two structural facts fall out of the table. First, the **commodity mechanisms are each going to zero** —
packing, compression, vector search, memory recall are all becoming one-line libraries or provider-native
features — which is *why* we wrap them rather than build a business on any one. Second, the **buyer needs
all of them, governed, with a number attached, and served to any agent** — and that composite is what no
column ships.

---

## 3 · The 2×2 — the empty quadrant

Two axes separate "moves data near a model" from "makes a fact safe for an agent to act on." Both are
required for agent-grade context; the field clusters where neither or only one holds.

- **X — lifecycle-managed fact state:** is a fact a *static snapshot you re-pull by hand*, or a
  **versioned, freshness-tracked, conflict-reconciled, revocable object with history**?
- **Y — verifies & proves before use:** does the layer **retrieve-and-hope**, or **verify the fact
  against authority and hand the agent a portable receipt** before it is consumed?

```
        Y: verifies & PROVES facts before an agent uses them
        ▲
 high   │  Source-intelligence feeds          ┌──────────────────────┐
        │  (verified + current, but           │       BALTOR         │
        │   closed, single-domain,            │  verify · prove ·    │
        │   no agent-neutral object)          │  lifecycle · receipt │
        │                                     │  open · agent-neutral│
        │                                     └──────────────────────┘
 ───────┼────────────────────────────────────────────────────────────▶
        │  Vector DBs · RAG platforms         Knowledge graphs ·       X: lifecycle-
 low    │  raw retrieval                      memory libs · enterprise   managed fact
        │  "retrieve nearest, trust nothing"  search via connectors      state w/ history
        │                                     "fresh-ish state, but
        │                                      asserts usefulness;
        │                                      no proof-before-use"
        ▼
```

- **Bottom-left (neither):** vector DBs, RAG platforms/frameworks. They move bytes near the model and
  trust the model to sort truth out.
- **Bottom-right (lifecycle, no proof):** knowledge graphs, memory libraries, enterprise search. They
  track state — sometimes temporally — but **assert** usefulness; nothing is verified or proven before an
  agent acts on it.
- **Top-left (verify, no lifecycle object):** source-intelligence vendors verify and keep currency, but
  inside one closed domain with no agent-neutral, composable object or portable receipt. *(GRC tools also
  verify-with-history, but on org controls — a different plane than agent-consumed facts, so they sit off
  this 2×2 entirely.)*
- **Top-right (both + open + receipt):** **Baltor — the empty quadrant.** Verifies and proves facts,
  manages their state over a lifecycle, serves them **agent-neutral** with a **portable receipt**.

---

## 4 · Baltor's distinct column

What Baltor does that no column above does, stated as the slide-12 differentiator:

1. **Verify + package + PROVE facts *before* agents use them.** Reconcile conflicting sources by
   authority, hold out the losers and the unverified, serve only the reconciled winner, and attach
   **lineage + a receipt** to it. (Demo invariant: CFPB "10 business days" served by Reg-E authority, the
   30-day FAQ and the narrative allegation held out — `serves_truth` is enforced, not asserted. OFAC
   sanctions: deterministic flag on a held-out would-be violation, with an always-green synthetic
   conformance proof plus a dated live SDN catch.)
2. **Lifecycle-managed fact state with history.** A fact is a versioned object — freshness/CDC, conflict
   reconciliation, revocation on volatile facts, rehydratable prior versions — not a snapshot you re-pull
   by hand. The temporal-graph camp tracks *state*; we add **verification + an admission gate** on top of
   it.
3. **Portable receipts that travel across platforms.** The proof of *why this fact is safe to serve* is a
   **portable object**, not a row locked in one vendor's console. It rides with the context into whatever
   agent, RAG stack, or platform consumes it — which is exactly what a closed console cannot give and an
   acquirer cannot easily rebuild.
4. **Agent-neutral + open + composable.** Every input — a packer, a memory store, a retriever, a
   compressor — drops in as one **governed, measured, costed** component under a single provenance/eval
   contract, served to *any* agent. We are the assembler/refinery beneath the agent, not a destination
   app the buyer has to migrate into.

---

## 5 · The moat — defended against the two killer objections

The moat is **governed DATA + provenance + freshness + portable receipts + the Determinism Factory +
the measured-lift admission gate** — *not* model capability. A YC partner will fire two objections at it.

**(a) "Won't the next frontier model just close this?"**
No — the moat is **orthogonal to capability**. A bigger model is better at *reasoning over* context; it
supplies **none** of the governed-data primitives — provenance/AIBOM, citations, signed publishers,
CDC/freshness/revocation, entity resolution, lineage, a portable receipt. Those are properties of the
**data and its custody chain**, which improve with sources and time, not with parameter count. The
**measured-lift admission gate** is the structural turn: a component is admitted only on
`pipeline_score − bare_model_score > 0` **and** only if the lift is durable (won't close when the next
model ships). When a model *does* absorb a transient component, the gate **prunes it and re-parks the
registry on the moving frontier** — so the product gets *more* valuable as models improve, by
construction. And the **Determinism Factory** turns each expensive agent resolution into a cheap
**deterministic rule, losslessly** — capability flows *into* the moat as durable infrastructure, it does
not erode it.

**(b) "Won't Snowflake / Databricks add governance and crush you?"**
They own **data gravity**; we do not compete on storage — we **wrap their substrate**. Their governance
is **platform-bound** (govern *their* data, in *their* console, for *their* tenants). Baltor is the
**agent-neutral, OPEN governed assembler at the seam**: the receipt and the governed object are
**portable across platforms** — Snowflake *and* Databricks *and* a self-hosted agent *and* a customer's
own RAG stack. An incumbent adding governance makes its own walled garden nicer; it does not produce a
**cross-platform, model-portable, agent-neutral** proof object, because that openness is structurally
against its lock-in incentive. We are **complementary** (we produce the lineage their catalog records;
we are the lift + governance + composability layer on their substrate) right up until we are an
acquisition target — which is the friendly end of this objection.

---

## 6 · Open-core is a moat, not a giveaway

The free **OpenHubForAI registries** funnel (under `OpenHubForAI.io`) is the **demand-capture and trust-building top
of the moat**, not a leak of it:

- **The open layer is the spec, SDK, and engine; the paid layer is the *live governed data*.** A
  developer can pull a **freezable, verified snapshot** into an open Hub harness for free. What they
  **cannot** self-serve is the thing that decays the instant it is frozen — **live, kept-fresh serving
  against a dynamic corpus**, governed corpora subscriptions, and build-on-demand for a domain we don't
  yet carry. Freshness, custody, and the receipt are the recurring product; the snapshot is the sample.
- **The funnel feeds the paid layer.** OpenHubForAI developers wire governed components into bounded
  pipelines, hit the moment they need *live + provable + fresh*, and convert to Baltor — **one governed
  object, two doors** (a free freezable snapshot, a paid live layer), one COGS, two GTMs.
- **Open is a defense against the seam itself commoditizing.** If the assembler interface is open and
  model-portable, MCP and the next protocol become our **default serving surface**, not a bypass — what
  travels over the wire is *our* governed, measured, receipt-bearing object. Owning the open standard at
  the governance seam is harder to dislodge than owning a closed console, because the ecosystem builds
  *on* the standard rather than around it.

The throughline matches §1: every commoditizing mechanism is an **input we wrap**, and every one makes
our governed tier *cheaper or fresher*, never redundant. We sell the **governance + measurement +
portability** around the commodity — the one composite no column in §2 ships.

---

*Warrant: written on clear owner intent (this request) and grounded strictly in the master doc's §4.5
market / §5 slide 12 / §7 risk framing and the locked brand; all market/valuation/ARR figures are
labeled comparable-anchored ESTIMATES (recompute the proof gate, never hardcode it:
`PYTHONPATH=. python3 scripts/run_proofs.py` — 713 green is a dated 2026-06-25 snapshot, not a fixed
fact); no traction claimed (pre-revenue); `serves_truth=false`. No brand/strategy/pricing decision was
made unilaterally — positioning mirrors the canonical docs.*

---

## Appendix A — Contextual AI: company profile + the upstream play

> **Merged 2026-07-03** from the former `strategy/beat-contextual-positioning.md` (archived at
> `archive/legacy/_shared/strategy/beat-contextual-positioning.md`). Contextual AI was **absorbed into
> Google DeepMind (May 2026)** — read the profile below as the standalone-company snapshot that made the
> upstream/acquisition logic; the absorption is the proof of the "standalone managed RAG is a feature, not
> a durable company" read in §2. Figures are directional; re-confirm before external use. Companion engine
> deep-dive: `competitor-contextual-ai.md` (Agent-Composer analysis; a strategy deep-dive, not in this repo tree).

**The crisp position.** *"Verified, current, provable context — for the agent you already run."* Category =
**context assurance + governance, upstream of and adjacent to RAG** — not "better RAG agents." That sentence
puts us in a room Contextual isn't standing in, instead of a benchmark fight we lose.

**Company profile (as a standalone, pre-absorption).** Out of stealth **June 2023** (seed ~Apr 2023), Palo
Alto → SF / Mountain View. Founders **Douwe Kiela** (CEO — pioneered RAG at Meta FAIR, 2020; ex-Head of
Research, Hugging Face; Stanford adjunct) + **Amanpreet Singh** (CTO). ~**$100M** over two rounds (Seed $20M
led by Bain Capital Ventures; Series A $80M led by Greycroft; PitchBook est. ~$609M post) — strategic
investors **Bezos Expeditions, NVentures (Nvidia), HSBC Ventures, Snowflake Ventures**. ~**51–100** staff.
Products: the **Contextual AI Platform** (RAG 2.0 — jointly-optimized retriever+generator, sentence-level
attributions), the **Grounded Language Model (GLM)**, an instruction-following **reranker**, **LMUnit**
(eval, open-sourced Jul 2025), the no-code **Agent Composer** (Jan 2026), managed per-tenant **Datastores**
+ a few curated **Global Datastores**. Customers: **Qualcomm, HSBC**; document-heavy regulated Fortune 500.

**Why head-on is the wrong goal.** We do not out-RAG the person who invented RAG, with Nvidia + Bezos money
and a benchmark-leading grounding model. "Beat Contextual" must mean **own a job they structurally don't do,
for a buyer they don't serve, and sit upstream** — verify/govern the corpus, then feed it into whatever
retrieval stack the customer runs (turning the threat into a channel, and us into an acquisition target).

**The corpus question, settled.** Contextual *does* manage corpora (per-tenant vector stores + a few curated
global datastores) — so "we host corpora" is table stakes, **not** a wedge. The moat is the *kind* of corpus
object: (a) **portable / agent-neutral** (governed raw→compressed→hyper-efficient tiers served into the
customer's own agent over MCP, not locked to their GLM); (b) **verification, not just sync** (adversarial
verification against external authority + HITL — "is this corpus still true?", not "is it in step with the
source?"); (c) a **portable, regulator-facing compliance artifact** (AIBOM/CycloneDX, EU-AI-Act docs,
measured-fidelity record), not in-product citations; (d) a **commons** (oracle/government-publisher program +
cross-tenant sharing) they structurally lack (their datastores are private, per-tenant, agent-bound).

**Three durable wedges (each cuts against their incentives).** (1) **Audit the corpus, not just ground the
answer** — *context assurance* as a category: "Contextual makes the answer faithful to your documents. We
make sure your documents aren't wrong." (2) **Agent- and model-neutral serving** into the agent the developer
already runs (Claude Code / Codex / Cursor over MCP), against their GLM lock-in. (3) **Make the artifact a
compliance deliverable** — portable AIBOM / EU-AI-Act / measured-fidelity records for AML, GxP, customs,
food/water safety.

**Sit UPSTREAM — the real play (be the layer they buy FROM).** Three viable, non-head-on stances: (1)
**supplier INTO their customers** — push signed, verified regulatory corpora into the customer's Contextual
datastore via the same ingest API (the AP / CB-Insights-into-Snowflake motion); they keep the answer faithful,
we guarantee the corpus is right. (2) **customer OF Contextual** — run our verified corpora through their
RAG/GLM rather than rebuild RAG 2.0. (3) **neutral arms-dealer above ALL RAG** — the same verified corpus
feeds Contextual, Snowflake, Databricks, raw pgvector, and Claude Code; the **verified-ore supplier** profits
from everyone's growth. Moat (not the tech): oracle-publisher *relationships*, the operational muscle of
adversarial verification + HITL, and depth in domains they'd never prioritize. Guard: never let one platform's
ingest API be the only channel (that's why stance 3 exists).

**Orchestration is TABLE STAKES.** Contextual's **Agent Composer (Jan 2026)** ships multi-step reasoning, a
tool library, guardrails, three build paths, side-effecting **Task Execution** (API write actions), and is
**model-agnostic** — so "we orchestrate / act, they only retrieve" is eroding and must NOT be the pitch. The
durable moat is **orthogonal to orchestration**: (1) open / portable / low-end (the OpenHubForAI funnel), and
(2) verified context. Naming call: **keep "OpenHubForAI," do not rename to "Open Agent Hub"** (that collapses
the harness-vs-agent line and drops us into the commoditizing agent category); use "agent" in taglines / SEO
for findability. Reversible (brand is config).

**The demand is real (RAG-failure sentiment; directional).** ~**62%** of enterprise RAG deployments hit
hallucination incidents at least weekly; ~**58%** update their vector indexes monthly or less (stale values
outliving the rule change); a planted fake "superseding" policy was retrieved + cited as authoritative in
**8 of 12** poisoning cases (BadRAG / TrojanRAG). "Inability to explain answers to auditors" is a named
production gap. These validate context-assurance + adversarial-verification + the compliance artifact.

**The real category competitor (not Contextual).** "Shared, governed corpora served to agents" is the
**hyperscaler data marketplaces** (Snowflake Marketplace lists AP, USA Today, CB Insights; Databricks / Google /
MSFT similar). Don't pitch a generic "corpus marketplace" — late. The open lane: esoteric / social-impact /
regulated domains the marketplaces ignore (CSDDD & EU Forced-Labour Regulation, food/water safety, customs);
oracle publishers + adversarial verification (C2PA / W3C-VC); capability-gap-closing corpus generation;
model-agnostic serving into open agents outside any cloud perimeter. Build targets the research surfaced:
governed connectors over Fivetran / Airbyte / Unstructured.io / LlamaHub / Composio; oracle sources EUR-Lex
JSON, SEC EDGAR, ILO conventions, FATF 40, EUDR/LkSG, EU high-value datasets. **What to STOP:** don't benchmark
retrieval/rerank against them, don't enter the multimodal-parsing arms race, don't build a GLM, don't call
ourselves "specialized RAG agents." Wrap their Component APIs (Parse / Rerank / GLM / LMUnit) as governed
measured-lift adapters; compete only on assurance + governance + the oracle/social-impact commons + agent-neutral serving.

---

## Appendix B — Positioning throughline + one-liners

> **Merged 2026-07-03** from the former `strategy/positioning-v2.md` (archived at
> `archive/legacy/_shared/strategy/positioning-v2.md`). Naming is locked to **AI Done Right** (parent) /
> **Baltor** / **OpenHubForAI** — brand identity/messaging live in `docs/strategy/brand-architecture.md`.

**The throughline (read this first).** Don't position on "harness beats RAG" — Contextual is closing that gap
(Agent Composer = orchestration, multi-tool, model-agnostic no-code builder that does API *write* actions).
Orchestration / actions / build-UX are becoming table stakes. The two things that stay *ours*: **(1) open /
portable / low-end** — OpenHubForAI for the devs Contextual treats as a funnel; **(2) verified context,
upstream** — the service that checks the *corpus* against authoritative truth, kept current, with provenance,
feeding *any* agent (including Contextual itself).

**The wedge line (memorize).** *"Most platforms keep your docs CURRENT. We CONTINUOUSLY verify they are
CORRECT — cross-checked against external authoritative sources, hunting for contradictions before your agent
cites them."* Their compliance = completeness + recency of the *customer's own* docs; they do not verify the
corpus is correct against external truth, keep external regulated corpora current as a product, offer
oracle-signed shared corpora, or reconcile conflicting authorities. **That one sentence is the whole business.**

**Confirmed at the source (their docs).** The shared "global datastores" are **demo-only** (read-only, "Demo"
badge, not for production); everything real is customer-provided + per-tenant isolated. So there is **no
production shared corpus, no cross-customer sharing, no marketplace, no oracle-publisher path** — the
verified-corpus-commons gap is documented, not inferred; their architecture's Enterprise-Knowledge layer must
be *fed*, which is the exact slot we supply (strengthens the upstream + acquisition logic).

**The two products (one governed object, two doors).** **OpenHubForAI** = the bounded, governed harness
(free/OSS funnel + low-end wedge; components admitted only on measured lift; works with the agent you already
run). **Baltor** = the moat (recurring verified-context SaaS: corpora cross-checked vs authoritative truth,
freshness/CDC, C2PA provenance + oracle publishers, HITL, compliance artifacts). The join: one governed
corpus/tool, minted + scored once (lift + fidelity), consumed two ways.

**Competitive stance vs Contextual — don't fight where they're strong** (RAG quality, orchestration, the
grounded model, the no-code builder, side-effecting actions incl. API writes, governance / RBAC / model-armor /
observability, model-agnostic choice — they have them). **Learn, don't rebuild** (adopt their eval rigor —
RAG 2.0 / FACTS / the LMUnit pattern — and wrap their Component APIs as governed adapters). **Win where they
structurally can't:** open/portable/low-end; verified context (they ground answers but never check the docs
are correct or current); and sitting **upstream**.

**The crisp one-liners.** Company: *"The open harness layer + verified context for trustworthy agents."*
OpenHubForAI: *"Power your agents with governed harnesses."* (free, open, portable, measured.) Baltor:
*"Verified, current, provable context — for the agent you already run."* (the moat.)

**Honesty guards.** We don't claim to out-RAG Contextual, to have novel orchestration, or measured-lift we
haven't run (our measured-lift evidence is still thin — `measured-lift-head-to-head.md` is the harness to fix
it). Open = freezable (download it); paid = anything that must stay live/verified/provenanced (the open-core
line, `open-core-model.md`). Beachhead: sanctions & export controls (OFAC/BIS/EU) — "rules that change faster
than anyone re-indexes, where stale is a legal event," and the easiest start (lists already public +
machine-readable; `docs/strategy/oracle-corpus-and-tooling-map.md`). Real acquirers: the data clouds
(Snowflake/Databricks), a hyperscaler, or a GRC incumbent — the most *defensible* (upstream/verified)
positioning is also the most *acquirable*.

*Merge warrant: lossless consolidation per this request — the two source docs are archived intact under
`archive/legacy/_shared/strategy/`; their unique material (Contextual company profile, the three wedges + three
upstream stances, RAG-failure stats, the wedge line, one-liners, honesty guards, demo-only-datastore
confirmation) is preserved here. Figures directional; `serves_truth=false`; re-confirm before external use.*
