# services/ — the service layer

Two **product services** over one **shared platform plane**. This folder is the thin *service layer*:
entrypoints, contracts, and the registry. The implementation stays in `scripts/` (libraries by
concern); a service `owns` scripts packages, it doesn't duplicate them. Canonical design:
`docs/architecture/backend-services-and-platform.md`. Machine-readable map: `services/registry.yaml`.

## Layout
```
services/
  registry.yaml                  single source of truth: every service + tier + owned scripts/ pkgs + command
  products/
    harness_hub/entrypoint.py        OpenHubForAI (request) — serves web/openhubforai/ (OH_PRODUCT pin)
    baltor/entrypoint.py Baltor / Baltor (request) — serves web/baltor/
  platform/_shared/telemetry.py  the cross-cutting telemetry contract (logs · metrics · traces)
  worker/celery_app.py           opt-in Celery adapter for the async + scheduled tiers
  scheduler/                     scheduled-tier DAGs live in infra/airflow/dags/
```
The shared **platform services** (ingestion · foundry · measurement · enrichment · retrieval ·
governance) are declared in `registry.yaml` with their owned `scripts/` packages; their code lives in
`scripts/` today and migrates behind these boundaries incrementally (non-breaking).

## Service consumption and auth

Cross-service access is a product requirement, not an implementation detail. Use
[`docs/architecture/service-auth-and-consumption-model.md`](../docs/architecture/service-auth-and-consumption-model.md)
as the current contract:

- browser users authenticate with OIDC/session auth;
- external SDKs, CLIs, and publishers use scoped API keys or OAuth clients;
- internal services use distinct service accounts, short-lived scoped tokens,
  and mTLS/SPIFFE or cloud workload identity in production;
- queue workers authenticate as workload identities with least-privilege queue
  and datastore rights;
- no service shares a god token, and raw secrets are never stored in repo files;
- every privileged call carries tenant, purpose, scope, correlation ID, and
  audit/receipt context.

Machine-readable policy:
[`architecture/service_auth_consumption_model.json`](../architecture/service_auth_consumption_model.json).
Run the focused gate after changing `registry.yaml` or service auth policy:

```bash
python3 scripts/check_service_auth_consumption_model.py --self-test
```

## Run a service
```bash
# product doors (each pins its front-end folder + brand via OH_PRODUCT; telemetry wired)
python -m services.products.harness_hub.entrypoint --port 8000
python -m services.products.baltor.entrypoint --port 8001
#   …or both behind their own tunnels: bash scripts/serve_two_products.sh

# async tier — default light worker (no extra deps) OR the Celery adapter (opt-in)
python -m scripts.foundry.worker --serve
celery -A services.worker.celery_app worker -Q foundry,ingest,enrich,measure -l info   # needs requirements-platform.txt

# scheduled tier — cron / Celery beat / Airflow (infra/airflow/dags/)
# full local platform (2 products + shared plane + datastores + observability):
docker compose -f infra/docker-compose.platform.yml up --build
```

## Rules
- A service imports from `scripts/`, **never** from another service. Cross-service talk is the queue
  or the event bus (`registry.yaml` `comms`), not a Python import.
- One telemetry contract: `from services.platform._shared import telemetry` (logs/metrics/traces).
- The core image stays light; Celery/Prometheus/OTel are opt-in (`requirements-platform.txt`,
  `--build-arg INSTALL_PLATFORM=1`).
