# Verification Packet Record Persistence

Expert review, grounded search, and multi-model checks produce valuable
verification evidence, but that evidence only scales if it can enter the same
canonical row path as generated primitives. This pattern turns a verification
packet into source, object, entity, dedupe, review, and index JSONL shards.

## Purpose

The exporter is designed for high-risk knowledge objects: legal rules, public
health facts, labor rights facts, safety procedures, child-safety signals, and
objects with many downstream pipeline dependencies.

It stores:

- a `source_record` for the verification packet;
- `normalized_object` rows for the versioned fact, decision gate, and evidence;
- `canonical_entity` rows for risk tier, jurisdiction, decision, and channels;
- `object_entity_ref` graph edges;
- `dedupe_cluster` rows for deterministic duplicate suppression;
- `review_ticket` rows when a packet is high-risk, conflicted, or held;
- keyword, vector, graph, facet, quality, and freshness `index_record` rows.

## Privacy Boundary

Reviewer names, email addresses, raw messages, signatures, quoted threads, and
raw search payloads are not exported by default. The public-safe row families
retain reviewer role, assessment, channel, source URL, hashes, and structured
evidence. Raw material belongs in tenant-private storage or an approved
evidence vault.

## Factory Flow

1. Route the packet through source governance.
2. Export canonical JSONL row families.
3. Run relationship preflight before database load.
4. Prepare bulk-copy inputs for Postgres/pgvector.
5. Emit index records for keyword, vector, graph, facet, quality, and freshness
   search.

This makes expert-review loops additive: a new reply, grounded source, or model
review can append evidence without rebuilding the whole registry.
