---
name: esg-pillar-review
description: Wraps the ESG pillar deep-dive review flow as a reusable harness. Reviews
  ONE pillar (E, S, or G) at SASB + ISSB + TCFD + GRI depth, cross-checks against
  greenwashing rule pack, and emits framework- coded findings with disclosure-code
  citations.
when_to_use: Use when the user needs evaluation. Use when the user needs verification.
  Use when the user needs retrieval. Use when the user needs reasoning. Particularly
  relevant for esg. Particularly relevant for esg.csrd. Particularly relevant for
  sustainability. Particularly relevant for climate. Particularly relevant for compliance.
---

# ESG pillar (E / S / G) deep-dive review harness

Wraps the ESG pillar deep-dive review flow as a reusable harness.
Reviews ONE pillar (E, S, or G) at SASB + ISSB + TCFD + GRI depth,
cross-checks against greenwashing rule pack, and emits framework-
coded findings with disclosure-code citations.

## Applied layers

- `persona`
- `grep`
- `rag`
- `tools`

## disclosure + pillar (E|S|G) → industry SASB topics → framework alignment → greenwashing scan → grade

*model_call:* `required`

**Steps**

1. classify company into SICS industry
2. fetch SASB industry-specific material topics for pillar
3. fire greenwashing GREP pack
4. RAG against SASB+GRI+TCFD+ISSB pack per material topic
5. judge per esg-pillar-depth-v1 rubric
6. propose specific drafting fixes per gap
7. emit audit trace

**Verification**

- every finding cites disclosure code (SASB / ISSB / GRI / TCFD)
- greenwashing-flag list attached
- double-materiality covered for every material topic

## Privacy boundaries

- **raw_input**: stays local; disclosure text is usually public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/esg-pillar-review` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
