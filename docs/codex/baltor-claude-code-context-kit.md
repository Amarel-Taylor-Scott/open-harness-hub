# Baltor Claude Code Context Kit

Updated: 2026-06-09

This is the lightweight local client/SDK path for Baltor before a full
organization context platform exists.

For a Claude Code Max handoff, also load:

```text
docs/BIBLE.md
docs/DESIGN-BIBLE.md
docs/INTEGRATION-BIBLE.md
docs/design/openharness-claude-design/START-HERE.md
docs/codex/ai-done-right-family-polish-goal.md
docs/architecture/service-auth-and-consumption-model.md
dist/sites/openharness-design/README.md
```

Those files carry the current AI Done Right family shape (5 surfaces sharing one
design system, light theme + Inter), the canonical design handoff
(`docs/design/openharness-claude-design/` plus the DESIGN and INTEGRATION bibles;
`dist/sites/openharness-design/` is the richer reference bundle), the full Baltor
method spine, and the unresolved service-to-service auth work.

## Path

```text
Markdown or Obsidian memory
-> local Baltor MCP/context tools
-> team Claude Code kit
-> organization MCP gateway or portal
-> central context service and indexed retrieval
```

Do not make local memory the enterprise source of truth. Use it to prove the
context-pack format, source-handle discipline, and review workflow.

## Included Repo Artifact

The repo now includes a Claude Code skill:

```text
.claude/skills/baltor-context-gateway/SKILL.md
```

The skill tells Claude Code to use Baltor as the controlled context gateway,
prefer bounded context tools over raw source tools, and treat local
Markdown/Obsidian memory as an inspectable cache.

The repo also includes a local cache writer:

```bash
python3 scripts/baltor_context_cache.py \
  --base-url http://127.0.0.1:9304 \
  --query "agency active vendor CCO ownership"
```

The cache writer uses the dependency-free local SDK client in:

```text
scripts/baltor_context_client.py
```

That client exposes reusable methods for `status`, `search`, `fetch`, `trace`,
`connectors`, `glossary`, `heartbeat`, and `queue_health`, so Claude Code
commands, hooks, memory sync jobs, or a later packaged SDK do not need to copy
gateway URLs or request shapes.

The cache writer writes safe Markdown cache files under
`dist/baltor-context-cache/` by default:

```text
dist/baltor-context-cache/
  INDEX.md
  cache-manifest.json
  cache-writes.jsonl
  runs/<run-id>.context.md
  glossary/<run-id>.glossary.md
```

The cache writer stores compact facts, risks, source handles, and glossary
packets. It does not mirror raw source documents. `cache-manifest.json` uses
kind `baltor.local-context-cache-manifest`, records the latest cached run,
and keeps a small auditable entry list for local Markdown, Obsidian, Basic
Memory, or Claude-Mem style sync.

Offline cache readers can use:

```bash
python3 scripts/baltor_context_cache_read.py \
  --out-dir dist/baltor-context-cache
```

or the Claude Code command:

```text
/baltor-cache-status
```

This path reads only `cache-manifest.json`; it does not call the gateway or
source systems.

## Local Memory Layout

Recommended local or team workspace:

```text
~/AgentMemory/
  INDEX.md
  repos/
  tickets/
  decisions/
  glossary/
  sessions/
```

Memory entries should store compact source-linked claims:

```text
Claim: Agency is ambiguous in BILL-782 context.
Source handle: ctx://baltor/adm-.../claim/claim-id=fact-014
Glossary packet: glossary-001
Verified at: 2026-06-01
Policy: source-local only until reviewed
```

Do not store raw source-system dumps, secrets, customer data, or unreviewed
global glossary definitions.

## Gateway Tools

Current local surface:

```text
context_status
context_search
context_fetch
context_trace
context_connectors
context_heartbeat
context_queue_health
context_glossary
```

HTTP equivalents:

```text
/api/context-gateway/status
/api/context-gateway/search
/api/context-gateway/fetch
/api/context-gateway/trace
/api/context-gateway/connectors
/api/context-gateway/glossary
/api/debug/heartbeat
/api/admin-dashboard/queue-health
```

## Glossary Packet Rule

When `context_glossary` returns packets, the terms are not safe to promote into
global memory, canonical graph nodes, ontology labels, or stable edge labels.

Each packet must stay source-scoped until one of these resolves it:

- a source-local glossary definition;
- a reviewed ontology mapping;
- a local LLM glossary review that remains a proposal;
- a human glossary owner decision.

## Suggested Team Kit

A later `company-claude-code-kit` can package:

```text
CLAUDE.md
.claude/skills/baltor-context-gateway/
.claude/commands/baltor-cache-context.md
.claude/commands/baltor-cache-status.md
.claude/commands/context-ticket.md
.claude/commands/context-mr.md
.claude/hooks/pretool_policy.py
.claude/hooks/posttool_audit.py
scripts/baltor_context_cache.py
scripts/baltor_context_client.py
scripts/baltor_context_cache_read.py
memory-templates/ticket-context.md
memory-templates/glossary-note.md
mcp/read-only.example.json
```

The first stable contract is the context pack, not the vector database. Backends
can evolve from local Markdown to Basic Memory, Obsidian, live source MCPs,
Onyx, Cloudflare AI Search, Qdrant, Weaviate, or a custom index without
changing how Claude Code asks for context.
