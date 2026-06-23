# Teleon registry federation — briefing for external review (GPT 5.5)

**Purpose.** This is a self-contained brief for an external model (GPT 5.5) to critique. It describes a
proposed **federation of machine-readable registries** — "a canonical knowledge graph of all executable
capability" — plus the cross-cutting architecture (storage, access, front end, embeddings, RAG, search,
I/O + object standardization, the backbone, and synergies). Status labels (`live`/`partial`/`gap`) are
**grounded against a real codebase** (file paths are given as evidence). Please pressure-test the
ontology, the universal interface, the standardization choices, and the sequencing — and name what's
missing or wrong.

**One governance invariant runs through everything:** a registry **registers pointers / rules / shapes,
never truth or a raw data dump** (`serves_truth=false`). Discovery ≠ trust: a registry *discovers* and
*scores* candidates; a separate verification rail (called Baltor) *disposes* truth. Keep this in mind when
critiquing — these registries are an optimization/selection substrate, not a database of facts.

---

## 1. Thesis

Teleon is a **compiler for cognitive work**: a request ("extract invoice fields under $0.02, deterministic
preferred") is lowered to a verified, cost-optimized execution graph (DAG) by *pruning* over registries.
Every optimization decision reads one or more registries. So the registries **are** the knowledge of the
compiler. The endgame is not workflow automation; it is the machine-readable model of *all* computation,
transformations, costs, and strategies.

**Consumption model (the demand side).** The registries are a **buffet** an AI **agent** (the customer)
consumes to assemble a functional, value-add DAG: *supply* = the registries, the *menu* = the universal
`Registry<T>` interface (search/lookup/score/benchmark), *demand* = agents building DAGs via the synthesis
compiler. An agent doesn't hand-write a DAG — it **picks** ingredients under its constraints, then the compiler
*composes → verifies → optimizes → executes → measures*. Agents-as-customers: they call stable receipt-backed
capabilities instead of burning tokens re-deriving them. Corollary (the sequencing law): **a registry no
DAG-builder reads is dead weight** — fill what the buffet is actually asked for.

Two load-bearing claims to critique:
- **The federation is mostly already built.** Of **98** proposed registries (across 5 layers; count computed
  by `check_registry_ontology.py`), **96 have real backing on disk** (13 `live` + 83 `partial`); only **2 are
  true gaps** (`agent_behavior`, `agent_qa` — both need a per-step agent-telemetry seam). The repo carries
  **~180 `architecture/*.json` registries + 48 `src/teleon/` modules + 45 `schemas/` dirs** today. Adjacent
  registries are kept non-redundant by a single-source `boundaries` block + per-entry `distinct_from` (enforced).
  The whole suite is green (`642/642` proofs).
- **The moat is the flywheel, not the registry count.** A wall of empty catalogs is not a moat; the moat is
  the loop that *fills and scores* registries from real runs. The likely moat layers are **Layer 0
  (Discovery)** and **Layer 4 (Verification)** — see §3.5, §3.7.

**The 5-layer model (architectural spine).** Every registry belongs to exactly one layer (enforced as a clean
partition): **(0) Discovery** — continuously map the external computational supply chain (the "search engine
for global machine capability"); feeds all · **(1) Capability** — what computation can do · **(2) Execution**
— what runs it · **(3) Optimization** — make it cheaper/faster/more deterministic · **(4) Verification** —
know it was correct + continuously improve. Layers 1–3 are heavily modeled; **Layers 0 and 4 are the
underbuilt moats**. Orthogonal `kind` axis (enforced): **static** (curated/indexed) · **discovery** (crawls
the world) · **meta** (pointer-only index of *where external registries live* — stores no content; pointer ≠
copy, the governance-correct default for external sources).

---

## 2. The backbone: one universal interface + one object shape

The proposal is that **every registry obeys the same interface** (so 35 registries are one governed
pattern, like `makeHub(config)` — not 35 bespoke services). Each verb already has a backing primitive:

| Verb | Meaning | Backing primitive (real) |
|---|---|---|
| `search(query)` | find entries | `src/teleon/synthesis/component_search.py` (lexical+vector) |
| `lookup(id)` | fetch one | `src/teleon/storage/record_store.py` (port) |
| `benchmark(id)` | score on a dataset | A/B harness + `open_benchmark_registry.json` |
| `score(id)` | quality/lift score | the "brain" (optimization KB) + two-axis lift |
| `health(id)` | liveness/status | `model_provider_status_codes.json`, endpoint due-diligence |
| `relationships(id)` | graph edges | `open_hubs_bridge_graph.json` + `capability_taxonomy.json` |
| `history(id)` | version history | `record_store` history tier + run receipts |
| `mutate(id)` | candidate variants | `synthesis/synthesis_tree.py` backtracking + `src/teleon/evolution/` |
| `simulate(input)` | dry-run / cost | `src/teleon/economics/` simulator + `verify_buildable_dag` |
| `explain(id)` | provenance/metadata | source handles + provenance records |

**Universal object shape** (every entry inherits — Models, APIs, Providers, Templates, Datasets, Adapters,
Policies, Prompts all the same shape): `{ id, name, type, versions, metrics, benchmarks, dependencies,
cost_model, security_profile, trust_score, historical_runs, relationships }`.

**Status (updated):** the contract is now **declared + conformant** — `src/teleon/registry/port.py` is the
`RegistryPort` menu (`list/lookup/search/explain`) over **7 source catalogs** (lookup_portals, observability,
geospatial, vulnerability, knowledge_taxonomies, human_expert, semantic), proven uniform by
`check_registry_port` (an agent picks ingredients with identical call shape across all of them). Remaining
verbs (`benchmark/score/health/relationships/history/mutate/simulate`) wire to their named primitives next, and
more catalogs join the menu. Canonical machine-readable source: `architecture/registry_ontology.json`
(`universal_interface.contract` + `consumption_model` + `universal_object`).

---

## 3. The full registry catalog (72, in 5 layers)

`stage` ∈ {pre_llm, model, post_llm, runtime, cross_cutting}. `status` grounded against disk. The table below
is Layers 1–3 (registries 1–35); **§3.5 is Layer 4 (Verification, 36–55)**; **§3.7 is Layer 0 (Discovery,
56–69) + three Execution additions (70 `agent_systems` — pre-built agents that already DO things; 71
`external_systems` — AI-compatible SaaS/tools/infra; 72 `lookup_portals` — META: where to look up a license/
property/tax/weather, pointer-only)**.

| # | Registry | Holds | Status | Stage | Backing (evidence) |
|---|---|---|---|---|---|
| 1 | capability | abstract actions (extract_text, web_search) — the action ontology | live | cross | `capability_taxonomy.json`, `capability_ladders.json` |
| 2 | component | implementations + deterministic/memory/cold-start metadata | live | cross | `tool_registry.json`, `src/teleon/components` |
| 3 | api_endpoint | individual endpoints + auth/rate-limit/pagination/errors | live | model | `external_api_registry.json`, `capability_endpoint_registry.json` |
| 4 | model | every model + **multidimensional** scoring | partial | model | `model_index.json`, `ml_model_registry.json` |
| 5 | provider | same model × providers + uptime/latency/burst | live | model | `model_provider_graph.json`, `execution_backend_pricebook.json` |
| 6 | prompt | prompt-pattern families + accuracy/format metadata | partial | model | `synthesis_prompt_templates.json` |
| 7 | failure | global failure modes + frequency + best fallback | **partial** | cross | `worker_failure_taxonomy.json` |
| 8 | transformation | universal type-conversion graph (html→md, pdf→img) | partial | pre_llm | `type_lattice.json`, `synthesis/type_system.py` |
| 9 | constraint | exec constraints (local-only, EU-residency) that prune | partial | cross | `access_policy.json`, `egress_route_policy_taxonomy.json` |
| 10 | optimization_pass | the (evolving) passes + legality checks (LLVM-style) | live | cross | `optimization_passes.json` |
| 11 | equivalence | equivalent paths per capability → enables mutation | **partial** | cross | `descent_strategy_registry.json` |
| 12 | dataset | benchmark + synthetic corpora | partial | cross | `open_benchmark_registry.json`, `schemas/benchmarks` |
| 13 | human_heuristic | human strategies (selectable-text→don't OCR) | partial | cross | `optimization_heuristics.json`, `input_profilers.json` |
| 14 | agent_behavior | how agents behave (95% start with browser search) | **gap** | runtime | — (agentic_loop_catalog is templates, not observed) |
| 15 | cost_prediction | predictive economics (peak-demand, spot pricing) | partial | cross | `src/teleon/economics`, `pricing_sources.json` |
| 16 | authentication | auth patterns (oauth2/jwt/bearer) + auto-adapters | partial | runtime | `credential_registry.json`, `service_auth_consumption_model.json` |
| 17 | rate_limit | rpm/tpm/burst + historical throttling | partial | model | `free_limited_llm_endpoint_policy.json` |
| 18 | retry_strategy | per-error best strategy (learned) | partial | runtime | `src/teleon/self_healing`, `worker_lifecycle_policies.json` |
| 19 | schema | every record schema + raw→schema transforms | live | cross | `schema_object_templates.json`, `schemas/` (45 dirs) |
| 20 | semantic_ontology | canonical field → aliases (invoice_number=bill_number) | **gap** | cross | — (high-value extraction gap) |
| 21 | decision_policy | reasoning policies (conf<0.80→escalate) | partial | cross | `default_brain_policy.json`, `descent_strategy_registry.json` |
| 22 | sandbox | isolated sandboxes + risk/conformance/cold-start | live | runtime | `sandbox_provider_catalog.json`, `src/teleon/sandbox` |
| 23 | security | package risk (license/CVE/supply-chain/score) | partial | cross | `risk_register.json`, `schemas/security` |
| 24 | trust | trustworthiness → trust_score | partial | cross | `trust_tiers.json`, `source_authority_registry.json` |
| 25 | latency | historical latency time-series (p50/p95) | partial | model | `inference_lane_profiles.json` |
| 26 | cache | content-addressed memoization (sha256→instant) | partial | runtime | `src/teleon/context`, `storage_tier_policy.json` |
| 27 | human_approval | approval rules (payment>$10k→human) | live | post_llm | `org_guardrail_policies.json`, `access_policy.json` |
| 28 | compliance | regulations (GDPR/HIPAA) → graph-pruning constraints | partial | cross | `egress_route_policy_taxonomy.json`, `licensed_professions.json` |
| 29 | execution_memory | historical runs (v14: 92M runs, 97% success) | partial | runtime | `src/teleon/monitoring`, `schemas/memory` |
| 30 | environment | deploy targets (lambda/cloudflare/gpu/k8s) | live | runtime | `execution_environment_profiles.json`, `deploy_topology.json` |
| 31 | data_source | external sources (postgres/salesforce/s3) + capability | live | pre_llm | `source_registry.json`, `ingestion_connector_catalog.json` |
| 32 | scheduler | orchestration modes (cron/event/queue/human) | partial | runtime | `routine_library.json`, `agentic_loop_catalog.json` |
| 33 | observability | monitoring providers (prometheus/otel/datadog) | **gap** | runtime | — (we have our telemetry; not a provider registry) |
| 34 | capability_relationship_graph | OCR→preprocessing→{tesseract,paddle,vision} edges | partial | cross | `capability_taxonomy.json`, `open_hubs_bridge_graph.json` |
| 35 | execution_pattern | learned patterns (scraping fails on Cloudflare→API) | partial | cross | `pattern_registry.json`, `inefficient_pipeline_archetypes.json` |

### 3.5 Layer 4 — the Verification Universe (registries 36–55)

The higher-order layer: *how do autonomous systems know computation is correct, safe, reproducible,
explainable, and continuously improvable?* `status` grounded against disk.

| # | Registry | Holds | Status | Backing (evidence) |
|---|---|---|---|---|
| 36 | validation | output-correctness validators (schema/regex/cross-doc/reconciliation/confidence) | live | `validate.py`, `dag_contract.py`, `conformance.py` |
| 37 | benchmark | **multidimensional** benchmarks (accuracy/cost/latency/determinism/hallucination/security/adversarial/edge) | partial | `open_benchmark_registry.json`, `check_teleon_ab_harness.py` |
| 38 | regression | regression history per optimization (downgrade→−7% accuracy) — compiler memory | partial | `eval/measured_lift_headtohead.py` |
| 39 | ai_testing | prompt-injection/jailbreak/hallucination/malformed-schema suites (Promptfoo/DeepEval) | partial | `run_proofs.py`, `eval/rulearena_benchmark.py` |
| 40 | ui_testing | selector-drift/layout-shift/CAPTCHA/mobile-render (Playwright/Cypress) | partial | `research/browser_port.py`, `browser_escalation_ladder.json` |
| 41 | magic_number_audit | every hidden constant + provenance ("why 0.83? validated?") | **gap** | — (discipline doc only; no scanner) |
| 42 | synthetic_data | auto edge-case generation (rotated/blurry/multilingual/handwritten) | partial | `eval/vertical_eval_suites.py`, `worked_examples.json` |
| 43 | adversarial | malicious-input testing (injection/payloads/unicode) + success_rate | partial | `check_adversarial_auth_all_realms.py` |
| 44 | explainability | reasoning chain — why the compiler chose this DAG | partial | `src/teleon/evolution`, `descent_method_catalog.json` |
| 45 | drift | behavior-change detection (site/API/model/OCR changed) | partial | `fragile_context_atlas.json` |
| 46 | agent_qa | agent-waste telemetry (loops/hallucinated calls/wasted tokens) | **gap** | — (needs per-step telemetry seam) |
| 47 | code_audit | generated-code analysis (vulns/dead-code/races) — Semgrep/CodeQL | partial | `panel_review.py`, `risk_register.json` |
| 48 | formal_verification | DAG correctness — constraints/leak/deadlock (Z3/SMT) | partial | `dag_contract.py`, `conformance.py` |
| 49 | experiment | every change is an A/B → winner + cost_reduction (CI-automated loop) | live | `src/teleon/experiments`, `ci_check.py` |
| 50 | human_preference | per-user optimization target (accuracy/cost/no-external-APIs) | live | `tenant_preferences.json`, `tenant_objective_bindings.json` |
| 51 | determinism | per-component determinism score (regex 1.0, GPT 0.42) | partial | `schemas/determinism`, `configuration_standards.json` |
| 52 | failure_recovery | recovery trees (OCR fail→2nd→preprocess→vision→human) | partial | `src/teleon/self_healing`, `capability_ladders.json` |
| 53 | provenance | field-level output lineage (JSON←PDF p4←PaddleOCR←regex v7) | partial | `source_authority_registry.json`, `io/governed_record.py` |
| 54 | observed_reality | production truth vs docs (doc 300ms, observed 1800ms) | partial | `src/teleon/monitoring`, `multi_source_run_matrix.json` |
| 55 | economic_opportunity | detect expensive workflows + optimization potential | partial | `opportunities.json`, `inefficient_pipeline_archetypes.json` |

**The 5 true gaps (status=gap):** `agent_behavior` (14), `semantic_ontology` (20), `observability` (33),
`magic_number_audit` (41), `agent_qa` (46). Owner-flagged moat gaps to fill first: `magic_number_audit`
(41), `failure` (7), `equivalence` (11), `semantic_ontology` (20).

### 3.6 Anti-fragmentation — the rigid schema spine (the owner's #1 concern)

With 55+ registries the failure mode is *ontology fragmentation*. The discipline that prevents it:
- **One rigid entry schema** every registry conforms to: `schemas/registry/RegistryOntologyEntry.v1.schema.json`
  — the single source of truth for the entry shape. The proof check *reads* this schema's `required`/`enum`/
  `pattern` and enforces it on every entry, so adding a field/value means editing the schema, not the check.
- **One universal object shape** every *item inside* a registry inherits:
  `schemas/registry/RegistryObject.v1.schema.json` (`id/name/type/versions/metrics/benchmarks/dependencies/
  cost_model/security_profile/trust_score/historical_runs/relationships`). This is what makes one universal
  interface and one universal dashboard work across all registries.
- **Clean universe partition:** the 4 universes are defined as id-lists in one place; the check enforces every
  registry id appears in exactly one universe. No registry can drift between or out of the model.
- All of the above is enforced by `scripts/check_registry_ontology.py` in the proof gate (458 assertions).

### 3.7 Layer 0 — the Discovery Universe (registries 56–69) + the meta-registry keystone

The intake layer that continuously maps the **external** computational supply chain (Kaggle/HF/PyPI/npm/
arXiv/RapidAPI/Crunchbase/cloud) and feeds Layers 1–4. **Static registry** (curated, indexed) vs **discovery
registry** (continuously crawls + benchmarks + scores) vs **meta registry** (knows *where* public registries
are; stores pointers, never content). Registries: `dataset_discovery` (56), `model_discovery` (57),
`package_discovery` (58, GitHub/PyPI **proven-live**), `paper_discovery` (59), `api_discovery` (60),
`benchmark_discovery` (61), `competitor_intel` (62), `provider_arbitrage` (63, cheapest-provider routing),
`workflow_discovery` (64, autonomous market discovery), `synthetic_capability_discovery` (65),
`repo_discovery` (66, **proven-live**), `infra_discovery` (67), `agent_marketplace_discovery` (68) — all
`partial`, all backed by a real, partly-proven crawl pipeline (`harvest_tools.py`, `github_repo_harvester.py`,
`source_search.py`, `research_radar.py`, `discovery_pipeline.py`).

**The meta-registry keystone (69 `external_registry_index`).** The governance-correct answer to "index all of
HF/Kaggle/PyPI": we do **not** copy. A meta-registry stores only *where* an external registry lives + access/
license/freshness; content is fetched on demand and lands as a **candidate** in the `staged_massive` tier
(`architecture/registry_layers.json` = core_curated | staged_massive | feeds), not read until promoted past a
license-gated boundary. *Pointer ≠ copy; discovery ≠ trust; no data dump.* The proposed crawl→classify→
benchmark→audit→populate subsystem (`discovery.aidoneright.com`) is owner-gated (recorded, not claimed).

---

## 4. Cross-cutting architecture (the part the owner specifically wants reviewed)

### 4.1 Object standardization — the shape every row inherits
- **Canonical object shell** (a 14-section template) + schema mixins: `schema_object_templates.json`,
  `object_shell_migration.json`. Every registry entry is the *same* base object (§2 universal object).
- **Seven primitives** the system reduces everything to — Input · Knowledge Corpus · If Statement ·
  Action · Loop · Stop/End · Output: `fundamental_primitives_taxonomy.json`.
- **Versioning rule:** version lives in **metadata**, never in names/IDs. IDs carry **stable hash
  suffixes** (normalized-body hash, version-definition hash, source-content hash) so daily batches don't
  collapse on dedupe/merge. Formatting changes must not create false versions; source changes must be
  detectable even when the wrapper is unchanged.
- **Required row families** every batch emits/preserves: `source_record`, `normalized_object`,
  `canonical_entity`, `object_entity_ref`, `dedupe_cluster`, `label_assignment`, `dimension_value`,
  `object_embedding`, `index_record`, `review_ticket` (when risk warrants).

### 4.2 Storage — tiered, scale to trillions of rows
`architecture/storage_tier_policy.json` + the `record_store` port (`src/teleon/storage/record_store.py`):
- **config tier** = JSON in git (all `architecture/*.json` — the curated, vetted registries);
- **operational tier** = SQLite (local) / **Postgres + pgvector** (cloud) via the port (staged candidates,
  discovered tools, the component search index);
- **history tier** = warehouse (CDC events, version history, replay).
Staged high-volume rows live in **JSONL staging**, *not* thousands of static pages. A **promotion
boundary** separates "candidate-table load-ready" (has source + dedupe + content hash + embeddings +
index records) from "tenant-visible" (no open review tickets / placeholders / unresolved provenance).

### 4.3 Input/Output standardization
- **Per-plane I/O contracts:** `plane_io_contracts.json` — every "plane" (OCR, search, browser, ASR…)
  declares a typed I/O contract so components are swappable.
- **Shared I/O spine:** `shared_io_spine.json` + `src/teleon/io/` (`event_io.py`, `governed_record.py`,
  `inference_io.py`, `work_io.py`). A type lattice + coercion (`type_lattice.json`,
  `synthesis/type_system.py`) makes the transformation graph (registry #8) typed.

### 4.4 Embeddings, descriptions, labels
- Every component is labeled with **text + keywords + a vector** by
  `src/teleon/synthesis/component_search.py` (deterministic **lexical** embed, `INDEX_DIM=256`); the
  embedding sits behind an **agnostic port** (`src/teleon/retrieval/embedding_port.py`) so a *learned*
  embedder drops in with zero call-site change.
- `object_embedding` is a first-class **row family** (§4.1); index built by
  `scripts/build_component_index.py`.
- **Descriptions/labels** are governed metadata on the object shell (not free text in names).

### 4.5 Search + RAG facilitation
- **Component search:** `component_search.py` `search()` (lexical+vector) + `compose()` (assemble per
  ladder rung). Checked by `scripts/check_component_search.py`.
- **RAG spine (agnostic ports):** `src/teleon/retrieval/` — `embedding_port.py`, `hybrid.py` (hybrid
  lexical+vector), `reranker_port.py`, `search_port.py`. DAG steps `retrieve / rerank / chunk / merge`
  (`pipeline_step_catalog.json`).
- **The corpus RAG pulls from** is itself a governed registry: OpenContextHub serves **governed context
  packs** with source handles (point-in-time, what may be served) — *current ≠ verified*; a freshness
  change is a signal to re-verify, never auto-truth.

### 4.6 Access / authorization
`architecture/access_policy.json` + `src/teleon/runtime` key holder: **deny-by-default**, 5 tiers
(public < authenticated < plan_gated < restricted < internal). A BYO key or paid plan unlocks
`plan_gated`; evasion/social-scrape/PII tools are `restricted` (need a grant); private-bench is
`internal` (staff). A BYO key **never** unlocks a restricted tool. Secrets are env-var **names** only
(`credential_registry.json`), redaction-safe.

### 4.7 Front end / standardized views (one UI → N registries)
- **One shared engine** drives all 22 hubs: `src/openharnesshub/hub_engine.py` (config from the registry;
  lifecycle scrape→ingest→digest→verify→version→serve; pluggable model/scraper ports) +
  `component_store.py` (versioned, multi-tenant, lossless, governed — only *verified* served).
- **Browse-everything view + per-hub sites** generated by `scripts/build_hub_browser.py` +
  `build_hub_sites.py` from one template. This is the substrate for the owner's "every subdomain looks
  structurally identical" idea — a **universal dashboard** (Search · Metadata · Versions · Benchmarks ·
  Relationships · Cost curves · Failure modes · Trust/Security score · Execution traces · Mutation
  candidates) is one template over the universal object (§2).
- **Owner-gated:** standing up public `*.aidoneright.com` subdomains needs owner domain/trademark
  clearance (same gate as the `.io` hub sites). Recorded as *proposed*, never claimed.

### 4.8 The backbone (ports + bus + seams)
- **Agnostic provider ports** (`src/teleon/ports/`): `environment_provider`, `reward_provider`,
  `blackboard_provider`, `stateful_swarm_provider`, `capability_binding_provider` — every external thing
  is behind a port populated from a registry, so future models/tools/providers drop in with zero
  call-site change.
- **Event bus / shared infra:** a single event bus connects modules; dev-plane shared infra
  (`scripts/_llm_client.py`, `_jsonl_store.py`) is strictly separated from the product runtime
  (`src/teleon`), enforced by a plane-separation check.
- **Architectural law (enforced):** Baltor → Teleon → OpenHarnessHub, never the reverse
  (`portfolio_dependency_law.json`). Registries live at the OpenHarnessHub/Teleon layer; the truth
  product (Baltor) consumes them, never vice-versa.

### 4.9 Synergies (how registries compose)
- **Bridge graph:** `open_hubs_bridge_graph.json` + `portfolio_connection_map.json` map how hubs/registries
  feed each other (e.g., OpenSourcesHub *where* to fetch → OpenLinkingHub *how* to match → OpenContextHub
  *what* may be served → OpenReceiptHub *the portable attestation*).
- **Recipes:** `module_bundles.json` — pre-wired multi-registry compositions (8 recipes today).
- **Ladders:** `capability_ladders.json` — each capability is a cost-ordered, deterministic-first descent
  whose rungs are pulled from *multiple* registries (component + endpoint + model + cost + constraint).
- **Three-layer map (machine-readable):** `candidate_open_hubs.json` (brand/release) →
  `hub_profiles.json` (28 hubs, the pullable rule/context/module types) → `registry_ontology.json` (the 35
  registries → real backing). Each has an anti-drift check in the proof gate.

---

## 5. Honest status summary

- Registries: **13 live, 65 partial, 2 gap** (of 80, across 5 layers + static/discovery/meta kinds). ~180 registry JSONs exist repo-wide.
- Gap-fills shipped (gap→partial, in the gate): #20 `semantic_field_ontology` (canonical field→aliases resolver), #74 `human_expert_sources`, #33 `observability_providers`. New source registries: #77 `geospatial` (OSM/Census), #78 `vulnerability` (CVE/OSV/GHSA), #79 `reverse_engineering` (governed/restricted), #80 `industry_classification` (NAICS/DUNS). Remaining 2 gaps need a per-step agent-telemetry seam.
- Three tools shipped this round (in the gate): `audit_magic_numbers` (#41 scanner — flags unnamed literals),
  `lookup_portals.json` (#72 — 14 pointer-only fact portals), `provider_arbitrage.py` (#63 — cross-provider
  price spread). New intake registries: 73 feed_sources (RSS/email), 74 human_expert_sources (Upwork/hackathons),
  75 community_sources (governed social), 76 website_navigation (per-site click-path recipes).
- Backbone primitives for all 10 universal-interface verbs **exist**; the single conformance **contract
  does not** (highest-leverage next step).
- RAG/search/embeddings/storage/IO/ports/front-end-engine: **all have real, grounded backing** (paths
  above). Gaps are depth (learned embedder, time-series telemetry, graph-DB relationships, a declared
  interface), not absence.
- **Sequencing law (the honest constraint):** schema-all-now / fill-gap-first; a registry nothing reads is
  dead weight; prove on the one starter vertical (a healthcare-admin provider directory) before
  generalizing; moat = the flywheel.

---

## 6. Questions for GPT 5.5

1. **Ontology completeness/cuts:** Of the 55, which are genuinely orthogonal vs which should *merge*
   (e.g., is `trust` (24) just a view of `security` (23) + `execution_memory` (29)? is `latency` (25) a
   slice of `provider` (5)?)? What registry is *missing* entirely?
2. **Universal interface:** Is a single `Registry<T>` contract the right abstraction, or does forcing 10
   verbs onto (say) the `constraint` or `compliance` registry create dishonest stubs? Which verbs should
   be *optional capabilities* a registry advertises rather than mandatory?
3. **Object standardization:** Is one `RegistryObject` base shape across Models/Prompts/Datasets/Policies
   a strength (uniform UI/search) or a straitjacket (forces lowest-common-denominator metadata)? Where
   should it be a discriminated union instead?
4. **Embeddings/RAG:** For a *registry of registries*, what should be embedded — the object metadata, the
   description, usage examples, or run outcomes? How do you keep a 256-dim lexical index honest until a
   learned embedder is warranted?
5. **The IR question (deferred):** We have NOT built a formal compiler IR (a "TIR" like LLVM IR) or a
   SAT/Z3 legality layer — the DAG is built directly. Is deferring the IR correct given "win one vertical
   first," or is the IR the thing that makes the other 34 registries composable and therefore *prior*?
6. **Moat:** Is "the flywheel that fills/scores registries from real runs" a defensible moat, or is the
   defensibility actually in 2–3 specific registries (`failure`, `equivalence`, `execution_memory`)?
7. **Subdomain federation:** independent `*.aidoneright.com` services per registry vs one monolith with
   logical namespaces — at what scale does the split pay for its operational cost?
8. **Sequencing:** given 50/55 already have backing, where would *you* spend the next unit of effort —
   the interface contract, the 5 gaps, or depth on an existing `partial`?
9. **Layer 4 as moat:** is "Verification Universe" (correctness/regression/drift/provenance/observed-reality)
   genuinely more defensible than Layers 1–3, or is it table-stakes that every serious player will also build?
10. **Schema discipline:** is one rigid `RegistryObject` + one entry schema enough to prevent fragmentation
    across 55+ registries, or do you need a per-registry schema *registry* (schemas that validate schemas)?
    Where does the single-shape discipline start producing dishonest stubs?
11. **Second product family:** does Layer 4 want its OWN brand/product family (`verify.aidoneright.com` /
    `audit` / `drift` / `observe` …) separate from Teleon, or is it a feature *of* Teleon? What's the
    customer/buyer difference that would justify the split?
