# Statute / regulation clarity review harness

*harness* · `harness/statute-clarity-review` · v0.1.0 · experimental

Wraps the statute-clarity review flow as a reusable harness with
persona + GREP + RAG + tools layers. Targets local-Ollama or
Anthropic/OpenAI for the judge model arm. Emits citation-first
findings tagged with canon name, severity, suggested redline, and
cited authority.

| axis | value |
|---|---|
| industry | legal, legal.compliance, government, government.regulatory |
| capability | evaluation, verification, retrieval, reasoning |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**Contributes to:** `pipeline/statute-clarity-review`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_judge` | `anthropic` | external | False | False |

## Logic paths

### statute text → ambiguity flags → canon analysis → grade + redlines  
*model_call: `required`*

1. normalize statute text + extract section structure
1. fire ambiguity GREP pack
1. RAG against canons-of-construction pack
1. judge per statute-clarity-v1 rubric
1. propose smallest-fix redlines per finding
1. emit audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`, `extracted_fact`

**verification:** every finding cites canon name OR drafting-failure category, every finding quotes the exact text being analyzed, every finding has a suggested redline OR explicit 'requires policy decision'



## Privacy boundaries

- **raw_input**: stays local to the running pipeline
- **derived_output**: may sync to hub if statute text is public-law
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

