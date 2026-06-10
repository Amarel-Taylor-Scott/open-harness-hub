# Template field gem — parse {{field}} placeholders and drive one-shot agentic tasks

*processor* · `processor/template-field-gem` · v0.1.0 · stable

Pre-LLM processor implementing the Trove "gem" (no-code local agentic task)
pattern. Parses a prompt template containing {{field_name}} placeholders,
resolves the fields from a user-provided context object, and assembles the
final prompt ready for a one-shot LLM call. Supports:

  - Simple scalar substitution: {{user_name}}, {{date}}, {{task}}
  - Conditional fields: {{?optional_field}} (omitted if not present in context)
  - Iteration fields: {{each:items}} ... {{/each}} (repeats block per item)
  - Nested path resolution: {{user.address.city}}

A "gem" in Trove is a prompt template + context object that together define
a complete, self-contained agentic task — no code required. This processor
is the engine that activates a gem: it takes the raw template and context,
resolves all placeholders, validates that required fields are present, and
emits the assembled prompt. If required fields are missing it raises a
structured error listing the missing field names, not a model hallucination.

CAPABILITY LIFT (structural): without a template engine, each agentic task
requires custom code or manual prompt assembly. The model cannot reliably
assemble multi-field prompts from a context object without hallucinating
field values or omitting required fields. A deterministic template engine
guarantees exact field substitution. lift_reason: deterministic_guarantee;
mechanism: sub_token (string interpolation is below the token boundary —
the model cannot do it reliably).

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | agent_loop, format_conversion, verification |
| modality | text, structured |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



