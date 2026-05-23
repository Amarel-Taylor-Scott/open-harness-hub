# Bill_info AI evaluation set (28 documents)

*dataset* · `dataset/bill-info-test-documents` · v0.1.0 · beta

The 28-document evaluation set used in Sviatoslav Grabovsky's
Bill_info AI (Gemma 4 Good Hackathon — Impact Track). Mixes:
 - Reddit-sourced real German Inkasso / Mahnung letters (from r/germany)
 - Redacted documents for refusal testing (7 documents)
 - Clear synthetic cases
 - Adversarial edge cases (e.g. synthetic Polish-IBAN scam letter)

Reported metrics on this set:
 - Documents tested: 28
 - Extraction success rate: 96% (27/28)
 - Overall field accuracy: 95.8%
 - Refusal accuracy on redacted documents: 100% (7/7)
 - Average latency (local): 8.5s

The single failure was a synthetic info-letter that triggered a
schema validation error — the safe failure mode. The validation
layer rejected malformed output rather than showing a plausible-
but-invalid analysis.

The original repository is the authoritative source — gold
standards + evaluation harness are reproducible via
`python -m eval.run_eval`.

| axis | value |
|---|---|
| industry | bureaucracy_translation, humanitarian, humanitarian.refugee |
| capability | evaluation |
| modality | image, text |
| lifecycle | beta |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



