# Off-The-Shelf Component Pipelines

The product should give users a pipeline blueprint from a sentence, then let them swap cost, model, hosting, verification, and deployment choices.

Example request:

```text
Build me an LLM pipeline that intakes a photo plus description and processes it in the cheapest way possible to classify whether it has to do with human exploitation.
```

The generated template should not be a single prompt. It should be a chain of components:

1. `pre_llm`: normalize photo and description, route media, check sensitive data, retrieve relevant rules and facts.
2. `llm`: choose the cheapest model path that can handle the modality and risk tier.
3. `post_llm`: threshold the result, verify claims, cite sources, redact unsafe output, and route high-risk cases to review.
4. `control_flow`: iterate when confidence is low, branch by jurisdiction or modality, retry failed tools, and escalate to humans when needed.
5. `deployment`: emit container, function, Terraform, MCP, or local runtime blueprints.

## Why This Matters

Most user value will come from areas where the base model does not already have a capability spike. The database should therefore store the reusable pieces that improve weak areas: verified facts, procedures, checklists, rubrics, labels, model routes, test sets, failure cases, and review questions.

Priority for new components:

```text
usefulness x demand x complexity x time savings x deployment frequency
x not easily solved by a base model
x cost savings
x deployment and management improvement
x ability to swap models over time
```

## Template Expansion Contract

The template expander returns:

- `template_id`
- task family
- cost profile
- modalities
- storage target
- vector-search target
- ordered steps
- layer per step
- optional control-flow kind per step
- scale notes

Templates are candidates until reviewed. The database can then attach ratings, usage, deployment history, cost observations, benchmark scores, and source provenance.
