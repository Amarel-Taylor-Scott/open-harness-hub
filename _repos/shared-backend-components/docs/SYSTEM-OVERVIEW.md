# System Overview — AI Done Right / OpenHubForAI substrate

> Single authoritative overview: what each **surface**, the **architecture**, and the **primitive database** are;
> the **rules / contracts**; how we **benchmark, expand, and prove actual token savings**; the **infrastructure**
> (what is flat-file/JSONL today vs what belongs in databases/microservices); and **hosting + costs + separation of
> concerns**. Grounded in the repo as of 2026-07-09. Everything the substrate returns is `serves_truth=false` —
> pointers and shapes, never truth. If this disagrees with `BIBLE.md`, the BIBLE wins; if it disagrees with the
> executed savings ledger (`REAL_SAVINGS_NUMBERS.md`, `HANDOFF-GPT-5.6.md`), the executed evidence wins.

---

## 1. Purpose & end goal

**End goal:** a **computational substrate for executable capability** — a database-backed registry federation of
reusable AI-pipeline components ("primitives") + the factory that generates/verifies them + the service-plane that
serves them, so that AI coding/agent work is done by **composing verified deterministic components** instead of
re-generating and re-deriving code every time. The governing principle: **the LLM proposes, the deterministic system
disposes.** The commercial thesis: prove and sell **measured token/cost savings + correctness + governance** on real
agentic developer work.

**The four filters that gate what we build** (`architecture/substrate_layers.json → foundational_law`):
1. *System filter* — does this improve compiler intelligence? If no, don't build it.
2. *Execution filter (descent)* — can intelligence be removed from this execution path? Descend toward that.
3. *Component admission* — must LIFT over the bare model AND the lift must be STRUCTURAL/durable.
4. *Binding constraint* — DEPTH BEFORE BREADTH: every layer serves the ONE vertical being proven to a paying customer.

---

## 2. The surfaces (product layer)

Five product surfaces + the AI-usage observer. Each is the full built-out app in `web/<brand>/`, served by the
**showcase** over the shared kit, wired to the service-plane through same-origin **seams** (`/api/identity/`,
`/registry/`, `/api/teleon/`, `/api/observer/`). **Never build a skinny static replacement for a surface** — serve the
rich app; if a backend call 501s, wire the seam + a service-plane service.

| Surface | Definition | Functionality | End goal / contract |
|---|---|---|---|
| **AI Done Right** (`aidoneright.dev`) | Parent/platform brand ("AI, done right.") | Portfolio front door; brand + navigation | Holds the family together; not a product itself |
| **Teleon** (`teleon.dev`) | The purpose-driven, eval-gated, self-adaptive compute **runtime SaaS** | Owns PurposeTask/CapabilityTask, runtime selection, evidence ledger, promotion/policy gates, boundary approvals, adapters, the assurance dashboard (Control Tower + Capability Assurance Portal) | Runs capabilities; LLM output is never truth without a passing proof |
| **Baltor** (`baltor.ai`) | The applied, customer-facing **context/truth product**, powered by Teleon (a tenant) | Six-stage context pipeline + verification rail; governance, provenance, signed facts, CDC | Governs context truth; first live `serves_truth=true` = OFAC/sanctions screening |
| **OpenHubForAI** | The open ecosystem (evals/harnesses/templates/skills) + the open **CapabilityTask spec (CTS)** | Discovery surfaces: registries (live + private-bench) | Discovery is not trust; the neutral open spec |
| **AIDevObserver** | The AI-usage layer (session review, NOT code review) | Observes real AI coding sessions; reuse hints; redundancy detection; feeds the primitive factory | Watches usage; findings are candidate advice until proven |

**Architectural law (enforced by `scripts/check_portfolio_dependency_law.py`):**
`Baltor → Teleon → OpenHubForAI`, **never the reverse**. Teleon must never import Baltor (it is reusable
infrastructure, not a Baltor feature); OpenHubForAI imports neither (the open spec stays neutral).

---

## 3. Architecture — the substrate (8 layers) & separation of concerns

The **shared-backend-components** repo is the substrate every product consumes (never the reverse). Its 8 layers
(`architecture/substrate_layers.json`): `computational_genome · infrastructure_registry · software_relationship_graph
· human_behavioral_registry · ai_waste_engine · universal_adapter_factory · capability_futures ·
existing_systems_registry`. It exposes: the registry federation, the seven-primitive model, the code graph, the
eval-harness, the storage tiers, the credential plane.

**Separation of concerns (planes):**
- **Development plane** (`scripts/…`) vs **product plane** (`src/<x>/…`, physically `_repos/<x>/backend/src/<x>/…`).
  Dev tooling never ships in the product; product code follows the deterministic naming law from the first draft.
- **Registry federation** — ONE `Registry<T>` behind a uniform port (`src/teleon/registry/port.py`), verbs
  `list/lookup/search/explain`; every registry is a `CATALOGS` entry, never a bespoke accessor. #1 risk = ontology
  fragmentation → the reinvention guard + `search_all` are the grounding moat.
- **Two deterministic naming planes:** CODE objects use `py_<kind>__<file>__<scope>__<name>` (`scripts/pyprefix.py`);
  DATA ids are minted only by `src.teleon.experiments.ids.canonical_id` (`{prefix}-{sha256[:16]}`). Version lives in
  `schema_version` metadata, never in a name/id.

---

## 4. The primitive database

**The seven primitives** (`docs/concepts/component-taxonomy-and-stages.md`): Input · Knowledge Corpus · If Statement ·
Action · Loop · Stop/End · Output. Product vocabulary: **Knowledge Corpus** (not "knowledge pack"), **If Statement**
(not "rule pack"), **Action** (a persona/tool/processor/harness/rubric). Components span **pre-LLM** (intake, OCR,
normalization, dedupe, routing), **LLM/model** (local/hosted/browser models, embeddings, rerankers, fine-tunes), and
**post-LLM** (verification, scoring, review queues, CDC, signed updates).

**Candidate/truth boundary (law #3):** every generated row is born `candidate=true, serves_truth=false`. Generation is
not promotion. Keep **generated / staged / load-ready / promotion-ready / committed / search-ready** as distinct
counts — never report raw generated lines as active components.

**Required row families** a factory batch preserves: `source_record · normalized_object · canonical_entity ·
object_entity_ref · dedupe_cluster · label_assignment · dimension_value · object_embedding · index_record`
(+ `review_ticket` on risk).

**Corpus reality (audited):** ~**112,731 distinct searchable cards** (verified factory + edge cards, disjoint) +
~15K gap-fill ≈ 128K governed/source-backed; the jump to ~**1.17M records** is a 1M synthetic seed corpus + 37K
drafts, un-promoted. **Do not claim "1.17M primitives" as product** — the governed figure is ~112–128K.

---

## 5. Infrastructure & data tier — current reality → target (monolith files → databases/microservices)

**This is the biggest infrastructure debt.** The system was DESIGNED for a database tier but the data actually lives
in flat files. Audited 2026-07-09:

- **38,880 JSONL files, ~68 GB** under `data/dev-intel/`.
- A **one-record-per-file anti-pattern**: **2,070 `economic_observations-*.jsonl`** files (each a single row — should
  be ONE table/topic).
- **Multi-GB monolith JSONLs** that should be DB tables / columnar warehouse: `grid_primitive_candidates.jsonl`
  (4.6 GB), `minted_gap_primitive_candidates.jsonl` (1.1 GB), `component_breakdowns.jsonl` (635 MB),
  `question_answers.jsonl` (458 MB), `linkable_primitive_cards.jsonl` (358 MB).
- **`db/postgres/schema.sql` EXISTS** (tables `component`, `component_version`, `setting_profile`, + btree indexes)
  and an `object_embedding` pgvector table is defined — **but the primitive cards were never loaded into Postgres**,
  the pgvector **HNSW index is commented out and unpopulated**, and there is no faiss/hnswlib anywhere.

**Storage-tier policy (target, `architecture/storage_tier_policy.json`):** three tiers, cleanly separated —
**config = JSON (versioned, in git)** · **operational = Postgres + pgvector (served, low-latency)** · **history =
warehouse (BigQuery/ClickHouse, append-only telemetry)**. The local→cloud swap is meant to be **config-only**.

**What should migrate, and to what:**

| Today (flat file) | Problem | Target home | Why |
|---|---|---|---|
| Primitive card JSONL (`verified_*`, `edge_*`, `*_candidates.jsonl`) | 68 GB scattered; no indexed query; re-read whole file | **Postgres `component`/`component_version` (operational)** + **pgvector `object_embedding` (HNSW)** | O(candidates) search, ANN semantic search, transactional promotion |
| 2,070 `economic_observations-*.jsonl` (one row per file) | Filesystem inode blowup; unusable for analytics | **Warehouse table (history tier)** — one `economic_observations` topic, partitioned by time | Time-series analytics, cheap append, no inode sprawl |
| Multi-GB monolith JSONLs (candidates, breakdowns, Q&A) | Whole-file rewrite; no partial update; memory blowup | **Staging table + CDC → operational**, large blobs to **object storage** with handles in the DB | Streaming load, partial update, dedupe at load |
| Persisted lexical inverted index (`primitive-search-index/`, 120 MB) | Flat, single-node, rebuild-to-update | **Postgres GIN-FTS or Elasticsearch/OpenSearch BM25** | Incremental update, distributed query |
| Persisted embeddings (`dist/primitive-embeddings/`) | In-process matmul over a stored matrix | **pgvector HNSW / faiss / hnswlib** | Sub-linear ANN at scale |

**Microservice decomposition (separation of concerns → services behind seams):** the monolith `scripts/` engine
should factor into services, each behind a same-origin seam (`launch_service_plane_tunnels.py` already stands seams
up):
1. **Registry service** (`/registry/…`) — CRUD + `list/lookup/search/explain` over the Postgres component tables.
2. **Retrieval/embedding service** — lexical (GIN/ES) + semantic (pgvector HNSW) + fusion; the `intent_query` /
   `capability_retrieval` MCP surface.
3. **Composition service** — `compose_route` / `capability_compose`: deterministic wiring of verified primitives at
   0 model tokens.
4. **Experiment/benchmark service** — the reuse grid + savings ledger, writing receipts to the history tier.
5. **Factory/ingest workers** — mint → verify → promote, streaming into staging then operational.
6. **Credential plane** — env-name-only, deny-by-default (`credential_plane`), never embeds keys.

**Migration discipline (lossless, law #7):** every migration creates a new *versioned* DB layer while preserving the
raw JSONL + lineage + rollback target until the DB layer is proven (side-by-side, shadow, prove rehydration). Archived
JSONL is **moved, not deleted** (`archive/legacy/…`, in git).

---

## 6. Benchmarking & proving ACTUAL savings (the honest program)

**Discipline (no-proxy gate):** a savings number is headline-eligible only when both lanes ran the SAME task, both are
REAL (executed against a hidden oracle), both PASSED, and no-proxy holds. `both-fail = inconclusive`; a proxy (e.g.
chars/4 accounting) may **quantify a mechanism** but may NEVER headline. Report aggregates with sample sizes
(**MIN_N=8**); prefer `by_lane_model` over pooled `by_lane`; `tokens_per_pass` (all tokens incl. failed attempts /
passing run) is the fair cross-lane comparator.

**The experiment spine (this session's build, all `--self-test` green, in `run_proofs`):**
- `reuse_experiment_grid.py` — the comprehensive grid: **4 lanes × 7-model zoo × 5 task families × repeats**,
  resumable, aggregates-only. Lanes: `without` (build from scratch), `prompt:<6 variants>` (present the verified
  primitive 6 ways), `compose` (deterministic). Run to completion with `run_reuse_grid_to_completion.sh`.
- `primitive_reuse_prompt_matrix.py` — the 6 prompt variants + a **reimplementation_rate** diagnostic.
- `multi_step_task_ab.py` — `PrimitiveSessionManager` + **deterministic composition** (0-token, oracle-passing).
- `edge_exposed_gapfill.py` — **partial composition**: DB covers portions + exposes typed edges; LLM fills only the gap.
- `realistic_session_harness.py` — a **multi-turn tool-using session** with **full-session token accounting** (input
  re-sent each turn → input-dominated).
- `input_token_lever.py` — quantifies the biggest lever: compact capability-cards vs raw re-reads.
- Model zoo: codestral · qwen-coder-32b · glm-4.6 · deepseek · llama-3.3-70b · gpt-oss-120b · **gemma-4-coding**
  (browser-context CDP via `openwebui_cdp_bridge.py`, session-dependent).

**Reconciled findings (executed, 2026-07-09 — NOT yet universally concluded, grid running):**
- Single-shot **OUTPUT** savings on common code are **marginal**.
- Prompt-reuse is **prompt- AND model-dependent**: `full_source_asis` ("show full tested source + use-as-is") reaches
  pass ≈ `without` at ~**17× fewer output tokens** on some models; `signatures_only`/edges-only makes models
  **re-implement and FAIL** (~0.1 pass). Not universal.
- **Deterministic composition is the only robust 0-token win** (passes hidden oracles, model-independent).
- **Realistic sessions are INPUT-token-dominated** — the `input_token_lever` structural proxy shows a **50-turn session
  cuts input ~87%** (218,800→28,750 tokens) by mounting compact cards; **this is where "billions saved" comes from.**
- **Don't re-assert** "47.5%", "4.7–5.9×", "486×", or "1.17M primitives" as proven token savings (those are
  projection / context-byte reduction / raw-count).

**Full research agenda:** `docs/RESEARCH_PATHS_AND_IDEATION.md` — 56 ranked paths; top-8 = input/output accounting →
compact-reference-vs-raw-reread → partial composition → composition coverage scaling → presentation matrix →
large-real-codebase session replay → retrieval precision@k → reimplementation_rate KPI.

---

## 7. How we expand / increase savings
1. **Grow deterministic-composition coverage** — more templates + edge-typed auto-wiring → the 0-token floor covers
   more of each task (`validate_compose.py`, coverage_fraction curve).
2. **Scale the input-token lever** — capability-card context builders, delta/differential context, prompt-cache-stable
   verbatim mounts, frozen-substrate call surface (bodies never enter context).
3. **Broaden task families** beyond small HTTP services — refactors on large codebases, migrations,
   bug-fix-from-failing-test, ETL, infra-as-code, auth/billing (the capability-gap core).
4. **Mine → verify → template** from real built code (`saas_buildout_decomposer.py`) and consented sessions
   (demand-ranked) — the supply side of the flywheel.
5. **Admit on the two-axis gate** (lift × durability) so the DB holds only structural, durable wins.

---

## 8. Hosting (Fly.io / similar) & separation of concerns

**Model:** build local-first (default local/free/keyless), then the local→cloud swap is **config-only**
(`architecture/storage_tier_policy.json`). Teleon + Baltor deploy **same region/private network** (low Baltor→Teleon
latency) but stay **separable** (separate service / data / identity / IaC + a versioned API + graceful local
fallback). Hosting must be **agent-automatable**.

**Runbooks in repo:** `docs/architecture/fly-deploy-runbook.md`, `baltor-backend-infrastructure-stack.md`,
`surface-deploy.md`, `local-dev-tunnels-and-auth.md` (local testing without paid cloud),
`hundred-million-component-infrastructure.md` + `costed-blueprint-route-matrix.md` (scale + cost blueprints).
Deploy layer built (`scripts/launch_service_plane_tunnels.py` for local seams; Fly for cloud).

**Target topology on Fly.io (or equivalent):**
- **Stateless service apps** (registry / retrieval / composition / experiment / factory workers) as separate Fly apps,
  scaled independently, each behind its seam.
- **Managed Postgres + pgvector** (Fly Postgres or a managed provider) = the operational tier (component tables +
  HNSW embeddings).
- **Object storage** (S3/R2/Tigris) for large blobs (raw source snapshots, big candidate batches) — handles in the DB.
- **Warehouse** (BigQuery/ClickHouse) = the history tier (telemetry, economic observations, benchmark receipts).
- **Credential plane** = env-var/secret-manager only; deny-by-default; no keys in code or rows.

---

## 9. Costs

**Token economics (honest):** at ~$0.5–15 / M tokens, single-shot output savings (hundreds of tokens) ≈ fractions of a
cent — economically irrelevant. Real money is at **session scale**: a 500K-token session ≈ $2–7; the **input-token
lever** (~87% of input on a long session) is the dominant save. Pricing model: **% of MEASURED, auditable savings**
(built on `tokens_per_pass` + held-out-oracle receipts), delivered via MCP tools + private-repo scanning — NOT a raw
primitive count.

**Infra costs (target, order-of-magnitude):** managed Postgres+pgvector (small→mid instance) + a few stateless
service apps + object storage + a warehouse for telemetry. The 68 GB of JSONL should shrink dramatically once
normalized into Postgres (dedupe at load) + columnar warehouse (compression); the 2,070-file anti-pattern collapses to
one partitioned table. See `costed-blueprint-route-matrix.md` for the routed cost matrix and
`hundred-million-component-infrastructure.md` for the scale blueprint.

---

## 10. Rules / laws / contracts (inherited — do not weaken)
1. **Multi-path / non-commitment** — a design choice is a portfolio of contract-substitutable paths behind one
   selector, raced by measured receipts; never hardwire one strategy.
2. **Globally-unique naming** — two planes (pyprefix code / canonical_id data); version in metadata.
3. **Candidate/truth boundary** — born `candidate=true, serves_truth=false`; generation ≠ promotion.
4. **Change verification** — every change carries a warrant (user-intent / corroboration / principle) matched to blast
   radius; design/brand/strategy is never a unilateral single-agent call.
5. **Verify the verifier** — mutation gate + determinism gate + quality ratchet on every checker.
6. **No magic values** — repo-state numbers are computed, never typed; one definition, many readers.
7. **Lossless distillation** — distillation is never replacement; preserve raw + lineage + rollback.
8. **Archival** — move, never delete; never untrack; status-labeled under `archive/legacy/`.

Plus: **no real PII/secrets** (synthetic/public only); **avoid insurance** verticals; **sensitive domains** get review
queues + signed publishers + deterministic gates, not "just ask the model."

---

*Companion docs: `HANDOFF-GPT-5.6.md` (current handoff), `RESEARCH_PATHS_AND_IDEATION.md` (56 paths),
`REAL_SAVINGS_NUMBERS.md` (honest ledger), `BIBLE.md` (north star), `INTEGRATION-BIBLE.md` (frontend↔backend),
`strategy/teleon-baltor-openhubforai-portfolio.md` (portfolio architecture).*
