---
name: redact-pii-text
description: Deterministic text PII redactor. Regex + NER patterns + a per-pattern
  replacement contract; emits an audit log of (sha256(original), action). No model
  call by default.
when_to_use: Use when the user needs anonymization. Use when the user needs safety_gating.
---

# Redact PII (text)

Deterministic text PII redactor. Regex + NER patterns + a per-pattern
replacement contract; emits an audit log of (sha256(original), action).
No model call by default.

## Redact PII in text input

*model_call:* `none`

**Steps**

1. load privacy patterns (rule-pack/privacy-pii-text-en)
2. scan input with each pattern
3. replace match → generalized placeholder
4. record sha256(original) and replacement action to audit log

**Verification**

- audit log produced
- no original PII in output

## Privacy boundaries

- **raw_input**: never written to disk; audit log stores hashes only
- **derived_output**: safe to pass to downstream harnesses
- **external_calls**: none

## Model targets

| id | transport | trust | required | default |
|---|---|---|---|---|
| `no_model` | `none` | local | True | True |

## Provenance

- Hub artifact: `harness/redact-pii-text` v0.1.0
- License: `MIT`
- Lifecycle: `stable`
- Full source manifest: see `references/manifest.yaml`
