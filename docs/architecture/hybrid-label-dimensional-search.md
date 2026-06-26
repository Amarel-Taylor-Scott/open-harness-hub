# Hybrid Label and Dimensional Search

Vector search is necessary but not sufficient for a million-object registry. OpenHubForAI should combine pgvector with hierarchical labels, custom label sets, schema.org-style types, entity graph edges, and model-generated dimensions.

The result is hybrid search:

```text
query
-> keyword search
-> hierarchical label filters
-> schema.org / entity type filters
-> custom dimension filters
-> vector search
-> graph expansion
-> model-polished reranking
-> cost/trust/freshness filters
```

## Label Layers

Every source object, primitive, and pipeline can carry multiple label layers:

- **Catalog labels**: component type, industry, capability, modality, lifecycle, trust boundary.
- **Hierarchical labels**: domain paths such as `finance.aml.alert_review`, `healthcare.public_health.guidance`, or `software.devops.containerized_worker`.
- **Schema.org-style labels**: `Dataset`, `SoftwareApplication`, `DefinedTerm`, `GovernmentService`, `MedicalGuideline`, `HowTo`, `Action`, `Organization`, `CreativeWork`, and similar web-scale concepts.
- **Custom tenant labels**: customer-defined labels such as internal policy family, team owner, system-of-record, review queue, risk tier, or product line.
- **Generated dimensions**: low-cost LLM or classifier outputs such as complexity, deployment difficulty, review risk, automation potential, data sensitivity, evaluation burden, cost-savings opportunity, and model-swap value.

Labels should be queryable and versioned. A generated label is not a fact unless it has review or evaluation support.

## Flexible Hierarchies

Core manifest fields such as capability and modality should remain small,
stable, and cross-cutting. They are not the right place for every vertical,
sub-industry, jurisdiction, workflow family, buyer segment, or deployment
environment. Expansion should happen through label records and dimension
records.

Examples:

- `vertical.trades.electrical.permit_review`
- `vertical.trades.plumbing.backflow_prevention`
- `vertical.energy.oil_gas.pipeline_integrity`
- `vertical.veterinary.animal_hospital.triage`
- `jurisdiction.us.state.california`
- `law.us.state.bank_disclosure`
- `workflow.content_moderation.image_text_triage`
- `creative.content_creation.brand_safe_asset_generation`
- `market.competition_analysis.product_feature_matrix`

This keeps the public schemas flexible while avoiding constant churn in
controlled vocabularies. New labels can be tenant-defined, publisher-defined,
model-generated, or curator-approved. Promotion rules decide when a generated
label becomes trusted enough for search ranking or deployment routing.

## Dimensions

Dimensions are numeric or categorical features used for sorting, filtering, routing, and recommendation.

Useful dimensions include:

- `task_complexity`
- `domain_specificity`
- `out_of_box_llm_weakness`
- `deployment_frequency`
- `human_review_need`
- `privacy_sensitivity`
- `regulatory_risk`
- `cost_savings_opportunity`
- `runtime_cost_sensitivity`
- `model_swap_value`
- `evidence_requiredness`
- `freshness_volatility`
- `evaluation_difficulty`
- `containerization_need`

Some dimensions are deterministic, some are curator-provided, and some can be model-generated. A cheap local model such as Gemma can be a default labeler/reranker, but the platform should support many local and cloud models behind a routing wrapper.

## Model Routing

Do not hard-code one model family into the platform. Use a model capability router that selects providers by:

- task type: label, rerank, extract, summarize, classify, judge, embed, caption, code, media;
- modality: text, image, audio, video, structured;
- trust boundary: local, tenant, external, mixed;
- cost ceiling;
- latency budget;
- context window;
- output schema strictness;
- privacy and data residency;
- batch support;
- provider availability;
- quality tier.

Gemma remains useful as an inexpensive local/default route for labels, reranking, extraction, and RAG result polishing. It should be one option in a model registry, not a platform assumption.

## Index Records

Hybrid search needs separate but linked index records:

- keyword document;
- vector document;
- graph edge;
- hierarchical label assignment;
- schema.org label assignment;
- custom label assignment;
- dimension score;
- model route decision;
- quality/eval/freshness/cost records.

This lets a user ask for “cheap deployable AML alert-review components that are high-confidence, low privacy risk, and not solved by a generic LLM,” and have the ranker combine semantic similarity with explicit labels and dimensions.

## Storage

Postgres can store labels and dimensions early:

- `label_set`
- `label_assignment`
- `dimension_definition`
- `dimension_value`
- `model_route_decision`

pgvector still stores semantic embeddings, but labels and dimensions should be ordinary indexed fields so exact filters remain cheap and explainable.
