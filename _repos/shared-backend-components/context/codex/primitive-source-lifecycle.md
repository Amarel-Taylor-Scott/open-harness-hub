# Primitive Source Lifecycle

**Status:** global operating model  
**Scope:** Teleon, OpenHubForAI, Baltor, AIDevObserver, AI Done Right, and future domain surfaces  
**Truth boundary:** every row is candidate evidence until proof and promotion.

## Purpose

Primitive generation is a platform capability, not an AIDevObserver-specific capability.

AIDevObserver is one important source of signals because it observes AI coding sessions and finds reinvention. But the lifecycle must be global because every system depends on the same ability to convert public and private evidence into reusable primitive records.

The global loop is:

```text
public / private / first-party source evidence
  -> source candidate
  -> primitive opportunity or primitive draft
  -> ranking
  -> digest
  -> implementation backlog
  -> proof plan
  -> compact search card
  -> vector row
  -> promotion candidate only after proof
```

The model-assisted version of this loop is defined separately in:

```text
_repos/shared-backend-components/context/codex/global-multimodel-primitive-foundry.md
```

That contract lets Codex, GLM 5.2 through Ollama, Kimi Code 2.7 through
Ollama, browser capture tools, and deterministic gates cooperate without
letting any model output become registry truth by itself.

## Source Inputs

The lifecycle can ingest candidate rows from:

- AIDevObserver review findings and accepted/reused/dismissed outcome memory;
- first-party repo symbols, docs, scripts, workflows, tests, examples, and Claude project packs;
- package registries such as PyPI metadata;
- public repo metadata from GitHub/GitLab;
- Kaggle competitions, datasets, and notebooks as metadata and task evidence;
- n8n, GitHub Actions, Terraform, MCP, OpenAPI, and workflow registries;
- official documentation and open-licensed OER sources;
- DeterministicBuilds.io request/vote/bounty/proof-backlog records;
- benchmark and proof records.
- AI startup/product directories, builder launch feeds, newsletters, VC market
  theses, open-source trend directories, and AI app demo hubs, documented in
  `docs/codex/ai-startup-source-surface-discovery-map.md`.
- official industry taxonomies such as NAICS, expanded into candidate-only
  multilingual source scopes by `scripts/naics_primitive_scope_generator.py`.
- developer primitive feedstock such as algorithm repositories, data-structure
  catalogs, programming dictionaries, software engineering resource indexes,
  job-role taxonomies, and public job-board directories.
- federal opportunity and award sources such as SAM.gov, USAspending, and
  Grants.gov, treated as procurement metadata before any solicitation or
  attachment body is fetched.
- generated first-principles business-operation scopes from
  `scripts/business_operation_scope_generator.py`, crossing operation atoms,
  functions, roles, systems, data objects, geographies, and technologies.
- generated developer-resource search leads from
  `developer_resources_10000_rows.md`, reviewed in
  `docs/codex/developer-resource-primitive-review.md` and wired through the
  design in `docs/codex/developer-resource-foundry-design.md`.
- government workforce and procurement source maps, including USAJobs,
  USAJobs developer APIs, OPM/agency career surfaces, SAM.gov, USAspending,
  Grants.gov, federal/state/local bid portals, and contractor supplier pages,
  summarized in
  `docs/codex/government-workforce-and-procurement-source-map.md`.
- hook-enforced local memory frameworks such as CreativLogic's Staged Memory
  System, used as source evidence for layered context loading, local markdown
  memory indexes, context-injection hooks, and deterministic guard hooks. See
  `docs/codex/hook-enforced-staged-memory-system.md`.

Public or third-party source rows stay metadata-only until rights, attribution, privacy, and redaction gates pass.

## Multilingual Source Discovery Scope

The context foundry includes curated multilingual search scopes in:

```text
catalog/knowledge-packs/data/aidevobserver-multilingual-search-scopes/scopes.jsonl
```

These rows expand the primitive-foundry backlog across multiple languages and
provider types without storing raw third-party content. Each row becomes:

- a `source_candidate` with multilingual queries and provider lanes;
- a synthetic AIDevObserver session spec for replay/demo generation;
- one or more candidate primitive opportunities with compact contracts.

Current scope families include public dataset indexes, Kaggle competitions and
notebooks, agentic workers, embedding/vector/RAG systems, n8n workflows,
cloud/Kubernetes/serverless runtimes, package reuse across PyPI/npm, backend
API/service patterns, frontend app microsurfaces, data engineering, data
science/MLOps, LLM app frameworks, MCP tools/connectors, CI/CD/IaC, observability
and evals, security/DevSecOps, browser automation, industry SaaS microsurfaces,
AI startup/builder ecosystem sources, stock-trading/market-data workflows,
employment-agency/staffing workflows, and NAICS-wide industry scopes.
The newer source families add algorithm/data-structure primitives,
programming-concept vocabulary, developer/job-role taxonomies, federal
contracting opportunities, federal award intelligence, grants, and procurement
proposal workflows.

NAICS scope generation is separate from the base curated search scopes:

```bash
python3 scripts/naics_primitive_scope_generator.py --csv path/to/naics.csv
python3 scripts/naics_primitive_scope_generator.py --self-test
```

Generated rows are consumed by the context foundry as multilingual search
scopes. They create source candidates, synthetic session specs, and primitive
opportunities only. They do not fetch third-party source bodies, create
implementation truth, or promote records.

NAICS-specific third-party repositories are tracked as source surfaces for CSV,
JSON API, hierarchy-generation, crawler, and SIC-crosswalk discovery. They
should feed `naics_csv_loader`, `naics_json_api_adapter`,
`naics_hierarchy_generator`, `sic_to_naics_crosswalk`, and
`naics_search_scope_generator_input` candidates only until source licenses,
revision years, official provenance, and proof gates are attached.

Algorithm and programming-concept sources should be converted into edge
metadata before code. A valid candidate needs at least a label, contract shape,
blackbox behavior, complexity fields when known, source ref, license status,
test/proof obligations, and mutator options. The implementation is copied or
rewritten only after license and equivalence proof pass.

Federal contracting sources are high-value because they turn public demand
signals into concrete workflow primitives: opportunity ingest, RFP
classification, NAICS/PSC matching, set-aside checks, compliance extraction,
proposal assembly, deadline monitoring, award enrichment, and vendor/agency
market intelligence. These rows are still candidate evidence, not served truth.

First-principles business-operation scopes ask the same primitive questions
across every business area:

```text
What is being communicated or transferred?
What is being stored or remembered?
What is being transformed or computed?
What is being decided, routed, scheduled, allocated, or approved?
What evidence proves the action happened correctly?
```

The generator currently exposes a deterministic cross-product of operation
atoms, functional areas, positions, systems, data objects, geographies, and
technologies:

```bash
python3 scripts/business_operation_scope_generator.py --max-rows 5000
python3 scripts/business_operation_scope_generator.py --max-rows 0
python3 scripts/business_operation_scope_generator.py --offset 5000 --max-rows 5000
python3 scripts/business_operation_scope_generator.py --self-test
```

`--max-rows 0` means the full generated search grid. Smaller offset windows are
the normal long-running-loop mode so multiple workers can cover the space
without duplicating work.

The matching non-live search seeds live in:

```text
catalog/knowledge-packs/data/aidevobserver-source-discovery-search-seeds/search-topics.jsonl
```

Those seeds keep the loop useful when live GitHub/Kaggle/RSS/browser fetching is
disabled. Live fetching must remain behind explicit flags and source-policy
gates.

Developer-resource rows should be collapsed before source search. A generated
row such as `Topological sort - data engineering` is a lead for one normalized
capability family, not a primitive by itself. The expected path is:

```text
generated row -> normalized concept -> source search -> edge card -> proofable primitive draft
```

Government workforce and procurement sources are a separate high-value source
family. USAJobs role and series pages should feed role/task/skill edge cards,
application workflow templates, and benchmark fixtures. SAM.gov, USAspending,
Grants.gov, and state/local bid portals should feed opportunity-ingest,
solicitation-classification, NAICS/PSC matching, set-aside eligibility,
proposal-compliance, deadline-monitoring, and vendor-fit primitives. These rows
remain metadata and candidate extraction outputs until source terms, privacy,
source-span, and proof gates pass.

The lifecycle also packages a quality-filtered subset of AIDevObserver
edge-foundry cards into the global digest/search/vector artifacts. These cards
are source-backed records extracted from real code, docs, schemas, workflows,
notebooks, manifests, and structured artifacts. By default the bridge includes
public-demo-safe cards with known source refs, contract edges, blackbox behavior,
deterministic mutator options, runtime targets, and quality score >= 70. Private
edge-foundry cards and generic JSONL materialization rows are opt-in.

## Row Families

### Source Candidate

```text
source_candidate
```

Where the evidence came from. Examples: PyPI package metadata, GitHub repo metadata, first-party repo symbol, Kaggle competition metadata, DeterministicBuilds request.

### Primitive Opportunity

```text
primitive_opportunity
```

A useful capability idea that is not source-backed enough to implement or promote yet.

### Primitive Draft

```text
primitive_draft
```

A candidate primitive with stronger source evidence, contract fields, effects, proof requirements, and source refs. Still `serves_truth=false`.

### Lifecycle Digest

```text
primitive_lifecycle_digest
```

A compact, ranked, source-linked summary of a primitive candidate or opportunity. This is the row humans, agents, and routing systems should inspect first.

### Implementation Backlog

```text
primitive_implementation_backlog
```

The work queue for turning opportunities into deterministic implementations or proving existing source-backed candidates.

### Search Card

```text
primitive_search_card
```

A compact retrieval card with label, contract, effects, memory/cache, source state, and keywords.

### Vector Row

```text
primitive_lifecycle_vector
```

A deterministic lexical vector row for staging search and dedupe. It is not production semantic-search readiness and must not bypass promotion gates.

## Implementation State

Lifecycle digests classify rows into:

```text
implementation_backlog
existing_source_ref_candidate
source_backed_candidate_needs_proof
```

Meaning:

- `implementation_backlog`: source demand exists, but the deterministic implementation still needs to be found or built.
- `existing_source_ref_candidate`: a first-party/source-backed implementation candidate exists, but still needs proof.
- `source_backed_candidate_needs_proof`: stronger candidate evidence exists, but proof/promotion still blocks truth serving.

## Script

Run:

```bash
python3 scripts/primitive_source_lifecycle.py
```

Default input:

```text
data/dev-intel/aidevobserver_context_foundry/
```

Default output:

```text
data/dev-intel/primitive_source_lifecycle/
```

Private local AI-session derivatives are excluded by default from the global
output. Include them only for private/local runs:

```bash
python3 scripts/primitive_source_lifecycle.py --include-private-local-sessions
```

Edge-foundry bridge controls:

```bash
python3 scripts/primitive_source_lifecycle.py --edge-foundry-limit 5000
python3 scripts/primitive_source_lifecycle.py --edge-foundry-limit 0
python3 scripts/primitive_source_lifecycle.py --skip-edge-foundry
python3 scripts/primitive_source_lifecycle.py --include-private-edge-foundry
python3 scripts/primitive_source_lifecycle.py --include-edge-jsonl-records
```

`--edge-foundry-limit 0` means all eligible edge-foundry rows. The default keeps
the lifecycle useful and compact by selecting the highest-quality source-backed
edge candidates first.

Artifacts:

```text
primitive_lifecycle_digests.jsonl
primitive_implementation_backlog.jsonl
primitive_search_cards.jsonl
primitive_vector_export.jsonl
manifest.json
summary.md
```

After lifecycle packaging, generate route-level benchmark fixtures from the
search cards:

```bash
python3 scripts/primitive_route_fixture_foundry.py
python3 scripts/primitive_route_fixture_foundry.py --self-test
python3 scripts/primitive_route_fixture_verifier.py
python3 scripts/primitive_route_fixture_verifier.py --self-test
python3 scripts/runtime_adapter_coverage_report.py
python3 scripts/runtime_adapter_coverage_report.py --self-test
```

This emits:

```text
data/dev-intel/primitive_route_fixtures/route_fixtures.jsonl
data/dev-intel/primitive_route_fixtures/candidate_bundles.jsonl
data/dev-intel/primitive_route_fixtures/manifest.json
data/dev-intel/primitive_route_fixtures/summary.md
data/dev-intel/primitive_route_fixtures/verification_report.json
data/dev-intel/primitive_route_fixtures/verification_results.jsonl
data/dev-intel/runtime_adapter_coverage/runtime_adapter_coverage_report.json
data/dev-intel/runtime_adapter_coverage/runtime_adapter_fixtures.jsonl
data/dev-intel/runtime_adapter_coverage/runtime_adapter_gaps.jsonl
```

Fixture families:

- `direct_reuse`: one source-backed primitive should be reused directly.
- `mutator_reuse`: one primitive should be reused through a deterministic
  mutator such as `map_sequence`, `output_wrapper`, or `schema_validator_inserter`.
- `edge_chain`: two source-backed primitives compose because the first output
  edge exactly matches the second input edge.

The fixtures are benchmark/planning artifacts only. They do not execute source
and do not promote primitives.

The verifier checks that each fixture and CandidateBundle remains candidate-only,
that every referenced component exists in lifecycle search cards, that direct,
mutator, and edge-chain contracts line up, and that a small sampled set of
fixtures can retrieve its expected primitive IDs through the AIDevObserver
registry adapter. Retrieval sampling is deliberately bounded so daemon ticks
verify search readiness without scanning every fixture prompt against the full
edge corpus.

Runtime adapter coverage is tracked separately because source-backed primitive
edges are only broadly useful when they can be deterministically emitted into
common execution surfaces. The coverage report checks runtime target counts and
required wrapper mutators for `cloud.function.http`, `k8s.job`,
`k8s.deployment`, `k8s.cronjob`, API endpoint wrappers, and CLI wrappers.
Missing required runtime mutators block the coverage report. Low counts become
candidate backlog rows in `runtime_adapter_gaps.jsonl`, not promotion failures.
The generated runtime adapter fixtures are candidate-only prompts that test
whether a route can emit an existing primitive into a runtime without asking a
coding harness to rewrite the primitive.

Proof:

```bash
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/primitive_route_fixture_foundry.py --self-test
python3 scripts/primitive_route_fixture_verifier.py --self-test
python3 scripts/runtime_adapter_coverage_report.py --self-test
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
```

AIDevObserver compatibility wrapper:

```bash
python3 scripts/aidevobserver_primitive_lifecycle.py --self-test
```

## Current Boundary

The lifecycle does not:

- scrape raw third-party source code;
- copy copyrighted textbook content;
- download package archives;
- implement primitives automatically;
- promote primitives;
- claim vector search is production-ready.

It does:

- preserve source refs;
- compute stable digests;
- rank candidate work;
- create implementation backlog rows;
- create compact search cards;
- emit deterministic staging vectors;
- carry input/output edges, blackbox behavior, deterministic mutator options,
  runtime targets, blocking keys, and source visibility into search cards;
- keep `serves_truth=false`.

Default privacy posture:

- public and metadata-gated source rows are included;
- first-party repo primitive candidates are included;
- private local Claude/Codex session derivatives are excluded unless explicitly
  requested with `--include-private-local-sessions`.

## Ownership Split

- **OpenHubForAI** stores and indexes the global primitive/source/component records.
- **Teleon** compiles and proves deterministic primitive/template routes.
- **AIDevObserver** supplies AI-session reinvention signals and consumes reuse cards.
- **Baltor** supplies verified context packs and governs context truth.
- **DeterministicBuilds.io** supplies public demand signals and proof backlog priority.
- **AI Done Right** is the portfolio/mission surface explaining why this loop matters.

The pipeline is global because every product surface becomes stronger when the primitive database improves.
