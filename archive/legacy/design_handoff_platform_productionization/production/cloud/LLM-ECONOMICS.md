# LLM Economics — inference cost strategy (Pass 12)

How the platform spends money on models. The LLM plane (OpenAI-compatible router +
receipt per invocation) is already the seam; this doc gives it a routing POLICY and
the adoption triggers. Numbers verified Jun 2026 — re-verify at adoption; this market
moves monthly.

## The five lanes (route by workload class, not by vibe)

| Lane | Workload | Backend | Cost shape |
|---|---|---|---|
| **L-dev** | local development, prototyping | **Ollama local** — free and unlimited on own hardware; OpenAI-compatible | $0 |
| **L-agent** | long-running coding/agent loops (Claude Code, research agents) | **Fixed subscriptions** — Claude Max; Ollama Cloud ($0 / $20 / $100 flat, GPU-time limits, explicitly no overage bills for runaway agents) | flat $/mo |
| **L-interactive** | product features users wait on | Provider APIs via the plane, **model-class routing**: budget class default (e.g. nano/flash-tier at ~$0.10–0.27/M input), frontier class gated to tasks that measurably need it | $/token |
| **L-batch** | bulk, not latency-sensitive — **Baltor's verification rail is the canonical case** (scheduled re-verification of packs/sources), eval runs, enrichment sweeps | provider **batch endpoints** (~50% discount) or open models; queue + nightly window | $/token ÷ 2 |
| **L-selfhost** | sustained high-volume open-model traffic | **vLLM** on rented GPU (H100 ~$2.50–3.50/hr; Hetzner GEX44 €184/mo; RunPod 4090 ~$1.89/hr) | fixed $/mo |

The hybrid pattern is the whole strategy: open models for high-volume cheap inference
(classification, summarization, RAG synthesis, verification checks), frontier APIs for
the few requests that genuinely need frontier reasoning — the documented industry
result is a 60–80% bill cut without quality loss.

## Rules (binding)

1. **Model classes, not model names, in code** (S12): the plane's config maps
   `class: budget|frontier|batch|local → model id`. Swapping a model is config.
2. **Receipts decide, not enthusiasm.** Every invocation already emits usage + key.
   Lane moves require receipt evidence (below). Spend per key/realm/class is the
   weekly review input (OPERATIONS.md).
3. **Batching is a product feature for Baltor.** The verification rail re-checks
   thousands of facts on a schedule — that's batch-lane by construction. Build the
   queue once; it halves the largest predictable spend line.
4. **No silent model downgrades**: the served-answer receipt records which class
   served it.

## Self-hosting triggers (honest math — the trap is real)

Self-hosting LOOKS cheap and usually isn't: real cost runs **3–5× the raw GPU rental**
once DevOps time is priced (10–20 hrs/mo conservatively), and against budget APIs
($0.15–0.27/M input) the break-even is **billions of tokens/month**. One published
all-in figure: a single A100 deployment ≈ $3,240/mo at 1M tokens/day — a volume a
budget API serves for a few dollars.

Therefore L-selfhost requires ALL of:
- Receipts show provider spend ≥ 2× the ALL-IN GPU cost (rental × 3 for ops tax) for
  3 consecutive months, **or** a privacy/regulatory requirement that forbids provider
  APIs (then cost is moot), and
- the workload fits an open-weight model (quality gap to frontier ~5–10% on most
  benchmarks — fine for verification/classification, not for frontier reasoning), and
- the stack is **vLLM** (production: continuous batching, PagedAttention; TGI is in
  maintenance mode since Dec 2025; Ollama stays the dev/local tool — its concurrent
  throughput is 30–50% below vLLM by design).

Entry shape when triggered: ONE rented GPU box (Hetzner GEX44 €184/mo gate from
SCENARIOS S-G), vLLM serving a quantized model, registered as an adapter behind the
plane — callers never know. K8s GPU pools only after S-F triggers fire independently.

## Ollama Cloud — where it fits

Fixed-rate managed inference for open models ($20 Pro / $100 Max, GPU-time-based
limits, session caps reset 5-hourly/weekly): the right tool for **agent loops and dev
workloads** where runaway usage must not produce surprise bills, and a zero-ops
stepping stone before any vLLM commitment. Not an SLA-backed production backend —
product traffic stays on provider APIs until receipts justify L-selfhost.

## Adoption order (one per pass)
1. Model-class config in the plane (budget default, frontier gated) + class recorded
   in receipts. Proof: receipts show class per invocation.
2. Batch lane: queue + nightly batch-endpoint submission for verification-rail style
   jobs. Proof: one batch round-trip at ~half the per-token rate.
3. Ollama adapter (local first, Cloud optional) for L-dev/L-agent. Proof: plane serves
   a completion from Ollama with a receipt, zero code change for callers.
4. Spend dashboard from receipts: $/realm/class/week vs PRO-FORMA. Proof: weekly
   report generated from data.
5. (Trigger-gated) vLLM box per the rules above.
