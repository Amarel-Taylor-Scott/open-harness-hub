# Daily Component Production Run

The daily production runner is the standard path for growing the database-backed component inventory without turning the repository into one file per generated row. It joins the existing factories into one repeatable workflow.

## Command

```bash
python3 -m scripts.factory.daily_production_run \
  --run-date 2026-05-29 \
  --output-dir dist/daily-production-runs/2026-05-29 \
  --target-count 1000 \
  --matrix combined \
  --showcase-count 10
```

Scale the same command to `--target-count 2500` and then `--target-count 5000` once validation and staged load audits stay clean.

## What It Runs

1. Generate database-backed component candidates from the daily source-surface matrix.
2. Generate 5 to 25 review-ready showcase pipeline templates.
3. Score showcase template steps against generated candidates.
4. Convert partial or missing coverage into targeted gap-derived component candidates.
5. Merge the component and gap partitions into a deduped staged load package.
6. Emit bulk-copy SQL and a side-effect-free staged load audit.
7. Write `daily-production-run-summary.json` with closeout metrics.

## Review Boundary

The runner does not promote candidates, apply SQL, publish templates, or call external systems. It only writes staged rows and review evidence. Operators still need to approve:

- high-risk component candidates;
- source governance decisions;
- dedupe cluster merges;
- model routing and cost assumptions;
- showcase pipeline publication;
- Postgres load execution.

## Required Daily Metrics

The summary reports:

- generated component candidates;
- index records;
- embedding work records;
- review tickets;
- showcase templates and template steps;
- coverage counts;
- gap-derived candidates;
- raw, unique, and duplicate staged row counts;
- preflight status;
- load SQL path.

## First Full Run

The `2026-05-29` run used `--target-count 1000`, `--matrix combined`, and `--showcase-count 10`. It produced:

- 1,011 staged component candidates, including 11 gap-derived candidates;
- 10 showcase pipeline templates;
- 76 showcase template steps;
- 5,055 index records;
- 1,011 embedding work records;
- 211 review tickets;
- 65 covered showcase steps;
- 11 partial showcase steps converted into gap requests;
- 0 missing showcase steps;
- 59,122 unique staged load rows after dedupe;
- 0 preflight issues;
- `staged_only` load audit status.

## First Scale-Up Run

The `2026-05-30` run used `--target-count 2500`, `--matrix combined`, and `--showcase-count 10`. It produced:

- 2,500 staged component candidates;
- 10 showcase pipeline templates;
- 76 showcase template steps;
- 12,500 index records;
- 2,500 embedding work records;
- 1,000 review tickets;
- 76 covered showcase steps;
- 0 partial showcase steps;
- 0 missing showcase steps;
- 146,563 unique staged load rows after dedupe;
- 0 duplicate staged rows;
- 0 preflight issues;
- `staged_only` load audit status.

## First 5K Run

The `2026-05-31` run used `--target-count 5000`, `--matrix combined`, and `--showcase-count 10`. It produced:

- 5,000 staged component candidates;
- 10 showcase pipeline templates;
- 76 showcase template steps;
- 25,000 index records;
- 5,000 embedding work records;
- 2,000 review tickets;
- 76 covered showcase steps;
- 0 partial showcase steps;
- 0 missing showcase steps;
- 292,343 unique staged load rows after dedupe;
- 0 duplicate staged rows;
- 0 preflight issues;
- `staged_only` load audit status.

This proves the local factory can generate and audit 5,000 database-backed component candidates in a single daily partition. The next constraint is no longer candidate generation; it is promotion governance, database loading, embedding execution, and review throughput.

## Fallback Behavior

If one expansion route stalls, keep the daily run moving:

- use `--matrix core` if the combined matrix is too broad;
- use `--skip-gap-fill` if coverage backfill needs manual review;
- keep `--showcase-count 5` when product scenarios are the limiting factor;
- emit staged load SQL even when no database is available;
- open review tickets for high-risk rows instead of promoting them automatically.
