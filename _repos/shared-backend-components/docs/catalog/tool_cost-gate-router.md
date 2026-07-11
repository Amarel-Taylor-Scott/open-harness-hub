# Cost gate router

*tool* · `tool/cost-gate-router` · v0.1.0 · experimental

Routes each inference request to the cheapest model that meets
caller-supplied quality and cost ceiling constraints. Before
dispatching, estimates input and output token counts and projected
cost for every candidate route. Rejects routes that would breach
the per-request or per-day cost ceiling. Among remaining
candidates, selects the lowest-cost route whose quality tier
satisfies the minimum quality score. Emits a cost audit record
for each decision.

| axis | value |
|---|---|
| industry | ai, cross_industry, software.devops |
| capability | routing, governance, evaluation |
| modality | text, structured |
| lifecycle | experimental |
| trust_boundary | mixed |
| freshness | stable |
| license | MIT |



