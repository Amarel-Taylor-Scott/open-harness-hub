# AIDevObserver External Feedback Brief

**Date:** 2026-06-28  
**Audience:** external reviewer, AI product strategist, AI engineering agent, Claude/GPT review session  
**Purpose:** provide a standalone overview of AIDevObserver, its surrounding systems, current demo state, registry strategy, product positioning, and open questions.

## How To Review This Brief

Please review this as a product + architecture + go-to-market artifact.

Focus especially on:

- whether the positioning is compelling to developers and dev managers
- whether the product story clearly leads with developer speed and token savings
- whether the architecture is too complex for the first release
- whether the integration plan is realistic
- whether the benchmark plan proves the right claims
- whether the demo sequence makes sense for a friend, investor, technical buyer, or developer lead
- what should be cut, renamed, simplified, or moved later

Do not assume this is a finished commercial product. Treat it as an active product architecture and demo surface that is now being sharpened.

## Current Product Decision

The center of gravity is now:

```text
AIDevObserver is the practical developer-speed product.
Teleon, Baltor, and OpenHubForAI are the deeper infrastructure story underneath it.
```

First-contact users should understand this before they hear any architecture terms:

```text
Your AI coding agent is rebuilding code, helpers, workflows, or patterns that already exist in the primitive database.
AIDevObserver catches that and routes the session toward reusable work.
```

Public story:

```text
AIDevObserver reviews AI coding sessions, finds missed helpers, templates, workflows, and prior generated code in the primitive database, estimates wasted context, and turns accepted findings into reusable registry memory.
```

Technical drill-down:

```text
Under the hood, accepted findings can route into Teleon, where reusable primitives/templates become compiled, proof-gated capability routes. OpenHubForAI provides registry sources, and Baltor provides verified context when context truth matters.
```

This brief includes the full ecosystem because external agents need to understand the direction. The actual first demo should hide most of the ecosystem until the user asks for the technical explanation.

## Core Thesis

AIDevObserver reviews AI coding sessions and turns them into ranked reports that show where the agent:

- recreated code, helpers, workflows, or product surfaces that already exist
- spent too many tokens by reading or pasting too much context
- used a model loop where search, a registry lookup, or a deterministic tool would be cheaper
- repeated failed attempts, stalled, drifted, or ran a wasteful autonomous loop
- missed an internal primitive, template, workflow, or known-good route
- surfaced safety or compliance signals that a manager may still want to track

The core promise:

```text
Faster AI-assisted development by helping teams reuse what already exists.
```

The product should not feel like a blocker, police layer, or command-safety detector. Developers already know some actions are unsafe. The stronger adoption wedge is speed:

```text
Stop rebuilding the same utilities.
Spend model tokens on new work, not rediscovery.
Turn AI coding sessions into reusable primitive memory.
Route agents to cheaper deterministic paths.
```

Recommended headline:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

Recommended manager headline:

```text
Measure reuse, not just model usage.
```

Recommended report proof point:

```text
In 30 reviewed sessions, AIDevObserver found 42 reuse opportunities, 11 duplicate helpers, and 180k estimated prompt tokens avoided. Developers accepted 61% of high-confidence findings.
```

## One-Line Architecture

```text
AI developer session
  -> AIDevObserver review and replay
  -> Teleon registry/template/middleware search
  -> candidate findings and reuse suggestions
  -> human triage
  -> team reports
  -> reusable registry memory
```

Longer Teleon-shaped architecture:

```text
intent or session evidence
  -> primitive/template search
  -> CandidateBundle
  -> compact LLM PlanDelta, if ambiguity remains
  -> deterministic compiler
  -> registered RemixSurface / VariationRecord
  -> PlanLock
  -> runtime execution
  -> JSONL ledger
  -> proof / promotion
```

AIDevObserver is the adoption wedge. Teleon is the deeper capability compiler/runtime. Baltor is the governed context product. OpenHubForAI is the registry substrate.

For v1, split the architecture into two modes:

```text
Mode A: Observer Review Mode
  input: transcript/session
  output: ranked candidate findings
  truth level: candidate advice only
  runtime: lightweight

Mode B: Teleon Route Mode
  input: accepted finding or known task intent
  output: candidate route / PlanLock / proof path
  truth level: proof-gated
  runtime: compiler-backed
```

The product should launch with Mode A and show Mode B as the reuse path.

## Product Family Context

| Surface | Role | Relationship To AIDevObserver |
| --- | --- | --- |
| AI Done Right | Company / portfolio surface | Explains the parent thesis: governed AI capability beats raw model calls |
| AIDevObserver | AI coding session review, replay, examples, and middleware comparison | Reviews coding sessions, finds reuse opportunities, and demonstrates compiled workflows |
| Teleon | Purpose-driven runtime and capability compiler | Supplies the candidate -> compiler -> PlanLock -> ledger -> proof/promotion architecture |
| Baltor | Governed context assurance | Supplies verified context and proof-backed retrieval paths that agents should reuse |
| OpenHubForAI surfaces | Open registries for context, tools, skills, MCP servers, benchmarks, reviews, receipts, sandboxes, and related components | Provide the registry families that AIDevObserver can point developers toward |

The current portfolio is best understood as five surfaces with one shared design system:

| Surface | What It Is | Product Role |
| --- | --- | --- |
| AI Done Right | Parent / holding brand | Explains the mission and portfolio |
| Teleon | Purpose-driven, eval-gated, self-adaptive runtime | Compiles and executes capabilities through candidate/evidence/proof gates |
| Baltor | Managed, verified, provable context | Governs truth-bearing context served to agents |
| AIDevObserver | AI coding session review and in-session coaching | Finds wasted AI work and routes developers toward existing capabilities |
| OpenHubForAI | Open store and registry substrate | Supplies context, tools, skills, harnesses, templates, workflows, benchmarks, and proof artifacts |

The dependency law:

```text
Baltor -> Teleon -> OpenHubForAI
```

Baltor consumes Teleon as a tenant. Teleon consumes OpenHubForAI and other registry artifacts. OpenHubForAI remains independent and is not a truth authority.

Public naming recommendation:

```text
AIDevObserver = product
AIDevObserver Benchmark Lab = demo/example/eval mode inside the product, not a branded surface
Teleon = engine, mostly hidden
OpenHubForAI = registry source, mentioned when showing matches
Baltor = verified context layer, deferred unless context quality is the topic
AI Done Right = company / portfolio
```

For first-demo copy, avoid requiring people to understand all five surfaces before they understand AIDevObserver.

## Full Ecosystem Map

The ecosystem is layered, not a set of unrelated websites.

```text
AI Done Right
  portfolio, positioning, design system, operating standards

  AIDevObserver
    observes AI coding sessions
    finds reinvention, context waste, loops, and missed registry routes
    feeds candidate memory back into the ecosystem

  Teleon
    searches registries
    builds CandidateBundles
    accepts compact PlanDeltas only when needed
    compiles deterministic PlanLocks
    records ledgers, proofs, variations, and promotion candidates

  Baltor
    governs context truth
    reconciles, hardens, enriches, optimizes, and verifies context
    serves verified, current, provable context to agents

  OpenHubForAI
    open component and registry substrate
    hosts reusable AI system building blocks
    feeds Teleon and AIDevObserver search
```

The shortest version:

```text
OpenHubForAI stores reusable components.
Teleon compiles components into deterministic capability routes.
Baltor governs context truth.
AIDevObserver watches AI development and points agents back to existing routes.
AI Done Right explains and packages the system.
```

## How AIDevObserver Uses The Ecosystem

AIDevObserver should not be only a transcript summarizer. Its highest-value version is a search and comparison layer over the ecosystem.

Target review path:

```text
AI coding session evidence
  -> detect task intent and actions
  -> search local repo symbols and helpers
  -> search Teleon primitive/template/composite registries
  -> search OpenHubForAI hubs for tools, skills, harnesses, MCP servers, workflows, benchmarks, and proofs
  -> search Baltor governed context packs where verified context is needed
  -> compare agent path against known lower-cost route
  -> emit candidate finding with source_ref
  -> human triage: Accept / Reuse / Dismiss
  -> update reuse memory, negative memory, or promotion candidate
```

Example mappings:

| Session Evidence | Ecosystem Search | Likely Finding |
| --- | --- | --- |
| Agent writes a CSV parser | local repo helper graph + OpenToolsHub + Teleon primitive registry | "This parser already exists; reuse `utils.csv.read_rows`." |
| Agent scans 50 files with a model | deterministic project search + Teleon code-intelligence primitive | "Use deterministic symbol/file search before spending model context." |
| Agent builds a scraper from scratch | OpenTemplatesHub + workflow registry + Teleon template search | "This matches acquire -> fetch -> extract -> validate -> emit." |
| Agent creates a new MCP integration | OpenMCPHub + OpenToolsHub | "A governed MCP profile/tool contract already exists." |
| Agent pastes a huge schema | OpenCompressionHub + Baltor optimization methods | "Use a shaped context pack or schema slice." |
| Agent repeats failed test loops | AIDevObserver negative memory + Teleon proof history | "Stop retrying the same path; switch strategy or surface blocker." |
| Agent proposes document extraction | OpenHubForAI harness/pipeline registry + Teleon document template | "Use bounded extractor + schema/span gates instead of free-form JSON." |
| Agent creates an n8n-like workflow | workflow registry ingestion + Teleon graph distillation | "Import/distill existing workflow graph into candidate primitives." |
| Agent uses media generation code | media primitive registry + artifact/gate records | "Use model route + safety/quality gate + artifact refs." |

The key reviewer question:

```text
Does this product become much more valuable when it can say "this already exists here" instead of just "this looks inefficient"?
```

## OpenHubForAI And Hub Families

OpenHubForAI is the open store both products consume. It is not just documentation. It is the component, harness, skill, tool, workflow, and proof substrate that AIDevObserver should search.

The underlying catalog models AI systems at four layers:

```text
Layer 4 - Benchmarks and evaluations
Layer 3 - Pipelines
Layer 2 - Harnesses
Layer 1 - Knowledge packs, logic packs, rule packs, tools, personas, adapters, schemas
```

Everything reduces to seven broad primitives:

| Primitive | Meaning |
| --- | --- |
| Input | Typed input: text, document, HTML, PDF, image, video, audio, table, code, or combination |
| Knowledge Corpus | Facts: RAG corpora, tables, directories, citation graphs, labeled datasets |
| If Statement | Conditions: rules, classifiers, regexes, heuristics, policy checks, routing logic |
| Action | Things that do work: tools, processors, harnesses, adapters, rubrics, benchmarks |
| Loop | Orchestration: branch, retry, for-each, map-reduce, agent loop, pipeline |
| Stop / End | Guards, gates, terminal halts |
| Output | Result object plus trace, artifact, receipt, or report |

AIDevObserver can search these to decide whether the agent is building something the ecosystem already represents.

### Live OpenHubForAI Registry Families

| Hub | What It Holds | How AIDevObserver Uses It |
| --- | --- | --- |
| OpenContextHub | Context packs and corpora | Finds existing facts/context before agents paste or recreate context |
| OpenSkillsHub | Composable evaluated skills | Finds higher-level capabilities the agent is reimplementing |
| OpenToolsHub | Governed tools and callable contracts | Finds existing tools/helpers instead of new code |
| OpenSkillToTool | Skill-to-tool conversion records | Finds callable surfaces for known skills |
| OpenMCPHub | MCP server profiles, conformance, install metadata | Finds existing MCP/tool integrations and safer install paths |
| OpenCompressionHub | Compression, token budgeting, fidelity benchmarks | Explains context waste and suggests cheaper shaped context |
| OpenBenchmarkHub | Benchmark cards and result records | Grounds "this route works" in evidence |
| OpenReviewHub | Paper/repo review intelligence | Converts external claims/repos into reproducibility-aware candidates |

### Preview / Future Hub Families

These are not necessarily public products yet, but they define important registry lanes:

| Hub | What It Holds | Why It Matters To AIDevObserver |
| --- | --- | --- |
| OpenTemplatesHub | Template families and scaffolds | Finds pipeline shapes before an agent writes bespoke glue |
| OpenEndpointHub | LLM endpoint and gateway due diligence | Helps route tasks to acceptable model/provider lanes |
| OpenEnvironmentHub | Eval environments and reward specs | Grounds agent benchmarks in reproducible task worlds |
| OpenSandboxHub | Sandbox runtimes and conformance | Helps classify safe execution environments |
| OpenAgentHub | Agent runtime registry | Describes the runtimes that execute agent loops |
| OpenReceiptHub | Portable receipts and attestations | Records what model/tool/runtime actually served |
| OpenStateHub | Durable agent state and memory | Tracks governed working state distinct from truth context |
| OpenRoutingHub | Model-routing policy | Routes work by cost, latency, privacy, and capability |
| OpenReconciliationHub | Context reconciliation methods | Detects duplicate/conflicting context and object identity problems |
| OpenHardeningHub | Context hardening methods | Converts brittle text into refreshable knowledge objects |
| OpenEnrichmentHub | Context enrichment methods | Adds metadata, relationships, service graph links, and schema facts |
| OpenOptimizationHub | Context shaping methods | Summarizes, distills, ranks, and fits context to a task budget |
| OpenVerificationHub | Verification and citation methods | Binds claims to source evidence and proof |

Important nuance: the Open*Hub registries are internal to the OpenHubForAI ecosystem layer. They are registry lanes, not all separate parent-level products.

## Teleon In More Detail

Teleon is the capability compiler and deterministic runtime layer. It should be the system that turns registry evidence into executable or rejectable plans.

Teleon should maintain multiple planning routes:

```text
exact promoted composite reuse
  -> deterministic template fill
  -> CandidateBundle + compact PlanDelta
  -> deterministic remix/repair
  -> full PipelineIR only when needed
  -> source-level codegen as last resort
```

Core Teleon objects:

| Object | Role |
| --- | --- |
| PrimitiveIdentity | Stable registry identity |
| CallableSurface | Observed Python/function/object evidence |
| PrimitiveRecord | Canonical registry row |
| TemplateRecord | Reusable typed pipeline skeleton |
| CandidateBundle | Compact LLM/search boundary |
| PlanDelta | Small model output selecting candidates/remixes |
| RemixSurface | Deterministic variation menu |
| VariationRecord | Record of a remix and proof obligations |
| PlanLock | Deterministic execution manifest |
| Ledger | Observed runtime truth |
| ProofBundle | Evidence bundle |
| PromotionRecord | Permission to serve or reuse as truth-backed memory |

For AIDevObserver, Teleon matters because the best finding is not just:

```text
This was inefficient.
```

It is:

```text
This matches an existing primitive/template/composite route; here is the cheaper path.
```

## Baltor In More Detail

Baltor is the governed context assurance product. It answers a different question than AIDevObserver:

```text
Can this context be trusted, kept current, proven, and served to agents?
```

Baltor's conceptual stages map to several preview hub families:

| Baltor Stage | Related Hub | What It Does |
| --- | --- | --- |
| Reconcile | OpenReconciliationHub | Deduplicate, align objects, separate comments from decisions, surface contradictions |
| Harden | OpenHardeningHub | Replace brittle text with refreshable knowledge objects |
| Enrich | OpenEnrichmentHub | Add metadata, relationships, architecture links, schema facts, and source relationships |
| Optimize | OpenOptimizationHub | Shape, summarize, distill, rank, and fit context to budget |
| Verify | OpenVerificationHub | Bind claims to source evidence, hashes, citations, and proof |

AIDevObserver should use Baltor-style context when reviewing sessions that paste large docs, rely on stale context, quote unverifiable facts, or ask an agent to act from weak project memory.

Example:

```text
agent pastes full architecture docs
  -> AIDevObserver flags context waste
  -> OpenCompressionHub suggests shaping route
  -> Baltor pack supplies verified, current, optimized context
  -> Teleon can later compile the route into a reusable context-serving primitive
```

## Truth Boundary

The most important architecture boundary:

```text
Observer findings are candidate advice.
They do not serve truth and they do not promote artifacts by themselves.
```

The LLM can help summarize, classify, or propose. It cannot decide truth, create canonical identities, promote artifacts, disable gates, or bypass compiler checks.

Canonical vocabulary:

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

For AIDevObserver specifically:

```text
finding = candidate advice
accepted finding = useful human signal
registry memory = reusable signal, still not served truth
promotion = proof-backed path only
```

## Current Demo URL

Current public demo URL for this session:

```text
https://terminology-complexity-life-blades.trycloudflare.com/#/examples
```

Quick tunnels are temporary. Public demos should use `*.trycloudflare.com` URLs, not machine-local URLs.

Important demo routes:

```text
https://terminology-complexity-life-blades.trycloudflare.com/#/examples
https://terminology-complexity-life-blades.trycloudflare.com/#/review
https://terminology-complexity-life-blades.trycloudflare.com/#/sessions
https://terminology-complexity-life-blades.trycloudflare.com/#/agentic
https://terminology-complexity-life-blades.trycloudflare.com/#/reports
https://terminology-complexity-life-blades.trycloudflare.com/#/developer
```

Public demo safety:

- local session discovery is hidden in public demos
- review is read-only
- no transcript storage is intended
- findings are candidate-only
- `serves_truth=false`

## Current App Surface

The app has two layers.

Marketing/demo layer:

- `#/how` explains session-to-report flow
- `#/runs` explains where integrations run
- `#/examples` shows replayable demo sessions
- `#/demo` lets someone paste or load a session and see ranked findings
- `#/trust` explains read-only, suggestion-only behavior

Logged-in/product layer:

- `#/dashboard` shows local review activity and reuse rollups
- `#/review` accepts pasted or uploaded session text and returns findings
- `#/sessions` discovers local sessions only when explicitly enabled; public demos hide local paths
- `#/findings` shows candidate findings and human outcomes
- `#/agentic` reviews autonomous loops for stalls, thrash, repeated failures, budget overrun, and drift
- `#/examples` replays synthetic AIDevObserver benchmark-lab sessions
- `#/reports` summarizes reuse, hours saved, context waste, and cheaper deterministic paths
- `#/developer` documents API endpoints and integration commands
- `#/settings` shows connection settings and registry preferences
- `#/help` explains quick start paths

Current high-level app files:

```text
_repos/aidevobserver/frontend/index.html
_repos/aidevobserver/frontend/aidevobserver-main.jsx
_repos/aidevobserver/frontend/aidevobserver.css
_repos/aidevobserver/frontend/examples/manifest.json
_repos/aidevobserver/frontend/examples/*.txt
_repos/aidevobserver/frontend/examples/*.jsonl
scripts/observer_local_service.py
_repos/teleon/backend/src/teleon/observer
scripts/aidevobserver_mcp_server.py
scripts/aidevobserver_hook.py
```

## API Seam

The app documents this same-origin observer API seam:

```text
POST /api/observer/review
GET  /api/observer/sessions
POST /api/observer/live
POST /api/observer/agentic
```

Endpoint intent:

| Endpoint | Purpose |
| --- | --- |
| `POST /api/observer/review` | Review a pasted/uploaded/discovered session and return ranked candidate findings |
| `GET /api/observer/sessions` | Discover local Claude Code / Codex sessions when local discovery is explicitly enabled |
| `POST /api/observer/live` | Intra-session check with an interruption budget |
| `POST /api/observer/agentic` | Review autonomous agent loops for stalls, thrash, drift, and budget waste |

## What AIDevObserver Should Find

Primary developer-speed categories:

| Category | What It Means | Example |
| --- | --- | --- |
| Reinvention | The agent rebuilt something already present in the repo or registry | Creates a CSV parser when `utils.csv.read_rows` already exists |
| Stack reinvention | The agent introduces a new stack or library where the product already has a standard path | Adds a new scraping framework instead of the existing fetch/extract pipeline |
| Product reinvention | The agent starts building a product surface that already exists in the portfolio | Rebuilds an OpenHub-like registry page |
| Wasted context | The agent pasted or reread too much source, schema, or log context | Reads 50 files to find one constant |
| Missed cheaper path | The agent used expensive model reasoning where search, registry lookup, or deterministic tooling would work | Uses a model loop instead of project search |
| Agentic loop | An autonomous agent repeats failed actions, stalls, drifts, or burns budget | Keeps editing the same file without a passing proof |
| Missing proof | The agent made a change without the expected test, replay, contract, or validation | Refactor without contract report |

Secondary manager/compliance categories:

| Category | What It Means |
| --- | --- |
| Safety signal | Destructive operation, secret-handling issue, unsafe tool call, or compliance-sensitive step |
| Privacy signal | Transcript or artifact may expose sensitive content |
| Governance signal | A finding needs policy, review, or proof before it can become reusable truth |

Safety still matters, but it should not be the lead developer adoption message.

## Product Positioning

Recommended homepage message:

```text
AIDevObserver shows where AI coding agents recreate existing work, waste context, or miss cheaper deterministic paths, so teams ship faster and reuse spreads.
```

Recommended report message:

```text
See which known primitives, helpers, workflows, and product surfaces your agents keep rebuilding, where tokens are being spent, and which registry-backed routes are saving time.
```

Recommended developer message:

```text
Before the agent writes another helper, AIDevObserver checks whether the primitive database already knows one.
```

Lead with:

- speed
- reuse
- token savings
- finding existing work
- primitive memory
- deterministic cheaper paths
- developer adoption

Downplay as the lead:

- command-safety-first messaging
- policing
- blocking
- surveillance
- compliance-first language

Keep, but place in manager/compliance sections:

- destructive operations
- secret handling
- unsafe tool calls
- audit logs
- governance and policy review

## Developer Quick Start

Best first experience:

1. Open the example sessions page.
2. Replay the web scraper, document extraction, or pyprefix migration example.
3. Inspect findings for reinvention, context waste, cheaper deterministic routes, and missing proofs.
4. Try the Review page with a real or synthetic AI coding transcript.
5. Mark findings as Accept, Reuse, or Dismiss so the report becomes useful registry memory.

What developers should care about:

- fewer repeated agent attempts
- less prompting and context stuffing
- faster discovery of existing utilities
- fewer duplicate helpers
- faster path from AI output to tested, reusable code
- better handoff from one developer's session to the rest of the team

Developer-facing copy should use phrases like:

```text
Find the helper your agent missed.
Stop rebuilding the same utilities.
Turn AI sessions into reusable primitive memory.
Spend model tokens on new work, not rediscovery.
Route agents to the cheaper deterministic path.
```

## Manager Quick Start

Best first experience:

1. Open Reports.
2. Review reuse rate, hours saved, and where reinvention concentrates.
3. Look at repeated patterns by team, product area, or component family.
4. Use accepted findings to decide which internal utilities, primitives, docs, or templates need better discoverability.
5. Track whether teams move from repeated bespoke agent work toward registry-backed reuse.

What managers should care about:

- developer throughput
- AI spend per shipped change
- repeated work across the dev shop
- team-level reuse rate
- agent-loop waste and stalled work
- proof and governance for high-impact changes
- safety/compliance signals as a secondary operational view

Manager-facing copy should use phrases like:

```text
See where AI coding time is going.
Find repeated work across the team.
Measure reuse, not just model usage.
Turn agent sessions into operational intelligence.
Reduce avoidable AI spend without slowing developers down.
```

## Integration Modes

AIDevObserver is designed to meet teams where AI development already happens.

| Integration | Intended Use | Current Status |
| --- | --- | --- |
| Manual paste/upload | Fastest way to review any AI coding transcript | Active in app |
| Replay examples | Demo common sessions without real customer data | Active in app |
| Local session discovery | Find Claude Code / Codex sessions on a developer machine | Implemented, disabled by default in public demo mode |
| CLI | Review the latest or selected session from terminal/CI | Documented in app |
| MCP server | Let Claude Code hand session context to AIDevObserver tools | Documented and test-covered |
| PreToolUse hook | Show non-blocking coaching during a session | Documented as read-only advisory |
| VS Code / Cursor extension | Editor-native session review | Product surface copy exists; extension should use same review API |
| API | Review, sessions, live checks, and agentic supervision endpoints | Active backend seam |
| Registry connectors | Compare session actions to internal primitives, templates, docs, and known-good routes | Core next integration |

## Registry Strategy

AIDevObserver should connect to registries before it tries to generate advice. The useful comparison is:

```text
What the agent is doing
vs
what the primitive database already knows
```

Registry families to connect:

- repo utilities and internal helpers
- Python callable surfaces and primitive records
- Teleon templates, CandidateBundles, PlanLocks, and composites
- Baltor verified context packs
- OpenHubForAI component records
- n8n workflow graphs and distilled primitives
- MCP server profiles and tool registries
- document extraction schemas and validators
- media/image/video/audio pipeline components
- benchmarks, proofs, and known-good chains
- negative memory from failed or wasteful sessions

### Search Contract

AIDevObserver should treat each session as evidence, not as the truth source.

Search flow:

```text
session event or transcript span
  -> classify action intent
  -> extract candidate task, artifact, function, command, file, and workflow names
  -> query local repo indexes
  -> query OpenHubForAI component indexes
  -> query Teleon primitive/template/composite indexes
  -> query Baltor context packs when the issue is context quality or freshness
  -> query negative memory for known-bad routes and repeated loops
  -> rank possible matches by contract fit, proof/trust/readiness, freshness, cost, and developer usefulness
  -> emit finding with source_ref and suggested lower-cost route
```

The review should prefer deterministic evidence before asking a model to infer:

```text
exact symbol / file / primitive match
  -> semantic registry match
  -> known-good chain match
  -> compact LLM classification
  -> gap report
```

Minimum fields for a useful source-backed finding:

| Field | Meaning |
| --- | --- |
| `type` | reinvention, wasted_context, alternative, agentic_loop, safety_signal, etc. |
| `message` | what happened in the session |
| `suggestion` | what to do instead |
| `evidence` | short redacted session span |
| `source_ref` | existing component/helper/primitive/template/workflow/context pack |
| `confidence` | ranked confidence |
| `savings` | optional estimated hours/tokens/model calls avoided |
| `serves_truth` | always false for raw findings |
| `candidate` | true unless promoted by a separate proof path |

Ranking should weight:

- exact contract match over vague semantic similarity
- promoted/verified primitives over candidate records
- local repo helper over external suggestion when both satisfy the task
- deterministic search over model-only inference
- lower token/cost route when quality is equivalent
- known-good chain over newly generated glue
- negative memory suppressions when a route has failed before

### Example Search Outcomes

| Agent Behavior | Registry Match | Suggested Finding |
| --- | --- | --- |
| Writes `parse_csv()` | local helper + OpenToolsHub tool contract | Reuse existing CSV reader |
| Creates one-off scraper | OpenTemplatesHub scrape template + Teleon primitive chain | Use scrape/validate/emit template |
| Installs unknown MCP server | OpenMCPHub profile | Use governed MCP profile or flag missing conformance |
| Pastes whole schema | OpenCompressionHub + Baltor optimized context pack | Use schema slice/context pack |
| Rebuilds document extractor | OpenHubForAI pipeline + Teleon bounded extractor template | Use document extract/validate/emit route |
| Builds n8n-like workflow manually | workflow registry | Import/distill existing workflow JSON |
| Loops over same failing test | negative memory + proof history | Stop loop and switch strategy |

The end state:

```text
developer asks agent to build something
  -> AIDevObserver notices an existing path
  -> report suggests a registry-backed route
  -> accepted finding strengthens future retrieval
  -> repeated route can become a composite primitive candidate
```

## OpenHubForAI Registry Types

The broader repository models a host-agnostic, industry-agnostic registry/catalog of AI system components.

Core catalog families:

- harnesses
- pipelines
- rule packs
- knowledge packs
- tools
- personas
- adapters
- rubrics
- datasets / examples / benchmark specs where applicable

Hard taxonomy rules:

- pipelines should not wire raw rule packs directly to a model; rule packs reach a model through a harness
- volatile facts go in tools or knowledge packs, not personas
- every harness declares `model_targets`, even when the value is `none`
- privacy boundaries travel with the component, not the deployment
- reproducibility is first-class
- no magic values; values that must update in more than one place need one source of truth

## Workflow Registry Strategy

n8n workflows are high-priority because they are easy to scrape, inspect, normalize, and distill.

n8n import shape:

```text
n8n JSON
  -> redact credentials and private URLs
  -> parse node graph
  -> infer triggers, actions, transforms, and side effects
  -> convert nodes into candidate primitives
  -> convert edges into candidate template/chain records
  -> produce CandidateBundle or gap report
  -> never serve truth without proof/promotion
```

Potential workflow registries:

- n8n
- GitHub Actions
- Airflow
- Dagster
- Temporal
- Argo
- Flyte
- Zapier/Make-style automations
- ComfyUI and media workflow graphs

## Multimodal / Media Registry Strategy

This architecture should not be limited to code primitives.

For media workflows, primitives can be:

- image generation
- image safety gate
- image description / captioning
- image-to-video generation
- text-to-video generation
- video stabilization
- audio generation
- transcription
- speech synthesis
- encoding / transcoding
- quality gates
- artifact storage
- provenance and rights checks

Media primitive shape:

```text
input artifact or prompt
  -> model/tool primitive
  -> ArtifactRef output
  -> quality/safety gate
  -> encode/package
  -> ledger/proof
```

This lets AIDevObserver and Teleon compare agent-generated media pipelines against existing registry components, just like code or document workflows.

## Current Replayable Demo Pack

The demo pack currently contains 8 synthetic sessions:

| ID | Title | Industry | Task Family |
| --- | --- | --- | --- |
| `web-scraper-regulatory-rates` | Web scraper for regulatory rates | software.data_collection | web_scraping |
| `company-entity-enrichment` | Company/entity enrichment | sales.data_operations | entity_resolution |
| `document-json-schema-extraction` | Document to JSON schema extraction | finance.document_intelligence | document_extraction |
| `support-ticket-classification` | Support ticket classification | customer_support | classification |
| `revenue-regression-pipeline` | Revenue regression pipeline | data_science | regression |
| `safe-pyprefix-migration` | Safe pyprefix migration | software_engineering | safe_refactor |
| `workflow-replay-debugger` | Workflow replay debugger | devtools | ledger_replay |
| `n8n-workflow-distillation` | n8n workflow distillation | automation | workflow_registry |

Recommended public demo sequence:

1. Web scraper for regulatory rates.
2. Document-to-JSON extraction.
3. Company/entity enrichment.
4. Safe pyprefix migration.
5. Workflow replay debugger.
6. n8n workflow distillation.

This sequence shows:

```text
common coding request
  -> registry/template route
  -> compact plan
  -> compiler checks
  -> locked execution
  -> ledger/proof
  -> reusable composite candidate
```

## Token Savings Model

AIDevObserver saves tokens by preventing common expensive patterns:

- repeated full-repo scans by the model
- large schema or log pastes when only a slice is needed
- agents rebuilding helpers instead of finding existing ones
- repeated failed edit/test loops without new information
- runtime model calls for tasks that deterministic search or a registry can answer
- new code generation when an existing primitive, template, n8n workflow, or composite path exists

Metrics to wire into the product:

| Metric | Why It Matters |
| --- | --- |
| Prompt tokens avoided | Shows context savings |
| Model calls avoided | Shows cheaper deterministic replacement |
| Duplicate helpers caught | Shows direct engineering reuse |
| Existing components reused | Shows registry value |
| Agent loop interruptions | Shows saved time before thrash continues |
| Hours saved | Manager-friendly summary |
| Accepted findings | Separates useful signal from noise |
| Dismissed findings | Improves ranking and false-positive control |
| Reuse rate by team | Shows adoption and dev shop speed |

The strongest long-term report is not:

```text
How many unsafe actions did we catch?
```

It is:

```text
How much developer time and model spend did we save by routing agents to existing work?
```

## Evaluation / Benchmark Plan

The evaluation should be inspired by compiled-AI benchmarks but adapted to AI programming sessions.

Reference:

```text
Compiled AI: Deterministic Code Generation for LLM-Based Workflow Automation
https://arxiv.org/abs/2604.05150
```

AIDevObserver does not yet compile all business workflows. It reviews AI coding sessions, calls deterministic middleware, checks registries, measures token waste, and emits candidate findings that humans triage.

What must be proven:

```text
detects reinvention grounded in registries
detects token waste and cheaper deterministic routes
detects safety and secret-handling signals with redaction
detects agentic loops, stalls, and repeated failures
calls middleware primitives instead of relying only on LLM judgment
records token usage or deterministic estimates
compares baseline model-heavy usage against registry/tool/compiled routes
produces stable results on replay
keeps every finding candidate-only until human triage
```

Benchmark families:

1. Programming session review.
2. Middleware registry search.
3. Token economics.
4. Static safety / redaction.
5. Compiled route comparison.
6. Agentic loop supervision.
7. Replay determinism.
8. Test-of-tests / fixture integrity.

Required fixture domains:

```text
frontend
backend
software_engineering
data_science
data_engineering
devops
security
document_intelligence
workflow_automation
media_pipeline
```

Metrics:

- finding recall by type
- confidence ordering
- false positives on clean sessions
- registry hit rate
- source reference coverage
- reuse suggestion precision
- missed existing component rate
- baseline input/output tokens
- observer middleware tokens
- deterministic tool calls
- estimated tokens saved
- break-even repeat count
- replay digest stability
- accepted / reused / dismissed human outcomes

## Current Verification Status

Recent checks passed:

```text
python3 scripts/check_aidevobserver_example_sessions.py --self-test
python3 scripts/check_observer_local_service.py --self-test
python3 scripts/check_observer_review.py --self-test
```

Observed current behavior:

- example pack has 8 replay demos
- example pack has 16 upload/download files
- governed findings remain `serves_truth=false`
- observer service returns governed candidate findings
- local session discovery is disabled in public demo mode
- public demo routes are served through a `trycloudflare.com` tunnel

## Main Open Product Questions

Please answer these directly:

1. Is "developer speed through reuse and token savings" the right lead positioning?
2. Should safety/compliance be a secondary manager lens, or should it be more prominent?
3. Is "AIDevObserver" the right product name, and what should the unbranded benchmark-lab mode be called in demos?
4. Should the first buyer be a developer/team lead, engineering manager, platform team, or AI governance buyer?
5. What is the simplest first paid product: paste/upload reviews, local session discovery, team reports, editor extension, MCP server, or registry connector?
6. What should be cut from the first demo to avoid overwhelming users?
7. Is the Teleon/CandidateBundle/PlanLock story useful in the AIDevObserver demo, or should it stay mostly behind the scenes?
8. Are n8n workflow distillation and media pipeline registries helpful examples, or too broad for the first pitch?
9. What evidence would make the token-savings claim credible?
10. What is the most important benchmark to build first?

## Main Open Architecture Questions

Please challenge these assumptions:

1. Should AIDevObserver depend on Teleon registries early, or start as a lighter transcript analyzer?
2. Should registry search be deterministic first, LLM-assisted second?
3. How should accepted findings become reusable memory without polluting the registry?
4. What is the minimal canonical record needed for an "existing helper" or "existing workflow" suggestion?
5. Should local session discovery be part of the product, or should upload/paste remain the main flow?
6. How should token savings be measured when exact model token data is unavailable?
7. How should the system avoid false positives that annoy developers?
8. How should it distinguish "valid new code" from "reinvented code"?
9. What should the human triage loop look like?
10. What should be proof-gated before a finding can become registry memory?

## Main Open Demo Questions

Please review the demo flow:

1. Open examples.
2. Replay web scraper.
3. Show ranked review findings.
4. Show reports for reuse and hours saved.
5. Open developer integrations.
6. Explain registry-backed future path.

Questions:

- Is this sequence clear to someone outside the project?
- Should the first example be a web scraper, document extraction, company enrichment, or pyprefix migration?
- Does the app explain what to do without a salesperson narrating it?
- Is the public demo safe enough to send to a friend?
- What route should the landing page point to first: examples, review, reports, or developer?

## Main Open Ecosystem Questions

Please evaluate the broader ecosystem story:

1. Does the relationship between AIDevObserver, Teleon, Baltor, and OpenHubForAI make sense?
2. Should AIDevObserver explicitly show hub search results in the UI, or should that stay behind the finding card?
3. Which hub families are most important for first adoption: OpenToolsHub, OpenTemplatesHub, OpenMCPHub, OpenCompressionHub, OpenBenchmarkHub, or Baltor context packs?
4. Is OpenHubForAI best explained as an "open store," "registry substrate," "component graph," or something else?
5. Does the "Baltor -> Teleon -> OpenHubForAI" dependency law clarify trust, or does it create too much explanation overhead?
6. Should managers see ecosystem-level reports like "most reinvented internal primitive" and "most missed registry route"?
7. Should developers see exact registry matches inline, or should AIDevObserver only summarize the better route?
8. What is the minimum registry search that makes the product credible?
9. Should n8n/workflow registries and media registries be shown in the first external demo, or deferred?
10. What terms should be renamed so an external buyer understands the system faster?

## Suggested Reviewer Output Format

Please return feedback in this structure:

```text
1. Strongest parts
2. Confusing parts
3. Product positioning critique
4. Developer adoption critique
5. Manager/buyer critique
6. Architecture critique
7. Demo critique
8. Benchmark/evidence critique
9. Ecosystem / registry critique
10. What to cut or defer
11. Highest-leverage next 5 changes
```

## Current Bottom Line

AIDevObserver should be framed as:

```text
The speed and reuse layer for AI coding sessions.
```

Not primarily:

```text
A risky-command detector.
```

The strongest product loop is:

```text
AI session happens
  -> AIDevObserver finds duplicated work and token waste
  -> developer accepts/reuses the better path
  -> team learns what should be easier to find
  -> registry improves
  -> next AI session gets cheaper and faster
```

That is the story external feedback should validate or reject.
