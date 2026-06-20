# Baltor Medallion Context Positioning

Date: 2026-06-02

This document formalizes the medallion-context pitch as a testable marketing
and sales narrative. It should be used as pitch language, not as a replacement
for Baltor's deeper architecture terms.

## Positioning Hypothesis

In the world of AI, context is becoming the new data pipeline.

Baltor automatically turns messy company knowledge into medallion context:
Bronze raw sources, Silver verified claims, and Gold task-ready context packs.

The point is simple:

```text
AI workflows should not run on raw organizational knowledge.
They should run on fresh, verified, source-linked context.
```

## Recommended Elevator Pitch

```text
Baltor is the automated medallion context layer for the world of AI.

It turns raw company knowledge into Bronze, Silver, and Gold context, so every
AI workflow gets fresh, verified, source-linked context before work begins.
```

## Executive Version

```text
Companies are adopting AI faster than they can govern the context behind it.

Baltor creates an automated medallion context pipeline: raw knowledge becomes
verified claims, verified claims become task-ready context packs, and every
pack carries freshness, permissions, lineage, and audit.
```

## Concrete Version

```text
Baltor turns messy docs, tickets, code, architecture diagrams, service catalogs,
and local notes into verified context packs for tickets, merge requests, repos,
incidents, reviews, and decisions.

Instead of dumping raw context into prompts, teams get source-linked context
that has already been checked for freshness, permissions, conflicts, and
lineage.
```

## Medallion Context Model

| Layer | Meaning | Baltor output |
| --- | --- | --- |
| Bronze Context | Raw or lightly normalized source material. | Source snapshots, source handles, raw chunks, source metadata, ACL state. |
| Silver Context | Structured, source-linked, checked context units. | Context objects, verified claims, relationships, dimensions, conflicts, freshness records. |
| Gold Context | Task-ready, policy-safe context bundles. | Implementation packs, review packs, architecture packs, incident packs, context receipts. |

## Bronze Context

Bronze context is raw organizational knowledge captured with source identity and
basic safety controls.

Examples:

```text
Jira tickets
GitHub/GitLab issues and merge requests
Confluence pages
Slack threads
architecture diagrams
service catalog entries
EventCatalog and AsyncAPI specs
runbooks
incident reports
generated repo wikis
local developer memory
```

Bronze context must include:

```text
source handle
retrieval timestamp
source system
source type
source version or generation
content hash where possible
ACL and visibility metadata
raw expansion policy
```

Bronze context is not trusted just because it was ingested.

## Silver Context

Silver context is where Baltor starts adding durable value.

Bronze inputs are transformed into:

```text
normalized context objects
atomic claims
relationships
ownership facts
dependency facts
event and schema facts
freshness labels
conflict records
source precedence decisions
policy decisions
verification runs
```

Silver context answers:

```text
What does this source claim?
Which entity does the claim refer to?
Which source handle supports it?
Is it fresh?
Is it contradicted?
Is it allowed for this user and purpose?
Is it actual behavior, intended design, or generated explanation?
```

Silver context is the correct place for continuous background workers:

```text
source watchers
context interrogators
claim extractors
evidence verifiers
conflict hunters
freshness guards
policy checkers
contamination scanners
source precedence resolvers
```

## Gold Context

Gold context is the serving layer.

Gold context is not a bigger summary. It is a task-ready pack assembled from
checked context.

Examples:

```text
context_for_ticket("BILL-782")
context_for_mr("billing-service", "!4421")
context_for_repo("billing-service")
architecture_pack("billing-service")
review_pack("MR-4421")
incident_pack("INC-812")
```

Gold context includes:

```text
task summary
verified requirements
relevant decisions
code pointers
architecture/service graph context
event/API/schema impact
tests to run
risks and open questions
known conflicts
freshness status
policy decision
source handles
context receipt
```

Gold context should be optimized for:

```text
minimum sufficient context
freshness
source traceability
permission safety
conflict disclosure
token budget
task usefulness
auditability
```

## Automation Claim

The automation claim should be explicit:

```text
Baltor automatically upgrades raw organizational knowledge into verified
context packs.
```

Expanded:

```text
Baltor's automated Context Wizards continuously watch sources, extract claims,
check evidence, detect conflicts, enforce freshness, apply permissions, and
compile task-ready context packs.
```

Do not imply that automation removes human review. The better claim is:

```text
Baltor automates routine context assurance and routes unresolved or high-risk
conflicts to human stewards.
```

## Pitch-Test Variants

### Variant A: Short

```text
Baltor is the automated medallion context layer for the world of AI.
It turns raw company knowledge into verified, source-linked context packs.
```

### Variant B: Governance

```text
AI is only as trustworthy as the context behind it.
Baltor turns raw knowledge into verified context packs with freshness,
permissions, lineage, and audit.
```

### Variant C: Engineering

```text
Before AI works on a ticket or merge request, Baltor turns the relevant docs,
code, history, architecture, and service data into a verified implementation or
review pack.
```

### Variant D: Data-Platform Familiar

```text
Data teams use Bronze, Silver, and Gold layers to make analytics trustworthy.
Baltor brings the same medallion discipline to context for the world of AI.
```

### Variant E: Risk

```text
Most AI workflows still run on raw, stale, and contradictory context.
Baltor automatically upgrades that context into verified task packs before the
work begins.
```

## Language Rules

Prefer:

```text
world of AI
AI workflows
AI-assisted work
AI systems
AI-enabled teams
AI coding tools
```

Use sparingly:

```text
AI agent systems
agentic workflows
```

Avoid as primary pitch language:

```text
RAG
vector database
MCP gateway
enterprise search
chatbot
memory API
```

Those terms can appear in technical conversations, but they should not define
Baltor externally.

## What To Test

In customer and investor conversations, test:

```text
Does "medallion context" land quickly?
Does the Bronze/Silver/Gold metaphor clarify the product?
Does "automated" create trust or concern?
Does "world of AI" feel broad enough without becoming vague?
Do buyers understand that Gold context is task-ready, not just summarized?
Do security/platform buyers ask about permissions, audit, and human review?
Do engineering buyers ask for ticket and merge-request examples?
```

## Recommended Current Use

Use this as a pitch and sales-deck metaphor:

```text
Baltor is the verified context oracle.
Medallion context is how Baltor explains the pipeline.
```

Do not rename the whole product category to medallion context yet. The phrase is
promising, but it should be tested before it becomes the primary category name.
