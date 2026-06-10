# Synthetic commercial contract samples (3 cases)

*dataset* · `dataset/contract-samples` · v0.1.0 · experimental

Three synthetic commercial contracts for testing
`pipeline/contract-clause-review`. Fully synthetic — no real
contract data.

Cases:
 - sample-msa-clean.json — well-drafted MSA with all critical
   clauses present (capped indemnity with carve-outs, mutual
   liability cap, DPA attached, audit rights, anti-bribery
   warranty, 90-day termination with wind-down, symmetric
   assignment, broad force-majeure). Expected high grade.
 - sample-vendor-flagged.json — aggressive vendor agreement
   with 9 red flags (uncapped indemnity to vendor, $10k
   vendor cap vs unlimited customer liability, IP assignment
   of pre-existing IP, no residuals, no DPA, no audit rights,
   no anti-bribery, 5-day termination, free vendor assignment,
   narrow force-majeure). Expected highly flagged.
 - sample-nda-mixed.json — NDA missing residuals clause + 5y
   term (long but not red-flag). Mixed signals.

| axis | value |
|---|---|
| industry | legal, legal.contract, legal.compliance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



