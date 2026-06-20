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

- **One plane, many nodes:** every lane = a node in `architecture/model_provider_graph.json`
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
