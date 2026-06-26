---
description: Backend loop — harden the shared LLM routing plane + shared agentic-bot plane (OpenClaw/Hermes as governed candidates), one proof-backed increment per cycle
---

YOU ARE CLAUDE CODE RUNNING THE SHARED LLM PLANE + SHARED AGENTIC BOT IMPLEMENTATION LOOP.
A backend/platform implementation loop — NOT design, NOT greenfield, NOT a vendor-install loop, NOT a
"free API key" loop. Every cycle completes ONE NEW proof-backed increment unless `.agent/STOP_REQUESTED` exists.

Goal: a shared internal LLM routing plane + a shared agentic-bot control plane that route work to local
stubs, official providers, free/limited prototype endpoints, OpenClaw, Hermes, and future harnesses —
WITHOUT leaking secrets, bypassing governance, or creating a duplicate LLM wrapper / event bus / ledger.

## VERIFIED REALITY (2026-06-08 — re-verify each cycle; do NOT rebuild these)
- **LLM plane EXISTS under the `inference` naming** (NOT `llm`): `schemas/inference/{InferencePreference,
  InferenceRequest,ResolvedInferencePreference,ModelRouteDecision,ModelInvocationReceipt,FreeLimitedEndpoint,
  GatewayRepoAssessment,EndpointDueDiligenceReport}.v1`; `src/teleon/inference/{oips,adapters,free_endpoint_intel,
  api_projection}.py`; routes `/api/inference/{providers,receipts,model-graph,resolve-preference,
  preferences,structured-local,free-endpoints,health}` (`scripts/api_inference_handler.py`). Proven:
  check_inference_* , check_free_limited_endpoint_intel. The shared LLM plane (Inference Gateway + OIPS) is
  BUILT — P0B/P0C/P0D/P0E map to these. Treat `/api/llm/route` ≡ the existing inference route surface;
  EXTEND/alias, never fork a second gateway.
- **`architecture/free_limited_llm_endpoint_registry.json`** covers GitHub Models/Groq/Mistral/Gemini/Cerebras/
  Cloudflare Workers AI/OpenRouter:free/HuggingFace/NVIDIA NIM + Ollama; Together = paid (class 300); class
  codes already encode shared-key/bypass→quarantine(900), discovery→metadata(600), browser-runtime≠endpoint.
  ClawLess lives in `architecture/sandbox_provider_catalog.json` (runtime/sandbox), NOT the endpoint registry.
- **Agent plane: agent-runtime layer BUILT this session** — `src/teleon/agents/agent_runtime_provider.py`
  (AgentRuntimeProviderPort + LocalEmulator active + ClawLess/OpenClaw + Hermes CANDIDATE adapters returning
  AgentRuntimeUnavailable; `dispatch_agent_request` delegates to execution_backend_selector, hard-guards
  open-ended agents off generic cloud functions) + `architecture/agent_runtime_catalog.json` +
  check_agent_runtime_layer (flywheel 385). RIDES ExecutionProviderPort + FleetLedger — never a 2nd framework.
- **GENUINE GAPS (build these first):** (1) NO `schemas/agents/` governed run contracts (P1A:
  AgentRunRequest/Result/Receipt + Tool/Skill/Sandbox/Memory policies). (2) NO `check_agent_runtime_layer_redteam`
  (P1F). (3) OpenClaw/Hermes are runtime CANDIDATES but lack the AgentRunReceipt-level contract adapters + skill
  intake bridge (P1B/P1C/P1D). Start the loop on the AGENT track, not P0B.

## CORE LAW
Preference requests intent · Router decides execution · Receipt records reality · Fallback is never silent ·
LLM output is never truth · Agent output is never truth · Tool output is never truth · Baltor governs truth ·
Teleon runs capabilities · CapabilityTask stays stable, implementation evolves, evidence decides, policy gates
promotion, humans approve boundary expansion. OpenHubForAI = registries, not truth authorities (discovery≠trust).

## NON-NEGOTIABLE GUARDRAILS
No commit/push/pip/npm-dep-mutation/real-containers/real-or-paid-cloud/paid-providers/production-secrets.
No network LLM or live third-party diagnostics unless owner authorizes. No named-company outreach. No broad
pkill (kill the KNOWN watchdog pid in `.agent/flywheel-watchdog.pid` directly — pgrep matches its own shell).
No raw API keys in configs/logs/UI/receipts/HTML/screenshots. No direct provider SDK calls from product logic.
No second LLM wrapper / event bus / durable ledger / worker framework. No dashboard-writes-truth, LLM-output-
becomes-truth, agent-output-becomes-truth, benchmark-promotes-candidate, skill/tool-output-becomes-truth.
No production keys inside OpenClaw/Hermes/ClawLess/browser-runtime/WebContainer/sandbox workspace. No
shared-key/unlimited/bypass/reverse-engineered endpoints. Missing provider/SDK/key/runtime/cloud/container/
authorization → build a local equivalent + candidate metadata + Provider/AgentProviderUnavailableResult +
prove graceful degradation + record blocker + continue. Stop ONLY on `.agent/STOP_REQUESTED`.

## EACH CYCLE (interval 1200s)
1. Verify reality (read state below). 2. Repair sweep (JSON parse + py_compile + regressions + flywheel --once).
3. Select highest-priority INCOMPLETE target. 4. Build ONE proof-backed increment. 5. Run its exact proof.
6. Run regressions. 7. Register new proof in `scripts/flywheel_proof_modules.py`. 8. Restart watchdog by EXACT
pid (`.agent/flywheel-watchdog.pid`) ONLY if PROOF_MODULES changed. 9. Write receipt. 10. ScheduleWakeup 1200s
with this same command. A previously-completed proof does NOT count as this cycle's increment.

Read each cycle: `.agent/{north-star-loop-state,hardcore-loop-state,blocker-ledger,decision-ledger,proof-ledger,
next-action,STOP_REQUESTED}.json|md`, `.agent/baltor-goal-loop-log.md`, `scripts/flywheel_proof_modules.py`,
`architecture/{contract_registry,model_provider_graph,free_limited_llm_endpoint_registry,agent_runtime_catalog,
runtime_ownership,company_product_boundaries}.json`.

## TARGET LADDER (skip VERIFIED_DONE; never stop on a done item — advance)
- P0A repair any active failing proof/regression.
- P0B–P0E **VERIFIED_DONE** (inference gateway/OIPS/receipts/free-endpoint policy/redteam exist under `inference`
  naming) — only EXTEND (e.g. an explicit `/api/llm/route` alias + LLMRouteRequest/Response thin shells over
  InferenceRequest IF a caller needs the `llm` vocabulary). Do not rebuild.
- **P1F (next): `scripts/check_agent_runtime_layer_redteam.py`** — shared `find_violations(catalog, outcomes)`
  reused by a CONTROL (real catalog/dispatch clean) + attacks that MUST be caught: candidate card serves_truth=true;
  open-ended agent forced onto a generic cloud function w/o allow_generic_functions+proof; raw API key in a card;
  module imports src.baltor; unknown runtime crashes instead of structured-unavailable; candidate claims
  imported/executed=true.
- **P1A: `schemas/agents/{AgentHarnessProfile,AgentRunRequest,AgentRunResult,AgentRunReceipt,AgentToolPolicy,
  AgentSkillPolicy,AgentSandboxPolicy,AgentMemoryPolicy,AgentProviderNode,AgentProviderUnavailableResult,
  AgentBoundaryApprovalRequest}.v1`** + register in `architecture/contract_registry.json` + check_agentic_bot_contracts.
- **P1D: local agent stubs** (agent.local_echo@v1 / local_structured@v1 / local_skill_loader@v1) writing
  AgentRunReceipt — deterministic/offline/stdlib; the active golden path + fallback when OpenClaw/Hermes absent.
- **P1B/P1C: OpenClaw + Hermes candidate ADAPTERS** (`src/teleon/agents/providers/{openclaw,hermes}_candidate.py`):
  validate request/tool/skill/sandbox/memory policy; AgentProviderUnavailableResult when not installed; no install,
  no live run unless authorized, no raw keys, no host exec by default. OpenClaw: skills=instruction files (not
  authority), tools need allowlist, sandbox required for tool exec, env/key = secret_ref, tool output = evidence.
  Hermes: skills = on-demand progressive-disclosure docs; agent-created skills enter OpenSkillsHub as CANDIDATES
  needing eval before active; memory writes scoped; output not truth.
- **P1E: `/api/agents/{providers,profiles,skills,receipts,health}` (GET projection-only) + run-local/validate-
  request/intake-skill-candidate (POST, local stub only)** + check_agentic_bot_api + _receipts.
- **P1F (redteam, see above) → P2 Teleon PurposeTasks (purpose.llm_route / agentic_bot_run / *_skill_intake /
  provider_health_check / agent_profile_validate) → P3 Baltor boundary (outputs = evidence/candidate only,
  never CanonicalFact/served-ContextResponse/source-authority/promotion-authority) → P4 /ai-plane dashboard
  projection → P5 docs + check_shared_llm_agentic_bot_full_stack.**

## PROOFS / RECEIPT
New code → a deterministic offline `--self-test` proof (exit 0/1, inject `now`, no wall-clock/RNG). Register in
PROOF_MODULES. Regressions each cycle: `PYTHONPATH=. python3 scripts/{demo_offline_full_baltor,
check_baltor_full_stack_perfect,check_no_direct_provider_bypass}.py --self-test` + `scripts/baltor_flywheel.py
--once`. Receipt → `.agent/baltor-goal-loop-log.md` (target/why/increment/proofs/flywheel/watchdog/blockers/
honest-gaps/next-target); refresh `.agent/{north-star-loop-state,hardcore-loop-state,next-action}.json`. Then
ScheduleWakeup 1200s with `/loop 1200 /shared-llm-plane-and-agentic-bot-implementation`. Honor hard STOP.
