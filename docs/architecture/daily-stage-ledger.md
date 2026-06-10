# Daily Stage Ledger

Daily factory runs should be resumable. A failed embedding plan or closeout report should not force the system to regenerate component candidates, showcase templates, coverage reports, or load-audit rows that already have durable summaries.

`tool/daily-stage-ledger-builder` reads a daily run directory and `knowledge-pack/daily-factory-stage-contracts`, then writes a ledger with:

- stage status: `complete`, `missing`, `blocked`, `failed`, or `skipped`;
- expected summary path for each stage;
- prerequisite stages;
- deterministic resume commands;
- closeout readiness;
- operator notes that SQL application and promotion remain approval-gated.

## Command

```bash
python3 -m scripts.factory.daily_stage_ledger \
  --run-dir dist/daily-production-runs/YYYY-MM-DD \
  --output dist/daily-production-runs/YYYY-MM-DD/stage-ledger.json
```

The ledger is side-effect free. It inspects files and emits the next safe action, but it does not generate rows, apply SQL, contact model endpoints, train weights, or mutate Postgres.

## Why It Matters

The million-component path needs additive progress. The daily loop should be able to:

- resume an interrupted run;
- skip stages already proven by summary files;
- distinguish staged rows from committed database rows;
- keep high-risk promotion and sharing review-gated;
- produce reliable closeout metrics without full static-doc rebuilds.

