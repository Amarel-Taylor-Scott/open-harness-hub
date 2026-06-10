# Approved Component Promotion Plan

The database-backed factory has two separate boundaries:

1. candidate generation and scoring
2. active component publication

The approved component promotion planner handles the second boundary. It reads component candidates, subcomponent candidates, and promotion decisions, then emits a side-effect-free Postgres load bundle.

Outputs:

- `components.csv`
- `component-versions.csv`
- `subcomponents.csv`
- `candidate-state-updates.csv`
- `load-approved-components.sql`
- `approved-component-promotion-plan.json`

## Review Gate

A candidate becomes an active component only when all of these are true:

- the decision is `promote_candidate`
- the decision has no risk flags
- the decision has no review reasons
- the candidate review status is approved

All other decisions still update candidate state:

- `review_before_promotion` becomes `review`
- `hold` becomes `held`
- `reject` becomes `rejected`

This keeps generated rows additive and searchable while preventing low-confidence or dedupe-review rows from becoming reusable components.

## Active Rows

Approved candidates generate:

- one `component` row
- one `component_version` row with `definition_source = generated_factory`
- zero or more `subcomponent` rows
- one candidate state update

The planner maps generated primitive types into the allowed active component types. Generic candidate primitives become `knowledge-pack` rows unless a clearer active type is available.

## Current Seed Behavior

The current seed promotion decisions are all `hold` because the generated candidates belong to dedupe-review clusters. The planner therefore emits zero active component rows and 620 candidate state updates. That is expected: the review boundary is working.

The next promotion batch should either resolve dedupe clusters or use explicitly approved synthetic test candidates before publishing active rows.
