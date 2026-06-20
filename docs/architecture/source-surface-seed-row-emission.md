# Source Surface Seed Row Emission

Source-surface seeds describe where valuable primitives can come from. To move
toward a million-object registry, those seeds must become loadable factory
rows, not only research notes.

The source-surface row exporter converts each source surface into one candidate
seed per declared primitive, then delegates to the canonical use-case seed row
exporter. This produces:

- `source_record`
- `normalized_object`
- `canonical_entity`
- `object_entity_ref`
- `dedupe_cluster`
- `label_assignment`
- `dimension_value`
- `object_embedding`
- `review_ticket`
- `index_record`

## Conversion

Each source surface has a vertical, source surfaces, capability-gap reason,
candidate primitives, labels, risk tier, and excluded scopes. The exporter
turns every candidate primitive into a candidate object with:

- source surfaces as expected inputs;
- primitive name as expected output;
- source governance, entity linking, fuzzy dedupe, index emission, and review
  routing as required stages;
- flexible labels from the vertical, workflows, and primitive type;
- generated entities, dimensions, and embedding buckets.

This keeps esoteric industries like automotive sales, employment agencies,
plumbing and HVAC, woodworking, offshore oil and gas, and environmental reviews
compatible with the same storage and search path as broader use-case seeds.

## Review Boundary

High-risk source surfaces emit review tickets before promotion. Synthetic seed
metadata can be public. Real source snapshots, customer documents, private
manuals, emails, or records with PII must stay behind tenant-specific privacy
boundaries.
