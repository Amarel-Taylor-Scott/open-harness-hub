# Library - organized by capability

A capability-grouped index of every artifact in the catalog. Use this
as a "what's in the toolbox" overview before you compose a pipeline.

> Live counts (auto-updated by `scripts/build_catalog_index.py`):
> see [`docs/catalog/index.json`](../catalog/index.json) for the full
> machine-readable index.

## 1. Prompt engineering

### Personas (10)
`persona/research-analyst` · `persona/fact-checker` · `persona/clinical-reasoner` · `persona/aml-analyst` · `persona/cinematic-product-photographer` · `persona/code-consultant` · `persona/support-agent` · `persona/translator-improver` · `persona/math-tutor` · `persona/linux-terminal`

### Persona libraries (knowledge packs)
`knowledge-pack/common-personas-library` - 15 reusable role frames (research analyst, code reviewer, support agent, tech writer, translator, tutor, summarizer, fact-checker, plain-language rewriter, scientist, interviewer, moderator, skeptical critic, negotiator, clinical interviewer)

### Reasoning framework + output directives
`processor/reasoning-framework-selector` - picks CoT / Self-Consistency / ReAct / ToT / SoT / PoT / none
`processor/inject-output-schema` - renders JSON Schema into the prompt (with constrained-grammar markers)
`processor/inject-datetime-locale` - replaces `{{today}}` / `{{user_timezone}}` / `{{user_locale}}` / `{{user_currency}}` with real values

### Context assembly
`processor/context-window-packer` - LITM-aware reorganization with chunk delimiters
`processor/llmlingua-context-compressor` - selective-token compression

## 2. RAG (retrieval-augmented generation)

### Retrieval policies (rule packs)
`rule-pack/hybrid-retrieval-policy` - BM25 + dense + RRF + reranker + citation-graph + freshness window + min-score floor

### Embedding adapters
`adapter/openai-embeddings` - text-embedding-3-small/large
`adapter/bge-embeddings-local` - BAAI BGE small/large (local)

### Embedding & reranking processors
`processor/embedder-minilm` - local sentence-transformers (384-dim)
`processor/cross-encoder-reranker` - BGE / Cohere rerank

### Chunking
`processor/recursive-character-chunker` - LangChain-style recursive splitter

### Query optimization
`processor/sub-question-decomposer` - break compound questions into atomic sub-questions
`processor/hyde-query-expander` - Hypothetical Document Embeddings
`processor/intent-dispatcher` - classify intent + route to specialist sub-pipeline

### Knowledge packs (15)
**Reference vocabularies**: `common-abbreviations` · `iso-currency-codes` · `iso-country-codes` · `spdx-licenses-summary`
**Style / physics**: `style-references-cinematic` · `lens-physics-primers`
**Security**: `owasp-top-10-llm` · `mitre-attack-sample`
**Healthcare**: `icd10-sample` · `clinical-guidelines-sample` · `drug-interactions-sample`
**Finance**: `fatf-typologies-sample` · `sanctions-list-shape` · `aml-red-flags-extended`
**Personas**: `common-personas-library`

## 3. GREP / pattern detection

### Privacy
`rule-pack/privacy-pii-text-en` - general PII (email, phone, SSN, IBAN, etc.)
`rule-pack/phi-hipaa-en` - HIPAA Safe Harbor 18 identifiers
`rule-pack/financial-pii-en` - IBAN, SWIFT, PAN+Luhn, SSN/EIN, account#

### Secret scanning
`rule-pack/grep-cloud-secrets` - AWS, GCP, Azure, DO, Cloudflare, OCI, Heroku
`rule-pack/grep-ai-vendor-keys` - Anthropic, OpenAI, HF, Cohere, Replicate, Groq, Together, fal, Perplexity, Voyage, NVIDIA, Mistral
`rule-pack/grep-vcs-platform-pats` - GitHub, GitLab, Atlassian, Bitbucket, npm, pypi
`rule-pack/grep-private-key-blocks` - RSA, EC, OpenSSH, PGP, Age, encrypted PKCS#8

### Prompt-injection / jailbreak
`rule-pack/grep-prompt-injection-heuristics` - garak-aligned (ignore-previous, DAN, ANSI escape, invisible Unicode, grandma)

### Domain-specific
`rule-pack/grep-prohibited-terms` - image-gen guard rails (celebs, trademarks, NSFW)
`rule-pack/grep-output-safety-image` - post-gen image safety
`rule-pack/clinical-red-flags` - ACS, stroke, SAH, anaphylaxis, OB emergency, psych crisis
`rule-pack/aml-typologies-fatf` - structuring, layering, TBML, geographic risk

## 4. Search / online sources

### Search tools
`tool/web-search` - generic web search (Brave / Serper / DDG / SearXNG)

### Search policies
`rule-pack/web-search-allowlist-default` - allowlist of trusted sources (gov, IGOs, academic, major news) + PII sanitization + freshness windows
`rule-pack/sanctions-screening` - OFAC SDN / UN / EU / HMT / institutional PEP

### Verification
`processor/official-sources-checker` - verify candidates against authoritative-source allowlist; tier (primary / secondary / tertiary); jurisdiction match; freshness; cross-reference

## 5. Tools (function-call definitions)

### Generic
`tool/web-search` · `tool/txt2img-sdxl` · `tool/lookup-icd10` · `tool/sanctions-check` · `tool/transaction-graph-query`

### MCP servers (planned via `dist/mcp/server.py`)
The MCP server emitter exposes every `tool/*` plus model-safe `processor/*` as MCP tools. Connect via Claude Desktop / Cursor / cline / any MCP host.

## 6. Models (adapters)

### Generative
`adapter/ollama-default` - local Llama / Gemma / Mistral via Ollama
`adapter/sdxl-local` - local SDXL via Diffusers

### Embedding
`adapter/openai-embeddings` · `adapter/bge-embeddings-local`

## 7. Verification & evaluation

### Verification processors
`processor/citation-coverage` - every claim has a citation
`processor/hallucination-scorer` - SelfCheckGPT-style per-sentence confidence
`processor/json-schema-repair` - JSON parse + repair + validate
`processor/self-refine-critique` - single critique-and-revise pair
`processor/iterative-revise-loop` - generic verifier-driven loop (max_iter, cost ceiling, convergence policy)

### Judges (LLM-as-judge)
`processor/llm-judge` - generic rubric-driven LLM judge (Anthropic / OpenAI / local)

### Rubrics
`rubric/research-entity-v1` - 6 dimensions (groundedness, source quality, coverage, calibration, neutrality, privacy safety)
`rubric/verification-v1` - 4 dimensions (verdict, citation quality, calibration, abstention)
`rubric/brand-safe-image-v1` - 5 dimensions for image gen
`rubric/clinical-grounded-response-v1` - 6 dimensions for clinical outputs
`rubric/aml-investigation-v1` - 6 dimensions including sanctions-first ordering

## 8. Audit & delivery

### Audit
`processor/audit-trace-emitter` - emit per-step trace (sha256, model version, applied layers, ms, cost) to a configured sink
`processor/cost-meter` - per-call USD accounting via adapter pricing card

### Escalation / delivery
`processor/escalate-human-review` - route to human queue (Linear / Jira / Slack / webhook)
`processor/intent-dispatcher` - classify + route to one of N downstream

### Format conversion
`processor/pdf-to-text` - OCR + extractable-layer PDF → text
`processor/audio-to-text-whisper` - Whisper-family STT

### Memory / state
`processor/memory-conversational-store` - read / append / summarize per-(user, session) memory
`processor/recursive-character-chunker` - chunk for indexing

### Policy gates
`processor/cost-ceiling-gate` - fail-fast if predicted cost > budget
`processor/prompt-injection-detector` - two-tier (regex + small-model classifier) injection detection

## 9. Harnesses (the integrating layer)

| Harness | Wraps |
|---|---|
| `harness/text-safety-review` | General persona + GREP + RAG + tools + verify |
| `harness/redact-pii-text` | Deterministic gate (no model call) |
| `harness/clinical-decision-support` | Healthcare-specific composition |
| `harness/aml-investigation` | Finance-specific composition |

## 10. Pipelines (DAGs of the above)

| Pipeline | Kind |
|---|---|
| `pipeline/research-entity` | `research_entity` |
| `pipeline/verify-claim-against-corpus` | `verify_data` |
| `pipeline/brand-safe-product-photo` | `generate_image` |
| `pipeline/differential-diagnosis` | `classify` (clinical) |
| `pipeline/suspicious-transaction-review` | `classify` (financial) |
| `pipeline/code-review-with-risk-score` | `review_code` |
| `pipeline/deep-research-with-citations` | `research_web` |
| `pipeline/chat-with-pdf-citations` | `qa_attachment` |
| `pipeline/plan-execute-critic-loop` | `plan_and_execute` |
| `pipeline/multi-doc-qa-subquestion` | `qa_documents` |
| `pipeline/email-triage-and-draft` | `triage_email` |
| `pipeline/everything-research-pipeline` | `research_entity` (kitchen-sink, 22 passes) |

## Quick-reference: which artifacts you'd combine for…

| Goal | Combine |
|---|---|
| Chat-with-PDF | `processor/pdf-to-text` + `recursive-character-chunker` + `embedder-minilm` + `hybrid-retrieval-policy` + `cross-encoder-reranker` + `text-safety-review` + `citation-coverage` |
| Code review | 4× `grep-secrets-*` packs + `owasp-top-10-llm` + `mitre-attack-sample` + `code-consultant` + `text-safety-review` + `citation-coverage` |
| Deep research | `redact-pii-text` + `common-abbreviations` + `web-search-allowlist-default` + `web-search` + `official-sources-checker` + `text-safety-review` + `citation-coverage` |
| Customer support | `redact-pii-text` + `grep-prompt-injection-heuristics` + `intent-dispatcher` + `support-agent` + `text-safety-review` + `audit-trace-emitter` + `escalate-human-review` |
| Clinical DSS | `phi-hipaa-en` + `redact-pii-text` + `clinical-red-flags` + `clinical-guidelines-sample` + `lookup-icd10` + `clinical-reasoner` + `clinical-decision-support` |
| AML review | `financial-pii-en` + `sanctions-screening` + `sanctions-check` + `transaction-graph-query` + `fatf-typologies-sample` + `aml-red-flags-extended` + `aml-analyst` + `aml-investigation` |
| Image gen | `grep-prohibited-terms` + `style-references-cinematic` + `lens-physics-primers` + `cinematic-product-photographer` + `text-safety-review` + `txt2img-sdxl` + `grep-output-safety-image` |
| Eval / red-team | `grep-prompt-injection-heuristics` + `garak-aligned-probes` (planned) + `llm-judge` + `hallucination-scorer` + `citation-coverage` + `audit-trace-emitter` |

## Adding more - gaps to fill in next batches

- More GREP secret packs (payment SaaS, JWT, crypto wallets, intl ID numbers)
- More personas (interviewer, plain-language rewriter - partial coverage in `common-personas-library`)
- More retrieval processors (self-query filter, multi-vector retrieval, parent-document retrieval)
- More judges (Ragas faithfulness, garak-promptinject, DeepEval-hallucination as `rubric/*`)
- More MCP tool wrappers (filesystem, github, postgres, brave-search, playwright)
- Domain-specific knowledge packs (GDPR articles, contract clause taxonomy, code anti-patterns)
