# DeterministicBuilds.io Demand Surface

**Status:** proposed product/source surface  
**Truth boundary:** request records are demand signals only; `serves_truth=false` until proof and promotion.

## Purpose

`deterministicbuilds.io` should be a public, leaderboard-style surface for requests to move repeated LLM/agent behavior into deterministic, reusable components.

The simple public promise:

```text
Vote for the AI workflows you want made deterministic.
```

The internal architecture role:

```text
non-deterministic prompt / skill / agent loop / workflow
  -> public request record
  -> votes, examples, and proof requirements
  -> primitive opportunity
  -> candidate implementation
  -> proof bundle
  -> promoted deterministic primitive or template
```

## Why This Helps AIDevObserver

AIDevObserver detects when an agent is rebuilding known work. `DeterministicBuilds.io` creates the upstream demand queue for work that is not yet in the primitive database.

Example:

```text
Observer finding:
  Agent keeps writing custom CSV importers.

DeterministicBuilds request:
  "Make CSV import with schema validation, bad-row quarantine, and parquet emit deterministic."

Teleon/OpenHubForAI output:
  primitive/template family:
    acquire_csv -> validate_schema -> normalize_columns -> quarantine_bad_rows -> emit_parquet
```

This gives the ecosystem a public backlog of high-value deterministic conversions instead of relying only on internal guesses.

## What A Request Contains

Each request should be compact and contract-oriented:

```yaml
request_id: dbreq_csv_import_schema_quarantine
title: Deterministic CSV import with schema validation and quarantine
current_nondeterministic_surface:
  - repeated LLM-generated importer scripts
  - Claude/Cursor/Codex sessions that rebuild parser + validation + retry code
desired_output:
  kind: pipeline_template
  contract: FileArtifact>DatasetPublishReceipt
candidate_slots:
  - acquire FileArtifact>RawTableArtifact
  - validate RawTableArtifact>ValidatedTableArtifact
  - normalize ValidatedTableArtifact>NormalizedTableArtifact
  - quarantine InvalidRows>QuarantineArtifact
  - emit NormalizedTableArtifact>ParquetArtifact
proof_requirements:
  - schema_fixture_pass
  - malformed_csv_rejection
  - bad_row_quarantine_digest
  - deterministic_replay
  - source_attribution_gate
privacy_boundary: public_metadata_no_private_transcripts
serves_truth: false
```

## Leaderboard Signals

Rank requests by:

- votes from developers and teams;
- observed AIDevObserver findings that match the request;
- estimated token/context waste avoided;
- number of independent implementations already seen;
- availability of source evidence and fixtures;
- proof difficulty;
- launch/customer value.

Votes should affect priority, not truth. A popular request is not automatically a valid primitive.

## Accepted Build Path

```text
request accepted
  -> candidate primitive/template record
  -> source refs and fixtures attached
  -> deterministic implementation or route created
  -> benchmark/proof run
  -> VariationRecord/PlanLock if applicable
  -> promotion candidate
  -> serves_truth can flip only after proof/promotion
```

## Safety Rules

- Do not publish raw private AI transcripts.
- Do not copy proprietary prompts, skills, or source code into request text.
- Treat user-submitted examples as metadata until rights and redaction pass.
- Require source attribution for public examples.
- Keep accepted builds candidate-only until proof.
- Allow private/team-only requests for sensitive workflows.

## Relationship To The Ecosystem

- **AIDevObserver:** detects repeated reinvention and routes findings to matching requests.
- **Teleon:** compiles accepted requests into deterministic primitive/template routes.
- **OpenHubForAI:** stores request records, primitive opportunities, proof records, and promoted components.
- **Baltor:** provides verified context packs when a request needs trusted background context.
- **AI Done Right:** uses the surface as a public proof of the mission: less repeated generation, more reusable capability.

## First Request Families

Start with requests that map to common AI coding sessions:

- CSV/Excel ingestion with schema validation.
- Web scraper with provenance and source crosscheck.
- Document-to-JSON extraction with source spans.
- Company/entity enrichment with confidence and cache policy.
- Support ticket classifier with label schema and route policy.
- Backend API policy endpoint with idempotent persistence.
- Frontend component quality gate.
- Cloud function/Kubernetes deployment checklist.
- Safe Python refactor/proof pipeline.
- Kaggle-style tabular baseline pipeline.

## Source Map Row

The source surface is registered as:

```text
surface-deterministicbuilds-leaderboard
```

It should emit:

- `deterministic_build_request`
- `primitive_bounty`
- `proof_backlog`
- `llm_to_deterministic_route`
- `skill_to_primitive_conversion`
- `leaderboard_vote_signal`
- `accepted_build_proof_ref`

All downstream records remain `serves_truth=false` until proof and promotion.
