# Multi-agent debate with judge

*pipeline* · `pipeline/multi-agent-debate-with-judge` · v0.1.0 · experimental

Two or more debater personas argue different sides of a question
across N rounds. A judge persona scores the final positions. Used
for hard reasoning tasks where stress-testing improves accuracy.

Verified by Open Harness Hub clone:
`microsoft/autogen` implements the group-chat round-table pattern.

| axis | value |
|---|---|
| industry | ai |
| capability | reasoning, evaluation |
| modality | text |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Two or more debater agents argue different positions across N rounds;
judge scores final positions and outputs verdict + transcripts.

**pipeline_kind:** `multi_agent`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `spawn_debaters` | processor | `processor/persona-set-generator` | — |
| 3 | `round_1` | harness | `harness/text-safety-review` | — |
| 4 | `subsequent_rounds_loop` | processor | `processor/iterative-revise-loop` | — |
| 5 | `judge` | processor | `processor/llm-judge` | — |

