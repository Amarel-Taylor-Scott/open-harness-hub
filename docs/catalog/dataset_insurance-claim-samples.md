# Synthetic insurance claim samples

*dataset* · `dataset/insurance-claim-samples` · v0.1.0 · experimental

Two synthetic insurance claims:
 - sample-claim-clean.json — straightforward rear-end auto claim
   with police report, witness, repair estimate. Expected ~0 hits.
 - sample-claim-flagged.json — property fire with coverage
   increase 12 days before loss, no police report, conflicting
   witnesses, photos pre-date loss, 3 prior claims, IFB warrant
   outstanding. Expected many critical hits.

| axis | value |
|---|---|
| industry | insurance, insurance.claims, insurance.fraud, finance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



