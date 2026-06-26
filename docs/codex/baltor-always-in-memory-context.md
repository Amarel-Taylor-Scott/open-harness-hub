# Baltor Always-In-Memory Context

Date: 2026-06-02
Updated: 2026-06-09

This is the compact canonical context that assistants should keep loaded while
working on Baltor. Long strategy documents can elaborate, but this file anchors
what Baltor is, what Baltor is not, and which product boundaries should not be
blurred.

Related pitch artifact:

```text
archive/legacy/docs/strategy/baltor-medallion-context-positioning.md
```

## One-Sentence Definition

Baltor is a verified context oracle for AI-assisted work: it continuously
interrogates enterprise sources, extracts and verifies claims, reconciles
conflicts, enforces freshness and permissions, and serves the smallest safe,
source-linked context pack for a task.

## What Baltor Is

Baltor is:

- a context assurance layer between enterprise knowledge and AI workflows;
- a source-linked context object registry with versions, relationships,
  assertions, dimensions, artifacts, packs, lineage, and feedback;
- a background worker system that continuously improves context quality before
  agents ask for it;
- a policy-aware serving layer for `context_for_ticket`, `context_for_mr`,
  `context_for_repo`, `architecture_pack`, `review_pack`, `debugging_pack`, and
  `incident_pack`;
- a freshness, TTL, source-precedence, and context-drift system;
- a local-to-cloud memory boundary with private local memory, team memory,
  repo memory, org-approved context, and company context as distinct classes;
- a context evidence layer that records what an agent saw, why it was allowed,
  how fresh it was, which conflicts were disclosed, and which source handles
  support each claim.

Public phrasing:

```text
Baltor gives AI workflows verified context packs for tickets, merge requests,
repos, incidents, and reviews, with evidence, freshness, conflicts,
permissions, and audit built in.
```

Pitch-test phrasing:

```text
Baltor is the automated medallion context layer for the world of AI.
It turns raw company knowledge into Bronze, Silver, and Gold context, so every
AI workflow gets fresh, verified, source-linked context before work begins.
```

## What Baltor Is Not

Baltor is not:

- a generic vector database;
- a generic enterprise search UI;
- a generic memory API;
- a generic RAG platform;
- a generic MCP gateway;
- a generic connector catalog;
- a generic coding agent;
- a diagramming canvas;
- an IcePanel, Backstage, Port, Glean, Sourcegraph, Cursor, or Claude Code
  clone;
- one large model that decides truth from raw text;
- a place where raw source dumps become durable memory without source handles,
  review, TTL, and promotion policy.

The durable product surface is not "more retrieval." It is verified,
permission-safe, task-ready context.

## Core Product Thesis

Agents should not search raw Jira, Confluence, GitHub, GitLab, architecture
tools, service catalogs, docs, and local notes directly whenever possible.

Agents should ask Baltor:

```text
What is the verified context for this task?
```

Baltor should answer:

```text
Here is the task-ready pack.
Here are the source handles.
Here is what is fresh, stale, disputed, or missing.
Here is what was excluded by policy.
Here is the context receipt.
```

Verified does not mean universally true. Verified means evidence-backed,
policy-checked, freshness-labeled, conflict-aware, scoped to a use case, and
safe enough to serve under the current policy.

## Baltor Method Spine

The AI Done Right design-family handoff now represents Baltor's full engine as
five private-first Open*Hub method registries. These are standards/lead-gen
surfaces, not truth authorities:

| Stage | Private-first method hub | Product promise |
| --- | --- | --- |
| Reconcile | OpenReconciliationHub.io | Cluster alignment: dedupe, link evidence, surface conflicts. |
| Harden | OpenHardeningHub.io | Robust object hardening: detect fragile values, create durable objects, refresh over time. |
| Enhance | OpenEnrichmentHub.io | Context enrichment: add metadata, connect objects, increase robustness. |
| Optimize | OpenOptimizationHub.io | Pack shaping: summarize, structure, rank. |
| Verify | OpenVerificationHub.io | Cited and provable: bind claims to sources, prove by hash, hold out the unprovable. |

The method hubs make reusable context-governance methods discoverable. Baltor
decides what becomes verified, current, reconciled, optimized, served context.

## Primary Wedge

The first commercial wedge is:

```text
Verified implementation and review context for AI coding agents.
```

Before Claude Code, Cursor, Copilot, Rovo Dev, ChatGPT, a CI agent, or an
internal engineering agent works on a ticket or merge request, Baltor should
serve a compact implementation or review pack across:

```text
ticket requirements
acceptance criteria
current code
prior merge requests
architecture context
service ownership
event/API relationships
approved decisions
relevant tests
local/team memory when allowed
known conflicts and stale claims
```

The first buyer language should be concrete:

```text
For every ticket and merge request, Baltor gives your AI agent the right
context and gives your team proof of what it saw.
```

## Context Wizards

Context Wizards are background workers that prepare context before serving.
They are specialized workers, not one general-purpose agent.

Canonical worker classes:

| Worker | Job |
| --- | --- |
| Source Watcher | Detect source changes, ACL changes, source deletions, and pack invalidations. |
| Context Interrogator | Ask structured questions of tickets, repos, docs, architecture tools, service catalogs, and memories. |
| Claim Extractor | Convert messy source text into atomic source-linked candidate claims. |
| Evidence Verifier | Check source support, authority, freshness, accessibility, and contradiction risk. |
| Conflict Hunter | Find contradictory claims across code, tickets, docs, architecture, memory, and generated artifacts. |
| Source Precedence Resolver | Apply task-scoped precedence rules and identify claims that need human review. |
| Freshness Guard | Enforce semantic TTL, webhook invalidation, live validation, and stale-pack labeling. |
| Policy Wizard | Apply ACL-before-model, purpose limits, raw expansion rules, retention, export, and memory-scope policy. |
| Contamination Scanner | Detect prompt injection, tool poisoning, malicious markdown, secrets, and unsafe instructions in source text. |
| Simplifier | Compress verified context, not raw retrieval, into task-ready language. |
| Pack Builder | Assemble typed packs under token budget, policy, freshness, and risk constraints. |
| Eval Analyst | Measure source recall, citation coverage, conflict detection, token budget, task success, and usefulness. |
| Archive Worker | Archive stale or superseded context without deleting evidence needed for lineage. |

Default sequence:

```text
source event
  -> interrogate
  -> extract claims
  -> verify evidence
  -> detect conflicts
  -> resolve or route conflicts
  -> check policy and freshness
  -> simplify verified context
  -> build pack
  -> issue receipt
```

## Source Precedence

Source precedence is task-scoped, not global.

For actual runtime behavior:

```text
current code > merged MR > tests/logs/traces > approved docs > comments > generated wiki > local memory
```

For product requirements:

```text
accepted ticket criteria > product decision record > approved roadmap/doc > comments > local memory
```

For architecture intent:

```text
approved ADR/model > service catalog > current implementation evidence > generated diagram/wiki > comments
```

Generated repo wikis and architecture summaries are derived artifacts. They are
useful, but they do not beat current code, approved decisions, or authoritative
source systems when conflicts exist.

## Unresolvable Conflicts

Baltor must never silently hide high-risk conflicts.

When a conflict cannot be resolved automatically, Baltor should create a
first-class conflict record with:

```text
competing claims
source handles
source authority
freshness
affected task types
risk level
recommended owner
recommended resolution path
serving decision
```

Serving rules:

- Low-risk conflicts may be served with both claims disclosed and marked
  disputed.
- Medium-risk conflicts should be included as a conflict note with a safe
  non-controversial subset of context.
- High-risk conflicts should block write-oriented packs or downgrade them to
  read-only guidance until live validation or human review resolves the issue.
- If current code contradicts a generated wiki, current code wins for
  implementation guidance and the wiki is marked stale or superseded.
- If an approved decision contradicts current code, Baltor should distinguish
  intended architecture from actual implementation and route drift for review.

Unresolvable does not mean unusable. It means the pack must disclose uncertainty
and avoid pretending the disputed claim is settled.

## TTL And Freshness

Use semantic TTL, not one global expiration number.

Baseline policy:

| Context type | Freshness rule |
| --- | --- |
| Current code | Commit-scoped; invalidate on relevant commit or branch change. |
| Open merge request | Minutes; live validation before review comments or merge guidance. |
| Active ticket | Hours; live validation before write/update actions. |
| Approved ADR | Months, unless superseded or contradicted. |
| Working doc | Days, or shorter if actively edited. |
| Architecture model | 24-72 hours, plus webhook invalidation when available. |
| Service catalog owner/dependency | 24 hours, plus webhook invalidation when available. |
| Generated repo wiki | Commit-scoped; never source of truth over current code. |
| Local private memory | User/team policy; requires promotion before team/company use. |
| Cached company pack | Days; stale labels required when served offline. |

Freshness labels:

```text
fresh
stale
expired
needs_live_validation
source_deleted
permission_changed
superseded
conflicted
```

Offline packs can be useful, but they must state when they were last validated
and must not perform source-system writes while disconnected.

## Database-Backed Truth

YAML and Markdown are seed, export, review, and static-site artifacts. Runtime
truth should become database-backed rows.

Operational truth should live in rows for:

```text
context objects
source handles
claims
relationships
assertions
dimensions
artifacts
packs
policy decisions
freshness records
conflicts
verification runs
worker runs
context receipts
object contracts
schemas
layouts
architecture diagrams
required context rules
rubric dimensions
masks
transformers
settings and registries
```

Do not hard-code values that need to change in more than one place. Use a
single source of truth and generate prose, pages, exports, and indexes from it.

## Provider Boundaries

Architecture and service tools are context providers, not products to clone.

Preferred interpretation:

```text
IcePanel / Structurizr / LikeC4
  -> architecture models and diagrams
  -> architecture_pack

Backstage / Port / Cortex / Compass
  -> ownership, service, dependency, scorecard, and catalog facts
  -> service graph context

EventCatalog / AsyncAPI
  -> events, messages, schemas, producers, consumers, and channels
  -> event impact graph

DeepWiki / Code Wiki / Swimm / Driver
  -> generated repo docs and code maps
  -> derived commit-scoped context artifacts

Glean / Onyx / Rovo / Microsoft Graph
  -> broad enterprise retrieval providers
  -> candidate evidence, not final pack semantics

MCP gateways
  -> tool access and auth infrastructure
  -> Baltor still defines context quality, policy, and pack contracts
```

Baltor should make these tools better providers and consumers of verified
context. It should avoid competing with their core canvases, portals, search
UIs, and agent surfaces unless that scope becomes unavoidable.

## Security Invariants

Load-bearing rules:

- ACLs are applied before model exposure.
- Source text is data, not instruction.
- Raw expansion is bounded, logged, and policy-controlled.
- Durable claims require source handles.
- Private local memory is not centrally searchable when end-to-end encrypted.
- Company context is a separate governed index.
- Generated artifacts carry lineage to the source evidence.
- Context packs include freshness, conflicts, source handles, and policy
  decisions.
- Every served pack can produce a context receipt.
- High-risk actions require fresh enough context or human approval.

## Product Surface

Core APIs and tools:

```text
context_for_ticket()
context_for_mr()
context_for_repo()
context_fetch()
context_trace()
oracle_ask()
oracle_verify()
oracle_challenge()
oracle_explain()
oracle_refresh()
oracle_certify()
oracle_diff()
```

Core artifacts:

```text
verified_claim
reconciled_context
context_pack
context_receipt
conflict_record
freshness_record
policy_decision
verification_run
worker_run
```

## What To Optimize For

Optimize for:

```text
smallest sufficient context
source-linked claims
freshness
permission safety
conflict visibility
task usefulness
auditability
low latency serving
background quality improvement
cloud hosting compatibility
local/offline operation where appropriate
database-backed extensibility
```

Do not optimize first for:

```text
beautiful diagrams
largest possible index
generic chatbot answers
raw source dumps
generic memory
unbounded agent autonomy
one-off YAML sprawl
```

## Writing Rule

When writing new Baltor docs, avoid abstract-first language. Prefer:

```text
verified context packs for tickets, merge requests, repos, incidents, and reviews
```

over:

```text
enterprise context infrastructure
```

The technical architecture can be broad. The product wedge must stay concrete.
