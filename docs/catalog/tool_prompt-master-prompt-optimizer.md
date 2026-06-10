# Prompt Master prompt optimizer

*tool* · `tool/prompt-master-prompt-optimizer` · v0.1.0 · experimental

Turn a rough intent + a target AI tool into a sharp, token-efficient prompt.
Integration contract for Prompt Master, an MIT-licensed Claude skill that
detects the target tool, extracts intent dimensions, routes to a prompt
template, applies only bounded-effect techniques, and runs a token-efficiency
audit ("every word load-bearing") before returning one clean prompt + a
one-line strategy note.

Reference/integration contract, not a redistribution of upstream content.
Ties directly into this catalog's token-efficiency family
(pattern/input-token-compression, pattern/terse-output-budget) and the
output-format family (pattern/strict-output-format-contract): a good prompt
is the cheapest place to cut tokens and lock output shape. Its catalogue of
prompt anti-patterns and templates is a strong source surface for future
pattern/logic-pack intake (see the prompt-tooling source-surface plan).

| axis | value |
|---|---|
| industry | ai, cross_industry |
| capability | generation, format_conversion, routing |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



