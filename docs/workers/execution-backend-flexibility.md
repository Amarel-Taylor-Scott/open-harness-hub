# Execution Backend Flexibility

**Framing (use this wording):** Some simple workers *could* run as cloud functions, and we may want
Kubernetes workers and cloud-function workers operating **side by side**. Baltor should be able to switch
between them through **policy** as pricing, latency, reliability, cold-start behavior, and customer
requirements change. Avoid "these *should* be cloud functions"; prefer "these are *function-eligible by
default* / *Kubernetes-eligible by default* — a provider-policy decision, overridable with proof."

## EXECUTION BACKEND FLEXIBILITY CLAUSE

Some worker tasks may be eligible for cloud-function execution, while others may be better suited to
Kubernetes workers, Kubernetes Jobs, Cloud Run Jobs, local subprocesses, GPU pools, browser pools, or
sandboxed agent workers. Baltor treats these as **interchangeable execution backends behind
`ExecutionProviderPort`**. Do not hardwire a capability to Kubernetes or to cloud functions. The caller
submits a `CapabilityTask`; the policy + selector choose an execution provider based on task size,
cold-start tolerance, SLA, cost estimate, timeout limits, dependency needs, resource profile, tenant
policy, and current provider health. Kubernetes and cloud functions may run **side by side**; a task class
can be routed to cloud functions today, Kubernetes tomorrow, and local subprocesses in development without
changing the task contract. Because pricing and provider behavior change, backend choice must be
**policy-driven, telemetry-driven, and reversible**.

## The model

```
CapabilityTask.v1  →  WorkerRouter / bucket  →  ExecutionBackendPolicy + pricebook + health
                   →  execution_backend_selector  →  ExecutionProviderPort
       local_subprocess@v1 · local_function_emulator@v1 · k8s_deployment_worker@candidate ·
       k8s_job@candidate · {aws_lambda,gcp_cloud_run_function,azure_function}@candidate ·
       cloud_run_job@candidate · browser_pool@candidate · gpu_pool@candidate · sandbox_worker@candidate
```

The **DB FleetLedger remains the source of truth.** An execution backend only *runs* a task (atomic claim,
write artifacts/events, idempotency, retry/DLQ) — it never owns truth and never emits a
`CanonicalFact`/`ContextResponse` unless it is an explicit gate-approved consumption/export provider.

## Why this exists

Cost changes; workload shape changes; cold starts matter; idle cost matters; dependencies matter (browser/
GPU/agents are heavy for functions; utility/webhook handlers fit functions); customer requirements vary
(isolation, residency, no-external-functions); and switching should be a config change, not a rewrite.

## How selection works (`src/baltor/workers/execution_backend_selector.py`)

Pure + deterministic. Inputs: the task, the per-bucket policy (`architecture/execution_backend_policy_matrix.json`),
the **pricebook** (`architecture/execution_backend_pricebook.json` — *configuration*, never hardcoded),
provider health, and available credentials. Output: an `ExecutionProviderDecision`.

- A `policy_override.preferred_backends` order forces a deliberate switch (local ↔ k8s ↔ cloud function).
- Otherwise the cheapest eligible+available+healthy backend wins (**pricing/telemetry-driven** — change the
  pricebook, the choice flips, no code change).
- **Hard guards:** browser / GPU / open-ended / control-plane buckets exclude generic cloud functions by
  default; an override may allow them only `allow_generic_functions=true` (i.e. with proof).
- Missing credentials or unhealthy providers fall back to the **local function emulator / subprocess** —
  the offline correctness invariant — never a crash.

## Local function emulator = offline correctness invariant

`src/baltor/workers/function_emulator.py` is contract-identical to a cloud function: it atomically claims
durable tasks, runs a handler, writes the result, ack/nacks — idempotent, two-process-safe, no truth. It
proves the whole abstraction with zero cloud credentials. Real cloud-function adapters
(`execution_providers/*_candidate.py`) are **candidate** and return `ProviderUnavailableResult` when
unconfigured; no cloud SDK is imported outside an adapter.

## Proven now

`check_execution_backend_selector` (switch local↔k8s↔function by policy + by pricebook; browser/GPU
guarded; missing-creds/unhealthy fall back) · `check_local_function_emulator` (durable drain, idempotent,
two-process, no truth) · `check_execution_backend_policy_matrix` (matrix + pricebook well-formed; functions
side-by-side eligible; heavy buckets excluded) · `check_execution_backend_redteam` (no hardcoded prices,
SDK-free adapter load, no-truth, stable decision schema) · **`check_live_fleet_execution_backend_wiring`**
(the selector is on the LIVE fleet-supervisor dispatch path: `supervisor_watch.step(execution_backend=True)`
selects a backend per owned shard, records an idempotent `ExecutionProviderDecision`, and drains real durable
work via the chosen LOCAL executor — local-first default, cloud-deferred-never-blocking, one drainer per
queue, no truth).

## Wired live

`src/baltor/workers/execution_dispatch.py` (`dispatch_capability` / `dispatch_owned_shards`, with a
shard→bucket map so the live path exercises the real per-bucket policy) is called from
`supervisor_watch.step(execution_backend=True)`. The real loop turns it on with
`baltor_flywheel.py --watch --execution-backend`: each owned shard's queued work is routed through the
selector, the chosen backend is recorded as a switchable decision, and the work drains on the local executor
that matches that backend (function emulator / job emulator / worker pool). An unconfigured cloud backend
falls back to local in the selector, so the live path **never blocks on missing cloud credentials** — cloud
can wait, capability cannot. In this mode the raw `--dispatch` spawn-and-drain path is disabled so a queue
has exactly one drainer.

## Deferred (`OPP-execution-backend-surface`)

Real AWS Lambda / Azure Function / Cloud Run Job / k8s-Job adapters (need creds + owner approval) ·
side-by-side shadow / weighted-canary / parallel-compare execution · `/api/fleet/execution` + a UI panel ·
telemetry-fed pricebook refresh. Real adapters stay candidate until credentials + proofs exist; the emulator
stays the correctness invariant. (The fleet-supervisor wiring of the selector is now DONE — see "Wired live".)
