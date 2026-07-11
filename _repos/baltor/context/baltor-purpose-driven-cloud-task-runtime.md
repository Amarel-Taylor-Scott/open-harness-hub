# /workflows /baltor-purpose-driven-cloud-task-runtime (CANONICAL — supersedes baltor-cloud-task-self-adapting)

Build the **Purpose-Driven Cloud Task (PurposeTask)** runtime: a cloud-agnostic, backend-flexible,
self-evaluating, self-adapting task object **provisioned by purpose/capability, not by code or infra type.**
Vision: `_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md`. PoC + contract already built (flywheel 316:
`_repos/baltor/backend/src/baltor/purpose_tasks/` + `schemas/purpose_tasks/PurposeTaskSpec` + check_purpose_task_{poc,contracts}).

> **NAMING (load-bearing):** internal name is **PurposeTask** (a.k.a. Purpose-Driven Cloud Task). Do NOT call it
> "Cloud Task" — that collides with **Google Cloud Tasks** (a managed async queue/dispatch product). PurposeTask
> is bigger: a governed capability object that owns purpose + success criteria + backend selection +
> self-evolution + fallback preservation.
> **CI/CD refinement:** PurposeTask does NOT eliminate CI/CD — it **embeds CI/CD-like safety gates inside the
> task lifecycle** (versioning · contract tests · sandbox · side-by-side · canary · promotion · rollback ·
> audit). It self-adapts without a human manually driving the pipeline; it never drops the safety ideas.
> **Sequencing:** depends on the K8s/Cloud-Function Template Factory (real generated implementations +
> shape-switching) + Path/Skill factory + SkillGraph. Build those first; PurposeTask composes them. Focused
> increments; never concurrent with another repo-mutating workflow.

## PURPOSE TASK CLAUSE (carry in the North Star loop)
Workers and cloud functions are IMPLEMENTATIONS; **purpose/capability is the product unit.** A PurposeTask is
declared by intent (purpose · input/output contract · connected_to · guidelines · success_criteria ·
allowed_backends · resources · templates · skills · promotion_criteria · rollback_policy · self_evolution_policy)
and runs as a cheap deterministic hot path. The runtime chooses the backend by policy/telemetry/cost/SLA/health
(local-emulator-first; cloud/K8s peers are candidates that fall back to local). On drift it self-adapts via the
governed Parallel-Path Engine (propose → side-by-side on same snapshot → score → promote-only-if-criteria →
keep baseline as fallback → rollback recorded). Agents PROPOSE; the gate DISPOSES. Self-adaptation is bounded
autonomy + deterministic gates, never unbounded mutation.

## Competitive wedge (why this is a real category)
The hyperscalers have the PARTS, not the whole: AWS (Lambda · Step Functions Task · Bedrock action groups ·
Systems Manager runbooks · Q/CloudWatch investigations), GCP (Cloud Run functions/jobs · Workflows · Cloud
Deploy · **Cloud Tasks** queue · Gemini Cloud Assist), Azure (Functions · Container Apps Jobs · Deployment
Environments · Copilot), ServiceNow (governed agents), Kiro/Copilot/Q (spec→code). **None exposes a long-lived
capability object that owns success criteria + cost/fidelity/runtime gates + cross-backend selection +
self-evolution + baseline/fallback preservation.** Those tools become PROVIDERS/SKILLS inside PurposeTask, not
the control plane. Baltor's differentiation = the governed substrate (source handles · proofs · local emulators
· worker templates · replacement graphs · path comparison · promotion gates · receipts). One-liner: *Baltor
turns cloud functions and Kubernetes workers into self-improving, governed business capabilities — the unit of
management becomes the capability, not the function/manifest/image.*

## Planes (7) · Lifecycle (12)
Planes: Purpose · Implementation · Execution · Resource · Evaluation · Evolution · Governance. Lifecycle:
define → plan → provision-locally → run (via FleetLedger) → observe (JSON logs/telemetry/cost/fidelity) →
detect-pressure → propose-candidate → run-side-by-side → score → promote-or-reject → adapt-backend → preserve
(every version/receipt/decision/rollback-target).

## Build (PARTS, focused increments)
- **P1 Contracts** `_repos/shared-backend-components/schemas/purpose_tasks/{PurposeTaskSpec(DONE),PurposeTaskRun,PurposeTaskPath,PurposeTaskScorecard,
  PurposeTaskPromotionDecision,PurposeTaskSelfEvolutionPolicy,PurposeTaskResourcePlan,PurposeTaskReceipt,
  PurposeTaskBackendDecision}.v1` (register in contract_registry).
- **P2 Registry** `architecture/{purpose_task_registry,purpose_task_promotion_policies,
  purpose_task_self_evolution_policies,purpose_task_backend_policies}.json`. Each PurposeTask: purpose_task_id ·
  capability_slot · I/O contract · purpose · connected_systems · guidelines · success_criteria ·
  allowed_backends · resources · templates · skills · baseline_path_id · promotion/self_evolution/rollback policy
  · owner · status.
- **P3 Runtime** `_repos/baltor/backend/src/baltor/purpose_tasks/{registry,planner,runner,backend_selector,evaluator,promotion_gate,
  self_evolver,rollback,telemetry}.py` (extend the built purpose_task.py controller).
- **P4 Backend selection** — reuse `execution_backend_selector` (cloud-agnostic; Lambda/GCF/Azure peers; k8s_job/
  cloud_run_job/ACA-jobs peer jobs; local emulators = offline default; missing creds → local fallback; every
  backend still claims from FleetLedger; backend switch records a PurposeTaskBackendDecision).
- **P5 Resources** — reuse DataResourceSpec/ResourceManager (temp-vs-persistent · partition/cluster/KMS ·
  retention · tenant scope · cleanup; no unmanaged table/dataset creation).
- **P6 Self-evolution** — triggers (failure/latency/cost over threshold · source changed · provider unavailable ·
  backend price changed · new skill · redteam regression · criteria miss); allowed (propose candidate · shadow ·
  side-by-side · canary · batch/worker-policy adjust · regenerate-from-template · add skill candidate); BLOCKED
  (delete baseline · self-promote without proof · serve candidate truth · real cloud creds without approval ·
  change tenant isolation).
- **P7 Side-by-side** — same input snapshot; score correctness · output-contract · source-handles · lineage ·
  receipts · held-out · tenant-safety · runtime · cost · reliability · UI/UX · observability · maintainability;
  promote only if safety blockers pass + contract valid + handles preserved + baseline preserved + rollback
  exists + redteam green + score meets policy.
- **P8 Examples** (offline): purpose_task.utility_hash · purpose_task.sample_source_research (browser emulator/
  pool/k8s-job candidate) · purpose_task.cfpb_deadline_verification · purpose_task.cost_reduce_optimization_path.
- **P9 API/UI** `/api/purpose-tasks*` (run · run-side-by-side · promote-candidate · rollback; projection-only +
  local tests) · `/purpose-tasks` page (registry · purpose/contracts · connected systems · success criteria ·
  allowed backends · baseline + candidates · side-by-side scorecards · cost/runtime/fidelity · evolution triggers
  · promotions · rollbacks · resource plans · skills/templates · redteam).
- **P10 Redteam** `check_purpose_task_redteam` — all FAIL safely: promote-without-proof · delete-baseline ·
  cloud-without-local-emulator · k8s-against-policy · source-research emits CanonicalFact · serves FAQ-30 ·
  handles lost · resource without DataResourceSpec · self-evolver real-cloud-creds without approval ·
  self-evolver changes tenant isolation · UI promotes without gate · backend switched without decision receipt.
- **P11 Proofs** check_purpose_task_{contracts(DONE),registry,local_execution,backend_switching,side_by_side,
  self_evolution_gate,resource_plan,examples,api,ui,redteam,full_stack}; REGRESS demo_offline_full_baltor ·
  check_baltor_full_stack_perfect · check_durable_fleet_ledger · check_live_supervisor_full_stack ·
  check_execution_backend_full_stack · check_no_direct_provider_bypass · `baltor_flywheel.py --once`.

## Hard safety rules (a self-evolved task is safe ONLY if)
same input contract · same output contract · same-or-better scorecard · same-or-better source-handle coverage ·
same-or-better safety · same-or-lower-or-justified cost · same-or-better reliability · rollback exists · baseline
preserved · receipts written. A PurposeTask MAY generate a candidate; it may NOT replace/delete its baseline,
serve candidate truth, bypass source handles, skip redteam, use real cloud creds without approval, create
unmanaged cloud resources, or change tenant isolation by itself.

## Acceptance
contracts + registry exist · runs locally · chooses among local function/managed-venv/job/pool · cloud/K8s are
candidates behind the SAME contract · backend switching by policy · side-by-side works · self-evolution gate
works · baseline remains fallback · promotion gate blocks unsafe · resource plan works · API/UI · redteam fails
safely · offline demo + flywheel GREEN.

*Warrant: clear, repeated owner intent (provision workers/cloud-functions BY PURPOSE/CAPABILITY, not by code; a
self-adapting governed Cloud Task abstraction). Renamed PurposeTask to avoid the Google Cloud Tasks collision;
embeds (not eliminates) CI/CD-like gates; composes the built Parallel-Path Engine + execution-backend selector +
template factory + skill graph; no second runtime/ledger/registry; bounded autonomy + deterministic gates.
Supersedes baltor-cloud-task-self-adapting.md.*
