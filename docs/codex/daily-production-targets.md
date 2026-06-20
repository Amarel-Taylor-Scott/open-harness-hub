# Daily Production Targets

This goal should keep moving every day. The practical operating target is:

- 1,000 to 5,000 new database-backed component candidates per day;
- 5 to 25 preconfigured showcase pipelines per day;
- load/audit evidence that distinguishes raw generated rows, deduped staged rows, and committed Postgres rows;
- review tickets for high-risk or uncertain candidates;
- no real PII, secrets, proprietary dumps, or unlicensed source material.

## Daily Component Candidate Loop

Use a dated partition and a named matrix:

```bash
python3 -m scripts.factory.daily_thousand_component_seeds \
  --output-dir dist/daily-component-batch/YYYY-MM-DD \
  --target-count 1000 \
  --matrix core
```

Scale up in this order:

1. `--target-count 2500`
2. `--target-count 5000`
3. run a second partition with `--matrix expanded`
4. run a third partition with `--matrix combined`
5. merge partitions with `scripts.db.daily_partition_load_audit`

## Daily Showcase Pipeline Loop

Create or refresh 5 to 25 showcase pipeline templates. Each should include:

- a realistic user sentence;
- domain and risk tier;
- pre-LLM steps;
- LLM/model routing steps;
- post-LLM verification, scoring, escalation, or formatting steps;
- cost profile;
- deployment target;
- expected inputs and outputs;
- review gates.

Preferred showcase domains include AML alert review, social moderation, public fact propagation, water quality, food quality, disaster response, used-car sales, trades work-order triage, cyber SOC alert review, public procurement, government benefits, animal hospital operations, environmental review, and content creation approval.

## Fallback Rules

Do not stop when one route is blocked.

- If source ingestion is blocked, generate synthetic source-surface candidates and mark them as synthetic.
- If a source license is unclear, route it to source-governance review and switch surfaces.
- If full validation is slow, run focused validation, continue local tests, then run full validation before closeout.
- If database access is unavailable, emit load SQL and keep the audit `staged_only`.
- If component generation is blocked, generate showcase pipelines, rubrics, benchmark cases, promotion decisions, CDC plans, or index deltas.
- If a batch risks PII or sensitive data, stop that source path and switch to a safe public or synthetic path.

## Daily Closeout Metrics

Report these separately:

- public component definition count;
- generated candidate rows;
- deduped staged rows;
- committed Postgres rows, if available;
- review tickets opened;
- index records emitted;
- embedding work rows emitted;
- showcase pipelines created or refreshed;
- validation result;
- catalog page rebuild result;
- next source surface or factory area.

## One-Command Daily Run

Use the daily production runner when the goal is to produce a complete daily batch rather than exercising one factory stage at a time:

```bash
python3 -m scripts.factory.daily_production_run \
  --run-date YYYY-MM-DD \
  --output-dir dist/daily-production-runs/YYYY-MM-DD \
  --target-count 1000 \
  --matrix combined \
  --showcase-count 10
```

The runner creates component candidate rows, showcase pipeline templates, coverage reports, gap-derived candidates, and a staged load audit in one dated directory. It does not promote components or apply SQL; those remain review-gated operator actions.

## Scheduler Report

After a run finishes, build the schedule report:

```bash
python3 -m scripts.factory.daily_production_scheduler \
  --runs-root dist/daily-production-runs \
  --output-dir dist/daily-production-schedule/YYYY-MM-DD \
  --max-target 5000
```

The scheduler compares daily run summaries and recommends whether to scale to 2,500 or 5,000 candidates, hold at the current volume, rotate the matrix, or prioritize coverage gap fill.

## Current Throughput Evidence

The daily factory has now produced clean staged runs at the full target range:

- `2026-05-29`: 1,011 component candidates, 10 showcase pipelines, 59,122 unique staged rows, 0 preflight issues;
- `2026-05-30`: 2,500 component candidates, 10 showcase pipelines, 146,563 unique staged rows, 0 preflight issues;
- `2026-05-31`: 5,000 component candidates, 10 showcase pipelines, 292,343 unique staged rows, 0 preflight issues.

The next operating bottleneck is promotion and load governance: review tickets, database load execution, embedding execution, CDC capture, and tenant-visible publication should be scaled before increasing beyond 5,000 candidates per day.

## Promotion Readiness

After a daily run finishes, audit promotion readiness before any candidate-table load or active publication work:

```bash
python3 -m scripts.db.daily_promotion_readiness_plan \
  --daily-run-dir dist/daily-production-runs/YYYY-MM-DD \
  --output-dir dist/daily-promotion-readiness/YYYY-MM-DD \
  --run-id promotion-readiness-YYYY-MM-DD
```

Treat candidate-table load readiness and active component promotion readiness as separate gates. A row can be structurally ready to load into candidate tables while still blocked from tenant-visible promotion by review tickets or missing real embeddings.

## Embedding Execution Planning

After promotion readiness, plan embedding execution:

```bash
python3 -m scripts.db.daily_embedding_execution_batch_plan \
  --daily-run-dir dist/daily-production-runs/YYYY-MM-DD \
  --output-dir dist/daily-embedding-execution/YYYY-MM-DD \
  --run-id daily-embedding-YYYY-MM-DD
```

The planner shards `object_embedding` rows into retryable worker batches, records local and hosted model profiles, estimates token volume and cost where pricing is known, and runs vector readiness immediately. Vector search should stay blocked until stored vector metadata passes readiness audit.

## Local Embedding Worker Contract

After embedding execution planning, run a bounded worker contract smoke test before enabling real vector writes:

```bash
python3 -m scripts.db.local_embedding_worker_contract \
  --embedding-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/local-embedding-worker-contract/YYYY-MM-DD \
  --run-id local-embedding-contract-YYYY-MM-DD \
  --limit 256
```

This emits sampled completion rows, stored vector metadata rows, and a vector readiness audit. The rows are contract stubs, not semantic production embeddings. Use this stage to prove worker id matching, text hash matching, dimension matching, and readiness behavior before wiring the actual local or hosted embedding runtime.

## Local Hash Embedding Worker

Run the dependency-free local vector worker when the daily run needs real vector arrays without provider calls:

```bash
python3 -m scripts.db.local_hash_embedding_worker \
  --embedding-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --output-dir dist/local-hash-embedding-worker/YYYY-MM-DD \
  --run-id local-hash-embedding-YYYY-MM-DD \
  --limit 256
```

This joins planned completion rows back to source `object_embedding` text, writes deterministic fixed-dimension vectors, and runs vector readiness. Treat these vectors as an execution and storage baseline. Tenant-visible semantic search still needs quality evaluation or a stronger embedding runtime.

## Pgvector Embedding Load Plan

After a worker emits `stored-vector-rows.jsonl`, build the side-effect-free Postgres load plan:

```bash
python3 -m scripts.db.pgvector_embedding_load_plan \
  --stored-vectors-jsonl dist/local-hash-embedding-worker/YYYY-MM-DD/stored-vector-rows.jsonl \
  --source-embedding-rows-jsonl dist/daily-production-runs/YYYY-MM-DD/load-audit/merged-jsonl/object-embeddings.jsonl \
  --output-dir dist/pgvector-embedding-load-plan/YYYY-MM-DD \
  --run-id pgvector-embedding-load-YYYY-MM-DD
```

This writes accepted and rejected row evidence plus `object-embedding-load.sql`. It rejects rows that do not match the canonical `vector(384)` schema or cannot be joined back to source text. Applying the SQL remains an explicit operator action against the intended Postgres database.

## Embedding Committed Load Audit

Before applying SQL, prove the system is still not treating staged vectors as product-ready:

```bash
python3 -m scripts.db.embedding_committed_load_audit \
  --embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --pgvector-load-plan-summary dist/pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --output dist/pgvector-embedding-load-plan/YYYY-MM-DD/embedding-committed-load-audit.json \
  --run-id embedding-committed-load-YYYY-MM-DD
```

After applying the SQL and exporting committed counts, rerun with `--committed-counts`. Vector search should only become product-ready when committed Postgres `object_embedding` counts cover the accepted pgvector load rows.

## Local Pgvector Embedding Smoke Plan

When the operator is ready to exercise the local database path, generate the reviewed command plan:

```bash
python3 -m scripts.db.local_pgvector_embedding_smoke_plan \
  --pgvector-load-plan-summary dist/pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --embedding-execution-plan dist/daily-embedding-execution/YYYY-MM-DD/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --output-dir dist/local-pgvector-embedding-smoke/YYYY-MM-DD \
  --run-id local-pgvector-embedding-smoke-YYYY-MM-DD
```

The plan emits Docker, schema, load, count export, and committed-audit commands. It does not execute them. Treat this as the reviewed bridge from JSONL/SQL evidence to actual local Postgres proof.

## Theory To Component Batch

When a user supplies a technical theory, postmortem, or architecture critique, convert it into staged component candidates instead of leaving it as prose:

```bash
python3 -m scripts.factory.theory_component_seeds \
  --theory-seeds catalog/knowledge-packs/data/theory-to-component-patterns/theory-seeds.jsonl \
  --output-dir dist/theory-component-batch/YYYY-MM-DD \
  --target-count 1000 \
  --run-id theory-components-YYYY-MM-DD
```

This generates normalized component candidates, labels, dimensions, entity refs, embedding work rows, review tickets, and index records. Keep these rows staged until dedupe, review, approval, promotion, CDC, database load, and committed-count audits pass.

### Current Theory Batch Evidence

The `2026-05-26` theory-to-component batch expanded 5 theory seeds into:

- 1,000 normalized component candidates;
- 5,000 index records;
- 1,000 embedding work rows;
- 1,000 review tickets;
- 77,083 unique staged rows after load audit;
- 0 duplicate rows;
- 0 preflight issues;
- `staged_only` audit status.

This proves that user-provided theories, technical postmortems, and architecture critiques can feed the daily 1K candidate target without creating thousands of repository files.

After the staged load audit, run the governance bridge:

```bash
python3 -m scripts.db.theory_batch_governance_bridge \
  --theory-batch-summary dist/theory-component-batch/YYYY-MM-DD/theory-component-batch-summary.json \
  --load-audit-summary dist/theory-component-batch-load-audit/YYYY-MM-DD/summary.json \
  --output-dir dist/theory-batch-governance-bridge/YYYY-MM-DD \
  --run-id theory-batch-governance-YYYY-MM-DD
```

This produces promotion-readiness rows, review queues, embedding execution batches, and vector-readiness summaries while keeping active promotion blocked until review and vector execution are complete.

For the `2026-05-26` theory batch, the bridge produced:

- 1,000 structurally candidate-load-ready component rows;
- 1,000 rows still blocked from active promotion by review requirements;
- 1,000 rows still requiring embedding execution;
- 13 planned local embedding batches;
- 288,500 estimated embedding tokens at the local baseline profile;
- `not_ready` vector readiness with 1,000 missing stored vector rows.

After local vector execution and pgvector load planning, the same batch produced:

- 1,000 completed local embedding rows;
- 1,000 stored vector rows;
- 0 missing source text rows;
- vector readiness `ready`;
- 1,000 pgvector load-accepted rows;
- 0 pgvector load-rejected rows;
- committed-load audit `load_planned_not_committed`;
- vector search product-ready: false until committed Postgres counts cover the load plan.

Before mutating a local database, generate the operator-reviewed local Postgres smoke plan:

```bash
python3 -m scripts.db.theory_local_postgres_smoke_plan \
  --theory-batch-summary dist/theory-component-batch/YYYY-MM-DD/theory-component-batch-summary.json \
  --theory-load-audit-summary dist/theory-component-batch-load-audit/YYYY-MM-DD/summary.json \
  --pgvector-load-plan-summary dist/theory-pgvector-embedding-load-plan/YYYY-MM-DD/pgvector-embedding-load-plan-summary.json \
  --embedding-execution-plan dist/theory-batch-governance-bridge/YYYY-MM-DD/embedding/embedding-plan/embedding-execution-plan.json \
  --vector-readiness-summary dist/theory-local-hash-embedding-worker/YYYY-MM-DD/vector-readiness/vector-readiness-summary.json \
  --output-dir dist/theory-local-postgres-smoke/YYYY-MM-DD \
  --run-id theory-local-postgres-smoke-YYYY-MM-DD
```

The plan is side-effect free. It emits Docker, schema, candidate-row load, vector load, committed-count export, and post-load audit commands for operator review.

For the `2026-05-26` theory batch, the local Postgres smoke plan emitted 8 reviewed commands and verified:

- 1,000 theory-derived candidate rows;
- 77,083 unique staged rows;
- candidate preflight issue count 0;
- 1,000 vector load-accepted rows;
- 0 vector load-rejected rows;
- safe to apply locally: true.
