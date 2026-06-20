# /workflows /baltor-path-improvement-and-skill-intake-factory (CANONICAL — supersedes baltor-candidate-rating-and-skill-ingestion)

A governed factory with two linked jobs: **(1) generate/run/compare/score/promote better pipeline PATHS**, and
**(2) discover/ingest/sandbox/evaluate/catalog external SKILLS/repos** — both via ONE machinery: run
side-by-side against the baseline on the SAME input snapshot, score across shared dimensions, redteam, and
**promote only with proof; keep the baseline as a fallback alternative.** Foundation = the Parallel-Path Engine
(`src/baltor/experiments/*`, `schemas/experiments/*`) from `baltor-parallel-path-hard-mode`; this factory adds
the full dimension set + skill intake on top.

> **Sequencing:** focused increments; NEVER run concurrently with another repo-mutating workflow (shared
> registries clobber). Build AFTER the Parallel-Path Engine lands. Honors all locked principles (numeric-config
> + wrapped redundancy, measured-lift two-axis gate, no-truth-bypass, lossless, candidate-behind-port-never-runtime,
> cloud-defer-only-after-local-equivalent).

## PATH + SKILL FACTORY CLAUSE (carry in the North Star loop)
Any more-efficient pipeline path must run **side-by-side against the baseline on the same input snapshot** and
be scored across **correctness · output fidelity · source-handle coverage · lineage/receipts · safety · tenant
isolation · runtime · cost · reliability · observability · UI/UX · maintainability**. **Cheaper is not better
unless safety and fidelity are preserved.** Promotion requires scorecard + redteam + rollback + baseline
preservation. External skills/GitHub repos are **discovery artifacts ONLY** until sandboxed, contract-tested,
evaluated, redteamed, registered, and run as **candidate parallel paths**. No skill becomes active by popularity
or discovery alone. Agents PROPOSE; the gate DISPOSES.

## 0. Preserve the baseline
Offline demo · CFPB invariant ("10 business days"; FAQ-30 + allegations held out; only verified winner served;
lineage+receipt) · DurableFleetLedger · live supervisor · worker buckets · execution-backend flexibility +
local emulators · the existing optimization suite (baseline/candidates/bake-off/promotion receipts) ·
architecture guardrails · provider replacement graph. memory/browser/LLM/semantic-similarity/external-skill
output ≠ truth. No second runtime/worker-framework/durable-ledger/provider-registry/skill-registry; no bypass.

## 1. Core principle
A path/skill is NOT better because it's new, cheaper, popular, or an agent says so. It is better only if it
PROVES, vs baseline: ≥ output correctness · ≥ source-handle preservation · ≥ lineage/receipt · ≥ safety · ≥
tenant isolation · ≥ fidelity · ≥ reliability · ≥ observability · ≤ (or justified) cost · ≤ (or justified)
runtime · a clear rollback · baseline preserved. **Baseline stays active until promotion.**

## 2. Path contracts
`schemas/paths/{PathDefinition,PathVariant,PathImprovementProposal,PathRun,ParallelPathRun,PathComparisonReport,
PathScorecard,PathPromotionDecision,PathRollbackPlan,PathExperimentReceipt,PathEvaluationDimension,
PathEvaluationPolicy}.v1` (register in contract_registry). `PathDefinition`: path_id · capability_slot ·
path_type · implementation_node_id · input/output_contract · worker_bucket · execution_backend_policy_id ·
provider_selection_policy_id · tenant_scope · enabled · mode(baseline|candidate|shadow|canary|fallback|
deprecated) · safety_class · cost_model_ref · expected_runtime_profile · promotion_criteria ·
rollback_target_path_id · proofs · docs. `PathEvaluationDimension`: dimension_id · display_name · numeric_weight
· direction(higher_is_better|lower_is_better|pass_fail) · threshold · blocker_if_failed · measurement_method ·
evidence_artifact_ids. Proof `check_path_contracts`.

## 3. Standard evaluation dimensions (`architecture/{path_evaluation_dimensions,path_evaluation_policies}.json`)
- **Correctness/result:** answer_correctness · output_contract_validity · reference_case_match ·
  deterministic_repeatability · regression_count.
- **Fidelity:** source_handle_coverage · lineage_completeness · receipt_completeness · held_out_preservation ·
  rehydration_success · native_shape_preservation · semantic_fidelity (candidate-only).
- **Governance/safety (BLOCKERS):** unverified_truth_leak · held_out_leak · tenant_leak · stale_fact_served ·
  unresolved_conflict_served · candidate_served · memory/llm/browser_truth_bypass (each must be 0).
- **Runtime/reliability:** mean/p95_runtime_ms · timeout/failure/retry/dlq_rate · idempotency_skip ·
  crash_recovery_passed · worker_claim_conflict.
- **Cost:** estimated_{compute,model,browser,storage,human_review}_cost · cost_per_{success,verified_fact,
  context_response} · cost_reduction_percent.
- **Scale/ops:** throughput_per_worker · tasks_per_worker_start · queue_wait_ms · backlog_drain_time ·
  horizontal/vertical_scalability_score · observability/telemetry_coverage.
- **UI/UX:** operator_clarity · dashboard_projection_coverage · error_explainability · reviewability ·
  time_to_debug · user_visible_latency · user_trust_clarity.
- **Maintainability:** complexity_score · code_size_delta · dependency_count_delta · new_provider_count ·
  configuration_externalized · local_emulator_exists · redteam/docs_coverage · rollback_simplicity.

**Rules:** safety blockers override cost savings; held-out leak / source-handle loss / no-rehydration /
no-rollback → FAIL; cheaper-but-lower-fidelity → FAIL unless marked advisory/non-serving; UI/UX influences
promotion only AFTER safety+correctness pass. Weights are numeric config (gaps for inserting new dimensions).
Proof `check_path_evaluation_dimensions`.

## 4. Parallel path runner
`src/baltor/paths/{path_registry,parallel_path_runner,path_comparator,path_scorecard,path_promotion_gate,
path_rollback}.py`. Behavior: freeze input snapshot → run baseline → run candidate(s) on the EXACT same snapshot
→ validate+normalize outputs → compare → scorecard → redteam → write PathComparisonReport + PathExperimentReceipt
→ decide(reject|keep_shadow|keep_canary|promote_candidate|needs_human|needs_more_data) → preserve baseline →
record rollback plan. Rules: candidate can't mutate baseline; baseline active until promotion; same snapshot
mandatory; no candidate serves truth in shadow; parallel compare can't duplicate side effects; all diffs
explainable. Proof `check_parallel_path_runner`.

## 5. Path generation / agent review
`src/baltor/paths/{path_reviewer,path_improvement_planner,path_variant_generator}.py`. Agents MAY inspect a path
and propose: local alternative for a high-cost/fragile step · different provider/backend · better decomposition/
comparison/reconciliation · new skill/tool · simpler deterministic logic · caching/batching · leaf-convergence ·
worker-lifecycle change. Agents MAY NOT promote, remove baseline, serve candidate output, bypass Verification/
Reconciliation/Consumption, hide safety failures, or activate real cloud without approval. `PathImprovementProposal`:
baseline_path_id · proposed_candidate_path_id · improvement_type · expected_benefit/risks · required_contracts ·
required_local_emulator · expected_output_contract · evaluation_policy_id · rollback_plan · redteam_plan.
Proof `check_path_improvement_agent_review`.

## 6. Path promotion gates (`architecture/path_promotion_policies.json`)
Stages: proposed → implemented → local_emulated → contract_green → baseline_snapshot_green → shadow_green →
parallel_compare_green → canary_green → redteam_green → human_approval_if_required → promoted → monitored →
rollback_ready. **Blockers:** output-contract mismatch · missing source handles/receipts · held-out/tenant leak
· stale-fact/unresolved-conflict served · memory/LLM/browser truth bypass · no local emulator · no rollback ·
no redteam · no baseline preservation · non-idempotent side effects · cheaper-but-lower-safety · UI hides
warning · API bypasses gate. Proof `check_path_promotion_gate`.

## 7. Path comparison examples (≥5 local, deterministic)
(1) execution backend: local_subprocess vs local_function_emulator (output equality · claim correctness · cost ·
runtime · idempotency · retry/DLQ). (2) optimization/compression: current pack vs compressed (answer-critical
facts · handles · held-out · token/cost · consumption readiness). (3) reconciliation: authority policy vs
leaf-convergence-assisted (CFPB 10-vs-30 · held-out · receipts · no leak). (4) parser/decomposition: structured
vs alternate (atomic-fact count · allegation holdout · handles · contract). (5) worker lifecycle: cold-start vs
pool/cooldown-drain (startup · active · idle burn · tasks-per-start · output equality). Proof
`check_path_comparison_examples`.

## 8–9. Skill contracts + registries
`schemas/skills/{SkillArtifact,SkillSource,SkillManifest,SkillIntakeRequest,SkillIntakeReport,
SkillCapabilityMapping,SkillSandboxRun,SkillEvaluationReport,SkillPromotionDecision,SkillRiskReport,SkillVersion,
SkillDependencyReport}.v1` (register). `SkillArtifact`: skill_id · skill_version · source_type(local|github|mcp|
codex_skill|claude_skill|custom) · source_ref · content_hash · license · capability_slots · required_tools/
dependencies · local_emulator_required · sandbox_required · status_code · status_label · risk_score ·
evaluation_reports · promotion_status · owner · docs · proofs. Registries `architecture/{skill_registry,
skill_capability_graph,skill_intake_policy,skill_promotion_policy,skill_risk_taxonomy,skill_source_allowlist,
skill_dependency_policy}.json`. **Skill status codes** 100 disabled · 200 discovered · 300 intake_candidate · 400
sandboxed · 500 evaluated · 600 active_local · 700 active_external · 800 deprecated · 900 quarantined. **Edge
codes** 1000 SUPPORTS_CAPABILITY · 1100 REPLACES · 1200 SUPPLEMENTS · 1300 FALLBACK_FOR · 1400 SHADOW_OF · 1500
CANARY_OF · 1600 SUPERSEDES · 1700 BLOCKED_BY_POLICY · 1800 REQUIRES_REVIEW · 1900 REQUIRES_LOCAL_EMULATOR.
Skills are graph nodes mapped to capability slots; no import/exec before sandbox; none active without eval +
redteam + (if external) local emulator; runtime uses IDs/codes/edges, not display names. Proof `check_skill_registry`.

## 10–13. Discovery · intake · eval dimensions · sandbox
`src/baltor/skills/skill_discovery.py` (sources: local folder · GitHub URL · GitHub search/watchlist candidate ·
MCP catalog · codex/agent skill folder · awesome-lists · manual; live GitHub optional, offline fixture
`fixtures/skills/sample_skill_repos.json` MUST work; discovery ≠ trust). Pipeline `src/baltor/skills/{skill_intake,
skill_manifest_parser,skill_sandbox,skill_evaluator,skill_promotion}.py`: discover → fetch/load → content hash →
parse/infer manifest → classify capability slots → inspect license/deps/tools/network/secrets/file-access →
sandbox install/load → contract tests → task eval → redteam → SkillEvaluationReport → add to graph as candidate
→ optional shadow/candidate path → promote only by policy. Eval dimensions `architecture/skill_evaluation_dimensions.json`:
capability_fit · contract_validity · task_success_rate · output_fidelity · source_handle_preservation ·
tenant_safety · no_truth_bypass · dependency_safety · license_compatibility · maintainability · cost_estimate ·
runtime_ms · sandbox_safety · determinism · observability · redteam_pass_rate · docs_quality ·
local_emulator_quality (license/unsafe-dep/no-sandbox/no-redteam/contract-mismatch → BLOCK active; source-handle
loss → block truth use; may remain candidate if useful-but-unsafe-for-golden-path). Sandbox
`src/baltor/skills/local_skill_sandbox.py` (reuse managed-venv/sandbox port if present): temp dir · copy files ·
managed venv · allowed deps only (NO global pip) · no secrets · network off by default · timeout · capture
stdout/stderr · SkillSandboxRun · cleanup. Proofs `check_skill_discovery` · `check_skill_intake_pipeline` ·
`check_skill_evaluation_dimensions` · `check_skill_sandbox`.

## 14–15. Skill-as-parallel-path + example skills
A skill becomes a CANDIDATE PATH, not direct active logic: SkillArtifact → PathDefinition(candidate) →
ParallelPathRun → PathComparisonReport → SkillEvaluationReport → SkillPromotionDecision. Proof
`check_skill_as_parallel_path` (skill maps to slot · runs shadow · baseline stays active · contract validates ·
comparison written · unsafe skill rejected · safe local skill can go active_local). Example skills (≥3 offline):
(1) `skill.utility.normalize_duration` ("ten business days"/"10 biz days" → normalized; capability
typed_normalization; PASSES). (2) `skill.compare.runtime_config_diff` (compares worker policy/config leaves;
capability leaf_convergence; PASSES). (3) `skill.bad.truth_bypass` (tries to emit CanonicalFact directly; FAILS
redteam). Optional (4) `skill.optimization.context_trim` (must preserve handles + held-out). Proof
`check_skill_examples`.

## 16–17. API/UI + redteam
Skill API (local-only intake/evaluate/run-shadow/promote-local; no real GitHub/network/secrets from UI): GET
`/api/skills[/registry|capability-graph|intake-reports|evaluation-reports|risks]` + POST intake-local/evaluate/
run-shadow/promote-local. UI `/skills` (registry · discovered · capability mapping · intake/sandbox · eval
scorecards · redteam · shadow/canary · promotion · risk/license/dependency). Path API/UI via `/experiments` +
`/api/experiments/*`. Proofs `check_skill_api` · `check_skill_ui`. Redteam `check_path_skill_factory_redteam` —
all FAIL safely: cheaper path promoted despite handle loss · candidate serves FAQ-30 · hides held-out · diff
inputs in comparison · candidate deletes baseline · promotion without rollback · agent promotes own path · skill
imports forbidden dep · skill runs unsandboxed · writes outside sandbox · reads secrets · emits CanonicalFact/
ContextResponse · bypasses provider wrapper · active-without-eval · GitHub repo active after discovery only ·
display-string controls runtime.

## 18–21. Docs · registries · proofs · acceptance
Docs `docs/paths/{path-improvement-factory,parallel-path-evaluation,path-scorecards,path-promotion-gates,
side-by-side-testing,path-cost-runtime-fidelity-uiux,path-rollback}.md` + `docs/skills/{skill-intake-factory,
skill-registry,skill-sandboxing,skill-evaluation,github-skill-watchlist,skill-as-parallel-path,skill-redteam}.md`.
Update registries (section_maturity, contract_registry, runtime_ownership, tool_replacement_graph,
provider_selection_graph, skill_registry/capability_graph, path_evaluation_dimensions, path_promotion_policies,
technical_debt, opportunities, risk_register). Create/run all `check_*` above + `check_path_skill_factory_full_stack`;
REGRESS demo_offline_full_baltor · check_baltor_full_stack_perfect · check_durable_fleet_ledger ·
check_live_supervisor_full_stack · check_no_direct_provider_bypass · `baltor_flywheel.py --once`. **M10** (each
factory) requires contracts + runner/pipeline + comparison/eval + scoring + promotion gate + rollback + examples
+ API/UI + redteam + docs + regressions. Acceptance per §21 of the source spec. No fake M10.

*Warrant: clear, repeated owner intent (standardized rules/paths/gates for side-by-side pipeline-path rating
across results/output/fidelity/cost/runtime/ui-ux + a safe way to ingest/test/evaluate the hundreds of skill
repos published daily). Reuses the Parallel-Path Engine + measured-lift two-axis gate + sandboxed-execution
port; numeric rubric (config not code); candidate-behind-port-never-runtime; baseline always preserved. Build as
focused increments; never concurrent with another repo-mutating workflow. Supersedes the interim
baltor-candidate-rating-and-skill-ingestion.md.*
