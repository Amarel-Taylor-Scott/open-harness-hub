# Inject output schema directive

*processor* · `processor/inject-output-schema` · v0.1.0 · beta

Render a target JSON Schema (or Pydantic model) into the prompt as
an instruction the model is asked to follow. Pairs with
`processor/json-schema-repair` on the response side: if the model's
output doesn't conform, the loop processor can re-prompt with the
validation error appended.

Three injection styles:
  - `schema_only`: bare JSON Schema in a fenced code block.
  - `schema_plus_example`: schema + a minimal conforming example.
  - `constrained_grammar_marker`: hints for outlines / xgrammar /
    llama.cpp grammar-constrained decoding.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | format_conversion |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | local |
| license | MIT |



