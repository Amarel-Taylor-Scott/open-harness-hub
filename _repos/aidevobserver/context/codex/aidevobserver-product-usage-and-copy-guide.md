# AIDevObserver Product, Usage, And Copy Guide

This guide summarizes how AIDevObserver works today, how the app is structured, how integrations are intended to work, and how to explain it to developers and managers.

The adoption story should lead with developer speed and token efficiency, not command-safety warnings. Developers already know some actions are unsafe. The more useful wedge is that AI agents often recreate existing utilities, reread too much context, miss cheaper deterministic routes, and spend expensive model loops on work the team has already solved.

## Short Positioning

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

The sharper public headline:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

The product subheadline:

```text
AIDevObserver reviews AI coding sessions, finds missed helpers, templates, workflows, and prior generated code in the primitive database, estimates wasted context, and turns accepted findings into reusable registry memory.
```

The product should not feel like a blocker or police layer. It should feel like a speed layer that catches duplicated effort and turns every AI coding session into reusable primitive memory.

The first public demo should explain AIDevObserver before explaining Teleon, Baltor, or the OpenHubForAI hub family. Those deeper systems matter because they power registry-backed findings, but they should be introduced as the technical drill-down after the user understands the immediate value.

For Claude Code / Cursor / VS Code style project setup, use:

```text
_repos/aidevobserver/context/codex/aidevobserver-claude-project-integration-template.md
```

The practical scaffold command is:

```bash
python3 _repos/shared-backend-components/scripts/aidevobserver_project_scaffold.py --framework python --write
```

## Product Family Context

AIDevObserver fits into the broader AI Done Right system as the developer-facing review and feedback loop:

| Surface | Role | Relationship To AIDevObserver |
| --- | --- | --- |
| AI Done Right | Company / portfolio surface | Explains the parent thesis: governed AI capability beats raw model calls |
| Teleon | Purpose-driven runtime and capability compiler | Supplies the candidate -> compiler -> PlanLock -> ledger -> proof/promotion architecture |
| Baltor | Governed context assurance | Supplies verified context and proof-backed retrieval paths that agents should reuse |
| AIDevObserver | AI coding session review, replay, and benchmark-lab workflows | Reviews coding sessions, finds reuse opportunities, and demonstrates compiled workflows |
| OpenHubForAI surfaces | Open registries for context, tools, skills, MCP servers, benchmarks, reviews, receipts, sandboxes, and related components | Provide the registry families that AIDevObserver can point developers toward |

Public naming rule:

```text
AIDevObserver = product
AIDevObserver Benchmark Lab = internal examples, replay, and primitive-first eval mode; not a branded public surface
Teleon = engine, mostly hidden in the first demo
OpenHubForAI = registry source, mentioned when showing matches
Baltor = verified context layer, introduced when context quality matters
AI Done Right = company / portfolio
```

The most important architecture boundary:

```text
Observer findings are candidate advice.
They do not serve truth and they do not promote artifacts by themselves.
```

## How AIDevObserver Works

The runtime shape is:

```text
AI coding session
  -> transcript or live event stream
  -> observer review engine
  -> ranked candidate findings
  -> human triage
  -> team reports
  -> registry memory and reuse signals
```

The Teleon-shaped long-term version is:

```text
session
  -> normalize messages
  -> search registries and known routes
  -> compare against deterministic tools and primitives
  -> produce candidate findings
  -> record outcomes
  -> update hashed source-ref memory, negative memory, reuse memory, and candidate composites
```

The important distinction:

```text
The LLM can help summarize or classify.
The compiler, registries, tests, and proof boundaries decide what is reusable truth.
```

For v1, use two modes:

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

Launch with Mode A. Show Mode B as the deeper reuse path.

## What The App Does

The AIDevObserver web app has two layers.

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

The app's example gallery is the `#/examples` route. Serve the built-out app locally via the showcase
(`OH_PRODUCT=aidevobserver`); any public tunnel URL is ephemeral and is not a stable address.

## What The Review Finds

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

Safety still matters, but it should not be the lead adoption message for developers.

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
| Outcome memory | Append Accept / Reuse / Dismiss metadata without transcript storage; stores hashed source-ref keys for ranking | Local-first service seam |
| Registry connectors | Compare session actions to internal primitives, templates, docs, and known-good routes | Seeded for local symbols, constants, docs, scripts, and opt-in review enrichment; broader primitive/workflow precision remains next |

The app documents these endpoints:

```text
POST /api/observer/review
GET  /api/observer/sessions
POST /api/observer/live
POST /api/observer/agentic
POST /api/observer/outcome
GET  /api/observer/outcomes
GET  /api/observer/registry/search
```

Public demos hide local session paths. Installed/local usage may opt in to local discovery. Transcript text is not stored by the outcome loop; only finding/session ids and the triage outcome are appended.
Local registry search is also opt-in for installed/local usage; public demos return no local hits rather than exposing repo paths.

Launch readiness is tracked separately in:

```text
_repos/aidevobserver/context/codex/aidevobserver-launch-readiness-and-alpha-plan.md
_repos/shared-backend-components/architecture/aidevobserver_launch_readiness_contract.json
_repos/shared-backend-components/scripts/check_aidevobserver_launch_readiness.py
```

The first local registry connector proof is:

```text
python3 _repos/shared-backend-components/scripts/check_aidevobserver_local_registry_connector.py --self-test
```

It proves candidate-only, repo-relative source refs for Python helpers,
constants, README/docs snippets, and package/pyproject commands. It is not yet
the full primitive/workflow/OpenHubForAI registry search layer.

Installed/local usage can also enrich review findings:

```text
POST /api/observer/review
body: { "messages": [...], "registry_cwd": "<repo-root>" }
```

This is honored only when local registry search is explicitly enabled. The
response attaches repo-relative `local_repo` source refs to findings and still
returns `serves_truth=false`.

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
| Dismissed findings | Suppresses matching source refs and improves false-positive control |
| Reuse rate by team | Shows adoption and dev shop speed |

The strongest long-term report is not "how many unsafe actions did we catch." It is:

```text
How much developer time and model spend did we save by routing agents to existing work?
```

## Registry Connections

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

The end state:

```text
developer asks agent to build something
  -> AIDevObserver notices an existing path
  -> report suggests a registry-backed route
  -> accepted finding strengthens future retrieval through source-ref memory
  -> repeated route can become a composite primitive candidate
```

## Current Demo Pack

The example sessions currently cover:

- web scraper for regulatory rates
- company/entity enrichment
- document-to-JSON schema extraction
- support ticket classification
- revenue regression pipeline
- safe pyprefix migration
- workflow replay debugger
- n8n workflow distillation

These sessions are synthetic and safe to demo. They are designed to show upload, replay, review, deterministic-tool positioning, and candidate-only findings.

Useful demo flow:

```text
Open examples
  -> replay web scraper
  -> show CandidateBundle / PlanDelta / PlanLock story
  -> show findings in Review
  -> show Reports for reuse and hours saved
  -> open Developer for integrations
```

## Copy Direction

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

## Implementation Notes

The current app is built around:

```text
_repos/aidevobserver/frontend/index.html
_repos/aidevobserver/frontend/aidevobserver-main.jsx
_repos/aidevobserver/frontend/aidevobserver.css
_repos/aidevobserver/frontend/examples/manifest.json
_repos/aidevobserver/frontend/examples/*.txt
_repos/aidevobserver/frontend/examples/*.jsonl
_repos/shared-backend-components/scripts/observer_local_service.py
_repos/teleon/backend/src/teleon/observer
_repos/shared-backend-components/scripts/aidevobserver_mcp_server.py
_repos/shared-backend-components/scripts/aidevobserver_hook.py
```

The public demo backend should stay safe:

- read-only
- no transcript storage
- no local path exposure
- public session discovery disabled unless explicitly enabled
- findings marked as candidate advice
- `serves_truth=false`

## Next Product Improvements

Highest leverage next steps:

1. Add token accounting middleware for reviewed sessions.
2. Connect review findings to actual internal registry lookup.
3. Add "already exists" cards that show the specific helper, primitive, workflow, or template.
4. Let users turn accepted findings into registry memory.
5. Add team report filters by repo, surface, component family, and workflow type.
6. Add a manager dashboard focused on developer speed, reuse, and token savings.
7. Add n8n workflow registry distillation examples.
8. Add media/image/video/audio pipeline registry examples.
9. Add extension-native review summaries for VS Code and Cursor.
10. Add false-positive feedback loops so dismissed findings improve ranking.

The practical goal is simple:

```text
Every AI coding session should make the next session cheaper, faster, and less redundant.
```

## V1 Plan And Feedback Response (merged 2026-06-28)

*Merged from the former `aidevobserver-feedback-response-and-v1-plan.md` (archived for lineage under
`_repos/_shared/archive/legacy/aidevobserver/`). The positioning, headline/subheadline, the V1 Mode A/B
split, and the ecosystem-story copy that file proposed are already reflected above; the planning content
below is the part that was unique to it.*

### Product name decision

```text
AIDevObserver = product
AIDevObserver Benchmark Lab = examples, replay, and primitive-first eval mode inside the product
```

Do not introduce AIDevExplorer as a separate public product or branded surface. Keep `aidevexplorer` as a
legacy/internal namespace until a deliberate migration removes it.

### Public story vs technical drill-down

First contact:

```text
AIDevObserver helps teams ship faster with AI coding agents by finding duplicated work, wasted context, and cheaper reusable paths.
```

Technical drill-down:

```text
Under the hood, AIDevObserver can route accepted findings into Teleon, where reusable primitives/templates become compiled, proof-gated capability routes. OpenHubForAI provides registry sources, and Baltor provides verified context when context truth matters.
```

### Minimum viable registry connector

Do not wait for full OpenHubForAI coverage. Minimum useful registry search: local repo functions/classes,
existing scripts, README/docs snippets, package scripts, examples, a known helper registry, 5-10 common
workflow templates, accepted-finding memory, and dismissed-finding negative memory.

Minimum "aha" finding:

```text
The agent wrote parse_csv(), but your repo already has utils.csv.read_rows.
```

Minimum source-backed finding fields:

| Field | Purpose |
| --- | --- |
| `type` | reinvention, wasted_context, alternative, agentic_loop, safety_signal |
| `message` | what happened |
| `suggestion` | what to do instead |
| `evidence` | short redacted transcript span |
| `source_ref` | existing helper/template/primitive/workflow/context pack |
| `confidence` | ranking score |
| `savings` | estimated hours/tokens/model calls avoided |
| `candidate` | true |
| `serves_truth` | false |

### First demo sequence

Landing page should point to `#/examples`. Recommended flow: open Examples -> replay "Web scraper for
regulatory rates" -> show ranked findings -> expand one finding into an existing template/helper route ->
show Reports with reuse/token savings -> open Developer integrations only after the core value is clear.

First three examples (in order) and why:

1. **Web scraper for regulatory rates** — familiar request, concrete one-off-code failure, clear reusable route (acquire -> fetch -> extract -> validate -> emit), easy to explain token/context waste and proof gates.
2. **Document-to-JSON extraction** — shows schema, provenance, source spans, and validation gates.
3. **Company/entity enrichment** — shows API/cache/provenance/confidence and repeated workflow reuse.

Defer from the first pitch: n8n workflow distillation, media pipeline registries, the full Teleon object
glossary, the Baltor dependency law, all OpenHubForAI hub families, and local session discovery as default.
Keep behind an advanced/technical view: CandidateBundle, PlanDelta, RemixSurface, VariationRecord, PlanLock,
ProofBundle, PromotionRecord.

### Buyer and user focus

Likely first buyers: AI platform lead, DevEx lead, engineering productivity lead, engineering manager with
heavy AI-agent usage, and the platform team responsible for internal tooling. Avoid leading with a
governance/surveillance framing — if the product is sold first as compliance, developer adoption gets harder.

Manager dashboard should emphasize: repeated work across the team, duplicate helpers caught, accepted reuse
suggestions, estimated model calls/tokens avoided, agent loops interrupted, missed registry routes, most
reinvented components, and teams/products with the highest AI waste. Safety metrics (secret-handling,
destructive-operation, missing-proof, privacy-sensitive signals) stay present but secondary.

### Benchmark decision

Build the AIDevObserver Session Review Benchmark v0 before trying to prove full Teleon workflow compilation.
It should test: reinvention detection, wasted-context detection, missed-deterministic-route detection,
agentic-loop detection, missing-proof detection, safety/secret redaction, registry-backed suggestion
precision, and replay determinism.

Initial 80-session fixture set (10 each): frontend, backend, data engineering, data science, software
refactor, document extraction, workflow automation, security/devops. Each fixture includes the transcript, a
known existing helper/template/primitive, expected findings, expected `source_ref`, expected false-positive
traps, a token/context estimate, and a clean-session negative control.

Primary metric: **high-confidence `source_ref` precision** (if source references are wrong, developers stop
trusting the product). Token savings report their basis: exact tokens when model logs exist, tokenizer
estimate when only a transcript exists, deterministic proxy when only file counts/chars exist.

### Highest-leverage changes and build order

Highest-leverage next changes: rewrite landing/demo copy around speed and reuse; make the first demo a
guided replay, not a dashboard; build the minimum registry connector; create the first 80-session benchmark;
make human triage the product flywheel.

Concrete build order (thin slices):

1. **Copy and demo flow** — lead headline, Examples as the primary route, web-scraper replay first, one expanded finding with `source_ref`, "estimated tokens avoided" with a basis label.
2. **Local registry connector** — index local functions/classes, scripts and package scripts, README/docs snippets, and examples; map common helper names to `source_ref`s.
3. **Triage flywheel** — Accept / Reuse / Dismiss / Not relevant / Already known / Wrong match; accepted findings become registry memory, dismissed/wrong findings become negative memory.
4. **Benchmark v0** — the 80 session fixtures, expected findings and `source_ref`s, clean negative controls, token/context estimates, replay-determinism checks.
5. **Teleon route drill-down** — accepted finding -> candidate route, simple template match, gap report when no route exists; keep PlanLock/proof detail behind the advanced view.
