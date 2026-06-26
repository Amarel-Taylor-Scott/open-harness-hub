# Competitive Landscape 2026 — Four Camps, the Durable Edge, the Two Doors

> **Why this doc exists.** In 2026 the "context layer" stopped being our private thesis and
> became an analyst-tracked category with funded incumbents. This is the one place that writes
> down the landscape *as it actually is* — four camps, named players, the numbers — so positioning
> stops being re-derived in every pitch. Companions, not duplicates: [[competitive-swot.md]] (the
> iPaaS / cloud-platform / dev-hub matrix), [[competitive-positioning-deep-dive.md]] (compete-and-
> integrate, per-player), [[context-layer-pmf.md]] (the public-market consumption read). This doc
> covers the **OSS + enrichment + analyst-vendor** field those three don't, and states the
> commoditization threats bluntly.

**The one-line read.** The context layer is now a category with money in it — Glean is the
flagship — but it has fractured into four camps that each own one *mechanism* (packing,
memory, retrieval, the enterprise console) and **none owns the seam we sit on**: separate-evaluator
**measured lift/fidelity on the buyer's own data**, a **governance chain-of-custody**, **seven-
primitive composability**, and **two doors onto one governed object**. Lead with that seam; treat
compression, memory, and retrieval as **wrapped commodity inputs**, not as the product.

---

## The four camps (where the field actually is, mid-2026)

| Camp | What it owns | Named players (2026) | What it does *not* have |
|---|---|---|---|
| **1. Packing CLIs** | one-shot codebase/repo → token-dense file | Repomix (Tree-sitter, MCP, Claude Code plugin), gitingest, code2prompt, yek, Repo Prompt | hosted/governed tiers, freshness, **measured** fidelity, cross-org corpus |
| **2. Memory libraries** | the agent's recall/reflect lifecycle | Mem0, Zep, Letta/MemGPT, Hindsight | provenance, lineage, entity resolution, an admission bar, a measured delta |
| **3. RAG frameworks** | retrieval plumbing + app scaffolding | LlamaIndex, Onyx (self-host/air-gap), LangChain/LangSmith, Haystack | a curated **lift-gated** registry, governance glossary, costed composition |
| **4. Enterprise context-layer vendors** | the indexed-everything work console | **Glean** (~$7.2B val., ~$200M ARR), Snowflake **Cortex**, **Atlan** (governance/catalog) | open protocol, model-portable components, separate-evaluator lift on *your* data, two doors |

A fifth surface — **MCP** — is not a camp; it is the **convergence point** every camp is racing
toward (Repomix ships an MCP server; Cortex/Glean expose MCP; we serve through it). MCP is both
opportunity (one universal door) and threat (see *Disintermediation*, below).

The structural fact: **each camp owns one mechanism; the buyer needs all of them, governed, with a
number attached.** That composite — governed + measured + composable, served two ways — is the
unoccupied seam, and it is the same seam [[context-layer-pmf.md]] reads off the public tape.

---

## Camp-by-camp: what they are, how we win, what we wrap

### Camp 1 — Packing CLIs (Repomix and neighbors)
- **What they are.** Local, single-shot CLIs that pack a repo into a token-dense blob. Repomix is
  the clearest proof of the **raw → compressed** tier: Tree-sitter strips function bodies while
  preserving signatures for **~70% token reduction**, with per-file token counts, Secretlint
  scanning, an MCP server (`pack_codebase` / `pack_remote_repository`), and an **official Claude
  Code plugin**. `llms.txt` / `llms-full.txt` is the emerging doc-tier standard for the same job.
- **How we win.** They run **once, locally, ungoverned**. We host the tiers as **governed,
  downloadable, freshness-tracked** artifacts with a **published fidelity delta per tier**, and
  serve them to open agents. The CLI's output is a file you regenerate by hand and can't trust to
  stay current; ours carries provenance and a measured "did this tier preserve enough?" score.
- **What we wrap.** Their *technique* is a commodity input — structural packing is `compress.structural`
  in the shared backend (see [[context-enrichment-service.md]]). We do not rebuild Tree-sitter; we
  wrap it as one governed, measured component among several tiers.

### Camp 2 — Memory libraries (Mem0, Zep, Letta, Hindsight)
- **What they are.** The agent's memory lifecycle — recall, reflect, confidence, temporal graphs.
  Real, useful plumbing; this is the **established surround**, not novel ground.
- **How we win.** The builder-side research is blunt: these frameworks *"generally lack enterprise
  governance — no glossary, lineage, or entity resolution."* That absence is exactly the seam the
  commercial vendors sell into — and it is **our** moat (provenance, entity resolution, an admission
  bar, a measured delta). We don't out-feature Mem0 on recall; we make memory **governed and
  measured**.
- **What we wrap.** Memory is **context *management*** — table stakes we deliver, not the headline
  ([[context-enrichment-service.md]]: "sell the enrichment; deliver the management"). `memory/*`
  components ride the shared backend; we cover memory because an agent needs it, and claim no
  novelty there.

### Camp 3 — RAG frameworks (LlamaIndex, Onyx, LangChain, Haystack)
- **What they are.** Retrieval plumbing and app scaffolding. Onyx specifically proves the
  **self-host / air-gap** pattern regulated buyers want.
- **How we win.** A framework is a **blank canvas**: you wire nodes, pick a retriever, and there is
  no curated registry, no lift bar, no provenance, no costed composition. We are the **substrate +
  recommender** that fills the canvas with **lift-gated, governed** components and a number on each.
  LangSmith evals *your* app; it doesn't tell you *which components lift*.
- **What we wrap.** Retrieval (vector / lexical / graph / hybrid) is a first-class but **commodity**
  input — already the R0–R6 taxonomy + 20 `processors/retrieval/*` components
  ([[context-layer-pmf.md]]). We keep the regex/hybrid choice first-class and target self-host /
  air-gap delivery as a governed alternative to Onyx.

### Camp 4 — Enterprise context-layer vendors (Glean, Cortex, Atlan)
- **What they are.** The funded incumbents. **Glean** is the flagship — roughly **$7.2B valuation
  on ~$200M ARR** — selling an indexed-everything work assistant. **Snowflake Cortex** brings the
  context layer to where the data already lives; **Atlan** brings catalog/governance. This camp
  *validates the category* and is the strongest acquisition signal.
- **How we win.** They index the customer's *own* corpus into a closed console; they do **not**
  ship an **open protocol**, **model-portable** components, **separate-evaluator measured lift on
  the buyer's data**, or the **two-door** consumption model. They're a destination app; we're the
  governed *assembler/refinery* underneath any agent. We are complementary to Cortex (the data
  platform is the substrate; we are the lift + governance + composability layer on top —
  [[context-layer-pmf.md]]) and to Atlan (we *produce* the lineage they catalog).
- **What we wrap.** Nothing to wrap here — this camp is the **buyer/acquirer** archetype, not an
  input. The read for acquisition is in [[acquisition-positioning.md]] and [[acquihire-roadmap.md]].

---

## The durable edge (the defensible core — lead with this)

Four things, only one of which any single camp partially has, and **no camp has all four**:

1. **Separate-evaluator measured lift / fidelity on the buyer's own data.** A component is admitted
   only on `pipeline_score − bare_model_score > 0`, scored by a *separate* evaluator, never
   self-graded — the same engine extended from "does the pipeline lift?" to "did this tier
   preserve?" ([[context-enrichment-service.md]]; gate canon: `scripts/eval/reason_codes.py`,
   `scripts/eval/durable_gap_harness.py`). Glean asserts usefulness; we **publish a delta**, and the
   land motion proves it on the buyer's *own* system ("Import & Improve" — [[acquisition-positioning.md]]).
   The admission bar is also a **two-axis** test: the lift must be **structural/durable** (won't
   close when the next model ships), not transient.
2. **Governance chain-of-custody.** Provenance / AIBOM, citations, signed publishers, CDC /
   freshness / revocation, entity resolution, lineage — the exact list every OSS camp is *quoted*
   lacking. This is the **external moat**; it is orthogonal to model quality, so a bigger model
   supplies none of it ([[acquisition-positioning.md]]).
3. **Seven-primitive composability.** Every component reduces to one grammar — **Input · Knowledge
   Corpus · If Statement · Action · Loop · Stop/End · Output** ([[../concepts/component-taxonomy-and-stages.md]]) —
   so anything (a Repomix-style packer, a Mem0-style memory, a retriever) drops in as a governed,
   composable, costed node rather than a bespoke integration. Camps 1–3 are point tools; we are the
   composition layer.
4. **Two doors onto one governed object.** A Knowledge Corpus or tool is minted **once**, with one
   provenance trail and one lift + fidelity score, then consumed two ways: wired into a **bounded
   Open Harness Hub pipeline**, *or* served as **fuel** into an open-ended agent via Context
   Enrichment ([[two-services-shared-infrastructure.md]], [[context-enrichment-service.md]]). One
   COGS, two GTMs — a stronger acquisition story than any single camp.

The discipline that makes #1–#2 real is **honest counting**: we report `probed → confirmed →
sourced → built → novel → measured → promoted`, never "generated" as if promoted
([[acquisition-positioning.md]]).

---

## Commoditization threats (state them, don't flinch)

The mechanisms each camp owns are, individually, **going to zero** — which is *why* we wrap them
rather than build a business on any one. Naming the threats keeps positioning honest:

| Threat | What commoditizes | Our insulation |
|---|---|---|
| **Provider-native KV-cache** (e.g. TurboQuant, kvpress) | inference-time cache/quantization the model vendor ships for free | We don't sell caching; the **hyper-efficient tier** packages distilled facts onto a cacheable prefix so the *provider's* ~90%-off cache does the work — we sell the **governed, measured** packaging, and a free cache makes our tier *cheaper to run*, not obsolete ([[context-enrichment-service.md]]). |
| **Learned compression** (LLMLingua-2, and successors) | token-classification compression as a one-line library | It's a **wrapped component** (`summarize.llmlingua`), one tier among several; the moat is the **fidelity delta** scored by a separate evaluator, not the compressor. |
| **Free packing CLIs** (Repomix et al.) | raw → compressed structural packing | We host **governed, fresh, measured** tiers and serve them four ways; the CLI gives an ungoverned one-shot file that can't stay current. |
| **MCP disintermediation** | a universal protocol could let any corpus reach any agent directly, routing around an assembler | MCP is our **default serving surface**, not a bypass — what travels over MCP is *our* governed, measured, tier-negotiated object; the protocol carries the moat, it doesn't replace it ([[context-enrichment-service.md]]). |
| **Frontier models absorb long-tail capability** | components a better model can just do | The **two-axis lift gate** prunes absorbed components and reparks the registry on the moving frontier — the product gets *more* valuable as models improve, by construction ([[acquisition-positioning.md]]). |

**The throughline:** every commoditizing mechanism is an *input we wrap*, and every one of them
makes our wrapped tier **cheaper or fresher**, never redundant. The product is the **governance +
measurement + composability** around the commodity, not the commodity.

---

## How to position (the rule)

1. **Lead with measured-fidelity + governance, on the buyer's own data** — never with "we compress"
   or "we have memory." Those are commodity inputs; saying them first concedes the frame to Camp 1/2.
2. **Treat compression / memory / retrieval as wrapped commodity inputs** — name them as components
   we govern and measure, not as the thing we sell.
3. **Name the camp you're being compared to, then move to the seam.** Against Glean: "they index
   *your* corpus into a closed console; we're the open, governed assembler with a measured lift on
   *your* data, served two ways." Against Repomix: "that's one ungoverned tier; we host all three,
   fresh and measured." Against Mem0/LlamaIndex: "great plumbing — we make it governed and
   composable, with a number."
4. **For acquirers, the four-camp map *is* the pitch:** the category is real and funded (Glean,
   Cortex, Atlan), and the one composite none of them ships — governed + measured + composable + two
   doors on one COGS — is the asset. See [[acquisition-positioning.md]], [[acquihire-roadmap.md]].

---

*Grounds & companions: [[competitive-swot.md]], [[competitive-positioning-deep-dive.md]],
[[context-layer-pmf.md]], [[context-enrichment-service.md]], [[two-services-shared-infrastructure.md]],
[[acquisition-positioning.md]]; gate canon `scripts/eval/reason_codes.py`,
`scripts/eval/durable_gap_harness.py`; taxonomy [[../concepts/component-taxonomy-and-stages.md]].
All vendor numbers (Glean ~$7.2B/~$200M ARR, Repomix ~70%, etc.) are as reported in the 2026
competitive research cycle — treat each as a vendor/market claim, not an independently audited
figure, consistent with the skeptical stance in [[inference-time-capability-watch.md]].*
