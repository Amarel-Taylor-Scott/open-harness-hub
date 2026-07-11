# AIDevObserver Use-Case And Primitive Roadmap

**Date:** 2026-06-28  
**Purpose:** identify common AI coding and LLM-assisted development use cases, then turn them into AIDevObserver findings, registry objects, and Teleon primitive/template candidates.

## Why This Matters

AIDevObserver should not only review sessions after the fact. It should learn the recurring shapes of AI-assisted development work and build primitive registries around them.

The goal:

```text
Observe what developers keep asking AI agents to do
  -> define the common objects and actions
  -> derive source-backed primitive/template candidates
  -> detect reinvention and token waste
  -> route future sessions to existing work
```

The commercial wedge remains:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

## Current Market Signals

Signals from current research and industry reporting:

- AI use is heavily concentrated in software development and writing tasks. One Anthropic Economic Index paper reports that software development plus writing account for nearly half of observed Claude usage, and that usage is split between augmentation and automation.
- Coding agents are quickly appearing in real GitHub artifacts. One 2026 GitHub adoption study estimates coding-agent adoption across analyzed projects at roughly the low-to-high 20% range and finds agent-assisted commits are larger, with many features and bug fixes.
- AI tools can slow expert developers in mature repos when they lack project context. The METR randomized trial found experienced open-source developers were slower with early-2025 AI tools, despite expecting speedups.
- AI agent builders face repeated practical issues around runtime integration, dependency management, orchestration complexity, RAG engineering, and evaluation reliability.
- Industry reporting increasingly says the bottleneck is shifting from code generation to review, validation, traceability, and governance.

These signals support AIDevObserver's thesis:

```text
The next productivity layer is not more code generation.
It is reuse, context discipline, validation, and routing to known-good paths.
```

## Source Links For External Review

- Anthropic Economic Index: https://arxiv.org/abs/2503.04761
- GitHub coding-agent adoption study: https://arxiv.org/abs/2601.18341
- METR developer productivity RCT: https://arxiv.org/abs/2507.09089
- AI agent Stack Overflow challenges study: https://arxiv.org/abs/2510.25423
- State of GenAI in software development survey/literature review: https://arxiv.org/abs/2603.16975
- Agentic code review vision paper: https://arxiv.org/abs/2605.17548
- Cloud functions and Kubernetes checklist research: `_repos/_shared/research/cloud-functions-kubernetes-engineering-checklists.md`

## Common AI Development Use Cases To Model

These are the high-priority use cases AIDevObserver should detect and Teleon/OpenHubForAI should model as primitives/templates.

| Priority | Use Case | What Developers Ask AI To Do | AIDevObserver Opportunity |
| --- | --- | --- | --- |
| P0 | Find existing helper | "Build a parser/helper/client" | Detect when helper already exists |
| P0 | Bug fix | "Fix this failing test/error" | Detect repeated failed loops and known fixes |
| P0 | Test generation | "Write tests for this function" | Route to existing test template and coverage rules |
| P0 | Documentation | "Explain this code / write docs" | Avoid huge context; use code-aware doc primitive |
| P0 | Refactor | "Clean this up / migrate pattern" | Require contract/proof and find existing migration recipe |
| P0 | Code review | "Review this PR/change" | Use review checklist, source refs, and proof gates |
| P0 | Search/codebase question | "Where is X defined?" | Replace model scan with deterministic search |
| P1 | API integration | "Add Stripe/Salesforce/GitHub/etc." | Route to integration templates and tool contracts |
| P1 | Data extraction | "Extract JSON from docs/pages/files" | Use schema/span gates and bounded extractors |
| P1 | Web scraper | "Scrape this source into JSON/CSV" | Use acquire/fetch/extract/validate/emit template |
| P1 | Data pipeline | "Ingest/clean/transform this dataset" | Use schema/normalize/artifact templates |
| P1 | UI component | "Build this React page/component" | Use design-system and accessibility gates |
| P1 | DevOps automation | "Create CI/deploy workflow" | Search workflow registry before writing YAML |
| P1 | Agent/tool workflow | "Build an agent with tools/memory" | Use agent runtime/template registry |
| P1 | RAG/search app | "Make a chatbot over docs" | Route to retrieval, chunking, citation, eval templates |
| P2 | Migration | "Move framework/API/version" | Use migration plan, compatibility checks, proof |
| P2 | Performance tuning | "Optimize this slow function/query" | Use profiling + deterministic improvement templates |
| P2 | Security scan/fix | "Check vulnerabilities/secrets" | Use safety as secondary finding family |
| P2 | Data science model | "Train classifier/regression model" | Use feature/eval/leakage/artifact gates |
| P2 | Media workflow | "Generate/edit image/video/audio" | Use artifact refs, model routes, QC gates |

## Development Objects To Index

AIDevObserver should build searchable records for the objects AI agents most often recreate or misuse.

### Code Objects

- functions
- classes
- methods
- modules
- scripts
- CLIs
- config files
- package scripts
- test fixtures
- test helpers
- mocks
- migrations
- adapters
- clients
- API handlers
- React components
- hooks
- schemas
- validators
- type definitions

### Workflow Objects

- CI workflows
- deploy pipelines
- n8n workflows
- GitHub Actions
- Airflow/Dagster jobs
- Make/Zapier automations
- Temporal workflows
- data ingestion jobs
- release checklists
- quality gates
- runbooks

### AI/LLM Objects

- prompts
- system messages
- tool schemas
- MCP server profiles
- agent loops
- memory/state schemas
- retrieval configs
- chunking policies
- embedding indexes
- model routing policies
- eval suites
- promptfoo/lm-eval style benchmarks

### Context Objects

- docs snippets
- architecture decisions
- service maps
- API contracts
- schema slices
- dependency graphs
- glossary entries
- known gotchas
- source-backed facts
- Baltor-style verified context packs

### Artifact Objects

- document artifacts
- parsed text artifacts
- table artifacts
- image/video/audio artifacts
- browser traces
- proof logs
- test logs
- ledger events
- receipts

## Primitive Families To Build

These are the reusable primitives that should exist before we need a large generalized compiler.

Primitive records must be source-backed. If a row only expresses a good idea,
store it as a `primitive_opportunity` until there is evidence from a repo,
workflow, package/API schema, MCP/tool surface, public project, benchmark,
accepted finding, or catalog record.

Minimum source-backed primitive fields:

- candidate id and slug;
- source refs and attribution;
- license/provenance status;
- redaction status;
- input/output contract;
- effects, memory, cache, runtime, and privacy policy;
- readiness, trust, and `serves_truth=false`;
- proof requirements and benchmark/source-ref expectations.

### P0: Observer Review Primitives

| Primitive | Input | Output | Purpose |
| --- | --- | --- | --- |
| `session.parse_transcript` | TranscriptArtifact | SessionEventSet | Normalize Claude/Codex/Cursor/plain logs |
| `session.extract_actions` | SessionEventSet | ActionTrace | Extract files, commands, code blocks, goals |
| `session.classify_intent` | ActionTrace | IntentSet | Identify task families |
| `session.detect_loop` | ActionTrace | LoopFindingSet | Detect repeated failures, stalls, thrash |
| `session.detect_context_waste` | ActionTrace | ContextWasteFindingSet | Detect oversized reads/pastes/model scans |
| `session.detect_reinvention` | ActionTrace + RegistryHits | ReinventionFindingSet | Compare actions to existing helpers/templates |
| `finding.rank` | FindingSet | RankedFindingSet | Rank by confidence and usefulness |
| `finding.redact` | FindingSet | RedactedFindingSet | Remove secrets/private evidence |
| `finding.triage_record` | Finding + HumanOutcome | TriageEvent | Accept/reuse/dismiss memory |

### P0: Local Repo Search Primitives

| Primitive | Input | Output | Purpose |
| --- | --- | --- | --- |
| `repo.index_symbols` | RepoPath | SymbolIndex | Functions/classes/methods/modules |
| `repo.index_docs` | RepoPath | DocIndex | README/docs/comments snippets |
| `repo.index_scripts` | RepoPath | ScriptIndex | Package scripts, CLIs, automation |
| `repo.search_exact` | Query | SearchHits | Deterministic exact search |
| `repo.search_semantic` | Query | SearchHits | Semantic helper/template search |
| `repo.match_contract` | CandidateAction + SymbolIndex | ContractMatchSet | Find same input/output behavior |
| `repo.detect_duplicate_helper` | CodeBlock + SymbolIndex | DuplicateHelperFinding | Catch reinvented helpers |

### P0: Token And Context Primitives

| Primitive | Input | Output | Purpose |
| --- | --- | --- | --- |
| `tokens.estimate_transcript` | TranscriptArtifact | TokenEstimate | Estimate session token use |
| `tokens.estimate_context_slice` | TextSpanSet | TokenEstimate | Estimate pasted/read context |
| `tokens.compare_route` | BaselineRoute + ProposedRoute | TokenSavingsEstimate | Estimate savings |
| `context.slice_relevant` | Query + ContextArtifact | ContextSlice | Prefer targeted context |
| `context.find_overread` | ActionTrace | OverreadFindingSet | Detect unnecessary file/schema/log reads |
| `context.suggest_pack` | Query + Registry | ContextPackSuggestion | Use Baltor/OpenCompression style pack |

### P1: Template/Route Primitives

| Template | Shape |
| --- | --- |
| `template.find_helper_then_edit` | intent -> search -> inspect -> patch -> test |
| `template.bugfix_with_proof` | reproduce -> localize -> patch -> test -> report |
| `template.test_generation` | inspect contract -> generate tests -> run -> coverage report |
| `template.doc_generation` | inspect code -> generate docs -> lint examples |
| `template.safe_refactor` | audit -> plan -> migrate -> contract report -> proof |
| `template.web_scrape_validate_emit` | discover -> fetch -> extract -> normalize -> validate -> emit |
| `template.document_extract_validate_emit` | parse -> extract -> normalize -> schema/span gate -> emit |
| `template.api_integration` | validate request -> client call -> retry/idempotency -> response |
| `template.data_ingest` | acquire -> parse -> schema gate -> normalize -> artifact/catalog |
| `template.frontend_quality_gate` | parse -> typecheck -> design tokens -> a11y -> snapshot |
| `template.agent_loop_guard` | observe -> detect loop -> recommend pause/redirect |
| `template.workflow_distill` | import workflow -> redact -> graph -> candidate primitives |

### P1: Registry Search Primitives

| Primitive | Purpose |
| --- | --- |
| `registry.search_helpers` | Find existing functions/tools/scripts |
| `registry.search_templates` | Find workflow/template shapes |
| `registry.search_primitives` | Find Teleon primitives |
| `registry.search_workflows` | Find n8n/GitHub Actions/Airflow-like workflows |
| `registry.search_mcp` | Find existing MCP/tool integrations |
| `registry.search_benchmarks` | Find proof/eval records |
| `registry.negative_memory_lookup` | Suppress bad/dismissed matches |
| `registry.source_ref_pack` | Attach source_ref to finding |

## First 20 Primitive Cards To Create

These are the first concrete records worth generating once each row has source
evidence. Until then, treat the row as a primitive opportunity.

IDs are version-free (globally-unique-naming law): the version lives in `schema_version` metadata, never
in the id — each of these records starts at `schema_version` 1.

| ID | Priority | Why |
| --- | --- | --- |
| `prim:session.parse_transcript` | P0 | Everything starts with normalized sessions |
| `prim:session.extract_actions` | P0 | Needed for all findings |
| `prim:repo.index_symbols` | P0 | Needed for exact helper detection |
| `prim:repo.search_exact` | P0 | Replaces model repo scans |
| `prim:repo.detect_duplicate_helper` | P0 | Core "rebuilding what exists" wedge |
| `prim:session.detect_context_waste` | P0 | Core token savings wedge |
| `prim:tokens.estimate_context_slice` | P0 | Makes savings visible |
| `prim:finding.rank` | P0 | Keeps reports readable |
| `prim:finding.triage_record` | P0 | Product flywheel |
| `prim:registry.search_helpers` | P0 | Source-backed findings |
| `prim:template.find_helper_then_edit` | P0 | Common AI coding flow |
| `prim:template.bugfix_with_proof` | P0 | Very common AI coding flow |
| `prim:template.test_generation` | P0 | Common and easy to prove |
| `prim:template.safe_refactor` | P0 | High-value, proof-heavy |
| `prim:template.web_scrape_validate_emit` | P1 | Strong demo route |
| `prim:template.document_extract_validate_emit` | P1 | Common business use |
| `prim:template.data_ingest` | P1 | Common data engineering use |
| `prim:template.frontend_quality_gate` | P1 | Shows frontend coverage |
| `prim:registry.search_templates` | P1 | Moves beyond helper search |
| `prim:registry.negative_memory_lookup` | P1 | Reduces false positives |

## AIDevObserver Finding Types

The product should standardize finding families.

| Finding Type | Description | First Evidence |
| --- | --- | --- |
| `reinvention.helper` | Agent created helper/function that already exists | code block + source_ref |
| `reinvention.workflow` | Agent built bespoke workflow that matches template | action trace + template_ref |
| `reinvention.product_surface` | Agent rebuilt existing app/page/surface | file paths + product registry |
| `context.oversized` | Agent pasted/read too much context | token estimate + span |
| `context.duplicate_read` | Agent reread same files without new result | action trace |
| `alternative.deterministic_search` | Model scan should be deterministic search | query + exact hit |
| `agentic.loop` | Repeated failed actions or thrash | repeated actions |
| `proof.missing` | Change lacks expected test/proof | patch + no proof event |
| `quality.review_bottleneck` | Lots of generated code lacks review path | diff volume + no review gate |
| `safety.signal` | Secondary safety/governance issue | redacted command/evidence |

## Domain Use-Case Backlog

Create examples and benchmark fixtures for:

1. Frontend component build + quality gate.
2. Backend API endpoint + policy rule.
3. Bug fix with repeated test failure.
4. Safe refactor / pyprefix migration.
5. Test generation and coverage.
6. Documentation generation from code.
7. Web scraper with provenance.
8. Document-to-JSON schema extraction.
9. CSV/data ingestion.
10. Data science regression/classification.
11. RAG app over docs.
12. MCP/tool integration.
13. n8n workflow distillation.
14. CI/CD workflow generation.
15. Security alert triage.
16. Deployment readiness check.
17. Company/entity enrichment.
18. Contract/lease extraction.
19. Media generation pipeline.
20. Workflow replay debugger.

## Benchmark Plan

Build `AIDevObserver Session Review Benchmark v0`.

Start with:

```text
8 domains * 10 sessions = 80 fixtures
```

Domains:

- frontend
- backend
- data engineering
- data science
- software refactor
- document extraction
- workflow automation
- security/devops

Each fixture should include:

- session transcript
- known existing helper/template/primitive
- expected findings
- expected source_ref
- expected false-positive traps
- token/context estimate
- clean negative control

Primary metrics:

- high-confidence source_ref precision
- recall by finding type
- false-positive rate on clean sessions
- token estimate basis accuracy
- accepted/reused/dismissed simulation
- replay determinism

## Concrete Next Steps

1. Convert the first 20 primitive cards into `primitive_opportunity` rows unless source refs already exist.
2. Promote opportunity rows into candidate primitive drafts only after source evidence is attached.
3. Expand the local repo indexer for functions/classes/scripts/docs snippets into workflows, examples, tests, and configs.
4. Add source-backed finding cards to the first web scraper replay.
5. Add token estimate basis labels to reports.
6. Build 10 web-scraper and 10 bugfix session fixtures with expected source refs.
7. Add `Accept / Reuse / Dismiss / Wrong match / Already known` outcome values.
8. Generate negative memory from dismissed/wrong findings.
9. Build a simple source-backed template registry with 5 common workflows.
10. Wire AIDevObserver review to query helper/template/primitive registries.
11. Add source-ref top-1/top-3 gates to every new benchmark family.
12. Package one real install path, preferably CLI or Claude Code MCP, and prove it from fresh setup.
13. Re-run the external demo after the web scraper route can show an actual source_ref match.

## Product Principle

Do not start by trying to support every registry and every primitive type.

Start with the smallest loop that proves the wedge:

```text
AI agent creates code
  -> AIDevObserver finds the existing helper/template/primitive
  -> developer clicks Reuse
  -> registry memory improves
  -> next session avoids the duplicate work
```
