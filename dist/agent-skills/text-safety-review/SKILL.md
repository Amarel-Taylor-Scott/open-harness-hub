---
name: text-safety-review
description: A general-purpose text harness that composes persona + GREP + RAG + tools
  + (optional) online grounding around a model call. Designed to produce cited, bounded,
  citation-first responses.
when_to_use: Use when the user needs safety_gating. Use when the user needs retrieval.
  Use when the user needs reasoning. Use when the user needs dialogue.
---

# Text Safety Review

A general-purpose text harness that composes persona + GREP +
RAG + tools + (optional) online grounding around a model call.
Designed to produce cited, bounded, citation-first responses.

## Applied layers

- `persona`
- `grep`
- `rag`
- `tools`

## Prompt → grounded cited response

*model_call:* `required`

**Steps**

1. normalize chat messages
2. redact PII (via rule-pack/privacy-pii-text-en)
3. fire GREP rules; record severity hits
4. retrieve top-k RAG with BM25, optional dense, RRF merge
5. expand retrieved docs with 1-hop citation graph
6. compose persona + retrieved context + tool registry
7. call model
8. stream response + per-layer trace
9. verify every claim cited

**Verification**

- layer trace recorded
- citation coverage check
- rubric score >= 0.6

## Privacy boundaries

- **raw_input**: stays local to the running harness process
- **derived_output**: may be synced to the hub only after anonymization gate
- **external_calls**: only when model_target.trust_boundary == 'external' AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `openai_compatible` | `openai_compatible` | external | False | False |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub artifact: `harness/text-safety-review` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
