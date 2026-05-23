---
license: MIT
tags:
- anonymization
- cross_industry
- open-harness-hub
- pii
- redaction
- safety_gate
- safety_gating
- stable
- text
library_name: open-harness-hub
language:
- en
region:
- cross_industry
---

# Redact PII (text)

<!-- Generated from Open Harness Hub manifest `harness/redact-pii-text` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

Deterministic text PII redactor. Regex + NER patterns + a per-pattern
replacement contract; emits an audit log of (sha256(original), action).
No model call by default.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:


**Industries**: cross_industry
**Capabilities**: anonymization, safety_gating
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### Redact PII in text input

1. load privacy patterns (rule-pack/privacy-pii-text-en)
2. scan input with each pattern
3. replace match → generalized placeholder
4. record sha256(original) and replacement action to audit log

## Privacy boundaries

- **raw_input**: never written to disk; audit log stores hashes only
- **derived_output**: safe to pass to downstream harnesses
- **external_calls**: none

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `no_model` | `none` | local |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{redact-pii-text_open_harness_hub,
  title  = {Redact PII (text)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/redact-pii-text},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub artifact: `harness/redact-pii-text`.
