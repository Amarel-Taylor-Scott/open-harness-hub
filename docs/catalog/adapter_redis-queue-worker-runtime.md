# Redis job queue worker runtime adapter

*adapter* · `adapter/redis-queue-worker-runtime` · v0.1.0 · experimental

Provider-neutral adapter for a Redis-backed job queue used to dispatch and
consume asynchronous background jobs in the Open Harness Hub pipeline.

Supported job families: scan (source surface scan), embed (batch embedding
execution), eval (benchmark evaluation), price (model pricing lookup), and
promote (promotion readiness assessment). Workers dequeue jobs, execute them,
and write results back to the canonical Postgres store via the
postgres-pgvector-runtime adapter.

Compatible with Redis OSS, Upstash Redis, and any RESP2/RESP3-compatible
endpoint. Connection resolved from REDIS_URL environment variable at runtime.
Does not hardcode queue names, retry counts, or concurrency limits.

| axis | value |
|---|---|
| industry | ai, software.devops, cross_industry |
| capability | routing, serving, governance |
| modality | structured |
| lifecycle | experimental |
| trust_boundary | local |
| freshness | stable |
| license | MIT |



