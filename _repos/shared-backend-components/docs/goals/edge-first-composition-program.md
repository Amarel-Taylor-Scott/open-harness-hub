# Edge-First Composition — Execution Program (make it real)

Owner directive 2026-07-01: fully working infrastructure, demo, examples; millions of primitives;
integrated on all surfaces; templates first-class; tracking/logging; fuzzy matching + semantic/LSH key
blocking; connection-strength LEARNING; LLM-free remixing; explicit deterministic/light/heavy/frontier
tier routing. This document is the cycle-by-cycle backbone: every cycle takes ONE workstream increment,
proves it (`--self-test` registered in `scripts/flywheel_proof_modules.py`), and reports by quality level
(L0–L6). Truth boundary everywhere: `candidate=true / serves_truth=false` until a promotion gate passes.

## Already built — integrate, never rebuild (reinvention guard, verified 2026-07-01)

| Capability | Where it lives |
|---|---|
| Edge cards + search cards (72k+/5k) | edge foundry + `primitive_source_lifecycle` outputs |
| Hybrid match + BLOCKING (profile keys + semantic bucket keys) + fit classes + adapter plans + chain compatibility | `src/teleon/registry/primitive_match.py` |
| Edge-aware service search + reuse cards + outcome memory | `src/teleon/observer/registry_search.py` |
| Graph runtime + route verification | `src/teleon/dag/pipeline_dag.py` + `src/teleon/synthesis/dag_contract.py` |
| Route compile + group collapse + runtime planning | `src/teleon/primitives/groups.py` (`compile_exact_edge_route`, `collapse_route_to_group_card`, `plan_primitive_graph_runtime`) |
| Resource-envelope A/B harness (tokens + context + memory) | `scripts/primitive_lift_benchmark.py` |
| Factory (13k+ accepted/day) + verification loop + lifecycle packaging | `scripts/run_primitive_provider_fleet_loop.py` + `run_primitive_verification_loop.py` + `primitive_source_lifecycle.py` |
| Naming law enabling text-precise primitive surgery | pyprefix + `check_canonical_id_single_source` |

## Workstreams (each line = one or more bounded cycles; sequence within, parallel across)

**W1 — Learning layer (STARTED this cycle).** `src/teleon/registry/composition_affinity.py`: connection
strengths seeded from source-backed group member edges (known-good chains), updated from run receipts and
accepted/dismissed findings; deterministic learning (counts + outcome weighting + recency decay). Next
cycles: wire affinity boost into `primitive_match` scoring and `registry_search` ranking; decay tuning from
longitudinal replays; per-tenant vs global affinity separation.

**W2 — Derivation over population (three rings, families, routes).** Ring 1: precomputed high-value
variants for hot primitives/templates. Ring 2: on-demand deterministic remix at match time (adapter plans —
the strongest form; avoids population explosion). Ring 3: LLM repair proposals, candidate-only, targeted at
the named gap. Variants are never loose duplicates: every one carries parent, tool, reason, contract delta,
proof obligations, receipts — the unit of value is the **family** (base + lineage), and compatibility is
stored as **ROUTES, not booleans** (`compatible_after_remix` + route + proof obligations + receipt history),
so the system learns and proves paths instead of guessing from an ontology. Ranking operates at every level
(primitive · variation · family · slot-fit · route · known chain · composite) with receipts outranking
embeddings, and negative memory (FAILED_WITH_TEMPLATE / CONTRACT_MISMATCH / DISMISSED_BY_HUMAN /
SUPERSEDED_BY_VARIANT …) as first-class suppression. Templates are the population-control mechanism: pick
the template first, and each typed slot (allowed effects/remixes/traits) collapses shape-space. Cycles:
materialization policy + ledger; family/route record emitters in the factory; variant GC (losers sink to
lineage, never deleted); sibling/child naming under the canonical-id law (no `@N` — external-brief ids are
adapted on intake).

**W3 — Tier routing policy.** One policy table single-sourcing WHAT runs at WHICH tier: deterministic
(match/adapt/verify/execute/receipts) · light (query expansion, rerank, card summaries) · heavy (route
synthesis when no template fits, contract drafting) · frontier/open-weight (novel decomposition,
promotion-evidence review). Fit classes from `primitive_match` are the routing signal:
`exact/deterministic_edit` never call a model; `nondeterministic_edit` calls the cheapest tier that closes
the gap; `incompatible` falls to synthesis. Cycles: policy JSON in `architecture/` + router + gate.

**W4 — Templates first-class.** Template records above primitives in retrieval; template extraction from
group cards + successful routes (every N-times-successful route auto-drafts a template candidate); template
coverage per task family measured against the 10k-task corpus.

**W5 — Scale to millions (factory).** Raise daily shard targets 20k→50k; add ingestion source families
(websites, process docs, textbooks, workflow exports) to the decomposition foundries; the ingestion-quality
corpus (benchmark plan §3.7) gates every new family — contract truthfulness sampled BEFORE volume.
Observed-effects sandbox instrumentation joins verification (effects recorded, never asserted).

**W6 — Surface integration + demo.** Registry browser: affinity-ranked results + fit-class chips + adapter
plans; Observer IDE: "compose from primitives" path emitting few-token route plans; one END-TO-END demo —
prompt → tool-call search → route plan JSON → deterministic wiring → execution receipts — replayable in the
Benchmark Lab examples. Acceptance: 0 console errors under the showcase; honest disabled states.

**W7 — Benchmark program.** Execute `docs/benchmarks/edge-first-composition-benchmark-plan.md` M1→M4;
whitepaper v1.0 evidence appendix from the verified research pass + measured phases.

**W8 — Path-policy plane (the pipeline measures ITSELF).** Every stage of the composition pipeline —
search, tool-calling shape, LLM preprocessing, mutation, contract evolution, linking — is itself a
cost-ordered ladder with receipts, learned exactly like primitives: a meta-ledger tracks the performance of
every path combination our own graph executions use, continuously descending to the cheapest path that
still passes, with backup paths standing by and **redundant execution (2–3 paths at once) for agreement
checking** when stakes or uncertainty warrant. Reuse, don't rebuild: `src/teleon/experiments/`
(`parallel_paths`, `path_costing`, `path_comparator`, `path_promotion`, `path_rollback`) is the engine;
the capability-ladder descent doctrine is the law. Cycles: pipeline-stage ladder definitions; meta-receipt
ledger over composition runs; agreement-check policy (when to fan out, majority/consensus rules); descent
reports (which stages hardened to cheaper rungs this week).

**W9 — Flexible data plane (single source: `architecture/primitive_data_plane.json`).** Shapes are policy,
not accident: staging stays long-format JSONL (lossless raw layer); the operational tier is a normalized
core (primitive/family/variation/route/template/slot/chain/receipt/affinity/negative-memory tables in
Postgres+pgvector) with DENORMALIZED search projections rebuilt from truth (wide search cards: hot
attributes typed, long-tail JSONB); embeddings live LONG (`object_embedding`: one row per embedding column
per primitive — N columns per primitive, per-column method + dimensions, e.g. 128-dim edge vectors beside
768-dim blackbox vectors), with LSH bucket keys derived per column. Affinity boosting is multi-path
(seed-only / live-fold / daily batch snapshot / tenant blend) under W8 receipts, with path-divergence events
recorded when scorers disagree. Cycles: pgvector load plan for the normalized core; multi-column embedding
emitter honoring the manifest; per-column blocking; affinity snapshot batch job; divergence monitoring.

**W10 — Template universe (tens of thousands).** Templates come from four extractors, each a bounded
ingestion family gated by the ingestion-quality corpus: (1) pattern catalogs (Enterprise Integration
Patterns, GoF/POSA, microservices.io, cloud reference architectures — AWS/Azure/GCP publish hundreds each),
(2) workflow-template libraries (n8n's public templates alone are thousands; Airflow DAG galleries, CI
workflow catalogs), (3) decomposition of system-design corpora (system-design-primer scenarios,
architecture-diagram datasets, textbook chapter structures), (4) OUR OWN routes — every N-times-successful
route auto-drafts a template candidate (the compounding source). Licensing posture per family is an owner
gate before ingestion.

**W11 — Combinatorial query foundry (BUILT 2026-07-01; fetch stage pending owner gates).** Deterministic
sampled generation over the 14-dimension query cross-product (`architecture/query_foundry_dimensions.json`
+ `scripts/query_foundry.py`; seed space ~5.7e13 — sampled with reproducible seeds, never enumerated;
blocked dedupe; scope law enforced at generation). Pipeline: sample → gap-screen survivors → governed fetch
(browsing guardrails + W10 licensing gate per source family) → decomposition foundries → primitive/template
candidates → proof/promotion. Cycles: research-queue priority wiring; fetch-batch runner (bounded,
ledgered); decomposition adapters per publication medium; per-family quality sampling BEFORE volume.

**W11 staging ladder (required from batch 002 — batch 001 ran too short a path; lossless-distillation law):**
1. `search_result` — the SERP per query (query_id → ranked URLs+titles), tiny rows; enables per-dimension
   yield analytics that tune foundry weights.
2. `fetch_snapshot` — per fetched URL: content hash, length, fetch time, capped extracted-text excerpt; the
   URL is the durable source handle (re-fetchable), the hash detects drift, the excerpt allows
   RE-EXTRACTION without re-fetch.
3. `extraction_record` — snapshot → cards produced (with evidence spans) AND cards rejected by validation
   (kept + labeled, never vanished).
4. card staging (shards → batch) + `dedupe_cluster` — merged duplicates recorded as cluster members with a
   surviving canonical card, never silently dropped.
5. downstream (existing): review_ticket where risk warrants → object_embedding → index_record → promotion.
Funnel metrics (queries → results → snapshots → cards → survivors) are emitted per batch manifest so every
batch teaches the next one where the rich veins are.

## Lane assignments (throughput plan — model IDs come from the provider planner, never hard-coded here)

Five lanes run in parallel on DISJOINT surfaces (no working-tree collisions); every lane is non-looping
unless a live process + ledger + stop file + fresh output prove otherwise; models NEVER promote — the
deterministic gates are the same for every lane.

| Lane | Workstreams | Entry |
|---|---|---|
| **Claude Code / Fable** | The integrator: W1 affinity wiring into `primitive_match`/`registry_search` (+same-change checks), W3 tier-policy table, W6 surface integration + end-to-end demo, gate repairs, program synthesis | `/goal follow docs/goals/edge-first-composition-program.md` (or the paste-ready prompt in the Fable handoff) |
| **Codex** | Per-package mechanical migrations under gates: pyprefix packages (its designated role), the 71-file canonical-id baseline, W9 pgvector load plans, naming/layout sweeps | point at this doc + `architecture/pyprefix_migration.json` / `canonical_id_migration.json`; full proof gate after each package |
| **GLM lane** (Ollama Cloud) | Highest-volume L1→L2 candidate generation (proven ~7k accepted/day), source triage, contract review; `./loop` stall-breaker | `plan_primitive_provider_fleet.py --target-profile 20k --scale N` → `run_primitive_provider_fleet_loop.py … --max-cycles N` |
| **Kimi lane** (Ollama Cloud) | Long contract expansion, edge-case enumeration, **proof-obligation fixtures for W2 routes** (intent-fixtures are the compounding asset), code critique in the review board | same fleet loop; `./build run --harness opencode` for coding passes |
| **Gemma 4 Coder lane** | Compact candidate writing (cheap batch), W11 decomposition passes over fetched documents per publication medium, benchmark execution arms | fleet loop + `primitive_lift_benchmark` tier arms |

Verification (`run_primitive_verification_loop.py --max-ticks N`) and lifecycle packaging
(`primitive_source_lifecycle.py --limit N`) run after every generation wave, whatever lane produced it.
Throughput scales on three knobs: daily shard target (800 → thousands), fleet `--scale`, and lane count —
quality is held by the unchanged gates, and per-lane acceptance rates land in the batch ledgers so the
path-policy plane (W8) learns which lane is cheapest per work type.

**W12 — Benchmark-adapter plane (grow via source families + prove via existing benchmarks).** Each external
benchmark becomes an ADAPTER: source → BenchmarkTask + PrimitiveDemand → run under arms A0–A8 (A0 reference ·
A1 bare agent · A2 repo-search agent · A3 observer review-only · A4 template-fill · A5 CandidateBundle+PlanDelta
· A6 deterministic remix repair · A7 LLM micro-repair · A8 source-codegen fallback) → Scorecard (candidate-only
promotion evidence). New record families: BenchmarkSource, BenchmarkTask, PrimitiveDemand, RouteCandidate,
RoutePortfolio, RouteReceipt, Scorecard, PromotionEvidence. P0 adapters (each doubles as a primitive FACTORY,
not just an eval): OpenAPI · AsyncAPI · BFCL · SWE-bench(Verified) · DocILE · MLE-bench(Kaggle) · BigCodeBench ·
GitHub Actions · n8n workflows · Kubernetes/Terraform · OpenML · Inspect Evals. P1: ToolBench/API-Bank/
ToolSandbox, LiveCodeBench/EvalPlus/CRUXEval/Terminal-Bench, WebArena/AppWorld/τ-bench/GAIA/AgentBench,
DSBench/DrivenData/Codabench, BEIR/HELM/lm-eval-harness/OpenCompass. Metrics beyond tokens: Primitive
Invocation Rate + Group Reuse Rate (generalizing RepoExec's Dependency-Invocation-Rate — does the agent CALL
existing capability or duplicate it), Token Compression Ratio, Proof-Passing Route Rate, source-escalation
rate. Owner gates: Kaggle/benchmark licensing per source; which 3 adapters first. Governance: store source
refs + derived summaries, never bulk copyrighted text.

**W13 — Compiled-AI framing (prior art: XY.AI Labs "Compiled AI", DSPy, LLM+P).** Borrow the language + the
economics, sharpen the unit: their compiled artifact is CODE, ours is the **PlanLock** (probabilistic work at
compile time → deterministic execution at runtime → validation gates between; zero runtime model calls on the
hot path). Their reported numbers frame our token-amortization metric — break-even vs runtime inference, N× at
volume (cite as prior art; our own numbers measured separately). Compile-time/runtime split + a security gate
(prompt-injection + static-safety checks on generated business logic) become explicit W13 stages.

**W14 — Primitive manifest standard ("OpenAPI for everything").** OpenAPI proves the thesis for HTTP; the gap
is no universal equivalent for packages/functions/services/CLIs/workers/jobs/IaC/pipelines. Define a portable,
publishable manifest (`primitives.jsonl` / `/.well-known/ai-primitives.json` — an llms.txt analog but PROOFABLE)
any repo/package emits, plus an emitter from our registry. Distribution wedge: every coding agent
(Cursor/Copilot/Claude Code/MCP clients) has the same over-reading problem; the manifest is the layer
*underneath* them.

**Card-contract HARDENING (safety-critical — both briefs + Node-RED/MCP research).** Input/output edges are NOT
enough. A card MUST also carry effects, errors, auth, state, **privacy boundary**, idempotency, and proof
status as FIRST-CLASS fields — the Node-RED study found 55% of nodes had information flows the spec didn't
declare, and MCP tool-poisoning shows undeclared behavior is a supply-chain risk; a card that hides a
`network_write`/`stores_PII`/`non-idempotent` effect is worse than no card. Cards also need a **minimal tested
EXAMPLE** (the API-doc RAG study: examples contribute more lift than descriptions/param-lists, +83–220% on
uncommon libraries). The card schema (W9 emitters) adopts these fields; the effects field is verified by the
observed sandbox (W5), never asserted.

**Standing rules:** bounded runs only; ledger + manifest per cycle; focused gates for what changed; report
files/checks/rows-by-level/blockers/next-gate. `aidevexplorer` stays a legacy namespace (naming registry).
Multiple doctrines coexist deliberately (population + derivation + repair + path-policy); receipts — not
preference — decide which dominates per situation, and the monitoring plane exists precisely to watch that
balance over time.

## Primitive-kind family catalog (the KINDS the factory draws from — owner expansion 2026-07-01)

Single source: `catalog/knowledge-packs/data/aidevexplorer-primitive-kind-families/families.jsonl`
(generator `scripts/generate_aidevexplorer_primitive_kind_family_catalog.py`; gate
`check_aidevexplorer_primitive_kind_family_catalog`, registered in the proof suite). A primitive is a
reusable CONTRACT; a runtime shape is how it is exposed. 60 typed kinds so the factory and W10 template
extractors emit diverse families, not one flat table:

- **Runtime shapes** (already present): api.endpoint · service.group (microservice) · webhook.handler ·
  queue.consumer/producer · cron.job · workflow.step/group · cli.command · shell.script · container/kubernetes
  job · kubernetes.controller · terraform.module · github.action · db.migration · sql.view/proc · etl/elt ·
  ui.component/route · dashboard · rag.pipeline · vector.indexer · llm.tool · policy/auth/rate-limit middleware ·
  sdk.client · mock.server · contract.test · test.fixture · runbook · integration.connector.
- **Algorithm / function** (added 2026-07-01 — mine PUBLIC source-backed contracts only: Google OR-Tools/ScaNN,
  Meta FAISS, TheAlgorithms, RapidFuzz, NetworkX, scikit-learn; extract contract+source-ref, never copy code;
  no private Google/Meta/OpenAI internals): algorithm.sort · algorithm.graph · algorithm.optimization ·
  algorithm.fuzzy_match · algorithm.near_duplicate · algorithm.vector_search · **function.chain** (the value
  unit — the reusable normalize→block→score→decide chain, not the single fn).
- **Tools we build and use** (added 2026-07-01): tool.rapidapi_endpoint · tool.browser_automation (one of many
  escalation combinations — API→browser→CDP→stealth, the descent-climbs doctrine) · tool.web_scraper
  (license/robots-aware, provenance receipt) · tool.search_provider (keyless-first fan-out behind the search
  port, graceful degradation) · tool.query_lattice (keyword multiplication as a SCORED lattice, never a blind
  Cartesian — the W11 foundry's unit).
- **Visualization / media** (added 2026-07-01 — deterministic render/export vs seeded/probabilistic generation):
  viz.chart · viz.graph_network · media.image_processing · media.video_processing (gif/trim/caption/transcode) ·
  package.pypi_scan (API-surface card without copying source) · genai.image_generation · genai.video_generation
  (probabilistic model call wrapped in a DETERMINISTIC envelope + seed/safety/provenance receipts). Deterministic
  media validates by artifact metadata (dimensions/codec/duration/hash/frame-count); generative media validates
  the wrapper + rubric + safety, never "is it pretty".

## The all-paths tenet (owner law 2026-07-01 — support every method, let receipts choose)

A standing project law, not a workstream: for any feature, function, or DEVELOPMENT task, prefer building
**multiple viable paths/graphs** and let the system try, compare, randomly sample, and self-learn which wins
over time — rather than committing to one method up front. This is already the spine of the architecture, and
new work MUST preserve it:

- Every family carries **multiple `runtime_targets` + `adapter_mutators`** (many ways to run/adapt the same
  contract) and, for media/search, multiple candidate renderers/providers.
- **W8 path-policy plane** is the engine: every pipeline stage is a cost-ordered ladder with receipts; redundant
  2–3-path agreement runs when stakes/uncertainty warrant; continuous descent to the cheapest path that still
  passes, backups standing by.
- **Route portfolios** (W2) not single routes; **population + derivation + repair** doctrines coexist; ranking
  and negative memory — not a hardcoded preference — select the winner per situation.
- The monitoring plane watches the balance over time; adding a new method is ADDING A PATH (registry/ladder
  entry), never replacing the incumbent (lossless-distillation law: losers sink to lineage, never deleted).
