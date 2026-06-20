# Baltor Document Intelligence Pipeline

The admin demo now uses the same shape locally and in containers:

```text
upload/connect
-> document tree normalization
-> deterministic text hygiene
-> chunks
-> deterministic NLP/signals
-> deterministic graph candidates
-> ambiguity/conflict/fragility trust checks
-> hierarchical LLM review plan
-> optional parser/NLP/RAG/GraphRAG/LLM adapters
-> serving/export package
```

The key rule is still: do not make the first expensive model call against raw
documents. Every run should first create stable, inspectable records for files,
folders, pages, components, chunks, entities, claims, graph edges, and evidence.

## Implemented Baseline

These workers run without optional document-intelligence packages:

| Worker | Purpose |
|---|---|
| `context.document_tree.normalize` | Normalizes inline text, direct files, ZIP files, and UI-provided file-set manifests into file/page/component records. |
| `context.text.normalize` | Normalizes Unicode, HTML entities, line endings, control characters, and whitespace. |
| `context.chunk` | Creates stable chunk IDs from normalized text. |
| `context.dedupe.fingerprint` | Computes deterministic fingerprints for exact and near-duplicate checks. |
| `context.keyword` | Extracts low-cost lexical keywords. |
| `context.nlp.signals` | Produces sentence, heading, action-term, lexical-density, and text-statistic signals. |
| `context.proper_noun.extract` | Extracts casing-based proper-noun candidates and mention edges. |
| `context.regex.extract` | Extracts dates, money, URLs, emails, percentages, and sections with evidence spans. |
| `context.pii.detect` | Detects common PII signals before external routing. |
| `context.entity.extract` | Extracts baseline entities from deterministic text features. |
| `context.claim.extract` | Extracts candidate claims for verification. |
| `context.document_graph.build` | Builds run/folder/file/page/component graph nodes and lineage edges. |
| `context.graph.extract` | Builds context graph candidates from chunks, entities, and claims. |
| `context.graph.metrics` | Computes component, isolate, and high-degree metrics. |
| `context.fragility.scan` | Finds facts likely to require verification or refresh. |
| `context.ambiguity.scan` | Flags unclear or ambiguous claims before serving. |
| `context.conflict.scan` | Finds contradiction candidates among related claims. |
| `context.fragile_fact.enrich` | Makes claim risk, provenance, freshness, and serving status explicit. |
| `llm.trust.plan` | Queues hierarchical LLM review, graph enrichment, summaries, conflict review, and audit tasks. |
| `context.refresh.plan` | Emits follow-up refresh/research jobs. |
| `context.pipeline.pass` | Runs the deterministic baseline. |
| `context.pipeline.experimental_adapters` | Runs the baseline plus every enabled optional adapter, reporting readiness and failures explicitly. |

The local admin server posts uploaded files to Redis as
`context.pipeline.experimental_adapters`. The container worker writes a JSONL
ledger and artifact bundle, publishes worker lifecycle events to the Redis
stream `ohh:context:events`, and enqueues deterministic follow-up tasks. The
admin monitor reads both the ledger and the Redis event stream.

## File Sets and ZIPs

`context.document_tree.normalize` is the deterministic first step for file sets:

- ZIP folder hierarchy is retained.
- Every file gets stable `file_id`, path, folder, extension, source, byte count,
  character count, readability, and hierarchy tags.
- Text-like files are split into pages and page components.
- Components are classified as `heading`, `paragraph`, `list`, `table_like`, or
  `code_like` with text previews.
- Binary or unsupported ZIP members are retained in the manifest instead of
  being dropped.

The baseline intentionally does not pretend to parse arbitrary binary PDFs,
Office files, scans, charts, or images. Those are delegated to optional parser
and OCR adapters below.

## Optional Parser and OCR Adapters

These are registered now and can be enabled per payload or by
`CONTEXT_ENABLED_ADAPTERS`. They return `missing_dependency` or
`not_configured` when the local image lacks the package, CLI, or service URL.

| Adapter | Worker | Needs |
|---|---|---|
| Docling | `document.parse.docling` | `docling` Python package |
| Unstructured | `document.parse.unstructured` | `unstructured[all-docs]` |
| Apache Tika | `document.parse.tika` | `tika` and Java/Tika runtime |
| MarkItDown | `document.parse.markitdown` | `markitdown` |
| Marker | `document.parse.marker` | `marker_single` CLI |
| MinerU | `document.parse.mineru` | `mineru` CLI |
| PaddleOCR | `document.ocr.paddle` | `paddleocr` CLI |
| GROBID | `document.parse.grobid` | `GROBID_URL` service |
| PyMuPDF | `document.parse.pymupdf` | `PyMuPDF` |
| pdfplumber | `document.parse.pdfplumber` | `pdfplumber` |

## Optional Deterministic/NLP Adapters

| Adapter | Worker | Output |
|---|---|---|
| spaCy | `nlp.spacy.extract` | tokens, sentences, POS/dependency fields, noun chunks, NER |
| textacy | `nlp.textacy.extract` | terms and subject-verb-object candidates |
| Stanza | `nlp.stanza.extract` | multilingual tokens, lemmas, dependencies, NER |
| GLiNER | `nlp.gliner.extract` | configurable/custom entity candidates |
| ftfy | `text.ftfy.repair` | repaired Unicode/text |
| lingua | `text.language.detect` | language candidates |
| RapidFuzz | `entity.rapidfuzz.alias` | alias-match candidates |
| datasketch | `dedupe.datasketch.minhash` | MinHash signatures |
| Presidio | `privacy.presidio.detect` | PII detections |
| scikit-learn | `nlp.sklearn.features` | TF-IDF style features |

## Optional Graph, Search, RAG, and LLM Adapters

The registry includes adapters for NetworkX, RDFLib, Open Semantic Search,
FSCrawler, Solr/Tika, LlamaIndex, Haystack, Neo4j GraphRAG, Microsoft GraphRAG,
RAGFlow, LightRAG, FalkorDB GraphRAG, Docling-Graph, Cognee, Graphiti,
CocoIndex, OpenSPG/KAG, LangChain graph transformer, LangExtract, OntoGPT,
structured-output runtimes, constrained decoding, DeepKE, ReLiK, RAPTOR, Dify,
Flowise, Langflow, AnythingLLM, and Diffbot-style NLP services.

Those adapters are intentionally thin local contracts. Some are Python package
workers, some are CLI adapters, and many are service adapters requiring a URL.
The value of registering all of them now is that the same upload/run can produce
a comparable adapter matrix while you decide which stack is worth installing in
the heavy local image or deploying as cloud services.

## OSINT Gate

`osint.openosint.catalog` is safe preflight. `osint.openosint.run` will not call
the CLI unless the task payload sets `authorized=true` or
`OSINT_AUTHORIZED=true` is present in the environment. Treat OSINT as authorized
passive research only.

## Local Verification

```bash
python3 -m py_compile scripts/context_workers/workers/document_tree.py
python3 -m scripts.context_workers.runner --validate-manifest
python3 scripts/baltor_admin_demo_server.py --port 9302
```

Then open:

```text
http://127.0.0.1:9302/admin-demo/
http://127.0.0.1:9302/admin-dashboard/monitor
```

With Docker/Redis running, upload a text file or ZIP from `/admin-demo/sources`.
The monitor should show `queue.enqueued`, worker lifecycle events, and a
completed run with document hierarchy counts and adapter summary counts.

The async path is:

```text
admin upload
-> Redis list ohh:context:jobs
-> context-worker --watch
-> TaskResult.enqueue follow-up jobs
-> Redis stream ohh:context:events
-> dist/context-workers-ledger.jsonl + artifact JSON
-> /admin-dashboard/monitor
```
