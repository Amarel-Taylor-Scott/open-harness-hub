# Next Implementation Plan

- **OPP-api-serve** (api_runtime, M, risk medium) — Expose POST /api/context/serve returning ContextResponse.v1. Done when: POST /api/context/serve returns schema-valid ContextResponse.v1
- **OPP-worker-consume** (workers, M, risk medium) — Durable context.consume command through ConsumptionService. Done when: enqueue context.consume → worker drains → ContextResponse written
- **OPP-teleon-agent-capability-gateway** (teleon_agent_gateway, L, risk low) — Teleon Agent Capability Gateway — serve AI agents as customers: stable deterministic receipt-backed CapabilityTasks instead of token-burning re-reasoning. Done when: AgentCapabilityCard + run contracts exist + proven

Then P1:
- **OPP-consume-ui** (ui_pages, M, risk low) — web/baltor/consume.html ingestion→consumption page. Done when: /consume renders all panels
- **OPP-watchtower-min** (fragile_fact_watchtower, L, risk medium) — Fragile Fact Watchtower minimum slice feeding the gate real freshness. Done when: Reg E fact carries FragilityMetadata
- **OPP-vector-graph-lineage** (context_response, M, risk low) — Wire vector + deterministic graph ids into served-fact lineage. Done when: served fact has a deterministic vector id
- **OPP-admin-monolith-split** (api_runtime, L, risk medium) — Split the admin server monolith into src/baltor/api routes. Done when: ≥1 route extracted to src/baltor/api/routes
- **OPP-per-section-docs** (docs, L, risk low) — Per-section docs completion to the documentation standard. Done when: every section has a doc with required headings
- **OPP-optimizer-classes** (optimization_suite, L, risk low) — C44/C45/C46 optimizer classes (retrieval, LLM/router, worker throughput). Done when: each new optimizer behind the Optimizer contract
- **OPP-multi-source-consumption** (multi_source_consumption, M, risk low) — Generic source_type->consumption for all source types. Done when: every cataloged source_type reaches a ContextResponse or an explicit non_consumable_reason
- **OPP-pattern-factory-m10** (pattern_standards_factory, L, risk low) — Take the Pattern & Standards Factory from M6 to M10. Done when: add template_ids so candidate_templates trends to 0
- **OPP-wire-standards-monolith** (standards_api, S, risk low) — Standards monolith wiring DONE — remaining: candidate templates + enforcement. Done when: (done) GET /standards + /api/standards/* served + hub-linked
- **OPP-wire-memory-monolith** (memory_ui, S, risk low) — Memory monolith wiring DONE — remaining: capability-catalog slots. Done when: (done) GET /memory + /api/memory/* HTTP 200
- **OPP-pipeline-pages** (pipeline_pages, S, risk low) — Pipeline pages live — remaining: interactive Run action. Done when: (done) /pipeline + stages + /api/pipeline/* HTTP 200
- **OPP-contextops-runtime** (contextops, L, risk low) — ContextOps runtime: cost-ladder + CFPB reference + generated-worker execution + scheduler + API/UI. Done when: CFPB reference runs end-to-end through ContextOps (agents propose, Baltor disposes; reproduces '10 business days')
- **OPP-worker-fleet-surface** (worker_fleet_supervisor, L, risk low) — Worker fleet: persistent ledger on live dispatch + /fleet API/UI + metrics + KEDA wakeup + K8s templates. Done when: ledger persisted (SQLite) + two-process exactly-once claim proven
- **OPP-fleet-lifecycle-surface** (worker_lifecycle_telemetry, L, risk low) — Fleet lifecycle/telemetry: /fleet API+UI, wire spawn_decision on live dispatch, auto-apply recommendations, real breaker metrics. Done when: /fleet API/UI live (projection-only over telemetry)
- **OPP-supervisor-scaling-live** (flywheel_supervisor_scaling, L, risk low) — Supervisor scaling on the live path: persist coordination tables + wire leader/shard managers into the watch loop + multi-process failover harness. Done when: coordination tables persisted + CAS-safe across processes
- **OPP-fleet-driven-pipeline-surface** (fleet_driven_pipeline, M, risk low) — Fleet-driven pipeline: /dashboard 'Run via Fleet' button + durable FleetLedger on live dispatch + parallel stage workers. Done when: /dashboard 'Run via Fleet' button triggers the route + events stream live
- **OPP-shared-agent-runtime-layer** (teleon_agent_runtime, M, risk low) — Shared AI-agent runtime layer (Teleon): receive bounded agent request -> provision K8s/sandbox/cloud-function backend; ClawLess/OpenClaw + Hermes as candidate adapters. Done when: check_agent_runtime_layer_redteam green (control clean + every attack caught)
- **OPP-eval-env-synthesis** (eval_env_synthesis, M, risk low) — Repo->verifiable-RL-env synthesis (Repo2RLEnv / R2E-Gym / SWE-Gym) as CANDIDATE eval/training-data generators behind a Harbor-format harness-intake port. Done when: Repo2RLEnv/R2E-Gym/SWE-Gym registered as eval_env_synthesis candidates (metadata-only; license + Docker/LLM gates flagged)
