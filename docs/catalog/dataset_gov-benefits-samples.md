# Synthetic SNAP application samples

*dataset* · `dataset/gov-benefits-samples` · v0.1.0 · experimental

Two synthetic SNAP applications:
 - sample-snap-app-clean.json — 3-person household with minor
   children, $1850 gross income (below 130% poverty for HH of 3),
   ID + paystub + residence + school enrollment all verified.
   Expected ~0 hits.
 - sample-snap-app-flagged.json — 1-person household with
   undisclosed adult, $4800 gross income (over threshold),
   unreported self-employment, $6800 in bank (over resource limit),
   ABAWD with only 12 hours/month, active case in another state,
   outstanding fraud warrant. Expected many hits.

| axis | value |
|---|---|
| industry | government, government.benefits |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



