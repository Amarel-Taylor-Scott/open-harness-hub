# Microsoft Presidio PII detection proxy

*tool* · `tool/presidio-pii-detect` · v0.1.0 · stable

Proxy to Microsoft Presidio Analyzer for PII detection.
Substantially more thorough than `processor/redact-pii-text`
regex baseline — supports 30+ entity types across multiple
languages, ML-backed NER for PERSON names + LOCATION, custom
recognizers, denylist anchors, AnalyzerEngine + RecognizerRegistry.

Pair with `processor/redact-pii-text` for fast first-pass +
Presidio for thorough second-pass on high-stakes outputs.

| axis | value |
|---|---|
| industry | cross_industry, healthcare, finance, insurance, government |
| capability | anonymization, verification |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



