# Composable success criteria (regex + semantic + LLM-judge + deterministic + tool + composite)

*pattern* · `pattern/composable-success-criteria` · v0.1.0 · beta

Treat success criteria as first-class composable artifacts rather
than a single rubric+threshold check. Six concrete criterion kinds
combine via AND / OR / NOT into arbitrary boolean expressions.
This lets pipelines express realistic acceptance bars without
shoehorning everything into one rubric.

The six kinds:
 1. **rubric**       (legacy) — judge against rubric, require score
                     >= threshold
 2. **regex**        — target text matches (or must not match) a pattern
 3. **semantic**     — embedding similarity covers all required topics
                     above a threshold
 4. **llm_judge**    — adapter-backed LLM grades + threshold compare
 5. **deterministic**— compare a target value to an expected via
                     op (>, >=, <, <=, ==, !=, in, not_in, is_truthy,
                     is_falsy)
 6. **tool_validate**— invoke a tool (JSON schema validator, unit-test
                     runner, IBAN checker, axe-core a11y) and pass
                     iff the tool returns success
 7. **composite**    — AND / OR / NOT of any of the above (nestable)

Each criterion declares a SEVERITY (critical / high / medium / low)
so the aggregate pass-fail can be weighted; the pipeline runner
emits per-criterion results in the trace.

| axis | value |
|---|---|
| industry | cross_industry, ai, compliance |
| capability | verification, evaluation |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



