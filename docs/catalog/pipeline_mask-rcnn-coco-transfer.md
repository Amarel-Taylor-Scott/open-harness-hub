# Mask-RCNN with COCO transfer learning (instance segmentation + detection)

*pipeline* · `pipeline/mask-rcnn-coco-transfer` · v0.1.0 · stable

Mask-RCNN with ResNet-50-FPN backbone, COCO-pretrained weights as
starting checkpoint, fine-tuned on domain-specific instance
segmentation / detection task. Classic transfer-learning recipe for
small-medical-dataset detection (pneumonia, polyps, lesions).

Verified by Open Harness Hub mining: hmendonca Mask-RCNN and COCO
transfer learning LB:0.155 (1194 votes, RSNA Pneumonia Detection
Challenge).

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology, ai |
| capability | classification |
| modality | image |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Fine-tune Mask-RCNN (COCO-pretrained) on domain-specific object detection / instance segmentation.

**pipeline_kind:** `training_and_serving`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `train` | processor | `processor/iterative-revise-loop` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

