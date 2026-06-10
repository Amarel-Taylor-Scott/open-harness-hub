# Synthetic GDPR DSAR samples

*dataset* · `dataset/gdpr-dsar-samples` · v0.1.0 · experimental

Two synthetic DSARs:
 - clean: identity verified, 14-day response, all Art. 15 fields,
   no-transfer, free of charge. Expected 0 hits.
 - flagged: 2.5 months past deadline, no identity verification,
   no lawful basis, US transfer without SCC, $25 charge, erasure
   refused without basis, special-category without art 9(2),
   breach notification delayed. Expected many critical hits.

| axis | value |
|---|---|
| industry | privacy, privacy.gdpr, privacy.dsar, compliance |
| capability | evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



