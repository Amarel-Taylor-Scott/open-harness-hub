# production/ — the runnable platform scaffold (Pass 1 → Pass 6)

**Claude Code: start at `../START-HERE-CLAUDE-CODE.md` — it has the paste-in prompt,
the honesty table, and the ordered next targets.**

Goal: productionize the AI Done Right prototypes into a locally working,
TryCloudflare-accessible, end-to-end platform — one proof-backed increment per pass,
no fake URLs/secrets/providers, gaps documented honestly.

## What this folder contains

| Path | What it is |
|---|---|
| `core/` | **platform-core** — the shared backend plane (Node, zero-config). Auth + registration, user API keys, standardized service↔service handshakes, user-managed MCP/tool connections, analytics + A/B event sink, **Shared LLM Plane** (OpenAI-compatible router → real Anthropic/OpenAI keys only), HMAC-signed receipts. |
| `services.json` | **The self-understanding manifest** — one file the gateway, deployer and tunnel all read: every service, its kind (container/host/static), routes, health, start command. One path namespace (`/api/<plane>/*`) identical on localhost, tunnel, and prod. |
| `justfile` | **The one-click interface + S5a pipeline contract**: `just up` · `just deploy` (self-orienting) · `just tunnel` · `just plan` · `just vault-*` · CI stages (`lint/test/package/smoke`). |
| `scripts/deploy.py` | **Self-orienting deploy**: fingerprints every service, diffs against last shipped state, rebuilds/restarts ONLY what changed, regenerates routes on manifest change, health-verifies through the gateway, appends a signed deploy receipt. Stdlib-only. |
| `scripts/gen_caddy.py` | Generates the Caddyfile from `services.json` (`--check` = CI drift gate). |
| `vault/` | **Secrets vault** (SOPS + age — decision record in `vault/README.md`): encrypted-at-rest secrets in-repo, age key outside it, `just vault-edit/export`. OpenBao is the graduation path. |
| `docker-compose.yaml` | One command: Caddy serving **all 24 prototype surfaces** statically + platform-core behind `/api/*` and `/llm/*`, optional `--profile tunnel` TryCloudflare quick tunnel. |
| `Caddyfile` | The static-sites + reverse-proxy config. |
| `scripts/tunnel.sh` | TryCloudflare quick tunnel for any local port (dev/demo). |
| `contracts/` | The standardized contracts: `SERVICE-CONNECTIONS.md` (identity tiers, Baltor↔Teleon handshake, scopes), `EVENTS.md` (one event shape, A/B end-to-end definition). |
| `standards/STANDARDS.md` | **The production handbook** — S1–S10 lifecycle standards (design, Mode Protocol, API/auth, testing pyramid, CI/CD incl. S5a pipeline contract + S5b pull-based deploy, distribution, monitoring, secrets, flip-to-public, honesty), each with rule/contract/proof/status. |
| `ci/github-actions.yaml` | The adoptable pipeline (S5): lint→test→build→package(SBOM+cosign)→deploy→smoke. Refactor target: thin orchestration calling `just` stages only. |
| `terraform/` | Skeleton: Cloudflare named tunnels + DNS per surface + generated service secrets. Not yet applied (G-5). |

## Run it

```bash
cd production
just vault-init && just vault-edit   # or: cp .env.example .env and fill it in
just up                              # secrets → routes → containers → status
just tunnel                          # public https://<random>.trycloudflare.com
just deploy                          # after any change: touches only what changed
```

Without `just`: every recipe body is plain shell — read `justfile` and run the lines.

Smoke test (real round-trips, no mocks):

```bash
curl -s localhost:8080/api/healthz
curl -s -X POST localhost:8080/api/v1/auth/register -H 'content-type: application/json' \
  -d '{"email":"ada@example.com","password":"hunter22","product":"baltor"}'
# → token; then create a key, post an event, call the LLM plane (needs a provider key in .env)
```

## Gap ledger (honest — update every pass)

| # | Gap | Status |
|---|---|---|
| G-1 | Prototype UIs (OhAuth, OhApiKeys, OHExp) still run on mock data — not yet wired to `/api/*` | **partially closed** — `shared/oh-identity.js` + the Identity Wiring prototype cover auth/keys against the canonical identity service; remaining: fold into the kit's OhAuth/OhApiKeys pages + OHExp → events beacon |
| G-2 | Registries have no real CRUD/search backend (BACKEND-STACK.md contract) | not started — needs per-hub store + Meilisearch |
| G-3 | Receipts are HMAC-signed records, not Sigstore/Rekor | accepted local stand-in; shape is forward-compatible |
| G-4 | LLM plane: no streaming, no per-key rate limits/quotas | queued |
| G-5 | Terraform written but never applied; no host-provisioning module yet | skeleton only |
| G-9 | `deploy.py` + `gen_caddy.py` + `justfile` written here, not yet executed on the host (G-8); fingerprints use size+mtime, not sha256 | **run `just plan` locally to validate; tighten hashing when artifacts get checked in** |
| G-10 | Vault flow requires `sops` + `age` installed; falls back to plain `.env` honestly | by design — see vault/README.md |
| G-6 | Auth is platform-core JWT, not Keycloak/Ory SSO | acceptable for local; swap point documented |
| G-7 | JSON-file persistence; Postgres swap needed beyond demo scale | queued with G-5 |
| G-8 | This workspace cannot execute docker/terraform itself — everything here ships as runnable files, verified by review + the smoke tests above on the user's machine | permanent constraint, by design |
| G-11 | Host safety classifier blocks agent execution of downloaded bundle code (`just` fetch, compose build, direct node) — code REVIEWED clean (Pass 7); needs the operator to run the Pass-7 one-liner or grant a Bash permission rule | **blocking Phase 0.1 completion** — everything short of execution is done |

## Pass log

- **Pass 1 (2026-06-09):** scaffold created — platform-core, compose+Caddy+tunnel,
  contracts, terraform skeleton, audit doc (`../Productionization Pass 1 — Audit and Plan.html`).
- **Pass 2 (2026-06-09):** `../shared/oh-identity.js` — realm-aware client for the
  CANONICAL identity service (`scripts/identity_local_service.py`, 12 realms, no SSO)
  + `../Identity Wiring — Account Flow Prototype.html` (register→onboard→portal→keys,
  realm isolation, LIVE vs SIMULATED honesty).
- **Pass 3 (2026-06-09):** `../shared/oh-service-auth.js` + `../Service Connections —
  Dev Console.html` — service↔service dev-token slice as a PROPOSED contract
  (`/api/identity/<realm>/service/*`): scoped from→to tokens, raw-once, verify/revoke.
- **Pass 4 (2026-06-09):** `standards/STANDARDS.md` (S1–S10 with proofs) +
  `ci/github-actions.yaml` + `../AIDR Standards — Production Handbook.html`.
- **Pass 5 (2026-06-09):** CI/CD platform decision (`../CICD Options Review — S5
  Decision.html`): GitHub Actions as orchestrator; S5a pipeline contract (logic in
  `just` recipes); S5b pull-based deploy (host cosign-verifies and pulls).
- **Pass 6 (2026-06-09):** the self-orienting local platform — `services.json` manifest,
  `deploy.py` (orient→plan→act→verify→receipt, incremental), `gen_caddy.py` route
  generation + drift gate, `justfile` one-click interface (S5a made real), SOPS+age
  vault with decision record. Routes unified: one `/api/<plane>/*` namespace everywhere.
- **Pass 7 (2026-06-09, Claude Code on the host) — bundle landed; Phase 0.1 PARTIAL:**
  handoff fetched from the design share URL, landed losslessly at
  `design_handoff_platform_productionization/` (raw export archived at
  `dist/handoff-archives/aidoneright-productionization-2026-06-09.tgz`); transcript +
  READMEs + START-HERE + backlog read. Executed: repo `.gitignore` now covers `.env` +
  deploy state; `.env` written (SITE_ROOT=<repo>/dist/sites/openharness-design; locally
  generated CORE_/SERVICE_ secrets; LLM keys empty → plane 501s honestly);
  `gen_caddy.py` regenerated routes (was STALE vs services.json — the drift gate works);
  `deploy.py --dry-run` ORIENT/PLAN green (3 services; note: export the .env when
  running scripts without `just` dotenv-load). CODE REVIEW of the runnable surface:
  core/server.js (272 lines, express-only, no exec/eval/child_process, outbound ONLY
  api.anthropic.com|api.openai.com and only when keys are set), Dockerfile = standard
  node:20-alpine, tunnel.sh = clean cloudflared wrapper. **BLOCKED ON PERMISSION (G-11):**
  the host's safety classifier denied (a) the `just` binary fetch, (b) `docker compose
  up --build` of the bundle, (c) direct `node core/server.js` — downloaded-code
  execution needs explicit operator authorization. Operator one-liner to clear:
  `cd design_handoff_platform_productionization/production && set -a && . ./.env && set +a && docker compose up -d --build && python3 scripts/deploy.py --status`.
  Per this bundle's own rule, the next agent pass recreates the events/A-B plane
  natively (Python, repo patterns, EVENTS.md as the contract) — reference code stays
  reference.
