# LLM Trust Layer

The trust layer starts after deterministic parsing, chunking, entity extraction,
claim extraction, graph construction, fragility scanning, and node-research
planning. Its job is to let models improve the graph and summaries without
letting them silently promote risky context.

```text
documents
-> deterministic blocks/chunks/entities/claims/graphs
-> fragile facts, ambiguity, conflict candidates
-> node research tasks
-> hierarchical LLM review tasks
-> proposed nodes/edges/summaries/ratings
-> evidence gate and review before promotion
```

## First-Class Claims

Claims are separate records from entities and graph nodes. A claim record should
carry:

- `claim_id`
- normalized claim text
- subject
- source chunk
- polarity
- evidence span
- retrieval/source timestamps when available
- independent and authoritative source counts
- conflict status
- freshness/volatility signals
- context-serving state

This prevents a sentence from becoming a graph fact just because it appeared in
source text or an LLM output.

## Implemented Workers

| Worker | Purpose |
|---|---|
| `context.ambiguity.scan` | Flags pronouns, vague quantifiers, uncertain language, and time-relative terms. |
| `context.conflict.scan` | Finds deterministic contradiction candidates among related positive/negative claims. |
| `context.fragile_fact.enrich` | Produces claim risk records with freshness, provenance, verification, and context-serving metadata. |
| `llm.trust.plan` | Emits queueable hierarchical LLM review tasks. |
| `llm.claim.review` | Calls the selected local route for claim clarity, evidence-strength, freshness, and safe-context review. |
| `llm.graph.enrich` | Calls the selected local route for proposed nodes, edges, aliases, and evidence links. |
| `llm.context.summarize` | Calls the selected local route for cited source, node, section, and corpus summaries. |
| `llm.conflict.review` | Calls the selected local route for support/contradiction review. |
| `llm.audit.review` | High-risk audit task. Locally it downgrades to open-weight review unless frontier or human review is explicitly allowed and approved. |

The local Docker stack includes an Ollama CPU service and routes private tenant
work to the smallest practical Gemma 4 E2B Q4 route by default through the
OpenAI-compatible endpoint:

```text
OH_LLM_BASE_URL=http://ollama:11434/v1
OH_LLM_MODEL=batiai/gemma4-e2b:q4
```

The official `gemma4:e2b` tag is also supported, but Ollama lists it as a much
larger local pull. The model must be present in the Ollama volume before live LLM
calls can execute:

```bash
docker compose -f infra/docker-compose.context.yml --profile models run --rm ollama-pull
```

If the model route is selected but the model is not reachable, the worker records
`model_unreachable_or_failed` instead of fabricating reviews.

## Model Hierarchy

| Tier | Use |
|---|---|
| Deterministic | Parse, chunk, regex facts, claims, graph skeletons, fragility, ambiguity, obvious conflicts. |
| Small trainable open-weight LLM | High-volume claim cleanup, ambiguity detection, fragile-fact tagging, routing, summary drafts. |
| Mid trainable open-weight LLM | Node/edge extraction, evidence review, summary verification, contradiction candidates. |
| Large open-weight LLM | Hard reasoning, long-context comparison, graph-community summaries, multi-document synthesis. |
| Ensemble review | Multiple independent judges for support, conflict, fragility, ambiguity, and schema validity. |
| Frontier/human audit | High-risk contradictions, ambiguous instructions, public-facing promotion decisions. |

The executable policy lives in
`scripts/context_workers/model_cascade.py`. It is data-shaped on purpose:
task families choose a start tier and max tier, then escalation rules decide how
far to climb. The default ladder is:

```text
deterministic
-> small_open_weight
-> mid_open_weight
-> large_open_weight
-> ensemble_review
-> frontier_adjudication
-> human_review
```

The cascade escalates on low confidence, weak evidence directness, weak source
quality, uncertain entity resolution, conflict, high fragility, ambiguity,
high-stakes domain, user-facing context, or model disagreement.

The default plan queues:

- `llm.claim.review`
- `llm.graph.enrich`
- `llm.context.summarize`

It also queues `llm.conflict.review` when conflict candidates exist and
`llm.audit.review` for high-risk ambiguity/conflict findings. The local default
does not hold read-only LLM audit work for human approval: if the cascade would
reach frontier or human review but `allow_frontier_llm` is not set, the task is
downgraded to the local open-weight lane and the budget reason records
`frontier_downgraded_to_local_open_weight`. Explicit frontier or human review
can still require approval.

## Fine-Tuning Loop

The cheap/open-weight tiers should get better over time. LLM review workers emit
`training_examples` with:

- task name;
- selected cascade tier;
- model route;
- input claims/nodes/edges/conflicts/concerns;
- pending model output;
- placeholder for reviewed output;
- `do_not_train_changing_facts_into_weights: true`.

Use these records to build LoRA/QLoRA datasets for specialist adapters:

```text
claim_extraction_adapter
edge_extraction_adapter
ambiguity_detection_adapter
fragile_fact_adapter
evidence_review_adapter
safe_summary_adapter
conflict_review_adapter
```

Fine-tune workflow behavior and restraint, not changing facts. Current CEOs,
addresses, prices, laws, sanctions status, software versions, and similar facts
belong in retrieved sources and verification caches, not model weights.

## Promotion Rules

LLMs may propose:

- new nodes;
- new edges;
- aliases;
- summaries;
- evidence ratings;
- conflict decisions;
- freshness concerns.

LLMs may not directly promote a candidate to trusted serving context. Promotion
requires evidence IDs and a review gate. The serving layer should distinguish:

- `detected`
- `enriched`
- `resolved`
- `corroborated`
- `verified`
- `contradicted`
- `stale`
- `review_before_serving`

## Async Contract

The deterministic pipeline emits trust-layer work through `TaskResult.enqueue`.

```text
context.pipeline.pass
-> context.ambiguity.scan
-> context.conflict.scan
-> context.fragile_fact.enrich
-> llm.trust.plan
-> Redis list ohh:context:jobs
-> llm.* workers
-> Redis stream ohh:context:events
-> ledger/artifact records
```
