# Runtime planes — where Baltor's pieces run

Baltor separates into planes so the same object model deploys from a laptop to a regulated enclave
without rewrites. **Kubernetes is NOT required for the local MVP**; **durable workflows ≠ K8s Jobs**
(K8s schedules pods; a durable engine owns business state/replay); **agents do not own execution
state** (they act inside a DecisionContext and emit a DecisionReceipt — the durable engine executes).

| Plane | Holds | Local MVP | Enterprise |
|---|---|---|---|
| **Local Developer** | local MCP, local memory, repo context, local LLM | laptop / Docker Compose / Ollama | dev namespace |
| **Control** | tenant/connector/policy/schema/backend-tool registries, pack templates, workflow + eval defs, admin UI | config files + a small API | managed service + DB |
| **Data / Object** | source handles, context objects, claims, relationships, versions, artifacts, packs, receipts, policy decisions, queue messages, rot signals | Postgres + MinIO + Qdrant | RDS/Aurora + S3 + managed vector |
| **Worker** | source watchers, document decomposition (per-page fan-out), parsers, reconcilers, fragility hunters, enhancers, verifiers, rot sweepers, pack builders, eval runners | Compose workers | KEDA-scaled Jobs / Argo; durable engine (DBOS/Temporal) owns state |
| **Delivery** | MCP tools, REST/GraphQL, source-handle expansion, pack serving, CLI, CI hooks, web UI | local API/MCP | gateway + MCP portal |
| **Observability / Eval** | OTel GenAI traces/metrics, evals, pack quality, agent success | Langfuse (optional) | Langfuse/Phoenix + OTel collector |
| **Policy / Security** | OpenFGA (relations), OPA/Cedar (decisions), classification, retention, prompt-injection + MCP/skill scans | OPA + OpenFGA containers | + DLP, audit export, KMS |

## Progression (no premature Kubernetes)
- **Local demo:** Docker Compose (no cloud, no K8s) — proves the contracts.
- **Team beta:** managed containers (ECS/Fargate, Cloud Run) + managed Postgres + object store — **before** K8s.
- **Enterprise:** Kubernetes for the worker plane (KEDA/Argo for per-page document fan-out); durable engine (DBOS→Temporal) for long-running flows.
- **Regulated enclave:** customer VPC / on-prem; sandboxed execution (E2B → microsandbox / gVisor) for untrusted docs; self-hosted observability; strict retention/classification.

## Flywheel → plane mapping
Document-decomposition flywheel → Worker plane (Jobs, per-page fan-out). Context-rot flywheel →
Worker CronJob + on-demand. Verification rail + Gold-Pack Contract → Delivery + Policy planes.
Human-review flywheel → Control plane review queue (durable engine holds state until a decision).
Schemas: `schemas/pipeline/pipeline-object.schema.json`, `schemas/queue/{queue-message,worker-run}.schema.json`.
