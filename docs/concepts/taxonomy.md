# Taxonomy

The canonical taxonomy is in [`taxonomy/SPEC.md`](../reference/spec.md).
This page summarizes it.

## Artifact types

| Type | Layer | Purpose |
|---|---|---|
| `knowledge-pack` | 1 | Typed bundle of facts. |
| `logic-pack`     | 1 | Typed bundle of behavior - prompts, schemas, policies. |
| `rule-pack`      | 1 | Bundle of one rule family (GREP / RAG / classifier / heuristic / online-search / …). |
| `tool`           | 1 | Function-call definition. |
| `persona`        | 1 | Role / system-prompt frame. |
| `adapter`        | 1 | Provider-neutral model transport. |
| `rubric`         | 1 | Evaluation contract. |
| `dataset`        | * | Typed collection of inputs/outputs/labels. |
| `schema`         | * | Reusable typed I/O contract. |
| `harness`        | 2 | Named, repeatable workflow around a model or trust boundary. |
| `pipeline`       | 3 | DAG of harnesses + rule packs + tools that completes a task. |
| `benchmark`      | 4 | Pipeline run against a labeled set with a rubric. |

## Rule pack families

| Family | What |
|---|---|
| `grep` | Regex rules with severity + category. |
| `glob` | Filepath or text glob patterns. |
| `classifier` | Labeled-example rules for lightweight classifiers. |
| `heuristic` | Deterministic `condition → action` rules. |
| `rag` | Corpus + index + retrieval policy. |
| `citation` | Citation graph between RAG docs. |
| `online_search` | Allowlist / blocklist / per-source policy + sanitization + freshness. |
| `privacy` | PII detection + redaction recipes. |
| `schema` | JSON Schemas / Pydantic equivalents enforced at I/O boundaries. |
| `routing` | Input → downstream artifact dispatch. |

## Cross-cutting vocabularies

- **Industry** - open list. Sub-industries are dot-separated
  (`healthcare.radiology`, `finance.aml`).
- **Capability** - what the artifact does
  (classification / extraction / retrieval / safety_gating / …).
- **Modality** - text / image / audio / video / code / structured / tabular.
- **Trust boundary** - local / hub / external / mixed.
- **Lifecycle** - experimental / beta / stable / deprecated.
- **Freshness** - stable / volatile / dated.
- **License** - SPDX identifiers.

See [vocabularies](../reference/vocabularies.md) for the controlled
lists.
