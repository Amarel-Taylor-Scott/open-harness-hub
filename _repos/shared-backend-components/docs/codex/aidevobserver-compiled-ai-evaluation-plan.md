# AIDevObserver Compiled-AI Evaluation Plan

This plan turns AIDevObserver from a useful demo into a benchmarked middleware layer for real AI-agent programming
sessions.

The near-term goal:

```text
prove AIDevObserver on programming-session evidence
  before applying the same evaluation logic to Teleon compiled capabilities
```

The evaluation is inspired by the shape of the Compiled AI paper: task completion, determinism, security, token
amortization, cost, and repeated execution. The adaptation is different: AIDevObserver does not compile business
workflows yet. It reviews AI coding sessions, calls deterministic middleware, checks registries, measures token waste,
and emits candidate findings that humans triage.

Reference:

```text
Compiled AI: Deterministic Code Generation for LLM-Based Workflow Automation
https://arxiv.org/abs/2604.05150
```

## Product Split

```text
AIDevObserver:
  developer-facing session review, examples, transcript replay, middleware comparison,
  and an internal benchmark lab

Teleon:
  compiler/runtime layer; CandidateBundle -> PlanDelta -> PlanLock -> execution ledger

Baltor:
  governed context; decides what becomes verified, current, and served

OpenHubForAI:
  public/open registry substrate; components, workflows, tools, templates, harnesses

AI Done Right:
  portfolio and positioning layer; owns no runtime truth
```

## What We Need To Prove

AIDevObserver should be tested against actual AI programming sessions and realistic synthetic fixtures.

It must prove:

```text
detects reinvention grounded in registries
detects token waste and cheaper deterministic routes
detects risky commands and secrets with redaction
detects agentic loops, stalls, and repeated failures
calls middleware primitives instead of relying only on LLM judgment
records token usage or deterministic estimates
compares baseline model-heavy usage against registry/tool/compiled routes
produces stable results on replay
keeps every finding candidate-only until human triage
```

## Benchmark Families

### 1. Programming Session Review

Replay Claude Code, Codex, Cursor, or other AI-agent programming sessions.

Measure:

```text
finding recall by type
confidence ordering
false positives on clean sessions
deterministic replay digest
human triage outcome: accepted / reused / dismissed
```

### 2. Middleware Registry Search

The observer should not merely say "this looks reinvented." It should ground the claim.

Required middleware:

```text
registry.hybrid_search
registry.primitive_match
registry.reinvention_guard
registry.dependency_graph_query
deterministic.rg_search
deterministic.ast_symbol_lookup
```

Measure:

```text
registry hit rate
source_ref coverage
top-1 source_ref accuracy
top-3 source_ref accuracy
reuse suggestion precision
missed existing component rate
```

### 3. Token Economics

Compare the baseline agent path against the observer-recommended path.

Examples:

```text
baseline: upload entire repo to model to find a constant
observer: rg + targeted file read

baseline: ask model to inspect all files for an API
observer: AST symbol lookup + dependency graph query

baseline: repeated full-document prompting
observer: compiled extractor + schema gate
```

Measure:

```text
baseline input/output tokens
observer middleware tokens
deterministic tool calls
estimated tokens saved
break-even repeat count
execution tokens after compile
```

### 4. Security / Static Safety

Detect:

```text
force push to main
rm -rf style destructive commands
secret-shaped strings
auth headers in pasted cURL or n8n JSON
prompt-injection-like instructions
private-host unbounded egress
```

Hard requirement:

```text
never echo secret evidence
```

### 5. Compiled Route Comparison

For repeated tasks, compare ad hoc model work against a compiled/reused route.

Example:

```text
first run:
  model helps select/compile candidate route

later runs:
  deterministic tools execute route without runtime model tokens
```

Measure:

```text
compile success
PlanLock hash stability
execution success
token amortization ratio
quality gate pass rate
```

## Use-Case Fixture Matrix

The contract requires at least one fixture across these engineering domains:

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

And many industries:

```text
healthcare
finance
legal
logistics
ecommerce
insurance
education
manufacturing
media
sales_operations
software_tools
public_sector
saas
security
```

Initial fixture examples are in:

```text
architecture/aidevobserver_compiled_ai_evaluation_contract.json
```

## Test-Of-Tests

The benchmark must test itself.

Meta-checks:

```text
contract has at least 12 use-case fixtures
contract covers every required engineering domain
contract covers at least 10 industries
every fixture declares registry primitives
every fixture declares expected observer themes
every fixture declares a token test
every smoke session runs through the real review engine
every smoke finding is candidate=true and serves_truth=false
clean counterexamples are included
security cases are included
the prompt can generate new fixtures without served-truth claims
```

Checker:

```bash
python3 scripts/check_aidevobserver_compiled_ai_evaluation.py --self-test
```

## Fixture Generation Prompt

Use:

```text
.codex/prompts/aidevobserver-compiled-ai-evaluation.md
```

The prompt generates one candidate benchmark fixture at a time with:

```text
session transcript
baseline agent path
observer middleware path
expected findings
token accounting
determinism checks
security checks
clean counterexample
promotion policy
```

## Next Implementation Slice

1. Run the contract checker in CI/flywheel proof modules.
2. Add real anonymized local programming-session transcripts after consent/redaction.
3. Generate fixtures for each industry/domain pair.
4. Add middleware instrumentation to record actual registry queries and token estimates.
5. Compare three lanes:

```text
baseline session:
  raw agent transcript, no middleware

observer session:
  transcript + middleware registry/deterministic tools

compiled route:
  preselected reusable route / PlanLock-like execution
```

6. Publish a small results table in the AIDevObserver benchmark lab:

```text
tokens saved
reinventions caught
security findings
registry hits
accepted/reused/dismissed findings
break-even repetitions
```

## Final Rule

The observer is not a truth system.

```text
AIDevObserver finds candidate improvements.
Teleon compiles candidate capabilities.
Baltor governs served truth.
OpenHubForAI supplies reusable registry substrate.
AI Done Right keeps the product architecture coherent.
```
