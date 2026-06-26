# Competition & Moat — The Context Layer, 2026

> **Why this doc exists.** YC asks two questions every deck has to answer cleanly: *who else does this,
> and what stops them from crushing you?* This is the single consolidated answer. It does not re-derive
> positioning per pitch and it does not contradict the master doc
> (`docs/strategy/yc-master-current-state-business-plan-and-pitch.md`, §4.5 market / §5 slide 12 / §7
> risks) — it expands slide 12 into a defensible competition map and moat argument. Lineage:
> `archive/legacy/docs/strategy/competitive-landscape-2026.md` (the prior "four camps" framing).

**Honesty header (hard rails).** We are **pre-revenue, design-partner stage** — no traction is claimed
here. Every market/valuation/ARR figure below is a **comparable-anchored ESTIMATE** taken off the public
tape or as vendor-reported; none is audited by us. Counts are **computed and dated**, never hardcoded
facts. This is a positioning document — `serves_truth=false`; it is not a Baltor-verified served fact and
must not be cited as one. No insurance examples; no `_reference/` material.

**Where this product sits.** Parent brand **AI Done Right**. **Teleon** is the runtime engine →
**Baltor** is the customer-facing governed-context product, *powered by Teleon* → **Open\*Hubs** (free
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

The free **Open\*Hubs** funnel (under `OpenHubForAI.io`) is the **demand-capture and trust-building top
of the moat**, not a leak of it:

- **The open layer is the spec, SDK, and engine; the paid layer is the *live governed data*.** A
  developer can pull a **freezable, verified snapshot** into an open Hub harness for free. What they
  **cannot** self-serve is the thing that decays the instant it is frozen — **live, kept-fresh serving
  against a dynamic corpus**, governed corpora subscriptions, and build-on-demand for a domain we don't
  yet carry. Freshness, custody, and the receipt are the recurring product; the snapshot is the sample.
- **The funnel feeds the paid layer.** Open\*Hub developers wire governed components into bounded
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
