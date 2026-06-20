# Cloud graduation — L0 → L3 (S11)

The move to cloud is a *location change, not an architecture change*: the manifest,
gateway namespace, justfile, and vault seam are identical at every level. Each level
has an entry trigger, a monthly cost ceiling, and a rollback.

## The ladder

| Level | What | Trigger to enter | Cost ceiling | Rollback |
|---|---|---|---|---|
| **L0** (now) | Laptop + `just up` + quick tunnel | — | $0 | — |
| **L1** | Named Cloudflare tunnel + real DNS (terraform/, still laptop) | quick-tunnel URL churn becomes annoying; first external user | $0 (CF free tier) | delete tunnel, back to quick |
| **L2** | One small VM (Hetzner CX/CPX or DO basic) runs the SAME `just up`; host pulls signed images per S5b; laptop becomes a dev clone | need uptime beyond laptop hours | **$15/mo** (Hetzner CPX22 ≈ $9.49/mo post-Apr-2026, 20TB EU bandwidth; DO equivalent $24/mo — pick by region/UX) | `docker compose down`, point tunnel back at laptop |
| **L3** | Split planes (managed Postgres, object storage, per-hub containers on Fly/Cloud Run) | a MEASURED breach: p95 budget, 24h-uptime, or the $15 ceiling | per-service, each with its own ceiling, decided then | every service is a container — move it back |

Rules: never skip a level; never enter one speculatively; record the trigger that
justified the move in the pass log.

## Provider shortlist for L2 (reviewed 2026-06, revisit at entry)

- **Hetzner** — best price/perf for a single VM (CPX22 2v/4GB ≈ $9.49/mo even after the
  Apr-2026 increase; 20TB EU bandwidth); EU regions; no vendor lock. US regions ship
  only 1TB transfer — factor that for US-primary load.
- **DigitalOcean** — ~2–2.5× the price for the same specs, buys managed PG/K8s/docs UX
  if we ever want it; per-second billing since Jan 2026.
- **Fly.io** — only if L3 per-service splitting starts; not for the L2 monolith host.
- Big-3 hyperscalers — explicitly deferred: cost opacity + IAM complexity buy nothing
  at this scale.

Deeper field + K8s economics + growth scenarios: `PLATFORM-REVIEW.md` and `SCENARIOS.md`.

## Monitoring ladder (S11) — adopt in order

1. `/health` + deploy-verify + `just bench` budgets — **shipped**.
2. **uptime-kuma** container (one compose entry, ~20MB): watches every route through
   the gateway + the public tunnel URL, alerts via webhook to the events plane.
   This is the next monitoring increment.
3. Prometheus + Grafana + per-container metrics — only when >1 host or >10 containers.

## Cost & latency measures (live now)

- Latency: budgets in `services.json` → `just bench` → receipts in
  `dist/bench-receipts.jsonl`. Breach = exit 1 = CI-red.
- LLM spend: every invocation through the plane emits a receipt with usage + key —
  spend is attributable per user/service key from day one.
- Images: deploy receipts record what shipped; keep core images <200MB (alpine bases).
- The ceilings table above is binding: exceeding a ceiling without a recorded decision
  is an S10 honesty violation.
