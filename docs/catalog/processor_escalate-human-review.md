# Escalate to human reviewer

*processor* · `processor/escalate-human-review` · v0.1.0 · beta

Route an output (and its full trace + context) to a human reviewer
queue. Used when a safety gate fires, a confidence threshold is not
met, or a red-flag classifier triggers. Pluggable backend:
generic task queue, Linear, Jira, Slack, or a custom webhook.

| axis | value |
|---|---|
| industry | cross_industry |
| capability | routing, safety_gating |
| modality | text, structured |
| lifecycle | beta |
| trust_boundary | external |
| license | MIT |



