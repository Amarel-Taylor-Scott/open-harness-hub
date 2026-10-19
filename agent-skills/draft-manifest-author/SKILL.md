---
name: draft-manifest-author
description: 'Wraps the manifest-authoring flow as a reusable harness. Reads a structured
  knowledge node (from any walker: Wikipedia / USC / APQC PCF / NIST framework / etc.),
  drafts one or more catalog manifests, runs them through the YAML emitter + validator
  loop, and produces ready-for-curator-review drafts in `catalog/_inbox/`. Includes
  self-revise loop: on validation failure, the harness receives the structured error
  report and revises the draft up to N_max_revisions times before failing the node.'
when_to_use: Use when the user needs generation. Use when the user needs extraction.
  Use when the user needs verification. Use when the user needs classification. Use
  when the user needs reasoning. Particularly relevant for software. Particularly
  relevant for software.docs. Particularly relevant for ai.
---

# Draft-manifest authoring harness (knowledge-node → manifest)

Wraps the manifest-authoring flow as a reusable harness. Reads a
structured knowledge node (from any walker: Wikipedia / USC /
APQC PCF / NIST framework / etc.), drafts one or more catalog
manifests, runs them through the YAML emitter + validator loop,
and produces ready-for-curator-review drafts in `catalog/_inbox/`.

Includes self-revise loop: on validation failure, the harness
receives the structured error report and revises the draft up to
N_max_revisions times before failing the node.

## Applied layers

- `persona`
- `rag`
- `tools`

## knowledge node → proposed manifest types → draft YAML → validate → revise loop → write _inbox

*model_call:* `required`

**Steps**

1. classify node into proposed manifest target types (1-3)
2. RAG against manifest-shapes-and-conventions pack for canonical examples
3. draft each proposed manifest as a Python dict
4. self-grade against draft-manifest-quality-v1 rubric
5. emit each draft via draft-manifest-yaml-emitter
6. on validation failure: revise (max 3 attempts) using the structured error report
7. on success: write to catalog/_inbox/; emit audit trace

**Verification**

- every emitted draft validates against its schema
- every draft has attribution if node is from external source
- no draft has slug collision with live catalog
- no draft uses VOCAB-CHANGE-NEEDED values without flagging

## Privacy boundaries

- **raw_input**: stays local; source content is usually public
- **derived_output**: draft manifests stay in _inbox/ until curator promotes
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/draft-manifest-author` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
