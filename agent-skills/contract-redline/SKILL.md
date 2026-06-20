---
name: contract-redline
description: Playbook-cite-first harness for commercial contract review. Surfaces
  red-flag clauses + proposes concrete redline language + cites the playbook clause
  family for every finding.
when_to_use: Use when the user needs evaluation. Use when the user needs extraction.
  Use when the user needs verification. Use when the user needs reasoning. Particularly
  relevant for legal. Particularly relevant for legal.contract. Particularly relevant
  for legal.compliance.
---

# Contract Clause Redlining harness

Playbook-cite-first harness for commercial contract review. Surfaces
red-flag clauses + proposes concrete redline language + cites the
playbook clause family for every finding.

## Applied layers

- `persona`
- `privacy`
- `grep`
- `rag`
- `tools`

## contract → red flags → playbook citations → redline proposals

*model_call:* `required`

**Steps**

1. structured-to-prose
2. PII redact
3. contract-red-flags GREP
4. RAG against contract-law-clauses playbook
5. judge against contract-review-quality rubric
6. emit suggested redline language per finding
7. audit trace

**Verification**

- every red-flag has redline + playbook citation + severity
- no PII / privileged content in output
- no definitive 'unenforceable' assertions

## Privacy boundaries

- **raw_input**: stays local; subject to attorney-client privilege
- **derived_output**: may sync to hub only with explicit privilege waiver
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `local_ollama` | `ollama` | local | False | True |
| `anthropic_opus` | `anthropic` | external | False | False |

## Provenance

- Hub component: `harness/contract-redline` v0.1.0
- License: `MIT`
- Lifecycle: `beta`
- Full source manifest: see `references/manifest.yaml`
