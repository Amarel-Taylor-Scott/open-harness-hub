---
name: longformer-bigbird-ner
description: Train a LongFormer or BigBird token-classification model on long-document
  NER labels.
when_to_use: 'Pipeline kind: training_and_serving.'
---

# Long-document NER with LongFormer / BigBird

Token-classification NER on documents longer than the 512-token
BERT limit. Uses LongFormer (sliding-window attention) or BigBird
(sparse attention) to handle 4096-16384 token inputs. The
dominant Kaggle shape for argumentative-essay-element extraction
+ long-document NER tasks.

Verified by Open Harness Hub mining: cdeotte TensorFlow-LongFormer-NER
(1350 votes, Feedback Prize 2021), abhishek two-longformers-are-better-
than-1 (1323 votes — ensemble of two LongFormers), cdeotte PyTorch-
BigBird-NER (977 votes). 3 of the top kernels on the Feedback
Prize 2021 competition follow this exact shape.

## Task

Train a LongFormer or BigBird token-classification model on long-document NER labels.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **train** — `processor` → `processor/iterative-revise-loop`
3. **ensemble** — `processor` → `processor/multi-vector-fusion`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/longformer-bigbird-ner` v0.1.0
- License: `MIT`
- Industry: ai, education, media
- Full source manifest: see `references/manifest.yaml`
