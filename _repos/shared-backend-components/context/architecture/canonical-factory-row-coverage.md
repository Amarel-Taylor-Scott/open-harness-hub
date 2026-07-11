# Canonical Factory Row Coverage

The manifest catalog is intentionally curated and relatively small. The
million-object path depends on generated rows in Postgres plus pgvector, not on
one YAML manifest per extracted primitive.

## Row Families

Generated factories should be able to emit these row families as separate JSONL
shards:

- `source_record`: provenance, licensing, trust tier, freshness, and privacy boundary.
- `normalized_object`: procedure objects, question sets, checklists, tools, facts, and other generated primitives.
- `dedupe_cluster`: fuzzy grouping and canonical-object choice.
- `canonical_entity`: publishers, domains, standards, agencies, tools, frameworks, datasets, and other linked entities.
- `object_entity_ref`: edges from generated objects to canonical entities.
- `review_ticket`: human review routing before promotion or regulated use.
- `label_assignment`: controlled vocabulary, schema.org-style, hierarchical, and model-generated labels.
- `dimension_value`: scoring dimensions such as demand, complexity, cost savings, deployment frequency, capability gap, or economic value.
- `object_embedding`: text, model, hash, metadata, and optional pgvector value.
- `index_record`: keyword, vector, graph, facet, freshness, quality, and cost index updates.

## Factory Order

Use this order for local generation and preflight:

```text
source governance
-> normalized objects
-> dedupe clusters
-> canonical entities
-> object/entity references
-> review tickets
-> labels and dimensions
-> embeddings
-> index records
-> bulk COPY load
-> object count report
```

The preflight checker validates local shard relationships before load. Postgres
constraints remain the final authority after the `psql \copy` stage.

## Why This Matters

The registry should be able to hold millions of small, searchable, reviewable
objects without turning every object into a curated catalog manifest. YAML
manifests describe reusable components and policies. Database rows hold generated
and frequently changing primitives.

This split keeps:

- the static site fast;
- curator review practical;
- generated rows easy to count;
- vector, keyword, graph, and facet indexes rebuildable;
- labels and dimensions flexible as models, prices, and user demand change.

## Promotion Boundary

Generated rows can become catalog manifests only after review. Promotion should
consider provenance, license, dedupe status, privacy boundary, source quality,
usage, rating, evaluation results, and whether the object is broadly reusable.
