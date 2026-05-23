# DICOM medical image preprocessing (CT / MRI / X-ray)

*pipeline* · `pipeline/dicom-medical-image-preprocessing` · v0.1.0 · stable

Parse DICOM headers (pydicom), normalize Hounsfield units (HU),
window/level adjustment, resample to consistent voxel spacing,
optional lung-segmentation crop, convert to PNG / NumPy / NIfTI
for downstream CNN. Standard Kaggle medical-imaging preprocessing
pipeline.

Verified by Open Harness Hub mining: allunia Pulmonary DICOM
Preprocessing (1249 votes, OSIC Pulmonary Fibrosis Progression),
piantic OSIC Basic EDA (1132 votes — also DICOM preprocessing).

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology, ai |
| capability | format_conversion, extraction |
| modality | image |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Parse DICOM → normalize HU → window/level → resample → export tensor.

**pipeline_kind:** `format_conversion`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `preprocess` | processor | `processor/iterative-revise-loop` | — |
| 3 | `audit` | processor | `processor/audit-trace-emitter` | — |

