---
license: MIT
tags:
- beta
- cwe
- evaluation
- extraction
- harness
- open-harness-hub
- owasp
- reasoning
- sast
- security
- security.appsec
- software
- text
- verification
library_name: open-harness-hub
pipeline_tag: token-classification
language:
- en
region:
- security
- security.appsec
- software
---

# AppSec Code Audit harness

<!-- Generated from Open Harness Hub manifest `harness/appsec-code-audit` v0.1.0. Do not edit by hand; edit the source manifest and re-run `python scripts/emit/hf_model_card.py`. -->

## Model description

CWE-cite-first AppSec audit harness for source-code review. Detects
secrets-in-code + injection + crypto/auth weaknesses + describes
attack vectors + proposes fixes.

## Intended use

Use this harness as a **wrapping workflow around a model call**. It composes:

- `persona` layer
- `privacy` layer
- `grep` layer
- `rag` layer
- `tools` layer

**Industries**: security, security.appsec, software
**Capabilities**: evaluation, extraction, verification, reasoning
**Modalities**: text
**Trust boundary**: local

## How the harness runs

### code bundle → secrets+vuln GREP → CWE/OWASP citations → grade + fixes

1. structured-to-prose
2. PII / secrets redact
3. code-vulnerabilities GREP (29 CWE-cited rules)
4. RAG against OWASP Top 10 LLM + MITRE ATT&CK
5. judge against code-security-review rubric
6. propose concrete fixes (parameterized query, version bump, alternative library)
7. audit trace

## Privacy boundaries

- **raw_input**: stays local; production secrets must be redacted upstream
- **derived_output**: may sync to hub only after anonymization gate
- **external_calls**: only if model_target.trust_boundary == external AND user opted in

## Compatible model targets (provider-neutral)

| id | transport | trust |
|---|---|---|
| `local_ollama` | `ollama` | local |
| `anthropic_judge` | `anthropic` | external |

## Evaluation

Bench against a hub `benchmark/*` manifest with `python scripts/emit/lm_eval_harness.py` (emits lm-eval-harness YAML) or `python scripts/emit/promptfoo.py` (emits promptfoo config). Both reference the same `rubric/*` and `dataset/*` manifests.

## Risks & limitations

This is a workflow harness, not a trained model. Risk profile depends on the model wired in via the configured `model_target`. See the source manifest for `input_verification` and `output_verification` checks.

## Citation

```bibtex
@misc{appsec-code-audit_open_harness_hub,
  title  = {AppSec Code Audit harness},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/harness/appsec-code-audit},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `harness/appsec-code-audit`.
