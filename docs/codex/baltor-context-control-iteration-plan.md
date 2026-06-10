# Baltor Context-Control Iteration Plan

Updated: 2026-06-01

Use this file to keep a multi-hour agent focused after the current context is
read.

## North Star

Make Baltor feel like a real local-first, cloud-ready context-control console:
users can upload or connect document sets, watch asynchronous deterministic and
LLM workers process them, inspect evidence and trust concerns, and download
safe context packages for downstream agents.

## Work Loop

```text
ORIENT   Read current state, changed files, running services, worker ledger.
PROVE    Hit the local URLs and APIs before editing.
BUILD    Improve one visible or architectural gap.
TEST     Run focused Python/HTTP/browser checks and inspect logs.
RECORD   Append a ledger entry with exact files and proof.
REPEAT   Move to the next highest-value gap.
```

## Priority Queue

1. Keep the admin demo clickable and nonblank on every route.
2. Make the monitor page useful enough to debug uploads, queue handoff, worker
   progress, LLM calls, exports, and errors without opening terminal logs.
3. Make ZIP/document-set ingestion produce durable hierarchy metadata:
   folders, files, pages, components, tags, hashes, byte counts, extensions,
   source type, and extraction status.
4. Expand deterministic document processing before LLMs:
   text cleanup, language detection, page/block/chunk splitting, regex facts,
   proper noun/entity candidates, noun chunks, acronym/definition extraction,
   relation candidates, co-occurrence edges, graph statistics, and freshness
   signals.
5. Keep local adapters fully configured by default and external adapters gated
   by explicit env flags or connector credentials.
6. Feed worker artifacts back into the admin run state:
   claim risk records, ambiguous claims, conflict candidates, node evidence,
   proposed node edges, LLM reviews, proposed LLM nodes/edges, summaries, audit
   reviews, and training examples.
7. Make exports contract-specific instead of generic run dumps:
   manifest, text pack, RAG records, graph package, audit packet, and safe
   context bundle.
8. Improve the LLM cascade:
   deterministic validators -> small local Gemma/Ollama -> mid open model ->
   larger open model -> frontier model only for hard/high-risk cases.
9. Add proof scripts that can run without browser automation, and use
   Playwright/Chromium screenshots when available.
10. Keep local/cloud parity documented:
    Docker Compose locally; Redis/Postgres/Ollama now; K8s/KEDA/Temporal/Argo or
    serverless alternatives later.
11. Build Baltor as the MCP context gateway for coding agents:
    Claude Code asks for context; Baltor owns retrieval policy, ACL filtering,
    hybrid search, compression, citations, source handles, audit, and live
    source fallback. See
    `docs/architecture/baltor-mcp-context-gateway.md`.

## Things To Avoid

- Do not leave "configured later" placeholders for the local happy path.
- Do not add unsupported marketing copy to the demo.
- Do not make the LLM the first system to see raw documents.
- Do not require human approval for local read-only model review.
- Do not run external OSINT/person lookups by default.
- Do not hand-type shared counts, thresholds, model IDs, or paths in multiple
  places. Put shared values in one owner and import/read them.

## Good Next Improvements

- Add a run-inspector panel to `/admin-dashboard/monitor`.
- Add a self-contained ZIP upload proof script.
- Add a small synthetic corpus fixture with nested folders and conflicting
  claims.
- Add graph export normalization with controlled edge types.
- Add local model health checks to `/admin-demo/testing`.
- Add worker-event correlation by `run_id` and `job_id`.
- Add stale/fragile/safe-context warnings to exports.
- Add a simple red/yellow/green readiness strip on every run page.
- Add `ctx://` handles and typed context-pack exports for the MCP gateway path.
