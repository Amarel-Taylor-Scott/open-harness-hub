# Action sampler — N parallel rollouts

*processor* · `processor/action-sampler-multi-rollout` · v0.1.0 · experimental

Sample N independent action trajectories for an agent task; return
the trajectories + final-state candidates for downstream judging.
The N candidates can be reviewed by a separate judge processor to
pick the best.

Verified by Open Harness Hub clone:
`SWE-agent/sweagent/agent/action_sampler.py`.

| axis | value |
|---|---|
| industry | ai, software |
| capability | agent_loop, planning |
| modality | text, code |
| lifecycle | experimental |
| trust_boundary | local |
| license | MIT |



