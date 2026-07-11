# Specialized Model Card Load Plan

Specialized model-card rows should not jump directly from JSONL into promoted
catalog components. They need a load and promotion audit plan that proves the row
families are internally consistent, assigns promotion readiness, and produces a
database load package.

The load-plan wrapper for specialized model-card rows runs four stages:

1. relationship preflight across source records, normalized objects, entities,
   refs, dedupe clusters, labels, dimensions, embeddings, and review tickets;
2. deterministic candidate promotion scoring for each normalized object;
3. review-ticket and quality-index emission from promotion decisions;
4. CSV and `psql \copy` load-script generation for Postgres/pgvector.

## Why This Layer Exists

Model-card mining is high signal but not automatically authoritative. A model
card can imply useful task contracts, label schemas, or evaluation harnesses,
but those objects still need license review, dedupe review, domain review, and
embedding/index generation before they become stable primitives. The load plan
keeps that boundary explicit.

## Seed Plan

The current seed run loads the generated specialized model-card rows from
`dist/specialized-model-card-rows/seed` and emits:

- 33 promotion decisions;
- 33 promotion quality index records;
- 33 promotion review tickets;
- a bulk CSV set for 11 row families;
- a generated `load.sql` for Postgres staging-table upserts.

All seed candidates are held for review by the generic scorer. That is expected:
model-card-derived primitives carry license, dedupe, and high-impact review
signals until a curator or domain-specific promotion scorer clears them.

## Guardrails

- The load plan contains derived public model-card metadata only.
- Model weights are not downloaded.
- Private training data is not copied or stored.
- Promotion decisions are advisory and review-gated.
- Bulk output is a database import plan, not a public promotion decision.

