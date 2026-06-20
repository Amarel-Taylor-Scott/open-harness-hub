---
name: mask-rcnn-coco-transfer
description: Fine-tune Mask-RCNN (COCO-pretrained) on domain-specific object detection
  / instance segmentation.
when_to_use: 'Pipeline kind: training_and_serving.'
---

# Mask-RCNN with COCO transfer learning (instance segmentation + detection)

Mask-RCNN with ResNet-50-FPN backbone, COCO-pretrained weights as
starting checkpoint, fine-tuned on domain-specific instance
segmentation / detection task. Classic transfer-learning recipe for
small-medical-dataset detection (pneumonia, polyps, lesions).

Verified by Open Harness Hub mining: hmendonca Mask-RCNN and COCO
transfer learning LB:0.155 (1194 votes, RSNA Pneumonia Detection
Challenge).

## Task

Fine-tune Mask-RCNN (COCO-pretrained) on domain-specific object detection / instance segmentation.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **train** — `processor` → `processor/iterative-revise-loop`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/mask-rcnn-coco-transfer` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.radiology, ai
- Full source manifest: see `references/manifest.yaml`
