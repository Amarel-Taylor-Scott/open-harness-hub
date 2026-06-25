# Ornith-1.0 (DeepReinforce) → Self-Evolving Harness Architecture (SEHA)

> Intel brief + adopted synthesis, compiled 2026-06-25 via the research lane. **serves_truth=false** (candidate
> intel; benchmarks are vendor self-reported, same-day, no third-party replication, no arXiv/technical report as
> of 2026-06-25 — treat as claims). Primary page fetched directly.

## TL;DR
- **Ornith-1.0** (DeepReinforce, ~2026-06-25, MIT) is an open coding-model family (9B/31B dense, 35B/397B MoE,
  post-trained on **Gemma 4 + Qwen 3.5**) whose headline is **self-scaffolding**: via RL the model learns to
  **write its own task harness** instead of using a fixed human-designed one.
- **Mechanism:** each RL step is two stages — propose a refined scaffold (conditioned on task + its *previous*
  scaffold), then generate a solution rollout conditioned on that scaffold; **one reward flows to both**, so
  scaffolds mutate-and-select toward higher-reward trajectories. Token-level **GRPO**, async pipeline-RL with a
  staleness weight. The scaffold = the "inner policy scaffold: memory, error-handling, orchestration logic."
- **Reward-hacking defense = a three-layer immutable boundary:** (1) fixed outer trust boundary
  (environment/tool-surface/test-isolation outside the model's reach), (2) a **deterministic monitor** that
  zeroes reward for reading withheld paths / editing verifiers / unsanctioned tools, (3) a **frozen LLM-judge
  veto** on top of the verifier. **This maps near-1:1 to our governance spine.**
- **Lineage confirmed:** DeepReinforce's **CUDA-L1** ([arXiv 2507.14111](https://arxiv.org/html/2507.14111v9),
  Contrastive-RL) fed prior *kernel* variants+scores back into the next prompt; Ornith feeds back *scaffold*
  variants. Same idea, higher abstraction.
- **Key nuance:** Ornith's scaffold is learned at **training time over a task category**; at eval it runs inside
  *fixed* third-party harnesses (Harbor/Terminus-2, **Claude Code 2.1.126**, **OpenHands**, mini-SWE-agent). Our
  analog mutates orchestration at **runtime over an open registry** and compiles toward **deterministic
  substitution** — strictly further down the descent.

## The mapping (why this validates us)
| Ornith mechanism | Our existing asset |
|---|---|
| Immutable outer boundary (env/tool-surface/test-isolation) | `scripts/run_proofs.py` gate (must go green before commit) + git-**worktree isolation** (`scripts/worktree_build.py`) |
| Deterministic monitor (zero reward for editing the verifier / reading withheld paths) | `src/teleon/runtime/access_policy.py` deny-by-default + the promotion boundary + **`scripts/check_seha_boundary.py`** (built today) |
| Frozen LLM-judge veto (judge vetoes, isn't the reward) | `scripts/panel_review.py` multi-model board; "LLM proposes, gate/governance dispose"; `serves_truth=false` |
| Mutable inner policy scaffold only | Mutable cheap workers (`bot_swarm.py`, `build_loop.py`) behind the immutable gate |

## How we go further (the wedge)
1. **Runtime, not training.** Ornith bakes one task-category's scaffold into weights; we mutate orchestration at
   runtime over an open registry — no retraining, and each mutation is a **versioned, interrogable, lossless**
   record, not opaque weights.
2. **Reward = truth + cost, not pass/fail.** Our descent (work → cheap → **deterministic substitution**) +
   receipts means a winning harness must pass the gate **and** be cheaper **and** preserve truth lineage.
3. **Externally auditable boundary.** Ours is a git + proof + ledger artifact (warrant, lossless distillation,
   archive-not-delete) — losers/rejects survive with lineage.
4. **Premature-stop defense.** Ornith has no analog to our **search-exhaustion ladder + kickstart injector** —
   a durability axis we own.

## SEHA — Self-Evolving Harness Architecture (adopted plan)
The harness is an **interrogable, mutable object** that can self-diagnose, spawn variants, and request
intervention — but **only inside the immutable proof-gate/governance boundary**, so a self-modifying harness
*cannot* reward-hack (exactly as Ornith enforces). Concrete, buildable, tied to real assets:
1. **Harness-as-interrogable-object** — register the orchestration loop in `interrogation_taxonomy.json` so the
   interrogation engine questions the harness each cycle (runtime "propose a refined scaffold").
2. **Variant spawning under worktree isolation** — `worktree_build.py` spawns N harness variants in isolated
   worktrees, each run against the **same** `run_proofs.py`; select max-green/min-cost ("mutate-and-select").
3. **Immutable reward set (deterministic monitor)** — **`scripts/check_seha_boundary.py` (BUILT today):** fail
   red if a worker/variant diff touches the verifier (`run_proofs.py`, `flywheel_proof_modules.py`), the access
   policy, or net-removes assertions from a check — Ornith's "zero reward, excluded from advantage," by
   construction.
4. **Frozen-judge veto** — wire `panel_review.py` as a veto *on top of* the green gate for green-but-suspicious
   mutations (weakened/narrowed a test). `serves_truth=false` stays.
5. **Reward-hacking regression corpus** — encode Ornith's named exploits (read-test-and-hardcode, touch the
   checked-for file, write literal expected output, copy oracle) as permanent adversarial fixtures the loop must
   never trip.
6. **Cost-and-truth selection** — score variants via `src/teleon/economics` cost_model + `serves_truth`
   provenance, not verifier-pass alone.
7. **Kickstart = exhaustion guard** — reject any variant that declares unavailable before climbing
   `search_exhaustion_ladder.json`; the harness must self-diagnose premature stopping.
8. **Lossless lineage + intervention requests** — every spawned/mutated/rejected variant archived (lossless,
   archive-not-delete) with a ledger warrant; a variant that can't pass files a `review_ticket` instead of
   silently degrading.

## Verifiability notes
**Confirmed (primary page, fetched directly):** name/date/MIT, four model sizes, Gemma-4/Qwen-3.5 base, the
scaffold-as-learnable-object framing, two-stage RL with reward to both stages, GRPO + staleness-weight pipeline-RL,
the verbatim three-layer reward-hacking defense, the benchmark tables. CUDA-L1 lineage independently confirmed.
**Vendor-reported, unreplicated:** all benchmarks (Ornith-397B 77.5 Terminal-Bench 2.1 / 82.4 SWE-Bench Verified;
beats Opus 4.7, trails Opus 4.8) — same-day, single-vendor, no reproduction. Eval ran inside *fixed* harnesses
(Claude Code 2.1.126, OpenHands), sharpening the "training-time scaffold" reading.
**Page is silent on:** scaffold format, task categories, RL step counts, judge identity, exact monitor rules,
compute, training code. No paper/technical report exists as of 2026-06-25 — blog + HF weights + X only.
**Sources:** [Ornith-1.0](https://deep-reinforce.com/ornith_1_0.html) ·
[HF collection](https://huggingface.co/collections/deepreinforce-ai/ornith-10) ·
[MarkTechPost](https://www.marktechpost.com/2026/06/25/deepreinforce-releases-ornith-1-0-an-open-source-coding-model-family-that-learns-its-own-rl-scaffolds/) ·
[CUDA-L1 arXiv 2507.14111](https://arxiv.org/html/2507.14111v9) · [CUDA-L1 GitHub](https://github.com/deepreinforce-ai/CUDA-L1)
