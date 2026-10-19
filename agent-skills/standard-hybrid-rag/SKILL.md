---
name: standard-hybrid-rag
description: Answer a question over a governed regulatory/knowledge corpus with per-claim
  citations, or abstain when the corpus does not support an answer.
when_to_use: 'Pipeline kind: serving.'
---

# Standard Hybrid RAG (Bundle A)

The recommended default retrieval pipeline from the retrieval/prompt taxonomy
(docs/concepts/retrieval-and-prompt-taxonomy.md, Bundle A). Answers a question over a
governed Knowledge Corpus with cited evidence — or abstains — by composing the swappable
retrieval-taxonomy components: a hybrid retrieve (BM25 + dense) fused by RRF, reranked by a
cross-encoder, de-duplicated and ordered by source precedence, edge-placed to beat
"lost in the middle", behind a prompt-injection screen and a cite-or-abstain system prompt,
with deterministic JSON recovery on the way out. Every step except the one model call and the
cross-encoder is deterministic and freezable, so it adds lift without adding recurring cost.

## Task

Answer a question over a governed regulatory/knowledge corpus with per-claim citations, or abstain when the corpus does not support an answer.

## Steps

1. **injection_screen** — `processor` → `processor/prompt-injection-screen`
2. **retrieve_bm25** — `processor` → `processor/bm25-keyword-retrieve`
3. **retrieve_dense** — `processor` → `processor/dense-vector-retrieve`
4. **fuse** — `processor` → `processor/rrf-fusion`
5. **rerank** — `processor` → `processor/cross-encoder-reranker`
6. **dedupe** — `processor` → `processor/simhash-dedupe`
7. **select** — `processor` → `processor/source-precedence-select`
8. **system_prompt** — `processor` → `processor/system-prompt-builder`
9. **place_context** — `processor` → `processor/context-placer-edge`
10. **answer** — `adapter` → `adapter/ollama-default`
11. **recover_json** — `processor` → `processor/json-repair-coerce`

## Defaults

- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/standard-hybrid-rag` v0.1.0
- License: `MIT`
- Industry: cross_industry, compliance
- Full source manifest: see `references/manifest.yaml`
