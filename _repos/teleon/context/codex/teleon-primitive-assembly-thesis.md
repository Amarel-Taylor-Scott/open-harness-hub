# Teleon Primitive Assembly Thesis

The core product idea is not "LLM writes all the code." It is:

```text
User capability + context + guardrails
  -> retrieve proven primitives by contract/search
  -> assemble a graph of primitive calls and adapters
  -> run, log, verify, tune, version
  -> promote only the new verified primitives
```

Most code an AI agent writes has already been written before: loops, retries, schema validation, JSON
logging, scrapers, batching, dispatch, adapters, rate limits, parsers, transforms, and common data
structures. Teleon should avoid spending tokens regenerating those blocks. The agent should mostly manage
the edges between known blocks.

## The Product Shift

The user defines a capability, for example:

```text
Scrape maximum interest rates for all countries and sub-jurisdictions.
```

Teleon should turn that into a compact graph plan:

```text
Input
  -> primitive.web.fetch_with_retry
  -> primitive.scrape.extract_tables
  -> primitive.normalize.country_subjurisdiction_rates
  -> primitive.validate.maximum_interest_rate_schema
  -> Output
```

The model output becomes a graph and contract plan, not a large source-code dump. Fresh generated code is
reserved for missing primitives or thin adapters.

## Primitive Records

Each primitive needs enough metadata to be searchable, graphable, enrichable, and verifiable:

- purpose and problem solved;
- input contract and output contract;
- dependencies, side effects, execution surface;
- guardrails and failure modes;
- cost/latency profile;
- license and deployment constraints;
- proof commands and proof history;
- JSON log schema;
- examples and search text;
- graph edges to adjacent primitives, requirements, and capabilities.

This makes a primitive closer to a governed capability module than a loose helper function.

## Execution Loop

1. Intake capability, domain context, input/output surfaces, guardrails, and infrastructure constraints.
2. Retrieve primitives with hybrid search: semantic text, exact contract fields, graph neighborhood,
   proof history, cost, latency, license, and deployment fit.
3. Build a graph where edges map outputs to inputs and carry validation, retry, rate-limit, privacy, and
   logging constraints.
4. Generate only missing adapter code or candidate primitives.
5. Execute with structured JSON logs.
6. Tune variants under guardrails: lower cost, lower latency, fewer tokens, better reliability.
7. Store baseline and variants in a git-like graph repository.
8. Promote new primitives only after deterministic proofs, execution evidence, license metadata, and
   required owner/human approval.

## Cheap Primitive Mutation

Teleon should prefer deterministic primitive mutation before source regeneration. The first library for
that is `_repos/teleon/backend/src/teleon/synthesis/primitive_variations.py`.

Phase 1 mutations are intentionally boring and reliable:

- infer a candidate primitive contract from a callable signature;
- lift a scalar callable to `scalar_or_sequence` input without rewriting business logic;
- wrap an output into a named object field when the next primitive expects a different output surface;
- compose ordered primitive contracts into a linear graph with `maps_output_to_input` edges;
- execute that graph with structured JSON logs.

Later mutations should include model downshift, browser-to-deterministic extraction, local-vs-API
implementation swaps, retry/cache/rate-limit policy nodes, and bounded parallel batch execution.

This is the practical way to "mutate primitives cheaply": first change the contract and graph wrapper,
then prove the behavior. Source codemods are a later, higher-risk optimization.

## Input / Output Management

Input and output are not loose prose. Every primitive needs:

- `input_contract`;
- `output_contract`;
- `guardrails`;
- `dependencies`;
- `execution_surface`;
- `logs_schema`;
- `proofs`;
- `graph_edges`.

The graph edge is the adapter: it states how one primitive's output contract maps to the next primitive's
input contract. If the contracts do not line up, Teleon should insert a small adapter primitive rather
than rewriting either side.

## Hybrid Primitive Search

Primitive retrieval is not a single semantic/vector lookup. It is a staged candidate matcher:

1. Cheap blocking: exact id/name, keyword overlap, labels/tags/capability facets, input/output field
   overlap, graph-neighborhood overlap, and lexical embedding similarity.
2. Contract compatibility: classify whether the primitive's `input_contract` and `output_contract` can
   chain directly into the requested graph.
3. Deterministic mutation awareness: detect when scalar-to-sequence, output-field wrapping,
   field-renaming with an explicit map, retry/cache/rate-limit policy nodes, model downshift,
   browser-to-deterministic extraction, or local/API swaps could make the primitive fit without
   regenerating core business logic.
4. Non-deterministic mutation lane: if topic evidence is strong but contracts still do not line up,
   produce a generated-adapter candidate only. It stays `serves_truth=false` and cannot promote without
   proofs, logs, provenance/license metadata, and owner/human review where needed.

The implemented floor is `_repos/teleon/backend/src/teleon/registry/primitive_match.py`, governed by
`_repos/shared-backend-components/architecture/primitive_hybrid_search_contracts.json` and
`_repos/shared-backend-components/scripts/check_primitive_hybrid_search.py`. It returns one of four fit classes:
`exact_match`, `deterministic_edit_match`, `nondeterministic_edit_match`, or `incompatible`. This lets
the graph planner retrieve primitives that match now, primitives that match after cheap adapters, and
primitives that are only worth sending to a generated candidate edit lane.

## CI/CD, BYOK, Marketplace, And Control

Enterprise adoption is not won by token savings alone. The control plane has to support:

- source export into customer repos;
- package/private-service/third-party-API deployment modes behind the same contract;
- BYOK and model/provider policy for LLM-backed primitives;
- structured logs and proof records that CI/CD can consume;
- SBOM/provenance hooks and license/dependency metadata;
- rollback through a git-like graph variation store;
- local/self-hosted alternatives for customers that do not want opaque external APIs.

Marketplace primitives make sense for specialized or proactively maintained capabilities, but they must be
contract-compatible implementations, not black boxes. The customer needs the code/proof posture for local
primitives and the dependency/security posture for hosted/API primitives.

## Relation To Current Repo Systems

- `_repos/shared-backend-components/architecture/teleon_primitive_assembly_thesis.json` stores this as a machine-readable contract.
- `_repos/shared-backend-components/architecture/teleon_primitive_variation_contracts.json` stores the mutation/variation rules.
- `_repos/shared-backend-components/architecture/teleon_codegen_contracts.json` governs generated code when a new adapter or primitive is
  actually needed.
- `_repos/teleon/backend/src/teleon/synthesis/primitive_blocks.py` already provides scalar/batch, bounded-loop, dispatch, and
  candidate-envelope primitives.
- `_repos/teleon/backend/src/teleon/synthesis/primitive_variations.py` provides deterministic primitive contracts, scalar-to-batch
  wrappers, output adapters, graph composition, and JSON execution logs.
- `pyprefix` makes generated and existing Python symbols graphable with long context-rich names.
- `repo_code_inventory` and `repo_line_review_loop` produce the full file/symbol/reference/import/edge
  evidence base.
- `hybrid_repo_review_pipeline` turns deterministic findings and graph context into LLM review packets
  without letting LLM prose serve as truth.

## Why This Matters

This is more than a codegen optimization. It changes the programming unit from "source text" to
"verified primitive plus graph edge." That reduces token spend, improves blast-radius analysis, makes
reuse measurable, and lets Teleon support local code, private services, and third-party APIs under the
same input/output contract model.
