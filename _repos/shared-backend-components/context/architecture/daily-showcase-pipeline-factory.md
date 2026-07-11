# Daily Showcase Pipeline Factory

Daily component generation is not enough by itself. The product also needs preconfigured pipelines that show how components become usable workflows. The operating target is 5 to 25 showcase pipelines per day.

## What Gets Generated

The daily showcase factory reads curated scenario seeds and emits review-ready component pipeline templates. Each template includes:

- a realistic user sentence;
- domain, industry, modality, risk tier, cost profile, and deployment target;
- expected inputs and outputs;
- review gates;
- ordered pre-LLM, LLM, post-LLM, and control-flow steps;
- a Postgres component-template load plan.

The generated templates are database-backed rows, not hand-written YAML definitions. The public repository keeps the generator, seed scenarios, knowledge pack, and pipeline definition.

## Current Command

```bash
python3 -m scripts.factory.daily_showcase_pipeline_templates \
  --scenario-path catalog/knowledge-packs/data/daily-showcase-pipeline-patterns/showcase-scenarios.jsonl \
  --output-dir dist/daily-showcase-pipelines/2026-05-28 \
  --count 10 \
  --run-id daily-2026-05-28
```

This produces:

- template JSON files;
- `selected-showcase-scenarios.jsonl`;
- `component-pipeline-templates.csv`;
- `component-pipeline-template-steps.csv`;
- `load-component-pipeline-templates.sql`;
- `component-template-load-plan.json`;
- `daily-showcase-pipeline-summary.json`.

The first run produced:

- 10 review-ready showcase templates;
- 76 ordered template-step rows;
- 10 selected scenario seed rows;
- a side-effect-free Postgres load plan at `dist/daily-showcase-pipelines/2026-05-28/load-plan/load-component-pipeline-templates.sql`.

The first scenarios cover OFW placement-fee overcharge triage, high-risk child-safety moderation escalation, water quality public notice review, food quality hold/release review, used-car listing evidence review, SOC alert quality, AML alert review, disaster needs assessment, public procurement bid review, and content creation approval.

## Review Boundary

Templates are product-facing. They should stay `review_ready_template` until:

1. scenario language is checked;
2. component references are reviewed;
3. cost profile is checked against current pricing;
4. risk gates are confirmed;
5. the load SQL is applied to the intended Postgres environment;
6. staged-versus-committed counts are recorded.

## Fallback Use

When ingestion is blocked, this factory still moves the product forward. Generate more showcase pipelines, then backfill the candidate components and source facts later. A useful product demo with clear review gates is better than waiting on one unavailable source surface.
