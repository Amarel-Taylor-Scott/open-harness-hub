---
license: MIT
tags:
- beta
- bill-info-ai
- bureaucracy_translation
- evaluation
- hackathon
- humanitarian
- humanitarian.refugee
- open-harness-hub
- redacted-refusal
- synthetic
- verbraucherzentrale
task_categories:
- text-classification
size_categories:
- n<1K
language:
- en
pretty_name: Bill_info AI evaluation set (28 documents)
---

# Bill_info AI evaluation set (28 documents)

<!-- Generated from Open Harness Hub manifest `dataset/bill-info-test-documents` v0.1.0. Edit the source manifest and re-run `python scripts/emit/hf_dataset_card.py`. -->

## Dataset description

The 28-document evaluation set used in Sviatoslav Grabovsky's
Bill_info AI (Gemma 4 Good Hackathon — Impact Track). Mixes:
 - Reddit-sourced real German Inkasso / Mahnung letters (from r/germany)
 - Redacted documents for refusal testing (7 documents)
 - Clear synthetic cases
 - Adversarial edge cases (e.g. synthetic Polish-IBAN scam letter)

Reported metrics on this set:
 - Documents tested: 28
 - Extraction success rate: 96% (27/28)
 - Overall field accuracy: 95.8%
 - Refusal accuracy on redacted documents: 100% (7/7)
 - Average latency (local): 8.5s

The single failure was a synthetic info-letter that triggered a
schema validation error — the safe failure mode. The validation
layer rejected malformed output rather than showing a plausible-
but-invalid analysis.

The original repository is the authoritative source — gold
standards + evaluation harness are reproducible via
`python -m eval.run_eval`.

**Industries**: bureaucracy_translation, humanitarian, humanitarian.refugee
**Capabilities**: evaluation
**Modalities**: image, text
**Freshness**: stable
**Trust boundary**: local

## Provenance

- **origin**: Mixed: Reddit r/germany (real letters, redacted), synthetic clear cases, adversarial edge cases
- **collected_by**: Sviatoslav Grabovsky (Bill_info AI repo)
- **collected_through**: 2026-05
- **license**: MIT for the eval harness + gold standards; individual documents per their original source
- **anonymization**: Real documents are redacted; synthetic documents use plausible-but-fake details

## Croissant

A Croissant 1.0 JSON-LD record is emitted at `dist/croissant/bill-info-test-documents.croissant.json`. HF, Kaggle, and Google Dataset Search index this format automatically.

## Citation

```bibtex
@misc{bill-info-test-documents_open_harness_hub,
  title  = {Bill_info AI evaluation set (28 documents)},
  author = {Open Harness Hub contributors},
  url    = {https://open-harness-hub.dev/dataset/bill-info-test-documents},
  version= {0.1.0},
  year   = {2026}
}
```

License: `MIT`. Hub component: `dataset/bill-info-test-documents`.
