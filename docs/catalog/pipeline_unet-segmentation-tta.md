# U-Net medical segmentation with albumentations + TTA

*pipeline* · `pipeline/unet-segmentation-tta` · v0.1.0 · stable

U-Net (often with EfficientNet/ResNet/SEResNeXt encoder via segmentation_
models_pytorch) for medical image segmentation. Standard Kaggle shape:
5-fold CV + albumentations augmentation (flip / shift / scale / rotate
/ elastic) + Test-Time Augmentation (TTA) at inference (D4 horizontal/
vertical flip + 90° rotations averaged).

Verified by Open Harness Hub mining: awsaf49 UWMGI Unet Train PyTorch
(1473 votes, UW-Madison GI Tract) + UWMGI 2.5D Infer PyTorch (1092
votes), hidngnguyna baseline U-Net (617 votes, HuBMAP), corochann
SEResNeXt (823 votes, Bengali). 5+ kernels.

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology, ai |
| capability | classification |
| modality | image |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Train U-Net (with encoder backbone) on medical image segmentation; D4 TTA at inference; ensemble folds.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `augment_and_train` | processor | `processor/iterative-revise-loop` | — |
| 3 | `tta_inference` | processor | `processor/multi-vector-fusion` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

