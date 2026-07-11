# Specialized Model Card Row Emission

Specialized model-card scan jobs become useful to the registry only after they
are converted into canonical row families. The row emitter turns public
model-card signal metadata into the same JSONL shapes used by the broader object
factory and Postgres/pgvector loaders.

The emitter consumes queued `task_context_normalize` jobs from the specialized
model-card scan lifecycle and writes:

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

## What It Produces

Each specialized model signal can emit multiple candidate primitives: label
schemas, task definitions, input/output contracts, evaluation harness seeds,
limitations, replacement routes, and cost-aware routing candidates. These
objects are not model weights. They are reusable context that helps a general
LLM, RAG pipeline, small classifier, or human review flow approximate or route a
specialized task.

## Guardrails

The row emitter preserves the source boundary:

- model weights are not downloaded;
- private training data is not stored;
- model card bodies are not republished without license review;
- generated rows carry public metadata provenance;
- high-impact domains route to review tickets;
- excluded scopes stay attached to label and dimension rows.

## Scale Path

This makes Hugging Face, model leaderboards, papers, and model repositories
compatible with the same ingestion path as public-source blueprints. At scale,
container workers can scan thousands of specialized model cards, emit row
families, preflight relationships, bulk load into Postgres, embed text fields,
and expose hybrid keyword/vector/graph/facet search.

