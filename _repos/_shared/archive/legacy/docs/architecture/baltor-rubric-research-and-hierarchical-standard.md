# Baltor Rubric Research And Hierarchical Standard

This document turns current best practices into a deeper internal rubric
standard for Baltor. The goal is to evaluate systems that sync raw context,
process it, identify fragile information, keep it current, and deliver trusted
context packs to downstream tools and agents.

The core product should keep the narrow wedge:

```text
trusted, source-linked, freshness-aware context packs for engineering agents
```

The infrastructure should still be designed as a context-object system where
tools, rubrics, masks, transformers, processors, prompts, rerankers, schemas,
context packs, and source documents are all versioned context objects.

## Research Signals

The research base points to five practical conclusions.

First, AI-assisted development needs better context, not just stronger models.
Google Cloud's 2025 DORA reporting highlights widespread AI use in software
development and explicitly calls out the need to connect AI to internal context.
It also reports continuing trust concerns around AI-generated code.

Second, LLM applications need explicit risk controls. OWASP's LLM application
guidance covers prompt injection, sensitive information disclosure, excessive
agency, vector and embedding weaknesses, misinformation, and unbounded
consumption. Baltor rubrics should therefore score retrieval controls,
permission-before-model behavior, embedding privacy, source integrity, and
agent action limits.

Third, generative AI governance needs lifecycle risk management. NIST's
Generative AI Profile for the AI Risk Management Framework emphasizes risk
management across design, development, use, and evaluation. Baltor rubrics
should evaluate governance as an operating loop, not as a launch checklist.

Fourth, cloud architecture should be evaluated across reliability, security,
cost optimization, operational excellence, and performance efficiency. Azure's
Well-Architected guidance and cloud design pattern catalog are useful anchors
for cloud-compatible rubric dimensions.

Fifth, flexible data systems should use the right shape for the job. PostgreSQL
JSONB and GIN indexing support flexible document search, MongoDB's guidance
warns against unbounded arrays and bloated documents, ClickHouse explains the
fit of columnar storage for analytics, and Apache Iceberg documents schema and
partition evolution for large analytical tables. Baltor should reward systems
that combine document-style objects, long attribute/dimension records, graph
edges, and wide columnar analytics instead of forcing every use case into one
schema.

## Sources

- Google Cloud DORA 2025 AI-assisted software development:
  <https://cloud.google.com/blog/products/ai-machine-learning/announcing-the-2025-dora-report>
- Google DORA report summary:
  <https://blog.google/innovation-and-ai/technology/developers-tools/dora-report-2025/>
- OWASP Top 10 for LLM Applications:
  <https://owasp.org/www-project-top-10-for-large-language-model-applications>
- AWS mapping to OWASP LLM Top 10:
  <https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-security/owasp-top-ten.html>
- NIST AI RMF Generative AI Profile:
  <https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf>
- Azure Architecture Center:
  <https://learn.microsoft.com/en-us/azure/architecture/>
- Azure cloud best practices:
  <https://learn.microsoft.com/en-us/azure/architecture/best-practices/index-best-practices>
- PostgreSQL JSON types:
  <https://www.postgresql.org/docs/17/datatype-json.html>
- PostgreSQL GIN indexes:
  <https://www.postgresql.org/docs/current/gin.html>
- MongoDB schema design anti-patterns:
  <https://learn.mongodb.com/learn/course/schema-design-patterns-and-antipatterns/schema-design-patterns-and-anti-patterns/conclusion?page=1>
- ClickHouse columnar database guide:
  <https://clickhouse.com/engineering-resources/what-is-columnar-database>
- Apache Iceberg schema and partition evolution:
  <https://iceberg.apache.org/docs/nightly/evolution/>

## Hierarchical Rubric Model

The current catalog schema stores rubric dimensions as a flat list. To support
multi-level rubrics without changing the schema, use hierarchical dimension IDs:

```text
1                     domain
1.2                   capability group
1.2.3                 scored capability
1.2.3.evidence        evidence check, recorded in evidence_required
```

Example:

```yaml
dimensions:
  - id: "2.3.1"
    label: "Every fragile claim carries source handles, freshness, confidence, and risk"
    weight: 0.025
    scale: "0.0-1.0"
    evidence_required: "Inspect claim records, context packs, source-handle expansion, and freshness labels."
```

This lets us keep valid catalog manifests while making the review structure
human-readable and sortable.

## Standard Review Levels

Use four levels when evaluating Baltor systems.

```text
Level 0: Gate
  Disqualifying requirements. If these fail, do not ship.

Level 1: Foundation
  Required architecture and operating capabilities.

Level 2: Maturity
  Capabilities that make the system resilient, scalable, measurable, and useful
  across teams.

Level 3: Optimization
  Self-improving, cost-aware, risk-aware, and evidence-driven capabilities.

Level 4: Strategic Advantage
  Capabilities that become defensible product value, customer trust, and
  enterprise expansion.
```

The catalog rubrics encode these levels with numbered dimensions.

## Recommended Rubric Stack

For internal development reviews, run these together:

```text
Core executive perspective:
  baltor-cto-architecture-quality
  baltor-cio-cloud-governance-quality
  baltor-chief-ai-officer-quality
  baltor-chief-security-officer-quality
  baltor-staff-design-engineer-quality

Deep overlays:
  baltor-hierarchical-context-system-quality
  baltor-context-object-lifecycle-quality
  baltor-cloud-data-architecture-quality
  baltor-agent-safety-governance-quality
  baltor-business-operating-readiness-quality
```

## Scoring Interpretation

```text
0.00-0.20: absent or actively harmful
0.21-0.40: partial, brittle, or manually dependent
0.41-0.60: usable pilot capability with known gaps
0.61-0.80: production-ready for controlled rollout
0.81-0.95: mature, measurable, and resilient
0.96-1.00: exemplary, proven, and hard to replicate
```

Gates should be evaluated separately. A high average score must not hide a
failed gate for security, privacy, source traceability, freshness, or customer
trust.

## Required Evidence Packet

Every major review should produce:

```text
architecture diagram
source connector list
context object schema
relationship and dimension registry
mask and transformer registry
policy model
context-pack examples
retrieval trace
source-handle expansion trace
freshness/conflict report
cost report
eval report
security review
customer workflow evidence
open risks and owner list
```

## Anti-Patterns

Fail or heavily penalize systems that:

```text
send raw source to models before permission checks
store unlimited relationships inside object documents
put every score as a fixed column
treat embeddings as non-sensitive
make generated summaries look like source of truth
hide stale or conflicting context
skip source handles
combine personal encrypted memory and company-readable context without a boundary
make cloud provider choice part of the data contract
optimize only for vector similarity
let rerankers or model routers change behavior without lineage
build a broad platform before proving trusted context packs
```

