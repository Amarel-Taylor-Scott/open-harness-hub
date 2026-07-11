# Component Template Load Plan

Generated pipeline templates should become database rows, not loose JSON examples. The template load planner turns one or more generated template JSON files into:

- `component-pipeline-templates.csv`
- `component-pipeline-template-steps.csv`
- `load-component-pipeline-templates.sql`
- `component-template-load-plan.json`

The SQL loads `component_pipeline_template` first, then `component_pipeline_template_step`. Each step keeps:

- step order
- component layer
- optional control-flow kind
- resolved active component id when available
- resolved component candidate id when available
- original component reference in `body.component_ref`

Keeping unresolved references in the body matters at scale. A 100M-component store will often generate useful templates before every referenced component has been reviewed and promoted. The loader should preserve the blueprint without pretending unresolved references are active production rows.

## Review Boundary

Templates are product-facing objects, so they need their own review gate:

1. template generation
2. CSV and SQL load planning
3. staged database load
4. staged-versus-committed count audit
5. layer coverage audit
6. cost route audit
7. tenant-visible publication

## Search Readiness

Each template and each step should be embedded later as separate search subjects. That lets a user retrieve either a complete off-the-shelf pipeline or a modular piece such as a cheaper `llm` route, stricter `post_llm` verifier, or safer `control_flow.human_review` branch.

The first implementation stays side-effect free. It writes files only; actual database execution remains a separate operator or worker step.
