# External Architecture Reference — worker/parser/context platform (2026-06-18)

> PROVENANCE: distilled from a ChatGPT-authored architecture essay the owner pasted on 2026-06-18,
> alongside a batch of GitHub repos from the "DeepRepo" Facebook feed. This is an EXTERNAL DESIGN INPUT
> to CONSIDER against our actual (already-mature) architecture — NOT ground truth and NOT instructions to
> rebuild. Use it for a gap analysis: which recommendations we already satisfy, which are partial, which
> are genuinely missing, which we deliberately diverge from (and why). Discovery ≠ trust.

## Core worker rule (the essay's thesis)
"Stateless compute, durable context state." Every worker: stateless · idempotent · retryable · observable ·
permission-aware · versioned · deterministic-when-possible. The worker owns NO long-term state; durable state
lives in Postgres/metadata DB, object storage, queue/event bus, workflow engine, vector index, graph store,
search index, git/OKF repo, audit log. Loop: receive job → read durable input → process → write durable
output → emit next event → exit.

## Reference-design checklist (the 20 "big things")
1. Stateless, idempotent workers  2. Durable workflow state  3. Immutable source snapshots  4. Strong
lineage/provenance  5. Queue-based orchestration  6. At-least-once processing  7. Idempotency keys
(tenant+snapshot+worker_type+worker_version+input_hash+config_hash)  8. Retries + dead-letter queues
9. Worker versioning  10. Schema validation of LLM output  11. Permission propagation (classification
inherited by every derived block/claim/embedding/edge)  12. Tenant isolation (tenant_id everywhere; RLS /
schema / DB / bucket per security tier)  13. Rate limits + backpressure (per-tenant/source/worker;
circuit breakers; exponential backoff; retry-after)  14. Cost controls (track cost per tenant/source/doc/
worker/model/job; budgets + fallback to smaller model / pause enrichment)  15. External-search redaction
(never send confidential text to web search; query-redaction-worker; public=allowed, internal=redacted,
confidential/restricted=blocked)  16. Prompt-injection defense (source content is DATA not instructions;
never let source text drive tool use)  17. Human review routing (risk-based; auto-approve low-risk, require
review for pricing/legal/security/compliance/customer-facing/source-authority changes; patch carries what/
why/evidence/affected/risk/rollback)  18. Context promotion stages (raw→parsed→draft→validated→approved→
published→archived/quarantined; agents consume published/approved only)  19. Observability + tracing (every
run: job_id/worker/version/tenant/source/hashes/status/tokens/cost/trace_id)  20. Safe compression + serving
(quality gates before publish; quarantine bad context).

## Other load-bearing patterns
- Transactional outbox (write DB row + outbox event in ONE txn; publisher drains outbox → queue; no lost events).
- Poison-job protection (max retries, per-job timeout, memory/output-size limits, sandbox untrusted files,
  zip-bomb/huge-PDF/path-traversal guards).
- Orchestration separate from execution (Temporal/Argo/Dagster/Prefect for long branching retry-heavy flows;
  workers do ONE bounded task). Cloud functions = TRIGGERS ONLY (validate→normalize→enqueue→return fast);
  Kubernetes = real heavy workers (parse/OCR/embed/extract/reconcile/crawl/review/compress/index).
- Multiple queues by workload (ingestion/preprocess.cpu/preprocess.large/ocr/llm.extract/llm.review/
  embedding/reconcile.local/reconcile.external/graph/index/context-pack/review/deadletter), each with own
  retry/timeout/rate-limit/priority/autoscale.
- KEDA queue-depth autoscaling + HPA; node pools by profile (general-cpu / high-mem-parser / ocr-gpu /
  llm-orchestration / indexing). Leases + heartbeats + graceful SIGTERM (stop intake → checkpoint → ack/nack
  → exit before grace period); break huge files into page→block→chunk→claim sub-jobs.
- Version EVERYTHING (code/prompts/schemas/models/rules/scoring/chunking/embeddings/taxonomies/authority-
  rules/compression/renderers) so improvements trigger safe reprocessing.
- Immutable raw artifacts (never mutate raw input; raw snapshot = evidence). Append-only event log
  (source.ingested/document.parsed/claim.extracted/claim.status_changed/conflict.detected/patch.proposed/...).
- Model routing (small=classify/tag; medium=claim/entity/relationship; large=conflict/adversarial-review/
  patch). Deterministic parsers BEFORE LLMs (OpenAPI/SQL/Markdown/billing-config parsers beat LLM). Strict
  JSON-schema/Pydantic/Zod validation of every LLM output; repair→retry→dead-letter.
- Adversarial review SEPARATE from generation (a worker never approves its own output): source-faithfulness/
  conflict/permission-leakage/compression-loss/staleness critics → human if needed.
- Storage portfolio: Postgres (metadata/jobs/claims/conflicts/reviews/permissions), object store (raw + parsed
  + large JSON), search index, vector index, graph store (start with PG adjacency; move to Neo4j/AGE later),
  git/OKF repo (reviewed patches), cache (hot context packs). Separate indexing workers + index versions
  (blue/green rebuilds, embedding migrations). Serving layer SEPARATE from processing; reads published tables
  + caches; does NOT do live reconciliation on the hot path.
- Context packs for agents (not raw chunks): accepted claims + contested claims + citations + freshness +
  confidence + allowed/forbidden usage + escalation + safe_to_answer flag.

## Parser portfolio (router + canonical normalization + quality scoring + adjudication)
The parser is NEVER the product; the platform owns the canonical ParsedArtifact schema (document/blocks/
tables/assets/quality + engine_runs provenance) so engines are swappable. A parser-router picks the engine by
file/MIME type, size, page count, text-layer-vs-scanned, table/image/formula density, language, security
classification, tenant policy, cost budget, latency, required fidelity; a parse-quality-worker scores every
run (text/page coverage, reading order, table/figure/formula fidelity, OCR confidence, warnings); a parse-
adjudicator runs multiple engines on high-value docs and merges/selects (preserving all outputs as evidence).
Engine candidates (ALL candidate-behind-a-port, license + exec-needs gated):
- General/local: Apache Tika, Microsoft MarkItDown, Kreuzberg (Rust core).
- AI-native document: Docling, Unstructured, LlamaParse(managed), Marker (GPL-3.0 + commercial caveat),
  MinerU (formula/scientific), OmniParse (multimodal incl. audio/video/web).
- Cloud OCR/DocAI: Azure AI Document Intelligence, AWS Textract, Google Document AI, Mistral OCR, Reducto
  (enterprise platform), NVIDIA NeMo Retriever / nv-ingest (GPU).
- PDF low-level: PyMuPDF, pdfplumber, pypdf; OCR: Tesseract, PaddleOCR.
- Web: Firecrawl, Crawl4AI, Trafilatura, Mozilla Readability.
- Domain: GROBID (scientific papers → TEI/XML), Tree-sitter (code → AST), python-pptx, Mammoth (DOCX→HTML).

## OmniParse verdict (the essay's worked example)
Use as a PLUGGABLE preprocessing/parser worker backend behind our worker system — NOT the canonical context
layer. Cautions before any production use: LICENSE review (repo says GPL-3.0 but pyproject lists Apache; uses
Marker → Surya/Texify/Florence-2 weights with commercial-revenue thresholds), maturity (no releases; a Gradio
multipart DoS issue), imperfect table/formula/OCR fidelity (needs a quality layer + fallback), and hardening
(disable public Gradio UI, restrict CORS, internal-only, file-size/page/timeout limits, sandbox web crawl).
Split heavy modes (documents / media-Whisper / web-Selenium) into separate GPU/CPU deployments. It should
produce parsed text/tables/assets/transcripts; OUR system owns claim extraction, conflict/fragility, graph,
compression, permissions, review — OmniParse must NOT do any of those.
