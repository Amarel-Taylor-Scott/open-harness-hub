---
name: large-model-faiss-rag
description: Given a multiple-choice question + a Wikipedia-class corpus, FAISS- retrieve
  top-k context chunks, prompt a 70B-class instruction-tuned model to pick the answer,
  ensemble across seeds for calibrated probs.
when_to_use: 'Pipeline kind: qa_multichoice_rag.'
---

# Large-model FAISS RAG (Platypus2-70b style)

Use a large (70B-class) instruction-tuned model with FAISS-indexed
Wikipedia retrieval. The "go big or go home" Kaggle pattern that
wins multi-choice-with-context competitions.

Verified by Open Harness Hub mining of simjeg's "Platypus2-70B with
Wikipedia RAG" (1248 votes) on kaggle-llm-science-exam.

## Task

Given a multiple-choice question + a Wikipedia-class corpus, FAISS-
retrieve top-k context chunks, prompt a 70B-class instruction-tuned
model to pick the answer, ensemble across seeds for calibrated probs.

## Steps

1. **retrieve** — `rule_pack` → `rule-pack/hybrid-retrieval-policy`
2. **rerank** — `processor` → `processor/cross-encoder-reranker`
3. **answer** — `harness` → `harness/text-safety-review`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/hybrid-retrieval-policy`

## Provenance

- Hub artifact: `pipeline/large-model-faiss-rag` v0.1.0
- License: `MIT`
- Industry: ai, scientific_research, education
- Full source manifest: see `references/manifest.yaml`
