# Supplier disclosure pack schema (canonical input shape)

*dataset* · `dataset/supplier-disclosure-pack-schema` · v0.1.0 · experimental

Canonical input shape that `pipeline/supplier-policy-grading` and
`pipeline/deep-tier-supplier-audit` accept as the supplier
disclosure pack. Records the JSON Schema of the supplier-submitted
artifact so compliance teams can prepare their data once and feed
it into any pipeline in the ESG vertical.

The pack covers: supplier identity + tier + UBO + geography + sector
+ policy texts + self-assessment + grievance summary + audit reports
+ GHG inventory + EUDR-relevant commodities geolocation + worker
representation. Each section is OPTIONAL — pipelines flag missing
required-for-jurisdiction sections rather than fail.

Includes 3 sample disclosure packs for testing:
 - sample-T1-tech-supplier-good.json (a well-disclosed T1 supplier)
 - sample-T3-textile-mae-sot-flagged.json (a T3 supplier with
   forced-labor + corridor red flags)
 - sample-T2-agri-paraguay-mixed.json (a T2 soy supplier with
   mixed signals: strong S, weak E around deforestation)

| axis | value |
|---|---|
| industry | esg, supply_chain, compliance |
| capability | evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



