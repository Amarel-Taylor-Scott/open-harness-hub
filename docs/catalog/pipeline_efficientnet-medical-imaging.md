# EfficientNet for medical imaging classification + segmentation

*pipeline* · `pipeline/efficientnet-medical-imaging` · v0.1.0 · stable

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

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology, ai |
| capability | classification |
| modality | image |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Train EfficientNet (B0/B3) on medical imaging task; 5-fold CV + TTA at inference.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `augment_and_train` | processor | `processor/iterative-revise-loop` | — |
| 3 | `fold_ensemble` | processor | `processor/multi-vector-fusion` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

