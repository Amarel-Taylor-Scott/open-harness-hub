# High-Priority Primitive Opportunity Rankings Handoff

Last updated: 2026-07-01

Audience: Claude 5 Fable, Codex, Claude Code, and model lanes deciding which
primitive families to build next.

Status: generated seed ranking. These rows are candidate planning artifacts,
not promoted truth.

## Core Question

The highest-value primitive specialties are the ones that repeatedly turn vague
LLM work into source-backed, auditable, reusable capability:

```text
entity resolution
entity enrichment
data verification
related data search
fragile-context monitoring
geography-specific search
legal information search
source reference resolution
temporal freshness tracking
jurisdiction policy mapping
data quality profiling
schema mapping and normalization
relationship graph extraction
adverse media and risk discovery
sanctions and watchlist screening
document extraction with evidence
citation span verification
license and terms review
privacy boundary classification
proof receipt generation
```

These should outrank generic model-call wrappers because they are reusable
across industries, reduce hallucination, expose proof gaps, and make primitive
promotion possible.

## Seed Pack

The generated pack is:

```text
catalog/knowledge-packs/data/high-priority-primitive-opportunity-rankings/
```

It contains:

- `primitive_opportunities_1000.jsonl` with 1,000 ranked opportunity rows;
- `module_specialty_catalog.jsonl` with 20 high-value module specialties;
- `industry_priority_matrix.jsonl` with 25 industries;
- `route_variants.jsonl` with fast-triage and evidence-grade variants;
- `scoring_model.json` with the ranking formula.

The generator is:

```bash
python3 scripts/generate_high_priority_primitive_opportunity_rankings.py
```

The checker is:

```bash
python3 scripts/check_high_priority_primitive_opportunity_rankings.py --self-test
```

## Row Shape

Every opportunity row includes:

```text
module specialty
industry
route variant
priority score
rank
input edge
output edge
transformations
runtime targets
source surface hints
proof requirements
negative memory queries
materialization policy
```

All rows stay:

```json
{
  "candidate": true,
  "serves_truth": false
}
```

until source refs and proof receipts exist.

## How To Use It

Use the rankings to decide where primitive generation should spend tokens and
verification effort:

```text
top opportunities
  -> create or select source adapters
  -> generate candidate primitive cards
  -> attach proof obligations
  -> run fixtures or benchmark routes
  -> materialize only hot or proof-backed combinations
```

Do not use the score as truth. Use it as a queue priority.

## Problem-Solution Detail Layer

Ranked opportunity rows are intentionally compact. For implementation,
troubleshooting, and proof planning, use the linked detail layer:

```text
catalog/knowledge-packs/data/primitive-problem-solution-details/
```

Each detail row links to one `opportunity_id` and adds problem framing, user
triggers, stakes, non-goals, solution routes, transformations, implementation
notes, acceptance criteria, proof plans, failure modes, troubleshooting hooks,
negative memory queries, and synthetic example input/output.

Read:

```text
docs/codex/primitive-problem-solution-details-handoff.md
```

Use the score to pick work; use the detail row to make that work concrete.

## Validation

Run:

```bash
python3 scripts/generate_high_priority_primitive_opportunity_rankings.py
python3 scripts/check_high_priority_primitive_opportunity_rankings.py --self-test
```
