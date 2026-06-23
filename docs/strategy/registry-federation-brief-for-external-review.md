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

Two load-bearing claims to critique:
- **The federation is mostly already built.** Of 35 proposed registries, **32 have real backing on disk**
  (10 `live` + 22 `partial`); only **3 are true gaps**. The repo carries **~180 `architecture/*.json`
  registries + 48 `src/teleon/` modules + 45 `schemas/` dirs** today.
- **The moat is the flywheel, not the registry count.** 35 empty catalogs is not a moat; the moat is the
  loop that *fills and scores* registries from real runs.

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

**Status to critique:** the *primitives* exist; a *single declared interface contract* all registries
conform to does **not** yet exist. The claim is that declaring it is the highest-leverage next move.
Canonical machine-readable source: `architecture/registry_ontology.json` (with `universal_interface` +
`universal_object` blocks).

---

## 3. The full registry catalog (35)

`stage` ∈ {pre_llm, model, post_llm, runtime, cross_cutting}. `status` grounded against disk.

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

**The 3 true gaps:** `agent_behavior` (14), `semantic_ontology` (20), `observability` (33). Owner-flagged
moat gaps to fill first: `failure` (7), `equivalence` (11), `semantic_ontology` (20).

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

- Registries: **10 live, 22 partial, 3 gap** (of 35). ~180 registry JSONs exist repo-wide.
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

1. **Ontology completeness/cuts:** Of the 35, which are genuinely orthogonal vs which should *merge*
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
8. **Sequencing:** given 32/35 already have backing, where would *you* spend the next unit of effort —
   the interface contract, the 3 gaps, or depth on an existing `partial`?
