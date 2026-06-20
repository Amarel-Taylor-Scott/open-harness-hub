# Hosting Decision Matrix — every lane, verified costs (research date 2026-06-11)

Six parallel adversarial research passes (Fly deep-dive · managed scale-to-zero · VPS/k3s ·
PaaS · bare-metal/budget · MCP/agent-automation) feeding one decision. All prices were
verified on official pricing pages / billing APIs on 2026-06-10/11; key sources inline.
Companion adversarial narrative: `architecture-swot-hosting-review.md` §7.

## Owner requirement stack (2026-06-11)

1. Cheap — target well under $100/mo at launch scale.
2. One provider hosts frontends + backends + data in the SAME region (low latency).
3. **HARD: agent-automatable** — owner creates the account + confirms billing; an AI agent
   (MCP server, or scoped API token + CLI/Terraform) stands up everything else with zero
   console clicks.
4. Workers must scale up AND down (to zero) on queue depth; cloud-function-like burst compute.
5. Cloudflare stays in front (DNS/CDN/tunnel); static frontends can ride Cloudflare Pages free.
6. Owner leaning at research time: **Fly.io + custom Machines controller**.

## Workload shape priced everywhere

- 6 always-on small backend services (Python, 256–512MB each, low idle CPU)
- 4 mostly-static frontends (assume Cloudflare Pages free unless noted)
- Postgres + pgvector (~25GB) · small Redis/Valkey (job queue)
- Burst workers 0→8 × (1 vCPU/2GB), ~120 fleet-hours/mo, queue-driven scale-to-zero
- Single US region · ~50GB/mo egress

## Master table (monthly, our shape)

| Option | $/mo verified | Agent-setup score (0–10) | Scale-to-zero workers | Managed PG/Redis | Biggest risk |
|---|---|---|---|---|---|
| **Fly.io** (backends-only, self-run PG/Redis) | **$39 spec / $42–52 realistic** (−~$10 with 40% Machine Reservations; −$4 dropping dedicated IPv4s) | 8.5 — flyctl is agent-gold; one `fly auth login`, agent mints scoped tokens; `fly mcp server` experimental; **no Terraform** (archived) | **Custom controller required** (Machines API; rate limits fine). Official fly-autoscaler can't reach zero + dormant since 2024-06 | None we'd use (MPG $282+; Upstash Redis exists) | **65 incidents/90d (27 major)**; Jun 8 ARN host-capacity error blocked *starting stopped machines* — the exact scale-to-zero failure mode; fee churn (snapshot billing Jan 2026, private-net Feb 2026) |
| **DigitalOcean DOKS comfort** (2×4GB nodes + managed PG + Valkey) | **$81 base** (1GB PG, tight) → **$97–117** with 2–4GB PG; burst node pool +$4–13 | **9 — best non-hyperscaler**: official MCP covers droplets/DOKS/managed DBs/DNS (pushed 2026-06-11); doctl + Terraform complete; custom-scoped tokens | **KEDA as-built** (our `infra/k8s` manifests unchanged); per-second billed burst node pool since Jan 2026 | Yes — PG $15.15+, Valkey $15 | Cost creep (HA control plane +$40, PG tier up); ~2× Fly/Hetzner price |
| **Azure Container Apps** | **≈$79** ($75 pure-idle floor) | 9 — az CLI complete via service principal; official Azure MCP misses Container Apps namespace | **Native KEDA semantics** — scale rules ARE KEDA (redis scaler works, 0→N); ACA Jobs for run-to-completion | Yes — PG B1ms $16.09 (real SLA), **Managed Redis B0 $11.68** | Heaviest human bootstrap (MFA, subscription); idle-rate eligibility rules (chatty service bills 8× CPU); Log Analytics surprise ($2.30/GB, on by default) |
| **GCP Cloud Run** | **≈$73** ($91 w/ SLA-grade db-g1-small; **$126 if services need background CPU**) | 9.5 — 50+ Google-managed remote MCP servers (Cloud SQL create incl.); gcloud/TF fill gaps | No KEDA. Re-platform queue to Pub/Sub push, or worker pools + self-built scaler | PG db-f1-micro $7.67 (no SLA); **cheapest Redis $22.48** | Idle min-instances are **CPU-throttled** (our services do background work → instance-based 3× price); egress $0.12/GB |
| **Hetzner CPX41 US** (16GB, k3s everything) | **$56 all-in** ($46.49 + 20% backups + IPv4) | 7 — hcloud CLI/TF complete BUT **projects + tokens are console-only**; possible ID verification | KEDA as-built on the box (burst = free headroom) | None — self-run only | Account-level: opaque risk flags/KYC closures; **3 price hikes in 5 months of 2026**; US traffic cut to 4TB (was 20TB) |
| Railway (Pro) | $64 nominal / **$40–55 actual** (usage-metered) | 7.5 — official MCP (in CLI), GraphQL API; no official TF | App-sleeping is fragile: any held Redis connection blocks sleep | Containers on volumes (usage-billed) | $20 seat forced (5GB Hobby volume cap); egress $0.05/GB |
| Northflank | **≈$58** | 7.5 — full API/CLI/JSON templates; no official MCP | Per-second **Jobs** triggered via API (self-wired) | Addon PG/Redis (real backups) | ~25-person company carrying a wide surface |
| Vultr 16GB k3s | $96 | 7 — API/TF/CLI complete + community MCP; managed PG $15 | KEDA as-built | PG yes; Valkey opaque pricing | 2024 ToS scare; thin support |
| AWS (Fargate+RDS+ElastiCache) | $100+ before ALB/IPv4 fees | **10** — aws-api MCP = full CLI surface | No native queue scaler for ECS (EventBridge glue) | Yes (priciest) | Cost + assembly complexity at this scale |
| Render | **$127 — eliminated** | 7.5 (good MCP, workspace-wide key) | **None on paid tiers** | PG $19+/Key-Value $10 | Per-service sticker stacking punishes exactly our shape (user's skepticism confirmed) |
| Koyeb | $113 ($42–50 w/ external PG) | 6.5 — thin beta MCP | Best-in-class light sleep (~200ms) on standard instances | PG $59.52 (!); volumes "testing only" | **Acquired by Mistral 2026-02-17**; roadmap is theirs now |
| **Netcup RS 4000 G12** (Manassas VA — 12 ded. cores/32GB ECC/1TB NVMe) | **≈$40** | 5.5 — REST API for day-2 (reinstall/rDNS/firewall) but **ordering is a manual German webshop**, no TF | KEDA on the box | None | Day-0 friction + vetting; DE support hours |
| OVH Eco SYS-1 US (6c/12t/32GB ded.) | **$33** (+1mo setup) | 6 — full day-2 API incl. rescue/IPMI; **Eco ordering broken in TF** (issue #1176) | KEDA on the box | None | Eco support = days; prev-gen hardware |
| Contabo VPS 40 (12vCPU/48GB) | **$27** | 7 — official API/CLI/TF (rare at this price) | KEDA on the box | None | **20–40% CPU steal** — disqualified for Postgres |
| ReliableSite 32GB dedicated NYC | $39 | 4 — real API but IP-whitelisted; no TF | on-box | None | DDR3 silicon; ticket-speed hardware swaps |
| Latitude.sh bare metal | $296 | **9.5 + official MCP** (Oct 2025) | on-box | None | 6× budget for automation elegance |
| Oracle Always Free ARM (4 OCPU/24GB) | **$0** | 6 — full API/TF/MCP suite, strict signup | on-box | OCI services | Tenancy termination horror stories persist 2026 → **staging clone only** |
| Modal (workers ONLY) | **$0** (≤$30/mo credit; $7.58 list) | 9 in its lane — Python-code-first | **Native, the whole point** | n/a | Workers reach Redis over public internet (auth/TLS or tunnel) |
| Equinix Metal | — | — | — | — | **EOL 2026-06-30; servers get deleted. Do not build.** |

Sources (headline): fly.io/docs/about/pricing + status.flyio.net + isdown.app (2026-06-11) ·
prices.azure.com retail API · cloud.google.com/run/pricing · digitalocean.com/pricing ·
docs.hetzner.com price-adjustment table (Apr 1 2026 rates) · docs.railway.com/pricing/plans ·
northflank.com/pricing · render.com/docs/postgresql-refresh · koyeb.com/docs + TechCrunch
2026-02-17 · netcup.com/en/server/root-server + Manassas page · eco.us.ovhcloud.com ·
contabo.com/en-us/vps + registry.terraform.io/providers/contabo · reliablesite.net ·
latitude.sh/pricing + MCP changelog 2025-10-20 · modal.com/pricing ·
docs.oracle.com Always-Free + community termination threads · DCD on Equinix Metal EOL.
Full per-lane reports with every URL live in the 2026-06-11 session ledger entry.

## Agent-automation read (the hard requirement)

- **MCP is not the real gate** — a scoped API token + CLI/Terraform is equally automatable
  from Claude Code; MCP matters for shell-less clients and typed guardrails. Judge providers
  on **API completeness + token bootstrap**, not MCP presence. HashiCorp's official
  terraform-mcp-server covers any provider with a good TF provider anyway.
- Best agent stories at our price point: **Fly** (one human login → agent self-mints scoped
  tokens, deploys machines/volumes/secrets/certs headless) and **DO** (official MCP spanning
  20+ services incl. managed PG/Valkey/DOKS/DNS + custom-scoped PATs).
- Hyperscalers score highest in the abstract (AWS 10 / GCP 9.5 / Azure 9) but pay for it in
  signup friction + cost at our scale.
- The cheap dedicated lane mostly FAILS the requirement at order time (manual webshops,
  TF gaps) even when day-2 APIs are good; RackNerd/WholesaleInternet/Joe's fail outright
  (no API); IONOS fails on billing trust.
- Cloudflare's own MCP (Jan 2026, full 2,500-endpoint API) makes the DNS/edge layer fully
  agent-drivable regardless of compute pick.

## Recommendation (updated for the agent-automation requirement)

1. **Fly.io — the leaning pick survives adversarial review at ~$40–50/mo**, cheapest
   low-ops option that meets every requirement, with two eyes-open accepts: the incident
   cadence (mitigated by Cloudflare in front, self-run PG on volumes — never MPG — and a
   controller that retries on capacity errors; ord as fallback region) and writing the one
   missing piece, the **queue-depth Machines controller** (~50–100 lines; rate limits and
   API are friendly; justified because fly-autoscaler can't reach zero and is dormant).
   Buy Machine Reservations (40% off shared compute) once the shape stabilizes.
2. **DigitalOcean DOKS — the boring-safe pick at ~$97–117/mo**: KEDA manifests run
   as-built, managed Postgres takes the 25GB pgvector corpus off the pager, and the
   official MCP is the best agent story outside hyperscalers. Pay ~2× Fly for sleep.
3. **Azure Container Apps — the dark horse at ~$79/mo** if literal KEDA semantics matter
   more than reusing raw K8s manifests: scale rules ARE KEDA (redis scaler, 0→N), Managed
   Redis B0 $11.68 is the cheapest SLA-backed Redis anywhere, PG B1ms has a real SLA.
   Accept the heaviest signup friction and translate manifests → ACA config.
4. **Wildcards that compose with any pick**: Modal hosts the burst fleet for $0 at our
   volume (removes the custom-controller need entirely — but adds a second provider and
   public-internet queue access); Oracle Always-Free ARM is a $0 staging clone (never
   primary prod); Netcup RS 4000 Manassas (~$40) is the best raw-hardware $/GB in the US
   if we ever want a dedicated 32GB box and will eat manual ordering.

**What changes the answer:** if the owner won't accept Fly's incident history → DO. If
monthly cost must stay nearest $50 with managed-grade reliability → ACA. If the worker
fleet grows past ~8 concurrent or needs GPUs → Fly Machines or Modal lean further ahead.
If agent-bootstrap-with-zero-clicks is weighted above all → DO (MCP) or Fly (CLI).
