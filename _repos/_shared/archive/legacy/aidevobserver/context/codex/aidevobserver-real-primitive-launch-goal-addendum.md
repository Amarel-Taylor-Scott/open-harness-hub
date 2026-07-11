# AIDevObserver Real Primitive And Launch Goal Addendum

**Status:** candidate operating plan  
**Truth boundary:** `serves_truth=false` until proof and promotion.

## Purpose

This addendum sharpens the context-foundry goal for real launch work.
AIDevObserver should prefer real-source primitive extraction over synthetic
primitive generation.

Synthetic material is still useful for demos, fixtures, negative controls, and
privacy-preserving derivatives. It must not become a primitive record unless it
is explicitly marked as a synthetic fixture and excluded from trusted registry
promotion.

## Core Rule

```text
real source evidence -> primitive candidate -> proof bundle -> promotion
```

Do not create trusted primitive records from imagination. If a capability has no
source evidence yet, create a `primitive_opportunity`, not a `primitive_draft`.

Acceptable source evidence includes:

- first-party repo symbols, scripts, docs, workflows, tests, and examples;
- opt-in local AI coding session derivatives with private text removed;
- public GitHub metadata and licensed public code references;
- package registry metadata, CLIs, OpenAPI specs, MCP servers, and tool schemas;
- Kaggle competitions/datasets/notebooks as attributed public project evidence;
- n8n/workflow exports only when license and attribution are compatible;
- OpenHubForAI catalog records, benchmark records, and proof artifacts;
- user-accepted AIDevObserver findings and dismissed negative memory.

## Primitive Creation Pipeline

For each loop turn, prioritize moving at least one source-backed capability
through the global primitive source lifecycle:

1. **Discover source:** find a repo symbol, workflow, project pattern, package
   API, MCP/tool schema, benchmark, or accepted finding.
2. **Record provenance:** store source family, URL or repo-relative ref, license
   status, redaction status, source digest, and attribution handle.
3. **Classify capability:** helper, template, workflow, adapter, extractor,
   validator, model route, media transform, eval, proof, or context pack.
4. **Infer contract:** input, output, effects, memory policy, cache policy,
   runtime, privacy boundary, and failure modes.
5. **Dedupe:** compare against existing catalog, primitive drafts, accepted
   findings, and negative memory.
6. **Emit candidate:** write a candidate-only primitive draft with
   `serves_truth=false`, source refs, readiness, trust, proof requirements, and
   remix options.
7. **Attach examples:** generate a demo/replay only as a derivative view of the
   source-backed route, not as the source of truth.
8. **Benchmark:** add or update a fixture that expects the primitive/source ref
   to be found.
9. **Prove:** run deterministic checks, privacy scans, source-ref metrics, and
   any domain proof.
10. **Queue promotion:** create a promotion candidate only when license,
    redaction, contract, proof, and benchmark gates pass.

The lifecycle is not AIDevObserver-specific. AIDevObserver contributes AI-session
signals and consumes reuse cards, but digesting, implementation backlog,
summaries, search cards, and vector rows are global OpenHubForAI/Teleon
primitive infrastructure.

Global lifecycle command:

```bash
python3 scripts/primitive_source_lifecycle.py
```

## Source Connector Backlog

Build connectors in this order because each one directly improves launch value:

1. local repo symbol/docs/script/workflow indexer;
2. accepted/dismissed outcome memory connector;
3. primitive draft and template registry search;
4. GitHub metadata search with no raw source publication by default;
5. package registry and CLI/schema discovery;
6. MCP server/tool schema registry discovery;
7. OpenAPI/GraphQL schema ingestion;
8. Kaggle metadata/project-pattern discovery;
9. n8n/GitHub Actions/workflow import and distillation;
10. media/audio/video pipeline component registry ingestion;
11. benchmark/proof record search;
12. Baltor verified context-pack lookup.

The current source-surface map now splits the broad package/repo/document
space into explicit acquisition lanes:

- PyPI JSON metadata and PyPI Simple/Index distribution metadata;
- GitHub and GitLab public project metadata;
- GitHub Actions Marketplace and Terraform Registry workflow/IaC metadata;
- Python, cloud-native, and common framework official documentation;
- OpenStax/Open Textbook Library style OER sources for open-licensed learning
  material only;
- DeterministicBuilds.io-style request, vote, bounty, and proof-backlog
  records for moving repeated LLM/agent behavior into deterministic primitives.

Commercial coding textbooks are not a raw ingestion source. They can provide
metadata-level task inspiration only unless rights are explicitly granted. Use
open-licensed OER and official docs for source-backed primitive candidates.

Deterministic build requests are demand signals, not truth. They may raise
priority for a primitive family, but request popularity never bypasses license,
redaction, contract, proof, PlanLock, or promotion gates.

Proof:

```bash
python3 scripts/check_aidevobserver_source_acquisition_surfaces.py --self-test
```

Every connector must declare:

- enabled/disabled default;
- privacy boundary;
- license/provenance fields;
- redaction behavior;
- candidate output shape;
- proof command or self-test;
- failure mode when credentials or network access are absent.

## Launch Systems To Build

AIDevObserver launch requires more than examples. Keep advancing these systems:

- one packaged install path first: CLI or Claude Code MCP;
- Review UI with example picker, upload/paste, source-ref cards, and outcomes;
- outcome persistence across reloads/workspaces;
- local registry connector wired to review enrichment;
- primitive/template registry search endpoint;
- benchmark harness with source-ref top-1/top-3 accuracy;
- privacy/redaction scans for transcripts, paths, secrets, and PII;
- stable deployment path beyond temporary tunnel demos;
- backend health checks and rollback plan;
- auth/workspace boundaries before team use;
- billing/metering only after real usage paths work;
- docs for developer setup and manager reporting;
- launch readiness contract updated whenever gates change.

## Launch Readiness Gates

Do not call AIDevObserver launch-ready until these are true:

- at least one install path works end to end from fresh setup;
- a user can review a real or uploaded session and get useful source refs;
- findings can be accepted, reused, dismissed, and used as future memory;
- local registry enrichment is opt-in, privacy-safe, and benchmarked;
- primitive candidates are source-backed or explicitly opportunity-only;
- synthetic demos are labeled and never treated as real transcripts;
- all candidate records remain `serves_truth=false`;
- proof commands pass for review, examples, local service, connector, benchmark,
  launch readiness, and context-foundry loop;
- no raw private transcript text, local paths, secrets, or PII appear in public
  docs, examples, fixtures, or candidate rows.

## Work Selection Bias

When choosing the next loop action, prefer in this order:

1. real source connector or source-backed primitive candidate;
2. benchmark/source-ref precision improvement;
3. install/setup path that makes alpha use real;
4. review UI improvement that exposes source refs and outcomes;
5. privacy/proof check that prevents unsafe publication;
6. synthetic demo only when it is needed to show a source-backed route.

## Explicit Anti-Pattern

Avoid this:

```text
invent primitive -> invent session -> invent proof -> call it registry value
```

Use this instead:

```text
observe source -> derive candidate -> prove behavior -> promote later
```
