# Baltor Model And Document Pipeline

Baltor should run locally with cheap models and scale to hosted frontier models
without changing worker contracts.

## Document Processing Stack

Default local stages:

1. Source sync and versioning.
2. MIME detection and file routing.
3. Page splitting.
4. Page rendering and screenshot capture.
5. Page component extraction.
6. Paragraph, heading, table, image, figure, chart, and form extraction.
7. OCR/layout/table extraction when needed.
8. Hierarchical chunking and structural segmentation.
9. Page, component, chunk, and document summaries.
10. Keyword/entity/claim extraction.
11. Graph node and edge construction.
12. Freshness, weakness, evidence, and injection-risk scanning.
13. Reconciliation and source precedence.
14. Serving package generation.

The first rule is that documents are not just text blobs. A PDF, slide deck,
spreadsheet export, screenshot, scanned contract, or HTML page should become a
tree of durable artifacts before model calls do high-value reasoning:

```text
source
  -> source_version
  -> document
  -> page
  -> page_component
  -> paragraph | table | image | chart | form | margin_note | screenshot_region
  -> semantic_chunk
  -> claim | entity | edge | summary | evidence_requirement
```

Each artifact should carry:

- stable id;
- parent id;
- source version hash;
- page number or DOM path when available;
- bounding box or byte range when available;
- extraction method;
- confidence;
- model/tool route used;
- provenance pointer to the raw artifact.

Candidate tools to evaluate as pluggable workers:

- Docling for PDF/document conversion and layout-aware extraction.
- Unstructured for broad document parsing.
- PyMuPDF, pdfplumber, or Poppler for page splitting, page rendering, and
  bounding boxes.
- Tesseract, PaddleOCR, EasyOCR, or managed OCR for scanned files.
- LayoutParser, table extractors, and image/chart detectors for page components.
- spaCy and GLiNER for entity extraction.
- NetworkX for local graph construction.
- pgvector/Qdrant for vector retrieval.
- BM25/SQLite FTS/Postgres full text for lexical retrieval.
- Rerankers through local sentence-transformers or hosted APIs.

See `baltor-stateless-worker-standard.md` for the shared worker envelope used by
document workers and external research workers.

## Model Hierarchy

The model hierarchy should be a routing policy, not a single hardcoded model
chain. Workers request a capability and risk level; deployment config binds that
request to local Ollama, local vLLM/SGLang, a managed open-weight endpoint, or a
frontier API.

Use cheaper deterministic and local routes until the task needs broader
reasoning, stronger vision, longer context, or higher adoption confidence.

| Tier | Default role | Example bindings | Typical tasks |
|---|---|---|---|
| 0. Deterministic | Parse, split, hash, diff, route, validate, dedupe. | Python, Docling, Unstructured, PyMuPDF, Tesseract, spaCy, GLiNER, NetworkX. | Page splitting, page screenshots, OCR, paragraph extraction, table extraction, citation parsing, date/number detection, source diff. |
| 1. Efficient local | Fast first-pass understanding. | Gemma-class local model, small Qwen, small vision-language model, sentence-transformers. | Page captions, chunk summaries, labels, rough entities, claim candidates, simple source classification, injection-risk triage. |
| 2. Medium open-weight | Better structured extraction and cross-chunk synthesis. | Qwen 14B/32B-class, gpt-oss 20B-class, local or hosted vLLM/SGLang endpoint. | JSON extraction repair, entity resolution, edge proposals, document section summaries, evidence matching, table interpretation. |
| 3. Large open-weight | Long-context reasoning and hard reconciliation. | Qwen MoE/large, Kimi/K2-class, GLM/Z.ai-class, DeepSeek-class, gpt-oss 120B-class where available. | Whole-document synthesis, procedure discovery, disputed fact reconciliation, corporate hierarchy research, legal/statutory source analysis. |
| 4. Frontier/API | High-value unresolved cases and final adversarial checks. | OpenAI, Anthropic, Gemini, or other approved frontier APIs. | Adoption adjudication, adversarial review, hard web research, customer-approved high-stakes verification, generating training traces. |

Concrete names are deployment bindings. For example, `gemma4` can be the local
adapter name for Baltor's fast Gemma-class first-pass model, but the worker
contract should say `tier_1_efficient_local.summary` or
`tier_1_efficient_local.vision_caption`, not assume one public checkpoint name.

Current public references support the shape of this ladder:

- Google documents Gemma as a family with small deployable sizes and specialized
  variants, including Gemma 4 and variants such as MedGemma, EmbeddingGemma, and
  FunctionGemma.
- Qwen documents Qwen3 as dense and MoE open-weight models across small,
  medium, and large sizes, with local deployment paths through Ollama,
  llama.cpp, SGLang, vLLM, and other runtimes.
- OpenAI documents `gpt-oss` open-weight models in 20B and 120B sizes.
- Kimi K2 is a useful example of a large open-weight MoE model for agentic and
  tool-heavy reasoning workloads.

## Artifact Routing

| Artifact | First route | Escalate when | High-confidence output |
|---|---|---|
| Page | deterministic page splitter/render | scanned, rotated, image-heavy, or layout confidence is low | page image, text blocks, bounding boxes, OCR confidence |
| Page component | deterministic layout extractor | tables/charts/forms are ambiguous | component tree with coordinates and type |
| Image/figure | OCR + small vision model | image contains policy, chart, signature, map, or compliance evidence | caption, extracted text, bounding box, linked claims |
| Paragraph | deterministic text extractor | paragraph has malformed text or source-injection risk | normalized paragraph with source offsets |
| Semantic chunk | deterministic chunker + efficient local model | chunk crosses sections or contains many unresolved references | chunk summary, labels, source pointers |
| Chunk summary | tier 1 local | summary feeds adoption, policy, or legal reasoning | structured summary with cited source spans |
| Document summary | map-reduce: tier 1 chunks, tier 2/3 reduce | many sections disagree or source hierarchy matters | executive, procedural, and evidence summaries |
| Claim candidate | rules + tier 1 local | claim is numeric, dated, attributed, conditional, or jurisdictional | normalized claim with variables and evidence need |
| Entity | spaCy/GLiNER + tier 1 local | alias, hierarchy, or role ambiguity exists | canonical entity with aliases and source spans |
| Edge | deterministic relation rules + tier 2 | relation affects graph retrieval or adoption | typed edge with support spans |
| Reconciled fact | tier 2/3 verifier | only one source, weak source, changed fact, or internal mismatch | state transition proposal and evidence packet |
| Adopted fact | deterministic policy gate | policy allows frontier adjudication or human approval | current fact, history, provenance, serving modes |

## Model Lanes

The worker registry should expose model lanes that map to the hierarchy:

| Lane | Use | Examples |
|---|---|---|
| deterministic | Hash, diff, page split, chunk, regex dates/numbers, citation extraction, dedupe. | Python, SQLite/Postgres, NetworkX. |
| local_efficient | Summaries, entities, claim drafts, source classification, image captions. | Gemma-class local model, small Qwen/Llama variants, sentence-transformers. |
| open_weight_medium | Claim normalization, edge inference, evidence matching, reconciliation candidates. | Qwen 14B/32B-class, gpt-oss 20B-class, vLLM/SGLang endpoint. |
| open_weight_large | Long-context synthesis, procedure discovery, hard reconciliation. | Qwen large/MoE, Kimi/K2-class, GLM-class, DeepSeek-class, gpt-oss 120B-class. |
| frontier_controlled | Hard unresolved investigation, adversarial review, customer-approved final adjudication. | Approved OpenAI-compatible frontier endpoint. |
| hermes_discovery | Open-ended research that must emit reusable procedures. | Large open-weight or frontier route with artifact requirements. |
| openclaw_audit | Attack proposed resolutions, source trust, injection, scope, and edge cases. | Same model route, stricter prompts and evidence requirements. |

The lane names are product/runtime contracts. The concrete model name, endpoint,
quantization, GPU placement, and fallback chain belong in deployment config.

## Provider Neutrality

Use:

- `_repos/shared-backend-components/scripts/model_routes.py` for chat/model calls.
- `_repos/shared-backend-components/scripts/model_gateway.py` for policy-aware model route selection.
- `_repos/shared-backend-components/scripts/embeddings.py` for embeddings.

Every worker should receive the model lane as config, not hardcode a provider.

Local:

```bash
OH_LLM_BACKEND=http-openai
OH_LLM_BASE_URL=http://localhost:11434/v1
OH_LLM_MODEL=gemma4
```

Self-hosted OpenAI-compatible local endpoint:

```bash
OH_LLM_BACKEND=http-openai
OH_LLM_BASE_URL=http://localhost:8000/v1
OH_LLM_MODEL=qwen3-32b
```

Hosted/OpenAI-compatible:

```bash
OH_LLM_BACKEND=http-openai
OH_LLM_BASE_URL=https://provider.example/v1
OH_LLM_API_KEY=...
OH_LLM_MODEL=...
```

Fallback:

- If no model route is reachable, deterministic workers still run.
- If embeddings are not real, hash embeddings are allowed for staging only and
  must not be promoted.
- If local efficient models are overloaded, the route can either queue locally,
  spill to a hosted open-weight endpoint, or request approval for frontier use.
- If a task has a private-data policy, cloud spillover is disabled unless the
  tenant explicitly allows that provider and data class.

## Model Gateway And API-Key Routing

Baltor should have a thin model gateway policy layer above provider SDKs. The
gateway can use LiteLLM, Portkey, OpenRouter, LangChain middleware, or a direct
OpenAI-compatible client underneath, but workers should call the Baltor route
contract instead of importing provider-specific clients.

The route contract should support:

- multiple API keys per provider;
- local model endpoints and hosted model endpoints;
- free-credit, grant-credit, and paid-credit pools;
- retry on transient failures;
- fallback by status code, timeout, rate limit, provider outage, or budget;
- load balancing across equivalent keys when allowed;
- sticky routing when prompt/KV caching or provider-side cache hits matter;
- zero-data-retention or no-training requirements;
- tenant-specific provider allowlists;
- per-task maximum cost and maximum latency;
- full trace of attempted providers, selected provider, cost, latency, and
  fallback reason.

Recommended policy order:

```text
1. deterministic route if the task can be solved without a model
2. local model if privacy, cost, or latency policy prefers local execution
3. free/credit-backed hosted route if data policy allows it
4. lowest-cost compatible open-weight hosted route
5. stronger self-hosted or managed open-weight route
6. frontier route only when approved by policy, budget, and task risk
```

The gateway should not blindly choose "whatever works." It should choose the
first provider that satisfies:

```text
capability
  + data policy
  + cost ceiling
  + latency target
  + source/evidence risk
  + tenant allowlist
  + output contract support
```

If all compatible providers fail, the task should move to an explicit queue
state such as `budget_blocked`, `approval_required`, or `failed_permanently`
with the attempted route trace attached.

Gateway options worth evaluating:

| Option | Best fit | Caution |
|---|---|---|
| LiteLLM | Python-friendly OpenAI-compatible proxy, virtual keys, spend tracking, retries, and model fallbacks. | Keep Baltor's privacy and adoption policy outside LiteLLM config. |
| Portkey | Hosted or self-hosted AI gateway with fallbacks, load balancing, budget limits, circuit breakers, and request logs. | Gateway logs and key custody need enterprise review. |
| OpenRouter | Fast access to many hosted model providers with provider ordering, fallback controls, data-collection controls, and ZDR routing options. | Provider quality and data policy can vary by backend; route trace must be stored. |
| LangChain fallback middleware | Simple in-process fallback for chains/agents. | Useful for app code, but not enough as the central production policy layer. |
| Direct OpenAI-compatible client | Maximum control and minimal dependency. | More internal work for accounting, key rotation, and provider-specific errors. |

Useful current references:

- LiteLLM documents router retry/fallback logic, virtual keys, and spend
  controls: <https://docs.litellm.ai/>
- Portkey documents fallbacks, load balancing, retries, circuit breakers, and
  budget/rate limits: <https://portkey.ai/docs/product/ai-gateway>
- OpenRouter documents provider ordering, fallbacks, data-collection controls,
  and ZDR provider routing: <https://openrouter.ai/docs/features/provider-routing>
- LangChain documents model fallback middleware:
  <https://reference.langchain.com/python/langchain/agents/middleware/model_fallback>

The best practical setup is:

```text
worker
  -> Baltor model route contract
  -> policy resolver
  -> LiteLLM/Portkey/OpenRouter/direct adapter
  -> trace + cost + fallback ledger
  -> distillation/eval capture when allowed
```

This gives Baltor the convenience of multi-provider routing without outsourcing
trust, privacy, or fact-adoption decisions.

Current implementation hook:

```bash
python -m scripts.model_gateway
python -m scripts.context_workers.runner --resolve-model-route task.json
```

The route decision conforms to `_repos/shared-backend-components/schemas/model-route-record.schema.json` and
records selected route metadata, rejected candidates, fallback reasons, cost
estimate, privacy policy, and provider allowlist inputs.

## Distillation And Fine-Tuning Loop

Frontier calls should be treated as expensive teaching moments, not disposable
answers. When a frontier or large open-weight model resolves a case, the worker
must save a training-quality trace when policy allows it:

```text
input artifact set
  + retrieval/query plan
  + source snapshots
  + model route
  + structured output
  + verifier result
  + final state transition
  + replay fixture
```

Those traces feed four cheaper systems:

- deterministic extractors and resolver rules;
- prompt templates and query recipes for Hermes/OpenClaw;
- evaluation fixtures for regression testing;
- supervised fine-tuning or preference data for local open-weight models.

The rule is:

```text
pay once with a stronger model
  -> capture the procedure
  -> turn it into a cheaper repeatable worker, rule, eval, or fine-tune sample
```

Do not fine-tune directly on private customer data unless the tenant agreement,
data retention policy, and anonymization controls explicitly permit it. The safe
default is to store tenant-private traces only for that tenant's evals and
deterministic rule improvements.

## Adoption Policy

A model output is never enough to adopt a new fact by itself.

Adoption requires:

- source snapshots and hashes;
- provenance back to the uploaded or external source;
- source trust classification;
- required source count or authority exception;
- injection/spam check;
- state history transition;
- serving package update.

Typical states:

| State | Meaning | Next action |
|---|---|---|
| `candidate_extracted` | Found in uploaded or synced context. | Normalize and classify evidence need. |
| `one_source_found` | One plausible supporting source exists. | Queue second-source research or authority exception review. |
| `two_sources_found` | Two independent sources support the fact. | Reconcile and prepare adoption proposal. |
| `official_source_found` | Authoritative source supports the fact. | Archive source, run injection check, apply policy gate. |
| `reconciled` | New fact has been matched against prior customer context and source precedence. | Build serving artifacts. |
| `adopted` | Fact is eligible for current context serving. | Monitor for drift. |
| `needs_manual_confirmation` | Automation cannot safely resolve it. | Rare curator/customer confirmation. |

This keeps manual confirmation rare while preserving an audit trail for every
new or changed fact.

## Serving Modes

Produce four outputs:

- Text context pack.
- RAG records.
- Graph/hybrid retrieval package.
- Audit/provenance packet.

Each fact should support:

- `current_only`
- `current_with_sources`
- `current_with_history`
- `audit_packet`
- `diff_since_last_sync`
