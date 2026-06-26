> **EDITOR'S NOTE (captured 2026-06-06, verbatim from the owner).** This is the CANONICAL, LIVE build
> artifact for **Teleon's control & trust plane** (Staff Control Tower + Customer Assurance Portal). It is a
> **separate GREENFIELD TypeScript build** (its own `teleon/` repo, its own `CLAUDE.md`, its own
> `.claude/hooks/`), to be run by a FRESH Claude Code session in PLAN MODE — it is **NOT** for the autonomous
> Python `/baltor-no-stop-full-repair-loop`. Do **NOT** install Part B (`CLAUDE.md`) or Part D
> (`.claude/hooks/guard.py`, `.claude/settings.json`) into THIS repo root — they would hijack the Baltor repo.
> Canonical names (the kit's §5 still says "Purpose Runtime Control Tower" — a residual; the staff dashboard is
> **Teleon Control Tower**): platform/product = **Teleon** (`teleon.dev`, owned) · formal object =
> **PurposeTask** (an instance is colloquially "a teleon"; `CapabilityTask` = accepted synonym) · open standard
> = **Capability Task Specification (CTS)** · staff dashboard = **Teleon Control Tower** · customer dashboard =
> **Capability Assurance Portal**. Supersedes the earlier "independent-purpose-runtime-company" PART-1..8 prompt
> and the "Cairn" sub-brand (both retired). See `docs/strategy/teleon-naming-and-domain.md` +
> `docs/strategy/teleon-company-strategy.md`.

# Teleon — Claude Code Build Kit
### Teleon's control & trust plane — Staff Control Tower + Customer Assurance Portal

> **Platform / product:** Teleon — intent-native, eval-gated, self-adaptive compute · `teleon.dev`
> **Core unit/object:** `PurposeTask` — runtime-agnostic; an instance can be called *a teleon*. (`CapabilityTask` is an accepted synonym.)
> **What this kit builds:** Teleon's **control & trust plane** — a Staff Control Tower + a Customer Assurance Portal over one event-sourced truth model.
> **One-liner:** *Serverless runs code. Kubernetes runs workloads. Teleon runs purpose.*

**How to use this file with Claude Code.** It has four parts. You can paste the whole file as your first message, or (recommended) split it into the repo:
- **Part A → your first message to `claude`** (the kickoff prompt).
- **Part B → `CLAUDE.md`** at repo root (lean, durable rules — auto-loads every session).
- **Part C → `docs/teleon-spec.md`** (the full design Claude reads on demand).
- **Part D → `.claude/hooks/` + `ci/`** (enforcement that makes the invariants real, since CLAUDE.md is context, not enforcement).

A note on Claude Code reality that drives this design: `CLAUDE.md` is **guidance**, not a hard gate. Anything that must be *impossible* (UI writing truth, touching real cloud) is enforced with a **PreToolUse hook + CI**, not prose. This mirrors Teleon itself: governance is enforced by gates, not good intentions. Confirm the current hook/settings shapes against the Claude Code hooks docs when you wire Part D.

---

# PART A — Kickoff prompt (paste as your FIRST message to `claude`)

```
You are the build agent for Teleon, the Teleon Capability Plane: a web control plane + trust
surface for "PurposeTasks." Read CLAUDE.md and docs/teleon-spec.md IN FULL before doing anything.

Operate in PLAN MODE first: produce a written plan and the Phase 0 task list, then STOP and wait
for my approval before writing code. Use TaskCreate to track the phases in docs/teleon-spec.md
(§12); mark each task in_progress before starting and completed when done.

Hard constraints (do not violate; several are enforced by a PreToolUse hook and CI):
- MODEL + UI ONLY. Never connect to real cloud, never deploy, never call a real LLM to make a
  decision. Runtime adapters, the eval harness, and candidate generation are interfaces with
  clearly-labeled MOCK implementations driven by the seed fixtures.
- NO DASHBOARD TRUTH. The UI reads projections and requests governed actions only. There is no
  write path from UI to a truth field. All mutations go command -> handler -> event -> projection.
- Never fabricate scores, receipts, or evidence. Missing data renders an explicit empty state.

Before you do ANY of the following, use AskUserQuestion and wait for my answer:
- edit a file that already exists in a way that changes its behavior,
- weaken, skip, or delete any redteam check,
- change a stable-contract field (purpose, success criteria, permissions, data access),
- add an external dependency/service, or expand scope beyond docs/teleon-spec.md.

After each phase: run the full test suite, confirm the redteam suite (§9) is GREEN, commit with a
conventional-commits message, then STOP and summarize for my review (this is the phase checkpoint).
Do not begin the next phase until I say continue.

Start now: read the two docs, then give me the plan + Phase 0 tasks. Do not write code yet.
```

---

# PART B — `CLAUDE.md` (repo root; keep it skimmable)

```markdown
# Teleon — Project Memory

Teleon is intent-native, eval-gated, self-adaptive compute. This repo builds **Teleon's control &
trust plane**: a Staff Control Tower + Customer Assurance Portal over ONE event-sourced truth model
for **PurposeTasks**. Full design: `docs/teleon-spec.md` (read it).

## Product invariants (enforce in what you build; tested by §9 redteam)
1. **No dashboard truth.** UI reads projections, requests governed actions. No UI→truth write path.
   All state changes: command → handler (validates policy) → append-only event → projection (read-only).
2. **Evidence decides; policy gates; COST NEVER OVERRIDES GOVERNANCE.** A governance blocker blocks
   promotion regardless of cost/latency wins. Hard-coded, not configurable.
3. **Means vs. ends.** Implementation/runtime/prompt/parser/retry/timeout/fallback/model may change
   autonomously inside policy. Purpose/permissions/success-criteria/data-access/connected-systems/
   risk-class change ONLY via a human-approved BoundaryChange.
4. **One truth, two surfaces.** CustomerProjection is built from an explicit ALLOW-LIST + translated
   trust statements — never by hiding fields from the staff view. Zero staff-only fields; never any
   other tenant's data.
5. **Tenant isolation** enforced at the handler/projection layer, not just the UI.
6. **Promotion is a workflow, not a button.** "Promote" opens a Promotion object + runs the policy
   engine; it never deploys directly.

## Build rules
- MODEL + UI ONLY. No real cloud, no real deploys, no real-LLM decisions. Mocks + fixtures only.
- Never fabricate data — render explicit empty/"no evidence yet" states.
- Work in phases (`docs/teleon-spec.md` §12). After each: tests pass, redteam green, commit, STOP.
- Use AskUserQuestion before: editing existing files, weakening a redteam check, touching a
  stable-contract field, adding a dependency, or expanding scope.

## Enforcement (these are NOT just guidance)
- A **PreToolUse hook** (`.claude/hooks/guard.py`) blocks edits that add a UI→truth write path or a
  real-cloud SDK import. If it blocks you, fix the design — do not work around it.
- **CI** (`ci/`) fails on: UI truth-writes, red redteam suite, CustomerProjection leakage, or any
  test where a cost win flips a governance gate. If it would block a merge, it lives in CI.

## Stack & layout
TypeScript monorepo. `apps/command-api` (write), `apps/read-api` (read, projections only),
`apps/web` (staff + customer shells), `packages/core` (types/events/handlers/projections),
`packages/policy` (pure eligibility + blockers), `packages/adapters` (MOCK), `packages/redteam`,
`fixtures/`. Postgres event store + projection tables (SQLite ok for dev). Vitest + Playwright.
(Python/FastAPI or Go acceptable — keep the boundaries identical.)
```

---

# PART C — `docs/teleon-spec.md` (full design)

## 1. Glossary
| Term | Meaning |
|---|---|
| **PurposeTask** | Durable contract: purpose, I/O schemas, allowed/forbidden capabilities, connected systems, success criteria, governance. The stable object. |
| **Implementation** | A candidate way to fulfill the task: code/prompt/workflow/parser/selector/template/model+tool sequence. Replaceable. |
| **RuntimeBinding** | Maps an implementation to a runtime class (function, container, K8s job, queue worker, browser worker, durable workflow, GPU, edge). |
| **Run** | One execution record. **Scorecard** | Eval results across the §8.1 dimensions. **RuntimeDecision** | Why a runtime class was chosen (and which were rejected). |
| **Promotion** | Recorded incumbent→candidate decision with evidence/gates/rollback. **Rollback** | Reversion plan/result. |
| **Approval / BoundaryChange** | Human decision on an *ends* change (purpose, permission, external domain, cost ceiling, model provider, output sink, browser login). |
| **TaskOrientation** | Structured operational memory (failure modes, env facts, preferred/rejected strategies, successful migrations, predictive evals). Powers diagnosis AND user-visible explanations. |
| **PolicyResult / RedteamResult / CapabilityGraphEdge / Receipt** | Policy gate output / self-governance attack coverage / task relationship / per-output provenance. |
| **StaffProjection / CustomerProjection** | Read models. Staff = internals; Customer = allow-listed, translated assurance. |

## 2. Architecture (CQRS / event-sourced)
```
 UI ─POST→ Command API → Handlers (validate vs Policy) → Events (append-only) → Projection Builders
                                                                          ├→ StaffProjection
 UI ←GET── Read API (projections only, tenant-scoped) ←────────────────── └→ CustomerProjection
```
Guarantees the code must hold: all mutations via handlers; events immutable + replayable; projections read-only to UI; `CustomerProjection` composed via allow-list, never derived by subtraction.

**Components to build:** `command-api`, `read-api`, `core` (types/events/handlers/projections), `policy` (pure functions), `web` (two shells), `adapters` (MOCK `RuntimeAdapter`/`EvalHarness`/`CandidateGenerator`), `redteam`.

## 3. Data model (events versioned `.v1`; add fields freely, never remove stable-contract fields without approval)
```yaml
PurposeTaskSpec:        # STABLE (ends)
  id; name; owner; tenantId; riskClass[low|medium|high|critical]
  purpose{summary,businessValue,nonGoals[]}
  input{schema:jsonschema}; output{schema:jsonschema}
  allowedCapabilities[]; forbiddenCapabilities[]
  connectedSystems{reads[],writes[],neverAllowed[]}   # never: PII extraction, payments, credential harvest, unapproved domains, destructive writes
  successCriteria{schemaValid,minFieldAccuracy,maxP95LatencyMs,maxCostPerRunUsd,forbiddenToolCalls,sourceHandleCoverageMin}
  runtimePolicy{allowedRuntimeClasses[],routingObjectives[correctness,cost,latency,reliability]}; specVersion
PurposeTaskImplementation:   # VARIABLE (means)
  id; taskId; version; type[deterministic-parser|browser-script|http-fetch|api-connector|llm-extraction|ocr|agentic|hybrid-cascade]
  status[draft|shadow|canary|active|rejected|retired]; artifacts{codeRef?,promptRef?,parserRules?,selectors?,modelConfig?,toolSequence?}
  provenance{generatedBy,templateUsed?,skillsUsed?[],slsaRef?}
PurposeTaskRuntimeBinding: id; implementationId; runtimeClass; config{timeoutMs?,memoryMb?,concurrency?,batchSize?,cacheTtlS?}
PurposeTaskRun: id; taskId; implementationId; runtimeClass; inputHash; outputHash; outcome[success|failure|partial|held_for_review]
  schemaValid; latencyMs; costUsd; fieldConfidence; sourceHandleCoverage; forbiddenToolCalls
  cascadePath[cache|deterministic|browser|ocr|llm|agentic|human]; traceRef; receiptId?
PurposeTaskScorecard: id; taskId; implementationId; regressionPassed; shadowRuns; canaryRuns
  dimensions{correctness,sourceHandleCoverage,lineage,receiptCompleteness,heldOutPreservation,
             tenantSafety[pass|fail],latencyMs,costUsd,reliability,observability[pass|fail],maintainability,uxClarity,redteamStatus[pass|fail|missing]}
PurposeTaskRuntimeDecision: id; runId; selectedRuntime; reasons[]; rejectedRuntimes[{runtimeClass,reason}]
PurposeTaskPromotion: id; taskId; from; to; reason; policyResultId; rollbackPlanId; approvalId?
  evidence{goldenBefore,goldenAfter,p95Before,p95After,costBefore,costAfter,shadowRuns,canaryRuns}
  decision[eligible|blocked|approved|rejected|promoted|rolled_back]
PurposeTaskRollback: id; taskId; targetImplementationId; reason; result[ready|executed|failed]
PurposeTaskPolicyResult: id; subjectId; eligible; blockers[]; gates{outputContractPassed,regressionPassed,
  noPermissionExpansion,noSourceHandleLoss,noHeldOutLeak,noTenantLeak,rollbackAvailable,approvalSatisfied,
  redteamCovered,successCriteriaNotWeakened,observabilityEnabled}
PurposeTaskBoundaryChange: id; taskId; requestedBy; rationale; status[requested|approved|rejected]
  changeType[new_external_domain|browser_login|new_output_sink|higher_cost_ceiling|external_model_provider|permission_expand|purpose_change|data_class_increase]
  impact{addsWrites,addsDataSinks,costDeltaPerRunUsd}
PurposeTaskApproval: id; boundaryChangeId; audience[staff|customer]; decidedBy; decision[approved|rejected]
PurposeTaskRedteamResult: id; taskId; lastRunAt; overall[pass|fail]
  coverage{selfPromotionBlocked,purposeMutationBlocked,permissionExpansionBlocked,successCriteriaWeakeningBlocked,
           truthWithoutGateBlocked,baselineDeletionBlocked,dashboardTruthWriteBlocked,sourceHandleLossBlocked,
           customerDataRedacted,runtimeAllowlistEnforced}   # each pass|fail|missing
TaskOrientation: taskId; knownFailureModes[{mode,evidenceRef}]; environmentFacts[]; preferredStrategies[]
  rejectedStrategies[{strategy,reason}]; successfulMigrations[]; predictiveEvals[{fixtureSet,caughtRegressions}]
PurposeTaskReceipt: id; runId; taskId; implementationVersion; runtimeClass; producedAt; answer
  servedSources[]; heldOutSources[{source,reason}]; conflictsDetected[]; evalSuite; lifecycleStage[baseline|canary|promoted]; rehydratable
CapabilityGraphEdge: fromTaskId; toTaskId; relation[depends_on|produces_event|consumes_event|validates|fallback_for|shares_system]; detail?
```

## 4. API surface
**Commands (POST → handler → policy → events).** `run-side-by-side` · `run-shadow` · `start-canary` · `expand-canary` · `pause-canary` · `reject-candidate` · `generate-candidate` (MOCK) · `request-approval` · `grant-approval` · `promote-candidate` · `rollback` · `freeze`. `promote-candidate` MUST NOT deploy: it creates a Promotion, runs the policy engine, sets `eligible|blocked`, and only on eligible+approved emits `Promoted` that the MOCK adapter applies to the model.
**Queries (GET, projections only, tenant-scoped):** registry · task detail · runs · candidates · scorecards · runtime-decisions · promotions · approvals · orientation · receipts · redteam · `/graph` · `/cost` · `/exec-summary` · `/customer/capabilities[/:id]`.
**Forbidden (must not exist):** any route writing `active_implementation`, `eval_score`, `success_criteria`, or bypassing the promotion gate.

## 5. Staff Console — Teleon Control Tower
Four **modes** (a view lens, not separate apps): **Monitor / Diagnose / Evolve / Govern**.
- **Capability Card (build first, shared):** three zones — *Stable* (purpose, I/O contract, allowed/forbidden caps, success criteria, connected systems) · *Current* (health, runtime, impl, eval score, cost/run, last run) · *Governed* (evidence, gates, promotion, rollback, approvals). Same data feeds the customer trust card via the allow-list.
- **Registry (Monitor):** a list of *capabilities*, not workers. Cols: task, purpose, owner, tenant, runtime, impl, health, eval, cost/run, failure rate, last promotion, open candidates, approval needed, risk, rollback. Filters: degraded, approval-required, candidate-active, runtime-class, tenant, owner, cost-spike, policy-blocker, source-handle-failure, held-out-leak-risk, redteam-failure.
- **Task detail:** purpose · contracts · caps · connected systems · success criteria · runtime policy · current impl · candidates · runtime-decision timeline · scorecards · evidence · orientation · promotions · rollback targets · gates · approvals · cost arbitrage · audit. Layout makes stable/variable/governed obvious.
- **Runtime Decision Timeline (Diagnose):** per run, why this runtime + which were rejected (tasks are born as purpose objects, not Lambdas/pods).
- **Candidate Lab (Evolve):** compare baseline+candidates across §8.1. Actions: side-by-side · shadow · canary · reject · request approval · promote · rollback · freeze. **Promote opens the Promotion Gate; never deploys.**
- **Promotion Gate (Govern):** render the Promotion — candidate/incumbent, reason, evidence deltas, gates (§8.2), `eligible|blocked`. If blocked, show exactly why ("loses source handles on 4% of runs; cost cannot override governance").
- **Self-Evolution Workbench:** the full loop Observe→Diagnose→Propose→Evaluate→Gate→Promote→Monitor→Rollback. Panels: Trigger · Diagnosis · Candidate generation (diff, template/skills/model, runtime binding, risk class) · Evaluation (scorecard, regression, shadow, redteam, cost/latency delta, blockers) · Decision. The system proposes; evidence + policy decide.
- **Capability Graph:** render edges; answer instantly — if this fails what breaks; if it changes what must be revalidated; if this source changes which tasks refresh; which touch customer data; which can write externally; which depend on browser workers; which lack redteam coverage; which are deterministic-hardening candidates.
- **Cost Arbitrage:** cascade path distribution + cost distribution + savings vs always-browser / always-LLM. Slogan: *Agents discover. Evals harden. Runtime router cheapens.*
- **Redteam panel:** coverage + overall; **missing coverage blocks promotion** (§8.2). Safety is an operational metric.

## 6. Customer Portal — Capability Assurance Portal (assurance, not observability)
**6.1 CustomerProjection allow-list (build FROM this; deny everything else).** INCLUDE: purpose; health; last-success/freshness; trust status + badges; data-access (reads/writes/never); receipts; their cost trend; pending approvals (human-readable); high-level change history; runtime *class* (not provider unless an `external_model_provider` boundary is approved). EXCLUDE (never present): candidate diffs; code/prompt/parser internals; raw traces/logs; other tenants; redteam internals (badge only); staff notes; raw model/tool ids; TaskOrientation internals (customer-safe explanations only).
- **Capability overview:** capability, purpose, connected systems, health, last success, freshness, trust, cost trend, approvals needed, last change.
- **Trust/Evidence card:** impl version · runtime class · last eval · source support % · policy status · pending approvals · rollback available · last promotion. (No Kubernetes knowledge required to understand trust.)
- **Data Access view:** Reads / Writes / Never-allowed — policy as a customer-facing trust feature.
- **Output Receipts (signature UX):** implement the **CFPB conflict pattern** — serve the supported answer, **hold out** the conflicting source, **preserve the receipt**, keep source handles. (e.g. answer "10 business days"; served = CFPB regulation page; held-out = FAQ saying 30 days; reason = conflict, policy-source priority; trust = source-supported, contradiction preserved.)
- **Trust badges (clickable, evidence-backed):** source-supported · schema-valid · policy-passing · receipt-attached · rollback-ready · human-approved · redteam-covered · fresh · degraded · approval-needed.
- **Approval queue (human-readable):** translate boundary requests to plain language ("Teleon wants permission to use browser automation… adds browser-worker for this task only; no new writes/sinks; cost may rise ≤$0.006/run; accuracy 87.2%→99.1%; redteam passed; rollback available. [Approve][Decline]"). Types map to `BoundaryChange.changeType`.

## 7. Lifecycle state machine (enforce server-side)
`Draft→Validated→Active→Healthy→Degraded→Diagnosing→CandidateGenerated→Evaluating→Shadowing→Canarying→PromotionBlocked→ApprovalRequired→Promoted→RolledBack→Retired`. Reject any action not allowed in the current state. Examples: **Degraded**→diagnose/run-regression/generate-candidate/freeze/escalate; **Canarying**→expand/pause/rollback/promote; **PromotionBlocked**→view-blockers/request-approval/reject/regenerate; **ApprovalRequired**→grant-approval/reject (no promote until approved). Expose state + allowed actions in the UI.

## 8. Policy & promotion logic
**8.1 Score dimensions:** correctness · source-handle coverage · lineage · receipt completeness · held-out preservation · tenant safety · latency · cost · reliability · observability · maintainability · UX clarity · redteam status.
**8.2 Blockers (any one blocks promotion — cost cannot override):** source-handle loss · held-out leak · tenant leak · purpose change (no approved BoundaryChange) · permission expansion (ditto) · success-criteria weakening · missing rollback · missing redteam coverage · failed output contract · failed regression · observability disabled.
**8.3 Eligibility (pure function in `packages/policy`):**
```python
def evaluate_promotion(candidate, incumbent, evidence, redteam, boundary_changes) -> PolicyResult:
    gates = {
      "outputContractPassed":       candidate.scorecard.regressionPassed and candidate.outputContractOK,
      "regressionPassed":           candidate.scorecard.regressionPassed,
      "successCriteriaNotWeakened": not weakens(candidate.successCriteria, incumbent.successCriteria),
      "noPermissionExpansion":      (not expands_permissions(candidate)) or approved(boundary_changes),
      "noSourceHandleLoss":         candidate.scorecard.sourceHandleCoverage >= incumbent.sourceHandleCoverage,
      "noHeldOutLeak":              candidate.scorecard.heldOutPreservation >= 1.0,
      "noTenantLeak":               candidate.scorecard.tenantSafety == "pass",
      "rollbackAvailable":          candidate.rollbackPlan is not None,
      "redteamCovered":             redteam.overall == "pass",
      "observabilityEnabled":       candidate.scorecard.observability == "pass",
      "approvalSatisfied":          all_required_approvals_granted(candidate, boundary_changes),
    }
    blockers = [human_readable(k) for k, ok in gates.items() if not ok]
    beats_incumbent = evidence.goldenAfter >= evidence.goldenBefore  # cost/latency must also not regress beyond policy
    return PolicyResult(gates=gates, blockers=blockers, eligible=(not blockers and beats_incumbent))
# Cost/latency improvements may NEVER flip a blocker to pass. (CI test asserts this — §Enforcement.)
```

## 9. Redteam suite (build TEST-FIRST; green from Phase 2). Each = an executable test; expected = blocked/redacted/enforced. Missing coverage blocks promotion.
1 self-promotion · 2 purpose mutation w/o approval · 3 permission expansion w/o approval · 4 success-criteria weakening · 5 truth served/promoted bypassing the gate · 6 baseline/rollback-target deletion · 7 UI/query route writing a truth field · 8 source-handle loss · 9 CustomerProjection contains staff-only fields or another tenant's data · 10 binding to a disallowed runtime class.

## 10. AuthZ / tenancy
Roles: staff_admin/operator/viewer, customer_admin/viewer. Customers call only `/api/customer/*` for their own `tenantId`. Scope every query+command at the handler/projection layer. Cross-tenant access → 403 (and redteam-fail if it leaks). BoundaryChanges carry `audience`; customer-facing ones route to the customer queue.

## 11. Seed fixtures (so every view has data)
Two tenants (`tenant-acme`, `tenant-globex`). Tasks: **sample-site-extractor** (degraded; impl v17 browser-worker; open candidate v18 parser+browser eligible for 5% canary; rejected v20 LLM-only that hallucinated prices; open BoundaryChange requesting browser automation); **cfpb-deadline-verifier** (healthy; v7 local-function; receipt with held-out FAQ; rejected v12 source-coverage too low); **invoice-extraction** (healthy; hybrid cascade; cost data 91.8% deterministic / 7.6% browser / 0.5% LLM / 0.1% human); **context-pack-optimizer**, **customer-risk-summarizer**, **browser-page-renderer** (graph nodes). Include runs, scorecards, runtime decisions, one blocked promotion (+reason), one task with **missing** redteam coverage (→ promotion blocked), and TaskOrientation entries that drive explanations ("chose browser fallback — this source renders results client-side"; "avoided OCR — previously rejected as too expensive/less accurate").

## 12. Phased plan (TaskCreate per phase; checkpoint after each)
- **P0 Foundations** — monorepo, types, event store, command/handler/projection skeleton, MOCK adapters, fixtures loaded. *DoD:* events persist; projections rebuild from log; fixtures load. **Checkpoint.**
- **P1 Monitor** — read API + Registry + Task Detail + Capability Card; customer stubbed. *DoD:* lists capabilities not workers; stable/variable/governed visible; **zero** UI truth-write paths. **Checkpoint.**
- **P2 Evolve+Govern** — Candidate Lab, Scorecards, Promotion Gate, lifecycle, policy engine + blockers, **redteam green**, **enforcement (Part D) wired**. *DoD:* blocked promotion shows exact blockers; cost never flips a gate (CI test green); redteam green; lifecycle enforced. **Checkpoint.**
- **P3 Operator depth** — Self-Evolution Workbench, Runtime Decision Timeline, Capability Graph, Cost Arbitrage. *DoD:* full loop visible; graph answers §5 questions; cost view shows cascade + savings. **Checkpoint.**
- **P4 Customer Assurance** — CustomerProjection (allow-list), trust/evidence card, data-access card, receipts (CFPB), human-readable approvals, change history, badges. *DoD:* projection has zero staff-only fields + no cross-tenant data (redteam #9 green); approvals are plain language. **Checkpoint.**
- **P5 Executive + hardening** — exec summary, audit completeness, full redteam green, a11y pass. *DoD:* §13 acceptance tests pass. **Final checkpoint.**

## 13. Global Definition of Done (all must hold)
Redteam green (missing coverage blocks promotion) · no UI/query route writes a truth field (test #7 + hook + CI) · CustomerProjection has zero staff-only fields and no cross-tenant data (#9) · a candidate with cost/latency wins but any governance blocker is **blocked** (the v18 source-handle test) · lifecycle actions enforced server-side · tenant isolation verified on all `/api/customer/*` · every output renders a receipt; every promotion carries evidence + rollback target.
**Exec view metrics:** active capabilities; healthy vs degraded; customer-impacting degradations; open boundary approvals; cost saved by arbitrage; agentic/browser runs avoided; promoted/rejected; avg eval; redteam coverage; rollbacks; time-to-repair; human-review load. **Headline KPIs:** *% of agentic tasks hardened into deterministic/cheaper cascades*; *mean time from degradation → safe candidate promotion*.

---

# PART D — Enforcement scaffolding (makes the invariants real)

> `CLAUDE.md` is context, not enforcement. These two mechanisms make the hard invariants impossible to violate. Ask Claude Code to wire the hook per the **current Claude Code hooks docs** (the settings shape evolves).

### D.1 PreToolUse hook — block dangerous edits before they're written
Create `.claude/hooks/guard.py`. It inspects proposed file writes/edits and **exits non-zero to block** when an edit would introduce a UI→truth write path or a real-cloud/real-LLM dependency. Register it as a **PreToolUse** hook for the Edit/Write tools in `.claude/settings.json`.

```python
#!/usr/bin/env python3
# PreToolUse guard for Teleon. Reads the tool-call payload from stdin (JSON), inspects the target
# path + proposed content, and exits non-zero (blocking) on a forbidden pattern.
import json, re, sys

payload = json.load(sys.stdin)
ti = payload.get("tool_input", {})
path = ti.get("file_path", "") or ti.get("path", "")
content = ti.get("content", "") or ti.get("new_string", "") or ""

FORBIDDEN = [
    # UI must never write truth fields:
    (r"apps/web/.*", r"(active_implementation|eval_score|success_criteria)\s*[:=]"),
    # No real cloud / real-LLM SDKs anywhere in this build:
    (r".*", r"\b(aws-sdk|@aws-sdk|boto3|googleapis|@google-cloud|azure-|kubernetes-client|@kubernetes)\b"),
    (r".*", r"\b(openai|@anthropic-ai/sdk|anthropic|cohere|@google/generative-ai)\b"),
    # No write route that mutates truth:
    (r"apps/(command-api|read-api)/.*", r"(PUT|PATCH).*(active_implementation|eval_score|success_criteria)"),
]
for path_re, bad_re in FORBIDDEN:
    if re.search(path_re, path) and re.search(bad_re, content):
        print(f"BLOCKED by Teleon guard: '{bad_re}' in {path}. "
              f"Redesign as command->event->projection or use the MOCK adapter. "
              f"See docs/teleon-spec.md §0/§2.", file=sys.stderr)
        sys.exit(2)   # non-zero blocks the tool call
sys.exit(0)
```
```jsonc
// .claude/settings.json (confirm exact shape against current Claude Code hooks docs)
{
  "hooks": {
    "PreToolUse": [
      { "matcher": "Edit|Write|MultiEdit",
        "hooks": [ { "type": "command", "command": "python3 .claude/hooks/guard.py" } ] }
    ]
  }
}
```

### D.2 CI gates — fail the merge on any invariant violation
Create `ci/checks.sh` (run in CI and locally). These are the rules that "would block a merge," so they live in CI, not just CLAUDE.md.
```bash
#!/usr/bin/env bash
set -euo pipefail

echo "1/4 No UI truth-writes…"
! grep -RinE "(active_implementation|eval_score|success_criteria)\s*[:=]" apps/web/src \
  || { echo "FAIL: UI writes a truth field"; exit 1; }

echo "2/4 No write routes that mutate truth…"
! grep -RinE "\.(put|patch)\(.*(active_implementation|eval_score|success_criteria)" apps \
  || { echo "FAIL: a route mutates a truth field"; exit 1; }

echo "3/4 Redteam suite green…"
pnpm vitest run packages/redteam           # all §9 attacks must pass (expected = blocked)

echo "4/4 Governance > cost, and projection isolation…"
pnpm vitest run -t "cost cannot override governance"   # candidate w/ cost win + blocker => blocked
pnpm vitest run -t "customer projection has no staff-only fields"
pnpm vitest run -t "customer projection has no cross-tenant data"

echo "All Teleon invariants hold."
```
Wire `ci/checks.sh` into the repo's CI (GitHub Actions / GitLab CI) as a required check on every PR.

---

> **Build thesis:** Teleon turns fragile cloud functions and Kubernetes workers into governed, self-improving capabilities. It shows what each capability is *for*, whether it still works, what is trying to replace it, why the runtime was chosen, what evidence supports promotion, what policy blocks unsafe change, and what humans must approve — and **the dashboard never owns truth.** The product enforces its promises with policy gates; this build enforces its own with a PreToolUse hook and CI.
