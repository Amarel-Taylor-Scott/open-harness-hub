# Baltor Worker And Orchestration Research

Date: 2026-05-31

This research note broadens the worker architecture beyond K8s-only execution.
The right platform shape is hybrid: managed cloud services for commodity state
and triggers, Kubernetes for controlled execution pools, Temporal for durable
customer-visible workflows, Argo for batch DAGs, and cloud functions/jobs for
small bursty tasks.

## Core Recommendation

Use one worker contract and multiple execution substrates:

```text
task envelope
  -> worker registry
  -> queue/orchestrator adapter
  -> managed function, Cloud Run job, K8s deployment, Argo step, or Temporal activity
  -> artifact/evidence store
  -> state transition and follow-up tasks
```

Do not let any one backend define the product model. The stable product model is
the task envelope, lifecycle hooks, artifact contracts, fact/source state, and
priority policy.

## Orchestration Options

| Option | Best Use | Avoid When | Baltor Role |
|---|---|---|---|
| Local SQLite/Redis runner | local dev, CI, demos | production durability is needed | default local parity |
| Cloud Tasks / SQS / Pub/Sub | simple queues, rate limits, retries | complex multi-step stateful workflows are needed | managed queue option |
| Cloud Run Jobs / Azure Container Apps Jobs | finite container tasks with autoscaling | heavy browser/GPU/sandbox control is needed | bursty stateless execution |
| Lambda / Cloud Functions | small event-driven tasks | long jobs, heavy dependencies, browser automation | source pings, webhooks, archive callbacks |
| KEDA + K8s deployments | queue-draining worker pools, scale-to-zero | team cannot operate K8s yet | main controlled worker fleet |
| Argo Workflows | large bounded container DAGs | workflows span days or require human gates | reindex, rebuild, OCR batches |
| Temporal | durable workflows, retries, heartbeats, resumability | trivial fire-and-forget tasks | source sync, adoption, customer-visible progress |
| Celery | Python-native task routing and inspection | strict durability/replay is required | optional early backend, not source of truth |

Relevant docs:

- KEDA ScaledObject/external scaler model: <https://keda.sh/docs/2.19/concepts/external-scalers/>
- Argo Workflows: <https://argoproj.github.io/workflows/>
- Temporal docs and Python SDK: <https://docs.temporal.io/> and <https://python.temporal.io/>
- Celery routing: <https://docs.celeryq.dev/en/latest/userguide/routing.html>
- Cloud Run services/jobs/worker pools: <https://docs.cloud.google.com/run/docs/overview/what-is-cloud-run>
- Cloud Tasks queue rate limits and retry parameters: <https://docs.cloud.google.com/tasks/docs/configuring-queues>
- AWS Lambda with SQS event source mappings and failed-message quarantine queues:
  <https://docs.aws.amazon.com/lambda/latest/dg/services-sqs-configure.html>
- Azure Container Apps jobs and KEDA-backed event-driven jobs: <https://learn.microsoft.com/en-us/azure/container-apps/jobs>
- AWS Step Functions orchestration: <https://aws.amazon.com/documentation-overview/step-functions/>

## Managed Services Versus K8s

K8s is valuable for execution control, but it is not automatically better for
commodity infrastructure. For Baltor, managed services should be the default for:

- Postgres and pgvector;
- object storage;
- queue primitives;
- secrets;
- transactional email;
- schedules;
- observability;
- simple event functions.

K8s should be used when Baltor needs:

- Playwright/browser isolation;
- OCR/native dependency control;
- GPU node placement;
- tenant-specific network policy;
- long-running queue drainers;
- batch DAGs over large corpora;
- custom image and resource profiles.

This reduces operational drag while preserving a path to isolated enterprise
deployments.

## Worker Pool Design

| Pool | Image | Workloads | Notes |
|---|---|---|---|
| CPU | `baltor-worker-cpu` | chunking, keyword, claims, graph, package exports | cheap default |
| Orchestrator | `baltor-worker-orchestrator` | fan-out/fan-in, progress, N-pass coordination | keep small and reliable |
| Audit | `baltor-worker-audit` | adversarial validation, injection screening, trust scoring | stricter egress and logging |
| Research | `baltor-worker-research` | search, source lookup, official page reads | domain allowlists, source snapshots |
| Browser | `baltor-worker-browser` | JS-heavy pages, price checks, dynamic sites | Playwright sandbox |
| OCR/doc | `baltor-worker-ocr` | PDFs, scans, tables, layout | heavy dependencies |
| GPU | `baltor-worker-gpu` | embeddings, rerankers, local small models | optional; API model fallback |
| Archive | `baltor-worker-archive` or function | archive submissions and hash capture | low concurrency |

The worker registry should expose `capabilities`, `task_types`, `image`, and
`output_contract` so the queue router can choose the cheapest safe pool.

## Document Processing Research

Baltor should prefer deterministic or local-first document processing before
model escalation.

| Need | Candidate Tools | Notes |
|---|---|---|
| PDF/DOCX/HTML conversion | Docling, Unstructured, PyMuPDF | Docling emphasizes structured conversion, OCR, tables, formulas, and reading order. Unstructured partitions documents into semantic elements before chunking. |
| Chunking | structure-aware chunks, LangChain splitters, LlamaIndex ingestion | LangChain recommends recursive splitting as a generic baseline. LlamaIndex ingestion pipelines hash/cache node + transformation pairs. |
| Entity extraction | spaCy, GLiNER | spaCy has mature production pipelines; GLiNER is useful for lightweight zero-shot entity types. |
| Graph extraction | NetworkX, Neo4j GraphRAG, docling-graph | Use deterministic entity/claim edges first; escalate to LLM relation extraction when needed. |
| Hybrid retrieval | pgvector, BM25, graph traversal, rerankers | Serve text, RAG, graph, and audit packages from the same evidence lineage. |

Relevant docs:

- Docling: <https://www.docling.ai/>
- Unstructured chunking: <https://docs.unstructured.io/open-source/core-functionality/chunking>
- LangChain text splitters: <https://docs.langchain.com/oss/python/integrations/splitters/index>
- LlamaIndex ingestion pipeline: <https://docs.llamaindex.ai/en/stable/module_guides/loading/ingestion_pipeline/>
- spaCy pipelines and NER: <https://spacy.io/usage/processing-pipelines/> and <https://spacy.io/usage/spacy-101>
- GLiNER: <https://github.com/urchade/GLiNER>
- Neo4j GraphRAG: <https://neo4j.com/labs/genai-ecosystem/graphrag/>

## Reusable Project And Package Map

Baltor should standardize around wrappers and artifact contracts, not private
forks of every document, crawler, model, and orchestration project. The worker
contract is the stable surface; packages underneath can change per workload,
tenant, file type, or deployment environment.

| Domain | Projects to evaluate | How Baltor should use them |
|---|---|---|
| PDF/page extraction | PyMuPDF, PyMuPDF4LLM, pdfplumber, Poppler | Page splitting, page rendering, bounding boxes, first-pass text/table extraction. Wrap as `document.page.extract` and `document.page.render` workers. |
| Structured document conversion | Docling, Unstructured, MinerU | Convert PDFs/DOCX/HTML/images into page/component trees. Use as pluggable `document.structure.extract` backends. |
| OCR/layout/tables | Surya, PaddleOCR, EasyOCR, Tesseract, LayoutParser, Camelot/Tabula-style table tools | Run in OCR/doc image, not the base CPU image. Emit page components with coordinates and confidence. |
| Web crawling | Scrapy, scrapyd, trafilatura, inscriptis, Playwright | Scrapy for broad crawls; trafilatura/inscriptis for clean article text; Playwright/browser-use only for dynamic or workflow-heavy pages. |
| Browser agents | Playwright, browser-use, hosted browser APIs where allowed | Keep behind `baltor-worker-browser`; require domain allowlists, egress policy, source snapshots, and injection checks. |
| Model gateway | LiteLLM, Portkey Gateway, OpenRouter, direct OpenAI-compatible client | Use under Baltor's policy resolver. Do not let the gateway decide privacy, adoption, or source-trust policy. |
| Orchestration | Temporal, Argo Workflows, Prefect, Dagster, Celery, KEDA | Temporal for durable customer-visible flows; Argo for large K8s batch DAGs; Celery/Redis for early local/Python async; Prefect/Dagster are good data-pipeline alternatives where teams already use them. |
| Graph extraction | NetworkX, Neo4j GraphRAG, DeepKE, graph_builder, Open Semantic ETL | Start with deterministic graph construction; use relation-extraction packages for candidate edges, not direct fact adoption. |
| Observability/evals | OpenTelemetry, Langfuse, promptfoo, Ragas, DeepEval | Emit traces and model-route records for every model call; use eval packages to regression-test extraction, RAG, reconciliation, and distillation outputs. |
| Provenance/archive | Internet Archive Save Page Now, wayback Python clients, WARC tooling | Archive high-value verification sources and store hashes, timestamps, URL, retrieval method, and source-state transitions. |

Research notes from current sources:

- PyMuPDF is a high-performance Python library for extracting, analyzing,
  converting, and manipulating PDF and related document formats, and PyMuPDF4LLM
  can emit LLM/RAG-friendly Markdown with tables in reading order:
  <https://github.com/pymupdf/PyMuPDF>
- Docling's public docs emphasize OCR, layout, tables, formulas, reading order,
  and structured document output: <https://www.docling.ai/>
- Surya covers OCR, layout analysis, reading order, and table recognition across
  many languages: <https://github.com/datalab-to/surya>
- Scrapy is the mature Python crawling framework; scrapyd can run spiders as a
  service: <https://github.com/scrapy/scrapy>
- Portkey Gateway and LiteLLM both cover multi-provider model routing/fallback
  use cases, while OpenRouter offers hosted provider ordering and fallback
  controls: <https://github.com/Portkey-ai/gateway>,
  <https://docs.litellm.ai/>, and
  <https://openrouter.ai/docs/features/provider-routing>
- Langfuse gives open-source LLM observability, traces, prompt management, and
  eval hooks, including OpenTelemetry integration:
  <https://github.com/langfuse/langfuse>

## Standardization Strategy

Use a three-layer package strategy:

```text
1. Baltor artifact contracts
   stable JSON schemas for pages, components, chunks, claims, facts, routes,
   source snapshots, evidence packets, and serving packages

2. Baltor worker adapters
   small wrappers that call Docling, PyMuPDF, Surya, Scrapy, LiteLLM, Temporal,
   Langfuse, etc. and normalize outputs into Baltor contracts

3. External packages/images
   version-pinned dependencies isolated by image class: CPU, OCR/doc, browser,
   GPU, audit, research, orchestrator
```

This avoids lock-in and keeps dependency weight out of the base worker image.
For example, the CPU worker should not carry browser dependencies, OCR models,
or GPU runtimes. The OCR/doc worker should not know adoption policy. The model
gateway should not know whether a fact is safe to serve. Each module does one
job and emits a typed artifact.

Recommended implementation pattern:

| Need | Package shape | Reason |
|---|---|---|
| Shared contracts | internal Python package, later private/public PyPI | Every worker imports the same envelope, lifecycle, and schema helpers. |
| Worker adapters | repo modules first, split into packages when stable | Avoid premature packaging while APIs are still changing. |
| Heavy document tools | separate container images | Keep CPU workers small and reduce local setup pain. |
| Browser/research | isolated image or managed browser service | Stronger sandboxing and egress control. |
| Model gateway | thin internal resolver plus optional LiteLLM/Portkey/OpenRouter backend | Baltor keeps privacy/budget policy; gateway handles provider mechanics. |
| Evals/distillation | dataset artifacts plus eval runners | Frontier outputs become replay fixtures and fine-tuning candidates. |

Adoption rule for every external project:

```text
wrap, normalize, test, and trace
```

Do not let an external package's native object model leak into fact records,
serving packages, queue payloads, or customer-visible exports. Store the native
metadata in `raw_backend_metadata` only when useful for debugging.

## Source Trust And Security Research

External-source workers are exposed to untrusted content. The security model
should assume web pages, PDFs, emails, and retrieved snippets can contain
malicious instructions or spam.

Controls:

- separate instructions from source text in every prompt;
- never let source text select tools or permissions;
- enforce domain allowlists, egress limits, and source-scope policies;
- capture source URL, retrieval timestamp, content hash, and evidence span;
- require source trust scoring before adoption;
- retain original customer-source claim and new verified fact in provenance;
- prefer official or primary sources for adoption;
- require two independent sources unless policy allows an authoritative source;
- archive important sources after verification;
- keep unresolved states instead of guessing.

Relevant docs:

- OWASP LLM Prompt Injection Prevention Cheat Sheet: <https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html>
- OWASP Prompt Injection overview: <https://owasp.org/www-community/attacks/PromptInjection>
- NIST AI RMF: <https://www.nist.gov/itl/ai-risk-management-framework>
- OpenTelemetry docs: <https://opentelemetry.io/docs/>
- Internet Archive Save Page Now overview: <https://wiki.archiveteam.org/index.php/Internet_Archive/Save_Page_Now>

## Reliability Practices

Workers should be designed for at-least-once execution.

Required practices:

- idempotency key per task and artifact;
- content hashes for inputs and outputs;
- leases and heartbeats for long-running tasks;
- explicit max attempts plus specific terminal or hold states:
  `approval_required`, `budget_blocked`, and `failed_permanently`;
- structured failure reasons;
- queue dedupe key by tenant, task type, fact id, source id, and URL;
- retry with backoff;
- no adoption from failed, partial, or malformed outputs;
- deterministic replay fixtures for model-discovered procedures;
- OpenTelemetry traces, metrics, and logs around every task.

For source refresh, state history is product-critical:

```text
candidate_detected
-> one_source_found
-> needs_second_source
-> two_sources_found
-> archived
-> ready_for_adoption
-> served_current
```

If a fact is found with one source today, the system should schedule a higher
priority second-source search later instead of discarding the finding.

## Model Hierarchy

Use models as a costed escalation ladder:

| Stage | Tooling | Role |
|---|---|---|
| deterministic | regex, parsers, metadata, rules | first pass, cheap and reproducible |
| local small model | spaCy/GLiNER/rerankers/Gemma-class models | entity, classification, summaries, rerank |
| local GPU/open model | vLLM/Ollama workers | higher-volume private processing |
| hosted frontier model | API model | hard reconciliation, summaries, source comparison |
| Hermes/OpenClaw | open-ended and adversarial workers | unresolved cases and procedure discovery |
| compiled rule | deterministic worker/template | future cheap replay |

The key product loop is:

```text
expensive non-deterministic discovery
  -> evidence packet
  -> deterministic resolver/template
  -> replay fixture
  -> cheaper future worker run
```

## Product Implications

The demo and GTM language should emphasize:

- automated verification and refresh;
- reconciled and traceable context;
- source lineage and adoption states;
- rare manual exceptions;
- serving packages for text, RAG, graph, and audit;
- local-first execution with cloud-scale worker pools.

Avoid positioning Baltor as another generic agent builder. The stronger claim:

```text
Baltor keeps enterprise agent context verified, current, traceable, and ready to serve.
```

## Next Implementation Recommendations

1. Add a managed-service deployment matrix for AWS, GCP, Azure, and local.
2. Add OpenTelemetry task spans around `process_one`.
3. Add optional Docling/Unstructured/GLiNER workers behind dependency groups,
   not as hard base dependencies.

Implemented follow-up:

- `schemas/worker-manifest.schema.json` now defines the portable worker
  manifest.
- `scripts/context_workers/router.py` now maps task envelopes to registered
  workers, lanes, image classes, output contracts, and reason codes.
- `scripts/context_workers/requeue.py` now scans active fact/source records and
  emits deduped follow-up tasks for one-source, stale, reconciliation,
  source-trust, and archive-capture cases.
- `scripts/context_workers/adversarial_fixtures.py` now covers prompt injection,
  duplicate follow-ups, scanner dedupe, source-trust blocking, archive routing,
  and single-source follow-up policy.
