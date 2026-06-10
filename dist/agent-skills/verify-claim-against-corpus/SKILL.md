---
name: verify-claim-against-corpus
description: Given a claim (string) and a corpus (knowledge-pack ref), return a verdict
  in {supports, contradicts, no_evidence}, citations, and a calibrated confidence.
when_to_use: 'Pipeline kind: verify_data.'
---

# Verify Claim Against Corpus

Given a claim and a corpus, return supports / contradicts /
no-evidence with cited passages and a confidence score.

## Task

Given a claim (string) and a corpus (knowledge-pack ref), return a
verdict in {supports, contradicts, no_evidence}, citations, and a
calibrated confidence.

## Steps

1. **retrieve** — `knowledge_pack` → `$.inputs.corpus`
2. **judge** — `harness` → `harness/text-safety-review`

## Defaults

- **persona**: persona/fact-checker
- **model_adapter**: adapter/ollama-default

## Success criteria

- rubric `rubric/verification-v1` threshold 0.7

## Provenance

- Hub artifact: `pipeline/verify-claim-against-corpus` v0.1.0
- License: `MIT`
- Industry: cross_industry, media
- Full source manifest: see `references/manifest.yaml`
