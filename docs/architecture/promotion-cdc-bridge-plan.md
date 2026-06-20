# Promotion CDC Bridge Plan

Approved component promotion and component CDC are separate steps:

1. promotion decides whether a candidate can become an active component;
2. CDC records what changed and updates search/review projections.

The bridge planner connects those steps. It reads `component-versions.csv` from the approved promotion planner, converts the rows into canonical component version JSONL, and then runs the component CDC planner.

## Inputs

- `component-versions.csv` from approved promotion.
- optional `previous-component-versions.jsonl` from the database or a previous export.
- output directory.

When there is no previous version file, the bridge treats rows as first-publication events. That is useful for seed loads and synthetic tests, but production workers should export previous versions from Postgres whenever a component id already exists.

## Outputs

- `new-component-versions.jsonl`
- `component-change-events.jsonl`
- `component-change-index-records.jsonl`
- `component-change-review-tickets.jsonl`
- `load-component-change-events.sql`
- `promotion-cdc-bridge-plan.json`

This keeps approved component publication additive and auditable. A worker can load active component rows, then load CDC rows, then replay index deltas.

## Why It Matters

At one million components, rebuilding everything after each source refresh is the wrong shape. The platform needs incremental rows:

- which component changed;
- which version replaced which version;
- what hashes changed;
- whether signed publisher state changed;
- which search records need refresh;
- which changes need human or publisher review.

The bridge gives approved promotion batches the same lifecycle spine as public facts, signed knowledge objects, and volatile source refreshes.
