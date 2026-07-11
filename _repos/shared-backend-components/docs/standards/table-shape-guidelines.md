# Table-shape guidelines (the storage rule)

Canonical state is **NOT** text files. Text files are for docs, schemas, skills, prompts,
fixtures, and small human-readable exports. Durable state lives in databases + object storage.

| Shape | Use for | Store |
|---|---|---|
| **Object tables** | stable identities: `context_objects`, `source_handles`, `context_packs`, `tools`, `adapters`, `pipelines` | Postgres |
| **Version tables** | immutable snapshots: source/object/pack/prompt versions | Postgres (+ object store for blobs) |
| **Long tables** | sparse/extensible: claims, dimensions, scores, events, policy decisions, rot signals, verification findings | Postgres |
| **Relationship tables** | edges / n-ary: confirms, contradicts, supersedes, owned_by, approved_by, implemented_by, parent_of | Postgres → graph DB later |
| **JSONB facets** | source-specific long-tail: `jira.*`, `gitlab.*`, `confluence.*`, `github.*`, `parser.*`, `custom.*` | Postgres JSONB + GIN |
| **Wide tables** | fast UI/dashboard projections **only** | Materialized views (disposable) |
| **Object storage** | raw snapshots, parsed artifacts, page images, cropped figures/tables, generated wikis, large exports | S3 / R2 / MinIO |
| **Vector index** | chunk embeddings that **reference** leaf `object_id`s (not source-of-truth) | Qdrant (primary) / pgvector (demo) |
| **Graph index** | traversal / path / contradiction queries | Graphiti (primary) — **not Kuzu (archived Oct 2025)** |

## Decision rule
- Stable identity? → **object table**.
- Historical state? → **version table**.
- Sparse / source-specific? → **JSONB facet** or **long table**.
- A score/dimension/finding? → **long table**.
- A relationship/edge? → **relationship table**.
- An execution trace/event? → **event table**.
- A high-frequency read projection? → **wide materialized view** (regenerable, never the only copy).

## Do NOT
- store raw source dumps in git · keep source-of-truth context only in Markdown · make the vector
  DB canonical · let generated repo wikis be authoritative · nest a whole document tree as one blob
  (the recursion lives in fragment handles + parent relationships, kept first-class).

The recursive `context-object` model (`schemas/context-object.schema.json`) follows this: each
decomposed node is an object record; its parent is a `provenance.wasDerivedFrom` link, not a nested
child (proven in `scripts/ingest/decompose_to_context_objects.py`).
