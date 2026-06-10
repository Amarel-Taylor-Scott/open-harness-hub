# Personal code review with preference layer

*pipeline* · `pipeline/personal-code-review-with-preferences` · v0.1.0 · experimental

Review a code diff through the user's personal-preference layer. Loads the user's preferences pack, runs the personal-coding-reviewer persona, gates output against the personal-style rule pack, refuses to ship review comments that contain disallowed idioms.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | evaluation, safety_gating |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Review a code diff applying the reviewer's personal preferences.

**pipeline_kind:** `review`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `load_preferences` | rule_pack | `rule-pack/hybrid-retrieval-policy` | - |
| 2 | `structured_to_prose` | processor | `processor/structured-to-prose` | - |
| 3 | `review_with_persona` | processor | `processor/llm-judge` | - |
| 4 | `style_gate` | rule_pack | `rule-pack/grep-personal-style-flags` | - |
| 5 | `audit` | processor | `processor/audit-trace-emitter` | - |

