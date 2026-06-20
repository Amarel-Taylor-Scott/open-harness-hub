# Baltor Stateless Worker Standard

Baltor workers should be small, stateless, idempotent, and easy to run locally
or in Kubernetes. A worker owns a capability, not state.

State lives in durable systems:

- Postgres/source ledger
- object storage for raw, extracted, and exported artifacts
- vector, keyword, and graph indexes
- queue/orchestrator metadata
- run/event ledger

Workers receive task envelopes and emit structured evidence, artifact URIs,
child tasks, confidence, escalation signals, and deterministic artifacts when
they discover reusable procedures.

## Task Envelope

```json
{
  "task_id": "cw-...",
  "run_id": "run-...",
  "tenant_id": "tenant-...",
  "capability": "web.price.check",
  "lane": "research",
  "priority": "normal",
  "scope": {
    "privacy": "tenant",
    "allowed_domains": ["example.gov"],
    "blocked_domains": [],
    "max_pages": 25,
    "max_cost_usd": 0.25,
    "deadline_s": 120
  },
  "input": {
    "query": "current filing fee",
    "source_uri": "s3://...",
    "context_refs": []
  },
  "output_contract": "evidence_packet.v1",
  "model_policy": {
    "lane": "deterministic|small|medium|frontier",
    "allow_remote": false
  }
}
```

## Worker Classes

| Class | Purpose | Example capabilities |
|---|---|---|
| `source-sync` | Detect source changes and create version events. | Drive/SharePoint/Git/S3 sync, website sitemap scan. |
| `fetch` | Fetch one URL/API/object safely. | price page, statute page, company profile. |
| `browser-research` | Browse scoped sites with limits and evidence capture. | find latest address, browse government site for a fact. |
| `doc-process` | Extract and normalize uploaded content. | OCR, layout, tables, hierarchical chunking. |
| `context-analyze` | Work over processed chunks. | entities, claims, procedures, fragile-section ranking. |
| `graph` | Create or repair nodes and edges. | corporate hierarchy, source-to-claim graph, M&A relation edges. |
| `verify` | Check facts against sources. | statute citation, latest price, current address, source precedence. |
| `model-reason` | Use local/hosted models within bounded tasks. | reconciliation candidate, provenance summary. |
| `hermes` | Open-ended investigation for unresolved cases. | search many sources, produce resolution artifact. |
| `openclaw` | Adversarially test proposed resolutions. | counterexamples, overreach tests, scope boundaries. |
| `compile` | Turn non-deterministic solutions into reusable deterministic artifacts. | resolver rule, extraction template, query template. |

## External Research Capabilities

The same standard should cover:

- visit a website and check price information;
- visit a government website and read a published statute;
- browse a government site and find a specific fact;
- search for the latest business address;
- find the corporate hierarchy of a business;
- look for M&A news about employment agencies;
- look up capability or documentation for a function, class, API, or library;
- monitor a source for changes and enqueue downstream refresh jobs.

External research tasks must return source URLs, retrieval timestamps, extracted
answers, evidence spans or structured evidence, confidence, freshness labels,
next recommended tasks, and unresolved reasons when the worker cannot prove the
answer.

See `baltor-source-trust-and-adoption-policy.md` for multi-source adoption,
fact-state lineage, archive capture, publisher trust scoring, and injection/spam
screening.

See `baltor-queue-priority-orchestration.md` for the shared queue lanes,
priority signals, state attributes, and follow-up task policy that every worker
should use when it emits more work.

## Uploaded-Content Review Prioritization

After hierarchical chunking, workers should rank sections for immediate review:

- dated claims
- numeric thresholds
- owner/person claims
- legal/regulatory statements
- future-looking or ambiguous language
- uncited operational claims
- claims contradicted by higher-authority sources
- sections that changed since last sync
- sections frequently retrieved by agents

Output:

```json
{
  "capability": "context.fragile_section.rank",
  "sections": [
    {
      "chunk_id": "chunk-...",
      "priority": "high",
      "signals": ["dated", "numeric", "legal"],
      "recommended_worker": "verify.statute.lookup",
      "reason": "dated numeric legal threshold needs current authority"
    }
  ]
}
```

## Kubernetes Image Pattern

Use a few lane-based images, not one image per task:

- `baltor-worker-cpu`: registry runner, deterministic workers.
- `baltor-worker-orchestrator`: fan-out/fan-in, N-pass coordination, package
  builds, low-dependency workflow glue.
- `baltor-worker-audit`: source trust, adversarial validation, injection
  screening, adoption policy checks.
- `baltor-worker-research`: search, browser fetch, website reading, source
  snapshots, archive submission.
- `baltor-worker-browser`: Playwright/browser tooling, strict sandbox when the
  research image needs full browser automation.
- `baltor-worker-ocr`: OCR/layout/document dependencies.
- `baltor-worker-ml`: local model clients, embedding/rerank dependencies.
- `baltor-worker-gpu`: high-throughput local model serving where available.

Each image starts the same entrypoint:

```bash
python -m scripts.context_workers.runner --watch
```

Capabilities are selected by task envelope and worker registration, not by
changing orchestration code.

The worker manifest should expose `capabilities`, `task_types`, `image`, and
`output_contract` so the router can place work into the cheapest safe pool. See
`baltor-worker-operating-model.md` for the recommended split between managed
cloud services, always-on orchestrators, KEDA-scaled K8s pools, and optional GPU
workers.

## Python Code Organization

Start as a monorepo package with a plugin-style worker registry. Split into
private PyPI packages only after the contracts stabilize or dependencies diverge.

Current local structure:

```text
scripts/context_workers/
  registry.py              # task/worker/result contracts
  runner.py                # queue drain/watch/inline execution
  priority.py              # queue priority and follow-up policy
  common.py                # deterministic shared helpers
  tasks.py                 # compatibility import shell
  workers/
    chunk.py
    keyword.py
    entity.py
    claim.py
    graph.py
    fragility.py
    refresh.py
    pipeline.py
  backends/
    celery_app.py
    temporal_bridge.py
```

Future package split:

- `baltor-worker-core`: contracts, registry, runtime, telemetry, preflight,
  queues, artifact storage, shutdown handling.
- `baltor-worker-docs`: parsing, OCR, layout, tables, chunking.
- `baltor-worker-research`: browser/search/source-trust/archive capture.
- `baltor-worker-graph`: graph extraction, repair, indexing.
- `baltor-worker-models`: embeddings, rerankers, small-model and frontier-model
  adapters.

The stable extension point should be the task envelope, worker lifecycle, and
result contract, not a particular queue framework.

## Worker Lifecycle Hooks

Every worker should eventually support:

- `preflight`: check env vars, secrets, tools, model availability, network
  policy, allowlists, storage, and cost limits.
- `load`: lazily load models, browser contexts, index handles, or parser state.
- `execute`: run the task under deadline, retry, cost, and tenant-scope limits.
- `write_artifacts`: store raw outputs, evidence packets, graph records, and
  package manifests by content hash.
- `emit_followups`: enqueue child tasks with inherited state, priority signals,
  and queue policy.
- `shutdown`: release leases, close browser/model handles, flush telemetry, and
  clean temporary files.

That lifecycle keeps local SQLite workers, Redis/KEDA workers, Celery tasks,
Temporal activities, and Argo containers aligned.

## Safety And Governance

External workers must enforce domain allowlists, robots/rate limits where
applicable, max pages, max time, max cost, tenant-scoped caches, evidence
capture without excessive copied text, reproducible timestamps and source
hashes, and explicit unresolved status instead of guessed answers.

## Promotion Rule

A worker output can feed agent context only when it has source or internal
authority, requester scope allows it, freshness metadata exists, volatile claims
have a refresh policy, provenance is retained, and unresolved cases are not
silently promoted.
