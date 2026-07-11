# AIDevObserver Primitive Foundry Loop

Use this file as the long-running `/goal` target for building the most useful
AIDevObserver primitive system: source-backed, edge-addressable, remixable, and
cheap for LLMs to use.

Paste this short command into Codex `/goal`:

```text
/goal Follow docs/goals/aidevobserver-primitive-foundry-loop.md. Keep the daemonized primitive-foundry/agentic loop running and improving without stopping: mine real public/local source, docs, repos, notebooks, workflows, schemas, sessions, and app microsurfaces into global source-backed primitive edge cards, capability blueprints, template routes, slots, mutators, adapters, runtime emitters, tests, vector/blocking rows, and IDE proofs. Cover broad software/app/backend/frontend/data/ML/DevOps/K8s/cloud/workflow/MCP/security use cases, not just scrapers. No synthetic trusted primitives; candidates stay serves_truth=false until proof/promotion.
```

The command above is intentionally under 4000 characters. This file carries the
full loop contract.

## Mission

Make AIDevObserver the developer tool that stops token waste by finding,
selecting, and wiring already-existing code capabilities before a coding harness
rewrites them.

The loop is not only an example generator. It is the durable agentic factory for
the global primitive database: discover real capability surfaces, extract
contracted primitive candidates, index their input/output edges, attach
deterministic adapter options, verify retrieval, and make those primitives usable
by AIDevObserver, Teleon, OpenHubForAI, Baltor-adjacent context surfaces, and
future deterministic build surfaces.

The loop must continuously improve:

- source-backed primitive generation from real code, docs, workflows, notebooks,
  packages, and agent sessions;
- route-level primitive generation from source-backed capability blueprints,
  task archetypes, app microsurfaces, template routes, and typed slots, so broad
  user tasks can compile from known patterns instead of only matching one helper
  function at a time;
- coverage of ordinary developer work: software engineering, app building,
  frontend surfaces, backend APIs, data engineering, data science, ML evals,
  DevOps, Kubernetes, cloud functions, serverless jobs, queues, MCP/tools,
  n8n/workflow automation, media pipelines, and agent harnesses;
- input/output edge extraction and blocking keys;
- edge compatibility detection, edge mutation options, and deterministic
  adapter recipes;
- source visibility classification for public demo-safe versus private/internal
  candidates;
- deterministic mutator and adapter catalogs;
- compact retrieval packets for Kimi/GLM planner calls;
- agentic-loop supervision that chooses reusable routes automatically and uses
  coding harnesses only for missing glue or truly novel code;
- deterministic route compilation and materialization;
- behavior tests, proof records, and promotion boundaries;
- AIDevObserver IDE clarity, progress visibility, exportability, and runtime
  readiness.

The north-star path is:

```text
real source/session/workflow
  -> source-backed candidate primitive
  -> capability blueprint / template route / slot records when the source is a
     multi-step app, workflow, notebook, API, infra, or product microsurface
  -> input/output edge + blackbox behavior
  -> deterministic mutator affordances
  -> adapter/runtime target options
  -> source visibility and privacy boundary
  -> registry/search/vector/blocking export
  -> compact CandidateBundle
  -> deterministic blueprint/template route if available
  -> tiny planner/tool route over edge cards, only when deterministic matching is insufficient
  -> deterministic compiler/materializer
  -> copied/importable primitive source snapshots where allowed
  -> generated tests and runtime wrappers
  -> behavior tests/proofs
  -> promotion candidate, still serves_truth=false until proof
```

## Non-Negotiable Rules

- Do not promote synthetic or placeholder primitives.
- Do not make LLM output registry truth.
- Do not require users to manually select components in the IDE.
- Do not inject full source when compact edge summaries are sufficient.
- Do not give the coding harness work that deterministic workers can do.
- Do not create raw-source public leaks, PII leaks, API key leaks, or local path
  leaks.
- Do not let public/demo retrieval surface `private_internal_only` records.
- Do not hide useful private/internal candidates from opt-in local runs; keep the
  visibility boundary explicit in search results and receipts.
- Do not require users to prompt "search for primitives"; reuse search, compact
  planner context, and route compilation are automatic.
- Do not make the harness select primitives manually; the planner/compiler select
  routes and the UI only explains what happened.
- Do not let broad tasks collapse into one scraper or one helper match; retrieve
  capability blueprints, template routes, slots, and composed edge chains before
  falling back to harness codegen.
- Do not use live paid services unless explicitly authorized.
- Do not claim Kubernetes, cloud function, vector, or promotion readiness unless
  the corresponding artifact/check actually exists.
- All candidate records stay `candidate=true` and `serves_truth=false` until
  proof/promotion.

## Current Core Commands

Run these before and after meaningful edits:

```bash
python3 -m py_compile scripts/_config.py scripts/observer_local_service.py scripts/aidevobserver_edge_foundry.py scripts/aidevobserver_context_foundry_loop.py scripts/aidevobserver_primitive_foundry_daemon.py scripts/start_aidevobserver_primitive_foundry_daemon.py
python3 scripts/aidevobserver_edge_foundry.py --self-test
python3 scripts/aidevobserver_context_foundry_loop.py --self-test
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/primitive_route_fixture_foundry.py --self-test
python3 scripts/primitive_route_fixture_verifier.py --self-test
python3 scripts/runtime_adapter_coverage_report.py --self-test
python3 scripts/aidevobserver_primitive_foundry_daemon.py --once --skip-observer-self-test
python3 scripts/observer_local_service.py --self-test
```

Run the canonical persistent agentic loop forever as a detached process:

```bash
python3 scripts/start_aidevobserver_primitive_foundry_daemon.py --interval 3600 --max-ticks 0
```

The launcher uses a user `systemd-run` service when available, which is the
preferred path inside Codex because child processes from ordinary shell
backgrounding can be cleaned up at the tool boundary. The service unit is
`aidevobserver-primitive-foundry.service`; the current MainPID is mirrored to
`.agent/aidevobserver/primitive-foundry-daemon.pid`.

Run the same loop in the foreground when an agent should actively supervise
output in the current terminal:

```bash
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --max-ticks 0
```

Run one proof-gated tick:

```bash
python3 scripts/aidevobserver_primitive_foundry_daemon.py --once
```

The daemon is the default runner. It repeatedly scans source code and
structured developer artifacts, refreshes context/use-case/source-surface
candidate queues, runs proof checks, smoke-tests registry retrieval across
developer task families, and appends machine-readable plus human-readable
receipts.

Optional live/source modes are explicit:

```bash
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --live-github
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --live-kaggle
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --live-rss-feeds
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --live-markdown-indexes
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --include-local-claude --derive-local-reviews
python3 scripts/start_aidevobserver_primitive_foundry_daemon.py --interval 3600 --live-github --live-kaggle --live-rss-feeds --live-markdown-indexes
```

Only use live modes when credentials, licensing, and privacy expectations are
clear. Live discovery still creates candidate-only rows.

The context loop also reads curated multilingual/multi-provider search scopes
by default. These are not fetched source bodies; they are query/topic seeds for
GitHub, Kaggle, PyPI/npm, RSS/news/forums, arXiv/Semantic Scholar, docs, n8n,
cloud/K8s, vector/RAG, and public dataset discovery across languages. Limit or
disable them when needed:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --search-scope-limit 25
python3 scripts/aidevobserver_context_foundry_loop.py --once --skip-multilingual-search-scopes
python3 scripts/aidevobserver_primitive_foundry_daemon.py --watch --interval 3600 --search-scope-limit 25
```

Expected outputs:

```text
data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl
data/dev-intel/aidevobserver_edge_foundry/manifest.json
data/dev-intel/aidevobserver_edge_foundry/summary.md
data/dev-intel/aidevobserver_context_foundry/*.jsonl
data/dev-intel/aidevobserver_primitive_foundry_daemon/loop_ledger.jsonl
data/dev-intel/aidevobserver_primitive_foundry_daemon/latest_status.json
data/dev-intel/primitive_route_fixtures/route_fixtures.jsonl
data/dev-intel/primitive_route_fixtures/candidate_bundles.jsonl
data/dev-intel/primitive_route_fixtures/manifest.json
data/dev-intel/primitive_route_fixtures/verification_report.json
data/dev-intel/primitive_route_fixtures/verification_results.jsonl
data/dev-intel/runtime_adapter_coverage/runtime_adapter_coverage_report.json
data/dev-intel/runtime_adapter_coverage/runtime_adapter_fixtures.jsonl
data/dev-intel/runtime_adapter_coverage/runtime_adapter_gaps.jsonl
.agent/aidevobserver/primitive-foundry-loop-log.md
.agent/aidevobserver/primitive-foundry-daemon.pid
.agent/aidevobserver/primitive-foundry-daemon.log
```

Run the public/local IDE proof path after service edits:

```bash
python3 scripts/observer_local_service.py --self-test
```

If asked to restart the public demo, use the existing approved backend pattern
and the current Cloudflare URL only:

```text
https://conducted-walt-bra-uri.trycloudflare.com/ide
```

Never provide a `127.0.0.1` URL to the user.

## Cycle Protocol

Each loop cycle must do one or more real improvements.

1. Verify the current state with the commands above.
2. Read:
   - `docs/determinism/aidevobserver-primitive-foundry-and-remixers.md`
   - `docs/codex/primitive-source-lifecycle.md`
   - `docs/codex/primitive-registry-operational-schema.md`
   - `docs/codex/global-multimodel-primitive-foundry.md`
   - `scripts/_config.py`
   - `scripts/observer_local_service.py`
   - `src/teleon/observer/registry_search.py`
   - `scripts/aidevobserver_edge_foundry.py`
   - `scripts/aidevobserver_context_foundry_loop.py`
   - `scripts/aidevobserver_primitive_foundry_daemon.py`
   - `scripts/start_aidevobserver_primitive_foundry_daemon.py`
3. Pick the highest-leverage incomplete target from the priority ladder.
4. Implement it in code, schema, docs, test fixtures, or generated artifacts.
5. Run focused checks.
6. Generate/refresh candidate primitives or benchmark fixtures when relevant.
7. Record what changed in:
   - `.agent/aidevobserver/primitive-foundry-loop-log.md`
8. Continue to the next target unless blocked by missing external credentials,
   network approval, or an owner decision.

## Priority Ladder

### P0: Keep AIDevObserver Usable

- IDE accepts a natural-language task.
- It first runs deterministic route matching by input/output edge, blackbox
  behavior, blocking keys, visibility scope, and mutatable compatibility.
- Deterministic exact or safely adapted routes compile without model calls.
- Kimi/GLM planner/tool-loop route is used only when deterministic matching is
  insufficient, and the planner sees compact edge cards rather than raw source.
- Coding harness fallback is last resort and receives only compact selected edge
  summaries plus download/import instructions for allowed primitive snapshots.
- Users never need to click registry components manually; AIDevObserver explains
  the selected route and files after automatic selection.
- The UI shows:
  - step progress;
  - planner model calls;
  - coding harness calls;
  - selected primitive edges;
  - selected mutators/adapters and their proof obligations;
  - generated files;
  - copied primitive modules;
  - tests/proofs;
  - token savings estimate;
  - runtime target.
- Broad/open-ended tasks prefer source-backed `CapabilityBlueprint`,
  `PipelineRecipe`, `TemplateRoute`, and slot cards before low-level helper
  cards. Helper cards still matter, but they should be assembled underneath the
  selected route-level pattern.

### P1: Source-Backed Primitive Generation

Improve scanners that turn real artifacts into candidate primitive records:

- Python packages and local repos;
- PyPI source archives;
- GitHub repos;
- Kaggle notebooks/projects;
- Jupyter notebook code cells and surrounding markdown section context;
- n8n workflow JSON;
- generic workflow/DAG JSON definitions and step lists;
- MCP servers/tool manifests;
- OpenAPI specs;
- OpenAPI operation-level route contracts;
- SDK examples;
- cloud function samples;
- Kubernetes manifests/operators/controllers;
- CLI tools and scripts;
- docs/tutorials with executable snippets;
- Markdown/MDX/RST fenced commands and code examples;
- shell scripts, Makefile targets, Justfile recipes, and Taskfile commands;
- public agent/coding-session transcripts.
- structured repo artifacts: `package.json` scripts, JSON Schemas, OpenAPI /
  AsyncAPI specs, CI workflow YAML, Dockerfiles, Kubernetes manifests,
  Terraform, SQL files, catalog YAML, MCP manifests, JSONL examples, and
  benchmark manifests.

Every generated primitive needs:

- stable candidate id;
- source ref and source digest;
- surface visibility: `public_demo_safe_candidate` or `private_internal_only`;
- visibility scope compatibility for public, local, and all retrieval modes;
- blackbox behavior description;
- input edge;
- output edge;
- effect policy;
- memory/cache policy;
- runtime targets;
- deterministic mutator affordances;
- blocking keys;
- license/provenance candidate fields;
- `candidate=true`;
- `serves_truth=false`.

### P1A: Massive Use-Case And Microsurface Coverage

Do not optimize only for scraper demos. The loop must keep expanding source
coverage for thousands of common developer requests and product microsurfaces.

Create or improve source-backed records for:

- app/product surfaces: auth, login, signup, onboarding, profile, account
  settings, permissions, billing, checkout, subscriptions, invoices, uploads,
  imports, exports, tables, dashboards, search/filter/sort, notifications,
  reporting, audit logs, admin panels, integrations, webhooks, background jobs,
  and data sync;
- software engineering: bugfix loops, test generation, safe refactors,
  migration plans, package upgrades, API wrappers, CLI tools, error handling,
  observability, logging, tracing, release automation, CI checks, and workflow
  replay/debugging;
- frontend: forms, validation, tables, charts, file uploads, design-token gates,
  accessibility checks, visual regression, routing, state management, and app
  shell layouts;
- backend: CRUD, policy APIs, auth/session middleware, idempotent writes,
  queues, schedulers, webhooks, OpenAPI/GraphQL routes, caching, retry,
  pagination, rate limits, and database migrations;
- data engineering: CSV/Excel/JSON/Parquet ingestion, schema validation,
  normalization, dbt/Airflow/Dagster assets, SQL transforms, warehouse loads,
  metadata publishing, and data quality reports;
- data science and ML: Kaggle-style baselines, feature engineering,
  classification, regression, forecasting, eval harnesses, leakage checks,
  model registration, batch inference, and report generation;
- infrastructure: Dockerfiles, Compose, Terraform, Helm, Kubernetes jobs,
  deployments, services, cronjobs, operators/controllers, rollout gates,
  cloud functions, serverless handlers, queues, and event triggers;
- agent/tooling: MCP servers, tool schemas, OpenCode/Aider/Codex/Claude
  harnesses, browser automation, Playwright extraction, n8n/Zapier-style flows,
  deterministic build requests, and primitive-generation loops;
- security and operations: alert triage, secret scanning, redaction,
  dependency/license checks, deploy readiness, rollback validation, incident
  reports, and policy enforcement.

For each family, prefer source-backed:

- `CapabilityBlueprint` records for the whole task;
- `PipelineRecipe` or `TemplateRoute` records for the route shape;
- `CapabilitySlot` records for required steps;
- primitive edge cards for each reusable operation;
- deterministic adapter/mutator cards for edge mismatches;
- tests/proofs and runtime emitter candidates.

If the source only proves demand but not implementation, emit a
`primitive_opportunity` or `deterministic_build_request`; do not fabricate a
trusted primitive.

### P2: Edge Search And Minimal Context

Upgrade retrieval so the planner sees compact edge cards, not source:

- exact input/output edge match;
- compatible edge match;
- mutatable edge match;
- blocking-key search;
- lexical search;
- embedding/vector search where available;
- source-backed quality score;
- negative-memory suppression;
- known-chain reuse;
- compact CandidateBundle generation.
- capability blueprint / pipeline recipe retrieval for broad tasks;
- slot-aware route assembly before helper-level matching;
- public/local visibility filtering and receipts.
- adapter-aware route assembly that can join existing primitives through
  deterministic input/output edge mutations before asking an LLM for glue code.

The planner should receive only:

- task summary;
- selected route blueprint or template route, when one exists;
- compact slot list;
- local template candidates;
- edge cards;
- mutator options;
- proof obligations;
- known gaps.
- visibility-safe edge cards for the current surface.
- downloadable/importable primitive handles when source snapshots are allowed.

Public demo mode must use `visibility_scope=public` and exclude
`private_internal_only` rows. Opt-in local mode may use `visibility_scope=local`
and can include private/internal candidates, but they remain candidate evidence
and must not be exported to public examples.

### P3: Deterministic Mutators And Edge Adapters

Add and test deterministic remixers before using LLM codegen:

- scalar_to_sequence / `map_sequence`;
- filter predicate;
- field rename;
- field projection;
- input envelope wrapper;
- output wrapper;
- type cast;
- unit conversion;
- date/time normalization;
- artifact materialize/reference;
- cache wrapper;
- retry wrapper;
- idempotency wrapper;
- pagination expander;
- batch chunker;
- fanout/fanin;
- schema validator insertion;
- provenance wrapper;
- redaction wrapper;
- secret-ref wrapper;
- API endpoint wrapper;
- CLI wrapper;
- cloud-function wrapper;
- Kubernetes job/deployment/cronjob wrapper.

Each mutator needs:

- preconditions;
- input/output contract delta;
- effect delta;
- proof obligations;
- deterministic implementation or explicit candidate status.
- searchable metadata for `input_edge_before`, `output_edge_before`,
  `target_edge_template`, runtime targets, and proof obligations.

The loop should prefer adapter composition before code synthesis. Example:

```text
dict[str, object] -> ValidatedRequest
Url -> HtmlDocument
HtmlDocument -> list[HtmlTable]
HtmlTable+Path -> CsvArtifact
HtmlTable+Path -> ParquetArtifact
ValidatedRequest+Artifacts -> PolicyDecision
PolicyDecision+IdempotencyKey -> DecisionReceipt
DecisionReceipt+PolicyDecision -> ApiResponse
```

If those edges exist, the loop should compile a route and materialize imports,
runtime wrappers, and tests; it should not ask a coding model to rewrite the
same scraper/API/persistence logic.

### P4: Runtime Emitters

Add emitters that turn compiled recipes into deployable shapes:

- local Python function;
- CLI script;
- FastAPI endpoint;
- Dockerfile/container;
- Kubernetes Job;
- Kubernetes Deployment + Service;
- Kubernetes CronJob;
- Cloud Function HTTP handler;
- workflow JSON;
- MCP tool wrapper.

Emitters must be deterministic template workers whenever possible.

### P5: Behavior Tests And Proofs

Every materialized run should create or run behavior tests where possible:

- generated app imports copied primitive modules;
- happy path;
- validation failure;
- empty/no-op edge;
- idempotency proof for writes;
- cache/retry proof for network reads;
- JSON validity for recipe/report/manifest;
- redaction proof for logs;
- route graph consistency.
- model-use accounting that separates intent/planner calls from codegen/harness
  calls.
- adapter plan checks showing which deterministic wrappers were available or
  applied.

### P6: Thousand-Primitive Scaling

Build the daily primitive factory:

1. Source discovery queue.
2. Fetch/cache source archive or transcript.
3. Deterministic parser/extractor.
4. Kimi/GLM compact summarizer only for blackbox descriptions when needed.
5. Edge-card writer.
6. Quality/promoter sieve.
7. Vector/blocking export.
8. AIDevObserver registry search integration.
9. Benchmark/session generator.
10. Proof and promotion candidate output.
11. Daemon receipts proving each tick completed or failed honestly.

The long-run target is not a finite demo pack. The daemon should be able to run
for days or years, continuously broadening coverage, deduping, testing, and
ranking. Each tick should choose one of:

- discover new source surfaces;
- extract new primitive edge cards;
- extract route-level blueprints, task archetypes, template routes, or slots;
- add deterministic mutators/adapters;
- add runtime emitters;
- improve ranking/vector/blocking rows;
- add benchmark fixtures;
- prove IDE routing;
- record gaps as candidate primitive opportunities.

Target useful candidate classes first:

- CSV/Excel/Parquet ingestion;
- browser scraping/table extraction;
- document-to-JSON extraction;
- entity enrichment;
- classification/routing;
- API policy endpoints;
- auth/session helpers;
- retries/cache/pagination;
- data validation/schema normalization;
- feature engineering/eval harnesses;
- Kubernetes/cloud-function deployment helpers;
- MCP/tool wrappers;
- n8n/workflow automation nodes.
- frontend component/form/table/action surfaces;
- backend CRUD/API/policy/auth/payment surfaces;
- mobile app settings/forms/sync/offline surfaces;
- browser automation and Playwright extraction flows;
- agent/MCP/tool-call orchestration flows;
- observability/logging/tracing/alerting surfaces;
- cloud functions, queues, schedulers, and serverless handlers;
- Kubernetes operators, deployments, jobs, services, config, and rollout gates;
- CI/build/test/release workflows;
- package scripts and CLI wrappers;
- OpenAPI/AsyncAPI route contracts;
- dbt/Airflow/Dagster-style DAG assets;
- JSON Schema/validation contracts.
- common app micro-surfaces from large websites and SaaS products: auth,
  onboarding, checkout, profile, settings, notifications, search/filter/sort,
  import/export, admin tables, audit logs, billing, permissions, reports,
  integrations, webhooks, background jobs, and data sync.
- common AI coding task families: CRUD endpoints, form flows, schema
  extraction, scraper-to-artifact, enrichment, classification, regression,
  retrieval/RAG, eval harnesses, migrations, CI, deployment, observability,
  security triage, and workflow replay.

The loop is meant to run for hours, days, or longer. Each tick should make the
registry more useful, more searchable, more remixable, or better proved. If a
tick finds only gaps, it should record candidate primitive opportunities rather
than fabricating trusted primitives.

## LLM Use Policy

Use deterministic search first.

Use Kimi/GLM only for:

- intent interpretation when deterministic rules cannot identify a route;
- calling registry search tools and choosing among compact edge cards;
- generating blackbox summaries from small source snippets;
- proposing gap primitives or adapter recipes;
- ranking candidate sessions/use cases.

Do not use Kimi/GLM to:

- rewrite full modules when primitives exist;
- ingest huge source trees directly;
- mark candidates as truth;
- bypass compiler checks.

The desired loop is:

```text
deterministic search -> compact planner/tool call if needed -> PlanDelta/recipe
  -> deterministic compiler/materializer -> tests/proofs -> report/export
```

The undesired loop is:

```text
user prompt -> coding harness reads many files -> model rewrites known logic
```

## Done Criteria

The loop is complete only when:

- AIDevObserver can run common tasks through deterministic or planner-selected
  primitive routes;
- thousands of source-backed primitive candidates exist or the factory can
  generate them repeatedly;
- search considers input/output edges and mutatable compatibility;
- planner context stays compact;
- route reports distinguish deterministic build, planner LLM, and coding harness
  contributions;
- adapters/runtime emitters create inspectable files for API, CLI, cloud
  function, Kubernetes, container, and local runtimes when applicable;
- behavior tests/proofs are emitted;
- public IDE reports exactly what used LLMs and what was deterministic;
- public/local visibility scopes are tested and visible in registry receipts;
- all generated/promoted records preserve the truth boundary.
