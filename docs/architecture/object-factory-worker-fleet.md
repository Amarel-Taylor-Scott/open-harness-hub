# Object Factory Worker Fleet

OpenHubForAI can start with local LLM-assisted object generation, but a million-object registry needs a dedicated worker fleet. The worker fleet turns source pages, documents, procedures, repositories, workflow files, and user-submitted materials into normalized candidate objects that can be reviewed, deduplicated, embedded, labeled, and published.

The key design point is separation of responsibilities. A worker should do one bounded transformation, emit reproducible records, and leave an audit trail. LLM calls are routed through a provider-neutral model wrapper so the same job can run on a local model, an OpenAI-compatible endpoint, a managed cloud API, or a tenant-provided key.

## Worker Classes

| Worker | Responsibility | Typical runtime |
|---|---|---|
| Source ingest | Fetch source metadata, license, content hash, publisher, archive URL, and trust tier | Render worker, Cloud Run job |
| Page to Markdown | Convert HTML/PDF/docs into clean Markdown with retained headings, tables, links, and citations | Container worker |
| Document digest | Extract tasks, checklists, questions, facts, constraints, examples, and failure modes | CPU worker with optional LLM |
| Sensitive data gate | Detect and redact PII, secrets, confidential data, unsafe content, and source-policy violations before model calls | Local or tenant-hosted worker |
| LLM polish | Rewrite rough extractions into schema-conformant candidate objects without inventing facts | Model-routed worker |
| Verification | Cross-check claims against cited source spans, archive snapshots, schema constraints, and deterministic validators | CPU plus cheap judge model |
| Label and dimension | Assign hierarchical labels, schema.org-style labels, tenant custom labels, and generated dimensions | Cheap model plus rules |
| Dedupe and index | Cluster near duplicates, link entities, and emit keyword/vector/graph/facet records | Postgres/pgvector worker |
| Cost meter | Estimate token, embedding, storage, browser, GPU, and human-review costs per job | API worker |
| Publish review | Route objects to curator, publisher, legal, safety, or domain review queues | API worker |

## Local Baseline Workers

The first runnable slice lives in `scripts/factory/object_factory_workers.py`. It is deliberately stdlib-only so Codex, CI, and a cheap Render worker can exercise the object-factory shape before managed queues, object storage, browser containers, or model endpoints are available.

```bash
python3 -m scripts.factory.object_factory_workers --self-test
python3 -m scripts.factory.object_factory_workers page-to-markdown --input page.html --output page.md
python3 -m scripts.factory.object_factory_workers extract --input page.md
python3 -m scripts.factory.object_factory_workers screen --input candidates.json --markdown page.md
python3 -m scripts.factory.object_factory_workers polish --input redacted-candidates.json --spans spans.json
```

The local baseline supports:

- HTML/text to Markdown conversion with headings, links, bullets, and source spans;
- simple bullet/heading extraction into normalized object candidates;
- deterministic PII/secret screening for emails, US SSNs, phone-like strings, private keys, and API-key-like tokens;
- deterministic polishing that trims text, preserves evidence-span ids, and rejects uncited candidates when policy requires citations.

It is not a substitute for the later hosted worker fleet. Browser-rendered pages, PDFs, OCR, repository mining, richer entity recognition, and LLM-backed verification should move into container workers behind the same tool contracts.

## Job Contract

Every worker job should carry:

- stable `job_id`, `tenant_id`, `source_record_id`, and parent job ids;
- input object references, not inline secrets or raw private documents;
- privacy and trust policy;
- model route constraints such as allowed providers, budget, latency, and local-only requirements;
- expected output schema;
- reproducibility metadata: worker image, git commit, model id, prompt version, pricing snapshot, and run timestamp;
- audit status, error class, retry count, and review ticket ids.

The job payload should be small. Raw snapshots and generated components belong in object storage. Postgres stores canonical metadata, state, indexes, and review records.

## LLM Endpoint Wrapper

The model layer should not assume Gemma, OpenAI, Anthropic, Gemini, Ollama, vLLM, or any one provider. Workers call `tool/model-capability-router` with:

- task type: extraction, summarization, polishing, judging, labeling, embedding, captioning, code, media;
- modality and context requirements;
- schema strictness;
- privacy constraints;
- latency and budget;
- available tenant keys and local endpoints;
- fallback policy.

Gemma-class local models remain useful for cheap labeling, reranking, JSON repair, and RAG-result polishing. Higher-capability cloud models can be reserved for high-value jobs, difficult extraction, benchmark generation, or disputed verification.

## Privacy and Safety Gates

Sensitive data screening should happen before external model calls. The default flow is:

```text
raw source pointer
-> source governance router
-> page/document conversion
-> sensitive data gate
-> redacted digest
-> model-routed extraction or polishing
-> verification against source spans
-> review ticket if uncertain
```

The catalog should not publish raw PII, secrets, private tenant material, copyrighted source dumps, or confidential business documents. Published objects should contain only the minimal transformed knowledge needed for reuse, plus source provenance and licensing metadata.

## Deployment Shape

Start with:

- Render web service for API, auth, search, and blueprint generation;
- Render background worker for low-volume source scans and object jobs;
- Postgres with pgvector for canonical records and first search;
- Redis or managed queue for job orchestration;
- S3-compatible object storage for snapshots, markdown, JSONL, and components.
- the local baseline worker module for no-key conversion, extraction, privacy screening, and deterministic polish checks.

Split when needed:

- Cloud Run or similar container workers for browser automation, PDF conversion, repository scanning, and source-specific tools;
- GPU workers for media generation, local model inference, and batch embeddings;
- warehouse jobs for offline ranking, cost traces, and search analytics.

For the horizontal multi-container version, see
[`containerized-object-factory-orchestration.md`](containerized-object-factory-orchestration.md).
That design splits discovery, spidering, repository/workflow mining,
normalization, enrichment, embedding, verification, promotion, warehouse export,
and prompt-prefix cache normalization into separate queue lanes.

## Operating Rules

- LLM polishing must not create uncited facts.
- Every published object must trace back to a source record, a curator decision, or a signed publisher submission.
- Every model call must record provider, model id, route reason, input redaction status, and cost estimate.
- Every failed or uncertain worker emits a review ticket instead of silently dropping the object.
- Deduplication happens before expensive model calls whenever practical.
- Tenant-private source material remains tenant-private unless explicitly published through a review flow.
