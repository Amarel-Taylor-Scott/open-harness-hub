# Capability Task Specification (CTS) — a portable standard for autonomous-but-bounded cloud work

**Date:** 2026-06-06. **Status:** vision / draft standard (v0.1). **Owner intent:** create an **industry
standard** — not a Baltor product — for provisioning workers and cloud functions **by purpose/capability, not
by code**, where the task contract is the stable architectural object and cloud functions / K8s workers / jobs /
queues / browser workers / agents / workflows are interchangeable implementations.

> **Positioning (load-bearing): the standard is NOT named after Baltor.** Like OpenTelemetry / CloudEvents /
> OCI won adoption by being neutral, CTS must be vendor-neutral and built ON the CNCF/Linux-Foundation
> ecosystem, not competing with it. **Baltor is the best *reference implementation*** of CTS (its
> `PurposeTask` runtime), and the standard's existence makes Baltor's governed substrate the obvious conformant
> engine. The open spec lives (proposed) at `capabilitytasks.io` / `github.com/capabilitytasks/spec`.

> **Naming-layer reconciliation (avoid the collision in this repo):**
> - CTS **`kind: CapabilityTask`** = the higher-level **governed purpose object** (purpose + evals + adaptation
>   + runtime policy). Baltor's reference implementation of it is **`PurposeTask`** (`PurposeTaskSpec.v1`,
>   built — flywheel 316). *Also avoids Google Cloud Tasks; that's why Baltor's product noun is PurposeTask.*
> - Baltor's existing **`CapabilityTask.v1`** (FleetLedger) = the **lower execution-level unit** a worker
>   atomically claims to run ONE invocation. It is the substrate a `PurposeTask`/CTS `CapabilityTask` dispatches
>   onto — a different layer, not a rename. Both coexist; the docs/specs must always say which layer they mean.

## The inversion (the gap)
```
Current cloud:   code → runtime → deploy → monitor → manual DevOps adjustment
Capability Task: purpose → contract → runtime SELECTION → implementation CANDIDATE
                 → measured execution → EVAL-GATED adaptation → promotion / rollback
```
Existing systems cover scaling, orchestration, reconciliation, and skills — but **none** makes a governed task
object where **purpose, evals, evolution policy, and runtime choice are primary.** That is the missing layer.

## Sit ABOVE existing infra, don't replace it
```
Capability Task Specification
  → Task control plane (scheduler · evaluator · policy · runtime router)
  → Runtime adapters
  → Lambda / Cloud Run / Knative / K8s Jobs / KEDA / Temporal / Dapr / Argo / browser / GPU / edge
```
K8s, Knative, Cloud Run, KEDA, Temporal, Dapr, Argo, cloud functions all remain — CTS decides **which, when,
why, and under what success criteria.** Adoption is feasible *because* it demands no rip-and-replace; it gives a
common **intent layer.**

## Reuse existing standards (the novel layer stays small)
| Need | Reuse | CTS adds |
|---|---|---|
| I/O + HTTP contracts | JSON Schema · OpenAPI | task input/output + HTTP trigger contracts |
| Event interface | CloudEvents · AsyncAPI | standard task-lifecycle events |
| Workflow shape | CNCF Serverless Workflow | sub-workflow inside a task |
| Telemetry | OpenTelemetry (+ GenAI semconv) | task/adaptation/eval semantic attributes |
| Artifacts/packaging | OCI | portable task packages (contract+evals+impls+policies) |
| Provenance | SLSA · in-toto | how a candidate impl was generated/built |
| Registry | xRegistry | registry of tasks/schemas/events/runtimes/capabilities/policies |
| Workload portability | Score · OAM | + purpose · success-criteria · evals · adaptation · eval-gated runtime selection |
| Policy | OPA/Rego · CEL · K8s-admission-style | gates on task EVOLUTION (not just deploy) |
| API objects + reconcile | Kubernetes CRDs / operators | a purpose/capability object above workloads |

## The CapabilityTask object (17 metadata sections)
identity · purpose (summary/intent/nonGoals) · interface (input/output/error schemas + idempotency) · triggers
(http/event/schedule via CloudEvents) · capabilities (required/optional/**forbidden** — provision by declared
capability, not code) · connectedSystems (blast radius + access + approvalRequired) · resources (templates/
skills/knowledge/fixtures, as OCI/skill refs) · runtimePolicy (allowedRuntimeClasses + optimizer objectives +
escalationRules) · successCriteria (correctness/perf/reliability/safety, hard vs soft) · evaluations (golden/
regression/liveShadow) · adaptation (allowed/forbidden changes + diagnosisTriggers + candidatePolicy) ·
promotion (eval-gated-canary + rollback) · observability (OTel + retained artifacts) · provenance (SLSA/in-toto)
· security/governance (PolicyGates) · status (activeImplementation/runtimeClass/lastEvalScore/health) ·
relationships (the **capability graph**: produces/consumes/dependsOn/validatesWith/fallbackTo).

## Abstract runtime classes (vendor-neutral; vendors map them)
`edge-function · cloud-function · serverless-container · cloud-run-job · kubernetes-job · kubernetes-worker ·
queue-worker · durable-workflow · browser-worker · gpu-worker · batch-job · cron-task · stream-processor`.
Mappings (examples): cloud-function → Lambda/GCF/Azure-Functions; serverless-container → Cloud Run/Knative/ACA;
queue-worker → KEDA ScaledObject/ECS/Deployment; batch-job → K8s Job/Cloud Run Job/AWS Batch/Kueue;
durable-workflow → Temporal/Dapr/Inngest/Hatchet/Argo. The contract declares the CLASS; the platform binds.

## The five layers
1. **Contract** — human+machine-readable declaration (reuse JSON Schema/OpenAPI/CloudEvents/xRegistry).
2. **Runtime binding** — allowedRuntimeClasses + per-platform adapters (portable, like Score/OAM but with purpose+evals).
3. **Evaluation** — *what "working" means* (the part cloud platforms lack). No promotion unless a candidate beats
   the incumbent on golden+regression+shadow+canary+security+cost+latency+policy. CI/CD asks "did it build/deploy?";
   CTS asks "is the capability still meeting its purpose, is there a better impl, can it prove itself before promotion?"
4. **Adaptation** — bounded **TaskOrientation** memory (knownFailureModes · environmentFacts · preferred/rejected
   strategies) + the loop: detect → classify → propose candidate → offline evals → shadow → canary → promote-if-policy
   → rollback. Record what/why/evidence/tests/runtime/permissions/approver/rollback (SLSA-style provenance).
5. **Governance** — `PolicyGate` objects (CEL/OPA/admission-style) that a self-adapting task CANNOT bypass.

## Conformance tiers
- **CTS-0** read/validate the contract · **CTS-1** bind to ≥1 runtime class · **CTS-2** emit standard telemetry +
  run records · **CTS-3** eval-gated promotion (candidate+regression+shadow+canary+rollback) · **CTS-4** automatic
  runtime optimization (move across classes) · **CTS-5** bounded self-adaptation (propose+test impl changes,
  gated) · **CTS-6** cross-platform portability (a task moves between Baltor/K8s/AWS/GCP/Azure/Cloudflare/Temporal
  preserving contract+evals+policy+observability) — the industry-standard target.

## Lifecycle events (CloudEvents) + telemetry (OTel)
Events: `capabilitytask.{created,updated,run.started,run.completed,run.failed,evaluation.started,
evaluation.completed,candidate.created,candidate.rejected,candidate.promoted,runtime.rebound,policy.violation,
rollback.completed}`. OTel attrs: `capability.task.{name,version,purpose_hash,input_schema,output_schema,
runtime_class,implementation_id,candidate_id,eval_suite,eval_score,cost_usd,success_criteria.passed,
policy.passed,adaptation.reason,promotion.stage}` (+ reuse OTel GenAI semconv for LLM/tool calls inside a task).

## OCI package layout (portable task)
`<task>/{capabilitytask.yaml, schemas/{input,output,error}.schema.json, evals/{golden,regression}.jsonl +
scorer.yaml, policies/*.rego, resources/{skills,templates}.lock, implementations/{current,candidates}/,
examples/, provenance/attestation.intoto.jsonl}` → publish as `oci://…/capabilitytasks/<task>:<version>`.

## The killer feature — task-to-runtime arbitrage + agent→code hardening
A platform learns e.g. "92% of runs work with a cheap HTTP parser, 8% need browser, 0.5% need LLM" → runs a
**cascade** (cheap deterministic → browser fallback → LLM fallback → human review). A task can **start agentic**
(an agent discovers HOW) → a **compiler hardens stable behavior into deterministic code** → evals validate → the
runtime router moves it to cheaper compute → the agent remains only for diagnosis + rare fallback. **This is the
Determinism Factory applied at the cloud-task layer** — the path to lower cost + higher reliability, and the
exact middle ground between unbounded agents and static CI/CD.

## The philosophical boundary (self-healing vs self-corrupting)
**A Capability Task MAY self-adapt its IMPLEMENTATION, but MUST NOT self-amend its purpose, permissions, success
criteria, or governance policy without external approval.** Allowed: improve parser/selector/prompt · change
runtime · tune retry/timeout · switch model · generate an implementation candidate. Forbidden without approval:
change purpose · expand scope/permissions · add a secret/external system/domain · weaken accuracy thresholds ·
remove tests · destructive actions · send data elsewhere. This single rule keeps adaptation safe.

## Four kinds of intelligence (keep them separate)
**Selection** (which runtime/model/tool/impl) · **Diagnostic** (why it failed) · **Generative** (a candidate
patch/impl) · **Governance** (promote/rollback/escalate/ask-human — mostly deterministic policy+metrics, not vibes).

## How Baltor implements it first (reference implementation = PurposeTask)
Baltor already has the substrate: `PurposeTaskSpec.v1` + PoC (governed purpose object) · the cloud-agnostic
**execution-backend selector** (runtime binding) · the **Parallel-Path Engine** (side-by-side + eval-gated
promotion + rollback) · the durable **CapabilityTask.v1**/FleetLedger (execution units) · numeric provider graph
· measured-lift eval gate. **Phases:** (1) publish the spec (JSON Schema + OpenAPI controller API + AsyncAPI/
CloudEvents events + OTel attrs + OCI layout); (2) K8s CRDs (CapabilityTask/Implementation/Run/Evaluation/
Promotion/RuntimeClass); (3) runtime adapters (K8s Job → KEDA → Knative → Cloud Run → Lambda → Temporal →
browser); (4) **the eval harness** (more important than the generation engine); (5) **bounded** self-adaptation
(start with runtime-rebind/retry/timeout/selector/parser/model-fallback/cache — NOT full rewrite). Drive
adoption via CNCF Sandbox / CD Foundation / CloudEvents-Serverless WG alignment + conformance tests + adapters
for existing tools (Actions/Argo/Temporal/Dapr/Knative/KEDA/Cloud Run/Lambda/Modal/n8n/Trigger.dev).

## Honest read (assurance-brand discipline)
The *technical* design is sound and Baltor can build the reference impl on its existing substrate. The HARD parts
are: (a) **adoption/standardization is a multi-year political effort** — a spec without conformant runtimes +
a registry + adapters is a PDF nobody uses; lead with the working reference impl, not the committee; (b) **the
eval harness is the real moat** (and the hardest engineering) — "what does working mean" per task is where most
of the value and difficulty live; (c) the **agent→deterministic-code compiler** is genuinely novel and genuinely
hard (correctness + provenance). Frame "10,000× / new cloud service" as ambition; the robustness is the gates.

*Warrant: clear owner intent (create an industry standard for purpose/capability-provisioned, self-adapting
cloud work). Vendor-neutral, built on CNCF/LF standards; Baltor = reference implementation (PurposeTask), not the
namesake. Reconciles the CapabilityTask naming across layers (purpose object vs execution unit). Self-adapt
implementation, never purpose/permissions/criteria/policy without approval. Build spec:
prompts/baltor-open-capability-task-standard.md.*
