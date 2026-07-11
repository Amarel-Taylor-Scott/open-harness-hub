# Baltor MCP Context Gateway

Baltor should expose a controlled context gateway to coding agents such as
Claude Code. Claude Code is the agentic coding interface; Baltor owns retrieval
policy, access control, ranking, compression, citations, source freshness, and
audit.

The target shape is:

```text
Claude Code / IDE agent / CI agent
-> MCP context gateway
-> policy, retrieval, compression, source handles, audit
-> indexed context backend
-> live source connectors
```

Do not make the coding agent the primary retrieval brain. It should ask for
context through a small approved tool surface. The gateway decides where to
search, how to filter, what to compress, and how much to return.

## Why This Exists

Directly exposing Jira, Confluence, GitLab, and source APIs to a coding agent is
useful for live operations, but weak as the default enterprise context layer:

- retrieval quality depends on the model and source APIs;
- raw pages, issues, comments, diffs, and trees waste tokens;
- document-level ACLs and source freshness are hard to enforce consistently;
- prompt-injection and stale-context risk are higher;
- the same context cannot be reused cleanly across Claude Code, ChatGPT, Slack,
  CI agents, internal copilots, and review tools.

The gateway turns raw source systems into task-specific context packs with
source handles and safety metadata.

## Gateway Responsibilities

The context gateway owns:

- user identity, groups, project memberships, and source entitlements;
- source routing by task type, repo, issue key, freshness need, and token budget;
- hybrid search across keyword, vector, graph, and exact identifiers;
- source-system ACL filtering before content reaches an LLM;
- reranking and duplicate collapse;
- stale-source checks and live validation policy;
- prompt-injection and untrusted-content warnings;
- task-specific compression;
- citations and stable fetch handles;
- audit logs of what was requested and returned;
- retrieval and compression evaluation.

Claude Code owns:

- deciding when it needs context;
- applying returned context to a coding task;
- requesting expansion through handles when needed;
- using live action tools only when policy allows.

## MCP Tool Surface

Expose one project or enterprise MCP server, for example `context-gateway`.

Default tools:

```text
context_search(query, task_type, sources, repo, jira_key, token_budget, freshness)
context_fetch(handle, max_tokens)
context_expand(source_id, section, max_tokens)
context_trace(result_id)
context_status()
context_connectors()
context_heartbeat(run_id)
context_queue_health()
context_glossary(term, run_id, max_packets)
```

Optional gated tools:

```text
source_live_fetch(source_type, object_id)
source_action(action, source_type, object_id, payload)
```

Avoid exposing raw unrestricted tools as defaults:

```text
raw_confluence_search
raw_jira_search
raw_gitlab_search
get_all_comments
get_full_page_tree
get_full_merge_request_diff
```

Those operations can exist behind the gateway, but the gateway decides when they
are safe and token-efficient.

## Context Pack Contract

The gateway should return context packs, not raw top-k chunks.

Example:

```json
{
  "result_id": "ctxr_123",
  "task_type": "code_change",
  "token_budget_used": 2740,
  "confidence": "medium",
  "context_pack": {
    "summary": "Billing retry behavior is defined across ADR-014, Jira BILL-782, and GitLab MR !4421.",
    "facts": [
      {
        "claim": "Retries should be exponential with max 6 attempts.",
        "source": "confluence:ADR-014",
        "handle": "ctx://confluence/page/123#section-retry-policy",
        "citation": "ADR-014, Retry Policy",
        "freshness": "indexed",
        "trust": "strong"
      }
    ],
    "code_pointers": [
      {
        "path": "services/billing/retry_scheduler.ts",
        "reason": "Existing retry scheduler implementation",
        "handle": "ctx://gitlab/project/17/file/services/billing/retry_scheduler.ts"
      }
    ],
    "risks": [
      "BILL-912 suggests retry jitter was discussed but not merged."
    ],
    "next_fetches": [
      {
        "handle": "ctx://jira/BILL-782#comments:decision",
        "why": "Expand exact decision comment before changing retry count."
      }
    ]
  }
}
```

Every compressed claim must keep a handle to the raw source object or exact
evidence span. Compression without handles is not acceptable.

## Source Layers

Store multiple forms:

| Layer | Stored form | Purpose |
|---|---|---|
| L0 | Raw source snapshot | Audit, citation, fallback fetch |
| L1 | Parsed canonical document | Stable source representation |
| L2 | Structural chunks | Retrieval |
| L3 | Object summaries | Routing and quick grounding |
| L4 | Task-specific context packs | Coding-agent consumption |
| L5 | Fetch handles | On-demand expansion |

Claude Code should usually receive L4 and request L5 handles only when needed.

## Pack Types

Initial context pack types:

| Pack type | Used for |
|---|---|
| `implementation_pack` | Code changes |
| `debugging_pack` | Bugs, logs, incidents |
| `architecture_pack` | Design and ADR questions |
| `ticket_pack` | Jira planning and acceptance criteria |
| `review_pack` | MR/PR review |
| `migration_pack` | Large refactors |

Each pack should include a token budget, confidence, source coverage, stale
source warnings, conflicts, and expansion handles.

## Retrieval Backend Options

Baltor should own the gateway contract even when retrieval is managed.

Possible backends:

- Cloudflare AI Search / Vectorize / R2;
- Pinecone, Weaviate, Qdrant, Milvus;
- OpenSearch / Elasticsearch / Azure AI Search;
- Postgres + pgvector for smaller local deployments;
- LlamaCloud, Vectara, or other managed RAG services;
- custom object store plus chunk, graph, and vector indexes.

Cloudflare AI Search is a credible managed substrate when wrapped by the
gateway. It can provide hybrid retrieval, chunking controls, reranking, metadata
filters, and an MCP endpoint. Baltor should still own richer ACLs, source
normalization, task-specific compression, source handles, live fallbacks, and
audit.

## Live Source Connectors

Use live source connectors for:

- fetching one exact Jira issue or comment;
- checking current MR state;
- validating whether indexed context is stale;
- creating or updating issues;
- commenting or transitioning workflow state;
- reading latest pipeline status.

Do not use live source connectors as the default way to find all relevant
context. Indexed search and compressed context packs should be the default.

Connector definitions should be exposed as governed envelopes, not raw source
tool sprawl. The envelope describes connector type, target, ACL policy,
retrieval policy, source-handle prefix, freshness policy, and whether live
actions are allowed. This lets a client verify that Jira, Confluence, GitLab,
website, FTP/SFTP, drive, and object-store mirrors are wired through the same
gateway policy.

Example connector envelope:

```json
{
  "kind": "connector_envelope",
  "connector": "gitlab",
  "target": "https://gitlab.example.com/group/project",
  "handle": "ctx://baltor/run/connector/connector=gitlab/target=https-gitlab-example-com-group-project",
  "retrieval_policy": {
    "default_mode": "indexed_mirror_first",
    "raw_source_access": "fallback",
    "live_fetch_requires_exact_handle": true
  },
  "acl_policy": {
    "filter_before_model": true,
    "derived_context_inherits_source_acl": true
  }
}
```

## Heartbeat Contract

The gateway should expose a machine-readable heartbeat so agents, tests, and
operators can verify that each runtime layer is alive without scraping pages.

Required heartbeat fields:

```text
kind = baltor.debug_heartbeat
server.pid
server.uptime_seconds
run.run_id
run.status
run.heartbeat.stage
run.last_worker_event
run.recent_worker_events
queue.redis_available
queue.latest_context_worker_event_id
queue.oldest_pending_age_seconds
queue.pending_sample
queue.recent_worker_events
queue.active_worker_jobs
queue.active_worker_job_count
queue.stale_active_worker_job_count
queue.stale_pending_job_count
queue.thresholds
queue.warnings
queue.trend
queue.throughput
queue.throughput.by_family
queue.history
queue.pending_family_counts
queue.pending_family_scan
queue.recent_samples
worker.ledger_exists
worker.recent_heartbeat_count
events.latest_event
contracts.endpoints
```

The heartbeat is not a business summary. It is a proof surface for debugging:
server process, latest run, queue, worker event stream, worker heartbeat files,
and the gateway contract endpoints.

## Temporal Ownership Context Contract

Business-ownership claims are volatile enough to need explicit temporal
metadata. A context pack or graph export that includes acquisition, merger,
split/spinout, parent-company, or independent-ownership records should carry:

```text
claim.claim_type = ownership_change
claim.detected_dates
claim.temporal_fragility
claim.requires_refresh
claim.safe_context_instruction
claim.ownership_change.event_type
claim.ownership_change.proposed_edge_type
claim.ownership_change.entity_candidates
claim.ownership_change.promotion_allowed = false
graph.nodes[type=OwnershipChangeEvent]
graph.nodes[type=OwnershipConflictGroup]
graph.edges[type=PROPOSES_OWNERSHIP_EVENT]
graph.edges[type=HAS_OWNERSHIP_CONFLICT]
graph.edges[type=MAY_SUPERSEDE_OWNERSHIP_CLAIM]
ownership_conflict_groups.latest_claim_id
ownership_conflict_groups.superseded_claim_ids
ownership_conflict_groups.resolution_suggestion
ownership_conflict_groups.supersession_confidence
context_pack.ownership_refresh_jobs
refresh_job.task = context.search.verify
refresh_job.adapter_plan.person_level_osint = disabled
```

Historical events can be used with citation and source date. Current-owner,
parent-company, and independent-ownership records must be refreshed before a
coding agent or downstream LLM states them as current facts. When two dated
current-status records disagree for the same owned entity, context packs should
include an `ownership_conflict_groups` entry and a refresh warning. A newer
dated independent-ownership record may be marked as likely superseding an older
parent-company record through `resolution_suggestion` and a
`MAY_SUPERSEDE_OWNERSHIP_CLAIM` edge, but this remains a machine proposal with
`promotion_allowed: false`; it does not become a verified current-ownership fact
without refresh or review. Refresh plans may target official registries,
company websites, supplier portal exports, archived sources, and second
independent sources, but unrestricted raw source tools and person-level OSINT
remain disabled unless separately authorized.

## Term Clarity Context Contract

Documentation often contains terms that are clear to a local team but unsafe
for LLM context: one term may have multiple meanings, a business term may be
used without a glossary definition, or an acronym may be left unexplained. The
gateway should treat these as first-class context concerns, not ordinary text.

Expected records:

```text
term_clarity_concerns[].type =
  MULTI_MEANING_TERM | UNDEFINED_DOMAIN_TERM | ACRONYM_WITHOUT_DEFINITION
term_clarity_concerns[].term
term_clarity_concerns[].evidence
term_clarity_concerns[].possible_meanings
term_clarity_concerns[].claim_ids
term_clarity_concerns[].requires_glossary_review = true
term_clarity_concerns[].safe_context_instruction
graph.nodes[type=TermClarityConcern]
graph.edges[type=HAS_TERM_CLARITY_CONCERN]
context_pack.term_clarity_concerns
glossary_resolution_packets[].kind = baltor.glossary-resolution-packet
glossary_resolution_packets[].status = needs_glossary_review
glossary_resolution_packets[].review_routes
glossary_resolution_packets[].safe_context_policy.block_global_memory_promotion = true
glossary_resolution_packets[].safe_context_policy.block_canonical_graph_promotion = true
graph.nodes[type=GlossaryResolutionPacket]
graph.edges[type=HAS_GLOSSARY_RESOLUTION_PACKET]
context_pack.glossary_resolution_packets
```

The safe-context instruction should prevent the downstream model from turning a
poorly defined term into a canonical entity, ontology label, or graph edge. For
example, `agency` may mean a staffing office, a legal authority, or a recruiting
vendor; `active vendor` may need a source-local definition; and `CCO` should not
be expanded unless the source defines the acronym. These concerns can be
resolved by a glossary, ontology mapping, source-scope definition, or human/LLM
review, but unresolved terms should stay source-local.

The gateway exposes `/api/context-gateway/glossary` and the MCP wrapper exposes
`context_glossary` so coding agents can fetch only glossary review packets
without dumping raw source documents. Local Markdown or Obsidian memory may
cache packet summaries and source handles, but it must not convert unresolved
terms into global memory.

## ACL And Safety Rules

- Enforce ACLs before any retrieved content reaches a model.
- Keep raw source handles in the audit packet.
- Mark indexed context as stale when live source timestamps differ.
- Prefer primary or source-system records over copied summaries.
- Treat all source text as potentially untrusted.
- Separate source actions from source retrieval.
- Make write/action tools ask/deny/allow configurable by deployment.

## Local Implementation Path

The admin demo already has the first pieces:

```text
upload/ZIP
-> normalized hierarchy
-> deterministic extraction
-> trust records
-> local LLM review
-> manifest/text/RAG/graph/audit/safe-context/context-pack exports
-> local context gateway HTTP surface
```

Current local gateway API:

```text
GET  /api/context-gateway/status
GET  /api/context-gateway/connectors
GET  /api/context-gateway/search?query=...&task_type=...&run_id=...
POST /api/context-gateway/search
GET  /api/context-gateway/fetch?handle=ctx://...
POST /api/context-gateway/fetch
GET  /api/context-gateway/trace?result_id=...
GET  /api/debug/heartbeat?run_id=...
GET  /api/admin-dashboard/heartbeat?run_id=...
```

The local demo implementation uses keyword ranking over normalized components
and claims, then returns a bounded context pack with `ctx://baltor/...` handles.
It is intentionally a proof surface for the future MCP server contract, not a
replacement for a production hybrid/vector/graph backend.

Local MCP-style wrapper:

```bash
python3 _repos/shared-backend-components/scripts/baltor_context_gateway_mcp.py --base-url http://127.0.0.1:9304
```

Project-scoped MCP config:

```text
.mcp.json
```

The config registers `baltor-context-gateway` and points it at the local admin
demo server on port `9304`.

Self-test:

```bash
python3 _repos/shared-backend-components/scripts/baltor_context_gateway_mcp.py \
  --base-url http://127.0.0.1:9304 \
  --self-test
```

The wrapper is zero-dependency and speaks JSON-RPC over stdio with
Content-Length framing. It exposes:

```text
context_status
context_search
context_fetch
context_trace
```

Next gateway-oriented implementation steps:

1. Add `context.gateway.search` and `context.gateway.fetch` worker contracts.
2. Add context-pack exports grouped by `implementation_pack`,
   `debugging_pack`, and `architecture_pack`.
3. Add source connector envelopes for Jira, Confluence, GitLab, and website
   mirrors without enabling raw unrestricted access.
4. Add ACL metadata fields to source, file, chunk, claim, and graph records.
5. Add production MCP-client configuration examples for non-local deployments.
6. Add a production retrieval backend with hybrid search, reranking, and vector
   or graph indexes behind the same API.

## Non-Negotiables

- Retrieval policy lives outside the coding agent.
- Hybrid retrieval is the default for engineering context.
- Raw source access is a fallback or action path.
- Compression produces typed context packs with handles.
- ACL filtering happens before model exposure.
- Live validation is separate from indexed retrieval.
