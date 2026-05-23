# Stream 7 — Kaggle competition + agentic-RAG pipeline shapes

> Note: live notebook pages blocked by sandbox; agent distilled from
> training knowledge + local `_reference/gemma4_comp` docs.

## Top 15 pipelines to add to `catalog/pipelines/<kind>/<slug>.yaml`

| # | pipeline_kind | slug | 1-line task |
|---|---|---|---|
| 1 | `review_code` | `code-review-with-risk-score` | Diff → review comments + numeric risk score with cited lint/policy rules. |
| 2 | `plan_and_execute` | `plan-execute-critic-loop` | Planner drafts steps, executor runs tools, critic re-plans on failure. |
| 3 | `qa_documents` | `multi-doc-qa-subquestion` | Decompose question, retrieve per sub-Q, aggregate cited answer. |
| 4 | `triage_email` | `email-triage-and-draft` | Classify intent, extract entities, retrieve context, draft reply. |
| 5 | `summarize_meeting` | `meeting-summary-actions-decisions` | Transcript → summary + action items + decisions with timestamps. |
| 6 | `route_support` | `support-intent-router` | Inbound message → specialist sub-agent via classified intent. |
| 7 | `summarize_long` | `long-doc-mapreduce-refine` | Chunk → per-chunk summary → reduce → critic-refine. |
| 8 | `research_web` | `deep-research-with-citations` | Query plan → parallel search → verify → synthesize with citations. |
| 9 | `rewrite_image_prompt` | `idea-to-structured-image-prompt` | Rough idea → structured prompt + safety check. |
| 10 | `mine_reviews` | `voice-of-customer-themes` | Cluster reviews → themes with sentiment, aspect, representative quotes. |
| 11 | `judge_pairwise` | `pairwise-response-preference` | Prompt + two responses → A/B/tie + calibrated confidence (LMSYS). |
| 12 | `qa_multichoice_rag` | `rag-multichoice-science-qa` | Retrieve+rerank corpus, answer MCQ with citations. |
| 13 | `classify_provenance` | `detect-ai-generated-text` | Classify AI-generated vs human + calibrated probability. |
| 14 | `extract_structured` | `text-to-pydantic-schema` | Text → typed JSON + validator + auto-retry on schema fail. |
| 15 | `qa_attachment` | `chat-with-pdf-citations` | Upload PDF → chunk+embed → chat with retrieval+citations. |

## Stretch (next batch)
- `compare_harness` (baseline vs harnessed vs FT vs FT+harness — gemma4_comp A-00 shape)
- `redact_then_egress` (PII-safe external call)
- `web_action_agent` (stagehand-style observe-act-verify)
- `debate_multi_agent` (autogen group-chat with judge)

## Pattern decomposition (each step → hub primitive)

For every pipeline above the agent provided a primitive map. Worth
quoting one example:

**Code-review-with-risk-score**:
- parse diff → `processor` (ast-parse)
- static-lint → `rule-pack/grep-*` (per language)
- retrieve repo conventions → `knowledge-pack`
- reviewer-persona harness → `persona/code-reviewer` (we have)
- risk-score rubric → `rubric`
- tools: git-diff-parser, run-tests → `tool`

## Kaggle competition shapes (specific)
- **LMSYS Chatbot Arena**: pairwise prefer-A/B/tie; LoRA-tuned classifier head on Gemma-2-9B / Llama-3-8B / DeBERTa-v3-large + length/ngram features + fold ensemble.
- **LLM-Detect-AI-Generated-Text**: TF-IDF (byte-pair) + char-ngram → SGD/MNB + LightGBM stack + DeBERTa residual.
- **LLM Science Exam**: Wikipedia chunking → BM25+dense+rerank → DeBERTa multi-choice head or few-shot small LLM.
- **LLM Prompt Recovery**: Mistral-7B / Gemma-7B LoRA fine-tune on synthetic (text, rewrite, prompt) triples + sentence-T5 mean-pool scoring.
- **WSDM Cup Multilingual Chatbot Arena**: LMSYS + language-ID + per-language LoRA adapters.
- **Eedi Mining Misconceptions**: dense retrieve top-K → Mistral/Gemma reranker → InfoNCE fine-tune.

## Agentic / RAG reference repos (canonical flows)
- `langchain-ai/langgraph` examples: plan-execute, ReAct, multi-agent supervisor, reflection, hierarchical teams, RAG-with-citations, code-act
- `microsoft/autogen`: group-chat, code+critic, retrieve-then-chat, teachable agent
- `openai/swarm` + cookbook: handoff routing, structured-output extraction
- `princeton-nlp/SWE-agent`: file-search → patch → compile-test loop
- `browserbase/stagehand`: page-action plan → observe → action → verify
- `run-llama/llama_index` examples: sub-question, multi-step, router, recursive retriever, citation-query
- `anthropics/anthropic-cookbook`: patterns/agents (orchestrator-workers, evaluator-optimizer, prompt-chaining, routing)
- `huggingface/cookbook`: agentic-RAG with smolagents, code-agent for data analysis
