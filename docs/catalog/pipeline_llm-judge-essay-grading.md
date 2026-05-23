# LLM-judge essay grading (with adversarial prompt prefix)

*pipeline* · `pipeline/llm-judge-essay-grading` · v0.1.0 · stable

Run a frontier LLM as judge on candidate essays, using a few-shot
prompt with adversarial prefix patterns to discourage gaming. The
"you can't please them all" pattern: grade strictly, refuse to
inflate scores under social-engineering pressure.

Verified by Open Harness Hub mining of richolson's "Mash It Up" (561
votes), "Add It Up!" (333 votes), and jiprud's "Essays - simple
submission" (484 votes) on llms-you-cant-please-them-all.

| axis | value |
|---|---|
| industry | ai, education |
| capability | evaluation, reasoning |
| modality | text |
| lifecycle | stable |
| trust_boundary | local |
| license | MIT |



## Task

Given an essay + rubric, produce a grade (numeric or rubric-aligned)
with concrete justifications. Robust to adversarial-prompt prefixes
trying to inflate the score.

**pipeline_kind:** `evaluation`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `judge` | processor | `processor/llm-judge` | — |
| 3 | `ensemble_across_seeds` | processor | `processor/self-consistency-sampler` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

