# Fly.io deploy runbook — owner does billing, the agent does everything else

Status 2026-06-11: BUILT AND SELF-TESTED, NOT YET DEPLOYED (no Fly account yet). Owner
directive: support Fly.io now, keep switching cheap. Companion decision record:
`docs/strategy/hosting-decision-matrix.md` (~$40–52/mo expected for this plane).

## What exists (all provider-blind pieces are committed and gated)

| Piece | Where | Gate |
|---|---|---|
| Single-source topology (services, seams, scaling) | `architecture/deploy_topology.json` | generator refuses unknown service ids; queue key asserted == `scripts.foundry.queues.DEFAULT_QUEUE_KEY` |
| Generator → `fly/*.fly.toml` + `deploy/docker-compose.deploy.yml` | `scripts/deploy/generate_provider_configs.py` | `--check` (drift) + `--self-test` (12 invariants) + k8s cross-checks |
| Queue-depth Machines controller (the KEDA replacement on Fly) | `scripts/deploy/fly_worker_controller.py` | `--self-test` 12/12 (fake API: 429, capacity errors, drain cooldown, foreign-machine safety) |
| Service portability seams | `OH_BIND_HOST` (all 6 servers), `OH_SEAM_*_BASE` (showcase proxy), `AIDR_IDENTITY_BASE` (registry + teleon runtime) | showcase `--self-test`; unset envs = identical local behavior |
| K8s parity | `infra/k8s/service-plane.yaml` (now sets `OH_BIND_HOST`, fixed registry mount path), `worker.yaml` KEDA numbers cross-checked from the topology | `generate_provider_configs.py --check` |

The same image runs everywhere; only env differs. That is the whole switching story:
**Fly → anything else = re-point the seam envs and pick the scaling mechanism (KEDA on k8s,
controller on Fly, manual on compose).** No service code changes.

## Owner-only steps (the irreducible human minutes)

1. Create the Fly account, add the credit card.
2. Run `fly auth login` once in this shell (suggest typing `! fly auth login` in the session).
3. (Cloudflare already in hand) nothing else — every remaining step below is agent-runnable.

## Agent steps (after owner login)

1. `fly tokens create org -x 720h` → store as the working token; mint per-app deploy tokens
   for CI later. (flyctl can mint its own scoped tokens — no console.)
2. Follow `fly/README.generated.md` IN ORDER (it is generated from the topology):
   identity → registry → events → teleon-runtime → baltor-backend → web apps ×4 → redis →
   worker → worker-controller (postgres is phase-2). Per app: `fly apps create`,
   `fly volumes create` (stateful ones), `fly secrets set --stage` (keys listed per app,
   values from the owner's `.env`), `fly deploy -c fly/<app>.fly.toml --ha=false`.
3. Worker fleet bootstrap: after `fly deploy` of `aidr-worker`, stop the seed machine
   (`fly machine list -a aidr-worker -q | xargs -r -n1 fly machine stop -a aidr-worker`);
   set `FLY_API_TOKEN` (deploy-scoped for aidr-worker) + `REDIS_URL` secrets on
   `aidr-worker-controller`; the controller owns the fleet from then on
   (0→8 on `ohh:foundry:jobs`, receipts on stdout → `fly logs -a aidr-worker-controller`).
4. Cloudflare DNS: CNAME each product domain → `<app>.fly.dev` (proxied). `fly certs add`
   per domain if serving TLS at Fly instead of terminating at Cloudflare.
5. Run the gates against the public domains: `node e2e/ohh_public_gate.mjs`,
   `node e2e/teleon_gate.mjs`, then re-film journeys if surfaces changed.

## Eyes-open accepts (from the adversarial hosting research)

- Fly incident cadence is high (65/90d at research time); mitigations wired in: Cloudflare in
  front, self-run Redis on a volume (never Fly Managed Postgres), controller retries with
  capacity backoff (the Jun-8 ARN incident class — "can't start stopped machines" — degrades
  to slower queue drain, never job loss), `ord` as the fallback region in the topology.
- The 21 static portfolio/hub sites are NOT in this plane — they go to Cloudflare Pages free
  (`dist/` bundles); only the 4 wired apps + 5 backends + data plane live on Fly.
- `infra/k8s/web.yaml` is a stale Gradio placeholder, superseded by the topology's four web
  apps; service-plane.yaml + worker.yaml are the live k8s assets and stay cross-checked.
- Baltor backend persistence paths ride its runtime-settings namespace; before relying on
  durable Baltor state on Fly, pin those paths into the mounted volume (currently demo-grade).

## Switch playbook (the flexibility the owner asked for)

- **To any VPS/k3s (Hetzner/DO/Netcup/OVH):** `kubectl apply -f infra/k8s/` (KEDA already
  encodes the same scaling numbers) or `docker compose -f deploy/docker-compose.deploy.yml up`
  on a single box. Set the same secrets; seams resolve by service DNS automatically.
- **To DOKS:** same k8s path; managed Postgres/Valkey replace the data-plane containers by
  swapping `REDIS_URL`/`DATABASE_URL` secrets — services don't care.
- **To Azure Container Apps:** scale rules accept the identical Redis-scaler numbers from the
  topology (`queue_key`, `jobs_per_worker`); the controller role disappears (ACA = managed KEDA).
- In ALL cases `architecture/deploy_topology.json` stays the single source; add an emitter to
  the generator rather than hand-writing provider configs.
