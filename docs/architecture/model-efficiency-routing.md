# Model-efficiency routing — auto-pick the cheapest capable model (no new surface)

Owner question (2026-06-11): *"do we need a new surface for ClawWork, or could that fit into
OpenRouting?"* — **Answer: no new surface. It fits the routing layer you already have.**

## The three-part placement

| Concern | Where it lives | Status |
|---|---|---|
| Routing **policy/intelligence** (the surface users see) | **OpenRoutingHub** | hub exists |
| Runtime **mechanism** (picks a node per call) | **OIPS `select_provider`** (`src/teleon/inference/oips.py`) | built; orders by a fixed list today |
| **Evidence** (which model is most efficient per task class) | **`src/teleon/inference/model_efficiency.py`** (NEW) | built + self-tested 11/11 |
| **ClawWork** (an external economic leaderboard) | a **candidate data source**, wrapped + governed | `ingest_external_ranking` |

ClawWork is NOT a surface — it's the same shape as our other external wraps (ktx, LiteLLM): we
ingest its ranking *signal*, governed as a candidate (`is_truth:false`, weighted below our own
measured receipts, review-gated). We do not run its agent.

## What the ranking does (real, from data we already log)

Every `ModelInvocationReceipt` already records `cost_estimate_usd`, `latency_ms`, `tokens`,
`selected_model`, `requested_model_class`, `fallback_used`. `rank_models(receipts, task_class)`
aggregates those into a per-(model, task-class) **efficiency score** (cost 0.55 / latency 0.25 /
reliability 0.20, lower-is-better, min-max normalized within the class), best first, thin samples
flagged not hidden. An optional per-model **quality** map (fed by the measured-lift producer) turns
it into a true **quality-per-cost** ranking. Offline-honest: no receipts ⇒ empty ranking, never a
fabricated order.

## The OIPS wire-in (one line, documented — apply when ready)

`select_provider` today builds the eligible order from the policy's fixed `allowed_provider_nodes`:

```python
order = [n for n in eff.get("allowed_provider_nodes", []) if n not in disallowed and n in idx]
```

The wire-in reorders that *already-eligible* list by measured efficiency — eligibility (policy /
secret / specialization / health) is unchanged; only the ORDER among allowed nodes improves:

```python
from src.teleon.inference.model_efficiency import rank_models, efficiency_order, load_receipts
ranking = rank_models(load_receipts(RECEIPTS_PATH), task_class=eff.get(...class...))
order = efficiency_order(order, ranking)   # ranked-eligible first; unranked keep policy order after
```

`efficiency_order` never demotes a node with no measured evidence below a thin guess (it preserves
the declared preference for the unmeasured), so this is a safe, monotone improvement: as receipts
accumulate, routing gets cheaper without ever violating policy.

## Why this is on-thesis

This is the "self-adaptive compute" claim made concrete: the system measures its own cost/quality
per task and routes to the cheapest capable model — *measured efficiency, not vibes*. ClawWork
validates the same bet (rank by quality + cost + economic sustainability, not raw benchmarks). It
pairs with `flexible-inference-lanes.md` (the lanes) and the measured-lift producer (the quality axis).

## Honest remaining work
- Wire `efficiency_order` into `oips.select_provider` (one line above; deferred so it lands with a test).
- The quality axis needs the measured-lift producer (cut off by the session limit — redo it).
- A periodic job to refresh the ranking from the receipts sink (a scheduled tick, like the worker feeder).
- Optionally surface the ranking in the OpenRoutingHub UI (read-only projection — never truth).
