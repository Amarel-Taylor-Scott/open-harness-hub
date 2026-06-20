# Repo2RLEnv + RL-environment synthesis tools — fit assessment

**Question (owner, 2026-06-08):** is `huggingface/Repo2RLEnv` and similar repos helpful to our companies/infra?
**Verdict:** **Yes — as a CANDIDATE eval / training-data generator** for OpenHarnessHub + OpenBenchmarkHub,
Teleon's evidence/promotion layer, and skill-digestion held-out verification. **NOT** a Baltor truth surface,
**NOT** an adopted runtime. Same governance ladder as every external tool: discovery ≠ trust · candidate ≠
active · benchmark result = evidence, never promotion authority · output ≠ truth.

## What Repo2RLEnv is (verified)
HuggingFace tool — **Apache-2.0**, Python (99%), **209★ / 28 forks, v0.8.3 (May 2026)**, on PyPI as
`repo2rlenv`. Converts any GitHub repo into a **verifiable RL environment**: mines PRs / commits / CVEs →
synthesizes tasks (problem statement + oracle solution + **executable reward**) → exports in **Harbor** task
format → optionally pushes datasets to the HF Hub. Reward = test pass-rate OR diff-oracle (format / file-target
/ semantic-judge). Pipelines:
- `pr_diff` — **lightweight, text-only** (agent proposes an edit, verifier scores vs the merged diff). Runs on
  `python:3.12-slim`, **no Docker** for the scoring itself. ← the safe first candidate.
- `pr_runtime` — SWE-bench-style flagship; **runs the repo's test suite inside a Docker sandbox**.
- `commit_runtime`, `cve_patches`, `mutation_bugs`, `code_instruct`, `equivalence_tests` (experimental).
- **Bootstrap phase** (sandbox pipelines) does **LLM-iterated Docker image construction** → calls Anthropic/OpenAI.

## Peers / landscape
- **R2E-Gym** (R2E-Gym/R2E-Gym, COLM 2025) — 8.1K procedurally-curated executable tasks via SWEGEN synthesis;
  **hybrid (execution + execution-free) verifiers**; 51% SWE-bench-Verified (SOTA open-weights). The most mature peer.
- **SWE-Gym** — 2.4K manually-curated Python tasks, each with an executable env + unit tests (train agent + verifier).
- **SWE-bench / SWE-bench Verified** — the *benchmark* (gold patches, no exec scaffolding); the yardstick these feed.
- **SWE-Synth, SWE-RL (self-play), SWE-Hub, SWE-Next** — synthesis/scaling variants.
- **Harbor** — the task **spec/format** Repo2RLEnv exports to. **This is the interop win:** adopt Harbor as the
  task contract and any of these (Repo2RLEnv, R2E-Gym) drops in behind ONE harness-intake port.

## Where it fits OUR portfolio (all CANDIDATE, behind ports)
1. **OpenHarnessHub / OpenBenchmarkHub (strongest fit).** It produces exactly what these hubs hold: verifiable
   eval tasks with executable rewards. Wire it behind a **harness-intake port**: repo → tasks+verifiers →
   HarnessArtifact / BenchmarkArtifact **candidates**. Its execution-based reward matches our "deterministic
   verifier > ask-the-model" preference. Honors "benchmark result is evidence, cannot promote a candidate alone."
2. **Teleon evidence / promotion.** Teleon promotes a candidate PurposeTask implementation only when *evidence
   decides*. Repo-derived RL tasks are a **source of that measured evidence** (task success on held-out tasks) —
   feed the scorecard / measured-lift harness as a candidate evidence generator. The reward is verifiable, not a
   model's opinion.
3. **Skill/tool digestion ([[shared-sandbox-and-skill-digestion]]).** When we digest a skill into a cheaper
   deterministic runtime, we need held-out tasks to prove the digest preserves behavior. `equivalence_tests`
   (agent reimplements a function, verified) maps directly to "prove digested-runtime ≡ original."
4. **Agentic-bot plane (this session's `src/teleon/agents/`).** To compare OpenClaw / Hermes / local-stub agents
   we need a bounded task+reward harness. `pr_diff` tasks are a candidate eval substrate — agents propose edits,
   a verifier scores, output is **evidence, never truth**.

## Cautions / guardrails (why CANDIDATE, not adopt)
- **It measures CODE-AGENT capability, not GOVERNED TRUTH.** Per [[moat-reframe-data-not-capability-gap]] our
  external moat is verified/current/provable DATA. Repo2RLEnv is **internal eval/training tooling** — never a
  Baltor product surface or a fact source. Its rewards are code-correctness, not fact-correctness.
- **Hits hard guardrails:** sandbox pipelines need **real Docker** (no-real-containers), and the bootstrap phase
  makes **network LLM calls** (no-network-LLM-unless-authorized), and it **pushes to HF Hub** (outward-facing
  publish; owner-gated; never tenant-private data). → Adopt **`pr_diff` only** first (text-only, no Docker);
  keep `pr_runtime`/bootstrap behind **SandboxProviderPort + the inference plane**, OWNER-GATED. Never
  pip-install/run it inside the flywheel — **metadata-only catalog candidate** like every external tool
  ([[agentic-tools-contextops-candidates]], [[github-signal-flywheel]]).
- **License Apache-2.0** = clean (adoptable; not a quarantine case).

## Recommended next steps (candidate ladder — NOT done here, queued)
1. Catalog entry: add Repo2RLEnv + R2E-Gym + SWE-Gym as `eval_env_synthesis` capability candidates in the
   external capability catalog (status=candidate, license, do-not-adopt-as-runtime note, Docker/LLM gates flagged).
2. Adopt **Harbor task format** as the harness-intake contract (so any synthesizer is swappable behind one port).
3. A `HarnessSynthProviderPort` with a deterministic **local stub** (offline golden path) + Repo2RLEnv/R2E-Gym as
   owner-gated candidate adapters returning ProviderUnavailableResult until Docker/keys + authorization exist.
4. First real use: `pr_diff`-style held-out tasks to verify **skill digestion** equivalence — the cleanest,
   no-Docker, highest-governance-fit entry point.

**Sources:** [Repo2RLEnv](https://github.com/huggingface/Repo2RLEnv) ·
[repo2rlenv on PyPI](https://libraries.io/pypi/repo2rlenv) ·
[R2E-Gym](https://github.com/R2E-Gym/R2E-Gym) · [r2e-gym.github.io](https://r2e-gym.github.io/) ·
[R2E-Gym (OpenReview, COLM 2025)](https://openreview.net/forum?id=7evvwwdo3z) ·
[SWE-Synth (arXiv)](https://arxiv.org/pdf/2504.14757) · [SWE-Hub (arXiv)](https://arxiv.org/pdf/2603.00575)
