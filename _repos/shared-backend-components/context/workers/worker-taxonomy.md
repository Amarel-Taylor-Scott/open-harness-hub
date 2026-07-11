# Worker Taxonomy & Buckets

**Purpose.** Make worker classification a first-class architecture layer. Every Baltor worker belongs to a
**bucket** that determines its tool access, data access, queue lane, resource class, allowed outputs, whether
it can affect consumed truth, and what proof must pass before it is trusted. This rides the existing
durable-worker model (DurableStore/CommandEnvelope/ProcessorHarness — queue/lease/idempotency/retry/DLQ/
outbox, two-process exactly-once); it is **not** a second worker framework.

**Owner.** `_repos/baltor/backend/src/baltor/workers/worker_router.py` + `architecture/worker_bucket_registry.json` (+
`worker_registry.json`, `worker_resource_classes.json`, `worker_tool_policy.json`).

## The load-bearing safety split
> Open-ended / browser / model workers produce **evidence, candidates, traces, proposals**.
> Only the **verification + reconciliation + consumption(native_export) + human-review** gates turn that into
> **served truth.** No other worker may publish truth.

`can_publish_truth` is true for exactly `{reconciliation_policy, native_export, distillation_determinism,
human_review_signoff}` — and even those publish via a gate, never by LLM opinion. `open_ended_agent`,
`browser`, `model_inference`, `utility`, etc. have `CanonicalFact` + `ContextResponse` in
`forbidden_outputs`; the router refuses those outputs.

## The 18 buckets (queue prefix · determinism · can-publish-truth)
control_plane (`control.` · high · no) · open_ended_agent (`agent.` · non_deterministic · **no**, propose only) ·
browser (`browser.` · non_deterministic · no, evidence only) · utility (`utility.` · high · no) ·
ingestion_sync (`ingest.` · high · no) · parser_document (`parse.` · model_dependent · no) ·
decomposition_text_understanding (`decompose.` · model_dependent · no) ·
verification_fact_check (`verify.` · high · no direct) · reconciliation_policy (`reconcile.` · high · **yes/gated**) ·
model_inference (`model.` · model_dependent · no, must emit ModelTrace) ·
cpu_gpu_compute (`compute.` · model_dependent · no, gpu resource class) · vector_graph (`graph.` · high · no) ·
optimization_evaluation (`optimize.` · model_dependent · no) ·
distillation_determinism (`distill.` · high · **yes after promotion**) · memory_context (`memory.` · model_dependent · no) ·
native_export (`native.` · high · **yes/gated**) · observability_monitoring (`monitor.` · high · no) ·
human_review_signoff (`human.` · high · **via policy**).

## Inputs / Outputs
- **Input:** a `CommandEnvelope` whose `command_type` begins with a bucket's queue prefix.
- **Routing:** `route(command_type)` → the bucket with the longest matching `queue_prefix` (unknown prefix →
  `WorkerPolicyError` / ErrorEnvelope). `check_command(command_type, output_type)` additionally refuses a
  forbidden output.
- **Output:** each bucket's `allowed_outputs` (and never its `forbidden_outputs`).

## Resource classes
`tiny_cpu, standard_cpu, high_cpu, high_memory, browser_cpu, io_bound, gpu_small, gpu_medium, gpu_large,
sandboxed_agent, human_review, control_plane` — each with cpu/memory request, gpu flag, concurrency, timeout,
local/k8s replica caps, and an autoscale signal (queue depth / oldest-message age / GPU util — not raw CPU).

## Proofs
- `scripts/check_worker_bucket_registry.py` — 18 buckets complete + unique prefixes; capability-matrix
  invariants; resource classes + tool policies + classified workers consistent.
- `scripts/check_worker_router.py` — routing + unknown-prefix + forbidden-output (red-team) all fail safely.
- `scripts/check_worker_taxonomy_full_stack.py` — the table + the safety split + every classified worker
  routes to its bucket.

Commands: `PYTHONPATH=. python3 scripts/check_worker_bucket_registry.py --self-test` (and the other two).

## Limitations / Next (OPP-worker-taxonomy-surface)
Lean core = registries + router + consolidated enforcement proofs. Deferred: the 17 per-bucket task contracts
(AgentTask/BrowserTask/…), the 18 per-bucket docs, the `/api/workers/*` projection + `/workers` page, and
per-rule split proofs (the invariants are currently proven consolidated in the three proofs above).
