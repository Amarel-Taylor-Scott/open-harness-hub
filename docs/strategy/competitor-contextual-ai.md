# Competitor Deep-Dive: Contextual AI (Douwe Kiela, "RAG 2.0")

Status: net-new competitive intelligence (no prior Contextual / Kiela / LMUnit / RAG-2.0
reference existed in `docs/`, `scripts/`, or `catalog/` — grep clean). Date: 2026-05-29.
Companion to `competitive-positioning-deep-dive.md` (which covers iPaaS / cloud platforms /
dev-hubs: Zapier, n8n, Vertex, Bedrock, LangChain, HF, Dify — but NOT Contextual).

---

## Verdict (lead)

**Threat level: HIGH on engine + brand + the agent *shape*; STRUCTURALLY ABSENT on OHH's
actual moat.** Take it seriously and do not flinch from why:

- **Pedigree.** Founder Douwe Kiela is lead author of the original 2020 RAG paper (Meta FAIR,
  ex-Hugging Face; now also a research director at Google DeepMind). He *owns the RAG
  narrative.* Co-founder Amanpreet Singh. Founded 2023, ~93 employees.
- **Funding.** ~$100M raised: $20M seed (Jun 2023, Bain Capital Ventures) + $80M Series A
  (Aug 2024, Greycroft lead; Bezos Expeditions, NVentures/Nvidia, **Snowflake Ventures**,
  HSBC Ventures, Lightspeed, Conviction). No confirmed Series B / unicorn round as of May 2026
  (unicorn talk is press speculation). Third-party tracker (getlatka) cites ~$10.2M ARR — i.e.
  deep enterprise sales into marquee accounts (Qualcomm, Advantest, HSBC), not broad self-serve.
- **Engines are genuinely SOTA.** RAG-QA Arena 71.2% vs 66.8% best baseline; OmniDocBench 87.0;
  BEIR rerank 61.2; BIRD 73.5%; Generate 88% on Google FACTS grounding vs Gemini 2.0 Flash
  84.6% / Claude 3.5 Sonnet 79.4% / GPT-4o 78.8%. **These are better engines than OHH's local
  Gemma/BM25 stand-ins — and OHH's own thesis says to WRAP them, not rebuild.**
- **They are moving UP into agents.** Agent Composer launched **Jan 27, 2026** ("AI for when it
  actually is rocket science"), with a domain-demo gallery (Material Science, 3GPP, Raspberry
  Pi, device-log RCA, propulsion anomaly) that visibly occupies "cited multi-step agent over a
  knowledge base" — the same surface OHH pitches, shipped with logos OHH lacks.

**But the threat is bounded.** Across all of Contextual's own documentation, **three of OHH's
four load-bearing differentiators have no analog**, and the fourth (governance) is a different,
weaker sense of the word. They are the *single most capable competitor to one day add* a
lift bar or verified-content provenance given Kiela's research bench — so the encroachment
signal is worth monitoring — but today they have not built it.

Net posture: **wrap their Component APIs; do not out-build their reranker or agent-UX; double
down on verified negative-space content + measured lift + enrichment + governance where they
are structurally absent; and lead positioning with measured-lift + negative-space corpora.**

---

## The crux, answered definitively

### (1) Verified corpora / pre-built RAG knowledge packs / governed content? **NO.**

Contextual is a **bring-your-own-data** engine + platform. The pricing page has **zero content
line items** — only processing/infra: Parse ($3/1k pages text, $40/1k multimodal), Rerank
($0.02–0.05/M tok), Generate ($3 in / $15 out per M tok), LMUnit ($3/M tok in). Datastores are
"fully-managed vector stores" the **user** fills via connectors (Box, Confluence, Google Drive,
OneDrive, SharePoint) or upload. There is **no signed publisher, no provenance-carrying verified
public corpus, no CDC/freshness, no revocation, no content marketplace.**

> Contextual governs the **plumbing** (attribution, entitlements, audit) over *your* data.
> OHH governs the **content itself** (verified, signed-publisher, freshness-tracked corpora in
> the capability negative space). Different products.

Note on the word "verified": Contextual's "verified answers" / "fine-grained attribution with
bounding boxes" means **faithful-to-the-retrieved-doc (grounding)** — *not*
verified-by-a-signed-publisher. A different sense than OHH's verified corpus.

### (2) Content enrichment (compression / tiering / distillation with measured fidelity)? **NO product.**

Only ingestion-side enrichment exists: Parse "infer[s] document hierarchy and add[s] positional
metadata to each chunk." There is **no raw → compressed → hyper-efficient tiering with measured
fidelity-per-tier** — i.e. **no analog to OHH's Baltor.** No MCP/llms.txt "serve into open
agents" door.

### (3) MEASURED LIFT vs a bare model (paired pipeline − bare, separate evaluator)? **NO — not in OHH's sense.**

This is the crux. Contextual publishes three quantitative stories; **none is paired
pipeline-vs-bare-model lift as an admission gate:**

- **LMUnit** (arXiv:2412.13091, open-sourced Jul 2025) is an **evaluation model** — inputs
  {prompt, response, unit_test} → continuous **1–5 score**. It is the *judge*, and its
  benchmarks (RewardBench2 82.1% top-2, RewardBench 93.5% top-5, SOTA FLASK/BigGenBench, beats
  GPT-4o/Claude-3.5 as a judge by >9% on scoring unit tests) measure **judge quality**, not the
  lift a component-over-a-corpus adds. It grades **answer quality**, never whether a pipeline
  beats the same bare model on task accuracy.
- **GLM / "RAG 2.0"** publishes **model-vs-model factuality** (FACTS 88% vs frontier models) —
  *their grounded model's* factuality vs Gemini/Claude/GPT, **not** the lift of a
  component-over-a-corpus vs the same bare model.
- **Agent Composer's** only quantitative claims are **workflow time-savings** — root-cause /
  device-log analysis "from 8 hours to 20 minutes." That is **efficiency/throughput, not
  accuracy lift** = (pipeline_score − bare_model_score) from a separate evaluator.

All Contextual benchmark comparisons are **vs rival VENDOR stacks** (Cohere+Claude, Gemini,
GPT-4o), **never vs the bare model**, and there is **no durability / will-it-survive-the-next-
model axis.** Components are admitted **by vendor fiat**, not by measured negative-space lift.

### The Material-Science / Agent-Composer overlap: platform showcase over public docs, NOT a governed-corpus product.

This is the owner's escalated worry, assessed squarely. **Partly justified, mostly not.**

- **Agent Composer** *is* conceptually the same object as OHH's assembler: a low/no-code visual
  builder for cited multi-step agents over a knowledge base — "arbitrary computational graphs"
  of "pre-made components such as search tools, third-party API/MCP integrations, and various
  LLMs," with Static Workflows + Agentic Research Steps, templates (Basic/Agentic Search, Deep
  Research, Root Cause Analysis, Task Execution, Structured Extraction), and it even uses the
  word **"components."** A buyer skimming both could conflate them.
- **But the domain demos are showcases over INGESTED PUBLIC docs, not productized governed
  corpora.** Material Science = "Search across **7,500+ arXiv** materials science papers"
  (arXiv connector). 3GPP Spec Explorer = "The documents were **obtained from the 3GPP archive
  using the `download_3gpp` CLI** and ingested" — i.e. public specs pulled with open-source
  tooling, **user-replicable.** The gallery (Rocket/Propulsion, Raspberry Pi, Device-Log RCA,
  Mazda Connect crash logs, ATE Board Validation, Test Program Gen) is a "look what's possible"
  showcase of platform range. **No signing, no provenance beyond "the 3GPP archive," no
  freshness/CDC, no publisher partnerships, no corpus versioning, no marketplace.** The corpora
  are not the product — the platform is, and it ships **empty**, filled with the *customer's*
  data.
- **No measured lift.** The Material Science Agent doc explicitly carries **"no comparison
  baseline or capability lift analysis against unaugmented models."** Output framing is grounding
  only: "Return verified answers with citations to source papers." 3GPP: "answers are grounded
  in the actual specs … citations to the source documents." **Grounding ≠ lift.**

So the overlap is **shape, vocabulary, and surface narrative** — real, and a buyer can conflate
them. It is **not** a governed-corpus product, a measured-lift product, or a negative-space
product. OHH's wedge survives contact; the job is to make the distinctions *legible*, because
`grounding != lift` and `ingested-public != governed` are currently invisible to a casual buyer.

---

## Table A — Contextual Component APIs vs OHH Processor layer

OHH processor layer is real and schema-backed: **166 processor manifests** across ~36 families;
`schemas/processor.schema.json` is a genuine runtime interface contract (`process_kind`,
`deterministic`, `idempotent`, `side_effects`, `on_error`, `streaming`, inputs/outputs,
`latency_budget_ms`, implementations, model_targets, retry). The honest gap: OHH ships **governed
YAML definitions + a minimal executor** (`scripts/run_pipeline.py`: real Ollama/Anthropic/OpenAI
adapter calls for harness/judge steps, deterministic fallback, unknown steps → `simulated:true`);
Contextual ships **production, SLA-backed, hosted REST endpoints at scale.**

| Contextual API | What it is | OHH analog (verified in live catalog) | Overlap | Where OHH differs / wins |
|---|---|---|---|---|
| **Parse** `POST /parse` (async; PDF/DOC(X)/PPT(X)/PNG/JPG <300MB <2000pp → Markdown/JSON + hierarchy; `parse_mode`, `enable_document_hierarchy`, `enable_split_tables`; **$3/1k text, $40/1k multimodal**) | Hosted multimodal doc-understanding pipeline | `processor/doc-to-markdown-rag-ingest`, `on-device-ocr-prepass`, `faithful-extract-before-model`, `processors/extract/*`, `format-convert/*`, page-structure-aware + recursive chunkers | **Doc→structured ingest.** Strong. | OHH path is **local/offline-first** (negative-space, no-cloud). Contextual = higher-accuracy hosted. **Complementary — wrap the cloud path, keep the local path.** |
| **Rerank** `POST /v1/rerank` ("**first instruction-following reranker**"; `ctxl-rerank-v2-instruct-multilingual` (+mini, +v1); query+docs[]+NL instruction → index+score 0–1; SOTA BEIR; **$0.05/$0.02 per M tok**) | Dedicated benchmarked instruction-following multilingual reranker model | `processor/rerank/cross-encoder` + `processor/gemma-reranker` (`process_kind rerank.cross_encoder`, local Gemma-via-Ollama, NL-rationale, deterministic BM25 fallback) + fusion (RRF, community-mapreduce/GraphRAG) + MMR; whole retrieval family = 23 | **Rerank.** Strong. | Contextual's model is **a clearly stronger engine** than OHH's local-Gemma reranker. **Wrap it.** OHH adds retrieval *breadth* (BM25/dense/hybrid/HyDE/multi-query/GraphRAG/agentic-grep/LLMLingua/injection-screen). |
| **Generate** `POST /v1/generate` (Grounded Language Model; messages[]+knowledge[]+model; inline attributions; prioritizes retrievals over parametric; **88% FACTS** vs frontier; `avoid_commentary`; **$3 in/$15 out per M**) | Single tuned grounding LLM with inline attributions | `processor/faithful-extract-before-model` (**deterministic** extract-before-model anti-hallucination pre-pass; `lift_reason deterministic_guarantee`) + grounded-response rubrics (clinical-grounded, census-grounded, rag-citation-audit) + 20 model **adapters** wrapping Anthropic/OpenAI/Gemini/Llama/Mistral/Qwen/Gemma/Ollama | **Grounded/cited generation.** Different *mechanism*. | Contextual = one tuned GLM + inline attributions. OHH = **deterministic extract-before-model + a SEPARATE evaluator scoring it**, over a **governed corpus** the `knowledge[]` comes from. GLM is a wrap candidate; OHH's differentiator is the deterministic pre-pass + the governed source. |
| **LMUnit** `POST /lmunit` (≤7000 tok; {query, response, unit_test} → 1–5; **OPEN-SOURCE** Jul 2025: `LMUnit-llama3.1-70b`, `-qwen2.5-72b` on HF, repo `ContextualAI/LMUnit`; beats GPT-4/Claude-3.5 as judge; **$3/M in**) | General NL unit-test **judge model** (single 1–5 score) | **Sharpest overlap & sharpest contrast.** `processor/eval/llm-judge` + `checklist-evaluator` (GO/NO-GO deterministic) + the **entire `catalog/rubrics` tree (~230 `*-quality-v1` rubrics)** + the verify family (12 criterion evaluators: llm-judge / deterministic / regex / semantic / tool-validate / composite AND-OR-NOT / hallucination-scorer SelfCheckGPT / document-grader Self-RAG / entity-resolution) + `scripts/eval` (`durable_gap_harness`, `reason_codes`) | **Same primitive (NL unit-test grading).** Tightest. | LMUnit is **one general judge.** OHH's eval layer is **per-domain scored rubrics PLUS the capability-LIFT admission harness** (paired pipeline-vs-bare-model + `durability_class`). **LMUnit could BE the judge model OHH's `llm-judge` wraps; it does NOT replace OHH's lift-gate or per-domain rubrics.** |

**Access:** On-Demand pay-as-you-go + $25 free credits, no minimums; Enterprise = custom +
guaranteed throughput + SLAs. "Tuned models" deploy **only on the agent where trained**
(platform-locked). Only **LMUnit** is open; the platform is closed SaaS.

**Read:** these are best-in-class **engine primitives** — *exactly* the kind OHH's thesis says to
**WRAP, not rebuild**. They are sold as per-token capabilities, **not** as governed, measured-lift,
provenance-carrying components inside a composition grammar. Overlap is strong at the
**component-mechanics layer** (and Contextual's pieces are likely better engines), **not** at
OHH's moat layer.

---

## Table B — Contextual Agent Composer + domain agents vs OHH governed domain pipelines + Baltor

OHH's agent-shape surface is broad: **420 pipeline YAMLs across 281 distinct domain folders**
(aviation-safety, building-code, clinical-coding, biosecurity, adverse-media-kyc, csrd,
chemical-sds, …) vs Contextual's ~5–8 gallery demos — but **largely DEFINITIONS** (minimal
executor; no per-domain measured eval attached to most).

| Axis | Contextual (Agent Composer + Material-Science demo) | OHH (governed domain pipelines + Baltor) | Verdict |
|---|---|---|---|
| **Builder surface** | Low/no-code visual builder; "arbitrary computational graphs"; Static Workflows + Agentic Research Steps; prompt-to-agent + drag-drop; "completely model agnostic"; one-click feedback optimization | Seven-primitive composition grammar (Input · Knowledge Corpus · If Statement/Conditional · Action · Loop · Stop/End · Output); every component a subtype of exactly one primitive (`scripts/primitives/*`) | **OVERLAP (shape).** Both "build a cited multi-step agent." Contextual = freer builder + better UX. OHH = explicit **grammar + admission gate + abstain/route discipline**. |
| **The corpus** | **Ingested PUBLIC docs as platform showcase** (7,500+ arXiv; 3GPP via `download_3gpp` CLI). Bring-your-own; ships empty; filled with customer data | **38 verified sources** in `data/source-registry.jsonl` (35 gov/standards: eCFR, OFAC, EU AI Act, BSP, DOLE/OSHC PH, UN/ILO/WHO/FAO/IEC), each with explicit license (US-gov PD ×14, PH-gov ×9, UN/EU/ILO terms) + `source_kind` (regulation 20 / standard 7 / dataset 6 / guidance 5) + `gov` + `verified_fetch`; 440 Knowledge-Corpus manifests | **NO OVERLAP.** Contextual sells the *platform*; OHH sells the **verified content**. (Honest: OHH's registry is **small, not thousands** — early but real.) |
| **Admission gate** | **Grounding/faithfulness + workflow time-savings** (8hr→20min). Material-Science doc: **"no comparison baseline or capability lift analysis."** Benchmarks vs rival vendors, never vs bare model | **Two-axis measured lift**: must LIFT (`pipeline_score − bare_model_score > 0`) AND be **structural/durable** (`scripts/eval/reason_codes.py`: 13 lift_reasons = 7 structural + 5 transient + 1 mixed; 7 mechanisms; 5 retrievability tiers; 3 durability classes; `gap_durability_score 0..5`) | **NO OVERLAP — OHH's core wedge.** Contextual measures **answer quality**; OHH measures **lift + whether it survives the next model.** |
| **Negative-space reach** | Clean RAG over **addressable corpora (tiers 1–3)** | Same-shaped worked example deliberately in **tiers 4–5** the architecture can't reach | **NO OVERLAP.** See worked example below. |
| **Enrichment / serving** | Ingestion metadata only; no tiering; single closed door (enterprise sales) | **Baltor**: raw → compressed → hyper-efficient tiers w/ measured fidelity-per-tier; 4 surfaces (MCP / llms.txt / Claude-Code skill / CLAUDE.md) | **NO ANALOG.** (Honest: Baltor is **spec-level** — see real-vs-planned.) |
| **Governance** | Enterprise **ACCESS control** (SSO/RBAC, query-time entitlements) over the customer's **private** docs (Qualcomm: millions of pages, 24h ingestion). No signed publishers, no provenance of public data, no CDC/revocation | Provenance + signed publishers + open-core + **EU-AI-Act tagging** (`eu_ai_act_risk`, high_risk on building-safety) + accountable-signer framing (`scripts/foundry/openness.py`, `docs/strategy/open-core-model.md`) | **NO OVERLAP.** Contextual governs *access to your data*; OHH governs *the content's provenance/freshness/revocation.* |
| **Openness** | Closed SaaS; only LMUnit open-sourced; proprietary visual builder = lock-in | Open protocol/schemas/engine/grammar + externally-published gov content + public-good carve-out; commercial = OHH's own verified RAG DBs + custom tools + live layer | **NO OVERLAP.** Portability/no-lock-in is a real enterprise objection to a single-vendor closed stack. |

### OHH's single best head-to-head artifact vs the Material-Science demo

`docs/strategy/building-safety-dev-countries-worked-example.md` + **5 runnable pipelines** in
`catalog/pipelines/building-occupational-safety-ph/` (building-permit-amendment, NSCP
structural-load-coefficient verify, OSH fall-protection/scaffold check, floor-count/permit-
discrepancy detect, occupancy-permit prerequisite gate). This is a "governed domain pipeline over
a corpus" **exactly** like Contextual's Material-Science agent — but **deliberately built in the
NEGATIVE SPACE Contextual's clean-RAG architecturally cannot reach**: `no_addressable_source`
(counter-only permit records, tier-4), `embodiment_required` (as-built floor count = human site
visit, tier-5), `accountability_or_license` (PRC-licensed sign-off a model can't hold),
`volatile_fact` (IRR clause renumbering). Durability **5.0/5.0** via `reason_codes.py`. The
Knowledge-Corpus + If-Statement (**abstain when unverifiable, never infer**) + Action
(**route-to-authority-with-citations**) pattern is the credible counter to a clean-RAG demo that
*will* answer even when it shouldn't.

---

## OHH's durable edge — and honest risks

### Durable edge (Contextual has no analog)
1. **Durability axis** — structural-vs-transient lift, "will it survive the next model?"
   (`reason_codes.py`, single source). Contextual measures answer quality; it has **no**
   will-it-survive axis. This is the genuinely novel selection criterion.
2. **Verified negative-space content** — signed publishers / gov-standards / CDC freshness /
   revocation, targeted where base models lack capability. Contextual governs *private-doc
   access*, never *public-content provenance.* This is the **biggest white space.**
3. **Seven-primitive open grammar + open-core protocol** vs a closed proprietary builder.
4. **Enrichment tiers + two-doors (Baltor)** — one governed object, two doors (bounded OHH
   pipeline OR open-agent fuel via MCP/llms.txt). No Contextual analog.

### Honest risks
- **They win on RAG-engine quality.** Their Parse/Rerank/Generate/LMUnit beat OHH's local
  stand-ins on public benchmarks. Do **not** compete on engine mechanics or RAG benchmarks.
- **They win on agent-build UX + brand + logos + funding.** No-code builder, Kiela's RAG
  narrative, Qualcomm/Advantest/HSBC, ~$100M. OHH has none of these.
- **The build-pitch pressure is real.** If Agent Composer makes "cited domain agent over my
  data" trivial and free-feeling, OHH's *build* pitch is pressured — OHH must shift the story
  from "we build cited domain agents" (commoditizing) to "**governed VERIFIED content + measured
  lift/fidelity that engines like Contextual cannot self-certify.**"
- **They are the most credible org to encroach.** Kiela's research bench + Agent Platform +
  LMUnit eval + GLM inline attributions already supply **three of OHH's four moat ingredients**;
  the gap they'd still need to close is **verified-corpus-in-the-negative-space + the lift-
  admission gate.** Snowflake Ventures on their cap table aligns with OHH's own "context layer"
  TAM (SNOW/MDB/NET) — the collision zone is real.
- **OHH's measured-lift EVIDENCE is thin (credibility-critical, must not overclaim).** The
  *mechanism* is real and honest — `scripts/foundry/measure.py` computes
  `pipeline_score − bare_model_score`, leaves `lift=None` and **routes to review** when
  unmeasured ("never makes up a number"); `reason_codes.py` durability taxonomy is fully
  implemented. **But: 0 catalog YAMLs carry `measured_lift`/`pipeline_score`/`bare_model_score`
  fields** (verified by grep); the 4,377-row `capability_lift_gate.py` pass (kept 2,397 / culled
  1,980 at lift_floor 0.2) is an explicit **heuristic prefilter** (`heuristic_quality_score`),
  NOT paired measurement; Baltor is **spec-level** (two real scripts —
  `structural_compress.py` ~70% on code + `compression_fidelity_check.py` deterministic-proxy
  fidelity 0..1 — but the tier pipeline, MCP endpoint, 4 emitters, and meter are **not built**).
  **Framing rule: claim the lift MECHANISM and the DURABILITY taxonomy as real; do NOT claim
  measured-lift as a populated reality.**

---

## Strategic recommendation: WRAP, don't compete

**Decision: wrap Contextual's Component APIs as governed measured-lift OHH components; do not
out-build their reranker or agent-UX; concentrate force on verified content + measured lift +
enrichment + governance where they are structurally absent; lead positioning with measured-lift +
negative-space corpora.** This is fully consistent with OHH's stated wrap-the-best-engine thesis —
and Contextual's existence is a **validation** of it.

**Concede (do not contest):** shipped-scale production endpoints; RAG-engine benchmark wins;
no-code agent-build UX; brand/funding/logos.

**Compete (where they have no analog):** durability + negative-space + governed verified content +
open protocol + enrichment tiers/two-doors.

### Concrete next steps
1. **Ship a `contextual-ai` adapter family** under `catalog/adapters/` (none exists today — dir
   has Anthropic/OpenAI/Gemini/Llama/Mistral/Qwen/Gemma/Ollama/embeddings). Four adapters wrapping
   Parse / Rerank (ctxl-rerank-v2) / Generate (GLM) / LMUnit, each declared as a **measured-lift
   OHH component** with `process_kind`, deterministic-fallback to the existing local processor
   (`gemma-reranker`, `doc-to-markdown-rag-ingest`, `faithful-extract-before-model`, `eval/llm-
   judge`), and a `cost`/SLA note. **LMUnit is the highest-value wrap** — make it a selectable
   judge model behind `processor/eval/llm-judge` and the rubric tree.
2. **Publish a measured-lift head-to-head on a shared domain.** Stand up the *same* corpus
   (e.g. 3GPP specs or arXiv materials-science — both public, both replicable) and run
   `scripts/foundry/measure.py` paired (pipeline-vs-bare, separate evaluator) — the number
   Contextual's Material-Science doc explicitly **does not** publish. Put it head-to-head against
   their demo. **Do this for real or not at all** — overclaiming here is the one self-inflicted
   risk that would cost more than the win.
3. **Lead every comparison with the two distinctions a buyer can't see:** `grounding != lift`
   (they ship grounding/time-savings; OHH ships paired lift + durability) and
   `ingested-public != governed` (they ship an empty BYO platform; OHH ships verified,
   signed-publisher, CDC-fresh corpora in the negative space).
4. **Monitor the encroachment signal.** Watch Contextual releases for any "verified source
   provenance," "signed/certified content," "data provenance," or "measured improvement over
   base model" language — that is the direct moat-encroachment trigger and they are the single
   most capable org to attempt it.

---

## Sources

**Contextual AI (current, 2026):**
- https://contextual.ai/component-apis · https://contextual.ai/platform · https://contextual.ai/pricing · https://contextual.ai/lmunit/
- https://docs.contextual.ai/llms.txt · https://docs.contextual.ai/api-reference/parse/parse-file.md · https://docs.contextual.ai/api-reference/rerank/rerank.md · https://docs.contextual.ai/api-reference/generate/generate.md · https://docs.contextual.ai/api-reference/lmunit/lmunit.md · https://docs.contextual.ai/admin-setup/pricing-billing.md · https://docs.contextual.ai/reference/generation-model.md
- https://docs.contextual.ai/examples/material-science-agent · https://docs.contextual.ai/examples/3gpp-spec-explorer · https://docs.contextual.ai/examples/overview-demos · https://docs.contextual.ai/quickstarts/agent-composer · https://demo.contextual.ai/
- https://contextual.ai/blog/introducing-agent-composer · https://contextual.ai/blog/introducing-grounded-language-model · https://contextual.ai/blog/introducing-instruction-following-reranker · https://contextual.ai/blog/platform-benchmarks-2025 · https://contextual.ai/research/introducing-rag2 · https://contextual.ai/case-study/qualcomm
- https://github.com/ContextualAI/LMUnit · https://huggingface.co/ContextualAI/LMUnit-qwen2.5-72b · https://arxiv.org/abs/2412.13091 · https://arxiv.org/pdf/2412.13091
- https://deepmind.google/blog/facts-grounding-a-new-benchmark-for-evaluating-the-factuality-of-large-language-models/
- https://www.prnewswire.com/news-releases/contextual-ai-launches-agent-composerai-for-when-it-actually-is-rocket-science-302670581.html · https://venturebeat.com/ai/contextual-ais-new-ai-model-crushes-gpt-4o-in-accuracy-heres-why-it-matters · https://venturebeat.com/technology/contextual-ai-launches-agent-composer-to-turn-enterprise-rag-into-production
- https://en.wikipedia.org/wiki/Contextual_AI · https://en.wikipedia.org/wiki/Douwe_Kiela · https://contextual.ai/blog/announcing-series-a · https://www.greycroft.com/perspectives/expanding-our-investment-in-contextual-ai/ · https://getlatka.com/companies/contextual.ai · https://pitchbook.com/profiles/company/528886-72

**OHH self-map (corroboration — verified this turn):**
- `scripts/eval/reason_codes.py` (13 lift_reasons = 7 structural + 5 transient + 1 mixed; 7 mechanisms; 5 retrievability tiers; 3 durability classes; MAX_TIER 5) · `scripts/eval/durable_gap_harness.py`
- `scripts/factory/capability_lift_gate.py` + `dist/reports/capability-lift-gate.json` (total 4,377 / keep 2,397 / cull 1,980 @ lift_floor 0.2) · `scripts/foundry/measure.py` · `scripts/foundry/skillsbench.py` · `scripts/eval_judge_arms.py` · `scripts/run_pipeline.py`
- `schemas/processor.schema.json` (166 processor manifests) · `catalog/processors/verify/` · `catalog/processors/retrieval/` · `catalog/adapters/` (no contextual adapter yet) · 420 pipeline YAMLs · 440 Knowledge-Corpus manifests · 0 catalog YAMLs carry measured-lift fields (grep)
- `data/source-registry.jsonl` (38 verified sources: 35 gov; regulation 20 / standard 7 / dataset 6 / guidance 5) · `catalog/pipelines/building-occupational-safety-ph/` (5 pipelines)
- `scripts/seed/baltor_components.py` · `scripts/processors/compression/structural_compress.py` · `scripts/processors/verify/compression_fidelity_check.py`
- `docs/strategy/context-enrichment-service.md` · `docs/strategy/two-services-shared-infrastructure.md` · `docs/strategy/open-core-model.md` · `docs/strategy/building-safety-dev-countries-worked-example.md` · `docs/concepts/component-taxonomy-and-stages.md` · `docs/strategy/competitive-positioning-deep-dive.md` (covers iPaaS/cloud/dev-hubs, NOT Contextual)
