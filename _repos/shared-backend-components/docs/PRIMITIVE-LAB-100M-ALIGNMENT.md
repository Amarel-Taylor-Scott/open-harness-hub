# Primitive Lab → 100M+ Alignment (owner feedback intake, 2026-07-10)

> **Status:** owner-directed alignment map + hand-off prompt. Everything referenced is `candidate=true,
> serves_truth=false` until its own gates pass. Counts in this doc that describe the repo are COMPUTED by the named
> modules — run them rather than trusting prose (`primitive_attribute_plan.py --plan`, `adaptive_vectorization.py
> --levels`, `check_ai_done_right_surface_family.py`).

The owner shared an external ChatGPT "Primitive Lab scaffold" proposal (semantic ABI · 667 attributes · 1,152
description views · 53 stages × 369 paths · evidence graph · compatibility blockers · PrimitiveML-Kaggle 6-arm
benchmark) as **feedback/ideas, not a mandate**. This doc reconciles those ideas with what THIS repo already has
(wrap/extend, never rebuild), records what was adopted this session, and ends with the **copy-paste prompt for
Claude Fable 5** the owner asked for.

## 1. Reconciliation map — their idea ↔ our existing asset ↔ the gap

| External proposal | Already here (do NOT rebuild) | Real gap (adopt) |
|---|---|---|
| 53 stages × 369 interchangeable paths | `pipeline_path_graph.py` (8 stages × 36 options ≈ 76,800 paths) + the zoos (`query_expansion_zoo`, `rank_fusion_zoo`, `embedder_zoo`, `path_router_zoo`) + `graph_flexibility.py` ENFORCES extensibility | more stages as rows (intake/boundary-detection/ABI-extraction…) — additive rows, never a parallel graph |
| 667 attributes; 1,152 description views; 30,802 logical slots | 61-column multi-index (pilot slice) + facet enrichment (~90 surfaces/card) + 3-register embeddings | **CLOSED 2026-07-10:** `primitive_attribute_plan.py` — computed, uncapped: 32 facets × 9 styles × 4 audiences = 1,152 views; ≥500 floor RATCHETED; per-primitive logical slots ~65K (computed) |
| "retain full logical catalog, materialize only useful views" | **CLOSED 2026-07-10:** `adaptive_vectorization.py` — the 5-level usage-earned WATERFALL (L0 universal → L4 multi-model+ColBERT), persisted level state + lossless history + build worklist | wire the worklist into `build_primitive_embeddings` / `primitive_multi_model_store` batch builds |
| 8 embedding model slots | `embedder_zoo.EMBEDDER_BACKENDS` (18 live backends as of today; the plan module reads the zoo, so adding a model grows the plan) | hosted-provider rows (OpenAI/Cohere/Voyage/Gemini/Jina) as opt-in keyed lanes |
| 18 hash/LSH profiles (wide + slim) | MinHash-LSH in dedupe/bakeoff; blocking keys on cards | `HASH_LSH_PROFILES` catalog declared in `primitive_attribute_plan.py`; implement as store columns behind the waterfall |
| lexical/NLP matcher families with trainable weights (keyword, edit distance, word frequency, vowel/consonant/letter metrics…) | lexical index + `esoteric_query_bench` (letter-level corruption probes) + `linker_scoring_zoo.train_weights` | `LEXICAL_SIGNAL_FAMILIES` catalog (18 trainable lanes) declared; implement each as a search-stage row in the graph |
| Evidence graph (typed provenance, supports/refutes, supersession) | hash-chained `primitive_usage_ledger`, receipts everywhere, lossless-distillation law, promotion gates | typed claim/observation records per attribute (the observation model: state=known/unknown/conflicted, never silent false) |
| Compatibility blockers (similarity ≠ compatibility) | typed `input_edge`/`output_edge` contracts, the strict `compose_route` (refuses invalid joins), two-axis admission gate | ML-specific blockers (task/cardinality/rows/GPU/package-version) as structured pass/fail/unknown results |
| MCP + key-based self-service after billing | **CLOSED 2026-07-10:** `cloud_provisioning.py` (plan/preflight/apply guarded by `OH_BILLING_ENABLED=1`+confirm, registered in `.mcp.json`) + waterfall meta-tools; `capability_agent_tool.py` (deterministic, key-gatable) + `provision_access.py` (key minting) | run it for real once billing is enabled |
| MCP that learns from environment/requests/database | **CLOSED 2026-07-10:** `environment_request_learning.py` + the opt-in `OH_MCP_ADAPTIVE_LEARNING=1` lane in `capability_retrieval_mcp_server.py` (fingerprint any technology → request+usage ledgers → non-destructive learned rerank; fail-open) | let it accumulate real traffic; periodically race learned-vs-off like every other lane |

**Answer to "why did you only support 60 columns?":** 61 was a pilot slice derived from the role-matrix
vocabularies, never a design ceiling. The ceiling is now structurally impossible: `primitive_attribute_plan.py`
computes the column space from data catalogs (facets × styles × audiences × models × hashes × lexical families ×
projections). Supporting more = adding a row; its self-test proves a one-row addition grows the plan and fails if
the computed plan ever drops below the owner's 500 floor.

## 2. PrimitiveML-Kaggle — the 6-arm benchmark design (adopted as the target experiment)

The cleanest external test of the primitive thesis: an outcome number Kaggle scores, not our own rubric.

- **Arms:** A harness+LLM (baseline) · B +deterministic ML tools, no search (isolates tooling) · C +primitive
  retrieval, LLM integrates (isolates retrieval/RAG) · **D +retrieval+deterministic linker (the treatment)** ·
  E fixed AutoML, no LLM (is the LLM adding value?) · F oracle primitive set → linker (retrieval-perfect upper
  bound). A-vs-D is the headline; B/C stop us mis-attributing gains; C-vs-D isolates *deterministic linking* from
  ordinary RAG (D preserving score while slashing output tokens is the thesis-confirming shape).
- **Lanes:** (1) strict offline replay on the four TML-Bench tabular competitions (hidden holdout, no internet,
  their 240/600/1,200s budgets, 5 repetitions); (2) **live post-cutoff**: Playground S6E7 "Predicting Student
  Health Risk" (balanced accuracy, deadline 2026-07-31 — a genuinely un-memorized test if the model's cutoff
  predates it); (3) later, a ~12-task MLE-bench subset across modalities. Report lanes separately, always.
- **Token ceilings alongside wall-clock:** 10k / 40k / 150k effective tokens; a run stops at whichever limit hits
  first and is scored on its best complete artifact. Failed runs KEEP their full token/compute bill.
- **Primary metric:** normalized quality `Q = (agent − naive) / (reference − naive)` (direction-corrected), and
  `verified_quality_per_million_tokens` — never "fewer tokens" alone (a system can save tokens by failing). This
  matches our existing honest-numbers law and the orchestrated-lane framing (bare vs orchestrated, executed).
- **Leakage rules:** corpus provenance must predate/be disjoint from the evaluated competition
  (leave-one-competition-out; stronger: hold out task FAMILIES); Kaggle credential lives in the host evaluator,
  never the agent workspace; one legitimate team, few predeclared real submissions, everything else scored on the
  local hidden holdout. Our Kaggle token is already configured (`~/.kaggle/access_token`).
- **Pilot corpus:** 500–2,000 *verified* ML primitives (data-understanding / task+metric inference / splits /
  preprocessing+features / models / tuning+ensembling / submission-validation families), each with ML-specific
  hard blockers — NOT the 50M raw corpus. Scale count and lift-routing stay separate concerns (raw-count law).
- **Decision gates:** (1) does D beat A on quality-per-Mtoken at equal-or-better valid-submission rate? (2) does D
  beat B AND C (semantic selection + deterministic assembly, not tools or RAG alone)? (3) does the advantage grow
  with the fraction of the winning pipeline supplied by verified primitives?

**Build-out seams when we start:** the run harness extends `harness_bakeoff_spec` /
`run_realistic_session_benchmarks.py` patterns; the deterministic linker IS `primitive_runtime.compose_route`;
stage alternatives (loaders/splits/models/ensembles…) enter as `pipeline_path_graph` rows so every ML operation has
multiple raceable paths from day one; the Kaggle popularity loop (commit `05d3b19fa`) already mines the source side.

## 3. What landed this session (all self-tests green, registered in `flywheel_proof_modules.py`)

1. `environment_request_learning.py` — the MCP flexible/learning lane (any-technology fingerprint, request ledger,
   database-derived non-destructive rerank; OFF = bit-identical, ON = annotated; fail-open).
2. `capability_retrieval_mcp_server.py` v0.4.0 — opt-in adaptive lane wired into `primitive_search` (default OFF).
3. `capability_agent_tool.py` — the deterministic developer/agent tool: 16 allowlisted, receipt-backed, key-gatable
   actions over the SAME engines (search/get/compose/corpus + usage ledger + waterfall + provisioning + profile).
4. `adaptive_vectorization.py` — waterfall APPLY: persisted level state, append-only lossless history, build
   worklist; guarded; stale usage demotes losslessly.
5. `cloud_provisioning.py` v0.2.0 — + `vectorization_waterfall_plan/apply` MCP meta-tools; registered in `.mcp.json`
   as the `cloud-provisioning` server (the "MCP or key-based, set-it-up-yourself after billing" surface).
6. `primitive_attribute_plan.py` — the uncapped computed column space (≥500 floor ratcheted; 1,152 description
   views; 18 model slots read live from the zoo; 18 hash/LSH profiles; 18 trainable lexical families).

The closed loop these create: **every MCP/agent-tool request → hash-chained usage ledger + request ledger → learned
non-destructive ranking bias AND waterfall promotions → richer vectors only where usage earns them → better
retrieval for the environments actually asking.** Cost tracks usage, not corpus size — which is what makes the
uncapped logical plan affordable at 100M+.

## 4. THE PROMPT — pass this to Claude Fable 5

```text
You are Claude Fable 5 working in the ai_harness_and_knowledge_facts_and_logic_website_sharing monorepo
(read _repos/shared-backend-components/docs/BIBLE.md, root CLAUDE.md, and
_repos/shared-backend-components/docs/PRIMITIVE-LAB-100M-ALIGNMENT.md FIRST — that alignment doc is the
context for this prompt and maps every idea below to what already exists; wrap/extend, NEVER rebuild).

MISSION: make this repo fully aligned with the 100M+-primitive program — every codeblock, primitive, and
GROUP of primitives fully working, searchable, findable, and efficiently semantically linked — while
preserving every repo law (candidate/truth boundary, multi-path zoos, computed-not-typed counts, lossless
distillation, warrants, self-tests registered in flywheel_proof_modules.py).

OPERATING RULES
- Design for 100M+ primitives and beyond. Never argue scale down; never suggest fewer attributes, features,
  or search functions. The LOGICAL plan is uncapped (primitive_attribute_plan.py computes it; >=500
  attributes+descriptors per primitive is a ratcheted floor); PHYSICAL materialization is usage-earned via
  adaptive_vectorization.py (L0 universal -> promotions from the hash-chained primitive_usage_ledger).
- Every capability ships BOTH surfaces: the flexible MCP tool (capability_retrieval_mcp_server.py +
  environment_request_learning.py, opt-in OH_MCP_ADAPTIVE_LEARNING=1) and the deterministic developer/agent
  tool (capability_agent_tool.py, allowlisted + key-gatable + receipt-backed). New actions = registry rows.
- Every decision point is a ZOO row behind a selector (pipeline_path_graph.STAGE_OPTIONS, embedder_zoo,
  rank_fusion_zoo, path_router_zoo, LEXICAL_SIGNAL_FAMILIES, HASH_LSH_PROFILES): add rows, race them on
  receipts, keep losers as labelled fallbacks. graph_flexibility.py must stay green.
- Counts are COMPUTED, never typed. Any number describing the repo comes from running a module.
- Everything generated is candidate=true, serves_truth=false until source review + executed proof + gates.

WORKSTREAMS (in order; one proof-backed increment per cycle; run PYTHONPATH=. python3 <module> --self-test
after every change and register new modules in flywheel_proof_modules.py):
1. SEARCH/LINKING COMPLETENESS: every primitive corpus family (verified_factory cards, edge cards, drafts,
   minted packs) must be reachable through primitive_search_federation with L0 vectors + lexical index at
   minimum; run primitive_enrichment_coverage.py and drive coverage to 1.0 with gap tickets for the rest.
2. MULTI-SIGNAL LINKING: implement the 18 LEXICAL_SIGNAL_FAMILIES (exact keyword, keyword counts, tf-idf,
   BM25, char/word n-grams, Levenshtein/Damerau edit distance, fuzzy token-set, soundex/metaphone,
   vowel/consonant ratio, letter-frequency profile, word-length profile, stopword density, subword overlap,
   acronym expansion) as pipeline_path_graph search/rerank rows with TRAINABLE weights
   (linker_scoring_zoo.train_weights on usage-ledger training pairs); race vs dense/fused lanes; receipts.
3. HASH/LSH LAYER: materialize the 18 HASH_LSH_PROFILES (SimHash/MinHash-banded/angular 64-512 bit, wide AND
   slim cross-polytope, p-stable, winner-take-all) as store columns for the waterfall's promoted tiers;
   benchmark recall/bucket-occupancy/candidate-count/latency per profile before defaulting any.
4. GROUP-OF-PRIMITIVES LINKING: composite retrieval (route/recipe cards as first-class searchable objects
   with their own edges, embeddings, usage telemetry) so groups link to groups; compose_route receipts feed
   the same usage ledger.
5. DESCRIPTION/EMBEDDING FAN-OUT: generate the facets x styles x audiences description views and multi-model
   embeddings FOR PROMOTED CARDS ONLY (the waterfall worklist -> build_primitive_embeddings /
   primitive_multi_model_store); attribute observations use the versioned observation model (state=
   known/unknown/conflicted; five models may disagree without overwriting; agreement is a feature, never
   ground truth).
6. PRIMITIVEML-KAGGLE: stand up the 6-arm benchmark (A LLM / B tools / C retrieval / D retrieval+linker /
   E AutoML / F oracle) per the alignment doc SS2 - TML-Bench 4-competition offline lane first, then the
   post-cutoff live competition; hidden holdout, token+time ceilings, normalized quality Q, full token
   ledger, leakage provenance rules; every ML stage (load/profile/split/preprocess/features/model/tune/
   calibrate/ensemble/submit) gets MULTIPLE raceable path rows.
7. SELF-SERVICE SCALE: after the owner enables billing, drive cloud_provisioning (MCP server
   cloud-provisioning or the key-based CLI/agent tool) preflight -> apply; migrate stores per
   architecture/storage_tier_policy.json (config-only swap); keep idle cost ~$0 (storage-first serverless).

NON-NEGOTIABLES: no destructive overwrites (append-only ledgers/history; demotion never deletes); no raw
source bodies in primitive rows; no secrets in receipts; insurance verticals off-limits; report generated /
staged / load-ready / promoted counts SEPARATELY; never quote projections as measured savings (honest ledger:
docs/REAL_SAVINGS_NUMBERS.md). When a favorable number appears, try to refute it before reporting it.
```

## 5. Pointers

- Serving pair: `scripts/capability_retrieval_mcp_server.py` (flexible/learning) + `scripts/capability_agent_tool.py`
  (deterministic) — both delegate to the same engines.
- Spend policy: `scripts/adaptive_vectorization.py` (+ MCP meta-tools in `scripts/cloud_provisioning.py`).
- Column space: `scripts/primitive_attribute_plan.py` (uncapped, computed, floor-ratcheted).
- Learning state: `data/dev-intel/environment_request_learning/` · usage signals:
  `data/dev-intel/primitive_usage_ledger/events.jsonl` (hash-chained) · levels:
  `data/dev-intel/adaptive_vectorization/`.
- Honest savings ledger (do not contradict): `docs/REAL_SAVINGS_NUMBERS.md`,
  `docs/strategy/primitive-system-end-to-end-briefing.md` §4.
