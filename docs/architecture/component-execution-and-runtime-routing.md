# Component execution & runtime routing — how OHH runs components at scale

> **The two questions this doc answers.** (1) Do platforms like n8n / Zapier run
> *cloud functions for every component*? (2) Do they *containerize and run K8s that
> loads different inputs based on each component's preferences*? Short answers,
> grounded in the research below: **(1) No.** None of the surveyed platforms invoke a
> function-per-node for orchestration; FaaS appears only as a *sandbox* for untrusted
> code. **(2) Partly — and this is the part worth copying.** They run a *small fixed
> set* of generic worker pools as containers, scaled on **queue depth**, and route a
> job to the right pool by its declared requirements. They do **not** ship one
> container per logical component.
>
> This extends [[cloud-architecture.md]] (the 4-tier request/async/scheduled/data
> model; "queue non-negotiable, K8s earned") and [[backend-services-and-platform.md]]
> (the shared platform plane; "one image, per-service role"). It does not change the
> engine; it pins down *how the async tier dispatches a component*.

## 1. What the industry actually does

Four lanes of 2026 research — workflow automation (n8n), iPaaS (Zapier / Workato /
Make / Tray), durable-execution engines (Temporal / Inngest / Trigger.dev / Restate /
Step Functions), and the FaaS-vs-containers cost/isolation literature — converge on one
shape: **a durable queue feeding a generic, elastically-scaled worker fleet that
*interprets* the workflow/component definition.** The component is **data**, not a
deploy unit. FaaS shows up only at the trust boundary.

### Per-platform comparison

| Platform | Orchestration substrate | Dispatch unit | FaaS used for? | Container / K8s shape | Routing by component "preference"? |
|---|---|---|---|---|---|
| **n8n** (queue mode, v2.0 Dec-2025) | Redis/BullMQ + generic `n8n worker` Node procs | **Whole workflow** (worker runs all nodes in-proc, node→node) | **No FaaS in dispatch.** Only the *Code node* breaks out — to an on-demand, *shared, per-language* task-runner sidecar (a sandbox, not a scaling unit). | Helm chart: 3 pod roles (main / worker / webhook) from the **same image** by command; runner **sidecar** per pod. **KEDA on `bull:default:wait`** (queue length). | No per-node routing; every worker is identical. Isolates exactly **one** kind (untrusted Code). |
| **Zapier** | Celery + RabbitMQ on K8s | **Per workflow step** (a Celery task) | **Yes — sandbox only.** 100k+ Lambda fns on Firecracker microVMs run *partner/user code*, isolated per-tenant **and** per-Zap-type, behind an EKS control plane with a function inventory + canary upgrades. | K8s worker fleet; autoscale on **CPU + RabbitMQ ready-depth**. Worker pools **split by job class**: "polling / hooks / email / misc". | **Yes — by job class** onto separate pools. Component *type* is data the generic worker interprets. |
| **Workato** | Distributed queue + **stateless** worker pool | Recipe step ("any idle server" evaluates the descriptor on demand) | **No — explicitly not FaaS.** | EKS worker pools (migrated off EC2); linear autoscale (~100 req/s/workspace). On-Prem Agent = outbound TLS-WebSocket tunnel for in-network reach. | Recipe is "a descriptor decoupled from the runtime"; workers are generic. |
| **Make / Integromat** | **Undocumented** internal engine (AWS-hosted DAG-of-modules) | Module ("bundle") run | Offers a Lambda *connector*; engine-on-Lambda **not evidenced**. | Not publicly documented. | Not documented. *(The "Data-Store queue" pattern seen online is **user-land**, not Make's engine — do not cite as their architecture.)* |
| **Tray.io** | **Undocumented** (markets "serverless") | Connector operation | Exposes a Lambda *connector*; per-op-Lambda internally is **inferred, not documented**. | Third-party analysis: **hybrid** K8s + Docker + serverless frameworks. | Not documented. |
| **Temporal** | Worker **long-poll** of Task Queues | Activity / Workflow task (whole workflow re-runs via deterministic **replay**) | Serverless workers exist but **still poll a queue**; docs reserve them for **bursty/low-volume** and recommend long-lived workers for sustained throughput. | Cloud-Run/K8s worker pools; **KEDA / CREMA on "Approximate Backlog Count"** (queue depth). Helm chart, air-gap focus. | **Yes — by Task Queue.** Route activities to `GPU_ML_QUEUE` / `STANDARD_CPU_QUEUE` / `HIGH_MEMORY_QUEUE`; pools scale independently; **queue names are shared constants both sides import**. |
| **Inngest** | Hosted orchestrator + state/queue | **Per step = a fresh HTTP invocation** to *your* endpoint (step memoization) | Step code runs on *your* compute (FaaS or container). `connect` mode swaps HTTP-per-step for a **persistent WebSocket worker** with `maxWorkerConcurrency`. | Your choice of host. | Per-**function** flow control (concurrency / throttle / rate-limit / priority). FaaS-vs-pool is a **per-function knob**. |
| **Trigger.dev v4** | Hosted orchestrator | Your code in **their** managed microVMs (worker pool) | Neither pure FaaS nor self-poll: **CRIU checkpoint-resume** + warm-machine reuse (100–300 ms warm). | Supervisor runs **Docker containers**; horizontal scale = add worker containers; Helm chart, self-host/air-gap. | Platform owns the compute; routes by resource. |
| **AWS Step Functions** | Hosted state machine | **Per state transition** (billed); Task Lambdas billed **separately** | Tasks are typically Lambda (per state). | n/a (managed). | Per-state Task resources. Standard = exactly-once / long-running ($25/M transitions); Express = at-least-once / ≤5 min / high-volume. |

**Reading the table.** The *whole-execution / per-step-task* engines (n8n, Zapier,
Workato, Temporal) all run **generic workers behind a queue** and route by **job
class / task queue**, never by giving a component its own deployable. The
*FaaS-per-step* engines (Inngest serve, Step Functions) put one short invocation per
step behind a **central** orchestrator — and even there the FaaS-vs-pool choice is
collapsing into a **per-function knob** (Inngest `connect`, Temporal serverless
workers). The **only** place anyone runs an isolated runtime per component is the
**untrusted-code sandbox** (n8n task-runner; Zapier's 100k Firecracker microVMs).

### The cost / isolation evidence against the two extremes

- **FaaS-per-component loses at OHH's shape.** The foundry's bursty 10×1k partition
  fan-out is exactly the >~50k-invocations/day regime where FaaS flips to **~3×–79×**
  more expensive than containers (one cited migration: $9,400→$2,500/mo on Fargate, a
  73% cut; 50k images $380 on Lambda vs $4.80 on containers). It is fatal for the
  streaming / long-running / GPU steps — hosted-model streaming, embeddings, and
  local-model inference hit the **15-min cap** and **30–60 s GPU cold starts**
  (multi-GB weights + CUDA warmup; first token >40 s cold vs ~30 ms warm). And a DAG
  re-pays cold start on **every hop** — the "nanoservice" anti-pattern the field is
  retreating from in 2026. (AWS's Dec-2025 "Lambda Managed Instances" — EC2 pricing +
  15% fee — is itself a tell that vanilla FaaS economics break at steady volume.)
- **Container-per-component doesn't scale as a model.** Thousands of OHH components
  would mean thousands of images, deploy units, and scaling configs to babysit, plus
  idle cost per always-on container (~$72/mo for a 24/7 container vs ~$0.90 for the
  same trivial-volume work on FaaS). **Containerize the *runtime*, not the component.**

## 2. The OHH decision

**Generic stateless workers + job-class QUEUES + KEDA-autoscaled POOLS, with a thin
ROUTER that reads each component manifest's execution signals to pick the queue/pool.
Components stay data/jobs. Not cloud-functions-per-component. Not
container-per-component.**

This is **not a rewrite** — it is the natural next step from where the repo already is.
[[cloud-architecture.md]] and [[backend-services-and-platform.md]] already mandate a
swappable `Queue` protocol (`scripts/foundry/queues.py`, default `RedisQueue`), a
stateless worker (`scripts/foundry/worker.py`, pull/run_partition/ack + retry +
explicit failed-permanently state), one container image per service-role, and KEDA-on-queue-depth at Phase 2.
The **gap** is that there is exactly **one** queue today
(`DEFAULT_QUEUE_KEY = "ohh:foundry:jobs"`) and the per-component execution signals are
*carried but not yet used as a routing key*. This doc closes that gap.

### 2.1 The pools (a small *fixed* set — runtime, not component, granularity)

| Pool / queue class | Runs | Scaling posture | Why a distinct pool |
|---|---|---|---|
| **cpu** | The deterministic / idempotent / CPU-light bulk: gates, parsers, chunkers, format-converts, redaction, deterministic rubrics | KEDA on its queue depth, **scale-to-zero**, high concurrency | The cheap default; a cold start here is invisible. |
| **gpu** | Model / embedding / local-inference tier (the `model_route` proxy, `embed.*`, local models) | Serverless-container GPU pool (Cloud Run / Azure Container Apps GPU) **or** a GPU worker Deployment; **warm min-replicas > 0** | GPU init (multi-GB weights, CUDA) must not be paid per step; streaming can't tolerate scale-to-zero cold start. |
| **burst** (interactive) | `streaming=true` and very-low-`latency_budget_ms` steps | **Warm, min-replicas > 0, no scale-to-zero** | Scale-to-zero's own cold start is the enemy of a latency budget / a live stream. |
| **sandboxed-untrusted** | `trust_boundary ∈ {external, mixed}` or any user-supplied / build-on-demand code | Constrained, rate-limited; **gVisor / Firecracker / WASM** isolation | Never run untrusted code in the generic worker. This is the n8n / Zapier pattern. |
| **external-metered** *(may overlay cpu)* | `side_effects=external_call` / cost-gated model calls | Rate-limited; enforces `FoundryConfig.model_call_budget` + `access.py` billable events | Caps runaway provider cost; concurrency-limits against provider rate limits; keeps usage = revenue. |

These are **worker classes**, not component classes: one CPU-worker image, one GPU /
serverless-GPU host, one sandbox-runner image — matching the repo's "one image, per
service role" rule. Each pool consumes **its own** queue and KEDA-autoscales on **its
own** queue depth (KEDA's Redis-list `LLEN` / SQS scalers; scale-to-zero where the pool
allows). Multi-queue, per-pool `minReplicaCount` is a documented KEDA pattern.

### 2.2 The router (reads the manifest, picks the queue)

A **pure function** `(process_kind, latency_budget_ms, streaming, side_effects,
trust_boundary, deterministic, idempotent) → pool` that the **producer** (enqueue side)
and the **KEDA pool config** both reference. The pool/queue-class names live in **one**
shared constant module and are imported everywhere — the same discipline Temporal
documents (queue names as shared constants both sides import), and exactly the repo's
**No-Magic-Values** rule (`docs/codex/no-magic-values.md`) applied to infra. No new
queue key should be hand-typed twice.

### 2.3 Why not the two extremes (restated for the record)

- **Not cloud-functions-per-component:** cold start re-paid per DAG hop; ~3×–79× cost
  at the foundry's >50k/day bursty fan-out; 15-min cap + 30–60 s GPU cold start kill
  streaming / local-model / embedding steps; the nanoservice anti-pattern. No surveyed
  platform does this for orchestration.
- **Not container-per-component:** thousands of deploy units / images / scaling configs;
  idle cost per always-on container; the per-unit comms + maintenance overhead *dwarfs
  the work*. Containerize the runtime.

## 3. Where FaaS and sandboxes *do* fit

**FaaS — opt-in adapter, behind the same enqueue boundary, for the narrow slice where
its model genuinely wins:** short, stateless, cheap-init, idempotent, *intermittent*
work. Concretely for OHH: CDC / freshness / decay alert fan-out and signed-publisher
push notifications (`deliver.webhook`); enqueue-only cron triggers (Cloud
Scheduler / Render cron → queue) that just *queue* a partition rather than doing the
work; cheap deterministic gates with `side_effects=none` and a tiny latency budget; and
**Cloudflare Workers AI** (already an env-only adapter in [[cloud-architecture.md]]) as
the FaaS-style home for embeddings + small / router models. **Never** put the foundry
fan-out, streaming model proxy, or GPU inference on FaaS. The convergence noted above
means OHH's swappable `Queue` protocol already gives this as a *knob* — a job-class can
map to a worker pool **or** a FaaS consumer **or** a scale-to-zero job without locking
to a vendor (the portability / air-gap moat).

**Sandbox — keyed off `trust_boundary`, the one place per-component isolation is
right:** `local` / `hub` → standard container (optionally gVisor); `external` / `mixed`
or any untrusted / build-on-demand customer code → a stronger boundary — **Firecracker**
microVM (~125 ms boot, <5 MiB overhead, ~150 VMs/s/host, own kernel under KVM),
**gVisor** (user-space syscall interception; 10–30% I/O overhead), or **WASM**
(lightest; JS/TS-only). The manifest already anticipates this: `implementations.kind`
includes `docker` and `wasm`. If OHH ever ships per-component sandboxes at scale, copy
Zapier's **control plane**: an inventory keyed by component identity/version (OHH
already has content + version hashes — `docs/codex/no-magic-values.md`, ID/hash
discipline in `CLAUDE.md`) with a canary / rollback path for runtime upgrades. For
`trust_boundary=local` *connectivity* (reaching inside a private network without inbound
exposure), copy Workato's **outbound TLS-WebSocket tunnel agent**.

## 4. Mapping `processor.schema.json` → routing decision

The schema (`schemas/processor.schema.json`, plus the `envelope` in
`schemas/_common.schema.json`) already carries every signal the router needs. Each field
maps to a concrete dispatch decision:

| Field (manifest) | Routing / policy decision |
|---|---|
| `process_kind` (open vocab, SPEC §16) | Coarse pre-classification: `embed.*` / `call.judge` / `model_targets` set → **gpu**; `gate.*` / `parse.*` / `chunk.*` / `coerce.*` / `redact.*` → **cpu**; `deliver.webhook` / `escalate.*` / `audit.*` → FaaS-eligible glue. |
| `streaming` | `true` → **burst** (warm, no scale-to-zero); informs replay/checkpoint suitability. |
| `latency_budget_ms` | Small budget → **burst** / warm pool; large/absent → scale-to-zero-eligible pool. |
| `side_effects` (`none`/`read`/`write`/`external_call`) | `external_call` → **external-metered** (budget + rate-limit + `access.py` metering); `none`/`read` + CPU-light → pack densely on **cpu** / FaaS-eligible; `write` → at-least-once + dedup care. |
| `trust_boundary` (`local`/`hub`/`external`/`mixed`) | `external`/`mixed` → **sandboxed-untrusted** isolation tier; `local`/`hub` → standard container. **The one signal that picks per-component isolation.** |
| `deterministic` | `true` → safe for replay/memoization (the worker contract assumes converge-on-replay; OHH already has this via content-hashing + the resumable funnel ledger). |
| `idempotent` | `true` → safe **at-least-once** on cheap FaaS / aggressive retry; `false` → exactly-once-leaning worker queue + once-only handling (the Step Functions Standard-vs-Express distinction). |
| `on_error` / `retry` (`max_attempts`, `backoff`) | The queue's retry and explicit terminal/hold policy per job: `approval_required`, `budget_blocked`, or `failed_permanently`. |
| `model_targets` (when the processor wraps an LLM call) | Forces **gpu** / **external-metered** and binds the per-job `model_call_budget`. |
| `implementations.kind` (`callable`/`shell`/`http`/`openapi`/`mcp`/`docker`/`wasm`) | Selects the executor *within* a pool: `wasm`/`docker` are the natural sandbox runtimes for **sandboxed-untrusted**; `http`/`openapi`/`mcp` are external calls (→ **external-metered**). |

**One identified schema gap (worth a follow-up, out of scope here):** the envelope has
`trust_boundary` but **no explicit `resource_class` / `requires_gpu`** field, so the
router must today *infer* gpu/interactive from `process_kind` + `model_targets` +
`streaming` + `latency_budget_ms`. Inference is workable now; a small canonical
`resource_class` enum (`cpu_light | cpu_heavy | gpu | interactive_stream |
sandboxed_untrusted | external_metered`) defined **once** would make routing explicit
rather than inferred. Flagged, not built — this doc touches nothing else.

## 5. Sequencing

Honors [[cloud-architecture.md]]'s "K8s is earned" stance — **don't over-engineer**:

1. **Now (Phase 1, low-ops):** single `RedisQueue` + the built-in worker loop is fine
   while volume is low. *Add the router as a pure function and a small queue-class
   constant set first* — it's cheap, vendor-neutral, and unblocks per-pool scaling later.
2. **When pulled by scale or BYO-cloud (Phase 2):** split into the fixed pool set,
   one stateless container Deployment per pool, each with its **own** KEDA `ScaledObject`
   on its **own** queue depth (scale-to-zero where allowed). This is precisely the n8n
   Helm + Temporal + Trigger.dev v4 production shape — and it ships as a Helm chart into
   a lab's own cloud (the enterprise / air-gap / acquisition lever already named in the
   cloud-architecture doc).

The decision is deliberately *the same shape the industry validated*, no heavier.

---

## Warrant

- **Corroboration (platforms + sources).** The recommendation is the documented
  production design of every surveyed platform whose internals are public: **n8n** queue
  mode (generic `n8n worker` per whole-execution; KEDA on `bull:default:wait`;
  isolate-only-the-Code-node) — `docs.n8n.io/hosting/scaling/queue-mode/`,
  `docs.n8n.io/hosting/configuration/task-runners/`,
  `github.com/n8n-io/n8n-hosting/blob/main/charts/n8n/README.md`,
  `infralovers.com/blog/2025-12-12-n8n-2-0-hardening-release/`; **Zapier** (Celery +
  RabbitMQ on K8s, pools split polling/hooks/email/misc, Lambda only for untrusted code)
  — `zapier.com/engineering/automating-billions-of-tasks/`,
  `aws.amazon.com/blogs/architecture/how-zapier-runs-isolated-tasks-on-aws-lambda-and-upgrades-functions-at-scale/`,
  `newsletter.systemdesign.one/p/zapier-architecture`; **Workato** (stateless worker
  pool, explicitly not FaaS) — `workato.com/the-connector/serverless-mcp-for-enterprise-ai-tools/`,
  `docs.workato.com/on-prem/agents.html`; **Temporal** (poll a Task Queue, route by
  queue, KEDA on backlog count) — `docs.temporal.io/task-queue`,
  `temporal.io/blog/route-specialized-workloads`,
  `temporal.io/blog/deploying-temporal-workers-to-google-cloud-run`,
  `docs.temporal.io/evaluate/serverless-workers`; **Inngest** (per-step HTTP **and**
  persistent-worker `connect`) — `inngest.com/docs/learn/how-functions-are-executed`,
  `inngest.com/docs/setup/connect`; **Trigger.dev v4** (managed worker containers,
  CRIU) — `trigger.dev/docs/how-it-works`, `trigger.dev/launchweek/2/trigger-v4-ga`;
  **Step Functions** per-transition cost — `aws.amazon.com/step-functions/pricing/`. The
  cost/isolation evidence against the extremes: `byteiota.com/lambda-vs-containers-when-pay-per-use-costs-3x-more/`,
  `regolo.ai/scale-to-zero-cold-start-latency-why-serverless-gpu-breaks-real-time-ai-and-how-to-fix-it/`,
  `keda.sh/`, `learn.microsoft.com/en-us/azure/container-apps/gpu-serverless-overview`,
  `knative.dev/docs/`, `dev.to/mohameddiallo/4-ways-to-sandbox-untrusted-code-in-2026-1ffb`,
  `arxiv.org/html/2509.23013` ("Characterizing FaaS Workflows on Public Clouds"). Make's
  and Tray's internal engines are **not** publicly documented and are flagged inferred,
  not cited as precedent.
- **Principle (earned complexity / no over-engineering).** [[cloud-architecture.md]]
  establishes "a queue + worker tier is non-negotiable; K8s is *earned*, not day one,"
  and [[backend-services-and-platform.md]] establishes "one image, per-service role" with
  "heavy frameworks earned, not default." Generic workers + job-class queues is the
  minimal design that the entire industry independently converged on; per-component FaaS
  and per-component containers are *more* machinery for *worse* economics at OHH's
  bursty, GPU-bearing, high-volume shape — the over-engineering both docs warn against.
  The repo already carries the routing inputs (`schemas/processor.schema.json`) and the
  swappable queue/worker spine (`scripts/foundry/queues.py`, `worker.py`); this is the
  smallest step that uses what exists.
