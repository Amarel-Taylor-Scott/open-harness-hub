# GLOBAL context (generated from live code @ cd92dca9)

Computed inventory — not hand-typed, so it never drifts:

- python modules (src/+scripts/): 1755
- architecture/*.json registries: 198
- scripts/check_*.py proof gates: 586

Dependency law: Baltor depends on Teleon; Teleon may consume OpenHubForAI artifacts; OpenHubForAI depends on neither. Teleon must NEVER import Baltor (it is reusable infrastructure, not a Baltor feature). OpenHubForAI must import neither (the open ecosystem/spec stays neutral).

Descent axes (the dimensions a capability is bounded along): determinism(higher), cost(lower), latency(lower), llm_usage(lower), tokens_in(lower), tokens_out(lower), freshness(higher), verifiability(higher), reliability(higher), locality(higher), specialization(higher), privacy(higher), reproducibility(higher), portability(higher), resilience(higher), energy(lower), safety(higher)

Storage tiers: config: local=json_file/cloud=json_file; operational: local=sqlite_wal/cloud=postgres; history: local=sqlite_wal/cloud=warehouse


Surface map (each surface's WEDGE + how it COMMUNICATES — architecture/surface_map.json):
  ai-done-right [live] — Parent / holding brand — owns no runtime and no customer data; the PROMISE across the family (Context · Capability · Proof). An umbrella ove
  baltor [live] — Fully MANAGED, governed context — company-wide / department-wide / initiative-wide. Verified, Current, Provable. 'Models don't fail. Their c  ->> teleon (consumes (tenant)); sources (ingests)
  teleon [live] — Its OWN product (not just Baltor's runtime): program a capability in PLAIN TEXT and Teleon makes it ADAPT to the most EFFICIENT + BOUNDED fo  ->> openhubforai (consumes); registries (selects-from); baltor (serves); agents (serves)
  openhubforai [live] — The open STORE + the open CapabilityTask spec (CTS): a shared catalog of reusable components — context, tools, models, steps, DAG components  ->> (none) (imports-neither)
  open-star-hubs [mixed (9 live + 13 private)] — The STORE, by category — each OpenHubForAI hub registers reusable components BOTH Baltor and Teleon consume: models, context, compression, s  ->> teleon (feeds-substrate)
  teleon-demos [live] — The proof surface — every descent demo with its MEASURED saving vs the expensive default (extraction 47-91%, enrichment 86%), governed (serv  ->> teleon (reads)
  design-bundle [live] — The high-fidelity design/brand handoff bundle (24+ surfaces, 22 hubs) for Claude Code Max — the single source for the portfolio's UI.  ->> ai-done-right (renders)

Registry inventory (the SELECTION SUBSTRATE the runtime descends against):
  access_policy.json: 8 rows
  acquisition_strategies.json: 10 rows
  adapter_layers.json: 14 rows
  adjacent_verticals.json: 10 rows
  agent_environment_research_registry.json: 11 rows
  agent_frameworks_registry.json: 10 rows
  agent_runtime_catalog.json: 6 rows
  agentic_loop_catalog.json: 15 rows
  behavioral_heuristics.json: 30 rows
  benchmark_family_codes.json: 17 rows
  blackboard_provider_catalog.json: 6 rows
  brand.json: 8 rows
  browser_escalation_ladder.json: 8 rows
  candidate_open_hubs.json: 20 rows
  capability_adaptation_ladder.json: 9 rows
  capability_binding_landscape.json: 12 rows
  capability_implementation_registry.json: 9 rows
  capability_ladders.json: 17 rows
  capability_rubric_assessment.json: 5 rows
  capability_runtime_classes.json: 14 rows
  capability_synthesis_pipeline.json: 5 rows
  capability_taxonomy.json: 6 rows
  company_portfolio_map.json: 6 rows
  competitive_provider_mappings.json: 9 rows
  configuration_standards.json: 14 rows
  context_compression_provider_catalog.json: 2 rows
  context_engineering_patterns.json: 4 rows
  context_engineering_tool_catalog.json: 20 rows
  contract_registry.json: 177 rows
  credential_registry.json: 25 rows
  dag_templates.json: 6 rows
  default_brain_policy.json: 3 rows
  demo_surface_registry.json: 21 rows
  deploy_topology.json: 16 rows
  descent_method_catalog.json: 17 rows
  descent_strategy_registry.json: 12 rows
  discovery_pipeline.json: 4 rows
  domain_brand_risk_register.json: 4 rows
  e2e_persona_journey_registry.json: 10 rows
  egress_route_policy_taxonomy.json: 7 rows

## Thesis (from CLAUDE.md head)
# CLAUDE.md - AI Done Right Agent Instructions

> **READ `docs/BIBLE.md` FIRST** — the single north-star reference (vision · the 5 pillars · the ~35 OpenHubForAI surfaces
> + 103 registries · assumptions · guardrails · laws · contracts · hooks · tools). This file (CLAUDE.md) is the agent
> operating layer; the BIBLE is the canonical *what + why*. If they ever disagree, the BIBLE wins.

This file is for Claude Code, Claude desktop/browser agents, and any Claude 4.x/4.8/4.7-style workflow that opens this repository. Follow `AGENTS.md` first; this file adds speed and organization rules for scaling OpenHubForAI.

## Portfolio (owner-decided 2026-06-06; updated 2026-06-09 — read FIRST)

Current parent display brand: **AI Done Right** (`aidoneright.dev`), tagline
**"AI, done right."** The prior ContextIsEverything language is preserved as
founding thesis and legacy path context, not as the parent display brand. The
high-fidelity Claude Code Max handoff lives in
`dist/sites/aidoneright-design/`: start with `START-HERE-CLAUDE-CODE.md`, then
`README.md`, `CLAUDE-CODE.md`, and `HANDOFF.md`.

Current design-family snapshot: parent + **Baltor** + **Teleon** + **22
OpenHubForAI registries** (9 live open registries + 13 private-bench registries; the count is
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
`docs/strategy/teleon-baltor-openhubforai-portfolio.md`.

## Surfaces: serve the BUILT-OUT apps, never a basic replacement (read before touching any web surface)

The 5 product surfaces are the full apps in `web/{context-is-everything (AI Done Right), teleon, baltor,
openhubforai (OpenHubForAI), aidevobserver}`, served by the **showcase** (`OH_PRODUCT=<brand> python3 -m
scripts.showcase --port N` → `WEB_DIR=web/<OH_PRODUCT>`) over the shared kit (`web/<app>/kit/`), wired to the
service-plane backends through same-origin **seams** (`/api/identity/`, `/registry/`, `/api/teleon/`,
`/api/observer/`, …). Design system: `docs/DESIGN-BIBLE.md`. Frontend↔backend + local/cloud: `docs/INTEGRATION-BIBLE.md`.
Full contract: `docs/codex/surface-and-development-contract.md`.

- **NEVER build a new basic/skinny replacement server for a surface.** Serving a hand-built rich app with a static
  stub (no backend) is the recurring failure mode — `scripts/surface_server.py` (f
