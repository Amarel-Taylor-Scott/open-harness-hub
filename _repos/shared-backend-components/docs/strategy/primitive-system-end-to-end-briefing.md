# Deterministic Primitive Registry — end-to-end briefing (for external review)

> Self-contained briefing of a working system, written for an outside LLM/reviewer with **no repo access**.
> Honest state as of 2026-07-08: real numbers, real gaps, no placeholders. Everything generated is
> `candidate=true, serves_truth=false` until it passes promotion gates. Numbers are measured, not projected.

## 0. Thesis in one paragraph

We are building a **database-backed registry + supply-chain of reusable, typed, deterministic AI-pipeline
primitives**. The bet: the repeatable 70–90% of software/data work can be compiled into **verified deterministic
primitives** whose **bodies are reused at 0 model tokens** (instead of the model regenerating them) and whose
**retrieval is a deterministic index scan (0 model tokens)**. **We are honest that this is NOT "zero LLM": the model
is still spent — today — on understanding the request, SELECTING and ORDERING the primitives, and engineering the
glue/layout between them (the orchestration), plus any genuine capability gap.** The saving is the eliminated
*code regeneration* + *cached compiled routes on repeats*, not a claim that the LLM disappears. Shrinking that
residual orchestration spend (making selection/ordering/glue deterministic) is the central open frontier (§4, §7).
The governing law is **"the LLM PROPOSES, the deterministic system DISPOSES"**: models draft candidates, interrogate
sources, and orchestrate; deterministic gates validate, execute, dedupe, benchmark, and promote — and increasingly
retrieve + compose. Nothing becomes served truth by assertion. The moat is **governance/provenance + evaluated
lift**, not raw count.

The canonical unit is the **seven-primitive model**: Input · Knowledge Corpus · If-Statement · Action · Loop ·
Stop/End · Output. A "primitive" is a typed capability with a contract, schema, tests, verifier, provenance,
failure modes, permissions, cost profile, benchmark evidence, and lifecycle stage — not just a function.

## 1. The pipeline, start to finish (what is actually implemented)

```
source discovery → acquire/scrape → digest/normalize → interrogate/question → decompose
→ generate candidates → dedupe/canonicalize → security-gate → executor-synthesize + fixture-prove
→ benchmark → promote (5-stage lifecycle) → serve (retrieve→compile→deterministic-exec→LLM-only-for-gaps)
→ telemetry → gaps feed back into discovery
```

Every stage exists in code with a mutation-gated `--self-test`; the honest weak points are called out in §7.

### 1a. Source discovery
Governed source families (news, apps, systems, Kaggle notebooks, blog/Medium, system-design writeups,
textbooks/courses, Google-Scholar/citation clusters, papers, repos, discussions, websites, standards, API specs).
Each source gets a **trust tier (T0 official-standard … T4 unknown / T5 quarantine)** and a source policy. Discovery
is **gap-driven**: a benchmark's misses (algorithm/competitive-programming/Kaggle/SWE/agentic gaps) become
source-acquisition targets via a `gap_queue`.

### 1b. Acquire / scrape (driver-neutral)
A **driver-neutral browser + tab-control harness**: a backend **zoo** (stdlib Chrome-DevTools-Protocol over the
installed Chrome — zero pip deps; Playwright; nodriver; + browser-use / browser-harness / PinchTab / Lightpanda /
chrome-extension as documented adapter seams). A stable **command plane** (`session/tab/observe/act/verify`) where
**every action emits an evidence receipt** (before/after DOM state-hash, side-effect level, requires-confirmation,
verifier-result). **Read-only by default**; never bypasses robots/CAPTCHA/paywall/auth; per-domain throttle;
secret redaction; provenance hash; raw bodies are never stored (digests + bounded text + extracted structured units
only). We also probed **13 tool categories** live (6 working: raw-HTTP, CDP, Playwright, tiny-CLI dump-dom, LLM
endpoints, API-first discovery) and published a capability matrix — "Playwright is one adapter, not the strategy."
Plus a continuous offline scrape loop, a GitHub **report layer** (repo-inventory / primitive-mining / test-fixture →
candidate primitives), and an OpenAPI→interface-primitive importer.

### 1c. Digest / normalize
Artifacts → a canonical parsed-document shape (page/section/table/code-block/endpoint/example/notebook-cell). HTML
via stdlib; PDF/OCR engines are cataloged but partly unavailable in-env (honest gap). Everything carries a
source hash + evidence spans so a downstream candidate links back to the exact source.

### 1d. Interrogate / question
A **question engine** treats questions as first-class rows: a persistent **deconstruction-plane database** (18
planes, 14 analysis layers, 343 dimensions, **955 questions**, plane↔question edges, a completeness rubric) plus a
200+-question bank per source. Multi-pass interrogation (inventory → decomposition → typing → variants → tests →
safety → dedupe → promotion-recommendation) with specialized interrogators (API / schema / workflow / data-science /
browser / security / benchmark / standards). **Honest gap: questions are persisted but currently *inert*** — they
don't yet drive recrawl; re-mining is gap-queue/CDC-driven.

### 1e. Decompose
Deterministic rubric: nouns→data/object primitives, verbs→action primitives, tables→crosswalk/lookup, standards→
parser/validator/mapper, endpoints→interface wrappers, forms→browser primitives, errors→error-normalizers, rules→
policy gates, metrics→benchmark primitives, workflows→process molecules. Emits component-breakdowns → rebuild-plans →
primitive-candidates.

### 1f. Increase variety / enumerate all variations
"All possible primitives" is treated as a **coverage search**, not a static list. Levers:
- **Multi-axis atlas**: persona × industry × geography × standard × system × datatype × process-stage × action, with
  addressable facet columns (the atlas is a data seam — a new role-matrix YAML adds columns with no code change).
- **Standards factory**: 33 standards → 173 candidate specs (X12/FHIR/ACORD/NCPDP/ISO-20022/HL7 field transforms).
- **Process-stage factory**: research→load→ETL→preprocess→train→test→serve stages → ProcessStep primitives.
- **Grid remixer**: a ~77.4-billion-point coprime-strided grid; 200K minted at 0% placeholder in one run.
- **The Hy3 overnight flywheel** (see §3): concurrent free-LLM minting across 9 lanes / 8 keys / 8 job types.
Coverage gaps (covered vs candidate vs evidence-but-no-primitive vs high-value-no-coverage) become new research tasks.

### 1g. Generate candidates
The flywheel mints substantial primitives (avg body ~14.7K chars at max-output, up from ~348-char one-liners before
we fixed a `max_tokens=4000` truncation bug). Idea-minter produced 100K candidates at ~2.4% placeholder. All
candidate-only. A deterministic **usefulness gate** routes (non-destructively — upgrade over reject) generic-scaffold
/ mechanism-free cards away from truth.

### 1h. Dedupe / canonicalize
MinHash-LSH blocking, behavior signatures, exact + normalized-AST hashes. IDs come from **one authority**
(`canonical_id(prefix, *parts)` = `prefix-sha256[:16]` over canonical bytes) — never truncation-only, so daily
batches don't collapse on merge. Version lives in `schema_version` metadata, never in a name/id.

### 1i. Security-gate (generated code is never trusted)
Every generated body is scanned for `eval/exec/compile/__import__/network/filesystem/subprocess` etc.: verdict
`pass | fail | quarantine`. Quarantine ⇒ never auto-promote, human review. The flywheel **never executes** generated
code. (Verdict distribution and pass-rate feed the benchmark taxonomy.)

### 1j. Executor-synthesize + fixture-prove (the promotion-loop closer — newest)
This was the missing wire: factories mint `needs_executor=true` **specs**, but nothing turned a spec into a
**runnable** executor. Now: **Hy3 drafts {executor body + golden fixtures}** → security gate → **isolated subprocess
sandbox** executes the body against positive/negative fixtures → determinism check (run twice, byte-identical) →
promote `candidate→validated→certified` **only if every gate passes**. A dangerous body is quarantined and never
executed; a wrong-output body passes security but fails fixtures and stays candidate; a stochastic (D4) spec cannot
auto-promote. This is what turns "searchable card" into "executable, 0-token-reuse, promotion-proven primitive."
**Live-proven (2026-07-08):** a real Hy3-driven run over 3 specs (US-ZIP parse, currency normalize, Luhn checksum)
promoted **3/3 to certified**, all deterministic, fixtures 4/4·4/4·3/3 — **2 of 3 executors drafted by Hy3 itself**
(`tencent/hy3:free`), the third by the glm-5.2 fallback lane. No placeholders.

### 1k. Benchmark
A 7-metric taxonomy (incl. **break-even N\***: how many reuses until a compiled primitive beats regeneration),
realistic multi-prompt **session benchmarks** (deterministic chars/4 token proxy over app/warehouse/agent/regulated/
platform/ML-lifecycle/large-org buildouts, base-registry vs expanded-corpus), and an **orchestrated-lane A/B**
(below).

### 1l. Promote (5-stage lifecycle)
`candidate → validated → certified → production → (deprecated | quarantined)` with **receipt-gated** transitions:
candidate→validated needs `schema_valid + self_test_pass + verifier`; validated→certified needs `security=pass +
deterministic_replay + benchmark_result`; certified→production needs `provenance + run_proof + reviewer/approval`.
Only **D0-pure / D1-seeded / D2-bounded** determinism budgets are truth-eligible.

### 1m. Serve (this is the one stage that is fully mature)
Retrieve capability from the registry → **compile a route bundle** → execute verified deterministic primitives →
call the model **only** for a genuine missing edge. A compiled-route cache serves repeats at **0 model calls**.
**Honest caveat (see §4):** the *retrieval* and the *execution of verified bodies* are 0-token, but **selecting
which primitives and in what ORDER, and writing the glue/layout, still costs LLM tokens today** unless the pieces'
typed edges align exactly (then the deterministic `compose_route` composer wires them at 0-token — but across
independently-minted cards exact edge joins are ~0 today, the "canonical-edge-vocabulary" gap). The compiled-route
cache only zeroes the orchestration on **repeats** of a task-shape it has already compiled.

## 2. Making primitives searchable (the retrieval stack)

- **Corpus (honest denominator): 112,731 distinct searchable/governed cards** = 34,289 verified-factory + 78,442
  edge cards (disjoint). (The repo holds ≈1.17M primitive-bearing records, but ~90% is an un-promoted synthetic seed
  corpus — see §5.)
- **Multi-index (79 columns, 4 key kinds):** 6 textual (semantic + small/large **LSH** blocking + exact) + 8
  categorical (typed-edge term keys = composition joins) + 47+ facets auto-derived from `vocabularies/*-role-matrix`.
- **Embeddings persisted for all 112K** (model2vec potion-8M, dim 256, ~2.3s full rebuild). On a labelled paraphrase
  set: **fastembed BGE-small & MiniLM & Ollama-nomic all reach nDCG 1.00**; model2vec 0.86; a from-scratch TF-IDF+SVD
  0.63; crc32-proxy 0.22. **3-register descriptions** (plain / technical / semantic) each embedded.
- **Retrieval as a graph ("zoo of zoos"):** 8 ordered stages (analyze · preprocess · expand · secondary(LLM) ·
  search · fuse · rerank · compose), 36 interchangeable options → **76,800 runnable paths**; **CombMNZ** wins the
  fuse stage; a **stored-matrix lane** serves semantic search **91× faster** at 112K with identical top-10.
- **Storage reality:** cards + inverted index live in **JSONL** today (real, df-capped, O(candidates), ~120MB).
  pgvector-HNSW / faiss / ES-BM25 / serve-time MinHash-LSH are **drop-in config swaps** behind the same calls (built
  locally now; local→cloud is config-only).
- **How an agent actually queries it:** through an MCP tool surface (`primitive_search` / `capability_compose` /
  `find_reuse`) or the in-process `intent_query` API. The **retrieval compute is 0 model tokens** (deterministic
  scan), but — being honest — the **calling LLM still spends tokens forming the query string and reading the ranked
  results back**, which is part of the step-1/step-3 residual in §4. Results come back with typed input/output edges
  so a composer *can* wire them deterministically when the edges align (today they usually don't — §1m).

## 3. Fully leveraging free LLMs (Hy3 flywheel)

An overnight **concurrent** flywheel drafts candidates with **free** endpoints at $0: **Tencent Hy3**
(`tencent/hy3:free`, 262,144-token max output) first, then nemotron/qwen3-coder/gpt-oss/gemma-4/glm-5.2/kimi across
**9 lanes / 3 providers**, with **8 rotating API keys** (separate rate pools), per-lane exponential-backoff cooldown,
and **max-output-first** decoding. **8 job types**: composite-primitive · spec-executor · doc-digest · variation ·
critique-improve (→ code, security-gated) and primitive-labeling · question-generation · interrogate (→ metadata).
Every code body is security-gated; all output stays candidate-only. The same Hy3 lane order now drives the
executor-synthesizer (§1j).

## 4. Reducing token spend — how a query is answered, and where the tokens actually go

This section is deliberately explicit because it is the crux and the easiest thing to overclaim. A request flows
through five steps; here is the **honest per-step model-token cost today**:

| Step | Model-token cost | Why |
|---|---|---|
| **1. Understand the request** (NL task → intent) | **LLM tokens** — *unless* our deterministic `request_intake` + `session_context` normalize it first (0-token, built, but only in-loop for our own agents) | reading/normalizing natural language |
| **2. Search the primitive DB** (intent → candidate primitives) | **0 model tokens** | retrieval is a **deterministic index scan** — lexical (BM25-style inverted index) + dense (stored embedding matmul) + fusion (CombMNZ) + rerank. The graph's one optional `secondary(LLM)` expansion stage is **off by default**. Returns ranked candidates with typed edges. |
| **3. Select + ORDER + engineer the glue** (the LAYOUT) | **LLM tokens — this is the real residual spend** | deciding *which* candidates, in *what order*, and writing the glue between them. The deterministic edge-typed composer (`compose_route` → `compile_exact_edge_route`) does this at **0-token ONLY when the pieces' typed I/O edges align exactly**; across independently-minted cards exact edge joins are **~0 today** (the *canonical-edge-vocabulary* gap), so in practice the **LLM still plans the order and writes the glue**. |
| **4. Execute the verified primitives** | **0 model tokens** | deterministic code runs; no model in the path |
| **5. Fill a genuine capability gap** | **LLM tokens** | the uncertain 10–30% |
| **Replay the SAME task-shape later** | **0 model calls** | the compiled-route cache serves repeats free |

**So "~0 tokens" applies to search + reuse-of-verified-bodies + cached-route replay — NOT to the orchestration.**
We are, honestly, **still spending LLM tokens to understand, select, order, and lay out the primitives** (steps 1,
3, 5). The savings come from three real levers: (a) the model no longer **regenerates the verified primitive bodies**
— the large code chunks are injected at 0 tokens; (b) **compiled-route caching** zeroes steps 1–3 on any repeat of a
task-shape; (c) **deterministic intake + retrieval** zero steps 1–2 when our own agents are in the loop. The residual
is the *plan + order + glue*, and **making that deterministic for arbitrary tasks is the hard open frontier** — a
canonical typed-edge vocabulary so `compose_route` fires more often, a cheap learned planner/router, and wider
compiled-route reuse (§7, §8).

**What we've measured (and how to read it against the accounting above):**
- **Proxy-token session benchmarks: 4.96–7.54×** reduction (deterministic chars/4 proxy, base vs expanded corpus).
- **Orchestrated-lane A/B (our canonical measure):** *bare* = the LLM writes all code; *orchestrated* = the LLM
  plans A→B→C + glue and verified primitive code is injected at **0 tokens**; executed + cross-tested on real cloud
  lanes, quality-weighted. Glue-dominated turns are the minting targets.
- **Consumption proof:** enriched cards rank in the **top-5 for 91%** of intents among 3,000 distractors;
  cross-session reach **6.6×** vs placeholder embeddings.

**The honest gap (the single most important caveat):** on a small **real-executed** sample (n=16, glm-5.2 cloud),
the measured *generation-saved fraction* was **0.0** — the **proxy** shows large savings but a **real-log replay +
capped-decode A/B** has **not yet reproduced** them. The accounting above explains *why this is plausible*: the true
net saving is **(eliminated body-regeneration) − (residual orchestration: understand + order + glue + gap)**. If the
plan+glue the model still writes (step 3) costs about as much as the code-regeneration it replaced, net savings
collapse toward 0 — which is exactly the risk the n=16 result flags. So a credible measurement must **count steps 1,
3, and 5 as the cost side** and only credit step 4's eliminated regeneration, per real token ledgers (not the
chars/4 proxy). Closing this is priority #1; the **executor synthesizer (§1j) is one unblocker** (it yields
genuinely 0-token-reuse bodies so step-4 credit is real), but the **decisive lever is shrinking step 3** — making
selection/ordering/glue deterministic so the residual orchestration cost drops.

## 5. The honest numbers (a funnel, not a headline)

| Layer | Count | Meaning |
|---|---|---|
| Total generated records | ≈**1,170,000** | mostly a 1M **synthetic seed** corpus — un-promoted, never indexed |
| Searchable / governed | **112,731** | the real working corpus (verified-factory + edge, disjoint) |
| Measured retrieval **lift** | ~**72,576** | +0.24 over base hit-rate 0.76 (k=5) — candidate *admission* evidence |
| Enriched & consumption-proven | **3,195** store / 195 on-file | enriched beats plain; +0.46 cross-session reach |
| **Executable / oracle-tested WORKING** | **204** | actually runnable → 0-token reuse (this is the number that matters most) |

Per our own **marginal-utility law**, "useful" = *lift-proven*, not count: many skills don't help (external
benchmarks show ~80% zero-lift), so every primitive must A/B-prove lift or be deprecated. The moat is
evaluated/typed/lean, not the 1.17M or even the 112K.

## 6. Governance / laws (non-negotiable invariants)

Candidate/truth boundary (born candidate) · security gate on all generated code (never executed by the factory) ·
**lossless distillation** (raw + intermediates + rejected candidates + lineage always preserved; omitted ≠ deleted)
· **verify-the-verifier** (every checker ships a mutation gate + a determinism gate + a metric ratchet) · deterministic
globally-unique naming (one `canonical_id` data authority; a `py_<kind>__<file>__<scope>__<name>` code scheme) ·
**no-magic-values** (repo-state numbers are computed, never typed) · **reuse-first** (a reinvention guard + code-graph
audit before building anything — "this already exists, don't rebuild it" is the highest-ROI decision).

## 7. Honest gaps / open questions (from three read-only reuse audits)

The substrate is largely built; the gaps are **execution wiring**, not foundations. Of 12 discovery-factory stages,
**11 are partial and only *serving* is a clean "exists."** Ranked genuine gaps:
1. **The orchestration residual + real-executed savings proof** — retrieval/reuse are 0-token, but selection/
   ordering/glue still cost LLM tokens (§4); proxy savings ≠ real savings until that residual is counted and shrunk
   (deterministic composition when typed edges align; the canonical-edge-vocabulary gap is the blocker). *Highest priority.*
2. **Executor + golden-fixture synthesis at scale** — just built (§1j); needs a large live Hy3 run + yield/quality data.
3. **Durable-queue DAG factory spine** — stages run largely in-process; not yet resumable/parallel/fault-tolerant.
4. **Closing the question/coverage loop** — questions are inert; no covered/missing coverage-grid *enumerator*.
5. **Multi-role extraction ensemble** — discovery uses one decomposer role, not a routed classifier/critic/deduper set.
6. **Real capture/parse engines** — browser HAR/network/accessibility are stubbed; Postman/GraphQL importers and a
   no-pip HTML/PDF→markdown extractor are missing.
7. **New source surfaces** — process-mining from event logs, support-ticket mining, API schema-diff watchers.
Plus formalization gaps (anti-primitive/negative-knowledge store, expiring warranties, tool-rightsizer,
counterfactual-repair) — several in progress.

## 8. What we'd like external advice on

1. **Shrinking the residual orchestration spend — and proving real savings (the crux).** Retrieval and
   verified-body reuse are 0-token, but the model is still spent to **understand, SELECT, ORDER, and glue** the
   primitives (§4). Two linked asks: **(a)** how do we make that *selection/ordering/layout* deterministic for
   arbitrary tasks — a canonical typed-edge/port vocabulary so the `compose_route` composer fires, a cheap learned
   planner/router over the retrieved set, program-synthesis/constraint-solving over typed edges, or wider
   compiled-route caching — so the model plans *less* per request? **(b)** what real-token measurement (session-log
   replay, capped-decode A/B, quality-weighted, break-even N\*) would make a "5–7× reduction" claim credible while
   **counting the orchestration (steps 1/3/5) as a cost**, not just crediting eliminated regeneration?
2. **Scaling searchability** from 112K JSONL to millions: best hybrid of lexical (BM25/SPLADE) + dense ANN
   (HNSW/faiss) + learned-sparse + LSH blocking, and how to keep composition-join (typed-edge) retrieval exact.
3. **Reliable LLM-drafted executor synthesis at scale:** yield, near-duplicate collapse of executors, sandbox safety
   beyond a security scanner + subprocess isolation, and how to pick which specs are worth synthesizing.
4. **Selection / marginal-utility:** how to decide *which* primitives to build so we're mining the negative space
   (where base models are weak) rather than the head of the distribution.
5. **Is the strategy sound?** Governance/provenance moat + lift bar, LLM-proposes/deterministic-disposes, candidate/
   truth boundary — what's the strongest objection, and what would you change?
6. **What are we missing** in the scrape→interrogate→decompose→generate→dedupe→gate→execute→benchmark→promote→search
   loop that a serious external reviewer would flag first?
```
