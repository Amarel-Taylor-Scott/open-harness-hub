# Deployment plan — local testing (Cloudflare) → fully deployed

> 2026-06-25. Goal: the **same code/architecture runs locally (free, Cloudflare-tunneled) and in production**, differing
> only by config — "build toward scale, not replace later." Grounded in EXISTING assets: `deploy/`
> (docker-compose.localtest/emulators/deploy + `tofu/` IaC), `local_emulators/`, `src/teleon/runtime/execution_providers/
> cloudflare_workers.py` (BYO compute), tunnel tooling, `docs/architecture/local-dev-tunnels-and-auth.md` +
> `service-auth-and-consumption-model.md`. Cloud-agnostic by the `record_store` / execution-provider ports —
> Cloudflare is the default, not a lock-in.

## The scale architecture → Cloudflare → local equivalent
| Scale-arch component (from the review) | Production (Cloudflare default) | Local test (same code) |
|---|---|---|
| Operational index — `scale_index` (SQLite, sharded) | **D1** per leaf-shard (or external **Postgres+pgvector** at billions, behind the `record_store` port) | Wrangler/Miniflare **D1** (local SQLite — `scale_index.db` *is* this) / local Postgres |
| Vectors + ANN (#16) | **Vectorize** (or pgvector HNSW) | local hnswlib / sqlite-vss / Vectorize-emu |
| Object-store / cold (Parquet) | **R2** | Miniflare **R2** / `local_emulators` / MinIO |
| Durable queue (loops → workers) | **Queues** | Miniflare **Queues** |
| Compute — loops as stateless workers | **Workers** (+ containers on Fly/Cloud-Run via `tofu` for the Python services) | `wrangler dev` / `docker-compose.localtest.yml` |
| Inference (Kimi/GLM + deterministic) | **Workers AI** + the Ollama Cloud lane (BYO) | local Ollama + `local_emulators/model_emulator.py` |
| CDC log / coordination (#20) | **Durable Objects / KV** (or a Kafka/Redpanda for heavy throughput) | Miniflare DO/KV / a local `cdc.jsonl` |
| git projection (#19) | GitHub → **Pages** deploys from git | local git |
| Sites / hubs (HTML) | **Pages** | local serve + `cloudflared` tunnel |
| Secrets / service auth | Wrangler secrets + service bindings | `.env` + `check_local_dev_tunnel_auth_runtime.py` |
| External exposure | named Cloudflare tunnel | **trycloudflare** tunnel (`launch_service_plane_tunnels.py`) |

The mapping is near-1:1 — Cloudflare's primitives ARE the scale tiers, which is why local Wrangler/Miniflare can run
the production shape on a laptop, free.

## Local testing loop (today, free)
1. `docker-compose -f deploy/docker-compose.localtest.yml up` — the Python services (loops + search API) + a local
   Postgres/pgvector + R2/object emulator. (Emulators in `local_emulators/`.)
2. `scale_index.db` (SQLite) is the local D1; the loops ingest into it incrementally; search served from it.
3. Expose any service with a **trycloudflare tunnel** (`scripts/launch_service_plane_tunnels.py`) → a public URL for
   testing webhooks / the Observer upload UI / the hubs, with no cloud account.
4. `check_local_dev_tunnel_auth_runtime.py --self-test` + `check_teleon_local_emulation.py` keep local parity honest.

## Fully deployed (production)
1. **IaC**: `deploy/tofu/` (OpenTofu) provisions the cloud — Postgres+pgvector (Neon/Supabase/RDS) for the heavy
   operational/vector tier, object-store, and the container host (Fly.io — `fly/` — or Cloud Run) for the Python
   services/workers.
2. **Cloudflare edge/managed**: Pages (sites), R2 (cold), Vectorize (ANN, optional), Workers AI (inference), D1
   (per-shard edge metadata, optional), Queues, named tunnels — wired via Wrangler + service bindings.
3. **git → deploy**: push to `main` (the promoted projection) → Pages build + a CI deploy of the workers/services.
4. **Same code**: the `record_store` + execution-provider ports mean local SQLite/Postgres ↔ prod D1/Vectorize/pgvector
   is a CONFIG swap (a URL in `.env`), not a rewrite. `check_cloud_agnostic_execution.py` guards this.

## Honest scale nuances
- **D1 has per-DB size limits** → at billions, either shard across many D1 DBs (our hash-prefix leaf shards map 1:1 to
  D1-per-shard) OR use external **Postgres+pgvector** for the big operational store. Both sit behind the `record_store`
  port — choose by scale, no lock-in.
- **Cloudflare for edge/compute/sites/queues/object/inference; the giant metadata+vector store is the one piece that
  may live outside Cloudflare** (managed Postgres+pgvector) at trillions. Keep it agnostic.
- **Inference**: Workers AI for edge/cheap deterministic-substitution paths; the Ollama Cloud lane (Kimi/GLM) stays the
  BYO dev/bulk lane. Both behind the LLM port.

## Build order (toward this, queued)
1. `wrangler.toml` declaring D1 + R2 + Queues + Vectorize + Workers-AI bindings, so `wrangler dev` (local) and
   `wrangler deploy` (prod) are the same. (#21)
2. `record_store` → D1/Postgres backend (the `PostgresRecordStore` stub) selected by a `.env` URL; `scale_index` ↔ D1.
3. CDC log → Queues; loops → Workers/queue-consumers (#20, #loops-as-workers).
4. `deploy/tofu` apply for the external Postgres+pgvector + container host; Pages for sites.
