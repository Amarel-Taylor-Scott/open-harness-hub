# SWIFT BIC validator + BIC → bank metadata

*tool* · `tool/swift-bic-validator` · v0.1.0 · stable

Validate an 8 or 11-character SWIFT BIC (Bank Identifier Code) and
resolve it to the bank's name + country + city. Used by payment-
processing + KYC + AML pipelines for counterparty bank
identification.

Offline validation uses the SWIFT BIC structure rules (bank code
4 chars + country code 2 chars ISO 3166 + location code 2 chars +
optional branch code 3 chars). Online lookup against bundled
SWIFT BIC directory snapshot (refresh quarterly).

| axis | value |
|---|---|
| industry | finance, finance.kyc, finance.aml |
| capability | verification, extraction |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



