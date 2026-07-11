# Public Source Replay Row Emission

The replay runner proves which public-source jobs can run. The row emitter turns
those run records into canonical JSONL row families that can be validated,
preflighted, and bulk-loaded.

This layer is intentionally conservative:

- it consumes public blueprint metadata and replay audit records;
- it does not fetch source pages, PDFs, or scraped bodies;
- it emits schema-shaped rows for source records, normalized objects, entities,
  dedupe clusters, labels, dimensions, embedding stubs, index records, and
  review tickets;
- it keeps `insurance` in the excluded scope for this batch.

## Row Families

For each `source_ingest` replay record, the emitter creates candidate
primitives from the blueprint's expected object types. Each candidate is linked
to a source record, a blueprint source entity, a vertical concept, and required
workflow stages.

The resulting row families are:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `index_record`
- `review_ticket`

## Why This Matters

The platform can now test the whole path from source surface to database-ready
rows without network scraping. Real container workers can later replace the
synthetic candidate bodies with source-derived rows while preserving the same
row-family contracts, preflight checks, and Postgres/pgvector load path.
