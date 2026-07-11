# UN SDG alignment-claim review harness

*harness* · `harness/sdg-alignment-review` · v0.1.0 · experimental

Wraps the SDG alignment-claim review flow as a reusable harness.
Classifies free-text claims to candidate SDG goals via the
classifier rule pack, drills to target/indicator level via RAG
against the SDG knowledge pack, checks counter-targets, and grades
alignment quality.

| axis | value |
|---|---|
| industry | esg, sustainability, nonprofit, government, humanitarian |
| capability | evaluation, verification, retrieval, classification, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `classifier_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/sdg-alignment-assessment`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### claim text → candidate SDGs → target+indicator drilldown → counter-target check → grade  
*model_call: `required`*

1. classify each claim into candidate SDG goals
1. RAG against SDG pack to identify exact targets + indicators
1. check counter-target risks via target-interactions matrix
1. assess additionality + geographic-temporal fit
1. judge per sdg-alignment-v1 rubric
1. propose strengthening edits per gap
1. emit audit trace

**consumes:** `classifier_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every claim has target + indicator code OR explicit no-UN-indicator note, counter-target check present for every claim, additionality narrative present (may be 'unverified')



## Privacy boundaries

- **raw_input**: stays local
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

