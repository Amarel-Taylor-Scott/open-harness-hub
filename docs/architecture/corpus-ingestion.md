# Corpus Ingestion — Feed, Check, Re-ingest Loop

The corpus-ingestion layer is the pipeline that turns official and government sources into governed corpus rows and keeps them fresh. It has three phases: initial feed, recurring CDC check, and triggered re-ingest. The same container image runs all phases; only the command changes.

## The Loop

```
[data/source-registry.jsonl]
        │
        ▼
scripts.ingest.feed --all          ← initial ingest of every registered source
        │                             fetches → parses → emits row families → store
        │
        ▼
scripts.ingest.freshness           ← recurring CDC poll (every 6 h in cloud)
  --check --enqueue                  fetches each source, hashes content,
        │                             enqueues re-ingest job when hash changed
        │
        ▼
[queue: ohh:foundry:jobs]
        │
        ▼
scripts.foundry.worker --serve     ← drains the queue; re-runs feed per changed source
        │
        ▼
[store: Postgres/pgvector or SQLite]
```

The health check (`scripts.ingest.health --check`) runs out-of-band — CI, Kubernetes liveness, or an operator — to verify every registered source is reachable and parseable before a job is enqueued.

## Source Registry

All sources live in `data/source-registry.jsonl`. Each entry is a JSON object with at minimum:

```json
{
  "keywords": ["philippines", "aml"],
  "url": "https://bsp.gov.ph/aml",
  "author": "Bangko Sentral ng Pilipinas",
  "license": "CC0-1.0",
  "source_kind": "regulation",
  "gov": true,
  "name": "PH AML thresholds (BSP)"
}
```

`scripts.ingest` reads this file via `scripts.ingest.load_registry()` — the single, canonical reader. No other code re-implements JSONL parsing for this file. `scripts.foundry.scrapers.DEFAULT_REGISTRY` points to the same path.

## Entrypoints

| Command | Role |
|---|---|
| `python3 -m scripts.ingest.feed --all` | Feed every registered source into the corpus |
| `python3 -m scripts.ingest.freshness --check --enqueue` | CDC poll; enqueue re-ingest on change |
| `python3 -m scripts.ingest.health --check` | Reachability and parse check per source |
| `python3 -m scripts.foundry.worker --serve` | Consume re-ingest jobs from the queue |

All four entrypoints run fully offline in self-test mode (`--self-test`) using `CannedFetcher` and a temp `SqliteStore` / in-memory queue.

## Row Families

Each ingested source produces these row families (see `scripts.foundry.stage_load`):

| Family | Contents |
|---|---|
| `source_record` | URL, author, license, source_kind — deduplicated by source URL hash |
| `normalized_object` | typed component record with content_hash, version_hash, name |
| `object_embedding` | placeholder vector (staging) or real vector when an embedder is wired |
| `index_record` | facets, lift_delta, openness tier, delivery, approval_status — what search reads |
| `dedupe_cluster` | simhash + nearest_id for collapse during high-volume merges |
| `label_assignment` | lift_reason, durability_class, industry, capability labels |
| `knowledge_entry` | individually addressable corpus pages (§15.5), each with provenance |
| `review_ticket` | raised when provenance is incomplete or a human sign-off is required |

Gov sources with `"gov": true` flow to the `open` openness tier and the `live_subscription` delivery classification (see `scripts.foundry.openness` and `scripts.foundry.access`). The governed feed — not the static content — is the subscription value.

## Open vs. Governed Framing

Gov-published content is open: its license and legal basis are public record. The **maintained CDC feed** — the continuous freshness tracking, revocation alerts, and re-ingest automation — is the subscription. A subscriber who monitors for AML-threshold changes does not want to re-scrape BSP every morning; they want a governed feed that fires when the threshold actually moves.

This is the product split:

- **Open layer**: the component definitions themselves, the source provenance, the initial corpus rows — downloadable as frozen exports.
- **Governed layer**: the live freshness feed, the change events, the revocation alerts, the re-ingest automation — the subscription.

The `publisher_class` field (`public_authority` for gov sources) and the `freshness: volatile` payload flag are what `scripts.foundry.access.classify_access` uses to route to `live_subscription` delivery.

## Safety Gates

Every ingested row must pass these gates before it can be promoted to tenant-visible:

1. **Provenance**: `source_url` and `license` must be present and non-empty. Missing provenance raises a `review_ticket` with `risk: high`.
2. **No PII**: the ingest pipeline processes only official public metadata — no real names, no contact details, no credentials. The `_reference/` directory must never be republished.
3. **No secrets**: no API keys, passwords, or tokens in any row. The `.env` file is gitignored; the K8s secret is a sealed-secret template, never committed with real values.
4. **Promotion boundary**: an `object_embedding` row flagged `is_placeholder: true` is staging-only and must not reach vector search. Open review tickets and high-risk flags block promotion. See `scripts.db.daily_promotion_readiness_plan` for the promotion gate.
5. **CDC idempotency**: re-ingest uses content hashes for deduplication. Re-running `feed --all` on an unchanged source produces no new rows (upsert by ID in `SqliteStore` / Postgres).

## Running Locally

No services required for a single-machine run. The foundry falls back to SQLite for the store and an SQLite-backed queue:

```bash
# 1. initial feed (all registered sources, offline mock → live with network)
python3 -m scripts.ingest.feed --all

# 2. CDC check + enqueue
python3 -m scripts.ingest.freshness --check --enqueue

# 3. consume the queue
python3 -m scripts.foundry.worker --serve

# 4. health check
python3 -m scripts.ingest.health --check
```

Self-tests (fully offline, zero network, zero services):

```bash
python3 -m scripts.ingest.feed --self-test
python3 -m scripts.ingest.freshness --self-test
python3 -m scripts.ingest.health --self-test
python3 -m scripts.foundry.scrapers --self-test
```

### Local cloud-equivalent stack (Postgres + Redis)

```bash
# Start Postgres + Redis (from docker-compose.yml) + the ingestion services (ingest-compose.yml):
docker compose -f infra/docker-compose.yml -f infra/ingest-compose.yml up --build
```

The `freshness-cron` service loops on `INGEST_FRESHNESS_INTERVAL_S` (default 21600 = 6 h). Set it to `60` for local testing:

```bash
INGEST_FRESHNESS_INTERVAL_S=60 docker compose \
  -f infra/docker-compose.yml -f infra/ingest-compose.yml up --build
```

Environment is driven entirely by `.env` (copy `.env.example`). Switch `DATABASE_URL` and `REDIS_URL` to move from SQLite to Postgres + Redis without any code change.

## Cloud Deployment

### Compose → K8s mapping

| Local (ingest-compose.yml) | Cloud (K8s) |
|---|---|
| `freshness-cron` (while-true loop) | `infra/k8s/freshness-cron.yaml` (CronJob, `0 */6 * * *`) |
| `ingest-worker` (worker --serve) | `infra/k8s/worker.yaml` (Deployment + KEDA ScaledObject) |
| `postgres` | managed Postgres + pgvector (Neon / Cloud SQL) |
| `redis` | managed Redis (Upstash / MemoryStore / in-cluster) |

### Apply to K8s

```bash
kubectl apply -f infra/k8s/core.yaml            # namespace + config + secret template
kubectl apply -f infra/k8s/freshness-cron.yaml  # CDC CronJob (every 6 h)
kubectl apply -f infra/k8s/worker.yaml           # worker + KEDA autoscaler
```

The `freshness-cron` CronJob runs `scripts.ingest.freshness --check --enqueue` every 6 hours. On a content-hash change it enqueues a job to `ohh:foundry:jobs`. KEDA scales the worker Deployment from 0 to N on queue depth (`listLength: 10` — one worker per 10 queued jobs), drains them, and scales back to zero.

The `ohh-config` ConfigMap (in `core.yaml`) sets `FOUNDRY_QUEUE_KEY=ohh:foundry:jobs` — the single source for the queue key shared by the freshness cron, the worker, and the KEDA trigger.

### Queue depth and cost

The freshness cron only enqueues jobs for sources that actually changed. On a quiet day (no regulatory updates) the queue depth stays at zero and the worker fleet idles at zero replicas (scale-to-zero). On a day with many simultaneous gov updates, KEDA fans out to up to 20 workers to drain the queue, then scales back. This is the correct cost shape for a corpus that follows real-world publication schedules.

## Cross-references

- `scripts/foundry/scrapers.py` — `Fetcher` protocol, `HttpFetcher`, `CannedFetcher`, `content_hash`, `detect_change`, `parse_facts`, `WebSourceScout`, `DEFAULT_REGISTRY`
- `scripts/ingest/__init__.py` — `load_registry()`, `REGISTRY_PATH`
- `scripts/foundry/stage_load.py` — `StageLoadStage`, `PlaceholderEmbedder`, all row-family builders
- `scripts/foundry/store.py` — `from_env()`, `SqliteStore`, `PostgresStore`, `JsonlStore`
- `scripts/foundry/queues.py` — `from_env()`, `SqliteQueue`, `RedisQueue`
- `scripts/foundry/worker.py` — `Worker`, `Queue` protocol, `--serve`
- `infra/docker-compose.yml` — Postgres + Redis + web + foundry worker (base services)
- `infra/ingest-compose.yml` — freshness-cron + ingest-worker (this layer)
- `infra/k8s/freshness-cron.yaml` — K8s CronJob for the CDC poll
- `infra/k8s/worker.yaml` — K8s Deployment + KEDA ScaledObject for the consumer
- `infra/k8s/core.yaml` — namespace, ConfigMap (`FOUNDRY_QUEUE_KEY`), Secret template
