# Platform & Pricing Review — hosting, data, K8s, functions (Pass 9)

Status: decision record. Prices verified June 2026 from public comparisons — re-verify
at adoption time; cloud pricing drifts. This review feeds S11 (graduation ladder) and
S12 (abstraction seams). Nothing here changes the ladder's discipline: **never move
speculatively; every move needs a measured trigger.**

## The frame

We are L0 (laptop + tunnel) heading to L1/L2. The user direction adds: heavy eventual
reliance on **K8s + cloud functions + flexible database schemas**. The answer is NOT to
adopt them now — it's to keep every artifact **K8s-ready and function-ready** so the
move is a relocation, not a rewrite (S12 portability gates):

- 12-factor discipline: config via env only, stateless containers, logs to stdout,
  state only in declared volumes → the same images run on compose today, K8s later.
- `services.json` is our portable topology: kind/routes/health/budgets. Compose reads
  it now; a Helm chart or K8s manifests can be GENERATED from it later (same pattern
  as gen_caddy.py). The manifest is the abstraction; orchestrators are adapters.
- Handlers stay framework-thin (route → plain function) so any plane can be repackaged
  as a cloud function without touching business logic.

## Container hosting (L2/L3 candidates)

| Platform | Pricing shape (Jun 2026) | Strengths | Watch out |
|---|---|---|---|
| **Hetzner / DO VM** (L2 default) | ~$5–15/mo flat | Same `just up` as laptop; zero new concepts; predictable | You operate it (we already do) |
| **Render** | per-user ($0 hobby / $19 pro) + per-service compute (starter ~$7/mo; managed PG from ~$6/mo); runs on AWS | Closest Heroku successor: managed PG w/ PITR, workers, cron, flat bills | Always-on pricing gets expensive for bursty loads; single-region |
| **Fly.io** | usage-based; small VMs ~$2–3/mo; no fixed tiers | Containers at the edge, 30+ regions; cheap at low scale; volumes | More Fly-specific ops (flyctl); volume reliability history; no BYOC |
| **GCP Cloud Run** | per-request + CPU/RAM-seconds; scale-to-zero; generous free tier; egress ~$0.12/GB | Best serverless-container fit for our stateless planes; mature | Stateless only; session affinity best-effort; GCP IAM learning curve |
| **AWS Lambda** | GB-seconds + REQUIRED API Gateway ($10–35/mo at 10M req) | Fastest cold starts | The only one needing a paid gateway; per-fn packaging diverges from containers |
| **Railway** | $5/mo hobby min + usage | Fastest deploy DX | Containerized DBs lack PITR/replicas; pricier at scale |
| **Northflank/Coolify** | BYOC / self-host | If we ever want PaaS UX on our own VMs | Another platform to learn; defer |

**Decisions.**
- **L2 = plain VM (Hetzner/DO)** — unchanged. The platform is already self-orienting;
  a PaaS would duplicate what `just deploy` does.
- **L3 stateless planes → Cloud Run first** (scale-to-zero matches bursty hub traffic;
  containers unchanged). Fly.io is the alternative if edge latency ever becomes the
  measured breach. Lambda rejected: gateway tax + packaging divergence.
- **K8s**: adopt **managed only (GKE Autopilot / EKS)** and only at >1 host + >10
  containers (S11 monitoring rung 3 trigger). Until then: compose, with K8s-readiness
  enforced by S12. Self-managed K8s: never at this team size.

## Data layer

| Need | Now (L0–L2) | Later (L3) | Seam |
|---|---|---|---|
| Identity/realms | user's service (file/SQLite per realm) | Postgres per realm schema | repository fns only — no ORM lock-in |
| Platform state (keys, connections, receipts) | JSON file (core) | **Postgres + JSONB** | one storage module; `DATABASE_URL` env flips it |
| Events/analytics | JSONL + `/summary` | Postgres → **BigQuery export** when >1M events/mo or cross-product funnels need SQL warehouse | events plane POST is the contract; warehouse is a downstream sink |
| Local analytics | — | **DuckDB** over the JSONL/Parquet before paying for BigQuery | same SQL dialect family |

**Flexible-schema policy (S12):** relational spine + JSONB `props` column for the
flexible part; every record carries `schema_version`; migrations forward-only;
append-only for events/receipts. This gives schema flexibility WITHOUT NoSQL lock-in,
and BigQuery ingests it natively when the time comes.

## Why this isn't fragile

Every vendor above is reachable through a seam we already own: the manifest
(topology), env/vault (config), the events POST (analytics), ports/adapters (S12) for
email/payments/LLM. Switching any of them is an adapter swap + a manifest edit + a
pass-log entry. The forbidden state is code that knows a vendor's name outside its
adapter file.
