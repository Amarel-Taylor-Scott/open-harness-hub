# Terse-output budget (cap and shrink what the model writes)

*pattern* · `pattern/terse-output-budget` · v0.1.0 · beta

Constrain output length so the model returns only what the task needs,
cutting output tokens — usually the more expensive side of a call — without
losing correctness.

Models default to verbose, hedged, explanatory prose. For most production
tasks (classification, extraction, routing, structured answers) that prose
is pure cost. This pattern sets an explicit output budget and shapes the
response policy to fit it.

Budget levers (compose as needed):
 1. **hard cap** — max_tokens / max output chars enforced by the runtime.
 2. **answer-only response policy** — instruction + format that forbids
    preamble, restatement, and meta-commentary.
 3. **decoding profile** — stop sequences and (where available) length
    penalty tuned to end the response promptly.
 4. **summarize-then-return** — for tasks that need reasoning, think
    internally / in a scratch field, return only the conclusion.
 5. **field-scoped output** — return just the requested fields, not a
    narrative around them.

Pair every budget with a rubric or success criterion so brevity never
silently drops required content; emit tokens_out_before/after in the trace.

| axis | value |
|---|---|
| industry | cross_industry, ai |
| capability | generation, governance, routing |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | mixed |
| license | CC-BY-4.0 |



