# Verification Packet Record Persistence

Expert review, grounded search, and multi-model checks produce valuable
verification evidence, but that evidence only scales if it can enter the same
canonical row path as generated primitives. This pattern turns a verification
packet into source, object, entity, dedupe, review, and index JSONL shards.

## Upstream verification channels (what produces the packet)

Some knowledge objects should not be promoted just because a model extracted them
cleanly. High-risk facts, civil-society context, legal rules, public-health
guidance, labor-rights indicators, and safety-critical workflow objects need
external verification channels.

The DueCare/OpenClaw pattern is useful here: maintain a vetted reviewer network,
send small review questions by email, ingest replies, and digest the responses
into structured knowledge-object review evidence. For example:

- "Does this context fact make sense to you?"
- "Which of these indicators matters most in practice?"
- "Is this source still current?"
- "What would make this pipeline unsafe or misleading?"

The same verification gate can require additional machine checks for important
objects: grounded search, multiple LLM reviewers, source conflict checks, archive
comparison, and citation validation.

## Verification gate

A high-risk object can require one or more gates before promotion:

1. source governance and sensitive-data screening;
2. grounded search or official-source retrieval;
3. independent model reviews with disagreement detection;
4. expert email review campaign;
5. inbound response digest into structured evidence;
6. curator review ticket when evidence conflicts or confidence is low.

The output is not just an approval. It is a review packet: evidence spans,
rankings, dissent, source freshness, and promotion constraints that downstream
RAG and pipelines can consume — and that the persistence path below turns into
canonical rows.

## Contact governance

The platform should not publish scraped personal contact data. Reviewer outreach
should use consented subscribers, organization-approved contacts, role accounts,
or tenant-private contact lists with unsubscribe and suppression handling. Public
catalog seed data should store contact-policy patterns, not real email addresses.

Each reviewer response should become a source record with:

- consent or lawful-basis metadata;
- reviewer role class rather than private identity by default;
- received timestamp and message hash;
- privacy boundary;
- permitted downstream uses;
- confidence, disagreement, and review status.

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
