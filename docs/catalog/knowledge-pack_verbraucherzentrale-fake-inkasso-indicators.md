# Verbraucherzentrale Fake-Inkasso indicators (10-criterion taxonomy)

*knowledge-pack* · `knowledge-pack/verbraucherzentrale-fake-inkasso-indicators` · v0.1.0 · beta

Composite educational reference of the Verbraucherzentrale's
published Fake-Inkasso indicators. Used by Sviatoslav Grabovsky's
Bill_info AI to classify German payment demands as legitimate /
suspicious / likely-scam.

Source authority: Verbraucherzentrale Brandenburg Schwarzliste
Inkasso (~191,000 page views in a single year; 400 reported
fake-Inkasso letters in 2022) + sibling Verbraucherzentrale
publications.

Criterion tiers:
- **CRITICAL** (any one alone may justify likely_scam):
   (1) foreign IBAN (non-DE/AT/CH)
   (2) private-person recipient (vs. registered company)
   (3) legal threats (Schufa, Gerichtsvollzieher) in a FIRST letter
   (4) extreme 24-72 hour deadline
- **SUPPORTING** (multiple → suspicious / likely_scam):
   (5) missing regulatory information
   (6) unclear / unnamed creditor
   (7) dubious / surprising fees
   (8) phantom company names
   (9) premium phone numbers
   (10) pressure tactics ("letzte Mahnung" in a first letter)

Three-level classification:
- **legitimate**: no UI change (no false alarms on real Inkasso)
- **suspicious**: yellow advisory + verification step prepended
  to recommendations
- **likely_scam**: red banner + recommendations completely
  overridden to "do not pay, verify via Verbraucherzentrale,
  save as evidence"

| axis | value |
|---|---|
| industry | bureaucracy_translation, bureaucracy_translation.fraud_screening, humanitarian, humanitarian.refugee |
| capability | retrieval, classification, verification |
| modality | text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | dated |
| license | CC-BY-4.0 |



