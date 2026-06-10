# Context Worker Registry

Context Fidelity needs a registry of stateless workers that can be queued,
scheduled, retried, scaled, audited, and swapped across local development,
Redis/KEDA, Celery, and Kubernetes.

The core abstraction should not be Celery, Temporal, or Argo itself. The durable
abstraction is:

```text
task envelope -> worker registry -> queue backend -> stateless worker -> ledger/output refs
```

Celery, RQ, arq, SQS, Cloud Tasks, Temporal, Argo, and K8 Jobs can all sit under
or above that contract. The platform should keep task names and output contracts
stable so execution backends can change without rewriting the product.

## Backend Choice

| Backend | Best fit | OHH role |
|---|---|---|
| Local SQLite queue | no-service development, CI smoke tests | default fallback |
| Redis + KEDA | bursty queue draining on Kubernetes | first cloud worker fleet |
| Celery | Python task routing, scheduled jobs, Flower inspection, groups/chords | optional task backend |
| Temporal | durable N-pass runs, human review gates, long-running refreshes, workflow replay | premium durable orchestrator |
| Argo Workflows | K8-native container DAGs, scheduled batch runs, highly parallel document jobs | batch/container orchestrator |

The recommended order is:

```text
local registry + SQLite
-> Redis/KEDA worker fleet
-> Argo for bounded batch DAGs
-> Temporal for durable long-running/human-review workflows
-> Celery only where Python task ergonomics are worth the extra worker stack
```

## First Runnable Slice

The local scaffold lives in `scripts/context_workers/`:

- `registry.py` defines `WorkerRegistry`, `WorkerSpec`, `TaskContext`, and
  `TaskResult`.
- `router.py` maps task envelopes to registered workers, lanes, images, and
  output contracts without binding the product to a queue backend.
- `tasks.py` is a compatibility import shell for the built-in worker modules.
- `common.py` holds deterministic helper functions shared by built-in workers.
- `lifecycle.py` standardizes preflight, payload loading, structured JSON logs,
  runtime metadata, execution timing, follow-up counts, and closeout records.
- `runtime_io.py` provides shared artifact writes, heartbeat files,
  idempotency markers, atomic JSON writes, and runtime health checks.
- `workers/*.py` registers deterministic baseline workers by lane.
- `runner.py` enqueues and drains jobs through the existing
  `scripts.foundry.queues` adapter.

The document-intelligence implementation and adapter matrix are documented in
[`document-intelligence-pipeline.md`](document-intelligence-pipeline.md).
The node research, OSINT, public-record enrichment, and verification-tier layer
is documented in
[`node-research-and-verification.md`](node-research-and-verification.md).
The hierarchical LLM trust layer is documented in
[`llm-trust-layer.md`](llm-trust-layer.md).

Run:

```bash
python -m scripts.context_workers.runner --manifest
python -m scripts.context_workers.runner --validate-manifest
python -m scripts.context_workers.runner --validate-research-tasks tasks.json
python -m scripts.context_workers.runner --route-task task.json
python -m scripts.context_workers.runner --preflight-task task.json
python -m scripts.context_workers.runner --health
python -m scripts.context_workers.runner --requeue-scan facts-and-sources.json
python -m scripts.context_workers.runner --self-test
python -m scripts.context_workers.runner --adversarial-fixtures
python -m scripts.context_workers.runner --enqueue-pass context.txt
python -m scripts.context_workers.runner --serve --max-jobs 20
python -m scripts.context_workers.runner --watch
python -m scripts.context_workers.runner --run-inline-pass context.txt
```

Local development uses SQLite by default. Cloud can use Redis with KEDA on queue
depth. Celery can be added as another backend when its scheduler, routing, task
inspection, or retry ecosystem is worth the operational weight.

Optional backend shims:

- `scripts.context_workers.backends.celery_app`
- `scripts.context_workers.backends.temporal_bridge`

Optional dependency groups:

- `requirements-orchestration.txt` for Celery, Temporal, and Hera.
- `requirements-context-tools.txt` for document/context processing tools.

## Worker Lanes

Use named lanes rather than one undifferentiated queue:

| Lane | Purpose | Example workers |
|---|---|---|
| `ingest` | receive uploaded/raw context and source refs | source fetch, upload intake, snapshot |
| `normalize` | produce clean, chunkable text | HTML/PDF conversion, OCR, chunking |
| `analyze` | extract low-cost signals | keywords, entities, claims, dates, numbers |
| `graph` | produce nodes and edges | entity graph, claim graph, source graph |
| `embed` | produce vector records | chunk embeddings, claim embeddings, graph embeddings |
| `verify` | test reliability | fragility scan, citation check, reconciliation |
| `refresh` | update volatile facts | search, API tools, CDC feeds, publisher checks |
| `promote` | move verified outputs forward | review ticket, context pack update, index publish |

The first registered workers are:

- `context.text.normalize`
- `context.document_tree.normalize`
- `context.chunk`
- `context.dedupe.fingerprint`
- `context.keyword`
- `context.nlp.signals`
- `context.proper_noun.extract`
- `context.regex.extract`
- `context.pii.detect`
- `context.entity.extract`
- `context.claim.extract`
- `context.document_graph.build`
- `context.code_graph.build`
- `context.graph.extract`
- `context.graph.metrics`
- `context.fragility.scan`
- `context.ambiguity.scan`
- `context.conflict.scan`
- `context.fragile_fact.enrich`
- `model.cascade.catalog`
- `llm.trust.plan`
- `llm.claim.review`
- `llm.graph.enrich`
- `llm.context.summarize`
- `llm.conflict.review`
- `llm.audit.review`
- `context.refresh.plan`
- `node.research.catalog`
- `node.research.plan`
- `node.research.enrich`
- `node.evidence.score`
- `context.search.verify`
- `context.pipeline.pass`
- `context.lifecycle.requeue` is implemented as a scheduler/helper surface in
  `scripts/context_workers/requeue.py`; it scans persisted fact/source records
  and emits deduped follow-up task envelopes for second-source search, refresh,
  reconciliation, source trust review, and archive capture.

The deterministic pre-LLM pass now covers these non-model stages before any
Gemma/Hermes/OpenClaw style worker is needed:

- normalize Unicode, HTML entities, control characters, line endings, and
  whitespace;
- normalize uploaded files, ZIP file sets, connector envelopes, folders, pages,
  and page components into stable hierarchy records;
- chunk text with stable IDs;
- compute exact and near-duplicate fingerprints;
- extract keyword, regex, proper-noun, entity, claim, and text-statistic
  signals;
- detect common PII before external model routing;
- build document, code, and context graphs;
- compute baseline graph metrics for components, isolates, and high-degree
  nodes;
- scan fragility and emit refresh/research follow-up tasks.
- plan lawful public-record and OSINT-style research for detected nodes without
  promoting weak enrichment hits to verified graph facts.

The optional adapter surface is registered separately so experiments can turn
tools on and off without changing queue contracts. Adapters report `ready`,
`disabled`, `missing_dependency`, or `not_configured` rather than hiding why a
configuration did not run.

Document and OCR adapters:

- `document.parse.docling`
- `document.parse.unstructured`
- `document.parse.tika`
- `document.parse.markitdown`
- `document.parse.marker`
- `document.parse.mineru`
- `document.ocr.paddle`
- `document.parse.grobid`
- `document.parse.pymupdf`
- `document.parse.pdfplumber`

Deterministic NLP, privacy, dedupe, and feature adapters:

- `nlp.spacy.extract`
- `nlp.textacy.extract`
- `nlp.stanza.extract`
- `nlp.gliner.extract`
- `text.ftfy.repair`
- `text.language.detect`
- `entity.rapidfuzz.alias`
- `dedupe.datasketch.minhash`
- `privacy.presidio.detect`
- `nlp.sklearn.features`

Graph, search, and RAG integration adapters:

- `graph.networkx.analyze`
- `graph.rdf.export`
- `osint.openosint.catalog`
- `osint.openosint.run`
- `semantic.opensearch.etl`
- `semantic.opensearch.entity_link`
- `index.fscrawler.submit`
- `index.solr_tika.submit`
- `rag.llamaindex.property_graph`
- `rag.haystack.pipeline`
- `rag.neo4j_graphrag.build`
- `rag.microsoft_graphrag.index`
- `rag.ragflow.ingest`
- `rag.lightrag.index`
- `graph.falkordb_graphrag.build`
- `graph.docling_graph.extract`
- `memory.cognee.ingest`
- `memory.graphiti.upsert`
- `pipeline.cocoindex.extract`
- `kg.openspg_kag.build`
- `llm.langchain_graph_transformer.extract`
- `llm.langextract.extract`
- `llm.ontogpt.extract`
- `llm.structured_output.extract`
- `llm.constrained_decode.extract`
- `ie.deepke.extract`
- `ie.relik.extract`
- `summary.raptor.build`
- `app.dify.workflow`
- `app.flowise.workflow`
- `app.langflow.workflow`
- `app.anythingllm.ingest`
- `managed.diffbot.nlp`
- `context.adapters.catalog`
- `context.pipeline.experimental_adapters`

Use `CONTEXT_ENABLED_ADAPTERS=all` to leave every adapter eligible, or set a
comma-separated allow list such as `docling,pymupdf,spacy,networkx`. Individual
task payloads can also pass `enabled_adapters` or `disabled_adapters`.

OSINT adapters are gated separately. `osint.openosint.run` requires
`payload.authorized=true` or `OSINT_AUTHORIZED=true` before it will call the
OpenOSINT CLI. Use it only for authorized passive security research, enrichment,
or verification workflows.

Each registered worker advertises the runtime metadata that queue routers and
K8s deployments need:

- `capabilities` for capability matching;
- `task_types` for task-intent routing;
- `image` for CPU, audit, research, orchestrator, OCR, or GPU pool placement;
- `output_contract` for artifact validation and downstream package builders.
- `cost_policy` for budget enforcement, expensive-lane batching, and metered
  resource accounting.

That metadata keeps the local decorator registry compatible with future private
PyPI packages and cloud worker fleets.

The generated manifest is intended to validate against
`schemas/worker-manifest.schema.json`. That gives K8s, Temporal, Argo, Celery,
Cloud Run, and local runners one shared worker contract instead of separate
per-backend definitions.

Use `--validate-manifest` in local checks and CI when changing worker
registration metadata. The runner validates every registered worker against the
portable manifest schema before downstream orchestrators consume it.

Use `--validate-research-tasks` for emitted follow-up work. Research, refresh,
archive, reconciliation, and trust-review tasks should carry `task_id`, `state`,
lane, priority, cost estimate, budget policy, and queue policy before any local
queue, managed queue, Temporal activity, Argo step, Celery task, or K8s worker
consumes them. The `--requeue-scan` command runs this validation automatically
for its emitted tasks.

Task envelopes and follow-up tasks should also carry `cost_estimate` and
`budget_policy`. Local runners can only report these fields, but cloud routers
should enforce them before work reaches browser, research, audit, GPU, Hermes,
OpenClaw, or frontier-model lanes.

## Python Package Shape

Use a monorepo package first, with a clean path to internal PyPI packages later.
Do not create a separate repository or container image for every worker until a
real dependency, security, ownership, or scaling boundary exists.

Recommended package layout:

```text
scripts/context_workers/
  registry.py              # WorkerRegistry, WorkerSpec, TaskContext, TaskResult
  runner.py                # queue drain/watch/inline execution
  priority.py              # deterministic priority and follow-up policy
  common.py                # shared deterministic helpers
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

When the API stabilizes, promote stable parts into packages:

```text
baltor-worker-core          # contracts, registry, runtime, preflight, queues
baltor-worker-docs          # document/OCR/layout workers
baltor-worker-research      # browser/search/source-trust workers
baltor-worker-graph         # graph/index workers
baltor-worker-models        # local model, embedding, rerank workers
```

The public extension point should be the worker contract, not the current file
layout.

## Worker Lifecycle

Every worker should fit the same lifecycle even when implemented as a plain
function today:

```text
pull task
-> validate envelope and payload schema
-> preflight environment, secrets, tools, network, model, and storage
-> acquire lease / idempotency key
-> load lightweight resources
-> execute with timeout, cost, and scope limits
-> write artifacts and evidence packets
-> emit state, lineage, child tasks, warnings, and metrics
-> ack, retry, approval_required, budget_blocked, or failed_permanently
-> release lease and clean shutdown
```

The runnable implementation is `scripts/context_workers/lifecycle.py`. It wraps
all registered workers with:

- preflight checks for job id, worker match, run id, tenant id, payload shape,
  and output contract;
- JSON log events on stderr for `preflight`, `load`, `execute`,
  `emit_followups`, `budget_gate`, and `closeout`;
- runtime metadata including backend, hostname, pid, queue key, ledger path,
  worker image, and lifecycle version;
- durable ledger fields `runtime` and `lifecycle` for every processed job;
- artifact manifests and separate output/runtime/lifecycle/warnings JSON files
  under `dist/context-worker-artifacts/<run>/<job>/`;
- heartbeat files under `dist/context-worker-runtime/heartbeats/`;
- idempotency markers under `dist/context-worker-runtime/idempotency/`, where
  completed work suppresses duplicate delivery but held/failed work can be
  resumed after operator action;
- `SIGTERM`/`SIGINT` handling in `runner.py` so watch loops stop after the
  current poll/claimed task instead of silently disappearing.

This keeps the worker functions pure while making local Docker, K8s, Cloud Run,
Temporal, Celery, and CI runs produce the same operational record shape.

The eventual class-style contract should support:

```python
class Worker:
    name = "research.business.address.lookup"
    lane = "research"
    capabilities = ["search", "browser", "source_trust"]

    def preflight(self, ctx): ...
    def load(self, ctx): ...
    def run(self, task, ctx): ...
    def shutdown(self, ctx): ...
```

The current decorator registry can remain the lightweight local interface while
the runtime grows preflight, lease, telemetry, cancellation, and shutdown hooks
around it.

## Container Image Strategy

Use lane-based images first:

| Image | Contents | Example lanes |
|---|---|---|
| `baltor-worker-cpu` | registry runner, deterministic Python workers | normalize, analyze, graph, verify, package |
| `baltor-worker-browser` | Playwright/browser tooling, network sandbox | research, source trust, archive capture |
| `baltor-worker-ocr` | PDF/OCR/layout/table dependencies | ingest, parse, normalize |
| `baltor-worker-ml` | local embeddings, rerankers, small models | embed, classify, reconcile |
| `baltor-worker-gpu` | vLLM/Ollama/Gemma/Qwen clients where available | model-reason, high-volume embedding |

Split an individual worker into its own image only when it has heavy native
dependencies, strict sandbox needs, separate scaling behavior, or third-party
licensing constraints.

## Context Tooling

The worker registry should wrap deterministic tools first, then model-backed
workers where deterministic evidence is insufficient.

| Need | Deterministic / local-first tools | Model-backed extension |
|---|---|---|
| Document conversion | Docling, Unstructured, PyMuPDF, Tesseract | Granite-Docling, VLM layout readers |
| OCR/layout/table extraction | Docling, Tesseract, PaddleOCR, Table Transformer-style workers | frontier VLM verification |
| Chunking | structure-aware headings, page spans, sentence windows, token budgets | LLM chunk labeling |
| Keyword/facet extraction | regex, BM25, YAKE/RAKE-style scoring | small model topic tagging |
| Entity extraction | spaCy, GLiNER, rule dictionaries | frontier model entity adjudication |
| Node/edge extraction | deterministic claim/entity graph, NetworkX | docling-graph, LLM relation extraction |
| Reconciliation | source precedence rules, date/scope checks, polarity checks | judge model for ambiguous mismatches |
| Refresh | signed feeds, search APIs, CDC, publisher checks | frontier model source comparison |

Current research candidates:

- Argo Workflows and Hera for Kubernetes-native workflow DAGs.
- Temporal Python SDK for durable workflows and activities.
- Docling and Unstructured for document conversion, OCR, layout, chunking, and
  table-aware preprocessing.
- GLiNER and spaCy for local/open entity extraction.
- docling-graph for validated document knowledge graphs.

See `baltor-worker-operating-model.md` for adversarial validation, managed
cloud-service alternatives to K8s, and the recommended CPU, audit, research,
orchestrator, OCR, and GPU worker pools.

Sources:

- Argo Workflows: <https://github.com/argoproj/argo-workflows>
- Hera: <https://github.com/argoproj-labs/hera>
- Temporal Python SDK: <https://github.com/temporalio/sdk-python>
- Docling: <https://www.docling.ai/>
- Unstructured: <https://github.com/Unstructured-IO/unstructured>
- GLiNER: <https://github.com/urchade/GLiNER>
- docling-graph: <https://github.com/IBM/docling-graph>

## Task Envelope

Every queued task should carry:

```json
{
  "job_id": "cw-...",
  "task": "context.pipeline.pass",
  "task_type": "verify.second_source.find",
  "lane": "verify",
  "priority": "normal",
  "run_id": "run-...",
  "tenant_id": "tenant-or-local",
  "pass_index": 1,
  "parent_job_id": null,
  "priority_signals": {},
  "queue_policy": {},
  "payload": {},
  "queued_at": 1780200000
}
```

Large raw documents should move through object-storage pointers, not inline
queue payloads. Inline text is acceptable for the admin demo and local smoke
tests.

When a task is emitted from a fact, source, entity, label, dimension, review, or
normalized object, it should copy the relevant `state`, `priority_signals`, and
`queue_policy` from the producing record. See
`baltor-queue-priority-orchestration.md`.

## N-Pass Processing

The admin demo should evolve toward a repeated pass model:

```text
pass 1: chunk, keywords, entities, initial claims
pass 2: graph edges, entity resolution, claim grouping
pass 3: reconciliation, citation support, fragile-fact scan
pass N: refresh workers, stronger tools, curator review, context-pack promotion
```

Each pass emits append-only outputs and optional child jobs. Child jobs inherit
`run_id`, set `parent_job_id`, and increment `pass_index`.

## K8 Shape

For Kubernetes:

- one container image can run many registered workers at first;
- split images only when dependencies diverge, such as browser/PDF/OCR/GPU;
- route lanes to separate queue keys;
- use KEDA to scale deployments on queue depth;
- write outputs to object storage/Postgres and append a run ledger;
- keep workers idempotent so retries are safe.

The long-running deployable unit is:

```text
python -m scripts.context_workers.runner --watch
```

with environment selecting the queue:

```text
OH_QUEUE_PATH=dist/context-workers.sqlite       # local
REDIS_URL=redis://...                           # cloud/KEDA
CONTEXT_QUEUE_KEY=ohh:context:jobs              # lane key
```

Concrete local/cloud files:

- `infra/docker-compose.context.yml`
- `infra/k8s/context-worker.yaml`
- `infra/k8s/argo-context-pipeline.yaml`

## Celery Position

Celery is useful when we need:

- distributed scheduled jobs;
- mature retries and task routing;
- task introspection/UI;
- chord/group primitives for fan-out/fan-in;
- a known ops pattern for Python teams.

It should not define the product contract. It should be a backend adapter for
the same registry and task envelope. That keeps local development, K8 workers,
and future managed queues aligned.

## Product Rule

Workers do not directly publish public context. They emit evidence packets,
graph records, embeddings, refresh candidates, and review tickets. Promotion
requires verification, reconciliation, privacy-scope checks, and curator or
policy approval.
