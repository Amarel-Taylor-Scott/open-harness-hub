# Infra & Hosting Decision Brief — serving the 500K-primitive platform

> 2026-07-06. Grounded in MEASURED workload shape: store artifacts ≈ 3–4 GB immutable files (465K cards:
> 476 MB blackbox matrix + 3×476 MB register matrices + 120 MB lexical index + ~1 GB corpus/staged JSONL);
> queries are CPU matmul + dict lookups (0.2–0.7 s warm, no GPU); writes are batch rebuilds (atomic
> replace), not OLTP. Prices = July 2026 public anchors — verify at signup. serves_truth=false (a brief,
> not a booking).

## The shape → the ranking

Our serving tier is **read-only mmap over immutable artifacts** — the cheapest possible thing to host.
It wants RAM ≥ store size (4–8 GB), any modern CPU, tiny disk (20 GB), and nothing else.

| Tier | Pick | Why / cost anchor |
|---|---|---|
| **Tonight → first users** | **Fly.io**: 1× `shared-cpu-2x` 4 GB + 20 GB volume + IPv4 | ~$15–25/mo all-in; per-second billing; our deploy layer already targets Fly; `fly deploy` from the existing topology. Minimal VM is ~$1.94/mo; IPv4 $2; volumes $0.15/GB. |
| ~~Hetzner~~ | **REMOVED — owner decision 2026-07-06** ("Hetzner is not good") | superseded by the ranking below |
| **All-Cloudflare consolidation** | **Cloudflare Containers** (beta): instance types to 4 vCPU / 12 GiB — our 4–8 GB shape FITS | ~$26–31/mo for 4 GiB provisioned memory ($0.0000025/GiB-s) + $5 Workers Paid; CPU billed on ACTIVE use only (our bursty matmuls = cheap); same account already holds domains/DNS/CDN/R2/Queues/Pages → maximal one-vendor consolidation. Risk flag: PUBLIC BETA. |
| **Commodity VM alt** | **DigitalOcean** Premium droplets (2 vCPU/4 GB ≈ $24/mo; 8 GB basic ≈ $48) | per-second billing since Jan 2026 (672 h monthly cap); the single-box Caddy multi-domain pattern transfers as-is. Render ($25+ Standard) fits our RAM shape worst of the PaaS set. |
| **Zero-ops PaaS alt** | Railway | $5 base + ~$10/GB-RAM-mo → our 4 GB shape ≈ $40+/mo — fine DX, worse fit for RAM-heavy read-only serving. |
| **Edge/CDN/tunnel** | **Cloudflare** (free tier) | Keep: free tunnel today; later free proxy/CDN in front of Fly/Hetzner + R2 for store-artifact distribution (S3-compatible, zero egress fees to CF edge). Workers are NOT the serving tier (isolate memory limits ≪ our 4 GB mmap). |
| **pgvector (managed)** | **Neon** (serverless PG, scale-to-zero) or **Supabase** (~$19–25/mo entry tiers) | Only when we outgrow file stores or need multi-writer: enable the commented HNSW (`db/postgres/schema.sql:573`), populate `object_embedding`. Self-host option: pgvector on the same Hetzner box ≈ $0 extra. |
| **Queueing / pub-sub** | Start: **none** (batch rebuilds are cron). First real queue: **Cloudflare Queues** or **Redis/Valkey on the box**; at GCP scale: **Pub/Sub + Cloud Run jobs** for the minting/flywheel pipeline. |
| **Cloud functions** | Poor fit for serving (cold start + memory); fine for webhooks/outcome-ingestion (CF Workers / Cloud Run). |
| **K8s** | **Not yet.** Two boxes + a load balancer beat a cluster below ~10 nodes of load. Adopt K8s (or Fly Machines autoscaling first) only when replicas > ~5 and deploy cadence demands it; our stateless-replica design ports trivially then. |

## Scaling playbook (matches the architecture already built)

- **Vertical first**: RAM-fit the stores (4 GB → 16 GB covers ~2M cards at current dims). Cheapest lever.
- **Horizontal = replicas**: stateless service + immutable content-hashed stores → N replicas behind
  Fly's anycast or a $0 Cloudflare LB. No coordination; the mtime-revalidation swap is the deploy.
- **Shard at ~5–10M cards**: hash-range shards, scatter-gather via the existing rank-fusion merge; OR move
  the dense lane to pgvector-HNSW/faiss behind the same `load/search` seam and let PG do the memory math.
- **The 1M-embed pipeline stays offline**: minting/rebuilds run anywhere cheap (local box tonight; a
  Hetzner worker or Cloud Run job later), publish artifacts to R2/volume, replicas swap in.

## Start setting up tonight (owner actions, ~30 min)

1. **Fly.io account** + `fly launch` from the repo's deploy topology (shared-cpu-2x, 4 GB, 20 GB volume,
   LHR/IAD region near you) → persistent URL replacing the ephemeral tunnel. (~$20/mo)
2. **Cloudflare account** (free): DNS for the product domain(s) → proxy to Fly; later R2 bucket for store
   artifacts + Queues when the flywheel goes hosted.
3. **Neon account** (free tier): create the PG instance, run `db/postgres/schema.sql`, leave HNSW for the
   swap moment — zero cost until used.
4. Keep **Ollama Cloud** as the escalation model lane (already keyed, receipts prove 71–86 % savings) —
   no GPU hosting needed anywhere in this plan.
5. Defer: Kubernetes, dedicated instances, any GPU box, Kafka-class queues — all premature at current load.

## Single-box consolidation (minimum initial cost, clean scale-out seams)

Everything this portfolio serves fits ONE 8 GB machine — because the expensive part (stores) is immutable
mmap files and the web surfaces are kit-served fronts over seams:

| On the one box | Footprint | Notes |
|---|---|---|
| Capability API (465K+ stores) | ~4 GB RAM | the only RAM-heavy tenant |
| Postgres + pgvector | ~1 GB | ONE instance, one DATABASE PER PRODUCT (separable later by per-DB dump/restore — the Teleon/Baltor separability law holds at the schema boundary) |
| All 5 web surfaces + docs site | ~100 MB | static/kit fronts behind one reverse proxy |
| **Caddy** reverse proxy | ~50 MB | name-based vhosts: UNLIMITED domains on one IP (aidoneright.dev, teleon.dev, baltor.ai, subdomains), automatic HTTPS, $0 |
| Flywheel/mint cron jobs | burst | run off-peak; artifacts atomic-swap |

- **Cost floor:** Hetzner CAX21/CX32 class (8 GB) ≈ **€6–12/mo TOTAL** for API + DB + every domain; Fly
  equivalent ~$25–35/mo (RAM pricing) with nicer deploys. $0 option exists today: the current local box +
  Cloudflare tunnels (already live) — the €6 box is step one of PAYING hosting, not of existence.
- **Multiple domains = $0 extra**: Cloudflare free DNS (per domain) → one origin IP → Caddy SNI routing.
- **Cost METRICS to track** (wire into savings_statistics): $/1K queries (box ÷ query volume), $/GB-month
  artifacts, egress $/TB, and the offset line — measured token savings ($18–$461 per benchmark batch on
  the price sweep) vs hosting (~€6–20/mo): hosting is noise against model-token savings at any real usage.
- **Scale-out seams, in order** (each a clean move, none a rewrite): ① vertical resize 8→16 GB (one
  reboot); ② split Postgres out (Neon/managed or a second box) when WRITE load appears; ③ add stateless
  API replicas (immutable stores rsync/R2-synced; Caddy/CF load-balance); ④ split products onto their own
  boxes exactly along the documented service/DB/seam boundaries when a product earns its own bill.
