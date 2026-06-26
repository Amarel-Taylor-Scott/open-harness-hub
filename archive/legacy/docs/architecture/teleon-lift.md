# Teleon Lift — import existing cloud functions + Kubernetes into PurposeTask drafts

**Status:** built + proven (`scripts/check_teleon_lift.py`, flywheel-registered). Code: `src/teleon/lift/`.
Contracts: `schemas/teleon/lift/{ImportedWorkload,RuntimeProfile,PurposeTaskDraft,CapabilityTaskDraft,
AdoptionPlan}.v1` (registered in `architecture/contract_registry.json`).

Most customers won't start with pristine PurposeTasks — they already run Lambdas, Cloud/Azure Functions, K8s
Deployments/Jobs/CronJobs, KEDA/Knative/Argo workers. **Teleon Lift** discovers those implementation-first
workloads and lifts them into purpose-first runtime objects **without taking over production.**

> Teleon Lift never says *"we imported your Lambda into Teleon."* It says: *we discovered an existing
> ImplementationCandidate, inferred a PurposeTaskDraft, preserved your current runtime as the rollback baseline,
> and you can now evaluate alternatives safely.* That language protects the architecture.

## Pipeline
```
native workload → ImportedWorkload → RuntimeProfile + Trigger/Dependency graphs → PurposeTaskDraft
(confidence + ALWAYS requires_human_review) → CapabilityTaskDraft → baseline ImplementationCandidate
(= rollback target) → AdoptionPlan (6-mode ladder, read-only first)
```
Entry point: `src.teleon.lift.lift_inventory(connectors, imported_at=…)` / `lift_workload(native, imported_at=…)`.

## Load-bearing invariants (each proven)
- **The legacy workload becomes an ImplementationCandidate** (`status: imported_baseline`) that **is the
  rollback target** — never a live/managed PurposeTask on import. *We preserve, we don't replace.*
- **Inferred purpose is a DRAFT** — `requires_human_review` is **always true**. A human confirms purpose +
  boundaries before Teleon may manage anything. `confidence ∈ [0,1]` reflects how many weak signals (name,
  tags, triggers, repo, runtime class) agree.
- **Adoption starts read-only.** The 6-mode ladder is `discover → model → observe → shadow → managed_promotion
  → full_managed`. Levels 0–2 are read-only; production is affected only at levels 4–5, and entering a managed
  mode **requires a human-confirmed purpose** (`set_mode` refuses otherwise with a `blocked` reason).
- **No secret leak.** Env-var **values are never imported** — only key names (`env_redacted_keys`).
- **Evidence is never fabricated.** `RuntimeProfile` is built only from supplied telemetry; absent telemetry →
  an explicit `unavailable` profile with null metrics.
- **CTS-1 bindable.** `runtime_class_guess` is drawn from `architecture/capability_runtime_classes.json`, so a
  lifted workload feeds straight into the CTS-1 runtime-class binding.
- **Dependency law.** `src/teleon/lift/` never imports `src.baltor` (Teleon is reusable infrastructure).

## Interpretation map (what a native kind becomes)
| Native | runtime_class_guess | interpretation |
|---|---|---|
| AWS Lambda / GCP/Azure function | `cloud-function` | capability_task_implementation |
| K8s **Job** | `kubernetes-job` | capability_task_implementation (runs to completion — cleanest candidate) |
| K8s **CronJob** | `cron-task` | scheduled_trigger |
| K8s **Deployment** | `kubernetes-worker` | long_running_worker_or_service |
| K8s StatefulSet / DaemonSet | `kubernetes-worker` | stateful_dependency / node_agent |
| KEDA ScaledObject | `queue-worker` | event_driven_runtime_binding |
| Argo/durable Workflow | `durable-workflow` | workflow_implementation_candidate |
| Service / Ingress | — | trigger_or_interface_hint |

## Connectors — offline default + labelled live seams
The pipeline runs fully offline from **canned** connectors (`CannedK8sConnector`, `CannedLambdaConnector`). The
**live** connectors are labelled seams (`LiveConnectorSeam`) that document the real provider API and raise until
creds/network exist (the `sanctions_feed_live --live` discipline):
- **AWS** — Lambda `ListFunctions`/`GetFunction` + event-source-mappings + EventBridge + IAM summary + CloudWatch refs.
- **GCP** — Cloud Asset Inventory `searchAllResources` + Cloud Functions/Run v2 list (`location=-`) + Pub/Sub + Scheduler + IAM.
- **Azure** — Resource Graph + Function Apps + App Insights + Event Grid/Service Bus + managed identity.
- **K8s** — API list/watch (resourceVersion + bookmarks; relist on 410 Gone) + kube-state-metrics.
- **IaC** — Terraform/CloudFormation/Helm/Kustomize/GitHub Actions parse. (Terraformer is **deprecated 2026-03-16** — do not build on it.)

## Lift suite (subfeatures)
Lift **Scan** (read-only inventory) · Lift **Graph** (triggers/dependencies/permissions) · Lift **Draft**
(PurposeTask/CapabilityTask drafts) · Lift **Observe** (telemetry baseline) · Lift **Shadow** (candidate
side-by-side) · Lift **Adopt** (managed promotion) · Lift **Rollback** (restore the imported baseline).

## What's built vs queued
**Built + proven offline:** normalize (K8s + Lambda) · runtime profile · trigger/dependency graphs · semantic
lifter (confidence + human-gated drafts) · the baseline/rollback model · the 6-mode adoption ladder + managed
gate · offline connectors + live seams · 5 schemas. **Queued:** the live cloud/K8s connector adapters (need
creds/network), the GCP/Azure/IaC importers, and Lift Shadow/Adopt wired to the Parallel-Path Engine + the
Teleon assurance dashboard.
