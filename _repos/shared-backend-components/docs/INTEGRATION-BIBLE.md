# THE INTEGRATION BIBLE - frontend <-> backend, local and cloud

> The backend counterpart to `docs/DESIGN-BIBLE.md`. The DESIGN-BIBLE standardizes the UI (one shared kit, the
> components, the layouts). This file standardizes how every frontend talks to a backend, and how the same code runs
> locally and in the cloud. If another doc disagrees about integration or deployment, this wins. serves_truth=false.

## 1. The one integration law

A frontend NEVER hardcodes a backend host or port. It calls a **same-origin seam path** (`/api/<service>/...` or
`/registry/...`). The serving layer (the showcase) rewrites that seam to the real backend. The frontend code is
identical whether the backend is a local process or a cloud service. This is the exact parallel to the design law
(one shared kit, differ only by accent + copy): one integration surface, differ only by where the seam points.

## 2. The seams (the standardized FE <-> BE contract)

Source of truth: the seam table in `scripts/showcase/server.py` (`_seam_base(env_key, port)` + the table). Each seam
maps a same-origin path to a backend, resolved from the local service registry by default and overridden by an
`OH_SEAM_*_BASE` env in the cloud.

| Frontend calls (same origin) | Backend service | Local registry id | Cloud override env |
|---|---|---|---|
| `/api/identity/...` | auth / identity | `local_auth_service` (9410) | `OH_SEAM_IDENTITY_BASE` |
| `/registry/...` | registry / catalog projection | `local_openhubforai_projection_api` (9423) | `OH_SEAM_REGISTRY_BASE` |
| `/analytics/...` | event tracking | `local_event_tracking_service` (9420) | `OH_SEAM_ANALYTICS_BASE` |
| `/api/mailbox/...` | mailbox | `mailbox_local_service` (9428) | `OH_SEAM_MAILBOX_BASE` |
| `/api/teleon/...` | Teleon runtime | `teleon_local_runtime` (9430) | `OH_SEAM_TELEON_RUNTIME_BASE` |
| `/api/observer/...` | AIDevObserver session review | `observer_runtime` (9431) | `OH_SEAM_OBSERVER_BASE` |
| live-ops | Baltor admin / live-ops | `baltor_admin_demo_server` | `OH_SEAM_LIVEOPS_BASE` |

The frontend just does `fetch('/api/observer/review', {method:'POST', body})`. Same call, local or cloud.

## 3. The standardized backend service shape

Every backend is the SAME small stdlib HTTP service (the service-plane pattern). To add one, copy
`scripts/events_local_service.py` / `scripts/observer_local_service.py`:

- a `BaseHTTPRequestHandler`, JSON in/out, CORS-open (the seam is same-origin, but direct calls work too);
- `GET /health` -> `{"ok": true, "service": "<id>"}`;
- the real routes (verbs + JSON), reusing an existing engine, never rebuilding it;
- `serves_truth=false` on model/agent/candidate output; read-only unless governed;
- a `--serve [--port N]` runner and a `--self-test`;
- registered in `architecture/local_service_registry.json` (service_id, port, env, start_command, purpose).

## 4. Adding a new frontend <-> backend integration (the recipe)

1. Build the service (copy the pattern above), reusing the existing engine.
2. Register it in `architecture/local_service_registry.json` (free port).
3. Add one line to the showcase seam table: `("/api/<x>/", "", _seam_base("OH_SEAM_<X>_BASE", <x>_port))`.
4. In the frontend, `fetch('/api/<x>/...')` (same origin). Done. It works locally now and in cloud once
   `OH_SEAM_<X>_BASE` is set.
5. Add a `scripts/check_<x>_local_service.py --self-test` proof and register it.

## 5. Local deployment (what runs now)

- Backends: the service-plane (`scripts/*_local_service.py`), started from `architecture/local_service_registry.json`
  via `scripts/local_services_lib.py`. Currently up: auth 9410, events 9420, registry 9423, mailbox 9428,
  teleon-runtime 9430, observer 9431.
- Frontends: the showcase per surface (`OH_PRODUCT=<brand> python3 -m scripts.showcase --port N` -> `web/<brand>/`),
  with the seams resolving to the local service-plane. Five surfaces, five ports, optionally tunneled for sharing.
- Reference: `docs/architecture/local-dev-tunnels-and-auth.md`.

## 6. Cloud deployment (ready to move)

- Each backend service deploys as its own container/service; set its public URL in the consumer's `OH_SEAM_*_BASE`.
- Each frontend surface deploys via the showcase (one service per `OH_PRODUCT`), `OH_BIND_HOST=0.0.0.0`, the platform
  injects the port; set the `OH_SEAM_*_BASE` envs so the seams point at the cloud backends.
- The same frontend code and the same seam paths work unchanged; only the `OH_SEAM_*_BASE` values differ.
- References: `_repos/shared-backend-components/context/architecture/fly-deploy-runbook.md`, `docs/architecture/service-auth-and-consumption-model.md`,
  `_repos/_shared/architecture/surface-deploy.md`.

## 7. Governance (the integration is governed, not just plumbed)

- Identity/auth flows through the `/api/identity/` seam (`docs/architecture/auth-identity-kit.md` +
  the service-auth/consumption model); a service consuming another presents a service account or delegated call.
- Backend output that is model/agent/candidate-derived carries `serves_truth=false`; only deterministic, verified,
  human-approved records may assert truth. BYO keys are used for one request and never stored.
- Read order for an engineer/designer wiring a surface: this file -> `docs/DESIGN-BIBLE.md` (the UI) ->
  `scripts/showcase/server.py` (the seam table) -> the service-plane services.

*Warrant: written on owner intent (the FE<->BE standardization question). Grounded in the real seam table
(`scripts/showcase/server.py`), the service registry (`architecture/local_service_registry.json`), and the deploy
runbooks. serves_truth=false.*
