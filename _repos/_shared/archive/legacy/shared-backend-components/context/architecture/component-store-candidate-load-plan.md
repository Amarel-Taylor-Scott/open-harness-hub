# Component Store Candidate Load Plan

The database-backed component store needs a safe loading boundary. Generated rows should not jump directly into public active components. They first enter candidate tables with source traceability and review state.

## Tables

The load plan targets:

- `component_candidate`
- `subcomponent_candidate`
- `source_component_link`

These sit between staged factory output and active `component` / `subcomponent` rows.

## Why Candidate Tables

Candidate tables let the platform scale ingestion without overstating quality:

- generated components can be counted honestly;
- source, license, trust, and privacy metadata stays attached;
- high-risk or low-confidence rows remain review-gated;
- promotion can happen later without re-running ingestion;
- rejected or held rows remain useful for dedupe and future audits.

## Current Load Planner

`scripts/db/component_store_load_plan.py` reads `component-store-plan.json` and writes:

- `component-candidates.csv`
- `subcomponent-candidates.csv`
- `source-component-links.csv`
- `load-component-store.sql`
- `component-store-load-plan.json`

It does not connect to Postgres. A worker or operator can review the SQL and then run it with `psql`.

## Load Order

The intended order is:

1. Load source records and normalized objects.
2. Load component candidates.
3. Load subcomponent candidates.
4. Load source-component links.
5. Run committed-count audit.
6. Promote reviewed candidates to active components and subcomponents.

This keeps the million-component target tied to database rows and review state, not repository file counts.
