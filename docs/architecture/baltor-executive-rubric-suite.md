# Baltor Executive Rubric Suite

This suite evaluates Baltor from the perspective of executive, design,
operations, finance, technology, customer, revenue, and staff engineering
leaders.

The rubrics are intentionally role-specific, but they share one architectural
principle:

```text
Do not reward brittle components.
Reward extensible, flexible, cloud-compatible systems that can ingest raw
context, find fragile information, keep it fresh, and serve trusted context
packs to downstream agents and systems.
```

## Shared Evaluation Themes

Every role should consider:

```text
extensibility
schema flexibility
non-fragile components
self-optimizing feedback loops
source-handle fidelity
freshness and fragile-information handling
document-style storage fit
long attribute/facet storage fit
wide columnar analytics fit
cloud hosting compatibility
cost and operational sustainability
human trust and auditability
```

## Rubrics As Context Objects

Rubrics should not be treated as static review prose. In Baltor, a rubric is a
context object:

```text
rubric object
  stable ctx:// identity
  versioned scored dimensions
  relationship edges to packs, tools, masks, transformers, policies, and evals
  lineage for who changed it and why
  dimension values for quality, freshness, authority, and fit
  evidence requirements that can be checked during review
```

The same rule applies to tools, masks, and transformers.

```text
Tool context object:
  callable capability with permissions, inputs, outputs, audit, and failure modes

Mask context object:
  redaction, projection, field-selection, permission, or view policy that controls
  which parts of a context object can be shown, stored, synced, indexed, or sent
  to a model

Transformer context object:
  deterministic, model-assisted, or learned conversion from one representation to
  another, such as raw source to normalized Markdown, object to artifact, artifact
  to embedding, retrieval candidates to reranked list, or context pack to UI view

Rubric context object:
  reusable evaluation contract that scores objects, packs, tools, masks,
  transformers, architectures, and workflows
```

This matters because rubrics, masks, tools, and transformers are not passive
configuration. They affect what agents see, what data is hidden, what is
derived, what is trusted, what is routed, and what gets refreshed. They need the
same versioning, lineage, relationships, dimensions, and policy treatment as
source documents and context packs.

## Data Shape Guidance

Baltor should not force one storage model everywhere.

Document-style records fit:

```text
context objects
facets
source payloads
context packs
connector envelopes
policy snapshots
```

Long attribute/facet records fit:

```text
dimensions
assertions
claims
scores
relationship attributes
model/reranker decisions
freshness assessments
```

Wide columnar records fit:

```text
operational metrics
cost analytics
pack outcome analytics
retrieval evaluation
usage trends
latency/cost/freshness dashboards
```

The rubrics should reward architectures that can support all three shapes
without hard-coded migrations for every new source, dimension, or customer.

## Dimension Overlays

The role rubrics are intentionally focused. For internal development reviews,
combine each role rubric with these overlay rubrics:

```text
catalog/rubrics/baltor-context-object-component-quality.yaml
catalog/rubrics/baltor-schema-flexibility-quality.yaml
catalog/rubrics/baltor-fragile-information-quality.yaml
catalog/rubrics/baltor-self-optimizing-architecture-quality.yaml
catalog/rubrics/baltor-hierarchical-context-system-quality.yaml
catalog/rubrics/baltor-context-object-lifecycle-quality.yaml
catalog/rubrics/baltor-cloud-data-architecture-quality.yaml
catalog/rubrics/baltor-agent-safety-governance-quality.yaml
catalog/rubrics/baltor-business-operating-readiness-quality.yaml
```

These overlays add deeper dimensions for:

```text
identity and source handles
versioning and bitemporal history
relationship and hyperedge design
attribute/facet extensibility
document, long attribute, and wide columnar schema fit
masking, redaction, and projection behavior
transformer lineage and reversibility
reranking and learned optimization
fragile-information detection and refresh loops
cloud hosting compatibility
tenant isolation and policy enforcement
cost observability
eval feedback and self-improvement
```

The deeper research-backed standard is documented in:

```text
docs/architecture/baltor-rubric-research-and-hierarchical-standard.md
```

## Catalog Rubrics

The suite is stored as reusable rubric components:

```text
catalog/rubrics/baltor-cto-architecture-quality.yaml
catalog/rubrics/baltor-coo-operating-model-quality.yaml
catalog/rubrics/baltor-ceo-strategy-quality.yaml
catalog/rubrics/baltor-chief-ui-ux-product-experience-quality.yaml
catalog/rubrics/baltor-chief-customer-experience-quality.yaml
catalog/rubrics/baltor-chief-revenue-officer-quality.yaml
catalog/rubrics/baltor-chief-expense-officer-quality.yaml
catalog/rubrics/baltor-cfo-financial-control-quality.yaml
catalog/rubrics/baltor-staff-design-engineer-quality.yaml
catalog/rubrics/baltor-cio-cloud-governance-quality.yaml
catalog/rubrics/baltor-chief-ai-officer-quality.yaml
catalog/rubrics/baltor-chief-security-officer-quality.yaml
catalog/rubrics/baltor-context-object-component-quality.yaml
catalog/rubrics/baltor-schema-flexibility-quality.yaml
catalog/rubrics/baltor-fragile-information-quality.yaml
catalog/rubrics/baltor-self-optimizing-architecture-quality.yaml
catalog/rubrics/baltor-hierarchical-context-system-quality.yaml
catalog/rubrics/baltor-context-object-lifecycle-quality.yaml
catalog/rubrics/baltor-cloud-data-architecture-quality.yaml
catalog/rubrics/baltor-agent-safety-governance-quality.yaml
catalog/rubrics/baltor-business-operating-readiness-quality.yaml
```

Use them together for quarterly architecture reviews, design-partner readiness,
pilot closeouts, and investor/customer diligence.
