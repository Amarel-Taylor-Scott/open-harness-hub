# Synthetic GxP validation samples (3 cases)

*dataset* · `dataset/gxp-validation-samples` · v0.1.0 · experimental

Three synthetic GxP-validated-system packets for testing
`pipeline/gxp-validation-review`. Fully synthetic.

Cases:
 - sample-validated-LIMS.json — fully compliant LIMS: audit trail
   on + reviewed quarterly, individual accounts, IQ/OQ/PQ current,
   2-factor signatures, ALCOA+ reviewed. Expected high grade.
 - sample-flagged-MES.json — MES with multiple critical findings:
   audit trail disabled on batch records, shared 'operator-night'
   account, OQ incomplete on a production module, single-factor
   signatures, backup-as-archive, post-hoc backdated alteration.
   Expected many critical findings.
 - sample-mixed-CTMS.json — CTMS mixed: audit trail enabled but
   not reviewed quarterly per risk-based schedule, uncontrolled
   blank CRF templates, batch-approved changes. Mixed signals.

| axis | value |
|---|---|
| industry | pharma, pharma.gxp, healthcare.pharmacy, compliance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



