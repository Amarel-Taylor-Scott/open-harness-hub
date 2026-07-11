# AIDevObserver Systems, Registries, And Surface Overview

**Status:** working architecture and demo overview  
**Updated:** 2026-06-28  
**Scope:** AI Done Right, AIDevObserver, Teleon, Baltor, OpenHubForAI, registry sources, demo routes, and integration priorities.

This document is the current operator-facing map of the portfolio, with extra focus on making AIDevObserver useful as the developer-facing demo, integration, and evidence-capture surface.

## One-Line Architecture

```text
AI developer session
  -> AIDevObserver review and replay
  -> Teleon registry/template/middleware search
  -> CandidateBundle + compact PlanDelta
  -> deterministic compiler + RemixSurface
  -> PlanLock + JSONL ledger
  -> proof/promotion
  -> reusable registry memory
```

AIDevObserver is the adoption wedge. It watches real AI coding sessions, surfaces where the agent is wasting tokens or reinventing existing capabilities, and turns accepted findings into reusable registry evidence for Teleon, OpenHubForAI, and eventually Baltor-governed workflows.

## URL Policy

Surfaces are served by the showcase (`OH_PRODUCT=aidevobserver`) over the same-origin `/api/observer/` seam;
link to the app's routes, not to any tunnel host. An ephemeral tunnel may front the local app for external
sharing, but tunnel hostnames are transient and are never a stable or canonical address.

The app's routes:

```text
#/examples
#/review
#/sessions
#/agentic
#/developer
```

Internal service addresses may remain in machine-readable local service registries and health checks, but
they should not be presented as user-facing URLs. When a shareable URL is genuinely needed, capture the
active (ephemeral) tunnel in the launch manifest or operator notes rather than hard-coding it here.

## Portfolio Split

| Surface | Role | Domain / public identity | Code surface | Truth boundary |
| --- | --- | --- | --- | --- |
| AI Done Right | Parent brand, portfolio positioning, standards strategy | `aidoneright.dev` | `_repos/aidoneright/frontend` | Owns no runtime truth |
| AIDevObserver | Developer-facing AI session review, replay, examples, middleware comparison, and internal benchmark-lab workflows | `aidevobserver.io` | `_repos/aidevobserver/frontend`, `_repos/teleon/backend/src/teleon/observer` | Suggestions and candidate findings only |
| Teleon | Capability compiler, deterministic runtime, registry search, PlanLock execution | `teleon.dev` | `_repos/teleon/frontend`, `src/teleon` | Governs efficiency and evidence |
| Baltor | Governed context and source-grounded applied product | `baltor.ai` | `_repos/baltor/frontend`, `src/baltor` | Governs served truth |
| OpenHubForAI family | Open registry substrate for context, tools, skills, evals, templates, workflows, specs | `openhubforai.io` plus Open*Hub surfaces | `_repos/openhubforai/frontend`, `catalog`, `schemas`, `vocabularies` | Reference artifacts and candidates only |

The dependency law remains:

```text
Baltor -> Teleon -> OpenHubForAI
```

Baltor consumes Teleon as a tenant. Teleon consumes OpenHubForAI and other registry artifacts. OpenHubForAI remains independent and is not a truth authority.

## AIDevObserver Current Surface

AIDevObserver is both a product surface and a review engine projection.

Primary app files:

```text
_repos/aidevobserver/frontend/index.html
_repos/aidevobserver/frontend/aidevobserver-main.jsx
_repos/aidevobserver/frontend/aidevobserver.css
_repos/aidevobserver/frontend/examples/manifest.json
_repos/aidevobserver/frontend/examples/*.txt
_repos/aidevobserver/frontend/examples/*.jsonl
```

Observer backend and engine files:

```text
_repos/shared-backend-components/scripts/observer_local_service.py
_repos/shared-backend-components/scripts/showcase/server.py
_repos/teleon/backend/src/teleon/observer/
```

Important UI routes:

```text
#/review       paste or upload a session and get a ranked report
#/sessions     discover and review local AI coding sessions
#/findings     inspect latest findings and outcomes
#/agentic      supervise autonomous loops and repeated failures
#/examples     replay demo sessions and compiled-AI patterns
#/reports      usage, reuse, hours saved, and team rollups
#/developer    documented API seam and integration instructions
#/settings     review mode, advisory mode, and behavior controls
```

Same-origin observer API seam:

```text
POST /api/observer/review
GET  /api/observer/sessions
POST /api/observer/live
POST /api/observer/agentic
POST /api/observer/outcome
GET  /api/observer/outcomes
GET  /api/observer/registry/search
```

The backend is read-only for demo review, uses synthetic/public session text by default, stores only optional metadata-only triage outcomes, and marks observations as candidate evidence. AIDevObserver should not promote truth directly.

Outcome memory now stores hashed source-ref keys when a user triages a finding
with Accept / Reuse / Dismiss. In installed/local mode, accepted/reused source
refs boost future local registry hits and dismissed/ignored refs suppress them.
The stored memory remains metadata-only and candidate-only; raw transcripts,
absolute local paths, and evidence snippets are not stored for this ranking
signal.

## What AIDevObserver Should Detect

A useful AIDevObserver review should identify:

```text
reinvention of existing repo/registry capabilities
stack or product surface reinvention
oversized context and duplicate file reads
token-waste loops and repeated failed attempts
missed cheaper deterministic routes
agentic stalls, runaway loops, and goal drift
unnecessary source-code generation when a primitive/template exists
missing tests, missing proofs, and weak validation boundaries
places where a CandidateBundle or deterministic tool should replace free-form coding
safety, compliance, destructive-operation, and secret-handling signals
```

Current finding families should remain advisory. A finding can become useful memory only after a human accepts it or after a proof-backed promotion path exists.

## AIDevObserver Integration Surfaces

The strongest near-term integration pattern is:

```text
capture session
  -> review session
  -> identify missed deterministic route
  -> search registries
  -> attach repo-relative source refs
  -> show lower-token route
  -> let user accept finding
  -> create registry candidate or negative-memory edge
```

Integration points:

| Integration | Purpose | Expected status |
| --- | --- | --- |
| Manual paste/upload | Fastest demo path for Claude, Codex, Cursor, and other transcripts | Primary |
| Local session discovery | Review local AI coding sessions from the same workspace | Primary |
| CLI review | Run post-session review from terminal scripts | Primary |
| Editor extension | Bring review findings into VS Code/Cursor-style flows | Active target |
| MCP server | Let agents ask the observer for review/search context through a standard tool seam | Active target |
| Pre-tool hook | Non-blocking warning before risky operations or obvious reinvention | Advisory only |
| Live route endpoint | Spot loops or waste during long-running agentic sessions | Active target |
| Registry search middleware | Compare current agent behavior against Teleon/OpenHubForAI capabilities | Highest leverage |
| Token accounting middleware | Measure actual context and runtime savings | Highest leverage |

The first registry middleware slice is implemented locally:

```text
explicit repo root
  -> Python symbol/constant index
  -> Claude project context / skills / commands / hooks / MCP docs
  -> README/docs snippet index
  -> package/pyproject script index
  -> candidate source refs
  -> outcome-memory score adjustment
  -> optional review finding enrichment
```

Public demos keep this disabled. Installed/local mode can opt in and pass
`registry_cwd` to `/api/observer/review`; the response still emits candidate
findings only and never includes the raw local root path.

## Replayable Demo Pack

The current example pack is under:

```text
_repos/aidevobserver/frontend/examples/
```

The manifest currently supports replayable session demos for:

```text
web-scraper-regulatory-rates
company-entity-enrichment
document-json-schema-extraction
support-ticket-classification
revenue-regression-pipeline
kaggle-tabular-baseline
kaggle-image-classification-baseline
kaggle-text-classification-baseline
safe-pyprefix-migration
workflow-replay-debugger
n8n-workflow-distillation
frontend-component-quality-gate
backend-policy-api
data-engineering-csv-ingestion
rag-docs-search-app
ci-workflow-generation
bugfix-repeated-test-loop
```

Recommended public demo route (on the showcase-served app; any external tunnel is ephemeral):

```text
#/examples
```

Best first demo sequence:

1. Web scraper for regulatory rates.
2. Document-to-JSON extraction.
3. Company/entity enrichment.
4. Safe pyprefix migration.
5. Workflow replay debugger.
6. n8n workflow distillation.

This sequence shows the core story: common coding request -> registry/template route -> compact plan -> compiler checks -> locked execution -> ledger/proof -> reusable composite candidate.

## Registry Families

AIDevObserver should increasingly search across multiple registry families rather than only source files.

| Registry family | Examples | Use in AIDevObserver |
| --- | --- | --- |
| OpenHubForAI catalog | harnesses, pipelines, rule packs, knowledge packs, tools, personas, adapters, rubrics | Find existing reusable components before new code is written |
| Teleon primitives | transforms, gates, routers, expanders, reducers, adapters, external calls, composites | Suggest deterministic routes and candidate replacements |
| Remix tools | `map_sequence`, `field_rename`, `output_wrapper`, `retry`, `cache`, `idempotency`, `artifact_reference` | Repair contract mismatches without source rewriting |
| Workflow registries | n8n, GitHub Actions, Airflow, Dagster, Temporal, Argo, Flyte, ComfyUI | Distill existing workflows into candidate templates and primitives |
| Media registries | image, video, audio, captioning, safety, encode/decode, quality gates | Support multimodal workflows with artifacts and model routes |
| Code intelligence registries | AST graphs, dependency graphs, migration plans, proofs, codegen contracts | Catch reinvention and propose safer code changes |
| Benchmark registries | TCCB cases, security suites, eval packs, proof manifests | Compare token use, determinism, compile success, and replay reliability |
| Negative memory | failed chains, unsafe aliases, repeated loop patterns, stale APIs | Suppress known bad routes and explain why |

## Canonical Teleon Artifact Chain

AIDevObserver should explain Teleon routes using this vocabulary:

```text
PrimitiveRecord      canonical registry truth for a capability
CallableSurface      observed Python/object/function evidence
TemplateRecord       typed pipeline shape
CandidateBundle      compact planning bundle shown to a model
PlanDelta            model-selected candidate intent
RemixSurface         deterministic mutation menu
VariationRecord      durable record of an applied remix
PlanLock             deterministic execution truth
Ledger               observed runtime truth
ProofBundle          evidence that a candidate behaved correctly
PromotionRecord      permission to serve or reuse as trusted memory
```

The LLM can propose a PlanDelta. It cannot decide truth, create canonical identities, promote artifacts, disable gates, or bypass compiler checks.

## Domain Coverage For Demos

AIDevObserver should showcase at least one high-quality session per domain family:

```text
software engineering: safe refactor, pyprefix migration, test repair
frontend: component quality gate, accessibility, snapshot checks
backend: API policy workflow, idempotent persistence, saga/receipt checks
data engineering: CSV ingestion, schema validation, parquet/catalog publishing
data science: regression, classification, feature engineering, leakage checks
document intelligence: invoice, lease, contract, resume, source spans
web/data acquisition: web scraper, regulatory source extraction, evidence gates
entity enrichment: company profile enrichment, dedupe, provenance, confidence
security: alert triage, prompt-injection handling, secret redaction
DevOps: deployment readiness, secrets, rollback, health checks
workflow automation: n8n import, graph distillation, template promotion
media: image-to-video, audio/video primitives, quality and safety gates
healthcare and finance: high-stakes examples with audit and proof requirements
```

## Useful AIDevObserver Demo Patterns

### 1. Reinvention Catch

Show a user or agent building a scraper, parser, retry wrapper, schema validator, or component quality gate from scratch. AIDevObserver should point to existing primitives/templates and estimate saved tokens/time.

### 2. Session Replay

Replay a stored transcript and JSONL event stream. Show findings, accepted/dismissed outcomes, and how the accepted finding becomes candidate registry memory.

### 3. CandidateBundle Comparison

For a task like company enrichment, show:

```text
normal agent path: long prompt + custom code + uncertain tests
compiled path: compact CandidateBundle + PlanDelta + compiler checks + PlanLock
```

### 4. Agentic Loop Supervision

Use the agentic screen to show repeated commands, repeated failures, missing termination, and budget drift. The observer should recommend a bounded plan, proof, or stop condition.

### 5. n8n Workflow Distillation

Ingest an n8n workflow JSON as candidate evidence:

```text
n8n workflow JSON
  -> redact credentials
  -> normalize graph
  -> map nodes to primitive candidates
  -> create CandidateBundle
  -> compile if contracts match
  -> keep candidate-only until proof
```

### 6. Media Primitive Registry

Show a media workflow:

```text
input safety -> image describe -> motion plan -> video generation -> stabilize -> QC -> encode
```

The key point is that media artifacts are primitives too. The registry should track artifact refs, model routes, safety gates, parameters, costs, and quality proofs.

## AIDevObserver To Teleon Bridge

The strongest product loop is:

```text
AIDevObserver finding
  -> human outcome: accept, reuse, dismiss, defer
  -> registry candidate update
  -> Teleon route search improves
  -> future sessions get cheaper CandidateBundles
  -> successful plans promote to composite primitives
```

Concrete bridge outputs:

```text
PrimitiveCandidate
TemplateCandidate
NegativeMemoryEdge
KnownGoodChain
CompositePrimitiveCandidate
BenchmarkCase
ProofRequirement
TokenSavingsObservation
```

## AIDevObserver To Baltor Bridge

Baltor should consume only governed outputs. AIDevObserver findings can help Baltor engineers improve context and workflows, but they should not become served truth directly.

Safe bridge rule:

```text
AIDevObserver observation -> Teleon proof/promotion -> Baltor-governed truth decision
```

## AIDevObserver To OpenHubForAI Bridge

OpenHubForAI is the open substrate for reusable artifacts:

```text
accepted session pattern -> public/synthetic benchmark case
accepted primitive pattern -> candidate component definition
accepted workflow pattern -> template or workflow capsule
accepted proof pattern -> harness/rubric/eval pack
```

No private customer data or real PII should be published. Synthetic and composite examples are the default.

## Current Proof And Check Scripts

Useful checks for this area include:

```text
_repos/shared-backend-components/scripts/check_aidevobserver_example_sessions.py
_repos/shared-backend-components/scripts/check_aidevobserver_session_benchmark.py
_repos/shared-backend-components/scripts/check_aidevobserver_compiled_ai_evaluation.py
_repos/shared-backend-components/scripts/check_observer_local_service.py
_repos/shared-backend-components/scripts/check_observer_review.py
_repos/shared-backend-components/scripts/check_observer_router.py
_repos/shared-backend-components/scripts/check_observer_agentic.py
_repos/shared-backend-components/scripts/check_aidevobserver_mcp.py
_repos/shared-backend-components/scripts/check_aidevobserver_vscode_ext.py
_repos/shared-backend-components/scripts/check_ai_done_right_surface_family.py
_repos/shared-backend-components/scripts/check_surface_map.py
_repos/shared-backend-components/scripts/check_northstar_design.py
```

The example-session checker is especially important because the demo pack is now a first-class AIDevObserver surface. It should keep the manifest, transcript files, event files, and app wiring from drifting.

The session benchmark currently includes three Kaggle-style synthetic public-project cases and gates reviewer source-ref recall for tabular, image-classification, and text-classification primitive routes.

The context foundry loop now also ingests curated public codegen use-case seeds from:

```text
catalog/knowledge-packs/data/aidevobserver-public-codegen-use-cases/use-cases.jsonl
catalog/knowledge-packs/data/aidevobserver-microsurface-atlas/microsurfaces.jsonl
```

Those seeds cover common LLM coding tasks such as web scraping, entity enrichment, document extraction, support classification, Kaggle-style ML baselines, CSV ingestion, RAG apps, CI workflows, frontend quality gates, backend policy APIs, n8n workflow distillation, safe refactors, security triage, deployment readiness, data quality incidents, and eval harnesses.

Each seed is converted into candidate source records, synthetic session specs, primitive drafts, and ranking rows. This is the practical bridge from likely AI coding demand to AIDevObserver demos and Teleon/OpenHubForAI primitive candidates. It is not live public-source ingestion yet; live GitHub/Kaggle/package/workflow connectors still need explicit license, attribution, redaction, and proof gates.

The microsurface atlas is the expansion path for non-GitHub surfaces: common
product surfaces such as login, checkout, admin tables, search, notifications,
file upload, review queues, maps, media generation, analytics, marketplaces,
and support workflows. The intended scale is hundreds to thousands of these
microsurfaces across the top websites, apps, platforms, and enterprise systems.
Each row decomposes a surface into reusable objects, actions, templates,
primitive candidates, effects, and artifact policies.

The foundry also has opt-in live metadata connectors:

```text
--live-github  metadata-only GitHub discovery
--live-kaggle  metadata-only Kaggle competition/dataset/kernel discovery
```

Both connectors keep raw content fetch, publication, and promotion behind later
license/redaction/proof gates.

## Near-Term Build Priorities

1. Serve the app via the showcase; capture any ephemeral tunnel (external sharing only) in a small manifest consumed by docs and demo scripts, and never treat a tunnel host as a stable address.
2. Make the Examples page the default public demo path for AIDevObserver.
3. Add token accounting to review results: estimated prompt tokens, repeated reads, duplicate context, and compile-route savings.
4. Add registry search middleware behind reviews: source graph, Teleon primitives, OpenHubForAI catalog, curated codegen use-case seeds, n8n workflow candidates, and negative memory.
5. Add a TCCB smoke benchmark page that compares direct coding, runtime agent orchestration, and compact PlanDelta compilation.
6. Add a "turn finding into candidate" action for accepted findings.
7. Add a "replay as live session" path for every example transcript.
8. Add n8n workflow upload/distill demo with redaction and candidate-only warnings.
9. Add media primitive demo using image/video/audio artifact refs and quality gates.
10. Add a public demo script that points reviewers to the showcase-served app (or the current ephemeral tunnel if one is active).

## Operating Rules

```text
Use public tunnel URLs for user-facing demos.
Keep internal-only addresses out of user-facing responses.
Keep AIDevObserver findings candidate-only by default.
Do not store or publish real PII in session examples.
Do not leak secrets into transcripts, ledgers, or compact views.
Prefer compact generated views over raw source in LLM context.
Let the compiler apply remixes; do not let the LLM rewrite source as the first repair.
Execute only PlanLock, not PlanDelta.
Promote only after proof.
```

## Related Documents

```text
docs/strategy/teleon-baltor-openhubforai-portfolio.md
docs/codex/aidevobserver-compiled-ai-evaluation-plan.md
_repos/teleon/context/codex/teleon-architecture-routes-and-fallbacks.md
_repos/teleon/context/codex/teleon-universal-workflow-registry-and-n8n.md
_repos/teleon/context/codex/teleon-multimodal-media-primitive-registry.md
_repos/teleon/context/codex/teleon-external-feedback-response.md
taxonomy/SPEC.md
_repos/shared-backend-components/architecture/local_service_registry.json
_repos/shared-backend-components/architecture/surface_capability_spec.json
```
