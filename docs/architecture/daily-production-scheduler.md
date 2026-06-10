# Daily Production Scheduler

The daily production scheduler is a planning layer over completed factory runs. It reads dated `daily-production-run-summary.json` files, computes trend metrics, and emits the next recommended command. It does not generate candidates or apply SQL by itself.

## Command

```bash
python3 -m scripts.factory.daily_production_scheduler \
  --runs-root dist/daily-production-runs \
  --output-dir dist/daily-production-schedule/2026-05-29 \
  --max-target 5000
```

The output directory contains:

- `daily-production-schedule-report.json`;
- `daily-production-schedule-report.md`;
- the next recommended `python3 -m scripts.factory.daily_production_run ...` command.

## Recommendation Logic

The scheduler uses conservative rules:

- if no prior run exists, start with `target_count=1000`, `matrix=core`, and `showcase_count=5`;
- if the last run has preflight issues, hold volume and switch to `core`;
- if duplicate rate is high, hold volume and rotate the matrix;
- if coverage is low or missing steps remain, hold volume and prioritize gap fill;
- if the last run is clean, climb the target ladder from 1,000 to 2,500 to 5,000 candidates per day.

## Metrics

The schedule report tracks:

- component candidates per run;
- showcase pipelines per run;
- index records and embedding work records;
- review tickets;
- coverage rate;
- duplicate rate;
- raw and unique staged row totals;
- preflight status;
- recommended next command and reason.

## Current Recommendation

After the `2026-05-29`, `2026-05-30`, and `2026-05-31` runs, the scheduler observed:

- 8,511 total staged component candidates;
- 30 total showcase pipeline templates;
- 42,555 index records;
- 3,211 review tickets;
- 498,028 unique staged rows;
- average coverage rate of 0.952;
- average duplicate rate of 0.000079;
- 0 preflight issues on the latest run.

The next recommended command is:

```bash
python3 -m scripts.factory.daily_production_run \
  --run-date 2026-06-01 \
  --output-dir dist/daily-production-runs/2026-06-01 \
  --target-count 5000 \
  --matrix combined \
  --showcase-count 10
```

The scheduler is now holding at 5,000 candidates per run because that is the configured maximum target. Further scale-up should happen after the promotion/load path can absorb staged candidates safely.

## Review Boundary

The scheduler only writes reports. Operators still decide when to run the recommended command, whether to apply generated SQL, and whether to promote review-ready components or showcase templates.
