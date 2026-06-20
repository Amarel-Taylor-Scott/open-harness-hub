# Enterprise Context Databases: Build Phases And Patterns

Updated: 2026-06-01

This note summarizes public engineering patterns for organizations building
their own context databases, context gateways, and agent-ready retrieval layers.
The consistent lesson is that strong teams do not start with one giant vector
database. They phase from governed access, to context packs, to narrow indexes,
to hybrid retrieval/evals, and only later to graph-scale context.

## What A Context Database Usually Is

A production context database is a composite system:

```text
source connectors
-> raw source snapshots
-> normalized documents / chunks / entities
-> metadata + ACL store
-> keyword / vector / hybrid indexes
-> optional relationship graph
-> context-pack compression
-> gateway / MCP / API delivery
-> evals, audit, traces, and heartbeats
```

The "database" is not just embeddings. It includes source handles,
permissions, freshness, provenance, source relationships, pack assembly, and
runtime governance.

## Public Patterns Reviewed

### Gateway First

Grab's AI Gateway is a useful pattern for Phase 0. Grab centralized provider
access, reviews new use cases with a mini-RFC/checklist, issues short-lived
staging-only exploration keys, applies rate limits, and tracks usage/costs.
This argues for letting teams experiment, but through a governed gateway rather
than unmanaged credentials.

Source:

- <https://engineering.grab.com/grab-ai-gateway>

### Shared RAG / Agent Platform

Grab's SpellVault evolution shows a second pattern: make RAG/apps/plugins a
shared internal platform rather than letting every team build a separate stack.
It also moved toward MCP exposure so apps and RAG capabilities become reusable
agent services.

Source:

- <https://engineering.grab.com/spellvault-evolution-beyond-llm>

### Enriched Indexes And ABAC

Salesforce's Enriched Index pattern emphasizes multi-round indexing, metadata
enrichment, summaries, hierarchical indexing, fallback paths, and access
control. Its ABAC point is critical: derived context must follow the visibility
rules of source materials. A compressed summary can be sensitive even when it
does not look like a raw document.

Source:

- <https://engineering.salesforce.com/the-next-generation-of-rag-how-enriched-index-redefines-information-retrieval-for-llms/>

### Code Context Is Special

GitHub Copilot and Sourcegraph both reinforce that code retrieval is not normal
document retrieval. Code assistants need snippets, symbols, tests, docs, bugs,
file paths, function names, and repository structure. GitHub reports a newer
embedding model improved Copilot retrieval quality by 37.6%, roughly doubled
throughput, and reduced index size 8x. Sourcegraph describes Cody's context
engine as using code search/code intelligence and hybrid dense-sparse retrieval
for code and docs, avoiding fully model-orchestrated context fetching because
serial LLM decisions can add latency and randomness.

Sources:

- <https://github.blog/news-insights/product-news/copilot-new-embedding-model-vs-code/>
- <https://docs.github.com/en/enterprise-cloud@latest/copilot/using-github-copilot/copilot-chat/indexing-repositories-for-copilot-chat>
- <https://webflow.sourcegraph.com/blog/cody-is-generally-available>
- <https://webflow.sourcegraph.com/blog/how-cody-understands-your-codebase>

### Contextual Retrieval And Reranking

Anthropic's contextual retrieval research is directly relevant to chunk design.
It found contextual embeddings reduced top-20 retrieval failure by 35%;
contextual embeddings plus contextual BM25 reduced failure by 49%; adding
reranking reduced failure by 67%. This supports context-rich chunks, hybrid
search, and reranking before final context-pack compression.

Source:

- <https://www.anthropic.com/research/contextual-retrieval>

### MCP Governance

Cloudflare MCP portals, Portkey MCP Gateway, and TrueFoundry's MCP gateway all
point to the same operational pattern: centralize authentication,
authorization, credential injection, tool allowlisting, request logging, and
audit instead of letting each agent connect to every MCP server directly.

Sources:

- <https://developers.cloudflare.com/cloudflare-one/access-controls/ai-controls/mcp-portals/>
- <https://developers.cloudflare.com/agents/model-context-protocol/governance/>
- <https://portkey.ai/docs/product/mcp-gateway/architecture>
- <https://truefoundry.com/docs/ai-gateway/mcp/mcp-gateway-auth-security>

### Graph Later, Not First

GraphRAG-style approaches are useful for multi-hop and corpus-level questions,
but they are usually a later phase for engineering context. The early win is
ticket/MR packs, exact handles, hybrid search, and ACL-safe compression. Graphs
become valuable once you need relationships like:

```text
ticket -> MR -> file -> service -> ADR -> owner -> incident -> runbook
```

## Common Build Phases

### Phase 0: Access And Experimentation Control

Goal: let teams experiment safely.

Deliverables:

- small pilot group;
- read-only source access;
- ask-before-write source actions;
- deny broad export/delete/admin tools;
- tool-call logs;
- short-lived experimentation credentials;
- usage/cost tracking.

Evidence to collect:

- which tools are used;
- which source queries work;
- which calls return too much;
- which writes are requested;
- where prompt-injection or over-fetch risks appear.

### Phase 1: Local Memory And Context Packs

Goal: learn the context artifact shape before building a full index.

Deliverables:

- ticket context packs;
- MR review packs;
- local Markdown/Obsidian memory for reviewed notes;
- source handle convention;
- context-first agent instructions;
- debug heartbeats and audit logs.

Do store:

- compact claims;
- decisions;
- gotchas;
- source handles;
- verification dates.

Do not store:

- raw Jira histories;
- full Confluence page dumps;
- full GitLab diffs;
- secrets;
- customer data;
- uncited conclusions.

### Phase 2: Thin Context Gateway

Goal: make the agent use one stable interface.

Tools:

```text
context_status
context_search
context_fetch
context_trace
context_connectors
context_heartbeat
context_for_ticket
context_for_mr
```

The backend can still call live source APIs initially. The value is
standardizing policy, logs, handles, compression, and client behavior.

### Phase 3: Narrow Indexed Context Database

Goal: index one valuable domain.

Start with one team/service:

- one Jira project;
- one Confluence space;
- one GitLab group/repo family;
- recent MRs, ADRs, runbooks, and incidents.

Storage split:

```text
R2/S3/GCS       raw source snapshots
Postgres        metadata, ACLs, object links, sync state
Search backend  BM25/hybrid/vector index
Object store    context packs and artifacts
Gateway         search/fetch/trace delivery
```

Evaluate:

- source recall;
- source precision;
- token budget;
- latency;
- ACL correctness;
- stale-source behavior;
- downstream code/task success.

### Phase 4: Hybrid Retrieval, Reranking, Compression

Goal: make retrieval quality reliable.

Add:

- BM25 / exact identifier search;
- vector search;
- reranking;
- contextual chunks;
- duplicate collapse;
- recency ranking;
- source reliability;
- context-pack templates;
- eval gates.

Pack types:

```text
implementation_pack
debugging_pack
review_pack
architecture_pack
migration_pack
incident_pack
```

### Phase 5: Context Graph

Goal: traverse relationships before retrieval.

Initial graph can be Postgres tables:

```text
context_objects(id, source, type, key, title, url, updated_at, acl_key)
context_edges(src_id, dst_id, relationship_type, confidence, source)
```

Add graph database only when traversal and graph analytics require it.

### Phase 6: Production Evals And Operations

Goal: make context changes safe to ship.

Gates:

- merge-time retrieval regression checks;
- staging eval suite;
- production sampling;
- citation-fidelity checks;
- ACL tests;
- latency and cost budgets;
- heartbeat and trace contracts.

## Recommended Baltor Path

Baltor should pursue this blend:

1. Keep direct source tools as pilot/fallback only.
2. Use the thin Baltor context gateway as the agent-facing contract.
3. Add `context_for_ticket` and `context_for_mr` next.
4. Generate ticket/MR context packs before building a broad index.
5. Compare Cloudflare AI Search/Vectorize, Pinecone, Weaviate, Qdrant, Azure AI
   Search, Onyx, and Glean behind the same contract.
6. Store raw snapshots in R2/S3 and metadata/ACLs in Postgres.
7. Add hybrid retrieval and reranking after the pack format is proven.
8. Add graph relationships once ticket/MR/file/service/ADR relationships are
   common enough to justify it.

The product rule remains:

```text
Claude Code asks.
Baltor governs.
Retrieval providers retrieve.
Baltor compresses and cites.
Live tools validate and act.
Heartbeats prove runtime state.
```

## Why This Matters For The Demo

The local admin demo now needs to prove not only that pages load, but also that
the framework exposes:

- source connector envelopes;
- source handles;
- context packs;
- gateway policy;
- heartbeat/debug contracts;
- queue and worker observability;
- exportable audit evidence.

That is the correct local version of the broader enterprise context database
roadmap.
