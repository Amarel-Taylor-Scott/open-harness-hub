# Theory To Component Factory

Technical theories, postmortems, and architecture critiques should not remain isolated prose. When they describe a recurring capability gap, the factory can convert them into component candidates that are searchable, reviewable, and wireable into pipelines.

## Input Shape

A theory seed records:

- the capability gap;
- domain and risk tier;
- source kind;
- label paths;
- expansion axes;
- constraints;
- extra stages needed for review or deployment.

The seed should avoid reusable harmful payloads, private data, secrets, and proprietary text. Store defensive summaries, hashes, constraints, and synthetic fixture plans instead.

## Expansion Shape

The generator expands each theory across component roles:

- pre-model detector;
- model router;
- post-model verifier;
- evaluation rubric;
- deployment blueprint;
- audit trace;
- cost guard;
- human review gate.

It also varies deployment targets and risk routes so the same idea can produce local, hosted, containerized, browser, mobile edge, and analytics-tier candidates.

## Daily Use

```bash
python3 -m scripts.factory.theory_component_seeds \
  --theory-seeds catalog/knowledge-packs/data/theory-to-component-patterns/theory-seeds.jsonl \
  --output-dir dist/theory-component-batch/YYYY-MM-DD \
  --target-count 1000 \
  --run-id theory-components-YYYY-MM-DD
```

The output is staged JSONL, not published components. Promotion still requires dedupe, review, approval, CDC capture, database load, embeddings, and committed-load audit.

## Why This Helps The Million-Component Goal

This gives the project a path from ideas to repeatable component production. One useful technical critique can produce hundreds or thousands of candidate rows without adding thousands of repository files. The same pattern works for guardrail failures, search architecture, verified facts, expert review loops, hosting cost models, and workflow automation patterns.
