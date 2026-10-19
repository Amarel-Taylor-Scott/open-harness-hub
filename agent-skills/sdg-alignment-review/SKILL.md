---
name: sdg-alignment-review
description: Wraps the SDG alignment-claim review flow as a reusable harness. Classifies
  free-text claims to candidate SDG goals via the classifier rule pack, drills to
  target/indicator level via RAG against the SDG knowledge pack, checks counter-targets,
  and grades alignment quality.
when_to_use: Use when the user needs evaluation. Use when the user needs verification.
  Use when the user needs retrieval. Use when the user needs classification. Use when
  the user needs reasoning. Particularly relevant for esg. Particularly relevant for
  sustainability. Particularly relevant for nonprofit. Particularly relevant for government.
  Particularly relevant for humanitarian.
---

# UN SDG alignment-claim review harness

Wraps the SDG alignment-claim review flow as a reusable harness.
Classifies free-text claims to candidate SDG goals via the
classifier rule pack, drills to target/indicator level via RAG
against the SDG knowledge pack, checks counter-targets, and grades
alignment quality.

## Applied layers

- `persona`
- `classifier`
- `rag`
- `tools`

## claim text → candidate SDGs → target+indicator drilldown → counter-target check → grade

*model_call:* `required`

**Steps**

1. classify each claim into candidate SDG goals
2. RAG against SDG pack to identify exact targets + indicators
3. check counter-target risks via target-interactions matrix
4. assess additionality + geographic-temporal fit
5. judge per sdg-alignment-v1 rubric
6. propose strengthening edits per gap
7. emit audit trace

**Verification**

- every claim has target + indicator code OR explicit no-UN-indicator note
- counter-target check present for every claim
- additionality narrative present (may be 'unverified')

## Privacy boundaries

- **raw_input**: stays local
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/sdg-alignment-review` v0.1.0
- License: `MIT`
- Lifecycle: `experimental`
- Full source manifest: see `references/manifest.yaml`
