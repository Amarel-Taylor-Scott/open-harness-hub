# Local Dev Tunnels And Auth

Status: local design  
Updated: 2026-06-09

This repo does not require paid cloud hosting to test the AI Done Right
portfolio. The local path is:

1. run static sites, demos, product services, workers, and data stores on
   localhost or local Docker networks;
2. expose selected local ports with temporary TryCloudflare quick tunnels when a
   public review URL is useful;
3. keep authentication and access boundaries modeled locally with service
   accounts, scoped local tokens, queue identities, and `secret_ref` placeholders;
4. treat every TryCloudflare URL as temporary preview, not production hosting.

Machine-readable plan:

```text
architecture/local_dev_tunnel_auth_runtime.json
```

Focused proof:

```bash
python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test
```

## What Runs Locally

Static launch sites:

```bash
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --restart
PYTHONPATH=. python3 scripts/serve_portfolio_sites.py --status
```

Temporary public preview URLs:

```bash
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --restart
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --status
PYTHONPATH=. python3 scripts/launch_portfolio_trycloudflare.py --stop
```

Local identity & access (separate realms per product — registration, login,
sessions, hash-only API keys; see `docs/architecture/auth-identity-kit.md`):

```bash
PYTHONPATH=. python3 scripts/identity_local_service.py --serve
```

Containerized local stacks:

```bash
docker compose -f infra/docker-compose.yml up --build
docker compose -f infra/docker-compose.platform.yml up --build
docker compose -f infra/docker-compose.context.yml up --build
```

These compose files provide local equivalents for Postgres/pgvector, Redis,
workers, product APIs, observability, object storage, and context-worker
experiments. They are local parity tools, not paid hosting.

## Tunnel Policy

TryCloudflare quick tunnels are useful for testing and review, but they are not
production hosting and they are not an auth system.

Rules:

- **No fake URLs.**
- only record real `*.trycloudflare.com` URLs printed by `cloudflared`;
- never invent a public URL;
- record `MISSING_CLOUDFLARED` when the binary is absent;
- record `TUNNEL_UNREACHABLE` when a URL is not captured in time;
- stop tunnels by exact recorded PID only;
- never store tunnel tokens or named-tunnel credentials in the repo.

## Local Auth Model

Local testing should mirror the production boundary model without requiring
cloud identity. Internal services still use service accounts conceptually, but
local development can mint scoped local tokens instead of requiring cloud
workload identity:

| Surface | Local auth mode | Notes |
| --- | --- | --- |
| Static marketing/prototype pages | `none_static_preview` | No private data, no writes, no truth promotion. |
| Demo Control Tower | `anonymous_demo_read` | Projection-only; links surfaces and manifests. |
| Product APIs | `local_internal_service_token` plus user/demo session where applicable | Must carry tenant, scope, audience, subject, expiry, and correlation id. |
| Workers | `queue_identity` | Scoped to queue and job kind. |
| Secrets | `secret_ref_only` | Use placeholders such as `secret_ref://local/demo/main`; never raw keys. |

The authoritative service-auth policy is still
`architecture/service_auth_consumption_model.json`, documented in
`docs/architecture/service-auth-and-consumption-model.md`.

## Boundary Rules

- AI Done Right is the parent/platform brand.
- Baltor governs context and truth.
- Teleon runs capabilities.
- Open*Hubs are registries and discovery surfaces only.
- Discovery is not trust.
- Output is not truth.
- Dashboards and Control Towers are projection-only.
- TryCloudflare exposes a local port; it does not make a surface production or
  trusted.

## Held Items

Do not proceed without explicit authorization for paid cloud hosting, named
production tunnels, production DNS, production secrets, live third-party
diagnostics, or network LLM calls with sensitive data.
