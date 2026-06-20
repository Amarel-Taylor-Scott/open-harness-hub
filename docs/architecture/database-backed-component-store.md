# Database-Backed Component Store

The production registry should be a Postgres-backed component store. Repository files and JSONL are useful for bootstrapping, review diffs, import/export, and static docs, but they are not the product database.

## Core Model

A **component** is an active reusable unit that can be searched, versioned, rated, evaluated, wired into a pipeline, deployed, and updated.

A **subcomponent** is a smaller reusable unit inside or attached to a component:

- fact
- rule
- check
- review question
- evaluation criterion
- prompt fragment
- schema field
- cost dimension
- label
- generated dimension
- entity reference
- index record
- embedding work item
- review route
- deployment step

This lets the platform scale to millions of useful records without pretending every record should become a hand-curated repository file.

## Storage Shape

Postgres owns the canonical state:

- `component`
- `component_version`
- `subcomponent`
- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `index_record`
- `object_embedding`
- `review_ticket`
- `promotion_decision`

Pgvector is the first semantic search backend. Postgres full-text search, labels, dimensions, entity links, and graph-like edges stay first-class so retrieval remains explainable and cheap.

## File Role

Files are still useful, but only in limited roles:

- seed definitions for public components;
- portable JSONL shards for staging and replay;
- generated static docs;
- export bundles for users;
- review diffs for contributors.

The hosted product should write to Postgres first and generate file views from the database when needed.

## Factory Flow

```text
source surface
-> source governance routing
-> normalized objects
-> entity links and dedupe clusters
-> labels and dimensions
-> component candidates
-> subcomponent candidates
-> review tickets
-> promotion decisions
-> canonical component and subcomponent tables
-> keyword/vector/graph/facet indexes
-> static export or deployment blueprint
```

## Current Seed Plan

`scripts/db/component_store_plan.py` converts staged factory JSONL into:

- `component-candidates.jsonl`
- `subcomponent-candidates.jsonl`
- `source-component-links.jsonl`
- `component-store-plan.json`

It does not mutate Postgres. It proves the row shape and count model before a load worker is added.
