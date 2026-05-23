# USPS address validation

*tool* · `tool/usps-address-validator` · v0.1.0 · stable

Proxy to the USPS Address Information API. Given a US address,
returns: standardized form, ZIP+4, deliverability, DPV (Delivery
Point Validation) status, RDI (Residential Delivery Indicator).
Use to confirm an address is mailable before accepting it into a
customer / shipping record.

Requires USPS_USER_ID env var (free tier: 5 requests/sec).

| axis | value |
|---|---|
| industry | cross_industry, retail, finance, government |
| capability | verification |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | external |
| license | MIT |



