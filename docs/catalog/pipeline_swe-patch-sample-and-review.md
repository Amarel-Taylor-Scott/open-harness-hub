# SWE-agent: sample N patches + reviewer judges

*pipeline* · `pipeline/swe-patch-sample-and-review` · v0.1.0 · experimental

The princeton-nlp/SWE-agent pattern. Given a bug report + repo: sample
N action-rollouts (each producing a candidate patch via file-edit + run-
test loop), then a reviewer model judges the N candidates and picks
the best patch.

Verified by Open Harness Hub clone: SWE-agent's
`sweagent/agent/{agents,reviewer,history_processors,action_sampler}.py`
implements exactly this.

| axis | value |
|---|---|
| industry | ai, software, software.codereview |
| capability | reasoning, code_synthesis, agent_loop |
| modality | text, code |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



## Task

Given a bug report + repo path, sample N candidate patches, run tests
on each, then have a reviewer model pick the best one.

**pipeline_kind:** `code_patch_search`

## Steps

| # | id | kind | ref | when |
|---|---|---|---|---|
| 1 | `guard_bug` | rule_pack | `rule-pack/grep-prompt-injection-heuristics` | — |
| 2 | `sample_candidates` | processor | `processor/action-sampler-multi-rollout` | — |
| 3 | `reviewer_judge` | processor | `processor/llm-judge` | — |
| 4 | `audit` | processor | `processor/audit-trace-emitter` | — |

