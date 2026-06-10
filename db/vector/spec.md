# Vector DB spec — Open Harness Hub

Two indexes:

1. **Catalog index** — one vector per component (embedding of
   `name + description + tags`). Powers semantic catalog search and
   "find similar harnesses / pipelines / rule packs" features.
2. **Knowledge index** — one vector per `knowledge_leaf` (embedding of
   the leaf body's text content). Powers RAG retrieval inside pipeline
   execution.
3. **Source/object index** — one vector per normalized high-volume object
   extracted from source surfaces. Powers candidate primitive discovery,
   dedupe, and source-backed search before an object becomes a curated
   manifest.
4. **Entity index** — one vector per canonical entity description and
   alias set. Powers entity linking, fuzzy organization, and graph search.

Vector search is paired with non-vector indexes for hierarchical labels,
schema.org-style labels, tenant custom labels, and dimension scores. These
labels are not embedded away; they remain exact, filterable records.

The canonical model, dimension, similarity function, backend names, and
per-index profile names come from `scripts/_config.py` and can be exported with:

```bash
python3 -m scripts.db.vector_config_registry --format markdown
```

Hosted deployments should seed/check `setting_profile` / `setting_value`
rows from that export instead of copying these values into backend-specific
DDL by hand.

Both indexes are populated by `scripts/db/build_vector_index.py`.

## Index: `oh_catalog`

| Field | Type | Required | Use |
|---|---|---|---|
| `component_id`    | string | yes | Primary key. |
| `type`           | string | yes | Filter. |
| `industry`       | array  | no  | Filter. |
| `capability`     | array  | no  | Filter. |
| `modality`       | array  | no  | Filter. |
| `trust_boundary` | string | no  | Filter. |
| `lifecycle`      | string | no  | Filter. |
| `embedding`      | f32[D] | yes | The vector. `D` matches embedder dim. |

Default embedder and `D` are registry values. Override through a registered
embedding profile or database setting row rather than a parallel prose value.

## Index: `oh_knowledge`

| Field | Type | Required | Use |
|---|---|---|---|
| `leaf_id`        | string | yes | Primary key. |
| `pack_id`        | string | yes | Filter to a single pack. |
| `leaf_type`      | string | yes | Filter to a leaf type. |
| `language`       | string | no  | Filter. |
| `industry`       | array  | no  | Filter. |
| `chunk_index`    | int    | no  | Sub-chunk order within a leaf. |
| `text`           | string | yes | Original text used for the embedding. |
| `embedding`      | f32[D] | yes | The vector. |

## Index: `oh_source_object`

| Field | Type | Required | Use |
|---|---|---|---|
| `object_id` | string | yes | Primary key. |
| `object_type` | string | yes | Filter: task, review_question, checklist_item, versioned_fact, workflow_node, etc. |
| `source_record_id` | string | yes | Provenance join. |
| `canonical_entity_ids` | array | no | Entity filter and graph expansion. |
| `dedupe_cluster_id` | string | no | Near-duplicate grouping. |
| `trust_tier` | string | no | Trust and publisher filtering. |
| `privacy_boundary` | string | no | Retrieval policy filtering. |
| `quality_status` | string | no | Draft, reviewed, evaluated, deprecated. |
| `text` | string | yes | Embedded text. |
| `embedding` | f32[D] | yes | The vector. |

## Hybrid label/dimension records

Vector results should be joined with:

| Record | Purpose |
|---|---|
| `label_record` | Exact hierarchical, schema.org-style, tenant custom, curated, or generated labels. |
| `dimension_record` | Numeric/categorical features for ranking and filtering. |
| `model_route_record` | Which model assigned a generated label/dimension and why. |

Examples:

- `finance.aml.alert_review`
- `schema_org:HowTo`
- `tenant:risk_tier.high`
- `dimension:evidence_requiredness=0.92`
- `dimension:model_swap_value=0.81`

## Index: `oh_entity`

| Field | Type | Required | Use |
|---|---|---|---|
| `entity_id` | string | yes | Primary key. |
| `entity_type` | string | yes | person, organization, law, occupation, tool, model, dataset, concept, etc. |
| `canonical_name` | string | yes | Display and exact match. |
| `aliases` | array | no | Fuzzy matching and query expansion. |
| `identifiers` | array | no | Registry IDs, URLs, DOIs, CVEs, SOC, O*NET, ESCO, package IDs. |
| `description` | string | no | Embedded text. |
| `embedding` | f32[D] | yes | The vector. |

## Backend mapping

| Backend | Index | Native filters | Notes |
|---|---|---|---|
| Pinecone | namespace per index | metadata filter | Managed. |
| Weaviate | class per index | where-filter | Open source. |
| Qdrant   | collection per index | payload filter | Open source. |
| Chroma   | collection per index | metadata filter | Embedded. |
| pgvector | extension on `knowledge_leaf` + `component` | SQL WHERE | Same DB as canonical store. Recommended default. |

The pgvector option is the recommended default because it keeps both
the canonical relational store and the vector index in one database,
which removes a class of sync bugs at small/medium scale.

## Refresh policy

The vector indexes are derived. They MUST be regenerated whenever a
manifest changes its embedded text. CI runs the rebuild on every
push to `main` and writes a vector-index checksum into `db/vector/checksum.txt`.
