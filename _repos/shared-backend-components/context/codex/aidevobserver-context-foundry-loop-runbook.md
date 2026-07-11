# AIDevObserver Context Foundry Loop Runbook

Date: 2026-06-28

## Purpose

The context foundry loop continuously turns source surfaces, public project evidence, and opt-in local AI coding sessions into candidate-only material for:

- more realistic AIDevObserver examples;
- long synthetic sessions for large applications;
- source-backed primitive drafts with contracts and proof requirements;
- primitive opportunities when source evidence is not yet sufficient;
- input/output edge cards, deterministic mutator options, adapter recipes, and
  runtime emitter candidates for common developer tasks;
- registry memory candidates that can later be reviewed, tested, and promoted.

It does not promote anything. It creates candidate records only.

```text
source surface or local session
  -> candidate source record
  -> source-backed primitive draft or opportunity record
  -> input/output edge card + mutator/adapter affordances
  -> synthetic session spec / demo view
  -> compact planner/search card
  -> deterministic materializer/test/runtime wrapper when selected
  -> proof/promotion queue later
```

## Script

Top-level primitive-foundry daemon:

```bash
python3 scripts/start_aidevobserver_primitive_foundry_daemon.py --interval 3600 --max-ticks 0
```

The launcher uses `systemd-run --user` when available and mirrors the service
MainPID into `.agent/aidevobserver/primitive-foundry-daemon.pid`. This is the
durable path for Codex-launched loops.

Use the foreground daemon directly only when an agent should actively supervise
the process output in the current terminal.

One proof-gated daemon tick:

```bash
python3 scripts/aidevobserver_primitive_foundry_daemon.py --once
```

The daemon is now the preferred agentic loop. It calls the context foundry,
regenerates edge cards from real source/code/structured artifacts, runs focused
proof checks, smoke-tests registry retrieval across developer task families,
and appends receipts. The context foundry remains the source/use-case/session
sub-loop:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py
```

Pasteable Codex goal command:

```text
_repos/aidevobserver/context/codex/aidevobserver-context-foundry-goal-command.md
```

Longer Codex goal prompt/reference:

```text
.codex/prompts/aidevobserver-context-foundry-goal.md
```

Real-source primitive and launch bias: inlined below in this runbook (see "Real-Source Primitive And Launch
Bias"). The former `aidevobserver-real-primitive-launch-goal-addendum.md` is archived for lineage under
`_repos/_shared/archive/legacy/aidevobserver/`.

Global primitive source lifecycle:

```text
_repos/shared-backend-components/context/codex/primitive-source-lifecycle.md
```

Global multi-model primitive foundry:

```text
_repos/shared-backend-components/context/codex/global-multimodel-primitive-foundry.md
```

Deterministic build demand-signal surface:

```text
_repos/shared-backend-components/context/codex/deterministicbuilds-demand-surface.md
```

Claude-style project integration template:

```text
_repos/aidevobserver/context/codex/aidevobserver-claude-project-integration-template.md
```

Output directory:

```text
data/dev-intel/aidevobserver_context_foundry/
data/dev-intel/aidevobserver_edge_foundry/
data/dev-intel/aidevobserver_primitive_foundry_daemon/
.agent/aidevobserver/primitive-foundry-daemon.pid
.agent/aidevobserver/primitive-foundry-daemon.log
```

Files:

```text
source_candidates.jsonl
synthetic_session_specs.jsonl
primitive_drafts.jsonl
candidate_rankings.jsonl
loop_ledger.jsonl
primitive_edge_cards.jsonl
manifest.json
summary.md
latest_status.json
```

The global primitive lifecycle consumes these rows and writes digest, backlog,
summary, search-card, and vector artifacts under:

```text
data/dev-intel/primitive_source_lifecycle/
```

Run:

```bash
python3 scripts/primitive_source_lifecycle.py
```

`primitive_drafts.jsonl` is currently a compatibility file name. Rows inside it
must be inspected by `record_type`:

```text
primitive_opportunity = useful capability idea still missing source evidence
primitive_draft       = source-backed candidate ready for proof review
```

Every record is candidate-only:

```json
{"serves_truth": false, "trust": "candidate"}
```

## Proof

```bash
python3 scripts/aidevobserver_primitive_foundry_daemon.py --once --skip-observer-self-test
python3 scripts/aidevobserver_context_foundry_loop.py --self-test
```

Related AIDevObserver replay and benchmark proofs:

```bash
python3 scripts/aidevobserver_project_scaffold.py --self-test
python3 scripts/check_aidevobserver_example_sessions.py --self-test
python3 scripts/check_aidevobserver_session_benchmark.py --self-test
python3 scripts/check_aidevobserver_launch_readiness.py --self-test
python3 scripts/check_aidevobserver_local_registry_connector.py --self-test
python3 scripts/check_aidevobserver_source_acquisition_surfaces.py --self-test
python3 scripts/primitive_source_lifecycle.py --self-test
python3 scripts/check_global_multimodel_primitive_foundry.py --self-test
python3 scripts/check_observer_review.py --self-test
```

The proof verifies:

- the daemon can run a full source/context/search/proof tick;
- generated edge cards stay candidate-only and `serves_truth=false`;
- generated edge cards include enough input/output edge, blackbox behavior, and
  mutator/adapter metadata for compact planner use;
- structured artifacts such as package scripts, schemas, CI workflows, SQL,
  Terraform, OpenAPI/AsyncAPI, MCP manifests, Docker/K8s manifests, and JSONL
  examples can become source-backed edge candidates;
- search smoke tests return candidate primitives across API, frontend, ML,
  K8s/cloud, workflow replay, CI, schema, and MCP-style task families;
- agentic build routes prefer deterministic primitive composition and only use
  Kimi/GLM or coding harnesses when deterministic matching is insufficient;
- source surfaces become candidate source records;
- opportunities become synthetic session specs;
- source-backed opportunities become primitive drafts;
- unsourced capability ideas remain opportunity records;
- candidate rows become a ranked next-work queue;
- opt-in local Claude sessions become private candidate records;
- local paths are omitted by default;
- local evidence snippets are stored as digests, not text;
- appends are idempotent.

The benchmark proof verifies the Kaggle-style synthetic public-project cases under:

```text
fixtures/benchmarks/aidevobserver_session_review_v0/
```

It intentionally separates target expected findings from current reviewer findings so recall gaps can be measured without promoting candidate claims.

The local registry connector proof verifies the first source-ref precision seed:

- repo-relative Python functions, classes, methods, and constants;
- README/docs snippets;
- Claude-style `CLAUDE.md`, `skills/*/SKILL.md`, `commands/*.md`, `hooks/*.md`, and `mcp/*.md` surfaces;
- package and pyproject command entries;
- opt-in `/review` enrichment with local helper source refs;
- outcome-memory scoring over accepted/reused and dismissed/ignored local source refs;
- candidate-only rows with `serves_truth=false`;
- no absolute local path leakage.

The source acquisition surfaces proof verifies explicit PyPI, public repo,
workflow/IaC, official-docs, and open-textbook/OER source lanes for primitive
coverage expansion. It is intentionally metadata/license-gated: commercial
textbooks and unreviewed package/repo code must stay metadata-only until rights,
redaction, and proof gates pass.

It also verifies the `DeterministicBuilds.io` demand-signal lane. That surface
is a request/vote/proof-backlog source, not registry truth: votes and bounties
raise priority, while proof/promotion still decide whether a deterministic
primitive or template can serve truth.

The project scaffold proof verifies that a target repo can generate a
Claude-compatible AIDevObserver pack and that the connector indexes the pack as
structured project-context, skill, command, hook, MCP, and session-memory
candidate rows.

The first Kaggle-style fixture now acts as a source-ref recall gate for:

- tabular baseline primitives;
- image-classification baseline primitives;
- text-classification baseline primitives;
- compact schema/manifest/sample summary primitives.

It also reports and gates:

- `source_ref_coverage`;
- `top1_source_ref_accuracy`;
- `top3_source_ref_accuracy`.

## One-Tick Runs

Generate candidate records from the source-surface map:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once
```

Limit the number of source surfaces during iteration:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --surface-limit 4
```

Opt into local Claude Code sessions with derived summaries only:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --include-local-claude \
  --derive-local-reviews \
  --max-local-sessions 10
```

The default local-session behavior stores:

- content digest;
- path digest;
- project digest;
- byte size;
- finding counts;
- finding type histogram;
- top-finding evidence digests and lengths.

It does not store:

- raw transcript text;
- raw local paths;
- evidence snippets.

## Long Local Sessions

Local transcript review derivation is byte-capped by default so a multi-day watcher does not stall on huge transcripts.

Default:

```text
--max-local-review-bytes 8388608
```

To index huge transcripts as digest-only candidates, keep the default cap.

To derive summaries from very large local sessions in a private run:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --include-local-claude \
  --derive-local-reviews \
  --max-local-sessions 5 \
  --max-local-review-bytes 0
```

Use `--include-local-paths` only for private local workflows where raw path references are acceptable:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --include-local-claude \
  --include-local-paths
```

Do not use `--include-local-paths` for public demo artifacts or files intended for external review.

Generate source-backed primitive drafts from an explicit first-party repo:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --local-repo-root <repo-root> \
  --local-repo-limit 40
```

Generate a Claude-compatible AIDevObserver setup pack in a project:

```bash
python3 scripts/aidevobserver_project_scaffold.py --framework python --write
```

Dry run first to see the files without writing:

```bash
python3 scripts/aidevobserver_project_scaffold.py --framework python
```

This lane indexes repo-relative functions, methods, classes, constants, package
scripts, pyproject entry points, and selected docs. It skips private scratch and
reference/history folders such as `.agent/`, `.agents/`, `.codex/`,
`_reference/`, `repo_reference/`, and `archive/`. Tests remain useful proof
evidence but are not emitted as primitive drafts. Code symbols sort before doc
snippets so the launch primitive queue starts with callable components rather
than broad prose. Every emitted row remains candidate-only and blocks raw source
republication.

Python functions and methods include annotation-derived contracts, a compact
callable surface, and source/contract/record fingerprints. This is still
evidence, not truth:

```json
{
  "candidate_schema": "local_repo_primitive_v0.2",
  "contract": {"input": "dict[str,Any]", "output": "dict[str,Any]"},
  "callable_surface": {"signature": "run(inputs: dict[str,Any]) -> dict[str,Any]"},
  "source_fingerprints": {
    "source": "sha256:...",
    "contract": "sha256:...",
    "primitive_record": "sha256:..."
  },
  "serves_truth": false
}
```

## Continuous Mode

Run the source-surface loop hourly:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --watch --interval 3600
```

Run a private local-session-aware loop:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --watch \
  --interval 3600 \
  --include-local-claude \
  --derive-local-reviews \
  --max-local-sessions 25
```

Bounded test run:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --watch --interval 30 --max-ticks 2
```

## Sanitization

If an older local candidate record contains evidence snippets, sanitize it:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --sanitize-existing
```

## Candidate Ranking Queue

Each loop tick rewrites:

```text
candidate_rankings.jsonl
```

The ranking file is a deterministic queue for the next goal turn. It combines:

- primitive opportunity counts;
- generated synthetic session specs;
- generated source-backed primitive drafts and opportunity rows;
- private local review finding counts, when local summaries are explicitly enabled;
- source privacy/license status;
- a proxy token-savings estimate.

The token estimate is not billing truth. It is a deterministic planning proxy:

```text
estimate_basis=deterministic_proxy_from_candidate_counts_not_billing_truth
```

Refresh rankings without generating new candidates:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --refresh-rankings
```

Ranking records also default to:

```json
{"serves_truth": false, "trust": "candidate"}
```

This rewrites local `top_findings` from a private-text-bearing shape to a digest-only shape.

```json
{"private_text_field": "..."}
```

to:

```json
{"evidence_digest": "sha256:...", "evidence_chars": 120}
```

## Current Source Backbone

The loop reads:

```text
catalog/knowledge-packs/data/primitive-source-surface-map/surfaces.jsonl
catalog/knowledge-packs/data/aidevobserver-public-codegen-use-cases/use-cases.jsonl
catalog/knowledge-packs/data/aidevobserver-microsurface-atlas/microsurfaces.jsonl
```

That file already includes candidate source surfaces such as:

- Kaggle datasets and competitions;
- GitHub repositories, topics, issues, and releases;
- package registries;
- DeterministicBuilds.io deterministic-conversion requests;
- MCP registries;
- n8n/workflow-style inspiration;
- public government data portals;
- scientific literature sources;
- model and benchmark sources;
- security and standards catalogs.

The public codegen use-case seed file is a curated bridge between broad source
surfaces and actual AIDevObserver examples. Each row names a likely LLM coding
task, the common reinvention patterns, the expected template route, and the
candidate primitive family that should be generated.

This lane is enabled by default. It is still candidate-only; it does not claim
that a live public source has already been fetched or licensed.

The loop should now distinguish:

```text
primitive_draft       = source-backed candidate with provenance and proof needs
primitive_opportunity = useful capability idea that still lacks enough evidence
```

Do not let synthetic-only capability ideas masquerade as primitive drafts.
Synthetic sessions can demonstrate a route, but the primitive candidate should
point to source evidence such as a repo symbol, package/API surface, workflow,
public project, accepted finding, benchmark, or catalog record.

Limit it during iteration:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --use-case-limit 5
```

Disable it when testing only the generic source-surface map:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --skip-public-use-case-seeds
```

Current seed families include:

- provenanced web scraping;
- company/entity enrichment;
- document-to-JSON extraction;
- support ticket classification;
- Kaggle-style tabular, image, and text baselines;
- CSV ingestion;
- RAG documentation search;
- CI workflow generation;
- frontend quality gates;
- backend policy APIs;
- n8n workflow distillation;
- agent test-loop debugging;
- safe Python refactors;
- workflow replay debugging;
- security alert triage;
- deployment readiness;
- data quality incident analysis;
- prompt/model eval harnesses.

The microsurface atlas is a second curated seed lane. It decomposes common app
and platform surfaces into reusable objects, actions, templates, and primitive
families. The goal is to scale from dozens of demo tasks toward thousands of
recurring product surfaces used across the top apps and websites.

Initial microsurface families include:

- auth/session/MFA;
- billing/subscription/checkout;
- admin table/CRUD/import/export;
- search/filter/sort/recommend;
- notification preferences and delivery;
- file upload/preview/scan/convert;
- review/approval/escalation;
- maps/geocoding/routing/geofences;
- media generation/QC/publish;
- analytics dashboards/metrics/alerts;
- marketplace listing/cart/order/return;
- support chat/ticket/CRM/SLA.

Limit it during iteration:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --microsurface-limit 4
```

Disable it when testing only other source lanes:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py --once --skip-microsurface-atlas
```

## Kaggle Path

Kaggle is not treated as raw AI-session data. It is treated as finished public project evidence.

The loop should eventually support live Kaggle connectors that discover:

- competitions;
- datasets;
- public notebooks/kernels;
- notebook outputs;
- metrics and submission formats.

Those should produce synthetic sessions like:

```text
user asks for competition baseline
agent inspects data
agent writes loader/features/model/eval/submission
observer finds existing split/metric/submission primitives
session becomes a primitive/template candidate
```

Candidate primitive families:

- dataset schema inspection;
- missing-value fill;
- categorical encoding;
- numeric scaling;
- seeded train/validation split;
- RMSE/AUC/F1/logloss metrics;
- LightGBM/XGBoost/CatBoost training;
- submission CSV validation.

## GitHub / Published Session Path

GitHub Code Search and public datasets should feed candidate sources, not automatic publication.

Search examples:

```text
path:*.jsonl "role" "assistant" "tool_calls"
path:.aider.chat.history.md
"swe-agent" "trajectory" "patch"
"OpenHands" "trajectory" "SWE-bench"
```

Every public source still needs:

- license review;
- source attribution;
- PII/secret scan;
- redaction;
- candidate-only ingestion.

The loop now has an explicit live GitHub metadata connector:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --live-github \
  --github-query-limit 2 \
  --github-result-limit 3
```

Optional authentication comes from the configured environment variable:

```bash
GITHUB_TOKEN=... python3 scripts/aidevobserver_context_foundry_loop.py --once --live-github
```

The token is never written to candidate records.

GitHub Code Search may require authentication. When code search is not
available, the connector still attempts bounded repository metadata search and
emits any code-search authorization error as a candidate-only ledger field.

Live GitHub mode stores metadata only:

- public GitHub URL;
- repository URL/name;
- file path/name;
- source SHA when provided by the API;
- search-query digest and label;
- license/redaction status.

It does not download raw transcript content, source code, or local/private files.
Every discovered row remains:

```json
{"license_status":"needs_review","redaction_status":"not_fetched","serves_truth":false}
```

Raw public content fetch and benchmark publication remain separate future gates.

## Live Kaggle Metadata Connector

The loop also has an explicit live Kaggle metadata connector:

```bash
python3 scripts/aidevobserver_context_foundry_loop.py \
  --once \
  --live-kaggle \
  --kaggle-topic-limit 1 \
  --kaggle-result-limit 2
```

It uses the Kaggle CLI to list competitions, datasets, and kernels by topic.
It stores metadata only and does not pull notebooks, datasets, outputs, or
competition files.

Each discovered row remains:

```json
{"license_status":"needs_review","redaction_status":"metadata_only_not_downloaded","serves_truth":false}
```

The connector tolerates older Kaggle CLI versions by falling back when a
subcommand does not support `--page-size`, then truncates rows locally.

## Promotion Path

Candidate records are not registry truth. A primitive draft becomes usable only after:

```text
contract review
  -> license gate
  -> redaction gate
  -> example session generation
  -> AIDevObserver review benchmark
  -> Teleon proof/eval
  -> promotion record
```

Until then:

```text
serves_truth=false
```

Before the contract review stage, every primitive draft should have:

- stable candidate id;
- source refs and source family;
- license/provenance status;
- redaction status;
- input/output contract;
- effects, memory, cache, runtime, and privacy policy;
- readiness and trust fields;
- proof requirements;
- remix/tool affordances when relevant;
- benchmark or example fixture that expects the source ref.

## Next Improvements

1. Run the local-repo source-backed primitive lane on this repo and any opt-in first-party demo repos; keep code symbols ahead of docs.
2. Add or harden real-source connectors in priority order: accepted memory, primitive/template registry, GitHub metadata, package/API schema, MCP/tool schema, OpenAPI/GraphQL, Kaggle metadata, n8n/workflows, media pipelines, benchmark/proof records, Baltor context packs.
3. Add primitive dedupe against existing OpenHubForAI catalog records, accepted findings, and negative memory.
4. Use `candidate_rankings.jsonl` to select source-backed primitive candidates before synthetic session generation.
5. Add token-savings estimates per session spec and source-backed primitive route.
6. Add benchmark fixtures from generated sessions and real-source connector outputs, starting with source-ref top-1/top-3 checks.
7. Extend the existing hashed source-ref outcome memory from local repo ranking
   into broader OpenHubForAI/Teleon candidate ranking and benchmark reporting.
8. Package one real launch path end to end, preferably CLI or Claude Code MCP first.
9. Add backend health, rollback, auth/workspace, privacy, and setup documentation before team launch.

## Real-Source Primitive And Launch Bias

*Inlined from the former `aidevobserver-real-primitive-launch-goal-addendum.md` (archived for lineage under
`_repos/_shared/archive/legacy/aidevobserver/`). It sharpens this loop toward real-source extraction over
synthetic generation; the connector priority order and creation pipeline it also described are already
covered by the sections above — the operating rules unique to it are captured here.*

**Core rule.** `real source evidence -> primitive candidate -> proof bundle -> promotion`. Do not create
trusted primitive records from imagination; if a capability has no source evidence yet, create a
`primitive_opportunity`, not a `primitive_draft`. Synthetic material stays useful for demos, fixtures,
negative controls, and privacy-preserving derivatives, but never becomes a primitive record unless it is
explicitly marked a synthetic fixture and excluded from trusted registry promotion.

**Acceptable source evidence:** first-party repo symbols/scripts/docs/workflows/tests/examples; opt-in local
AI-coding-session derivatives with private text removed; public GitHub metadata and licensed public code;
package-registry metadata, CLIs, OpenAPI specs, MCP servers, and tool schemas; Kaggle
competitions/datasets/notebooks as attributed public evidence; n8n/workflow exports only when license and
attribution are compatible; OpenHubForAI catalog/benchmark/proof records; and user-accepted AIDevObserver
findings plus dismissed negative memory.

**Source-surface acquisition lanes:** PyPI JSON metadata and PyPI Simple/Index distribution metadata; GitHub
and GitLab public project metadata; GitHub Actions Marketplace and Terraform Registry workflow/IaC metadata;
Python, cloud-native, and common-framework official documentation; OpenStax / Open Textbook Library style OER
(open-licensed learning material only); and DeterministicBuilds.io-style request/vote/bounty/proof-backlog
records for moving repeated LLM/agent behavior into deterministic primitives. Commercial coding textbooks are
**not** a raw ingestion source (metadata-level task inspiration only, unless rights are explicitly granted).
Deterministic-build requests are demand signals, not truth — request popularity never bypasses license,
redaction, contract, proof, PlanLock, or promotion gates.

Proofs: `python3 scripts/primitive_source_lifecycle.py` (global lifecycle) and
`python3 scripts/check_aidevobserver_source_acquisition_surfaces.py --self-test`.

**Launch readiness gates (do not call launch-ready until all hold):** at least one install path works end to
end from a fresh setup; a user can review a real or uploaded session and get useful source refs; findings can
be accepted / reused / dismissed and used as future memory; local registry enrichment is opt-in,
privacy-safe, and benchmarked; primitive candidates are source-backed or explicitly opportunity-only;
synthetic demos are labeled and never treated as real transcripts; all candidate records stay
`serves_truth=false`; the proof commands pass for review, examples, local service, connector, benchmark,
launch readiness, and this loop; and no raw private transcript text, local paths, secrets, or PII appear in
any public doc, example, fixture, or candidate row.

**Work-selection bias (prefer in order):** (1) a real source connector or source-backed primitive candidate;
(2) a benchmark / source-ref precision improvement; (3) an install/setup path that makes alpha use real;
(4) a review-UI improvement that exposes source refs and outcomes; (5) a privacy/proof check that prevents
unsafe publication; (6) a synthetic demo only when it is needed to show a source-backed route.

**Anti-pattern to avoid:** `invent primitive -> invent session -> invent proof -> call it registry value`.
Use instead: `observe source -> derive candidate -> prove behavior -> promote later`.
