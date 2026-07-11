# Sakana "Fugu" / "Fugu Ultra" and the LLM-Routing / Multi-Agent-Orchestration Landscape

> Intel brief compiled 2026-06-25 via the Ollama coding harness's research lane. **serves_truth=false**
> (discovery ≠ trust; candidate intel). Benchmark figures and quotes are drawn from Sakana's own materials;
> independent confirmation is flagged in the final section. Competitor benchmark numbers cited by Sakana are
> **provider-reported**, not independently re-run.

## TL;DR
- **Fugu is "a multi-agent system as a model"**: one OpenAI-compatible endpoint (`fugu`, `fugu-ultra`) that
  decomposes a task and routes sub-tasks across a closed pool of three frontier models — Gemini-3.1-Pro,
  Claude-Opus-4.8, GPT-5.5 — then verifies and synthesizes. Launched **2026-06-22**
  ([sakana.ai/fugu](https://sakana.ai/fugu/), [technical report](https://arxiv.org/html/2606.21228v2)).
- **Routing is learned, not heuristic.** Fugu (latency tier) uses a **selection head over the orchestrator's
  logits**; Fugu-Ultra (quality tier) uses a **Conductor trained with RL (GRPO)** that emits an agentic
  workflow in natural language — each step a `(subtask, worker-id, access-list)` triple, capped at **5 steps**.
- **Headline claim:** Fugu-Ultra matches export-controlled frontier models **without access to them** — e.g.
  SWE-Bench Pro **73.7**, GPQA-Diamond **95.5** — beating each individual worker. Only Fugu's own scores were
  re-run; competitor scores are provider-reported.
- **Lineage:** evolutionary weight-merging (2024) → AB-MCTS / TreeQuest inference-time multi-model search
  (2025) → behavior-level fusion (Fugu, 2026): composing black-box models without parameter access.
- **The wedge for our universal computation compiler:** every system here routes *among models*. None
  **compiles down to deterministic substitution**, exposes an **open agnostic registry**, or **governs truth +
  cost with receipts**. That is our defensible negative space.

## Primary — Sakana Fugu / Fugu Ultra
A trained orchestrator delivered as a single model API; the caller never sees the team behind it. Sakana
attributes it to two papers — **TRINITY** (an evolved coordinator assigning Thinker/Worker/Verifier roles) and
**Conductor** (RL-discovered natural-language coordination), described as ICLR 2026
([sakana.ai/fugu](https://sakana.ai/fugu/),
[MarkTechPost](https://www.marktechpost.com/2026/06/22/sakana-ai-launches-sakana-fugu-an-orchestration-model-that-routes-tasks-across-a-swappable-pool-of-frontier-llms/)).

**Architecture / routing (technical report):**
- *Fugu (latency):* a lightweight **selection head runs in parallel to the base model's LM head**, taking the
  hidden state and emitting logits that score which worker to call — uses the orchestrator's *logits, not
  generated text*, to cut latency. Tuned via singular-value fine-tuning. Trained SFT (KL to a soft target from
  running every worker n times) → evolutionary optimization (sep-CMA-ES) on real coding-assistant trajectories.
- *Fugu-Ultra (quality):* the **Conductor**, RL-trained with **GRPO (no KL penalty)**, outputs an **agentic
  workflow as natural language** dividing the task into sub-tasks. Each step carries a natural-language
  subtask, an integer worker id, and an **access list**. **≤5 steps**, with **intra-workflow agent isolation**
  to prevent "orchestration collapse," plus persistent shared memory and per-agent function-call tracking.
- *Emergent topologies (RL re-discovered):* debate/aggregation for knowledge tasks, build-and-debug (GPT-5.5
  builds, Opus verifies), and "bringing in a specialist."

**Benchmarks (report):** SWE-Bench Pro 73.7 (Ultra) vs Opus-4.8 69.2; GPQA-Diamond 95.5; LiveCodeBench 93.2;
Terminal-Bench 2.1 82.1; Humanity's Last Exam 50.0. Report's own caveat: *all non-Fugu scores are provider-
reported.*

**Access / cost.** Users can opt specific models out for compliance (Ultra's pool is fixed). Billed **once at
the top model's rate — fees never stack** across agents (Ultra ≈ $5 in / $30 out per 1M tokens). Not available
in EU/EEA pending GDPR work. Early third-party tests report up to **30-minute waits**
([TechTimes](https://www.techtimes.com/articles/318968/20260624/ai-orchestrator-sakana-fugu-claims-fable-5-parity-real-world-tests-reveal-30-minute-waits.htm)).
Strategic pitch = vendor-lock-in mitigation / redundancy
([VentureBeat](https://venturebeat.com/orchestration/no-claude-fable-5-no-problem-sakana-achieves-frontier-performance-with-new-fugu-multi-model-auto-synthesis-system)).

## Sakana's through-line
- **Evolutionary Model Merging (2024):** evolutionary search merged open models into a 7B Japanese-math model
  beating 70B models
  ([VentureBeat](https://venturebeat.com/ai/how-sakana-ais-new-evolutionary-algorithm-builds-powerful-ai-models-without-expensive-retraining));
  extended by **M2N2** ([arXiv 2508.16204](https://arxiv.org/html/2508.16204v1)).
- **AB-MCTS / TreeQuest (2025, Apache-2.0):** Adaptive-Branching MCTS uses Thompson sampling to choose
  "go wider" vs "go deeper"; Multi-LLM AB-MCTS adds a multi-armed-bandit choice of *which* model. On ARC-AGI-2,
  Gemini-2.5-Pro + DeepSeek-R1 + o4-mini hit **>30% Pass@250** vs **23%** for o4-mini alone
  ([sakana.ai/ab-mcts](https://sakana.ai/ab-mcts/), [GitHub](https://github.com/SakanaAI/treequest)).

Arc: **weight-level → inference-time-search-level → behavior-level** fusion. Same thesis (collective
intelligence beats any single model) at progressively higher abstraction.

## Secondary systems

| System | Routing mechanism | Open? | Cost lever | Notable |
|---|---|---|---|---|
| **Sakana Fugu** | Learned selection-head (logits) + RL Conductor workflow | Closed | Single top-tier rate, no fee stacking | Frontier-to-frontier; ≤5-step + access lists |
| **RouteLLM** (LMSYS) | Learned **strong-vs-weak** classifier on Arena data | **Open** ([repo](https://github.com/lm-sys/RouteLLM)) | Easy queries → cheap model | >85% cost cut at ~95% GPT-4 quality ([2406.18665](https://arxiv.org/abs/2406.18665)) |
| **FrugalGPT** (Stanford) | **Cascade/escalation** + learned scorer | Paper | Stop early on cheap confident answer | Up to **98%** cost reduction ([2305.05176](https://arxiv.org/abs/2305.05176)) |
| **Together MoA** | Layered **aggregation** (proposers → aggregator) | **Open** ([blog](https://www.together.ai/blog/together-moa)) | Cheap open models, collectively | Beats GPT-4 Omni on AlpacaEval LC ([2406.04692](https://arxiv.org/abs/2406.04692)) |
| **OpenRouter** | Marketplace; Auto Router + price/outage-aware provider routing | Gateway, agnostic | Provider arbitrage | 400+ models/60+ providers |
| **Martian** | Learned router by uptime/skill/cost | Closed | Cost-performance routing | "First LLM router"; RouterBench |
| **NotDiamond** | Query→best-model classifier | Closed | Per-query selection | [awesome-ai-model-routing](https://github.com/Not-Diamond/awesome-ai-model-routing) |
| **vLLM Semantic Router** | Semantic intent classifier (Rust+Candle) | **Open** ([repo](https://github.com/vllm-project/semantic-router)) | Cut wasted tokens; route by intent | Adds jailbreak/**hallucination** detection |

*Taxonomy:* learned classifier (RouteLLM/NotDiamond/vLLM-SR) · cascade (FrugalGPT) · tree-search/bandit
(AB-MCTS) · aggregation (MoA) · learned decomposition+RL (Fugu) · marketplace/heuristic (OpenRouter).

## What this project should learn (→ proposal backlog)
1. **Logit-level selection head as rung-0 routing** — a near-zero-latency classifier that predicts which
   registry component to try first (intelligence-light, fits "remove intelligence from the path").
2. **Access-list as a first-class field on every compiled DAG node**, enforced through `access_policy.json` /
   `credential_registry` — routing and authorization become one artifact.
3. **Bounded decomposition + intra-workflow isolation** (hard depth cap like Fugu's 5 steps + context
   isolation) baked into `synthesis_tree` / `intent_to_dag` as a stability rail.
4. **A named topology library** — catalog debate/aggregate (=MoA), escalation (=FrugalGPT), bandit-select
   (=AB-MCTS), builder+verifier as `vertical_playbooks` / compose templates the compiler instantiates.
5. **Vendor TreeQuest (Apache-2.0)** as a candidate backtracking engine for uncertain-component selection;
   feed per-component reward from receipts.
6. **"Single top-tier rate, never stack fees" pricing primitive** — bill predictably while the receipt
   itemizes fan-out; answers the "multi-agent = multiplied bill" objection.
7. **Independently measured lift** — two-axis admission (measured lift over the bare model) + receipts =
   a verifiability advantage frontier routers structurally avoid.
8. **Verification as a product, not a role** — external truth/provenance (receipts, CDC, stance/contradiction)
   that sits on top of any router, including Fugu-as-a-worker.

## How we differ / the wedge
1. **We compile *down*, not *across*** — terminal rung is deterministic substitution (remove the LLM). No
   router targets that.
2. **Open, agnostic, internet-scale registry** vs a closed 3-model pool.
3. **Two governed objectives (TRUTH + COST) with receipts** vs one (quality).
4. **A verified, inspectable, re-runnable DAG** vs a black-box answer.
5. **Routers are workers beneath us** (and we govern above them) — Fugu/OpenRouter/RouteLLM are expensive rungs
   the descent invokes only when cheaper/deterministic rungs fail.

## Verifiability notes
**Confirmed (primary/official Sakana):** two-tier structure; selection-head-on-logits; RL Conductor with
NL workflows + per-step access lists + 5-step cap + intra-workflow isolation + shared memory; 3-model pool;
benchmark figures; pricing; EU/EEA unavailability; the report's caveat that competitor scores are provider-
reported. AB-MCTS/TreeQuest mechanics + ARC-AGI-2 numbers + Apache-2.0 confirmed.
**NOT independently confirmed:** (a) the **7B "conductor"** parameter figure (in secondary coverage; **not in
the technical report** — treat as unverified); (b) **ICLR 2026** acceptance (Sakana-asserted); (c) whether
benchmark wins replicate under independent re-running; (d) the "30-minute waits" criticism (single secondary
report).
**Correction:** **"Lion" is NOT a Sakana product** — it is a Google/UCLA optimizer (Chen et al.,
[arXiv 2302.06675](https://arxiv.org/abs/2302.06675)). Thematically adjacent, but do not attribute to Sakana.
