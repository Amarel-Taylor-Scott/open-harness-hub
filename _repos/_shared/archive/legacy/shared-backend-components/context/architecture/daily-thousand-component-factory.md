# Daily Thousand Component Factory

The way to reach 1,000 new usable components per day is not to create 1,000 new YAML files. The scalable unit is a database-backed component candidate row with labels, dimensions, entity links, dedupe keys, embeddings, index records, and review routing.

## Current Batches

The first daily batch used the `core` matrix and was generated at:

```bash
python3 -m scripts.factory.daily_thousand_component_seeds \
  --output-dir dist/daily-component-batch/2026-05-26 \
  --target-count 1000 \
  --matrix core
```

It produced:

- 1,000 normalized candidate component objects;
- 1,000 deterministic embedding work rows;
- 1,000 dedupe clusters;
- 5,000 index records;
- 13,000 label assignments;
- 7,000 dimension values;
- 26,880 object/entity references;
- 334 canonical entities;
- 200 review tickets.

A second daily partition can use the `expanded` matrix:

```bash
python3 -m scripts.factory.daily_thousand_component_seeds \
  --output-dir dist/daily-component-batch/2026-05-27 \
  --target-count 1000 \
  --matrix expanded
```

The first expanded run produced:

- 1,000 normalized candidate component objects;
- 1,000 deterministic embedding work rows;
- 1,000 dedupe clusters;
- 5,000 index records;
- 14,000 label assignments;
- 7,000 dimension values;
- 28,920 object/entity references;
- 358 canonical entities;
- 680 review tickets.

The matrix argument is the growth control. `core` keeps generating from the first trades, moderation, public-health, quality, and operations set. `expanded` moves into utilities, cyber, public procurement, education, pharma quality, rail, airport, government service, marketplace, nonprofit, and humanitarian workflows. `combined` is useful when the target count is much larger than 1,000 and the run should blend both families.

## Why Not Start With Wikipedia?

Wikipedia is useful later for broad background RAG, but it is not the fastest path to deployable, wireable components. It is noisy, unevenly structured, and often too general.

For component generation, curated source-surface matrices are faster:

- industry: plumbing, HVAC, used cars, AML, water quality, food quality;
- source type: public form, checklist, standard, guidance, workflow template;
- primitive type: checklist item, rule, evidence question, index record, review route;
- deployment target: Postgres, pgvector, worker, pipeline template;
- review risk: generated candidate, high-risk review, approved promotion.

This gives us searchable and customizable rows immediately, without scraping ambiguity.

## Matrix Design

Each matrix row is intentionally simple:

- domain and title;
- primitive types that can become pre-LLM, LLM, or post-LLM components;
- source-surface type such as public forms, guidance, checklists, standards indexes, training materials, workflow templates, registries, or notices;
- required stages for source governance, normalized rows, entity linking, fuzzy dedupe, index record emission, and review routing.

The output is additive. A new matrix does not require schema churn, a new storage model, or a new search path. It only adds more domains and primitive families into the same candidate row contract.

## Daily Operating Shape

Run this factory daily with a dated output directory. Then run:

1. bulk copy preflight;
2. dedupe resolution;
3. content approval;
4. active promotion for approved candidates;
5. promotion-to-CDC bridge;
6. index delta replay.

Only reviewed rows become active components. The rest remain searchable candidates.
