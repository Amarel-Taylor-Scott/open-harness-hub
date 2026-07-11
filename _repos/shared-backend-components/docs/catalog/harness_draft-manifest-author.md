# Draft-manifest authoring harness (knowledge-node → manifest)

*harness* · `harness/draft-manifest-author` · v0.1.0 · experimental

Wraps the manifest-authoring flow as a reusable harness. Reads a
structured knowledge node (from any walker: Wikipedia / USC /
APQC PCF / NIST framework / etc.), drafts one or more catalog
manifests, runs them through the YAML emitter + validator loop,
and produces ready-for-curator-review drafts in `catalog/_inbox/`.

Includes self-revise loop: on validation failure, the harness
receives the structured error report and revises the draft up to
N_max_revisions times before failing the node.

| axis | value |
|---|---|
| industry | software, software.docs, ai, cross_industry |
| capability | generation, extraction, verification, classification, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | volatile |
| license | MIT |

**Consumes:** `persona_block`, `rag_doc`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/external-knowledge-to-manifests`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### knowledge node → proposed manifest types → draft YAML → validate → revise loop → write _inbox  
*model_call: `required`*

1. classify node into proposed manifest target types (1-3)
1. RAG against manifest-shapes-and-conventions pack for canonical examples
1. draft each proposed manifest as a Python dict
1. self-grade against draft-manifest-quality-v1 rubric
1. emit each draft via draft-manifest-yaml-emitter
1. on validation failure: revise (max 3 attempts) using the structured error report
1. on success: write to catalog/_inbox/; emit audit trace

**consumes:** `persona_block`, `rag_doc`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every emitted draft validates against its schema, every draft has attribution if node is from external source, no draft has slug collision with live catalog, no draft uses VOCAB-CHANGE-NEEDED values without flagging



## Privacy boundaries

- **raw_input**: stays local; source content is usually public
- **derived_output**: draft manifests stay in _inbox/ until curator promotes
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

