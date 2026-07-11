# CPU-batch inference lane (foundry lane 2) — 2026-06-11

This is the implementation of **lane 2** from
[`flexible-inference-lanes.md`](flexible-inference-lanes.md): an **optional, flexible,
fully degrade-safe** capability that lets a foundry worker run its model calls against a
*local* OpenAI-compatible server (a quantized Gemma on CPU) for the duration of a batch, then
shut it down so the machine scales to zero. It is for long-running **non-realtime** work —
overnight enrichment, CDC re-verification, candidate generation — where tokens/sec doesn't
matter but **$/token and data-locality do**.

Code: [`_repos/shared-backend-components/scripts/foundry/batch_inference.py`](../../scripts/foundry/batch_inference.py) (the lane
manager) + the wiring in [`_repos/shared-backend-components/scripts/foundry/worker.py`](../../scripts/foundry/worker.py)
(`Worker._run_partition`). Pure stdlib + subprocess.

## What it is NOT

It is not a new model plane and not a second receipt sink. It is a **base_url switch**: the lane
stands up a server that speaks the OpenAI `/v1/chat/completions` shape — the exact shape
[`_repos/shared-backend-components/scripts/foundry/model_route.py`](../../scripts/foundry/model_route.py)'s `from_env()` and
`_repos/shared-backend-components/scripts/model_routes.py`'s `ChatRoute` already use — and points the existing route at
`127.0.0.1`. No caller changes; provenance still flows through the established route. Switching
lanes is configuration, never code (the architectural law of lane 2).

## The four laws this lane obeys

| Law | How it shows up here |
|---|---|
| **Optional / no-op** | When `OH_BATCH_LLM` is unset the lane is INACTIVE: no server starts, no env changes, and the worker's ledger line carries **no** `served_by_lane` key — byte-identical to the cloud-only path (verified by diffing `worker --self-test` / `--demo` output with the var unset). |
| **Honest degradation** | If `OH_BATCH_LLM=local` but no supported backend binary is runnable, the lane logs the reason to stderr and reports `available=False`; the worker falls back to the cloud route and records `served_by_lane:"cloud"`. It **never** fabricates a model answer and **never** crashes a worker. |
| **No magic values** | Every endpoint, binary, model, port, and timeout is a named constant with a rationale comment, overridable by env. No hardcoded paths or model tags in logic. |
| **Lossless / honest provenance** | The lane never rewrites outputs. The worker records which lane served each batch (`cloud` \| `local-batch`) so the funnel ledger can never lie about where a measurement came from. |

## Lifecycle: start → health → drain → stop

`batch_inference.batch_server()` is a context manager. Per batch (one partition job):

1. **Inactive guard.** If `OH_BATCH_LLM != local`, immediately yield an *unavailable* lane and
   return — nothing is started, no env touched. (The worker only even enters the real
   `batch_server()` when the job is *batch-eligible*; otherwise it uses the zero-side-effect
   `inactive_lane()`.)
2. **Backend detect.** `detect_backend()` resolves a runnable backend honoring
   `OH_BATCH_LLM_BACKEND` (`auto`|`llamacpp`|`ollama`). On `auto` it prefers **llama.cpp**
   (lower per-batch overhead) then **ollama**. llama.cpp is only considered runnable when BOTH
   the `llama-server` binary AND a GGUF model file (`OH_BATCH_LLM_LLAMACPP_MODEL_PATH`) exist —
   a server with no model can't answer, so we DEGRADE rather than start a broken endpoint. If
   neither backend resolves → log the reason, yield unavailable (→ cloud).
3. **Start.** Spawn the server subprocess on a loopback `host:port` (`OH_BATCH_LLM_HOST` /
   `OH_BATCH_LLM_PORT`). ollama takes its bind address from `OLLAMA_HOST`; llama.cpp takes
   `--host/--port/-m` flags. A spawn failure (`OSError`) degrades cleanly.
4. **Health.** Poll `GET {base}/v1/models` every `HEALTH_POLL_INTERVAL_S` until HTTP 200, bounded
   by `OH_BATCH_LLM_HEALTH_TIMEOUT_S` (default 120 s — a cold CPU load of a Q4 Gemma can take
   ~1 min). If the process dies during boot, or the deadline passes, stop it and yield
   unavailable (→ cloud).
5. **Yield.** On success, yield an *active* lane carrying the loopback `base_url` (`…/v1`), the
   model, the backend, and `lane_tag = "local-batch"`.
6. **Route.** `route_env_override(lane)` (also a context manager) sets
   `OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OH_CHAT_MODEL` so `model_route.from_env()`
   transparently builds a route to the local server, and **clears** the higher-priority
   `OLLAMA_API_KEY` / `ANTHROPIC_API_KEY` so a configured cloud provider can't shadow the on-box
   server. It restores the prior environment exactly on exit (lossless — no env leaks across
   jobs). For an unavailable lane this is a no-op that yields `False`.
7. **Drain + stop.** When the `with` block exits (the batch is drained), `_shutdown()` always
   runs: `terminate()` → `wait(SHUTDOWN_GRACE_S)` → `kill()`. Never raises. The machine can now
   scale to zero; `$0 idle`.

## Environment contract

| Var | Default | Meaning |
|---|---|---|
| `OH_BATCH_LLM` | *(unset)* | `local` turns the lane ON. Anything else / unset = INACTIVE (cloud unchanged). |
| `OH_BATCH_LLM_MODEL` | `gemma4` | Model tag to serve (smallest Gemma-4-class that runs Q4 on CPU). |
| `OH_BATCH_LLM_BACKEND` | `auto` | `auto` (llama.cpp→ollama) \| `llamacpp` \| `ollama`. |
| `OH_BATCH_LLM_HOST` | `127.0.0.1` | Loopback bind host (on-box only — never public). |
| `OH_BATCH_LLM_PORT` | `11533` | Bind port (high port; avoids ollama 11434 / vLLM 8000 clashes). |
| `OH_BATCH_LLM_LLAMACPP_BIN` | `llama-server` | llama.cpp server binary name (resolved on PATH). |
| `OH_BATCH_LLM_OLLAMA_BIN` | `ollama` | ollama binary name (resolved on PATH). |
| `OH_BATCH_LLM_LLAMACPP_MODEL_PATH` | *(unset)* | GGUF file for llama.cpp. Unset/missing ⇒ llama.cpp lane stays unavailable (no guessing). |
| `OH_BATCH_LLM_HEALTH_TIMEOUT_S` | `120` | Max seconds to wait for the server to become healthy. |

The lane reuses the route's own env vars (`OPENAI_BASE_URL` / `OPENAI_API_KEY` / `OH_CHAT_MODEL`)
to point `from_env()` at the local server — single source, so the worker wiring and the manager
can't drift on which vars carry the override.

### Latency-class gating

A job payload may carry `latency_class: "interactive" | "batch"`. An **interactive** job MUST NOT
use the batch lane even while it is active (CPU tokens/sec is too slow for a latency-bound
caller) — `job_wants_batch()` returns `False`, the worker keeps the cloud route, and the ledger
records `served_by_lane:"cloud"`. `batch` / untagged jobs are batch-eligible.

### Provenance stamp semantics

- **Lane unset** → no `served_by_lane` key (byte-identical path).
- **Lane active, batch job served locally** → `served_by_lane:"local-batch"`.
- **Lane active, but interactive or degraded to cloud** → `served_by_lane:"cloud"` (honest: it
  records that this job deliberately/necessarily bypassed the batch lane).

## Test methodology: a FAKE local server

Neither `llama-server` nor a real model is guaranteed in CI/dev, so the self-tests must NOT
depend on one. `batch_inference._fake_server_script()` emits a ~15-line stdlib `http.server` that
speaks just enough OpenAI-compat to exercise the whole lifecycle:

- `GET /v1/models` → `200` (health),
- `POST /v1/chat/completions` → a fixed completion carrying a **sentinel** string.

`batch_server(_spawn=…)` accepts an injectable spawn function, so the self-test launches the fake
server in place of a real backend and proves, end-to-end:

1. **no-op** — lane unset ⇒ unavailable, nothing started, route override is a no-op;
2. **degradation** — lane on but the configured binary missing ⇒ unavailable + reason, no crash;
3. **lifecycle** — start → health 200 → route a **real** call through `model_route.from_env()`
   pointed at the local server → the sentinel comes back (proving the call was served *locally*,
   not by cloud) → context exit → the port is no longer healthy (clean shutdown);
4. **latency gating** — interactive job never eligible; batch/untagged jobs eligible.

The `worker --self-test` adds the integration proof: a fake-server-backed lane records
`served_by_lane:"local-batch"` for a batch job, `"cloud"` for an interactive one, and **no key**
when the lane is unset.

Run:

```bash
python3 -m scripts.foundry.batch_inference --self-test   # offline lifecycle proof (fake server)
python3 -m scripts.foundry.batch_inference --status      # resolved lane decision for the current env
python3 -m scripts.foundry.worker --self-test            # includes the batch-lane integration checks
```

## Cost math: CPU-batch Gemma-4 on Fly shared-cpu vs cloud

Anchors (from `flexible-inference-lanes.md`): OpenRouter `gemma-4-26b` = **$0.06 / $0.33 per 1M**
input/output tokens; a Fly **shared-cpu-4x / 8 GB** machine ≈ **$0.03/hr-class**, **$0 idle**
(scale-to-zero). Assume a representative foundry call ≈ **1,500 in + 500 out tokens** (grounded
prompt + a short measured answer), and a CPU Q4 Gemma-4 sustaining **~6 calls/min** (~150 tok/s
aggregate) per shared-cpu-4x worker.

| Calls/day | Cloud (OpenRouter) $/day | Cloud $/mo | CPU-batch machine-hours/day | CPU-batch $/day | CPU-batch $/mo |
|---:|---:|---:|---:|---:|---:|
| 1,000 | (1k×1.5/1M×$0.06)+(1k×0.5/1M×$0.33) = **$0.255** | ~$7.7 | 1,000 ÷ 360/hr ≈ **2.8 h** | 2.8×$0.03 ≈ **$0.083** | ~$2.5 |
| 10,000 | **$2.55** | ~$77 | ≈ **27.8 h** (≈1.2 machines) | ≈ **$0.83** | ~$25 |
| 100,000 | **$25.50** | ~$765 | ≈ **278 h** (≈12 machine-hours-worth, parallel) | ≈ **$8.33** | ~$250 |

Reading: CPU-batch is roughly **3× cheaper per token** than even the cheapest cloud Gemma route,
and the gap widens with volume because cloud is purely marginal while CPU-batch is bounded by
machine-hours you already pay $0 for when idle. Below ~1k calls/day the absolute savings
(<$0.20/day) rarely justify operating a server — **cloud (lane 1) is the right default**; the
batch lane earns its keep in the 10k–100k+/day regime and where **data-locality** (no prompt
leaves the box) is itself the requirement. (Real tok/s and call shape vary; treat these as
order-of-magnitude. The honest version of this table comes from the **receipts** — once
per-node $/1M actuals accumulate, promotion/demotion of a lane becomes an evidence decision, not
this estimate.)

## "Is this the best way?" — critique

**The design: in-worker sidecar (chosen).** The server lives and dies with the batch, on the
worker's own machine, behind the existing route. Pros: zero data egress (prompts never leave the
box — the strongest argument for lane 2); `$0 idle` because it rides the worker's scale-to-zero;
no new service/identity/IaC; switching to it is a base_url env flip. Cons: cold-load latency is
paid **per batch** (mitigated by batching — amortized over thousands of calls it's noise); one
model loaded per worker (fine for a homogeneous batch, wasteful if a batch needs many models);
the worker image must carry the backend + weights (bigger image / a pull step).

**Alternative A — a separate scheduled Fly app (a standing/cron batch-inference service).**
A dedicated app the workers call over the private network. Pros: model loaded once and reused
across many workers (better amortization at high concurrency); image/weights decoupled from the
worker; could batch requests across jobs. Cons: it's a **second service** (identity, IaC, a
versioned API, health/restart ownership) for what is otherwise a routing flip; it reintroduces a
network hop and a standing cost unless *it* also scales to zero (and then you've rebuilt the
cold-start problem at the service boundary); and prompts now cross a (private) wire, weakening the
data-locality win. This is the right move **only** past sustained high concurrency where
model-load amortization dominates — exactly the threshold `flexible-inference-lanes.md` reserves
for re-evaluation.

**Alternative B — GPU spot (lane 3).** Strictly a throughput play; irrelevant until ~300–500M
batch tok/mo or a diffusion/infill niche. Not a substitute for lane 2's locality/$0-idle profile.

**Verdict.** For the foundry's actual shape — bursty overnight batches, strong data-locality
preference, scale-to-zero economics, and a hard requirement to never crash or fabricate — the
**in-worker sidecar is the correct default**. Because lane selection is config (one node / one
env flip), graduating a hot path to Alternative A later is a routing change, not a rewrite, so
choosing the simplest correct thing now costs nothing later. The one improvement worth queuing:
feed the **receipt** per-node $/1M actuals back into the lane-selection policy so the
cloud-vs-CPU-batch choice becomes evidence-driven instead of the estimate above.
