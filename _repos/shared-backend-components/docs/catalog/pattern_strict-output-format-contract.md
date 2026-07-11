# Strict output-format contract (request, constrain, and validate-or-repair a response shape)

*pattern* · `pattern/strict-output-format-contract` · v0.1.0 · beta

Make the model return a response in a specific, declared shape — strict JSON
(against a schema), Markdown, a table, CSV, a fixed character/word count, or
a typed envelope — and guarantee the shape with a validator rather than
hoping the prompt was obeyed.

"Ask nicely in the prompt" is not a contract: models drift, add prose around
JSON, or violate the schema under load. This pattern treats the output shape
as a contract enforced at three layers, strongest first:

 1. **constrained decoding** (best) — grammar / JSON-schema constrained
    generation or provider function-calling, so invalid tokens cannot be
    produced (Outlines, guidance, llama.cpp GBNF, OpenAI structured outputs).
 2. **format instruction + exemplar** — render the target schema and a
    worked example into the prompt as a fallback when the runtime cannot
    constrain decoding.
 3. **validate-or-repair** (always) — parse and validate the output against
    the contract; on failure, run a bounded repair (re-ask with the error,
    or deterministic fix-up), and reject after N attempts.

Contracts supported: JSON-schema object, enum/single-value, Markdown
section skeleton, table/CSV with a column spec, and an exact char/word
budget. The validator's pass/fail and any repair attempts go in the trace.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | format_conversion, verification, generation |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



