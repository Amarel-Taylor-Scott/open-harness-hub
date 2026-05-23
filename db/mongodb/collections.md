# MongoDB collections — Open Harness Hub

The document-store mapping uses one collection per artifact `type`. The
`_id` of every document is the artifact `id`. The full manifest is the
document body.

| Collection | Document body |
|---|---|
| `harnesses`        | full harness manifest |
| `pipelines`        | full pipeline manifest |
| `benchmarks`       | full benchmark manifest |
| `rule_packs`       | full rule-pack manifest |
| `knowledge_packs`  | full knowledge-pack manifest |
| `logic_packs`      | full logic-pack manifest |
| `tools`            | full tool manifest |
| `personas`         | full persona manifest |
| `adapters`         | full adapter manifest |
| `rubrics`          | full rubric manifest |
| `datasets`         | full dataset manifest |
| `schemas`          | JSON Schema (raw) |

Each document also carries materialized `refs` for graph queries:

```json
{
  "_id": "pipeline/research-entity",
  "type": "pipeline",
  "name": "Research Entity",
  "...": "<full manifest>",
  "refs": [
    { "role": "step_ref",     "ref": "harness/redact-pii-text" },
    { "role": "step_ref",     "ref": "tool/web-search"          },
    { "role": "step_ref",     "ref": "harness/text-safety-review"},
    { "role": "rubric",       "ref": "rubric/research-entity-v1" },
    { "role": "default_persona", "ref": "persona/research-analyst"}
  ]
}
```

Suggested indexes (per collection):

```js
db.harnesses.createIndex({ "industry": 1 });
db.harnesses.createIndex({ "capability": 1 });
db.harnesses.createIndex({ "modality": 1 });
db.harnesses.createIndex({ "lifecycle": 1 });
db.harnesses.createIndex({ "tags": 1 });
db.harnesses.createIndex({ "name": "text", "description": "text", "tags": "text" });
```

A leaf collection holds the individual rules / knowledge leaves with the
pack-id as the parent foreign key — `rules` and `knowledge_leaves`.
