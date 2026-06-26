# Cloud hosting blueprint — from the local plane to K8s/cloud (skeleton, owner-gated)

Date 2026-06-11 (owner-requested). This maps the PROVEN local service plane onto cloud
infrastructure without changing any contract: the same registries stay the single source
(`architecture/local_service_registry.json`, `identity_realm_registry.json`,
`model_provider_graph.json`, `contract_registry.json`), the same env names switch providers,
and the same checks gate every plane. Nothing here is deployed yet — `infra/k8s/` is the
runnable-shaped skeleton; applying it is an owner action (domains/DNS/billing).

## 1. Topology (per the portfolio law)

One region, one private network; **Teleon and Baltor separable** (own namespaces, data,
identity, IaC; versioned API between them; local fallback preserved). Three namespaces +
a shared plane:

| Namespace | Workloads | State |
|---|---|---|
| `shared-plane` | identity · registry · events · ingress · cert-manager | PVC (JSONL/JSON state) → managed Postgres later (same append-only contracts) |
| `teleon` | teleon-app (showcase) · teleon-runtime | PVC for runtime state; receipts → object storage |
| `baltor` | baltor-app · baltor-backend · Redis (managed) · Postgres+pgvector (managed, `BALTOR_DURABLE_DB`) | managed stores |
| `openharness` | ohh-app · cie-app · vector-store build job (CronJob) | catalog read-only from image/volume; embeddings PVC |

Domains → Ingress: `aidoneright.dev` (cie), `baltor.ai`, `teleon.dev`, `openharnesshub.io`,
hub subdomains (`<hub>.openharnesshub.io` or per-hub domains when flipped live). The
trycloudflare tunnels retire; the seam-proxy model is unchanged (same-origin `/api/*`).

## 2. Model plane in the cloud

Identical env contract, three options by workload: Ollama Cloud (current primary,
`OH_LLM_BASE_URL=https://ollama.com/v1`), OpenRouter (staged; add credits), or an in-cluster
Ollama GPU node pool for data-locality (embeddings sidecar: `nomic-embed-text`). Secrets via
ExternalSecrets/sealed-secrets → each namespace gets only its keys (`OH_LLM_API_KEY`,
`OH_EMBED_*`, `OH_INFERENCE_ALLOW_NETWORK`). `scripts/check_model_plane.py` runs as a readiness
gate (initContainer/CronJob) so a mis-secret can never silently degrade to hash/stub.

## 3. Cloud functions (event-shaped work, scale-to-zero)

Per the flywheel law (24/7 = lightweight control plane only): analytics ingest (`/api/events`),
page beacons, webhook receivers (registry submissions, CDC pings), scheduled CDC refresh
(OFAC/eCFR pulls feeding Baltor source-sync), and the vector-store rebuild — all fit
functions/CronJobs. Long-running model-built runs stay on the runtime Deployments.

## 4. Initial components, rules, contracts, starting data (the seed set)

Everything already exists in-repo as the single source — the cloud seed job is a copy of what
the local services already load:

| Seed | Source of truth | Loaded by |
|---|---|---|
| Component catalog (2,5xx YAML + governance) | `catalog/**` | showcase index + governance cache |
| Hub registry catalogs (all 22) | bundle `entries:` arrays | `registry_local_service` extract |
| Identity realms (25) + TTL/onboarding rules | `architecture/identity_realm_registry.json` | identity service |
| Service/port registry | `architecture/local_service_registry.json` | every seam + health harness |
| Contracts (commands/events/artifacts) | `architecture/contract_registry.json` | proof checks + handlers |
| Provider graph + tier/edge codes | `architecture/model_provider_graph.json` (+code files) | OIPS gateway |
| Capability seeds (4 deterministic suites) | `scripts/teleon_local_runtime.py` CAPABILITIES | teleon runtime |
| Templates (14-section shell + mixins) | Shared Template Registry (src/teleon/templates) | instantiator |
| Demo corpora / fixtures (CFPB, sanctions) | `scripts/pipeline/verified_context_flow.py` + bundles | Baltor backend |
| Vector store | built from catalog by `scripts/db/build_vector_store.py` | CronJob on catalog change |

Promotion/review rules ship as code+state contracts (registry review queue: candidate ≠ active;
gate thresholds in `teleon_local_runtime` and `reason_codes.py`) — no hand-typed cloud config.

## 5. Keys & access provisioning (owner + customer)

- **Customers (self-serve):** per-realm sign-up → console `/keys` mints scoped keys (shown once,
  hash-only at rest) — live on all 25 realms today; unchanged in cloud.
- **Owner/operator:** `AIDR_REGISTRY_ADMINS` env seam seeds registry admins at deploy; admins
  grant reviewers in-app (audited). A `provision_access` CLI (queued) wraps register→onboard→
  login→mint(+grants)→share-link with a receipts ledger — runs identically against local or
  cloud bases. Service-to-service auth follows
  `docs/architecture/service-auth-and-consumption-model.md` (scoped service accounts, never
  shared user keys).

## 6. Sequence to first cloud deploy

1. Container images: one base (python:slim + repo) parameterized by the existing start_commands.
2. Apply `infra/k8s/` to a staging cluster; secrets via ExternalSecrets; PVCs for state dirs.
3. Run the gate suite in-cluster (services health, identity runtime, registry backend,
   model plane, family surfaces against the staging ingress).
4. Cut DNS per domain; keep the local plane as the dev/proof environment (it IS the spec).
