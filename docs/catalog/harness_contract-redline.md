# Contract Clause Redlining harness

*harness* · `harness/contract-redline` · v0.1.0 · beta

Playbook-cite-first harness for commercial contract review. Surfaces
red-flag clauses + proposes concrete redline language + cites the
playbook clause family for every finding.

| axis | value |
|---|---|
| industry | legal, legal.contract, legal.compliance |
| capability | evaluation, extraction, verification, reasoning |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**Emits:** `reasoning_step`, `context_snippet`

**Contributes to:** `pipeline/contract-clause-review`, `pipeline/full-vendor-due-diligence`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_opus` | `anthropic` | external | False | False |

## Logic paths

### contract → red flags → playbook citations → redline proposals  
*model_call: `required`*

1. structured-to-prose
1. PII redact
1. contract-red-flags GREP
1. RAG against contract-law-clauses playbook
1. judge against contract-review-quality rubric
1. emit suggested redline language per finding
1. audit trace

**consumes:** `grep_rule`, `rag_doc`, `persona_block`, `response_policy`

**emits:** `reasoning_step`, `context_snippet`

**verification:** every red-flag has redline + playbook citation + severity, no PII / privileged content in output, no definitive 'unenforceable' assertions



## Privacy boundaries

- **raw_input**: stays local; subject to attorney-client privilege
- **derived_output**: may sync to hub only with explicit privilege waiver
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

