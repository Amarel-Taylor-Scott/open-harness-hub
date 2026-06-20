# Baltor Context Engine — backend architecture overview

> Index for the backend. The six visible stages (Source → Reconciliation → Anti-Fragility →
> Enhancement → Optimization → Consumption + the universal Verification rail) are the *flow*;
> this page maps what's underneath. Tool picks here are the **verified** ones
> (`research/backend-tool-verification.md`) — not the raw upstream lists.

## Product boundary (keep it clean)
**Baltor owns:** the context-object contract, source handles, verification, enhancement, pack
building, receipts, policy, and delivery. **Everything else is swappable infrastructure** behind
capability adapters (`ParserProvider`, `RetrievalProvider`, `GraphProvider`, `WorkflowEngineProvider`,
`PolicyProvider`, …). Domain code depends on the capability, never a vendor SDK.

## Flow
```
Source Systems → Adapter/Manager layer → Bronze (raw+controlled) → Canonical Registry
   → Index/Graph layer → Workers (the 6 stages + verification) ⇄ Queue/Orchestration
   → Delivery (packs + receipts via MCP/API) ; Policy gates Workers+Delivery ; everything → Observability
```
The **Source → Adapter** edge hides the raw-document decomposition sub-pipeline — specified in
[`document-decomposition.md`](./document-decomposition.md) (a doc becomes a recursive tree of
addressable, typed context objects; that tree is the contract Baltor owns).

## Storage model — canonical state is NOT text files
Text files are for docs, schemas, skills, prompts, fixtures, small human-readable exports.
**Canonical state lives in databases + object storage.**

| Shape | Use for | Store |
|---|---|---|
| **Object tables** | stable identities: `context_objects`, `source_handles`, `context_packs`, `tools`, `adapters`, `pipelines` | Postgres |
| **Version tables** | immutable snapshots: source/object/pack/prompt versions | Postgres (+ object store for blobs) |
| **Long tables** | sparse/extensible: claims, dimensions, scores, events, policy decisions, rot signals, verification findings | Postgres |
| **Relationship tables** | edges/n-ary: confirms, contradicts, supersedes, owned_by, approved_by, implemented_by | Postgres → graph DB later |
| **JSONB facets** | source-specific long-tail: `jira.*`, `gitlab.*`, `confluence.*`, `custom.*` | Postgres JSONB + GIN |
| **Wide tables** | fast UI/dashboard projections **only** | Materialized views (disposable) |
| **Object storage** | raw snapshots, parsed artifacts, page images, generated wikis, large exports | S3 / R2 / MinIO |
| **Vector index** | chunk embeddings that *reference* leaf object IDs | Qdrant (primary) / pgvector (demo) |
| **Graph index** | traversal/path/contradiction queries | Graphiti (primary) — **not Kuzu (archived Oct 2025)** |

**Do NOT:** store raw source dumps in git · keep source-of-truth context only in Markdown ·
make the vector DB canonical · let generated repo wikis be authoritative.
**DO:** put large artifacts in object storage · put identity/lineage/policy/receipts in Postgres ·
use long tables for scores/claims/events/relationships · use wide tables only as read models.

## Verified backend stack (primary → fallback)
Full table + rationale + the hallucination report in `research/backend-tool-verification.md`;
machine-readable in `data/backend-tools.yaml`. Headlines: **Docling→Unstructured** (parse) ·
**Crawl4AI→Scrapy** (scrape) · **Qdrant→pgvector** (retrieval) · **Graphiti→Cognee** (claim graph) ·
**DBOS→Temporal** (durable workflow; **Pydantic AI→LangGraph** for the agent layer) ·
**IBM ContextForge→Docker MCP Gateway** (MCP) · **OpenFGA + OPA/Cedar** (policy) ·
**Langfuse→Phoenix+Ragas** (obs/evals, emit OTel GenAI) · **E2B→microsandbox** (sandbox).
**Corrected from the upstream map:** drop "Synapse AI" (unverifiable), "Microsoft Conductor"
(dev-CLI, not a durable engine), and "Kuzu" (archived).

## Local, no-paid-services demo
Docker Compose: `postgres` (pgvector) + `qdrant` + `minio` + `openfga` + `opa` + `ollama` +
`langfuse` + Baltor `api`/`worker`. Free demo data sources (no-/low-auth) in
[`../../research/free-demo-apis.md`](../../research/free-demo-apis.md). The proven real connector
to copy: `scripts/ingest/sanctions_feed_live.py` (live OFAC fetch → verified-context flow).

## Build runbook
Phased, verify-first, context-rot-conscious: [`../../prompts/baltor-context-engine-build.md`](../../prompts/baltor-context-engine-build.md).
