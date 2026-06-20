---
license: MIT
tags:
- cwe
- evaluation
- experimental
- open-harness-hub
- sast
- security
- security.appsec
- software
- synthetic
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Synthetic code-review samples (3 cases)
---

# Synthetic code-review samples (3 cases)

<!-- Generated from Open Harness Hub manifest `dataset/code-review-samples` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Three synthetic code bundles for testing
`pipeline/code-security-review`. Fully synthetic — values that
look like AWS keys / JWT / Slack tokens follow the format
documented in AWS / RFC 7519 / Slack docs but are not real
credentials.

Cases:
 - sample-clean-python.json — Flask endpoint with parameterized
   SQL, env-based secrets, hashed passwords, @login_required,
   CSRF-honoring. Expected 0 findings.
 - sample-vulnerable-python.json — Django views with hardcoded
   AWS access key + secret + GitHub PAT + Slack token + private
   key block, SQL string-format injection, MD5 password hashing,
   pickle.loads on request.body, eval of user query, subprocess
   with shell=True + format-string, DEBUG=True. Expected many
   critical findings.
 - sample-mixed-js.json — Node/Express + React with SQL string
   concat (CWE-89), Function() constructor on user input
   (CWE-94), dangerouslySetInnerHTML + innerHTML XSS (CWE-79),
   hardcoded JWT. Expected mixed signals.

**Industries**: security, security.appsec, software
**Capabilities**: evaluation
**Modalities**: text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Fully synthetic — no real credentials or production code
- **collected_by**: Open Harness Hub contributors
- **collected_through**: 2026-05-20
- **license**: MIT
- **anonymization**: fully synthetic; key shapes match docs but are non-functional

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/code-review-samples.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{code-review-samples_open_harness_hub,
  title  = {Synthetic code-review samples (3 cases)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/code-review-samples},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/code-review-samples`.
