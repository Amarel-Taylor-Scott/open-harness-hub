# Primitive Database Agent Brief

**Purpose:** give another AI agent enough context to search for, design, create, and improve useful reusable primitives and primitive groups for the AIDevObserver / Teleon / OpenHubForAI ecosystem.

Copy this document into another coding agent when you want it to continue expanding the primitive database.

## Mission

We are building a massive searchable primitive database so AI coding agents do not waste tokens recreating capabilities that already exist.

The goal is not just many tiny functions. The goal is:

```text
User intent -> compact edge search -> reusable primitive or primitive group -> deterministic assembly -> proof -> searchable registry memory.
```

The LLM should only see the smallest useful contract:

```text
visible input edge + visible output edge + blackbox behavior + effects + proof status
```

It should not read every internal function or edge unless it asks for drill-down.

## Core Concepts

### Primitive

A primitive is a reusable capability with a clear blackbox contract.

Minimum useful fields:

```json
{
  "primitive_id": "prim:stable-id",
  "kind": "py.fn",
  "title": "Human readable title",
  "input_edge": "InputTypeOrEnvelope",
  "output_edge": "OutputTypeOrReceipt",
  "contract": {"input": "InputTypeOrEnvelope", "output": "OutputTypeOrReceipt"},
  "blackbox": {"does": "What it does without implementation detail."},
  "effects": [],
  "memory": "inline|artifact|external",
  "cache": "content_hash|policy_required|none",
  "runtime_targets": ["local.python", "container.python"],
  "proof_requirements": ["unit_test", "contract_test"],
  "candidate": true,
  "serves_truth": false
}
```

### Primitive Group

A primitive group is a larger first-class capability made from smaller primitives, adapters, templates, and deterministic workers.

Primitive groups are essential because they reduce the number of edges the LLM has to understand.

Example:

```text
RawRecordBatch+ImportPreparationPolicy -> PreparedRecordImport
```

This one visible group edge can hide:

```text
field normalization
explicit aliases
collision preservation
required-field validation
identity dedupe
deterministic sort
schema fingerprint
idempotency key
```

The group card should expose one visible input/output edge and keep member edges in `group_contract.hidden_member_edges`.

Minimum group card shape:

```json
{
  "primitive_id": "grp:domain.capability@1",
  "kind": "artifact.primitive_group",
  "title": "Prepare record import group",
  "input_edge": "RawRecordBatch+ImportPreparationPolicy",
  "output_edge": "PreparedRecordImport",
  "contract": {
    "input": "RawRecordBatch+ImportPreparationPolicy",
    "output": "PreparedRecordImport"
  },
  "group_contract": {
    "visible_input_edge": "RawRecordBatch+ImportPreparationPolicy",
    "visible_output_edge": "PreparedRecordImport",
    "hidden_member_edges": [
      "RecordFields->NormalizedFields",
      "RecordBatch+IdentityFields->DedupedRecordBatch"
    ]
  },
  "blackbox": {
    "does": "Prepare imported records in one deterministic group.",
    "llm_context_policy": "show_group_edge_first; reveal member edges only on drilldown"
  },
  "candidate": true,
  "serves_truth": false
}
```

## Current Local Registry Lanes

Generated edge cards:

```text
data/dev-intel/aidevobserver_edge_foundry/primitive_edge_cards.jsonl
```

Curated grouped primitive cards:

```text
data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl
```

Current grouped primitive code:

```text
src/teleon/primitives/groups.py
```

Current grouped primitive tests:

```text
tests/unit/test_teleon_primitive_groups.py
```

AIDevObserver searches both generated edge cards and curated group cards.

## What To Build

Prioritize primitives and groups that developers, data teams, operators, and business users repeatedly ask AI agents to recreate.

Good primitive-group categories:

- record import preparation
- file mutation with archive/manifest receipt
- API request validation + policy decision + persisted response
- browser extraction + table normalization + artifact export
- source discovery + dedupe + ranking + digest
- job description ingestion + skill extraction + role taxonomy mapping
- public procurement opportunity ingestion + NAICS/PSC extraction + deadline ranking
- GitHub repo scan + capability extraction + license gate
- PyPI/package scan + API surface extraction + edge cards
- n8n/Zapier workflow import + primitive route conversion
- Kaggle notebook/project analysis + pipeline primitive extraction
- log/session ingestion + action extraction + replay summary
- codebase scan + helper detection + reuse recommendation
- Kubernetes manifest validation + deployment readiness plan
- cloud function wrapper + request schema + response schema + local test harness
- SQL/CSV/Parquet data load + schema fingerprint + quality checks
- embedding/vector index build + retrieval proof
- policy/rule-pack evaluation + appeal/audit receipt

## Source Surfaces To Mine

Use source-backed public surfaces. Prefer official docs, package APIs, examples with licenses, and stable machine-readable feeds.

High-value surfaces:

- GitHub topics, trending repos, awesome lists, and source trees
- PyPI packages, package metadata, READMEs, examples, and typed APIs
- npm packages and workflow libraries
- official docs for common SDKs and APIs
- n8n templates, Zapier integrations, Make templates, Pipedream components
- Kaggle competitions, datasets, notebooks, and discussion posts
- Hugging Face models, datasets, Spaces, and papers
- YC AI directory, Product Hunt AI, Show HN, startup directories
- AI startup/tool directories and API docs
- developer-resource megarepos, algorithm repos, programming dictionaries
- USAJobs, OPM, SAM.gov, USASpending, Grants.gov, agency procurement pages
- NAICS/PSC/SIC datasets and crosswalks
- industry standards, compliance checklists, engineering runbooks
- public data catalogs, public APIs, government open data portals
- forums, RSS feeds, newsletters, and recurring engineering blogs
- non-English sources for common business/software workflows

Do not blindly copy code. Extract contracts, ideas, source refs, and implementation opportunities. Respect licenses and never republish restricted source.

## Search Strategy

For every source area, ask:

```text
What data enters?
What data leaves?
What deterministic transformations happen?
What side effects happen?
What proof would show this works?
Can this be grouped so the LLM sees fewer edges?
Can adapters make near-matches exact?
Can a deterministic worker build it without model codegen?
```

Use many search lenses:

```text
"how to build X"
"X checklist"
"X API reference"
"X examples"
"X template"
"X workflow"
"X open source"
"X data pipeline"
"X validation"
"X import export"
"X integration"
"X automation"
"X n8n"
"X zapier"
"X python package"
"X github"
"X schema"
"X benchmark"
"X public dataset"
```

Also search by role, industry, and object:

```text
role + task + input + output
industry + workflow + validation
department + report + data source
NAICS name + software workflow
government job title + recurring task
startup category + API workflow
```

## Primitive Generation Rules

Create source-backed or implementation-backed candidates only.

Do:

- keep `candidate=true` and `serves_truth=false` until promotion;
- include input/output edges;
- include side effects;
- include proof requirements;
- include source refs;
- include deterministic mutator options;
- prefer grouped primitives when a common route has many internal steps;
- write tests for implemented primitives;
- add small examples only when they prove the edge;
- keep LLM context compact.

Do not:

- create synthetic primitives with no source, code, or proof path;
- claim a primitive serves truth before proof and promotion;
- expose huge implementation context as the default search result;
- create one primitive per trivial line when a group edge is more useful;
- hide network, file, shell, database, or model-call effects;
- republish source from restricted references.

## Useful Edge Mutators

Mutators make near-matches usable without asking a coding agent to write glue.

Prioritize deterministic mutators:

- `map_sequence`: `A -> B` becomes `list[A] -> list[B]`
- `input_envelope_wrapper`: `A+B -> C` becomes `Envelope[A+B] -> C`
- `output_wrapper`: `A -> B` becomes `A -> Wrapped[B]`
- `field_rename`: explicit field aliasing
- `field_project`: keep required fields only
- `schema_validator_inserter`: add deterministic schema validation
- `type_cast`: declared scalar/path/string/dataclass casts
- `path_to_bytes`
- `bytes_to_text`
- `json_to_dataclass`
- `dataclass_to_json`
- `pagination_expander`
- `retry_wrapper`
- `cache_wrapper`
- `idempotency_wrapper`
- `artifact_materialize`
- `artifact_reference`
- `api_endpoint_wrapper`
- `cloud_function_wrapper`
- `kubernetes_job_wrapper`
- `pretooluse_hook_wrapper`
- `route_to_group_card`

Each mutator needs preconditions and proof obligations.

## Group Factory Pattern

When many primitives chain together, collapse them into a primitive group.

Process:

```text
1. Search primitive cards by requested input/output edges.
2. Build an exact edge route with deterministic graph search.
3. Insert deterministic adapters where allowed.
4. Prove the route with unit/contract tests.
5. Emit a group card with one visible input/output edge.
6. Store hidden member edges for drill-down.
7. Search the group card first next time.
```

Output:

```text
RoutePlan -> PrimitiveGroupCard
```

This is the main path to unlimited reusable groups without exploding LLM context.

## Quality Bar

A useful primitive or group should pass at least one of these:

- it is implemented locally and unit-tested;
- it is source-backed with clear API/docs references and proof plan;
- it maps to a common developer/business workflow;
- it reduces a multi-step LLM coding task to one deterministic edge;
- it has adapters/mutators that make it reusable across variants;
- it has a safe runtime target such as local Python, container Python, cloud function, Kubernetes job, or CLI.

Promotion requires stronger proof:

```text
source ref exists
license/policy reviewed
input contract validated
output contract validated
side effects declared
unit or smoke test passes
privacy boundary reviewed
runtime/resource profile declared
candidate remains serves_truth=false until promotion gate
```

## Example Tasks For Another Agent

Use these prompts:

```text
Search the provided source surfaces for recurring data import, validation, dedupe, and export workflows. Create 10 source-backed primitive group candidates with visible input/output edges, hidden member edges, source refs, mutators, and proof obligations.
```

```text
Mine PyPI packages in the web scraping, document parsing, CSV/Parquet, API validation, scheduling, and Kubernetes categories. Extract candidate primitive groups that hide multiple common steps behind one edge. Do not copy package code.
```

```text
Search n8n templates and Zapier app categories for common automation patterns. Convert them into primitive group candidates with trigger edge, action edge, effects, adapter options, and proof plan.
```

```text
Review USAJobs/SAM.gov/USASpending source surfaces and design primitive groups for job/opportunity ingestion, classification, NAICS mapping, deadline ranking, entity extraction, and alert generation.
```

```text
Read local source files and identify repeated internal routes that can be collapsed into primitive groups. Add tests and curated group cards for the strongest candidates.
```

## Expected Output Files

If implementing code:

```text
src/teleon/primitives/<domain>.py
tests/unit/test_teleon_<domain>_primitives.py
```

If adding curated group cards:

```text
data/dev-intel/aidevobserver_edge_foundry/curated_primitive_groups.jsonl
```

If adding source maps or discovery seeds:

```text
catalog/knowledge-packs/data/<source-map-name>/*.jsonl
docs/codex/<brief-name>.md
```

## Final Operating Rule

The best primitive database is not a pile of code snippets. It is a searchable graph of compact, typed, proofable capabilities.

Default to this:

```text
Make the LLM choose or design the route.
Make deterministic workers execute, adapt, test, persist, and summarize it.
Make grouped primitives hide complexity behind one reusable edge.
```
