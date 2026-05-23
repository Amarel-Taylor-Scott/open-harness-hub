---
name: knowledge-graph-from-corpus
description: Given a corpus, build a knowledge graph (entities + relationships + community
  summaries); answer queries via local / global / DRIFT search.
when_to_use: 'Pipeline kind: knowledge_graph.'
---

# GraphRAG: knowledge-graph from corpus + global/local query

Microsoft GraphRAG pattern. Extract entities + relationships from
documents into a graph; build community summaries via Leiden
clustering; query via local (ego-network), global (map-reduce over
communities), or DRIFT (primer + follow-up hybrid).

Verified by Open Harness Hub clone:
`microsoft/graphrag/packages/graphrag/graphrag/query/structured_search/`
contains `local_search/`, `global_search/`, `drift_search/` modules.

## Task

Given a corpus, build a knowledge graph (entities + relationships +
community summaries); answer queries via local / global / DRIFT search.

## Steps

1. **extract_entities_and_edges** — `harness` → `harness/text-safety-review`
2. **build_communities** — `processor` → `processor/community-summary-mapreduce` (when `$.inputs.search_mode in ['global', 'drift']`)
3. **local_search** — `harness` → `harness/text-safety-review` (when `$.inputs.search_mode == 'local'`)
4. **global_search** — `harness` → `harness/text-safety-review` (when `$.inputs.search_mode == 'global'`)
5. **drift_search** — `harness` → `harness/text-safety-review` (when `$.inputs.search_mode == 'drift'`)
6. **verify_citations** — `processor` → `processor/citation-coverage`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.75

## Provenance

- Hub artifact: `pipeline/knowledge-graph-from-corpus` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
