# Pipeline Runtime v1 — versioned, swappable, durable, concurrent

The architectural correction: **CFPB ingestion is no longer "the architecture" — it is the first
registered pipeline** (`cfpb_structured_ingest@v1`). Pipelines are manifests, processors are swappable
plugins, runs are durable ledger records, artifacts are content-addressed. The **run ledger + artifacts
+ events are the source of truth; the dashboard is a projection.**

## Pieces (all on the existing durable_store — no 2nd bus, no greenfield)
- **`scripts/pipeline_runtime/specs.py`** — `PipelineSpec` / `PipelineStepSpec` (+ `discover()` over
  `pipelines/*.json`, `validate()`). A manifest declares versioned steps, each naming a
  `processor@version`, declared input/output artifact types, gates, and an idempotency-key template.
- **`scripts/pipeline_runtime/processors.py`** — `ProcessorRegistry` + adapters
  (`source.cfpb_fixture@v1`, `decompose.structured_atomic@v1`, `verify.governance@v1`,
  `package.context_pack@v1` and `@v2`, `parser.docling@v0` = experimental/unavailable seam). The runner
  resolves processors ONLY through the registry — swapping a processor is a manifest edit, not a code edit.
- **`scripts/pipeline_runtime/store.py`** — `PipelineLedger` (pipeline_runs / step_runs /
  content-addressed artifacts) composed onto `DurableStore` (same db + lock; backward-compatible).
- **`scripts/pipeline_runtime/runner.py`** — `run_pipeline()` executes a run; `enqueue_run()` +
  `execute_command()` are the durable-worker path.
- **`scripts/flywheel_worker.py`** — routes `command_type=pipeline.run` → the runtime (one worker drains
  any pipeline; N workers drain concurrently).
- **Routes:** `POST /api/dev/pipelines/run`, `GET /api/dev/pipelines`, `/pipelines/runs`,
  `/pipelines/runs/<id>`. Dashboard: `/dev` "Pipeline runtime" panel (projection from the ledger).
- **Manifests:** `pipelines/cfpb_structured_ingest.json`, `.v2.json`, `unstructured_pdf_docling.json`.

## Reprocessing: input version AND pipeline version (the requirement)
The idempotency key is `{tenant_id}:{source_id}:{document_version}:{pipeline_id}:{pipeline_version}`
where `document_version = hash(input)`. So a **changed document/page/line** (new input hash) OR a
**changed pipeline config** (new pipeline_version) ⇒ a **distinct run** = reprocessing; an identical
re-request is a no-op. Proven (`check_pipeline_runtime`): same input+version → duplicate; changed input
→ new run; changed version → new run; old run stays readable.

## Concurrency & scale (local now ⇄ broker/KEDA later)
Many pipelines/tenants/versions run at once: enqueue `pipeline.run` commands → N `flywheel_worker`
processes drain them with exactly-once (cross-process claim). Proven
(`check_pipeline_parallel_runs`): 2 tenants × v1/v2 = 4 runs, 2 worker processes, no double-process,
queue drained. Local SQLite queue → SQS/RabbitMQ/NATS; in-proc drain → KEDA-scaled `flywheel_worker`
Deployment; ledger SQLite → Postgres + S3 — **same enqueue/claim/ledger contract**.

## Data isolation (the customer requirement)
`PipelineSpec.isolation` = `shared` (default; tenant-partitioned lanes + tenant-scoped run records) or
`per_tenant_db` (a customer who must never share a table → its OWN durable db file). **PROVEN**
(`check_pipeline_tenant_isolation`, + live `/api/dev/pipelines/run`): `scripts/pipeline_runtime/
isolation.py` `db_for_tenant`/`resolve` route a `per_tenant_db` pipeline's runs + artifacts to
`<base>/tenants/<tenant>/durable.db` — two tenants land in PHYSICALLY separate files with **no
cross-tenant row at the raw SQLite level**; tenant ids are path-sanitized (no traversal). Maps to a
per-tenant Postgres database/schema in production; encryption-at-rest is a backend property of that
store (SQLCipher / Postgres TDE) — a backend swap, not a contract change.

## Unstructured documents (same runtime, different ParserProvider)
`unstructured_doc_tree@v1` runs **end-to-end offline**: `source.canned_document@v1` → `parser.document_tree@v1`
(normalizes a parser's output into the recursive ContextObject tree — pages/paragraphs/tables/figures/OCR
spans, coordinate-precise `ctx://…#` leaf handles, per-node lineage, low-confidence flags). The byte-level
parse is the **ParserProvider SEAM**: a `CannedParser` fixture stands in now; real **Docling / PyMuPDF /
Unstructured** slot behind the same contract (the `unstructured_pdf_docling@v0` variant stays experimental
+ clearly unavailable until vendored). Proven: `check_pipeline_unstructured` (tree on the generic runtime,
addressable leaves, low-conf flagged, content-addressed; real-Docling variant a clean unavailable seam).
So **structured (CFPB facts) and unstructured (PDF tree) decompose on the SAME runtime — only the
processor differs.**

## Decomposition grains = processor versions (your point)
A CFPB record is more than atomic facts — sentences, paragraphs, conclusions, sentiment/vectors. Each
is just a **new decomposer processor version** behind the same step contract:
`decompose.structured_atomic@v1` (now) → `decompose.multigrain@v2` (sentences+paragraphs+claims) →
`decompose.llm_atomic@v3` (grounded extraction). The runtime already supports running them side-by-side
and comparing outputs by content_hash — no architecture change.

## Proven vs deferred
- **Proven:** registry+manifests, generic run, versioned side-by-side, processor swap by manifest,
  multi-grain decomposer as a processor-version (`decompose.multigrain@v2`), reprocessing semantics,
  durable concurrent multi-tenant runs via worker processes, **per-step queue routing** (each step on
  its own lane `flywheel.commands.<step>`; completing a step enqueues the next dependent step; a run
  completes across queues, not inline — `check_pipeline_per_step_queue`; in a fleet each step queue = a
  KEDA-scaled worker Deployment), unstructured Docling SEAM (discoverable + experimental + clear
  unavailable error recorded), dashboard projection, routes.
- **Deferred (owner/infra — paid/cluster, no contract change):** real broker/KEDA/Postgres swap;
  `per_tenant_db` routing + encryption-at-rest; Docling/PyMuPDF/Unstructured/spaCy/LangExtract processor
  implementations; GraphRAG relationship layer (after atomic claims are clean).
