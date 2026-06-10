# Baltor Context Layer MVP Roadmap

This roadmap keeps the enterprise context-layer work incremental. The final
shape is still:

```text
Claude Code asks.
Gateway governs.
Context service retrieves.
Compression layer packs.
Live tools validate and act.
```

## MVP Ladder

### MVP 0: Direct Source-Tool Baseline

Use direct Atlassian/GitLab/Glean/Onyx style MCP tools only as a measurement
baseline.

Deliverables:

- read-only source access by default;
- ask-before-write policy;
- deny rules for delete/admin/bulk export;
- source-tool audit logs;
- list of over-fetch patterns.

This is a pilot pattern, not the target end state.

### MVP 1: Ticket And MR Context Packs

Generate compact context packs before building a vector database.

Tools:

```text
context_for_ticket(ticket, repo?, max_tokens?)
context_for_mr(project, mr, max_tokens?)
context_fetch(handle, max_tokens?)
context_trace(result_id)
```

Pack contract:

```text
summary
high-confidence facts
implementation constraints
code pointers
conflicts / stale-source warnings
risks
open questions
source handles
suggested next fetches
```

Success is measured by whether the agent can work from the pack without
fetching full issue histories, full page trees, or full diffs.

### MVP 2: Thin MCP Context Gateway

Expose one governed tool surface and keep backend choices replaceable.

Initial tools:

```text
context_status
context_search
context_fetch
context_trace
context_connectors
context_heartbeat
```

The current local demo implements this through:

```text
/api/context-gateway/status
/api/context-gateway/search
/api/context-gateway/fetch
/api/context-gateway/trace
/api/context-gateway/connectors
/api/debug/heartbeat
```

### MVP 3: Governed MCP Portal

Put a Cloudflare MCP Portal, Portkey, TrueFoundry, or equivalent control plane
in front of the gateway and any temporary direct source tools.

Use separate portals or policies for:

- read-only engineering context;
- write-capable source actions;
- CI/MR review agents;
- sensitive repos or regulated data.

### MVP 4: Indexed Backend Bakeoff

Compare retrieval backends behind the same gateway contract.

Candidates:

- Cloudflare AI Search / Vectorize + R2;
- Pinecone / Weaviate / Qdrant / Azure AI Search;
- Onyx or Glean for enterprise knowledge;
- Postgres metadata + raw S3/R2 snapshots + vector backend.

The winner is the backend that produces the best context packs, not the best
standalone search demo.

## Local Memory MVP

Local memory is useful in Phase 1, but it is not the enterprise context layer.

Recommended stance:

- enterprise source systems are read-only by default;
- local memory writes are allowed only in a scoped folder;
- memory stores compact claims, decisions, gotchas, and source handles;
- memory never stores secrets, customer data, raw issue histories, raw page
  dumps, or full diffs.

Useful local paths:

```text
~/AgentMemory/
<repo>/.claude/context/
```

Obsidian is a good human UI because it stores Markdown. It should hold reviewed
context packs and repo notes, not uncontrolled raw source mirrors.

Minimal memory layout:

```text
INDEX.md
repos/<repo>.md
tickets/<ticket>.context.md
decisions/<adr>.md
gotchas/testing.md
sessions/<date>-<topic>.md
```

Durable memory entry shape:

```text
Claim: Billing retries max out at 6 attempts.
Source handle: ctx://confluence/ADR-014#retry-policy
Verified: 2026-06-01
Confidence: high
```

## Heartbeat Contract

Every runtime surface should expose a heartbeat:

- server PID, start time, uptime;
- latest run ID, status, progress, stage, and queue job ID;
- Redis queue pending/hold/failure counts;
- worker event stream name and latest event ID;
- worker heartbeat file count and recent heartbeat records;
- latest admin events;
- contract endpoints.

Local endpoint:

```text
GET /api/debug/heartbeat
GET /api/admin-dashboard/heartbeat
```

MCP tool:

```text
context_heartbeat(run_id?)
```

Heartbeats prove that a system is alive, where it is waiting, and which
contract should be inspected next. They do not replace artifact assertions, but
they make failure states observable.
