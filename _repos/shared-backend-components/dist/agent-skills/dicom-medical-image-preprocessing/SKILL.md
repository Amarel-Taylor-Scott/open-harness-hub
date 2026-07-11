---
name: dicom-medical-image-preprocessing
description: Parse DICOM → normalize HU → window/level → resample → export tensor.
when_to_use: 'Pipeline kind: format_conversion.'
---

# DICOM medical image preprocessing (CT / MRI / X-ray)

Parse DICOM headers (pydicom), normalize Hounsfield units (HU),
window/level adjustment, resample to consistent voxel spacing,
optional lung-segmentation crop, convert to PNG / NumPy / NIfTI
for downstream CNN. Standard Kaggle medical-imaging preprocessing
pipeline.

Verified by OpenHubForAI mining: allunia Pulmonary DICOM
Preprocessing (1249 votes, OSIC Pulmonary Fibrosis Progression),
piantic OSIC Basic EDA (1132 votes — also DICOM preprocessing).

## Task

Parse DICOM → normalize HU → window/level → resample → export tensor.

## Steps

1. **guard** — `rule_pack` → `rule-pack/grep-prompt-injection-heuristics`
2. **preprocess** — `processor` → `processor/iterative-revise-loop`
3. **audit** — `processor` → `processor/audit-trace-emitter`

## Defaults

- **persona**: persona/research-analyst
- **model_adapter**: adapter/ollama-default

## Provenance

- Hub component: `pipeline/dicom-medical-image-preprocessing` v0.1.0
- License: `MIT`
- Industry: healthcare, healthcare.radiology, ai
- Full source manifest: see `references/manifest.yaml`
