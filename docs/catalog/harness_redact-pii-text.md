# Redact PII (text)

*harness* · `harness/redact-pii-text` · v0.1.0 · stable

Deterministic text PII redactor. Regex + NER patterns + a per-pattern
replacement contract; emits an audit log of (sha256(original), action).
No model call by default.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | anonymization, safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| freshness | stable |
| license | MIT |

**Consumes:** `grep_rule`

**Emits:** `audit_template`

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `no_model` | `none` | local | True | True |

## Logic paths

### Redact PII in text input  
*model_call: `none`*

1. load privacy patterns (rule-pack/privacy-pii-text-en)
1. scan input with each pattern
1. replace match → generalized placeholder
1. record sha256(original) and replacement action to audit log

**consumes:** `grep_rule`

**emits:** `audit_template`

**verification:** audit log produced, no original PII in output



## Privacy boundaries

- **raw_input**: never written to disk; audit log stores hashes only
- **derived_output**: safe to pass to downstream harnesses
- **external_calls**: none

