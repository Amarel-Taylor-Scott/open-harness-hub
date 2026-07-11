# Kubernetes + orchestration (Phase 2)

The production topology from `docs/architecture/cloud-architecture.md`, made concrete.
Two orchestration patterns, each for the workload it fits:

- **KEDA → the worker fleet (streaming).** The web tier enqueues partition jobs on
  Redis; **KEDA autoscales `ohh-foundry-worker` on queue depth (scale-to-zero → N)**.
  This is the high-throughput path for the bursty 10×1k fan-out (`worker.yaml`).
- **Argo Workflows → the scheduled batch DAG.** A `CronWorkflow` fans the day's
  partitions out as parallel, retried, observable steps (`argo-foundry.yaml`). Use
  Temporal instead if you need long-running durable sagas; Argo is the K8s-native fit
  for this batch DAG.
- **CronJobs → the freshness/demand/decay loops** (`cron.yaml`): daily factory,
  re-scrape (CDC), demand-mining, decay re-benchmark.

One image (the root `Dockerfile`), many roles — only the command differs, exactly as in
`render.yaml`. Set `IMAGE` to your registry build (e.g. `ghcr.io/Amarel-Taylor-Scott/openharnesshub`).

## Apply order
```bash
kubectl apply -f core.yaml        # namespace · config · secret (template) · redis broker
kubectl apply -f web.yaml         # request tier + Service + HPA
kubectl apply -f worker.yaml      # worker Deployment + KEDA ScaledObject (needs KEDA installed)
kubectl apply -f cron.yaml        # CronJobs: factory · scraper · demand-mining · decay
kubectl apply -f argo-foundry.yaml  # Argo WorkflowTemplate + CronWorkflow (needs Argo installed)
```
Prereqs: **KEDA** (`keda.sh`) and **Argo Workflows** (`argoproj.github.io`) installed in-cluster;
a managed Postgres+pgvector (Cloud SQL/AlloyDB/RDS or Neon) reachable via `DATABASE_URL`.

## Secrets
`core.yaml` ships a **template** Secret. In production use **sealed-secrets** or
**external-secrets** (e.g. backed by GCP Secret Manager / AWS Secrets Manager) — never
commit real values. Workers read `OLLAMA_API_KEY` / `DATABASE_URL` / `REDIS_URL` from it.

## BYO-cloud / air-gap (enterprise + acquisition lever)
This same set + a Helm chart (TODO) deploys into a customer's or a lab's cluster (VPC /
air-gapped), which is the enterprise tier and a portability asset for acquisition.
