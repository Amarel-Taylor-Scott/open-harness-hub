# Showcase Candidate Coverage

Daily showcase pipelines should not be disconnected demos. Each template step needs a path to staged component candidates, and weak spots should feed the next component-generation batch.

## Coverage Flow

The coverage reporter reads:

- generated showcase template JSON files;
- staged `normalized-objects.jsonl` candidate rows.

It emits:

- `showcase-step-coverage.jsonl`;
- `missing-component-requests.jsonl`;
- `showcase-candidate-coverage-summary.json`.

Coverage is deterministic and side-effect free. It does not promote candidates, load Postgres, or publish tenant-visible templates.

## Status Meaning

- `covered`: strong domain and role match exists in staged candidates.
- `partial`: some candidate signal exists, but the match is weak.
- `missing`: the template step should create a generation request for the next daily component batch.

The matching logic is intentionally simple at this stage: domain aliases, industry overlap, step-role keywords, risk tier, and pipeline-step labels. Later versions can use pgvector, BM25, graph edges, and LLM reranking.

## Current Command

```bash
python3 -m scripts.factory.showcase_candidate_coverage \
  --template-dir dist/daily-showcase-pipelines/2026-05-28/templates \
  --normalized-objects dist/daily-component-batch-load-audit/2026-05-26_to_2026-05-27/merged-jsonl/normalized-objects.jsonl \
  --output-dir dist/showcase-candidate-coverage/2026-05-28
```

The first run scored 10 showcase templates against 2,000 staged component candidates:

- 76 template steps scored;
- 72 covered steps;
- 4 partial steps;
- 0 missing steps;
- 4 missing-component generation requests;
- all 10 templates ready for review.

The partial steps are concentrated in the humanitarian disaster needs assessment template, so the next generation batch should add stronger humanitarian response primitives for resource-gap labeling, coordination updates, and safeguard review.

## Product Use

This report closes the loop between the daily product demos and the daily component factory. If showcase templates are missing strong components, those gaps become new generation requests with the needed domain, role, risk tier, cost profile, deployment target, and labels.
