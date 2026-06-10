# Inspiration bibliography — the works that shaped the platform

**Warrant: corroboration — the cited works themselves.** This is a *curated* bibliography, not a
literature survey: each entry gives **one line on the idea** and **one line on the exact platform
design choice it informs**. It exists so an agent or reviewer can trace any load-bearing decision in
Open Harness Hub / Baltor back to the public work that justifies it — and so we never
present a borrowed result as our own. Numbers below are **as reported by the cited authors**; we
admit no technique on its press release — every one is re-measured under our own lift/fidelity gate
before promotion (see the honesty rule at the bottom).

The platform thesis these works converge on: **the model is an analyst at a small desk; the scarce
resource is what sits on the desk, governed, at minimum token cost** ([[context-layer-and-the-desk]]).
We did not invent the context layer — we are building the *governed, measured-lift assembler* of it
([[context-layer-pmf]]). These are the shoulders that stands on.

---

## Memory — what stays on the desk across turns

### MemGPT / Letta — Packer et al., "MemGPT: Towards LLMs as Operating Systems" (2023; Letta = the productized successor)
- **Idea.** Treat the context window as **RAM in an OS memory hierarchy** — the agent itself pages
  information between a small in-context working set and larger external stores (recall/archival),
  with the model issuing its own memory-management calls.
- **Design choice it informs.** The canonical product metaphor *is* MemGPT's: **window = RAM,
  distilled memory/cache = swap, raw docs = disk, retrieval = the page-fault, MCP = the bus**
  ([[context-layer-and-the-desk]]). It is why the catalog separates *freezable* resident components
  from the one expensive model call we minimize, and why memory is a distinct component family
  (`memory/*`) rather than a prompt trick.

### Mem0 — "Building Production-Ready AI Agents with Scalable Long-Term Memory" / Hindsight (recall-network memory)
- **Idea.** Don't store raw chat history — **extract and store the distilled facts/observations**, so
  each retained token carries more signal; recall the few that matter, reflect, score confidence.
- **Design choice it informs.** The **hyper-efficient tier** of Baltor is Mem0/Hindsight
  shaped: distilled facts/observations **packaged onto a cacheable prefix** so the provider prompt
  cache does the heavy lifting ([[context-enrichment-service]]). It maps to "store what was *learned*,
  not raw history" — the `memory/distilled · reflect · confidence` family on the shared backend
  (`scripts/seed/context_layer_components.py`; the `enrichment` service is `status:planned` in
  `services/registry.yaml`). **Honest caveat, carried from the source review:** vendor agent-memory
  numbers (LongMemEval/LoCoMo, Hindsight's reported 91.4%) are **directional and don't all survive
  scrutiny** — which is *why* our lift is measured paired, on the user's data, by a separate
  evaluator, never a vendor figure ([[context-layer-and-the-desk]], honest-caveats section).

---

## Compression — more signal per inch of desk

### LLMLingua-2 — Pan et al., "LLMLingua-2: Data Distillation for Efficient and Faithful Task-Agnostic Prompt Compression" (Microsoft, 2024)
- **Idea.** Prompt compression as **token-classification** (keep/drop each token via a distilled
  encoder) rather than generation — task-agnostic, faithful, and **3–6× faster than LLMLingua v1** at
  2–5× compression (general 5–20×, up to ~95%).
- **Design choice it informs.** It is the **learned** lane of the three-tier compression stack
  (`summarize.llmlingua` / `llmlingua-compress`), distinct from the structural lane (next entry) —
  three different *mechanisms* are exactly why the tiers productize as three SKUs
  ([[context-enrichment-service]], recommended stack in [[recommended-stack-and-cloud]]). Pairs with
  the load-bearing **"cache first, compress only at a measured breakeven"** rule — the honest note
  attached to the compressor in the catalog.

### Repomix / Tree-sitter structural compression (the raw→compressed proof)
- **Idea.** **Strip function bodies, keep signatures** via AST/Tree-sitter parsing for ~**70% token
  reduction on code** while preserving structure losslessly — already shipping an MCP server and an
  official Claude Code plugin.
- **Design choice it informs.** The **structural** compression lane (`compress.structural`) and the
  *four delivery surfaces* (MCP · packed file/llms.txt · skill · CLAUDE.md fragment) are modeled
  directly on Repomix's proven shape; the whitespace is that **nobody hosts the tiers as governed,
  fresh, measured artifacts** — that gap is Baltor's opening ([[context-enrichment-service]]).

---

## Retrieval — point at the right page, not the whole shelf

### Amazon — "Keyword Search Is All You Need" (lexical search is a strong, often-sufficient baseline)
- **Idea.** For many production retrieval tasks, **lexical/keyword (BM25-style) search matches or
  beats** dense vector retrieval — exact terms, identifiers, laws, model names, and codes are found
  by the literal token, and hybrid only helps when you fuse the two.
- **Design choice it informs.** Keyword/lexical retrieval is **first-class, not a fallback**, in the
  R0–R6 taxonomy: the catalog keeps BM25, exact-id, and **fuzzy/regex** as real components alongside
  dense, with **hybrid + RRF** as the fusion option ([[context-layer-pmf]], retrieval row;
  `scripts/processors/retrieval/*`). The product's hybrid search is keyword **+** vector **+** graph
  **+** facets — exactly because lexical so often wins on the identifier-shaped queries our esoteric
  corpora are full of.

### GraphRAG — Edge et al., "From Local to Global: A Graph RAG Approach to Query-Focused Summarization" (Microsoft, 2024)
- **Idea.** Build a **knowledge graph + community summaries** from a corpus so the system can answer
  **global / multi-hop** questions a flat top-k vector retrieve cannot.
- **Design choice it informs.** `retrieval/graphrag` is a named member of the retrieval family and one
  of the explicitly-flagged **build gaps** to seed so the catalog matches where the market spends
  ([[context-layer-pmf]], retrieval row; [[context-layer-and-the-desk]], layer 2). It is treated as a
  *governed, measured-lift component we wrap*, not a framework we adopt wholesale.

---

## Standardization & runtime — the bus and the connectors

### MCP — Anthropic, "Model Context Protocol" (2024)
- **Idea.** An **open protocol** for feeding tools and context to any agent — the converging standard
  that lets a corpus/tool be served to Claude Code, Cursor, or any MCP client without a bespoke
  integration.
- **Design choice it informs.** MCP is the **default delivery surface** for Baltor
  (`deliver.mcp_serve`) and OHH's connector layer (`/connect`, Confluence/GitLab/Postgres connectors)
  ([[context-enrichment-service]], [[two-services-shared-infrastructure]]). The **deliberate caveat,
  corroborated by the research:** *"MCP moves context, it does not produce it"* (Gartner's read that
  ~60% of MCP-only agentic projects fail by 2028 without a consistent governed layer beneath) — which
  is precisely the seam the governed assembler fills ([[recommended-stack-and-cloud]]).

---

## Operating discipline — how the platform behaves by construction

### 12-Factor Agents / 12-Factor AgentOps (and awesome-context-engineering)
- **Idea.** A field-sourced set of operating principles for reliable agents: *everything is context
  engineering; no agent grades its own work; if it's not in git it didn't happen; cache first; store
  what was learned, not raw history; treat all retrieved content as untrusted; keep critical rules out
  of compaction.*
- **Design choice it informs.** These are enforced **by construction**, not as advice
  ([[context-layer-and-the-desk]], best-practices section): the eval/rubric stage + human-approval
  gate (a separate reviewer — lift measured *paired*, never self-asserted, also the source of the
  hard rule in [[../codex/change-verification-contract]]); the fully git-versioned + content-hashed
  catalog; the `cache/` family before the compressor; governed Conditionals kept out of lossy
  summarization; and the adversarial screen (next entry).

---

## Adversarial & verification — the gate guard and the fact-checker

### Prompt-injection defense lineage (LLM Guard · garak · Rebuff · NeMo Guardrails; the grep/pattern-detection corpus)
- **Idea.** **Treat all retrieved content as untrusted** — prompt injection, secret leakage, and
  poisoned context are the core threat surface; defend with layered input/output scanners, canaries,
  and deterministic pattern detectors (gitleaks/trufflehog/Presidio/Semgrep families).
- **Design choice it informs.** The adversarial layer is a real component bucket —
  `processor/prompt-injection-screen`, trust boundaries, read-only/ACL-aware connector scoping — and
  the deterministic detectors seed the **Conditional / grep rule** families
  ([[context-layer-and-the-desk]], layer 5; `.research-notes/stream-6-grep-libraries.md`). This is
  also why a fitted artifact (e.g. an activation gate) is treated as *potentially carrying its
  training data* and reviewed for leakage before promotion ([[inference-time-capability-watch]]).

---

## Provenance & governance — every claim traces to a source (the external moat)

### C2PA · SPDX · W3C DPV (and the broader AIBOM / lineage stack: PROV-O, OpenLineage, CycloneDX-ML)
- **Idea.** Open standards for **trustworthy provenance and rights**: C2PA signs *what an asset is and
  how it was made* (AI-generated assertions), SPDX is the de-facto *license* SBOM grammar, and W3C
  DPV gives machine-readable *personal-data category / purpose / legal-basis* IRIs.
- **Design choice it informs.** The product's **emit-don't-be** philosophy: OHH keeps its own
  composition taxonomy but **emits** these as the lingua franca — `license` already conforms to SPDX,
  image/audio/video generation components carry a **C2PA** AI-generated assertion, and free-form
  privacy fields are replaced by **DPV** IRIs ([[../research/standards-landscape]],
  `.research-notes/stream-4-provenance-privacy.md`). These standards are *how* governance — the
  external moat — is made auditor-ingestible without anyone writing a parser
  ([[value-propositions]], claim 2).

---

## Inference-time capability — techniques we host, not competitors

### Closed-form controllers / activation gates (Hassana Labs; NTK-dual → forward-pass activation multiply)
- **Idea.** A claimed shortcut for fine-tuning: the logit effect of one SGD step has an NTK
  closed-form that reduces to a **forward-pass elementwise activation gate** — fit a ~78 KB gate on
  support data (~$2/15-min on one A100), compose gates by addition (reported GSM8K base+gate 84% vs
  Instruct 73%; **arXiv pending, not yet citable**).
- **Design choice it informs.** It is admitted as a **"controller" Action** (an adapter subtype) — not
  a new primitive — with the gate's **support corpus as its Knowledge Corpus** and its provenance
  inherited by the artifact; composition is a **per-pair measured fact**, never an assumed sum
  ([[inference-time-capability-watch]], Result A). The lesson it confirms: cheaper adapters
  *commoditize the adapter layer and raise the value of the governed corpus + measurement* — our moat.

### "Reasoning with Sampling" — Karan & Du (training-free MCMC-style decoding on the model's own sharpened likelihood)
- **Idea.** Match much of RL post-training's reasoning gain by **sampling the base model more
  cleverly** (iterative MCMC toward higher self-likelihood) — no training, no reward model, and it
  *avoids RL's diversity collapse*; the unstated cost is **extra inference compute per answer**.
- **Design choice it informs.** Admitted as a **"reasoning-sampler" harness** whose Loop + Stop/End
  budget makes it *deterministic by config*, and whose lift contract reports **lift per unit inference
  compute** so "free" never leaks from the press framing into our cost estimator
  ([[inference-time-capability-watch]], Result B). Strategically it *raises the bare-model baseline*,
  which makes every component's measured lift **harder and therefore more credible** — a complement,
  not a threat.

---

## The market thesis — why the seam is worth building

### The context-layer investing thesis (Snowflake / MongoDB / Datadog / Cloudflare consumption prints, 2026)
- **Idea.** AI doesn't replace the data platform — it **feeds it more work** (retrieval, memory,
  real-time signals, governance), billed **per query / per GB / per inference**; the public-market
  winners are consumption-priced "context layers," and the open memory/RAG frameworks (Mem0, Zep,
  Letta, LlamaIndex, LLMLingua, GPTCache) supply the plumbing.
- **Design choice it informs.** It validates **where** the platform sits and **how** it charges: the
  named winners sell *infrastructure* and the OSS frameworks supply *plumbing* — **both lack
  governance + measured-lift + composability**, which is the seam OHH occupies as the open *governed
  assembler* ([[context-layer-pmf]]). Our billing axes (build-on-demand, live-subscription,
  hosted-endpoint) are already the per-query/per-GB/per-inference motion — applied to the *governed
  component layer*, not raw storage.

---

## The honesty rule that governs this whole list

No work above is adopted on its headline. Each technique becomes a **governed component only after a
*reproduced* lift over the *right* baseline on a held-out split, scored by a separate evaluator** —
the same `pipeline_score − bare_model_score` gate the whole registry runs on, and the same
measured-fidelity guarantee Baltor lives on ([[../codex/master-goal]],
[[value-propositions]]). Transient gains (better sampling, cheaper adapters) are tagged transient and
their decay is watched; the durable value sits in the **governed corpus, the measured composition
facts, the safety gate, and the assembler** — none of which a bigger model or a faster decoder
supplies ([[inference-time-capability-watch]], [[../codex/change-verification-contract]]).

---

*See also:* [[context-layer-pmf]] · [[context-enrichment-service]] ·
[[two-services-shared-infrastructure]] · [[context-layer-and-the-desk]] ·
[[recommended-stack-and-cloud]] · [[inference-time-capability-watch]] ·
[[../research/standards-landscape]] · [[value-propositions]] · [[../codex/master-goal]] ·
[[../codex/change-verification-contract]].
