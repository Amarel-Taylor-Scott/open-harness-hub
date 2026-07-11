# Primitive Discovery Factory — reuse map & build order

> Owner design intake 2026-07-08 (five specs: Primitive Discovery Factory · Primitive-OS 40-class expansion ·
> driver-neutral browser/tab-control substrate · GitHub reports · recursive six-plane factory). This doc maps that
> whole vision onto **what already exists in this repo** so we build only genuine gaps. Grounded in three
> read-only reuse audits (2026-07-08). **Reuse-first is the law here** — "this already exists, don't rebuild it"
> is the highest-ROI decision (`CLAUDE.md`, `docs/codex/…`).

## 0. Thesis (the audit's verdict)

The substrate is **already built and proof-backed**; the owner's specs are ~85% reconciliation, ~15% genuine new
work, and the new work is **execution wiring + a few formalizations**, not foundations.

- **Primitive Discovery Factory (12 stages): 11 PARTIAL, 1 clean EXISTS** (serving). Every stage has real,
  proof-gated substrate; the gaps are an orchestrated durable spine, executor/fixture synthesis, a closing
  question/coverage loop, a multi-role extraction ensemble, and real capture/parse engines.
- **Primitive-OS (41 classes): ~19 EXIST, ~14 PARTIAL, 7 true GAP.** Cheapest high-value wins are
  formalization-only (warranties, counterfactual-repair, tool-rightsizer, anti-primitives).
- **Source surfaces:** GitHub *harvesting* exists; the *report layer*, process-mining, tickets, schema-diff, and
  SQL/stored-proc surfaces are the gaps.

The owner's own principle is already our law: **LLMs propose & interrogate; deterministic systems store, validate,
execute, monitor; humans approve high-risk; everything is born `candidate=true, serves_truth=false`.**

## 1. The owner's architecture ↔ our planes

The "six planes" / "recursive factory" map onto existing subsystems:

| Owner plane | Our existing home | Status |
|---|---|---|
| Source Plane | `continuous_primitive_scrape_loop.py:SOURCE_POLICIES` (12 governed families), `foundry/sources.py:SourceScout` | PARTIAL — no T0–T5 ladder, no active radar |
| Acquisition Plane | `primitive_browser_control_harness.py` (browser+tab, NEW), `acquisition/github_repo_harvester.py`, `aidevobserver_pypi_source_scan.py`, `ingest/source_adapters.py:REGISTRY` | PARTIAL — HAR/a11y/network + Postman/GraphQL importers missing |
| Digestion Plane | `ingest/parser_provider.py:DoclingParser`, `schemas/ParsedDocument.schema.json`, `import_openapi_as_api_primitives.py` | PARTIAL — pdf/html→md engines cataloged-but-unavailable |
| Interrogation Plane | `continuous_primitive_scrape_loop.py:generate_question_bank`, `primitive_deconstruction_plane_pipeline.py` (955-question DB) | PARTIAL — questions first-class but **inert** (don't drive recrawl) |
| Primitive Factory Plane | `source_to_primitive_foundry.py`, `foundry/pipeline.py:Foundry`, `primitive_package_contract.py:formalize_card`, `primitive_security_gate.py`, `primitive_lifecycle.py`, `lint_primitives.py`, `primitive_benchmark_taxonomy.py` | PARTIAL — **spec→executor+fixture synthesis missing** (the promotion bottleneck) |
| Registry + Runtime Plane | `primitive_runtime.py:compose_solution`, `compiled_route_cache.py`, `capability_retrieval_mcp_server.py`, `primitive_multi_index.py` (79-col), storage tiers | **EXISTS** — retrieve→compile→deterministic-exec→LLM-only-for-gaps |

## 2. Factory-1 — 12 stages (audit)

| # | Stage | Status | Strongest evidence | Gap |
|---|---|---|---|---|
| 1 | Source radar / trust tiers | PARTIAL | `check_source_authority.py:classify`, `primitive_browser_control_harness.py:classify_trust_tier` | no T0–T5 ladder, no active radar |
| 2 | Browser capture (DOM/shot/HAR/AX/net) | PARTIAL | `browser_capture.py:CDP`, `primitive_browser_control_harness.py:CdpBackend` | HAR/a11y/network still `None`-stubbed |
| 3 | API ingestion (OpenAPI/Postman/GraphQL) | PARTIAL | `import_openapi_as_api_primitives.py` | Postman + GraphQL→primitive importers missing |
| 4 | Artifact normalization | PARTIAL | `ingest/parser_provider.py`, `schemas/ParsedDocument.schema.json` | pdf/html→md engines unavailable (no-pip) |
| 5 | Architecture digestion (typed graph) | PARTIAL | `continuous_primitive_scrape_loop.py:build_primitive_graph` | no single object×action×state×standard digester |
| 6 | Question engine (first-class) | PARTIAL | `primitive_deconstruction_plane_pipeline.py` | questions **inert** — don't drive recrawl |
| 7 | Decomposition rubric | PARTIAL | `primitive_descriptor.py`, `standards_factory_minter.py:OP_SETS` | keyword scoring, not a POS/noun-verb rubric |
| 8 | Coverage grid (all-possible) | PARTIAL | `vocabularies/primitive-atlas-axes-role-matrix.yaml`, `primitive_multi_index.py` | no covered/missing grid **enumerator** |
| 9 | LLM worker-role ensemble | PARTIAL | `src/baltor/workers/worker_router.py`, `context_workers/model_cascade.py` | discovery loop uses ONE decomposer role |
| 10 | candidate→spec→package | PARTIAL | `primitive_package_contract.py:formalize_card`, `primitive_security_gate.py` | **nothing synthesizes executor+golden fixtures** |
| 11 | DAG + durable queues | PARTIAL | `foundry/queues.py:SqliteQueue.reap_stuck`, `src/teleon/dag` | queues only at partition boundary; stages run in-process |
| 12 | Serving (retrieve→compile→exec) | **EXISTS** | `primitive_runtime.py:compose_solution`, `compiled_route_cache.py` | the one clean EXISTS |

**Top-5 gaps by leverage:** (1) durable-queue DAG spine · (2) spec→executor+fixture synthesis [= task #26, unblocks
the whole atlas] · (3) close the question/coverage loop · (4) multi-role extraction ensemble · (5) real
capture/parse engines (HAR/a11y/network + Postman/GraphQL + pdf/html→md).

## 3. Primitive-OS — 41 classes (audit, condensed)

**EXISTS (~19):** proof-receipts (`schemas/…/EnvironmentRunReceipt`, `ModelInvocationReceipt`), shadow-diff
(`schemas/determinism/ShadowRunReport`), counterexample miners (`PatternCandidate.counterexample_trace_ids`),
lineage/genealogy (`primitive_provenance_graph.py`), collection prims (`robust_query_grains.py:_jaccard`),
sequence/CDC (`temporal_cdc_primitives.py`), process→primitive mining (`PatternCandidate`), reason-codes,
unit-economics (`primitive_benchmark_taxonomy.py:break_even_n`), demand-signals (`mint_unmet_edge_producers.py`),
evidence-packs, primitive-local memory, linter (`lint_primitives.py`), data-contracts
(`generate_parametric_validation_rules.py`), side-effect+least-privilege (`primitive_package_contract.py`,
`EgressRoutePolicy`), schema-remixer (`domain_fmt_domain_messages.py` X12/HL7/FHIR/ISO20022), benchmark-source
ranker, coverage-map (`primitive_enrichment_coverage.py`), loss-bounded compression (`check_context_compressor.py`).

**PARTIAL (~14):** simulation-envs (agent/economic sims exist; fake ERP/EHR/payer/bank absent), UI state-machines,
semver-compat, data-rights/retention, human-skill-extraction, cross-domain-transfer, synthetic-customer-packs,
risk-mode-router (per-axis pieces, no unified selector), canary, ask-one-question, workflow-salvage,
action-reversibility, kill-switch (card gate, no runtime control plane), business-rule mutation tests.

**GAP (7):** anti-primitives/negative-knowledge · policy-delta compilers · tool-rightsizer · data-type
chaos-monkey/fuzzers · primitive warranties (tested_on/not_tested_on/expires) · review-budget optimizer ·
counterfactual-repair suggestions.

**Cheapest high-value wins (data/infra already present — formalization only):** ① warranties (the bench+receipt
data already exists) · ② counterfactual-repair (lint/gate findings + `primitive_repair_path_graph.py` already
exist) · ③ tool-rightsizer (`path_router_zoo` + `permission_manifest` substrate) · ④ anti-primitives
(counterexamples captured but never aggregated into a "don't-mint" store).

## 4. Source-mining surfaces (audit, condensed)

**EXISTS:** PyPI (`aidevobserver_pypi_source_scan.py`), GitHub repos (`acquisition/github_repo_harvester.py`),
Kaggle (strong: `mine_meta_kaggle.py`, `kaggle_notebook_primitive_foundry.py`), OpenAPI import + a diff engine
(`pipeline_runtime/source_graph.py:diff_source_graph`).
**PARTIAL/emit-only:** GitLab/Actions/dbt/Airflow/Dagster (catalog tags, no parsers), OpenML/HF/Croissant
(emit-only, no ingest), spreadsheets (`check_formula_registry.py` spec, no .xlsx extractor), prompt-to-spec
(`request_intake.py` — task+schema, **no role/negative-tests/verifier**).
**GAP:** Kedro/Hamilton, D3M, SOP docs, email threads, RPA traces, **process-mining from event logs**, tickets
(Zendesk/Jira/ServiceNow), SQL history/stored-procs, GraphQL/protobuf/avro schema-diff watchers.

**Top-6 gap surfaces by yield:** process-mining · tickets · schema-diff watcher · SQL/stored-procs · HF/Croissant
ingest · prompt-to-spec completion (role+negative-tests+verifier).

## 5. Browser + tab-control substrate (driver-neutral) — SHIPPED + building

Owner directive: *"the important thing is not the driver, it is that every action produces an evidence record;
build the stable tab-control API + report format first — every tool becomes an adapter."* Implemented exactly:

- **`primitive_browser_control_harness.py`** (committed `90189cd5e`, `290b56c5b`): a **backend ZOO** (11 driver
  rows — `static`+`cdp` implemented over system Chrome via the zero-dep stdlib CDP transport reused from
  `browser_capture.py`; `nodriver`/`playwright` available; `browser-use`/`browser-harness`/`pinchtab`/`lightpanda`/
  `agent-browser`/`chrome-extension` as documented seams) · the owner's **`browser_*` primitives** (readable-text,
  links, forms, openapi/graphql/downloadable/side-effect/login-wall/captcha detectors — detect-only, never
  bypass) · **tab control** (open/list/switch/close, last-tab protected; live over CDP `Target.*`) · the
  **safety rail** (robots respect, per-domain throttle, secret redaction, provenance hash, never-submit) →
  evidence-linked **CapturedArtifact** rows (candidate-only, no raw body).
- **`TabControlAPI`** (the driver-neutral command plane): ~19 stable commands (`session/tab/observe/act/verify`)
  over ANY backend; **every command emits an action receipt** (`command_id`, before/after `state_hash`,
  `side_effect_level` on the read_only…money_movement ladder, `requires_confirmation`, `verifier_result`,
  `artifact_refs`, `error`). **Read-only by default** — act commands are refused unless `allow_side_effects=True`,
  and `write`+ levels still require confirmation.
- **Building (subagents, offline-fixture, candidate-only):** GitHub report layer (`github_repo_report.py`:
  repo_inventory/primitive_mining/test_fixture) · browser session + **tab-graph** reports
  (`browser_session_report.py`) · browser primitive-candidate generator
  (`browser_report_to_primitive_candidates.py`) + `schemas/{browser_session_report,tab_state,browser_primitive_candidate,github_report}.schema.json`.

## 6. Ranked build order (genuine gaps only — additive, law-bound)

Each slice is `candidate=true, serves_truth=false`, offline `--self-test` (mutation-gated + deterministic),
registered in `flywheel_proof_modules.py`, ids via `canonical_id`, security-gated if it generates code.

1. **Spec→executor + golden-fixture synthesizer** (Factory-1 #10; task #26). The bottleneck that strands the whole
   atlas at "candidate." Turn a `needs_executor=true` spec (standards_factory / OpenAPI / process_stage) into a
   runnable executor + positive/negative fixtures → run → benchmark → promote. Highest leverage.
2. **Durable-queue DAG factory spine** (Factory-1 #11). Wire the existing `foundry/queues.py` + `src/teleon/dag`
   *between* stages so discovery is resumable/parallel/fault-tolerant.
3. **Close the loop** (Factory-1 #6+#8): unanswered-question → recrawl task; a coverage-grid enumerator over the
   atlas axes emitting `coverage_gap` rows into the existing `gap_queue`.
4. **Real capture/parse engines** (Factory-1 #2/#3/#4): CDP HAR/network + accessibility tree; **API-from-browser**
   inference; Postman + GraphQL→primitive importers; a no-pip html/pdf→markdown extractor.
5. **Multi-role extraction ensemble** (Factory-1 #9): route the discovery LLM step across
   classifier/architecture/critic/deduper/benchmark roles (the `hy3_overnight_flywheel` task registry + the
   deterministic `worker_router` are the substrate; TinyRouter's oracle-ceiling gate decides if routing pays).
6. **Formalization quick-wins** (Primitive-OS GAPs): warranties · counterfactual-repair · tool-rightsizer ·
   anti-primitives/negative-knowledge store.
7. **New source surfaces** (highest yield first): process-mining · tickets · schema-diff watcher · prompt-to-spec
   completion.

## 7. Laws every slice inherits

Candidate/truth boundary (born candidate) · reuse-first (check the guard before building) · security gate on all
generated code (never executed by the factory) · lossless distillation (raw + rejected + lineage preserved) ·
no-magic-values (counts computed) · globally-unique naming (`canonical_id` data plane, `pyprefix` code plane) ·
verify-the-verifier (mutation + determinism + ratchet). Browser-specific: read-only default · never bypass
robots/captcha/paywall/auth · redact secrets · every action → an evidence receipt.
