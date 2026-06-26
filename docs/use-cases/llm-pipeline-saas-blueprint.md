# LLM pipeline-as-a-service blueprint

This product direction turns OpenHubForAI into a SaaS that helps a user describe what they want to accomplish with LLMs inside their own hosting environment, then returns deployable pipeline options with cost, risk, runtime, and setup tradeoffs.

The core interaction:

> I need an LLM workflow for this business task, in my cloud or local environment. Show me cheap, balanced, and high-quality options, estimate cost, generate the pipeline, and give me the Terraform/runtime/MCP setup blueprint.

## What The SaaS Does

1. Intake: collect task, data sensitivity, hosting target, budget, latency target, compliance constraints, volume, and preferred providers.
2. Match: search the catalog for pipelines, harnesses, rule packs, tools, datasets, rubrics, processors, adapters, and patterns.
3. Price: query active model and infrastructure pricing through tool-backed adapters.
4. Enrich: optionally use browser research, browser-local LLM profiling, web search, and embedding search when the task needs fresher evidence or stronger retrieval.
5. Compose: produce several candidate architectures, usually `cheap`, `balanced`, and `quality_first`.
6. Estimate: calculate expected model calls, token use, storage, vector index, observability, and human-review costs.
7. Generate: emit pipeline manifests, runtime config, Terraform modules, environment-variable templates, and MCP setup plans.
8. Verify: attach benchmarks, rubrics, redaction tests, cost ceilings, and audit traces.
9. Hand off: either create a blueprint bundle for the user or, with permission, use MCP tools to set up the environment.

## Active Pricing Boundary

Live prices are volatile. They should not be copied into personas or stable knowledge packs.

Use this split:

| Layer | Pricing treatment |
|---|---|
| `tool/model-pricing-lookup` | Active provider/model price lookup |
| `tool/cloud-runtime-pricing-lookup` | Active compute, storage, network, and vector DB pricing |
| `processor/cost-ceiling-gate` | Runtime budget gate using the active price snapshot |
| `knowledge-pack/llm-pipeline-saas-blueprints` | Stable SaaS planning logic and cost dimensions |
| Generated pipeline manifests | Store the pricing snapshot id and assumptions, not a permanent price claim |

## Discovery And Runtime Tools

The SaaS can improve recommendations by selecting tools according to the user's trust boundary, latency target, and cost target:

| Tool | When to use it |
|---|---|
| `tool/web-search` | Fast fresh search over public pages or configured search providers |
| `tool/search-provider-router` | Select among model-native web search, search APIs, self-hosted search, private indexes, or custom functions |
| `tool/search-result-normalizer` | Convert provider-specific responses into a citation-ready common shape |
| `tool/cloud-search-function-adapter` | Call user-owned serverless search functions without hard-coding provider logic into the hub |
| `tool/containerized-search-runtime` | Run advanced search as a Docker/Kubernetes/ECS/Cloud Run worker for crawling, rendering, indexing, hybrid retrieval, or reranking |
| `tool/browser-research-session` | Rendered pages, dynamic docs, screenshots, or browser-only workflows |
| `tool/embedding-index-search` | Semantic search across catalog objects, policies, examples, and prior blueprints |
| `tool/browser-local-llm-runner` | Browser-side classification, extraction, embedding, or reranking when data should stay local |

Browser-local models can reduce hosted model calls, but they add device variability, model download size, and benchmark requirements. A SaaS answer should treat them as an option with measured feasibility, not as a default assumption.

Search should be provider-neutral. Current provider families include model-native web search, independent web indexes, search API wrappers, domain-specific APIs, self-hosted engines, enterprise/private indexes, user-owned cloud functions, and containerized search workers. The SaaS should store provider capability metadata separately from the generated pipeline so users can add or remove providers without rewriting their pipeline logic.

The common search contract should capture:

- `query`, locale, time range, domain allow/deny lists, freshness target, and safety constraints.
- privacy boundary, credential reference, expected cost, rate-limit policy, and fallback policy.
- normalized results with URL, title, snippet, fetched-content pointer, score, provider, retrieval timestamp, and citation metadata.
- audit fields for query issued, provider selected, result ids used, and reasons for excluding results.

## Containerized Search Runtime

Some search tools need more than a single HTTP call. Use a containerized runtime when the workflow needs:

- long-running crawl jobs, sitemap ingestion, robots-policy handling, or backoff queues.
- rendered browser fleets for JavaScript-heavy sites.
- private corpus indexing with local files, object stores, or enterprise document systems.
- hybrid retrieval that combines BM25, dense embeddings, reranking, deduplication, and citation extraction.
- GPU or high-memory rerankers, OCR, document parsing, or multimodal extraction.
- strict network controls such as VPC-only access, egress allowlists, proxies, or private DNS.

The generated bundle should include a `runtime.yaml` and either Docker Compose, Kubernetes, ECS, Cloud Run, Batch, or Nomad manifests. Cost estimates should include image build time, CPU and memory hours, GPU hours when used, index build time, storage, cache, queues, egress, observability, and scheduled refresh frequency.

## Generated Output Bundle

A complete SaaS answer should produce:

- `pipeline.yaml`: the executable pipeline manifest.
- `harness.yaml`: model targets, privacy boundaries, and trust boundary.
- `runtime.yaml`: adapter selection, token budgets, retries, caches, and observability.
- `terraform/`: optional cloud resources for queues, functions, secrets, vector DB, object storage, logs, and dashboards.
- `mcp.json`: MCP server plan for setup actions.
- `cost-estimate.json`: per-stage and per-1,000-item estimate.
- `eval/`: datasets, rubrics, and benchmark manifests.
- `runbook.md`: deployment, rollback, audit, and incident handling notes.

## Example: Cheap Social Moderation Pipeline

User request:

> I want to put together a cheap pipeline to flag social media content for review if it has a high likelihood of being related to overcharging of placements of OFWs.

Cheap plan:

- First pass: local GREP/rule packs.
- Retrieval: local BM25 plus optional embedding search over policy and red-flag knowledge packs.
- Model call: small local or low-cost classifier only after prefilter.
- Human review: only high-confidence or ambiguous cases.
- Cost control: reject paid model calls if per-1,000-item budget is exceeded.
- Output: reviewer packet with matched rule ids, evidence spans, confidence, and uncertainty notes.

Balanced plan:

- Adds dense retrieval, reranking, and LLM judge.
- Uses stronger adapter only for items that survive prefilter and rerank.
- Can use the search router, web search, custom cloud search functions, containerized search workers, or rendered browser research for current public guidance, provider docs, private policies, or regulator updates.
- Adds benchmark regression and appeal-review rubric.

Quality-first plan:

- Adds multi-model comparison, human quality review, and post-decision audit.
- Higher cost, lower false-negative risk, slower latency.

## Example: CSAM-Safe Moderation Pipeline

User request:

> I want to generate a pipeline to moderate social media content for potential CSAM.

Required behavior:

- Known-hash and restricted safety gates run before any model receives content.
- Suspected CSAM is routed to a restricted human/referral workflow.
- LLMs do not describe, classify, transform, or reason over suspected CSAM content.
- The audit trace records the safety gate, source ids, and referral workflow status without explicit content details.

## MCP Setup Mode

The SaaS can operate in two modes:

- Blueprint mode: generate files and instructions only.
- Assisted setup mode: use user-approved MCP tools to create repositories, secrets, cloud resources, vector indexes, dashboards, and CI checks.

Assisted setup must require explicit user approval before creating or modifying external resources. The generated MCP plan should list every intended action, target account/project, permissions required, estimated cost impact, and rollback path.

## Acceptance Checks

A SaaS-generated blueprint passes when it:

- Provides at least cheap, balanced, and quality-first options.
- Includes active pricing snapshot metadata and assumptions.
- Separates model cost, infrastructure cost, storage/vector cost, monitoring cost, and human-review cost.
- Produces deployable manifests or Terraform/runtime placeholders.
- Explains when model-native search, web search APIs, custom cloud search functions, containerized search workers, browser research, embedding search, or browser-local LLMs are selected or rejected.
- Adds evaluation components before suggesting production deployment.
- Preserves privacy and safety boundaries with explicit trust-boundary metadata.
- Uses MCP only for approved setup actions.
