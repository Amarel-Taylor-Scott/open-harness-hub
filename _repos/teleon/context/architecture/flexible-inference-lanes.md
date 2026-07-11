# Flexible inference lanes — adapt compute to the job, forever (2026-06-11)

Owner directive: Gemma-4-class models do NOT need a GPU for long-running non-realtime work;
Fly stays the host but with MAXIMUM flexibility. This doc is the adaptive-compute design the
provider graph + OIPS policy implement over time. Law: every lane is a provider-graph NODE
behind the one receipted plane (ChatRoute→OIPS, landed 2026-06-11) — switching lanes is
routing policy, never code.

## The four lanes (route by job class, not by habit)

| Lane | What | When | Cost shape |
|---|---|---|---|
| 1. Cloud APIs | Ollama Cloud (flat), OpenRouter (gemma-4-26b $0.06/$0.33; qwen3-next) | Interactive demo calls, anything latency-bound | ~$6/mo @1k calls/day |
| 2. **CPU batch self-host** | Gemma-4 quantized (Q4 ~3.8B-active MoE runs well on CPU) via llama.cpp/Ollama ON the worker fleet's own scale-to-zero machines (e.g. shared-cpu-4x/8GB ≈ $0.03/hr-class) | Foundry batches, overnight enrichment, CDC re-verification — anything where tokens/sec doesn't matter but $/token and data-locality do | Pennies per batch window; $0 idle |
| 3. GPU spot | RunPod-class 5090/L40S (Fly GPUs DIE 2026-08-01 — never assume them) | Only past ~300–500M batch tok/mo or if a diffusion/infill niche emerges | $0.65–1/hr only while running |
| 4. Local dev | gemma4-e2b on the dev box | Free iteration | $0 |

## How it adapts in the future (the flexibility mechanics)

- **One plane, many nodes:** every lane = a node in `_repos/shared-backend-components/architecture/model_provider_graph.json`
  with its own `base_url`/`model`; OIPS selects by `allowed_use` + policy; every call mints a
  receipt with `executed_base_host`. Adding a lane is a JSON edit (proven: the OpenRouter
  gemma-4 node landed with zero code).
- **Job-class routing:** foundry jobs carry `latency_class: batch|interactive` → policy maps
  batch→lane 2, interactive→lane 1. The worker image already contains everything needed to
  run a llama.cpp server as a sidecar process for the duration of a batch (start model →
  drain queue → exit → machine stops; receipts record the local base_host honestly).
- **Cost telemetry closes the loop:** receipts (now persisted) accumulate $/1M-token actuals
  per node; promotion/demotion of routes becomes an EVIDENCE decision (the same gate
  philosophy as capabilities) instead of vibes.
- **Provider failure = routing, not outage:** Ollama Cloud caps → OpenRouter fallback edge;
  OpenRouter price shift → re-point node; Fly exit → lanes 1/3 unaffected, lane 2 follows the
  workers to any provider (it's just CPU).

## Next builds (queued, in order)

1. `model.openrouter.gemma_4_26b@candidate` node — LANDED 2026-06-11 (key already on file).
2. Worker batch-inference sidecar: `OH_BATCH_LLM=local` flag in the worker → start llama.cpp
   with a baked/downloaded Q4 gemma-4, point ChatRoute at 127.0.0.1 for the batch, exit clean.
3. Policy: `latency_class` on foundry job payloads + OIPS mapping + per-node cost actuals
   report from the receipts sink.
4. Re-evaluate DiffusionGemma only on its triggers (llama.cpp/Ollama support; hosted ≲$0.15/1M).

---

## Model-efficiency routing — auto-pick the cheapest capable model (merged 2026-07-03 from `model-efficiency-routing.md`)

> **Merge note (2026-07-03):** the former `context/architecture/model-efficiency-routing.md` is folded in
> here (its home) and archived under `_repos/_shared/archive/legacy/teleon/context/architecture/`. It is the
> **efficiency-ranking** companion to the four lanes above: the lanes decide *what compute is available*;
> this decides *which allowed node is cheapest for the job*. Owner question (2026-06-11): *"do we need a new
> surface for ClawWork, or could that fit into OpenRouting?"* — **Answer: no new surface. It fits the routing
> layer you already have.**

### The three-part placement

| Concern | Where it lives | Status |
|---|---|---|
| Routing **policy/intelligence** (the surface users see) | **OpenRoutingHub** | hub exists |
| Runtime **mechanism** (picks a node per call) | **OIPS `select_provider`** (`_repos/teleon/backend/src/teleon/inference/oips.py`) | built; orders by a fixed list today |
| **Evidence** (which model is most efficient per task class) | **`_repos/teleon/backend/src/teleon/inference/model_efficiency.py`** | built + self-tested 11/11 |
| **ClawWork** (an external economic leaderboard) | a **candidate data source**, wrapped + governed | `ingest_external_ranking` |

ClawWork is NOT a surface — it's the same shape as our other external wraps (ktx, LiteLLM): we ingest its
ranking *signal*, governed as a candidate (`is_truth:false`, weighted below our own measured receipts,
review-gated). We do not run its agent.

### What the ranking does (real, from data we already log)

Every `ModelInvocationReceipt` already records `cost_estimate_usd`, `latency_ms`, `tokens`, `selected_model`,
`requested_model_class`, `fallback_used`. `rank_models(receipts, task_class)` aggregates those into a
per-(model, task-class) **efficiency score** (cost 0.55 / latency 0.25 / reliability 0.20, lower-is-better,
min-max normalized within the class), best first, thin samples flagged not hidden. An optional per-model
**quality** map (fed by the measured-lift producer) turns it into a true **quality-per-cost** ranking.
Offline-honest: no receipts ⇒ empty ranking, never a fabricated order.

### The OIPS wire-in (one line, documented — apply when ready)

`select_provider` today builds the eligible order from the policy's fixed `allowed_provider_nodes`:

```python
order = [n for n in eff.get("allowed_provider_nodes", []) if n not in disallowed and n in idx]
```

The wire-in reorders that *already-eligible* list by measured efficiency — eligibility (policy / secret /
specialization / health) is unchanged; only the ORDER among allowed nodes improves:

```python
from src.teleon.inference.model_efficiency import rank_models, efficiency_order, load_receipts
ranking = rank_models(load_receipts(RECEIPTS_PATH), task_class=eff.get(...class...))
order = efficiency_order(order, ranking)   # ranked-eligible first; unranked keep policy order after
```

`efficiency_order` never demotes a node with no measured evidence below a thin guess (it preserves the
declared preference for the unmeasured), so this is a safe, monotone improvement: as receipts accumulate,
routing gets cheaper without ever violating policy.

### Why this is on-thesis

This is the "self-adaptive compute" claim made concrete: the system measures its own cost/quality per task
and routes to the cheapest capable model — *measured efficiency, not vibes*. ClawWork validates the same bet
(rank by quality + cost + economic sustainability, not raw benchmarks). It pairs with the four lanes above
and the measured-lift producer (the quality axis).

### Honest remaining work
- Wire `efficiency_order` into `oips.select_provider` (one line above; deferred so it lands with a test).
- The quality axis needs the measured-lift producer (cut off by the session limit — redo it).
- A periodic job to refresh the ranking from the receipts sink (a scheduled tick, like the worker feeder).
- Optionally surface the ranking in the OpenRoutingHub UI (read-only projection — never truth).
