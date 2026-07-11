# Object factory worker fleet

*pipeline* · `pipeline/object-factory-worker-fleet` · v0.1.0 · experimental

Routes source material through dedicated workers for markdown conversion, sensitive-data screening, LLM polishing, verification, labeling, dedupe, indexing, cost metering, and publish review.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | extraction, summarization, verification, anonymization, routing, governance |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | volatile |
| license | MIT |



## Task

Convert governed source material into privacy-screened, polished, verified, labeled, deduplicated, and reviewable candidate primitives using dedicated workers and provider-neutral model routing.

**pipeline_kind:** `research_web.object_factory_worker_fleet`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_worker_patterns` | knowledge_pack | `knowledge-pack/object-factory-worker-patterns` | - |
| 2 | `route_conversion_job` | tool | `tool/object-factory-job-router` | - |
| 3 | `convert_page_to_markdown` | tool | `tool/page-to-markdown-converter` | - |
| 4 | `extract_digest_candidates` | tool | `tool/normalized-object-extractor` | - |
| 5 | `screen_sensitive_data` | tool | `tool/sensitive-data-object-gate` | - |
| 6 | `route_polish_model` | tool | `tool/model-capability-router` | - |
| 7 | `polish_and_verify` | tool | `tool/llm-polish-verify-worker` | - |
| 8 | `assign_labels_dimensions` | tool | `tool/hierarchical-label-dimensioner` | - |
| 9 | `dedupe_candidates` | tool | `tool/fuzzy-dedupe-clusterer` | - |
| 10 | `emit_index_records` | tool | `tool/index-record-emitter` | - |
| 11 | `audit` | processor | `processor/audit-trace-emitter` | - |

