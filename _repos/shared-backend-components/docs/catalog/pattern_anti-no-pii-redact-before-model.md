# Anti-pattern: PII reaches the model without redaction

*pattern* · `pattern/anti-no-pii-redact-before-model` · v0.1.0 · stable

Sending PHI / SSN / financial PII / credentials directly into a hosted LLM call. Even when the model 'doesn't store data,' the data is on the wire + in the provider's transient logs + may be replayed in incident response. Violates HIPAA, GDPR Art 5, GLBA. Not survivable in regulated industries.

| axis | value |
|---|---|
| industry | cross_industry, healthcare, finance, privacy, compliance |
| capability | safety_gating |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



