---
description: Backend loop — build a local-first Environment + Reward Spine (Repo2RLEnv/Harbor/OpenEnv-style agent eval as governed CANDIDATES), one proof-backed increment per cycle
---

YOU ARE CLAUDE CODE RUNNING THE AGENT ENVIRONMENT + REWARD SPINE LOOP. Backend/platform, NOT design.
Goal: a local, stdlib-only Environment + Reward Spine that can LATER adapt Repo2RLEnv, Harbor, OpenEnv, ORS,
SWE-bench, SWE-Gym, R2E-Gym, SWE-smith, Terminal-Bench, RepoLaunch, NeMo Gym — as CANDIDATES behind ports.
Each cycle = ONE NEW proof-backed increment unless `.agent/STOP_REQUESTED` exists.

## CORE POSITIONING
Teleon runs capabilities · Baltor governs truth · OpenBenchmarkHub defines WHAT is measured · OpenHarnessHub
runs/verifies HOW · Shared Sandbox Gateway isolates candidate execution · Shared LLM Plane routes model calls +
writes ModelInvocationReceipt. **Benchmark result = EVIDENCE, never promotion authority. Agent/LLM output is
never truth. Candidate ≠ active. Discovery ≠ trust.** This spine MEASURES agents/runtimes; it never promotes them.

## HARD GUARDRAILS
No install of Repo2RLEnv/Harbor/etc · No Docker · No live LLM · No dataset push · No provider keys · No raw keys
in source/configs/receipts · No benchmark-promotes-candidate · No agent-output-as-truth · No second ledger/bus/
LLM-wrapper/worker-framework. No commit/push/pip. Missing Docker/key/dep → ProviderUnavailableResult + local
equivalent + candidate metadata + record blocker + continue. Watchdog: restart ONLY by EXACT pid in
`.agent/flywheel-watchdog.pid` if PROOF_MODULES changed; never pgrep/pkill (pgrep matches its own shell). Stop
ONLY on `.agent/STOP_REQUESTED`.

## VERIFIED REALITY (re-verify each cycle)
- Agent-runtime layer BUILT + redteamed: `_repos/teleon/backend/src/teleon/agents/agent_runtime_provider.py` + `check_agent_runtime_layer`
  + `check_agent_runtime_layer_redteam` (the thing this spine measures). Sandbox: `_repos/teleon/backend/src/teleon/sandbox` (SandboxProviderPort).
  LLM plane: `_repos/teleon/backend/src/teleon/inference` (route model calls through it; never raw provider calls). flywheel ~386+.
- Repo2RLEnv research recorded: `_repos/shared-backend-components/context/research/repo2rlenv-and-rl-env-synthesis.md` + memory `rl-env-synthesis-tools`.

## TARGET LADDER (first incomplete; mark VERIFIED_DONE + advance, never stop)
- **P1 (start here): research registry** — `architecture/agent_environment_research_registry.json` (entries:
  envgen.repo2rlenv@candidate, harness.harbor@candidate, envspec.openenv@candidate, reward.openreward_ors@candidate,
  bootstrap.repolaunch@candidate, benchmark.swebench@reference, benchmark.terminalbench@candidate,
  benchmark.r2egym@candidate, benchmark.swesmith@candidate, benchmark.swegym@candidate, gym.nemo@candidate). Each:
  purpose · source_url · license(+confidence) · requires_docker/network/llm/api_key · local_equivalent ·
  openhub_mapping · teleon_fit · baltor_fit · status(candidate|reference, NEVER active) · proof_to_promote. Proof
  `scripts/check_agent_environment_research_registry.py`.
- **P0 contracts:** schemas/environments/{AgentEnvironmentArtifact,EnvironmentProviderNode,EnvironmentRunRequest,
  EnvironmentRunResult,EnvironmentRunReceipt,RewardSpec,RewardResult,RewardProviderNode,EnvironmentCompatibilityReport}.v1
  + register in contract_registry + check_agent_environment_contracts.
- **P2 local provider:** _repos/teleon/backend/src/teleon/environments/{local_environment_provider,reward_runner}.py + _repos/teleon/backend/src/teleon/ports/
  {environment_provider,reward_provider}.py — offline, no Docker, no key, writes EnvironmentRunReceipt, deterministic
  reward, output-contract validation + check_local_environment_provider.
- **P3 Baltor context env (the killer internal demo):** environment.baltor.cfpb_context_governance.local@v1 —
  reward = answer "10 business days" + FAQ "30 days" held out + source handles present + receipt present + no
  allegation served + no LLM-output-as-truth + check_baltor_context_environment. (Reuse the existing CFPB seed.)
- **P4 Teleon env:** environment.teleon.capabilitytask_runtime_selection.local@v1 — reward = candidate-not-active-
  before-promotion + scorecard + rollback + runtime-decision-receipt + boundary-approval + check_teleon_capability_environment.
- **P5 candidate adapters (stubs only):** _repos/teleon/backend/src/teleon/environments/providers/{repo2rlenv,harbor,openenv,ors,repolaunch}_candidate.py
  — no import-at-load if dep missing; ProviderUnavailableResult; Docker/LLM-required stay candidate; no raw keys; no push.
- **P6 redteam:** check_agent_environment_redteam — attacks: benchmark promotes candidate / agent output→Baltor truth /
  Repo2RLEnv runs Docker unauthorized / Harbor uses raw key / OpenEnv network without policy / reward LLM-judge without
  ModelInvocationReceipt / source license+provenance missing / private-repo marked public / Docker-required marked active /
  free endpoint with sensitive data. All fail safely.
- **P7 full stack:** check_agent_environment_full_stack + regressions.

## CADENCE / RECEIPT
New code → deterministic offline `--self-test` (exit 0/1, inject `now`). Register in PROOF_MODULES → restart watchdog
by exact pid if changed. Regressions each cycle: demo_offline_full_baltor + check_baltor_full_stack_perfect +
check_no_direct_provider_bypass + baltor_flywheel --once. Receipt → `.agent/baltor-goal-loop-log.md`; refresh
`.agent/{north-star-loop-state,hardcore-loop-state,next-action}.json`. ScheduleWakeup 1200s with
`/loop 1200 /agent-environment-and-reward-spine`. Honor hard STOP.
