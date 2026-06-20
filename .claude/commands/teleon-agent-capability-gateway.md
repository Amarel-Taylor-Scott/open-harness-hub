---
description: Backend loop — build Teleon as the deterministic capability layer for AI AGENTS (agents are customers): stable receipt-backed CapabilityTasks they call instead of burning tokens. One proof-backed increment per cycle.
---

YOU ARE RUNNING THE TELEON AGENT CAPABILITY GATEWAY LOOP. Position + implement Teleon as a capability layer for AI
agents: agents call stable, governed, DETERMINISTIC CapabilityTasks instead of burning frontier tokens re-solving
repeatable workflows. **MCP connects agents to tools; Teleon turns tools into governed capabilities. Agents ASK,
Teleon EXECUTES, Baltor GOVERNS truth.** One NEW proof-backed increment per cycle unless `.agent/STOP_REQUESTED`.

## POSITIONING / LAW
- Teleon is NOT a chatbot, NOT a truth authority. Agents cannot self-expand purpose/secrets/domains, promote
  candidates, weaken success criteria, or decide truth. Agent/LLM output is NEVER truth.
- Token-saving ladder (deterministic-first; jump to LLM only if policy allows): cached verified → deterministic
  parser → direct API → local calc → local small model → browser worker → specialized provider → frontier LLM →
  human review. Expose ~5 STABLE tools (list/describe/quote/run/get_receipt/request_boundary_expansion), NOT 300.
- Return a COMPACT receipt-backed result (answer+status+source_handles+held_out+receipt_id+fallback_used+
  tokens_saved_estimate), never the full raw corpus/tool-logs/reasoning chain. Boundary expansion = human-approved
  (BoundaryExpansionRequest stays pending, never auto-applied). Pricing metric = cost per successful capability run.

## VERIFIED FOUNDATIONS (reuse; re-verify each cycle)
- src/teleon/runtime/capability_binding.py (CapabilityTaskBindingProvider: local_function@v1 active; cloud/K8s by
  policy via execution_backend_selector) + check_capability_binding_provider.
- src/teleon/agents/agent_runtime_provider.py (+ redteam), src/teleon/inference/* (token ladder / OIPS / receipts),
  src/teleon/environments/baltor_cfpb_context_governance.py (the compact governed-result shape: "10 business days"
  + held-out "30 days" + source handle + receipt). schemas/agents/* (P1A run contracts). flywheel ~396+.

## TARGET LADDER (first incomplete; mark VERIFIED_DONE + advance)
- P0 contracts: schemas/agents/{AgentCapabilityConsumer,AgentCapabilityCard,AgentCapabilityRunRequest,
  AgentCapabilityRunResult,AgentCapabilityReceipt,AgentBoundaryExpansionRequest}.v1 + register in contract_registry +
  check_teleon_agent_gateway_contracts. (AgentCapabilityCard: capability_id,purpose,input_contract,output_contract,
  allowed_use,forbidden_use,expected_cost,expected_latency,freshness_policy,policy_notes,deterministic_first,
  llm_fallback_allowed,receipt_required.)
- P1 local gateway: src/teleon/agent_gateway/ — list/describe/quote/run local DETERMINISTIC capabilities
  (utility.hash, cfpb.deadline.verify [reuse the CFPB env], json.schema.validate, tariff.hs.classify.reference,
  source.fetch.official[stub], context.pack.optimize, document.atomic_facts.extract) returning a compact
  AgentCapabilityRunResult + AgentCapabilityReceipt; deterministic-first; LLM fallback gated (NOT used in self-test);
  no raw secrets. HTTP /api/agent/{capabilities,capabilities/<id>,capabilities/<id>/quote,capabilities/<id>/run,
  runs/<id>,receipts/<id>,boundary-expansion-request}. check_teleon_agent_gateway_local.
- P2 MCP projection: a local stub Teleon MCP server projecting the gateway as 5 tools (teleon_list_capabilities/
  describe/run/get_receipt/request_boundary_expansion) — projection-only, no live MCP install, no external exec.
  check_teleon_agent_gateway_mcp_projection.
- P3 runtime: capability run delegates to capability_binding_provider + execution_backend_selector (deterministic
  local first; browser/LLM/provider candidate only if policy allows; every run writes a receipt).
- P4 Baltor boundary: context capabilities return EVIDENCE/candidate; Baltor governs verified/served truth; held-out
  separate; source handles preserved. check_teleon_agent_gateway_baltor_boundary.
- P5 redteam: check_teleon_agent_gateway_redteam — agent sees raw secret / calls forbidden tool / expands purpose /
  weakens success criteria / bypasses Baltor truth gate / triggers LLM fallback when policy disallows / gets full raw
  context instead of compact receipt / uses benchmark score as truth / MCP exposes dangerous public exec. All fail safely.
- P6 full stack: check_teleon_agent_gateway_full_stack + regressions.

## GUARDRAILS / CADENCE
stdlib-only deterministic offline proofs (exit 0/1, inject now); NO install/Docker/live-LLM/keys/cloud/commit/push;
Teleon never imports Baltor; candidate≠active; benchmark=evidence-not-authority; no 2nd ledger/bus/wrapper/framework;
assemble any fake test key from fragments. Register new proofs in PROOF_MODULES → restart watchdog by EXACT pid
(.agent/flywheel-watchdog.pid, never pgrep) → flywheel green. Receipt + refresh state. ScheduleWakeup 1200s with
`/loop 1200 /teleon-agent-capability-gateway`. Owner authorized agents/sub-tasks → fan out disjoint-file subagents,
serialize PROOF_MODULES+flywheel+watchdog in the main loop. Stop ONLY on .agent/STOP_REQUESTED.
