---
name: chat-with-pdf-citations
description: Given an uploaded PDF and a user question, retrieve the most relevant
  passages via hybrid retrieval + rerank, then produce a cited answer.
when_to_use: 'Pipeline kind: qa_attachment.'
---

# Chat with PDF (with citations)

The canonical "upload a PDF, ask questions, get cited answers" pipeline
used by vercel/ai-chatbot, lobe-chat, codertom/chat-with-pdf, etc. Full
layered chain:
  pdf-to-text →
  recursive chunker →
  embedder (local or OpenAI) →
  hybrid retrieval policy (BM25 + dense + RRF) →
  cross-encoder reranker →
  persona (research analyst) →
  grep (PII guard on retrieved chunks before model sees them) →
  harness (text-safety-review) →
  citation-coverage verifier.

## Task

Given an uploaded PDF and a user question, retrieve the most relevant
passages via hybrid retrieval + rerank, then produce a cited answer.

## Steps

1. **pdf_to_text** — `processor` → `processor/pdf-to-text`
2. **chunk** — `processor` → `processor/recursive-character-chunker`
3. **embed** — `processor` → `processor/embedder-minilm`
4. **embed_query** — `processor` → `processor/embedder-minilm`
5. **retrieve** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
6. **rerank** — `processor` → `processor/cross-encoder-reranker`
7. **guard_chunks** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
8. **redact_chunks_pii** — `rule_pack` → `rule-pack/privacy-pii-text-en`
9. **answer** — `harness` → `harness/text-safety-review`
10. **verify_citation_coverage** — `processor` → `processor/citation-coverage`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **knowledge_packs**: —
- **rule_packs**: `rule-pack/hybrid-retrieval-policy`, `rule-pack/privacy-pii-text-en`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/chat-with-pdf-citations` v0.1.0
- License: `MIT`
- Industry: cross_industry
- Full source manifest: see `references/manifest.yaml`
