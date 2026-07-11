---
name: object-factory-worker-fleet
description: Convert governed source material into privacy-screened, polished, verified,
  labeled, deduplicated, and reviewable candidate primitives using dedicated workers
  and provider-neutral model routing.
when_to_use: 'Pipeline kind: research_web.object_factory_worker_fleet.'
---

# Object factory worker fleet

Routes source material through dedicated workers for markdown conversion, sensitive-data screening, LLM polishing, verification, labeling, dedupe, indexing, cost metering, and publish review.

## Task

Convert governed source material into privacy-screened, polished, verified, labeled, deduplicated, and reviewable candidate primitives using dedicated workers and provider-neutral model routing.

## Steps

1. **load_worker_patterns** — `knowledge_pack` → `knowledge-pack/object-factory-worker-patterns`
2. **route_conversion_job** — `tool` → `tool/object-factory-job-router`
3. **convert_page_to_markdown** — `tool` → `tool/page-to-markdown-converter`
4. **extract_digest_candidates** — `tool` → `tool/normalized-object-extractor`
5. **screen_sensitive_data** — `tool` → `tool/sensitive-data-object-gate`
6. **route_polish_model** — `tool` → `tool/model-capability-router`
7. **polish_and_verify** — `tool` → `tool/llm-polish-verify-worker`
8. **assign_labels_dimensions** — `tool` → `tool/hierarchical-label-dimensioner`
9. **dedupe_candidates** — `tool` → `tool/fuzzy-dedupe-clusterer`
10. **emit_index_records** — `tool` → `tool/index-record-emitter`
11. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: `knowledge-pack/object-factory-worker-patterns`, `knowledge-pack/hybrid-label-dimension-taxonomy`
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- deterministic `$.outputs.candidate_objects` is_truthy `True`
- deterministic `$.outputs.review_tickets` != `None`

## Provenance

- Hub component: `pipeline/object-factory-worker-fleet` v0.1.0
- License: `MIT`
- Industry: ai, software.devops, cross_industry
- Full source manifest: see `references/manifest.yaml`
