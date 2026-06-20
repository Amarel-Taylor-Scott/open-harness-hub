# Baltor Worker Taxonomy & Bucketization — queued spec

> Owner directive (2026-06-05). Make worker classification a FIRST-CLASS architecture layer: every worker
> belongs to a BUCKET that determines its tool access, data access, queue lane, resource class, allowed
> outputs, whether it can affect consumed truth, and what proof must pass before it's trusted. Builds on the
> proven durable-worker model (queue/lease/idempotency/retry/DLQ/outbox, two-process exactly-once). NO 2nd
> worker framework / queue system; rides the existing DurableStore/CommandEnvelope/ProcessorHarness path.

## The load-bearing safety split (the whole point)
Open-ended / browser / model workers may produce **evidence, candidates, traces, proposals**. ONLY
verification + reconciliation + consumption gates turn that into **served context**. No worker except the
approved consumption/export path may publish truth. (Aligns with [[contextops-verification-foundry]]'s
"agents propose, Baltor disposes" + [[lossless-distillation-law]] + [[baltor-wedge-wraps-providers]].)

## 18 buckets
1 control_plane · 2 open_ended_agent · 3 browser · 4 utility · 5 ingestion_sync · 6 parser_document ·
7 decomposition_text_understanding · 8 verification_fact_check · 9 reconciliation_policy ·
10 model_inference · 11 cpu_gpu_compute · 12 vector_graph · 13 optimization_evaluation ·
14 distillation_determinism · 15 memory_context · 16 native_export · 17 observability_monitoring ·
18 human_review_signoff.

## Capability matrix (machine-readable + docs)
| Bucket | Determinism | Network | LLM | Browser | GPU | Writes artifacts | Publishes truth |
|--|--|--|--|--|--|--|--|
| control_plane | high | no | no | no | no | commands/events | no |
| open_ended_agent | low | allowlist | yes | maybe | maybe | candidates only | no |
| browser | low/med | yes | maybe | yes | no | source evidence | no |
| utility | high | limited | no | no | no | utility/source artifacts | no |
| ingestion | high/med | source-specific | no | no | no | source artifacts | no |
| parser | med | no | maybe | no | maybe | parsed artifacts | no |
| decomposition | med/high | no | maybe | no | maybe | candidate artifacts | no |
| verification | high | limited | maybe | no | no | verification receipts | no direct |
| reconciliation | high | no | advisory | no | no | decisions/receipts | via gate |
| model_inference | low/med | provider | yes | no | maybe | model outputs | no |
| cpu_gpu_compute | med | no | maybe | no | yes | model outputs | no |
| vector_graph | high | no | no | no | no | vectors/edges | no |
| optimization_eval | high/med | no | maybe | no | maybe | candidates/receipts | no |
| distillation | high/med | no | maybe | no | no | rules/candidates | after promotion |
| memory | med | provider | maybe | no | no | memory artifacts | no |
| native_export | high | no | no | no | no | exports/sidecars | only gated |
| monitoring | high | limited | no | no | no | metrics/projections | no |
| human_review | high | no | no | no | no | signoff receipts | via policy |

## Registries (architecture/)
worker_bucket_registry.json (per bucket: bucket_id, description, determinism, risk_level,
allowed_command_prefixes, allowed_tools, forbidden_tools, allowed_outputs, forbidden_outputs,
resource_classes, network_policy, tenant_scope_required, sandbox_required, review_required,
can_write_artifacts, can_publish_truth, queue_prefix, autoscale_metric, retry_policy, dlq_policy,
proof_scripts, docs) · worker_registry.json (per worker: worker_id, bucket_id, command_types, in/out
contracts, queue, resource_class, determinism, idempotency_key_template, retry_policy, dlq, allowed/
forbidden_tools, network_policy, tenant_scope_required, proofs, docs, status — classify existing:
flywheel_worker, durable queue worker, tenant ingest, consumption worker, optimization/ingestion/
reconciliation workers) · worker_resource_classes.json (tiny/standard/high cpu, high_memory, browser_cpu,
io_bound, gpu_{small,medium,large}, sandboxed_agent, human_review, control_plane — each: cpu/mem request,
gpu_required, concurrency, timeout, max_replicas_local/k8s, autoscale_signal) · worker_tool_policy.json
(per bucket: allowed/forbidden ports, fs paths, network, secret access, tenant data, object store, artifact
write, model, browser, sandbox/review reqs).

## Queue prefixes (one bucket each)
control. agent. browser. utility. ingest. parse. decompose. verify. reconcile. model.cpu. model.gpu.
compute. vector. graph. optimize. eval. distill. memory. native. monitor. human.

## Router
src/baltor/workers/worker_router.py: route CommandEnvelope by command_type prefix → bucket; validate the
type is registered; validate bucket policy + allowed outputs; reject forbidden output; attach worker_bucket
to events/logs; ErrorEnvelope on policy violation.

## Bucket task contracts
AgentTask/BrowserTask/UtilityTask/IngestionTask/ParseTask/DecompositionTask/VerificationTask/
ReconciliationTask/ModelInferenceTask/ComputeTask/GraphTask/OptimizationTask/DistillationTask/MemoryTask/
NativeExportTask/MonitoringTask/HumanReviewTask (.v1).

## Proofs (the enforcement)
check_worker_bucket_registry · check_worker_registry · check_worker_resource_classes ·
check_worker_tool_policy · check_worker_router · check_worker_bucket_command_routing ·
check_open_ended_workers_cannot_publish_truth · check_browser_workers_source_evidence_only ·
check_utility_workers_deterministic · check_model_workers_emit_traces · check_gpu_workers_resource_class ·
check_worker_bucket_observability · check_worker_bucket_docs · check_worker_bucket_redteam ·
check_worker_taxonomy_full_stack. Requirements: every worker has a bucket; every command prefix maps to
exactly one bucket; unknown command type rejected; open-ended workers can't output CanonicalFact/
ContextResponse; browser workers can't output verified facts; utility workers can't call LLMGateway; model
workers must emit ModelTrace; GPU workers require gpu resource class; verification/reconciliation/consumption
gates remain authority; existing flywheel_worker + two-process exactly-once stay green.

## Red-team (fail safely)
open-ended emits ContextResponse · browser emits CanonicalFact · utility calls LLMGateway · model omits
ModelTrace · GPU command → CPU bucket · tenant-private command → global worker · unknown prefix accepted ·
direct provider bypass inside a worker.

## API/UI (deferred to opportunity)
GET /api/workers/{buckets,registry,resource-classes,tool-policy,queues} + /workers page (bucket registry ·
worker registry · queues · resource classes · tool policies · safety gates · queue stats · redteam).

## Build discipline + scope
NO 2nd worker framework/queue. Build agents isolated files + own proofs; MAIN integrates manifests + red-teams.
Determinism in proofs. No commit/push/pip/containers/network/secrets. LEAN CORE first (4 registries + router +
the key safety proofs + full-stack + redteam + a worker-taxonomy doc); DEFER the /workers API/UI + the 18
per-bucket docs to OPP-worker-taxonomy-surface. Prefer a single focused subagent over a multi-phase workflow
(the latter kept stalling on its last agent).
