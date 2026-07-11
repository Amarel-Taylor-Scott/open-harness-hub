# Synthetic radiology report samples (3 cases, fully synthetic)

*dataset* · `dataset/radiology-report-samples` · v0.1.0 · experimental

Three synthetic radiology reports for testing
`pipeline/radiology-report-grading`. Fully synthetic — no real
patient data.

Cases:
 - sample-ct-chest-good.json — well-structured CT chest with
   proper Fleischner-compliant disposition (expected high grade)
 - sample-ct-abdomen-flagged.json — CT abdomen/pelvis with
   MULTIPLE quality issues: unredacted PHI (MRN + DOB), thyroid
   nodule without TI-RADS, adrenal mass without workup, lytic
   lesion with definitive "is a metastasis" without differential,
   sub-solid pulm nodule without Fleischner follow-up, prior
   available but no comparison addressed, impression lacks
   recommendation
 - sample-mammo-screening-mixed.json — mammography with proper
   BI-RADS scoring + recommendation, comparison addressed; good
   case overall

| axis | value |
|---|---|
| industry | healthcare, healthcare.radiology |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



