---
name: unet-segmentation-tta
description: Train U-Net (with encoder backbone) on medical image segmentation; D4
  TTA at inference; ensemble folds.
when_to_use: 'Pipeline kind: training_and_serving.'
---

# U-Net medical segmentation with albumentations + TTA

U-Net (often with EfficientNet/ResNet/SEResNeXt encoder via segmentation_
models_pytorch) for medical image segmentation. Standard Kaggle shape:
5-fold CV + albumentations augmentation (flip / shift / scale / rotate
/ elastic) + Test-Time Augmentation (TTA) at inference (D4 horizontal/
vertical flip + 90° rotations averaged).

Verified by Open Harness Hub mining: awsaf49 UWMGI Unet Train PyTorch
(1473 votes, UW-Madison GI Tract) + UWMGI 2.5D Infer PyTorch (1092
votes), hidngnguyna baseline U-Net (617 votes, HuBMAP), corochann
SEResNeXt (823 votes, Bengali). 5+ kernels.

## Task

Train U-Net (with encoder backbone) on medical image segmentation; D4 TTA at inference; ensemble folds.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **augment_and_train** — `processor` → `processor/iterative-revise-loop`
3. **tta_inference** — `processor` → `processor/multi-vector-fusion`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/unet-segmentation-tta` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.radiology, ai
- Full source manifest: see `references/manifest.yaml`
