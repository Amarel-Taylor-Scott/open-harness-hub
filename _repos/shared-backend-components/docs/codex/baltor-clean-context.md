# Baltor Clean Context

This is the compact context agents should read before long autonomous runs. It
supersedes older component-count and generic-harness framing when the work is
about the current product direction.

## Current Product Truth

Baltor is the business. OpenHubForAI is the open funnel and component
substrate.

Baltor keeps enterprise agent context verified, current, reconciled, traceable,
and ready to serve. It does not compete as another generic agent builder. It
feeds trusted context into the agent, RAG system, or workflow platform the
customer already uses.

The operational story is:

1. Load data from files, folders, repositories, object stores, and SaaS systems.
2. Sync and version every source.
3. Extract text, tables, layout, entities, claims, procedures, nodes, and edges.
4. Resolve what can be resolved automatically.
5. Escalate only rare unresolved cases to Hermes/OpenClaw or a human owner.
6. Compile expensive model discoveries into cheaper deterministic workers.
7. Serve current context as text packs, RAG records, graph/hybrid retrieval, and
   audit packets with optional provenance history.

## Product Language

Prefer:

- verified
- current
- reconciled
- traceable
- modular
- token-efficient
- serving packages
- verification queue
- automated refresh jobs
- manual confirmation required

Avoid product-facing language like:

- conflict-aware
- fragile facts
- cache-shaped
- replacement
- generic agent builder

Use "needs reconciliation" only when the user sees a concrete resolution path.
Do not imply the customer data is broken.

## Core Architecture

Use the three-lane system:

- Web/API: stateless admin and serving API.
- Queue workers: cheap deterministic and model-backed document/context workers.
- Durable orchestration: Temporal for customer-visible long-running workflows,
  Argo for large batch document/index jobs.

Local-first and cloud-ready:

- Run locally with Python workers, Redis/Postgres, Ollama, and cheap open models.
- Move to cloud with Kubernetes, KEDA, Postgres/pgvector, object storage, and
  optional hosted model APIs without changing task contracts.

## Worker Hierarchy

Run cheapest-first:

1. Deterministic workers: hash, diff, MIME routing, OCR routing, chunking,
   keywords, dates, numbers, citations, dedupe, source freshness.
2. Small model workers: chunk summaries, entities, claims, table reading,
   document/source classification.
3. Medium model workers: claim normalization, evidence matching, graph edge
   inference, reconciliation candidates, provenance summaries.
4. Hermes/OpenClaw workers: unresolved investigations, adversarial review,
   external research, procedure discovery, deterministic artifact generation.

Hard rule: expensive workers should produce deterministic artifacts that cheaper
workers can replay later.

## Local And Frontier Model Flexibility

Use provider-neutral routes:

- Chat/model calls: `scripts/model_routes.py`
- Embeddings: `scripts/embeddings.py`

Local examples:

```bash
OH_LLM_BASE_URL=http://localhost:11434/v1 OH_LLM_MODEL=gemma4
OH_EMBED_BACKEND=local-st OH_EMBED_MODEL=all-MiniLM-L6-v2
```

Hosted/OpenAI-compatible examples:

```bash
OH_LLM_BACKEND=http-openai OH_LLM_BASE_URL=https://example.com/v1 OH_LLM_API_KEY=...
OH_EMBED_BACKEND=http-openai OH_EMBED_BASE_URL=https://example.com/v1 OH_EMBED_API_KEY=...
```

Never hardcode provider names, keys, model IDs, dimensions, or thresholds in new
logic. Add shared values to the existing config/registry.

## Current Demo Surface

The Baltor demo root is a quiet card-only console:

- `/admin-demo/` root launcher
- `/admin-demo/sources`
- `/admin-demo/monitoring`
- `/admin-demo/outputs`
- `/admin-demo/download`
- `/admin-demo/explore`
- `/admin-demo/testing`

Keep the root page quiet. It should show only the launcher cards. Put detail,
navigation chrome, processing internals, graph/RAG exploration, and integration
test surfaces only on dedicated pages.

## Active Risks

- `scripts/showcase/server.py` still owns shared static/generic showcase routing,
  but admin-demo API internals have been split into
  `scripts/showcase/admin_demo/routes.py`.
- `_repos/openhubforai/frontend/styles/admin-demo.css` is too broad.
- `scripts/context_workers/tasks.py` is approaching a worker monolith.
- Some older docs still lead with component-factory scale instead of Baltor
  product focus. Treat those as substrate/history unless this doc points to
  them for implementation detail.

## Definition Of Progress

A good autonomous cycle produces one validated improvement to one of these:

- Baltor admin demo quality
- backend boundaries
- worker registry and document pipeline
- local/cloud model flexibility
- serving/export packages
- source sync/versioning/provenance
- GTM/fundraising/customer acquisition material
- measurable pilot/demo evidence
- stateless worker standards for external research, source monitoring, and
  uploaded-content review prioritization
- multi-source fact adoption, source trust scoring, archive capture, and
  context-injection/spam defense
- fact-state lineage for candidates that have one source, two sources,
  authoritative support, adoption, rejection, or supersession
- shared lifecycle, state-history, priority-signal, and queue-policy fields
  across facts, sources, normalized objects, entities, labels, dimensions,
  review tickets, research tasks, jobs, and capability requests
- state-driven priority rules that requeue partial evidence, stale served facts,
  high-usage facts, trust risks, and unresolved reconciliation tasks
