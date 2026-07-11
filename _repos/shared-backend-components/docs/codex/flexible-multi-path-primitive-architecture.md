# The Flexible Multi-Path Primitive Architecture

Last updated: 2026-07-03. Why this system commits to NO single architecture, pipeline, model, prompt, scraper, or
search method — and instead builds a portfolio of paths at every step so that **data, metrics, and receipts choose
the most efficient path (or paths) for each situation.** Companion to `docs/OPERATIONS-BIBLE.md`,
`docs/handoff/parallel-paths-and-path-tracking-manual.md`, and `docs/codex/benchmark-solver-primitives-and-slm-uplift.md`.

> **HONESTY BANNER (adversarial red-team 2026-07-03).** Sections 1–6 describe the DESIGN. A 5-agent red-team measured
> the runtime and found much of it is still aspirational: the live search is a ~13s linear token-overlap scan (no ANN
> index, blocking keys don't prune), the "named multi-embedding profiles" are labels not vectors (one 64-dim lexical
> hash is the only per-primitive vector; the real matcher `primitive_match` + RRF `retrieval.hybrid` exist but are
> UNPLUGGED from the live seam), and **0 of 7.28M rows are `serves_truth=true` — no primitive had ever been proven**
> until the fix below. Read §8 for the claimed-vs-proven scorecard and the ranked wire-up plan. This banner is the
> change-verification correction; do not read §1–6 as "implemented" without checking §8.

---

## 0. The one principle

> Never commit to one way of doing anything. Every step is a PORTFOLIO of interchangeable paths; the engine runs a
> baseline plus challengers; the tracking ledger records which path won, which lost (kept as training negatives),
> and why. Adding a path is a data row, not a rewrite. The invariant everywhere: **compact context at the model
> boundary, proofed deterministic capability at the runtime boundary.**

This is the *non-commitment law*. It is why the system can absorb a new scraper, a new model, a new prompt style, a
new search method, or a new compiler without re-architecting — the new path joins the tournament and either earns its
place on receipts or is demoted to negative memory. The canonical machinery already exists and is reused, never
rebuilt: the parallel-path engine `src.teleon.experiments.parallel_paths.run_parallel` (modes
baseline/candidate/shadow/canary/fallback), the promotion gate `src.teleon.experiments.path_promotion`, and the
append-only tracking ledger `src.teleon.evolution.descent_attempt_store.DescentAttempt`.

The machine-readable catalog of paths-per-step is a real pack:
`catalog/knowledge-packs/data/step-path-portfolios/` (builder `scripts/build_step_path_portfolio_pack.py`, checker
`scripts/check_step_path_portfolio_pack.py`) — every path references a real engine mode and declares when it wins,
how it fails, its escalation order, and the receipt fields it emits.

---

## 1. Multiple paths at EVERY step

Each pipeline step is an ordered escalation ladder (cheapest / most-deterministic first). The system climbs only when
the cheaper path fails its receipt gate — the *escalate-before-unavailable* law. A representative slice:

### Generating seed content — many paths
- **deterministic table→row** (`build_raw_pack_primitive_candidates.py`) — structured MD/TSV packs → verifier rows, zero model tokens.
- **prompt-queue from compact seeds** (`build_prompt_queue_from_seeds.py`) — cluster millions of variation seeds into per-family briefs.
- **catalog intake** (`build_primitive_pipeline_catalog_intake.py`) — owner catalog → deduped family cards.
- **source-adapter extraction** — OpenAPI / MCP / PyPI / Terraform / GitHub Actions / schemas → contract cards.
- **model-drafted candidates** — Fable ultracode lanes, Ollama GLM/Kimi, Gemma 4 — bounded, candidate-only.
- **benchmark-demand extraction** — a benchmark task → the primitive demands it implies.
- **trace-to-workflow mining** — a successful agent/tool trace → a route candidate.
- **negative-memory→gap** — repeated failures mint new primitive demands.

### Scraping / acquisition — a ladder, not one scraper
`cached_snapshot → structured_api → html_fetch_parse → headless_browser → stealth_browser → vision_extraction →
human_review`. Each rung has a receipt gate; the system escalates only on failure and records honest-unavailable only
after the ladder is exhausted (already wired in `src/teleon/hub_freshness.py`).

### Preprocessing — many paths
`profile → validate → normalize → dedupe → quarantine`, each realizable deterministically (rules/schema) OR
hybrid (deterministic core + bounded-LLM fallback on the ambiguous field) OR model-assisted, with format mutators
(json↔parquet, wide↔long, csv↔table) carrying roundtrip proofs.

### Submitting to LLMs — many prompts, personas, lanes
The output contract is single-sourced (`scripts/_config.py:PRIMITIVE_CANDIDATE_OUTPUT_CONTRACT` +
`PRIMITIVE_CANDIDATE_PROMPT_EXAMPLE_ROW`) but the LANE is a portfolio: deterministic (no model), small-local
(Gemma 4 variants), large-cloud (GLM 5.2 / Kimi K2.7-code via Ollama), frontier (Claude Fable). Prompt STYLE is a
path too — sharp-atom vs long-pipeline-group vs chain-decomposition vs template-fill — and personas (writer /
reviewer / decomposer / judge) are model-slot paths. Model-slot selection itself is receipted
(`model_route_receipt` in the benchmark-seeds pack) so the cheapest lane that clears quality wins.

### Search / find / review / compile primitives — many paths
- **Search**: exact edge · type-compatible edge · schema/contract · lexical BM25 · dense vector · hybrid RRF · graph
  route · known-chain · negative-memory-suppress · source-fallback. Search returns a **CandidateBundle**, never one
  overconfident answer.
- **Review/plan**: exact route lookup · template slot-fill · deterministic graph search · contract-diff remix ·
  co-occurrence bundle completion · bounded-LLM PlanDelta · MCTS/evolutionary route search · trace replay · human review.
- **Compile**: deterministic template fill · schema-driven codegen · AST transform · typed graph lowering ·
  grammar-constrained generation · bounded model function · manual approval lock.

**Data chooses.** For a given situation the router asks: *which path solves this with the least source escalation,
least runtime model use, strongest proof, lowest side-effect risk, and best reuse value?* — and the answer is decided
by receipts accumulated over the co-occurrence graph, not by a hardcoded pipeline.

---

## 2. The primitive black box + contract edges (why the LLM never reads everything)

A primitive is a **black box with a compact visible contract.** The model sees WHAT it does, never HOW:

```text
visible input edge  +  visible output edge  +  blackbox behavior (one sentence)
+ effects  +  runtime targets  +  proof status  +  source/evidence status
+ ranking explanation  +  negative-memory warnings
```

That is ~150–300 tokens. The model does **not** read implementation, package source, member edges, dependencies, or
hidden workflow steps unless the route escalates to that depth (the L1→L7 context-depth ladder). Matching happens on
the EDGES and KEYS, not on bodies — so a small model can string a route by reading edge cards, exactly the
composition thesis.

**Nesting-doll architecture.** Capability is layered, each layer hiding the one below behind a single visible edge:

```text
Leaf primitive      one atomic contract  (parse, validate, hash, dedupe)
Primitive group     one visible edge hiding >=3 member edges  (import: parse->validate->normalize->dedupe->receipt)
Route portfolio     a chain of groups; group N's output_edge == group N+1's input_edge
Template            a slot-parameterized family of the above  (Raw{Entity}Batch+{Policy} -> Prepared{Entity}+{Receipt})
PDU                 the packaged/deployable form  (group -> runtime wrapper -> deployment artifact -> marketplace listing)
```

You open a doll only when you need to — the group card answers "can this solve my task?" without exposing its seven
internal member edges. The machine-enforced shape lives in `scripts/verify_primitive_candidates.py` (kind ∈
{primitive, primitive_group}; a group's `group_contract.hidden_member_edges` >= 3 with visible edges exactly equal to
its input/output).

---

## 3. The dimensional / columnar architecture (efficient matching without reading)

A primitive is not a blob — it is a wide record with many typed columns, so retrieval resolves by attribute, key,
and embedding rather than by prose. The load-bearing field families:

- **Contract columns**: `input_edge`, `output_edge`, `input_edge_description`, `output_edge_description`,
  `edge_contract{preconditions, postconditions, failure_modes, composition_notes}`, `contract{summary, input, output,
  errors, transformation_logic}`, `blackbox`.
- **Effect / runtime columns**: `effects[]`, `runtime_targets[]`, `mutators[]`, `proof_requirements[]`,
  `promotion_blockers[]`, `promotion_status`.
- **Key blocks (blocking keys)**: `blocking_keys[]` — the LSH-style lexical/semantic buckets that let search prune
  the universe to a small candidate set in one hop (`src/teleon/registry/primitive_match.py` blocking lanes).
- **Search / view columns**: `slug`, `domains[]`, `capability_tags[]`, `source_family`, `source_evidence_status`,
  `quality_score`, `readiness`, `trust`, `surface_visibility`, `card_hash`, `source_digest`.
- **Variation dimensions**: an extensible dimension bank (industry · region · jurisdiction · schema_standard ·
  data_shape · transform · runtime_target · package_target · role · privacy_class · …) —
  `catalog/knowledge-packs/data/primitive-variation-dimension-atlas/` (count from its manifest, never typed). A
  primitive carries a `variation_profile` naming which slices it applies to, so one row covers many variants instead
  of exploding into thousands of near-duplicate rows.
- **Multi-embedding profiles**: not one vector per primitive but NAMED profiles — `edge_io_embedding`,
  `blackbox_embedding`, `problem_statement_embedding`, `failure_mode_embedding`, `negative_memory_embedding`,
  `benchmark_task_embedding`, `deployment_packaging_embedding`, … each stored long-form (primitive_id,
  embedding_profile_id, model_id, dimensions, vector, source_field_hash) so different queries hit the right facet.
  Registry: `catalog/knowledge-packs/data/embedding-profile-registry/` (declarative); infra: `embedding_port.py`
  (LexicalEmbedder floor + LocalOllamaEmbedder nomic-embed-text 768) + RRF fusion.
- **Edge-type vocabulary (the input/output/edge layers)**: `catalog/knowledge-packs/data/canonical-edge-type-vocabulary/`
  — the shared intermediate-type system (RawGraphInput → EdgeList → AdjacencyGraph → DistanceMap → AnswerArtifact,
  …) that makes edges MATCH across primitives. A primitive's `output_edge` type_id reappearing as another's
  `input_edge` type_id is what makes routes COMPOSE — the difference between "relevant" and "chainable."

The payoff: a query prunes by blocking keys (one hop), reranks by the right embedding profile, and confirms by edge
compatibility — all over columns, never over implementation bodies. That is how ~113k+ primitives stay searchable and
composable at the model boundary without the model reading any of them.

---

## 4. Flexible mutations, remixes, and adjustments

A near-match is made usable without asking a model to write unbounded glue. Remix is itself a portfolio:

- **Deterministic mutators** (preferred — zero tokens, provable): `field_rename`, `field_project`, `type_cast`,
  `schema_validator_inserter`, `input_envelope_wrapper`, `output_receipt_wrapper`, `idempotency_wrapper`,
  `retry_wrapper`, `cache_wrapper`, `pagination_expander`, format mutators (`json_to_parquet`, `wide_to_long`, …),
  runtime wrappers (`api_endpoint_wrapper`, `queue_worker_wrapper`, `kubernetes_job_wrapper`, `mcp_tool_wrapper`),
  `route_to_group_card`. Each declares preconditions, postconditions, lossiness policy, proof obligations, and
  telemetry fields. Path: `RequestedEdge → CandidateBundle → ContractDiff → MutatorPlan → RouteCandidate →
  PlanLock → ProofReceipt`.
- **Non-deterministic / model-assisted remix** (bounded roles only): field-alias suggestion, ambiguous schema
  mapping, code micro-repair, proof-case suggestion, error explanation — the model PROPOSES, the deterministic
  compiler DISPOSES. Model output stays candidate=true / serves_truth=false until proven.
- **Tool / system-assisted**: mutators may call a real tool (a formatter, a linter, a validator, a schema compiler,
  a container build) as a bounded, receipted step — the tool result is the mutation, verified by a proof.
- **Genetic / sprout mutators** (experiment mode, budgeted): mutate retriever weights, embedding-profile mix,
  candidate-bundle size, context-depth limit, model-slot assignment, LoRA choice, route-member order, proof-gate
  order, blocking rule, matching threshold. Sprouts stay candidate-isolated and promote only on held-out wins.

Every mutation is a tracked path with a receipt — so the system learns which mutator wins for which contract-diff
shape, and the cheapest sufficient mutation is selected next time.

---

## 5. Globally-unique names → deterministic graphing

Advanced deterministic graphing depends on names being globally unique and meaning-bearing, so **grep-as-graph is
exact** — the code graph, primitive edges, and cross-codebase search resolve by NAME with zero ambiguity. Two planes,
one law (`docs/codex/ai-first-naming-and-graph-spec.md`):

- **Code objects (Python)**: the pyprefix scheme `py_<kind>__<file>__<scope>__<name>` — every defined thing gets a
  location-derived, unique, long name (a name is context the model uses; no name is ever reused; uniqueness lives IN
  the name). Every collision removed increases graph recall (`codegraph.py` drops ambiguous call edges today; unique
  names climb that back).
- **Data objects (records/ids)**: minted only by the single source `src.teleon.experiments.ids` —
  `canonical_id = "{prefix}-{sha256[:16]}"` over canonical bytes. Version lives in `schema_version` METADATA, never
  in a name or id (no `.vN`, no `@N` suffixes).

Because names are unique and edges name their endpoints (`input_edge` / `output_edge` type_ids from the vocabulary),
the whole primitive universe is a deterministic graph: a route composer WALKS it (producer_family → type → consumer_family
edges in the edge-type vocabulary's `family_edges.jsonl`) rather than guessing. Unique names + typed edges are what
let agents compose by reading names + edges, not bodies.

---

## 6. How it all composes (the flexible loop)

```text
user intent
 -> decompose (path portfolio: rule / small-model / frontier decomposer)
 -> multi-path SEARCH -> CandidateBundle (exact + near + template + mutator + fallback, with negative-memory warnings)
 -> multi-path ORDER/COMPOSE (edge-chain the bundle output_edge->input_edge; template fill; PlanDelta; graph search)
 -> multi-path REMIX (deterministic mutators first; bounded model only for the missing edge)
 -> PlanLock (canonical, hashable, replayable)
 -> multi-path EXECUTE (local fn / container / serverless / queue / k8s / human-review — by effect + risk + proof)
 -> proof receipts + telemetry
 -> metrics/receipts PROMOTE the winning path, DEMOTE losers to negative memory, QUEUE gaps
 -> registry memory compounds; next identical situation is cheaper
```

No box in that loop is a single implementation. Each is a portfolio, each choice is receipted, and the winner is
whatever the data says is cheapest-that-still-proves for THIS situation — which may differ next time as the registry,
the models, and the negative memory evolve. That is the whole design: **not one architecture, but a flexible
multi-path system that lets data choose.**

---

## 7. Why this is efficient (the summary)

- The model reads **edges, not bodies** — ~150–300 tokens per candidate, never implementation.
- Matching is **columnar**: blocking keys prune, embedding profiles rerank, edge types confirm composability.
- Remix prefers **deterministic, zero-token** mutators; the model generates only the genuinely missing edge.
- Every step is a **tournament with receipts**, so the system converges on the cheapest sufficient path and remembers
  failures instead of repeating them.
- **Nesting-doll** hiding + **globally-unique names** + **typed edges** make the universe a deterministic graph a
  small model can walk — the substrate for "retrieve capabilities, not code."
