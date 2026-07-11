# AIDevObserver Feedback Response And V1 Plan

**Date:** 2026-06-28  
**Purpose:** convert external feedback into product decisions, copy changes, demo priorities, and implementation sequence.

## Accepted Direction

The feedback is directionally correct.

AIDevObserver should lead as the practical developer-speed product:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

Teleon, Baltor, OpenHubForAI, CandidateBundle, PlanDelta, RemixSurface, PlanLock, ledgers, and proof/promotion remain important, but they should not be the first thing a new user has to understand.

The public wedge is:

```text
AI session
  -> detect duplicated work and token waste
  -> suggest existing helper/template/workflow/primitive
  -> human accepts/reuses/dismisses
  -> registry memory improves
  -> next AI session is cheaper and faster
```

## Positioning Decisions

### Product Name

Use:

```text
AIDevObserver = product
AIDevObserver Benchmark Lab = examples, replay, and primitive-first eval mode inside the product
```

Do not introduce AIDevExplorer as a separate public product or branded surface. Keep `aidevexplorer` as a legacy/internal namespace until a deliberate migration removes it.

### Lead Message

Use:

```text
Stop AI coding agents from reinventing code the primitive database already knows.
```

Subheadline:

```text
AIDevObserver reviews AI coding sessions, finds missed helpers, templates, workflows, and prior generated code in the primitive database, estimates wasted context, and turns accepted findings into reusable registry memory.
```

Developer CTA:

```text
Review my latest AI coding session.
```

Manager CTA:

```text
Show where AI coding time is being wasted.
```

### Secondary Message

Safety/compliance remains present, but not first:

```text
Also surfaces missing proofs, secret-handling issues, destructive operations, and governance signals.
```

## Public Story vs Technical Drill-Down

First contact:

```text
AIDevObserver helps teams ship faster with AI coding agents by finding duplicated work, wasted context, and cheaper reusable paths.
```

Technical drill-down:

```text
Under the hood, AIDevObserver can route accepted findings into Teleon, where reusable primitives/templates become compiled, proof-gated capability routes. OpenHubForAI provides registry sources, and Baltor provides verified context when context truth matters.
```

One-sentence ecosystem story:

```text
OpenHubForAI stores reusable components, Teleon compiles them into routes, Baltor governs verified context, and AIDevObserver watches development sessions to point agents back to what already exists.
```

## V1 Product Modes

### Mode A: Observer Review Mode

This is the launch product.

```text
input: transcript/session
output: ranked candidate findings
truth level: candidate advice only
runtime: lightweight
```

Capabilities:

- parse transcript/session
- extract actions, files, code blocks, commands, and task intent
- search local repo helpers and docs
- search lightweight template/helper registry
- optionally use LLM classification/ranking
- emit candidate findings
- collect human triage
- create reuse/negative memory

### Mode B: Teleon Route Mode

This is the deeper reuse path.

```text
input: accepted finding or known task intent
output: candidate route / PlanLock / proof path
truth level: proof-gated
runtime: compiler-backed
```

Capabilities:

- route accepted findings to Teleon
- search primitives/templates/composites
- build CandidateBundle
- compile or reject route
- attach proof requirements
- emit PlanLock or gap report
- promote only after proof

V1 should launch with Mode A and show Mode B as "advanced / under the hood."

## Minimum Viable Registry Connector

Do not wait for full OpenHubForAI coverage.

Minimum useful registry search:

- local repo functions/classes
- existing scripts
- README/docs snippets
- package scripts
- examples
- known helper registry
- 5-10 common workflow templates
- accepted finding memory
- dismissed finding negative memory

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

## First Demo Sequence

Landing page should point to:

```text
#/examples
```

Recommended flow:

1. Open Examples.
2. Replay Web scraper for regulatory rates.
3. Show ranked findings.
4. Expand one finding into "existing template/helper route."
5. Show Reports page with reuse/token savings.
6. Open Developer integrations only after the core value is clear.

First example:

```text
Web scraper for regulatory rates
```

Why:

- familiar AI coding request
- concrete one-off-code failure
- clear reusable route: acquire -> fetch -> extract -> validate -> emit
- easy to explain token/context waste and proof gates

Second example:

```text
Document-to-JSON extraction
```

Why:

- shows schema, provenance, source spans, and validation gates

Third example:

```text
Company/entity enrichment
```

Why:

- shows API/cache/provenance/confidence and repeated workflow reuse

Defer from first pitch:

- n8n workflow distillation
- media pipeline registries
- full Teleon object glossary
- Baltor dependency law
- all OpenHubForAI hub families
- local session discovery as default

Keep as advanced:

- CandidateBundle
- PlanDelta
- RemixSurface
- VariationRecord
- PlanLock
- ProofBundle
- PromotionRecord

## Buyer And User Focus

Likely first buyers:

- AI platform lead
- DevEx lead
- engineering productivity lead
- engineering manager with heavy AI agent usage
- platform team responsible for internal tooling

Avoid leading with governance buyer framing. Governance matters, but if the product is sold first as surveillance/compliance, developer adoption gets harder.

Manager dashboard should emphasize:

- repeated work across team
- duplicate helpers caught
- accepted reuse suggestions
- estimated model calls/tokens avoided
- agent loops interrupted
- missed registry routes
- most reinvented components
- teams/products with highest AI waste

Safety metrics should be present but secondary:

- secret-handling signals
- destructive-operation signals
- missing proof signals
- privacy-sensitive transcript signals

## Benchmark Decision

Build AIDevObserver Session Review Benchmark v0 before trying to prove full Teleon workflow compilation.

Benchmark should test:

- reinvention detection
- wasted context detection
- missed deterministic route detection
- agentic loop detection
- missing proof detection
- safety/secret redaction
- registry-backed suggestion precision
- replay determinism

Initial fixture set:

```text
10 frontend sessions
10 backend sessions
10 data engineering sessions
10 data science sessions
10 software refactor sessions
10 document extraction sessions
10 workflow automation sessions
10 security/devops sessions
```

Each fixture should include:

- session transcript
- known existing helper/template/primitive
- expected findings
- expected source_ref
- expected false-positive traps
- token/context estimate
- clean-session negative control

Primary metric:

```text
high-confidence source_ref precision
```

If source references are wrong, developers will stop trusting the product.

Token savings should report basis:

```text
exact tokens when model logs are available
tokenizer-estimated tokens when transcript is available
deterministic proxy when only file counts/chars are available
```

Example report line:

```text
Estimated 18,400 prompt tokens avoided.
Basis: tokenizer estimate over 12 files the agent read before discovering a helper already indexed locally.
```

## Highest-Leverage Next 5 Changes

1. Rewrite the landing/demo copy around speed and reuse.
2. Make the first demo a guided replay, not a dashboard.
3. Build the minimum registry connector.
4. Create the first 80-session benchmark.
5. Make human triage the product flywheel.

## Concrete Build Order

### Slice 1: Copy And Demo Flow

- lead headline with "Stop AI coding agents from reinventing code the primitive database already knows"
- make Examples the primary public route
- make web scraper replay the first highlighted demo
- show one expanded finding with source_ref
- show "estimated tokens avoided" with basis label

### Slice 2: Local Registry Connector

- index local functions/classes
- index scripts and package scripts
- index README/docs snippets
- index examples
- map common helper names to source_refs

### Slice 3: Triage Flywheel

- Accept
- Reuse
- Dismiss
- Not relevant
- Already known
- Wrong match

Accepted findings become registry memory. Dismissed/wrong findings become negative memory.

### Slice 4: Benchmark V0

- 80 session fixtures
- expected findings
- expected source_refs
- clean negative controls
- token/context estimates
- replay determinism checks

### Slice 5: Teleon Route Drill-Down

- accepted finding -> candidate route
- simple template match
- gap report when no route exists
- keep PlanLock/proof details behind advanced technical view

## Decision Summary

Use this crisp product story:

```text
AIDevObserver is the speed and reuse layer for AI coding sessions.

It reviews what your AI agent did, finds helpers and workflows it missed,
flags wasted context and repeated loops, and turns accepted findings into
registry memory so the next session is cheaper and faster.
```

Use this ecosystem story only after the user understands the product:

```text
OpenHubForAI stores reusable components, Teleon compiles them into routes,
Baltor governs verified context, and AIDevObserver watches development sessions
to point agents back to what already exists.
```
