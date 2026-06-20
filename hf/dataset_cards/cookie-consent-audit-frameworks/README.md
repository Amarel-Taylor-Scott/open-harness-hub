---
license: CC-BY-4.0
tags:
- cookie-consent-audit
- expansion-v5
- experimental
- marketing_ops.consent
- open-harness-hub
- privacy.gdpr
- retrieval
- verification
task_categories:
- text-classification
- text-retrieval
size_categories:
- n<1K
language:
- en
pretty_name: Cookie Consent Audit frameworks
---

# Cookie Consent Audit frameworks

<!-- Generated from Open Harness Hub manifest `knowledge-pack/cookie-consent-audit-frameworks` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

Composite benchmark and review context pack for cookie consent audit workflows.

**Industries**: privacy.gdpr, marketing_ops.consent
**Capabilities**: retrieval, verification
**Modalities**: text
**Freshness**: dated
**Trust boundary**: local

## Content types (leaf vocabulary)

- `rag_doc`
- `checklist`
- `control_summary`
- `evidence_matrix`
- `benchmark_context`

## Files

| path | format | schema |
|---|---|---|
| `data/cookie-consent-audit/frameworks.jsonl` | jsonl | — |

## Provenance

- **sources**: Cookie Consent Audit control checklist, Cookie Consent Audit evidence matrix, Cookie Consent Audit escalation playbook, Cookie Consent Audit benchmark context
- **collected_through**: 2026-05-24
- **collected_by**: Open Harness Hub contributors
- **anonymization**: composite educational summaries only

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/cookie-consent-audit-frameworks.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{cookie-consent-audit-frameworks_open_harness_hub,
  title  = {Cookie Consent Audit frameworks},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/knowledge-pack/cookie-consent-audit-frameworks},
  version= {0.1.0},
  year   = {2026}
}
```

License: `CC-BY-4.0`. Hub component: `knowledge-pack/cookie-consent-audit-frameworks`.
