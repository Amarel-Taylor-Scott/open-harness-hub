# ESG pillar (E / S / G) deep-dive review harness

*harness* · `harness/esg-pillar-review` · v0.1.0 · experimental

Wraps the ESG pillar deep-dive review flow as a reusable harness.
Reviews ONE pillar (E, S, or G) at SASB + ISSB + TCFD + GRI depth,
cross-checks against greenwashing rule pack, and emits framework-
coded findings with disclosure-code citations.

| axis | value |
|---|---|
| industry | esg, esg.csrd, sustainability, climate, compliance |
| capability | evaluation, verification, retrieval, reasoning |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/esg-pillar-deep-dive`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### disclosure + pillar (E|S|G) → industry SASB topics → framework alignment → greenwashing scan → grade  
*model_call: `required`*

1. classify company into SICS industry
1. fetch SASB industry-specific material topics for pillar
1. fire greenwashing GREP pack
1. RAG against SASB+GRI+TCFD+ISSB pack per material topic
1. judge per esg-pillar-depth-v1 rubric
1. propose specific drafting fixes per gap
1. emit audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every finding cites disclosure code (SASB / ISSB / GRI / TCFD), greenwashing-flag list attached, double-materiality covered for every material topic



## Privacy boundaries

- **raw_input**: stays local; disclosure text is usually public
- **derived_output**: may sync to hub
- **external_calls**: only on explicit user opt-in

