---
name: efficientnet-medical-imaging
description: Train EfficientNet (B0/B3) on medical imaging task; 5-fold CV + TTA at
  inference.
when_to_use: 'Pipeline kind: training_and_serving.'
---

# EfficientNet for medical imaging classification + segmentation

EfficientNet-B0 / B3 backbone + custom head for medical-imaging
competitions: skin lesion (ISIC), brain activity (EEG-as-image),
histopathology (HuBMAP), spine MRI (RSNA Lumbar). Uses timm or
segmentation-models-pytorch for pre-trained checkpoints; 5-fold
CV; image augmentation via albumentations.

Verified by Open Harness Hub mining: cdeotte EfficientNetB0 starter
(1564 votes, HMS Harmful Brain Activity), motono0223 ISIC PyTorch
baseline (794 votes, EfficientNet + timm), hidngnguyna baseline
U-Net + EfficientNet (617 votes, HuBMAP), awsaf49 HMS-HBAC KerasCV
(1733 votes — KerasCV variant of the same shape).

## Task

Train EfficientNet (B0/B3) on medical imaging task; 5-fold CV + TTA at inference.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **augment_and_train** — `processor` → `processor/iterative-revise-loop`
3. **fold_ensemble** — `processor` → `processor/multi-vector-fusion`
4. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/efficientnet-medical-imaging` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.radiology, ai
- Full source manifest: see `references/manifest.yaml`
