# /workflows /baltor-long-running-strategy-research-self-evolution-loop

You are Claude Code running the **BALTOR STRATEGY + RESEARCH + SELF-EVOLVING PARALLEL-PATH LOOP**.

Long-running. NOT a one-pass feature build · NOT a strategy memo · NOT planning-only · NOT research-only · NOT
code-only · NOT pitch-deck-only · NOT "flywheel green, stop." Continuously improve Baltor across five linked
dimensions while keeping the working system green: **1 product strategy · 2 startup/YC strategy · 3 competitive
research · 4 architecture strategy · 5 self-evolving parallel-path implementation.**

> **Build discipline (recorded lesson):** ship focused, proven increments (Agent subagents / direct edits),
> NOT a single multi-phase Workflow (it stalls on its last agent). Each lane/section below lands + proves green
> on its own; the flywheel stays green throughout. Honor every locked principle: numeric-config + wrapped
> redundancy ([[numeric-config-and-wrapped-redundancy]]), no-magic-values, Lossless Distillation, no-truth-
> bypass, cloud-agnostic execution, local-emulators-first, change-verification warrant.

## CORE PRINCIPLE — never replace a working path on faith
Do NOT replace a working path until the alternative has PROVEN: same-or-better correctness · governance ·
source-handle preservation · tenant safety · reliability · same-or-lower (or justified) cost · a *measurable*
improvement · rollback available · **original path preserved as fallback**. Originals remain alternatives; new
paths run **side-by-side first**; promotion requires **evidence**, not a claim. Agents PROPOSE; Baltor DISPOSES.

## 0. Preserve the current foundation
Offline demo green · CFPB invariant ("10 business days" served; FAQ-30 + allegations held out; only the
verified winner served; lineage + receipt) · DurableFleetLedger · live supervisor/flywheel · worker taxonomy ·
execution-backend flexibility (cloud-agnostic, local-emulators-first) · architecture guardrails · provider
replacement/candidate catalog + numeric preference graph · optimization suite + promotion gates · no direct
provider bypass · no dashboard/memory/LLM/browser truth · no candidate promoted without proof. **Do NOT create a
second** runtime / worker framework / durable ledger / artifact ledger / LLM gateway / provider registry /
memory authority / strategy system. **Extend + consolidate.**

## 1. North Star
Baltor is the **governed context-operations layer for AI systems**: ingest native/structured context →
decompose into governed leaves/facts → detect conflicts + fragile facts → verify + reconcile → optimize for
consumption → preserve lineage/sidecars/receipts → serve only safe, verified, current, tenant-scoped context.
Wedge: enhancement · reconciliation · governance · freshness · lossless distillation · source-handle
preservation · deterministic promotion · worker/flywheel orchestration · provider-agnostic execution ·
self-improving cost reduction. **Others retrieve context; Baltor governs context.**

## 2. Loop rules
Do NOT stop on: research/SWOT/competitor/deck written · workflow queued · provider cataloged · cloud dep missing
· integration deferred · emulator exists · flywheel/demo green · "next tick" · watchdog re-armed. **Every cycle
produces ≥1 of:** cited research update · competitor/integration map · architecture decision · strategy/YC
artifact · new proof · improved implementation · parallel-path experiment · cost/reliability measurement ·
promotion/rollback decision · redteam result · consolidation. Blocked by cloud/creds → build local emulator,
catalog the real provider as candidate, prove locally, continue. Candidate fails → keep the original, record
the learning, try another candidate.

## 3. Durable loop state — `.agent/strategy-self-evolution-loop-state.json`
Keys: `current_cycle · active_theme(research|competitor|startup|architecture|parallel_path|cost_reduction|
integration|yc) · current_target · baseline_path · candidate_paths · active_parallel_experiments ·
latest_{research,competitor,architecture,startup,yc}_updates · proofs_green · proofs_red · cost_findings ·
promotion_decisions · rollback_targets · next_command · resume_instructions`. Update every cycle + append
`.agent/baltor-goal-loop-log.md`.

## 4. Baseline FIRST every cycle
`demo_offline_full_baltor --self-test` · `check_baltor_full_stack_perfect` · `check_durable_fleet_ledger` ·
`check_live_supervisor_full_stack` · `check_no_direct_provider_bypass` · `baltor_flywheel.py --once`. Any RED →
fix first (rerun the exact failing proof) or honestly quarantine outside the golden path before strategy work.

## 5. Research lane
Areas: (A) competitors/adjacent — memory/context, GraphRAG/temporal, observability/eval, agent orchestration,
coding/self-evolving agents, data-governance/catalog/lineage, regtech, vector/search, workflow engines,
serverless/K8s; (B) integration candidates — Supermemory · Mem0 · Zep/Graphiti · Letta · Langfuse · Phoenix ·
LangSmith · OpenTelemetry · OpenLineage · OpenFeature · Temporal · DBOS · KEDA · K8s Jobs · Lambda/GCF/Cloud
Run/Azure Functions/Cloudflare Workers · Playwright/Selenium/Browser-Use/Browserbase · Docling/PyMuPDF/
Unstructured/**PaddleOCR** · Qdrant/pgvector/LanceDB/Neo4j · DSPy/Optuna/promptfoo/Ragas/**LLMLingua**/**Headroom**/
MLflow · OpenHands/Open-SWE/Claude Code/Codex/Cline · E2B/Daytona/sandboxes; (C) startup/YC — current YC advice,
AI-agent market language, customer discovery, launch, pricing benchmarks, ICP/pain, enterprise procurement +
compliance/security buyer concerns. Rules: **verify-first** (primary sources: official docs/GitHub/pricing/YC
library/standards), cite, no large copying, separate verified vs assumption, every integration → a capability
slot, every external provider → a local/emulator strategy. Outputs: `docs/research/{current-market-map,
competitor-landscape,integration-candidates,provider-watchlist,standards-and-protocols,startup-advice,
customer-discovery-notes}.md`. Proof `check_research_docs_current` (docs exist + cite + every competitor has a
category + every integration maps to a slot + every external provider has a local/emulator strategy +
assumptions labeled). *(Builds on the existing docs/research/*-landscape.md set — extend, don't duplicate.)*

## 6. Competitor lane — `architecture/competitor_matrix.json` + `docs/strategy/{competitor-analysis,positioning-map}.md`
Per entry: `competitor_id·name·category·core_value·strengths·weaknesses·overlap_with_baltor·baltor_
differentiation·integration_candidate·capability_slots·threat_level·partner_potential·evidence_sources·
last_reviewed_at`. Score each on: retrieves vs **governs** context · reconciles conflicts · preserves native
format + source handles · receipts · fragility/freshness · deterministic promotion · local/offline path ·
tenant isolation · dev-friendly API · **integrate vs compete head-on**. Proof `check_competitor_matrix`.

## 7. SWOT lane — `docs/strategy/swot.md` + `architecture/swot.json`
S: offline demo · source handles/receipts · reconciliation · fragility/freshness · lossless distillation ·
native format · worker/flywheel control plane · provider-agnostic + numeric graph · deterministic promotion ·
local emulators · candidate-integration strategy. W: complexity · too many workflows (→ wrapper-managed
redundancy) · demo/platform ambiguity · over-engineering before customer pull · limited real customer data ·
ICP/pricing clarity · onboarding. O: AI context governance · compliance/regtech · enterprise AI safety ·
tenant-policy reconciliation · regulated-doc ingestion · agent-memory governance · context observability · LLM→
deterministic cost reduction · YC narrative. T: memory/RAG/vector/observability incumbents adding governance ·
cloud bundling · category confusion · long sales cycles · data-security bar · model/provider volatility. Every
item: **evidence · implication · action · owner · metric to monitor.** Proof `check_swot_strategy`.

## 8. Startup-strategy lane — `docs/strategy/{startup-strategy,customer-discovery-plan,icp,pricing-hypotheses,gtm-plan,yc-application-notes,pitch-deck-outline,demo-script}.md`
Discipline: identify ICP · talk to users · launch a simple demo · do things that don't scale · sell before
overbuilding · narrow wedge before broad platform · track customer pull · demos→pilots→roadmap. ICP candidates:
compliance teams using AI · banks/fintech regulatory workflows · insurance compliance · legal/reg ops · AI-agent
teams needing governed context · enterprise copilots · support-QA compliance · risk/compliance data teams. Value
prop variants: governed context layer for regulated AI · reconciliation engine for conflicting knowledge ·
ContextOps (verify/refresh/serve) · native-format sidecars for compliance-grade context · LLM-cost reduction via
deterministic verifiers. Every doc: hypothesis · evidence · risk · interview questions · demo to show · success
metric · next action. Proof `check_startup_strategy_docs`. **Reconcile with the LOCKED brand** (`brand-
architecture.md`: AI Done Right (founding thesis: Context is Everything) · Baltor.ai · Verify/Corpus/Compress · OHH) — never re-open it.

## 9. YC/fundraising lane — `docs/strategy/{yc-one-liner,yc-application-draft,yc-pitch-deck,yc-demo-plan,yc-metrics-plan,investor-faq}.md`
One-liners: governed context layer for AI agents in regulated industries · reconciles+verifies enterprise
context before AI uses it · turns messy knowledge into safe/source-grounded/auditable AI context. Deck:
Problem · Why now · Demo · Product · Differentiation · Market/ICP · Business model · Traction/proof ·
Architecture defensibility · Roadmap · Team · Ask. Investor FAQ: why not RAG/vector/Supermemory-Mem0-Zep/
Langfuse · why can't they build it · why now · who buys first · the wedge · how it scales · pricing · moat ·
risks. **Honesty:** claims limited to what proofs support (assurance brand — overclaiming is fatal). Proof
`check_yc_strategy_artifacts`. *(Consolidate with the existing yc-master doc — don't sprawl.)*

## 10. Architecture-strategy lane — `docs/architecture/{architecture-strategy,flexibility-matrix,parallel-paths-and-promotion,self-evolving-cost-reduction,provider-graph-strategy,cloud-agnostic-execution,local-emulators-first,no-bandaids}.md`
Six planes (source/intake · object/leaf · governance · execution · consumption/export · observability/proof) ·
stable contracts outside / replaceable internals inside · provider GRAPH not string logic · local emulators
before cloud deferral · DB/FleetLedger = truth · cloud-functions/K8s/local/jobs side-by-side · worker buckets +
capability slots · leaf convergence at scale · temporal fact graph · memory/LLM/browser ≠ truth · side-by-side
path comparison · originals preserved as fallback. Proof `check_architecture_strategy_docs`.

## 11. PARALLEL-PATH ENGINE (the technical core — build first, it's the headline)
Generic: for any capability, run baseline + candidate side-by-side on the SAME input snapshot, compare, measure
cost/reliability/quality, promote only when safe. Contracts `schemas/experiments/{PathDefinition,ParallelPathRun,
PathComparisonReport,PathPromotionDecision,PathRollbackPlan,PathCostReport}.v1.schema.json` (register in
contract_registry). `PathDefinition`: path_id·capability_slot·implementation_node_id·input/output_contract·
execution_backend_policy·provider_selection_policy·tenant_scope·enabled·mode(baseline|candidate|shadow|canary|
fallback|deprecated)·promotion_criteria·rollback_target. `ParallelPathRun`: run_id·capability_slot·
input_snapshot_hash·baseline_path_id·candidate_path_ids·outputs·costs·latencies·errors·source_handle_coverage·
contract_validation·safety_validation·created_at. Code `src/baltor/experiments/{parallel_paths,path_comparator,
path_promotion,path_costing}.py`. Rules: SAME input snapshot · output contracts must match · source handles
survive · held-out warnings never leak · candidate cannot serve truth until promoted · baseline stays active
until promotion · rollback target recorded · both outputs preserved. Proofs `check_parallel_path_{contracts,
runner,comparison,promotion_gate,rollback,redteam}`.

## 12. SELF-EVOLVING COST-REDUCTION LOOP (safe)
Flow: identify expensive/fragile path → agent PROPOSES improvement → it becomes a candidate path → runs in
shadow/parallel → compare (correctness · cost · latency · reliability · source-handle coverage · safety · tenant
isolation · deterministic repeatability) → promote ONLY if criteria pass → keep baseline as fallback → record
the learning as a memory/skill/pattern → continue. Contracts `schemas/self_evolution/{PathImprovementProposal,
AgentPathReview,SelfEvolutionRun,CostReductionHypothesis,ImprovementSkill}.v1.schema.json`. Code
`src/baltor/self_evolution/{path_reviewer,improvement_planner,cost_reducer,skill_writer}.py`. Rules: agents
PROPOSE, cannot PROMOTE, cannot remove baseline · generated code runs in sandbox/local emulator · cost reduction
never sacrifices safety · cheaper path must preserve source handles + receipts · all improvements reversible ·
repeated success → a skill/template · failure → learning data. Proofs `check_{agent_path_review,
cost_reduction_hypothesis,self_evolution_parallel_run,self_evolution_promotion_safety,self_evolution_keeps_baseline,
self_evolution_redteam}`.

## 13. First local examples (≥3, deterministic, offline)
A — execution backend: local_subprocess vs local_function_emulator (output equality · claim correctness · cost
estimate · latency). B — compression: none vs compression stub/LLMLingua-emulator (answer-critical facts ·
source handles · token estimate · held-out leakage). C — reconciliation: deterministic authority vs enhanced
comparator/leaf-convergence (CFPB 10-vs-30 outcome · held-out warnings · receipts · cost). Proof
`check_parallel_path_examples`.

## 14. Cost model — `architecture/cost_model.json` + `docs/strategy/cost-model.md`
Dimensions: LLM tokens · model calls · browser/worker startup · CPU/GPU seconds · cloud-function invocations ·
job duration · queue wait · human-review time · provider fees · storage · observability. Local demo = ESTIMATES
(label confidence; relative cost; show deterministic-path savings). Metrics: cost_per_{successful_task,
verified_fact,context_response} · {llm,agent}_calls_avoided · browser_startups_saved · deterministic_cache_hit_
rate · baseline_cost · candidate_cost · savings_percent. Proof `check_cost_model`. Reuse the existing pricebook
config, don't fork it.

## 15. Observability — local now, OTel candidate later
Telemetry per run: path_id·run_id·input_snapshot_hash·output_hash·cost·latency·failure_rate·fallback_count·
source_handle_coverage·redteam_status·promotion_decision·rollback_target. `docs/observability/parallel-path-
observability.md` + `check_parallel_path_observability`.

## 16. API/UI (projection-only)
`/api/strategy/{current-state,competitors,swot,yc,research}` · `/api/experiments/{paths,runs,comparisons,
promotions}` + POST `{run-parallel,promote-candidate,rollback}` (local deterministic tests only). Pages
`/strategy` (thesis · competitor map · SWOT · YC one-liner · ICP · business-model hypotheses · integrations ·
architecture strategy · open risks · next experiments) + `/experiments` (baseline/candidate paths · shadow runs
· comparisons · cost reports · promotions · rollback targets · self-evolution proposals · redteam). Rules:
projection-only unless an explicit local test endpoint · no truth mutation from UI · no candidate promoted
without a gate · no secrets/private memory. Proofs `check_{strategy_api,strategy_ui,experiments_api,experiments_ui}`.

## 17. Redteam — `check_strategy_self_evolution_redteam`
All FAIL safely: agent promotes its own candidate · candidate replaces baseline without proof · cheaper path
drops source handles · serves FAQ-30 · hides held-out warnings · comparison uses different inputs · cost faked
without output equality · competitor research becomes product truth without citation · YC pitch claims
unproven production readiness · UI promotes without gate · failed candidate deletes baseline · self-evolution
writes the main path without rollback.

## 18–20. Docs / Proofs / Acceptance
Create/update the docs in §5–§16. Create+run the proofs in §5–§17 plus `check_strategy_self_evolution_full_stack`,
then REGRESS `demo_offline_full_baltor · check_baltor_full_stack_perfect · check_durable_fleet_ledger ·
check_live_supervisor_full_stack · check_no_direct_provider_bypass · check_worker_bucket_redteam ·
baltor_flywheel.py --once`. **Acceptance:** research/competitor/SWOT/startup/YC/architecture artifacts exist +
cited · parallel-path contracts + runner work · baseline & candidate run on the SAME snapshot · comparison works
· promotion gate blocks unsafe candidates · rollback preserves the original · ≥3 local examples work · cost
model exists · agent path-review PROPOSES but cannot PROMOTE · self-evolution keeps originals as alternatives ·
API/UI exist · redteam fails safely · offline demo + flywheel GREEN.

## 21. Final response format
After running the proofs, report: 1 loop status (GREEN/NOT-GREEN + blockers) · 2 research updates · 3 SWOT ·
4 startup strategy (ICP/wedge/pricing/GTM/YC one-liner) · 5 architecture strategy · 6 parallel-path experiments
(baseline/candidate/comparison/cost/promotion/rollback) · 7 self-evolution result (proposal/candidate/proof/
cost-reliability impact/promoted-or-kept-as-alternative) · 8 API/UI · 9 redteam · 10 files changed · 11 proofs
run (exact commands + pass/fail) · 12 remaining risks · 13 exactly ONE next target. **Then run the next command**
unless a hard stop fires.

## PARALLEL STRATEGY + SELF-EVOLUTION CLAUSE (add to the durable North Star prompt)
Baltor continuously researches the market, competitors, integrations, and startup/YC strategy, AND continuously
seeks cheaper/better implementations — by running candidate paths **side-by-side** with the working baseline on
the same input. A candidate is promoted ONLY when it proves equal-or-better correctness, governance,
source-handle preservation, tenant safety, and reliability at equal-or-lower (or justified) cost, with a
recorded rollback and the **original path preserved as a fallback alternative**. Agents PROPOSE improvements;
they never PROMOTE, never delete a baseline, and never serve unverified truth. Strategy claims cite sources;
cost claims require output equality; nothing reaches the served path without a gate. Research, competition, and
self-evolution are continuous lanes — never "done."

*Warrant: clear owner intent (a long-running prompt fusing research/competitor/SWOT/startup/architecture +
parallel-path comparison + self-evolving cheaper-and-better while preserving originals). Captured as a staged
build prompt; consistent with the locked brand + numeric-config/wrapped-redundancy/lossless/no-truth-bypass/
cloud-agnostic principles. Build as focused increments; the parallel-path engine + self-evolution loop is the
headline technical core.*
