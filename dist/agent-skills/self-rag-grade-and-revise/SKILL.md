---
name: self-rag-grade-and-revise
description: 'Given a user question and a corpus, produce a cited answer with the
  Self-RAG reflection-token pattern: graded retrieval, graded answer support, bounded
  iteration on failure.'
when_to_use: 'Pipeline kind: rag_iterative.'
---

# Self-RAG: grade-and-revise (concrete implementation)

Concrete pipeline implementing `pattern/self-rag`. Retrieve → per-doc
relevance grader → rewrite-query loop on irrelevant retrieval →
generate with grounding → answer-support grader → iterate up to
max_iterations on low support.

Verified by Open Harness Hub deep mining: the LangGraph reference
implementation at `langchain-ai/langgraph/tutorials/rag/langgraph_self_rag/`
+ Akari Asai's canonical implementation at
`AkariAsai/self-rag/retrieval_lm/run_short_form.py` (both cloned).

## Task

Given a user question and a corpus, produce a cited answer with the
Self-RAG reflection-token pattern: graded retrieval, graded answer
support, bounded iteration on failure.

## Steps

1. **decide_retrieve** — `harness` → `harness/text-safety-review`
2. **retrieve** — `rule_pack` → `rule-pack/hybrid-retrieval-policy` (when `$.steps.decide_retrieve.output.text == 'YES'`)
3. **grade_documents** — `processor` → `processor/document-grader` (when `$.steps.decide_retrieve.output.text == 'YES'`)
4. **rewrite_query_if_irrelevant** — `harness` → `harness/text-safety-review` (when `$.steps.grade_documents.output.all_irrelevant`)
5. **generate** — `harness` → `harness/text-safety-review`
6. **grade_answer_support** — `processor` → `processor/hallucination-scorer`
7. **iterate_if_unsupported** — `processor` → `processor/iterative-revise-loop` (when `$.steps.grade_answer_support.output.overall_score < 0.6`)

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default
- **rule_packs**: `rule-pack/hybrid-retrieval-policy`, `rule-pack/grep-prompt-injection-heuristics`

## Success criteria

- rubric `rubric/research-entity-v1` threshold 0.8

## Provenance

- Hub artifact: `pipeline/self-rag-grade-and-revise` v0.1.0
- License: `MIT`
- Industry: ai, cross_industry
- Full source manifest: see `references/manifest.yaml`
