# /workflows /portfolio-add-openbenchmarkhub

> **STATUS (2026-06-07).** BOUNDARY LOCKED: OpenBenchmarkHub.io added to the canonical portfolio map
> (`architecture/company_portfolio_map.json`, port 9504, domain proposed/unverified) + the open-hubs bridge graph
> (`open_hubs_bridge_graph.json`: artifact_owner BenchmarkArtifact→openbenchmarkhub; edge `BenchmarkArtifact RUN_BY
> HarnessArtifact`; `benchmark_result_cannot_promote: true`), guarded by the two updated portfolio proofs. Doc:
> `docs/benchmarks/benchmark-vs-harness.md`. The CONTRACTS/REGISTRY/WEBSITE/API/RUBRICS below are QUEUED.

You are Claude Code running the OPEN BENCHMARK HUB PORTFOLIO SPLIT workflow.

**Goal:** add OpenBenchmarkHub.io as a distinct open hub for benchmark definitions, cards, metric definitions,
datasets/tasks, result records, leaderboards, suitability reports, contamination/risk, and benchmark→capability
maps. **OpenBenchmarkHub is not OpenHarnessHub** — it defines WHAT to measure + records results; OpenHarnessHub
provides the runners/harnesses/rubrics/fixtures/conformance that EXECUTE them.

**Do not:** merge the two hubs · make OpenBenchmarkHub a runtime · treat a benchmark result as truth or as
production performance · let a benchmark result alone promote a Teleon/Baltor candidate · duplicate the eval
harness registry OpenHarnessHub already owns.

**Core rule:** A benchmark is EVIDENCE, not authority. Promotion requires policy gates + task-specific harnesses +
source handles + receipts + production-relevant scorecards + redteam.

1. **Discovery** → `.agent/openbenchmarkhub-discovery.json` (reuse: schemas/experiments/* PathComparison/Promotion,
   scripts/eval/*, the CFPB demo as the first benchmark fixture; the existing promotion-decision contract).
2. **Boundary** — DONE in the map/bridge graph. (companies/openBenchmarkHub/*.md docs still QUEUED.)
3. **Contracts (QUEUED):** `schemas/benchmarks/{BenchmarkArtifact,BenchmarkCard,BenchmarkDatasetRef,BenchmarkTaskRef,
   BenchmarkMetric,BenchmarkResult,BenchmarkRunRef,BenchmarkLeaderboard,BenchmarkSuitabilityReport,BenchmarkRiskReport,
   BenchmarkContaminationReport,BenchmarkToCapabilityMap}.v1`. BenchmarkArtifact required: benchmark_id,
   display_name, benchmark_family, capability_slots, input_contracts, output_contracts, metrics, datasets,
   harnesses, known_limitations, contamination_risk, suitability_notes, visibility, owner, status_code.
4. **Registry (QUEUED):** `architecture/{open_benchmark_registry,benchmark_metric_registry,benchmark_family_codes,
   benchmark_capability_map,benchmark_result_registry,benchmark_suitability_policy}.json`. Families: model_general/
   coding/reasoning, agent_tool_use, agent_memory, software_engineering, context_governance, rag_grounding,
   compression_fidelity, mcp_conformance, tool_safety, skill_effectiveness, runtime_selection, sandbox_security,
   chatbot_guardrail, regulated_context, domain_specific. Seed external refs as owner_provided_unverified: SWE-bench
   (+Verified), AgentBench, HELM, OpenCompass, lm-evaluation-harness, LiveBench, Open LLM Leaderboard, STATE-Bench.
5. **First first-party benchmarks (QUEUED):** `benchmark.baltor.cfpb_context_governance@v1` (metrics:
   answer_correctness, source_handle_coverage, held_out_leak_count, receipt_presence, allegation_leak_count,
   tenant_leak_count; expected: 10 business days; FAQ 30 held out; handles+receipts present; allegations not served),
   `benchmark.teleon.capabilitytask_runtime_selection@v1`, `benchmark.opencompression.fidelity@v1`,
   `benchmark.openmcp.conformance@v1`.
6–11. **Website / bridge edges (done) / API projections / rubrics / redteam / docs (QUEUED).** Hero: "The benchmark
   intelligence layer for AI systems." Redteam must fail: benchmark result promotes a candidate directly · result
   treated as Baltor truth · leaderboard overclaims production readiness · benchmark lacks limitations/metrics ·
   contamination ignored · private benchmark result public · OpenBenchmarkHub claims to run harnesses · model
   leaderboard score used for regulated context without a domain benchmark.
12. **Proofs (QUEUED):** check_openbenchmarkhub_{contracts,registry,examples,website,bridge_graph,api,rubrics,
   redteam,full_stack}. Regression: demo_offline_full_baltor, check_no_direct_provider_bypass, baltor_flywheel --once.

## OPENBENCHMARKHUB CLAUSE
OpenBenchmarkHub.io is a distinct hub for benchmark definitions/cards/metrics/datasets/results/leaderboards/
suitability/contamination. OpenHarnessHub.io owns the harnesses/runners that execute benchmarks. Benchmarks are
evidence, not authority; a benchmark result cannot directly promote a Teleon candidate or become Baltor truth.
Promotion still requires policy gates, receipts, source handles, task-specific scorecards, and redteam.
