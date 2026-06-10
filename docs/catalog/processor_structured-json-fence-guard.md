# Structured JSON fence guard (output coercion + safe parse)

*processor* · `processor/structured-json-fence-guard` · v0.1.0 · stable

Forces the model to wrap its structured output in a ```json ... ``` fence by
injecting a prompt prefix/suffix, then safely extracts and validates the JSON
block. Prevents the common failure where prose sanitisers (markdown strippers,
TTS pre-processors) remove surrounding braces or brackets, producing broken
output. Falls back to regex extraction if the fence is malformed; raises a
structured error if the extracted block fails schema validation.

CAPABILITY LIFT (structural / deterministic): a bare model call does not
guarantee output structure — the model samples, and even with JSON-mode
instructions, prose-mode middleware or downstream strippers can corrupt the
output. This processor is a deterministic verifier: it either returns a
valid JSON object or raises a typed error. The lift is
structural (deterministic_guarantee) because the model sampler cannot
promise parse success — only a validator outside the model can.
lift_reason: deterministic_guarantee; mechanism: rigid_grammar.

| axis | value |
|---|---|
| industry | ai, software, cross_industry |
| capability | format_conversion, verification, safety_gating |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



