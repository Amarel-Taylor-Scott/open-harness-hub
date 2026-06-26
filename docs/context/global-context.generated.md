# GLOBAL context (generated from live code @ 26a287dc)

Computed inventory — not hand-typed, so it never drifts:

- python modules (src/+scripts/): 1441
- architecture/*.json registries: 127
- scripts/check_*.py proof gates: 472

Dependency law: Baltor depends on Teleon; Teleon may consume OpenHarnessHub artifacts; OpenHarnessHub depends on neither. Teleon must NEVER import Baltor (it is reusable infrastructure, not a Baltor feature). OpenHarnessHub must import neither (the open ecosystem/spec stays neutral).

Descent axes (the dimensions a capability is bounded along): determinism(higher), cost(lower), latency(lower), llm_usage(lower), tokens_in(lower), tokens_out(lower), freshness(higher), verifiability(higher), reliability(higher), locality(higher), specialization(higher), privacy(higher), reproducibility(higher), portability(higher), resilience(higher), energy(lower), safety(higher)

Storage tiers: config: local=json_file/cloud=json_file; operational: local=sqlite_wal/cloud=postgres; history: local=sqlite_wal/cloud=warehouse

Registry inventory (the SELECTION SUBSTRATE the runtime descends against):
  agent_environment_research_registry.json: 11 rows
  agent_runtime_catalog.json: 6 rows
  benchmark_family_codes.json: 17 rows
  blackboard_provider_catalog.json: 6 rows
  brand.json: 8 rows
  candidate_open_hubs.json: 10 rows
  capability_adaptation_ladder.json: 9 rows
  capability_binding_landscape.json: 12 rows
  capability_implementation_registry.json: 9 rows
  capability_rubric_assessment.json: 5 rows
  capability_runtime_classes.json: 14 rows
  company_portfolio_map.json: 6 rows
  competitive_provider_mappings.json: 9 rows
  configuration_standards.json: 14 rows
  context_compression_provider_catalog.json: 2 rows
  context_engineering_patterns.json: 4 rows
  context_engineering_tool_catalog.json: 20 rows
  contract_registry.json: 177 rows
  default_brain_policy.json: 3 rows
  demo_surface_registry.json: 21 rows
  deploy_topology.json: 16 rows
  descent_method_catalog.json: 17 rows
  descent_strategy_registry.json: 12 rows
  domain_brand_risk_register.json: 4 rows
  e2e_persona_journey_registry.json: 10 rows
  egress_route_policy_taxonomy.json: 7 rows
  execution_backend_policy_matrix.json: 14 rows
  execution_environment_profiles.json: 14 rows
  external_capability_catalog.json: 30 rows
  file_layout_policy.json: 42 rows
  fragile_context_atlas.json: 25 rows
  fragile_context_taxonomy.json: 22 rows
  framework_integration_matrix.json: 6 rows
  free_endpoint_class_codes.json: 10 rows
  free_limited_llm_endpoint_policy.json: 13 rows
  free_limited_llm_endpoint_registry.json: 12 rows
  fundamental_primitives_taxonomy.json: 18 rows
  gateway_repo_watchlist.json: 6 rows
  git_platform_operation_map.json: 10 rows
  identity_realm_registry.json: 25 rows

## Thesis (from CLAUDE.md head)
# CLAUDE.md - OpenHubForAI Agent Instructions

This file is for Claude Code, Claude desktop/browser agents, and any Claude 4.x/4.8/4.7-style workflow that opens this repository. Follow `AGENTS.md` first; this file adds speed and organization rules for scaling OpenHubForAI.

## Portfolio (owner-decided 2026-06-06; updated 2026-06-09 — read FIRST)

Current parent display brand: **AI Done Right** (`aidoneright.dev`), tagline
**"AI, done right."** The prior ContextIsEverything language is preserved as
founding thesis and legacy path context, not as the parent display brand. The
high-fidelity Claude Code Max handoff lives in
`dist/sites/openharness-design/`: start with `START-HERE-CLAUDE-CODE.md`, then
`README.md`, `CLAUDE-CODE.md`, and `HANDOFF.md`.

Current design-family snapshot: parent + **Baltor** + **Teleon** + **22
Open*Hubs** (9 live open registries + 13 private-bench registries; the count is
computed by the family check, never hand-counted — don't trust this prose over
`scripts/check_ai_done_right_surface_family.py`). The private bench includes the
complete Baltor method spine (OpenReconciliationHub, OpenHardeningHub,
OpenEnrichmentHub, OpenOptimizationHub, OpenVerificationHub) and
OpenRoutingHub (model-routing policy; owner-proposed 2026-06-09). The owner-directed Codex loop for
this family is `docs/codex/ai-done-right-family-polish-goal.md`. The
parser-safe `/goal` entrypoint is
`/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md`.
Run `python3 scripts/check_ai_done_right_surface_family.py --self-test` before
trusting or editing family-surface counts. Run
`python3 scripts/check_handoff_docs_freshness.py --self-test` before handing the
bundle to another agent.

Service-to-service auth is an active architecture track. Read
`docs/architecture/service-auth-and-consumption-model.md` before implementing
API keys, service accounts, delegated calls, private-bench enforcement, or
cross-service consumption. For local testing without paid cloud, read
`docs/architecture/local-dev-tunnels-and-auth.md` and run
`python3 scripts/check_local_dev_tunnel_auth_runtime.py --self-test`.

Canonical portfolio architecture remains:
`docs/strategy/teleon-baltor-openharnesshub-portfolio.md`.

A holding company owns three product layers. **Teleon** (`teleon.dev`, domain owned) = the purpose-driven,
eval-gated, self-adaptive compute **runtime SaaS** — it owns PurposeTask/CapabilityTask, runtime selection,
evidence ledger, promotion/policy gates, boundary approvals, adapters, the assurance dashboard. **Baltor**
(`baltor.ai`) = the applied, customer-facing context product, **powered by Teleon** (a tenant). **OpenHarnessHub**
= the open ecosystem (evals/harnesses/templates/skills) + the **open CapabilityTask spec (CTS)**.

- **Architectural law (enforced by `scripts/check_portfolio_dependency_law.py` over
  `architecture/portfolio_dependency_law.json`):** Baltor → Teleon → OpenHarnessHub, **never the reverse**.
  Teleon must never import Baltor; OpenHarnessHub imports neither. PurposeTask is **Teleon**, not a Baltor
  subsystem — generic runtime code is being extracted `src/baltor/` → `src/teleon/` incrementally (lossless;
  see the law file's `migration_status`).
- **Naming:** product = **Teleon**; staff dashboard = **Teleon Control Tower**; customer dashboard =
  **Capability Assurance Portal**; object = **PurposeTask** (formal/spec synonym **CapabilityTask**). Brand
  doc: `docs/strategy/teleon-naming-and-domain.md`. ("Purpose R
