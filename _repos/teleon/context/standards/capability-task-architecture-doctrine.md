# CapabilityTask Architecture Doctrine — intent-native, eval-gated, self-adaptive compute

**Date:** 2026-06-06. **Status:** doctrine (the architectural constitution behind CTS + PurposeTask).
Companion to `_repos/shared-backend-components/docs/standards/open-capability-task-specification.md` (the standard) and
`_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md` (Baltor's reference runtime). PoC + CTS CTS-0
shipped (flywheel 317: `PurposeTaskSpec` is a conformant CapabilityTask; runtime-class vocabulary +
parallel-path promotion gate).

## The thesis
**Code should stop being the unit of cloud architecture. PURPOSE should become the unit.** Today we deploy a
function/container/worker/job and *hope* it still matches the business purpose months later. Instead, the stable
architectural object is the **CapabilityTask**: a declared, measurable, governed capability that can choose or
evolve its implementation. (Like Kubernetes' desired-state reconciliation — but the desired state is raised from
"these pods should exist" to "this business capability should keep meeting measurable success criteria.")

## The six-invariant killer design (each line is a separate control boundary)
1. **CapabilityTask stays stable** — purpose · interface · success criteria · permissions · governance are durable.
2. **Implementation evolves** — code · prompts · workflows · parsers · skills · tool sequences are replaceable candidates (a *portfolio*, not the identity).
3. **Runtime changes** — the task moves across runtime classes (function · container · job · worker · browser · workflow · GPU · edge) by policy/evidence, not a frozen Terraform decision.
4. **Evidence decides** — evals · traces · cost · latency · safety · shadow · canary determine promotion. *No candidate is promoted because an agent "thinks it fixed it."*
5. **Policy gates promotion** — no candidate may weaken success criteria, expand permissions, remove evals, or disable observability.
6. **Humans approve boundary expansion** — the system optimizes *inside* its box; only humans/external authority *redraw* the box.

## THE CORE INVARIANT (top of the spec)
> **A CapabilityTask may adapt its MEANS, but it may not autonomously change its ENDS.**
- **Means (autonomous, gated):** implementation · runtime · prompt · parser · workflow · retry · timeout ·
  fallback order · model · tool sequence.
- **Ends (human-approved only):** purpose · permissions · success criteria · data access · connected systems ·
  risk class · approval requirements.
This single distinction is the line between **self-healing** and **self-corrupting**. The policy engine must
REJECT any candidate that makes the task "easier" by weakening the contract (e.g. "accuracy is hard, lower the
threshold from 98%→85%" is forbidden; "DOM changed, add a selector and pass regression" is allowed).

## The three planes
- **Intent plane (stable):** CapabilityTask · CapabilityGraph · CapabilityPolicy · CapabilityEvalSuite ·
  CapabilityRuntimePolicy. *What should exist.*
- **Execution plane (replaceable):** functions · containers · K8s jobs · KEDA workers · Knative · Temporal ·
  browser/GPU/edge. *Runs the work* (reuse Score/OAM for workload description; add purpose+evals+adaptation above).
- **Evidence plane (the learning layer — most platforms lack it):** traces · metrics · logs · artifacts · evals
  · cost · latency · policy results · promotions · provenance. *Decides what changes.* This is what makes
  self-adaptation governable rather than magical.

## The object family
`CapabilityTask` (stable contract) · `CapabilityImplementation` (a candidate way to fulfill it) ·
`CapabilityRuntimeBinding` (task/impl → runtime) · `CapabilityEvalSuite` (golden/regression/adversarial/shadow/
human-rubric) · `CapabilityRun` (every execution record: input/output hash · impl · runtime · cost · latency ·
policy status · trace) · `CapabilityPromotion` (candidate vs incumbent + evidence + approvals + canary +
rollback) · `CapabilityBoundaryChange` (human-approved end-change) · `TaskOrientation/CapabilityMemory`
(STRUCTURED operational memory — known failure modes · successful/rejected strategies · runtime/cost history —
NOT mushy chat history).

## The lifecycle (explicit states)
Draft → Simulated → Validated → Shadow → Canary → Active → Degraded → Diagnosing → CandidateGenerated →
Evaluating → (Promoting | Rejected) → (Active | RolledBack). Degradation is detected against success_criteria;
diagnosis classifies the failure mode (source changed · schema/model drift · too slow · queue too deep · cost too
high · tool/permission/API failure); rollback is automatic on regression.

## The adaptation ladder (NOT all changes are equally risky — config artifact = next increment)
- **L0 runtime tuning** (timeout/memory/concurrency/retry/batch/cache TTL) — usually auto-promote with metrics.
- **L1 runtime rebind** (function→worker, job→workflow, browser→deterministic-parser, CPU→GPU) — cost/latency/reliability evals.
- **L2 configuration repair** (selector/endpoint/schema-map/prompt/parser patch) — regression + shadow.
- **L3 implementation candidate** (new code/workflow/model/tool sequence) — full eval + provenance + canary + rollback.
- **L4 capability decomposition** (split into validator/fallback/human-review tasks) — human approval.
- **L5 boundary expansion** (new data source/write permission/external domain/secret/destructive action/purpose) — ALWAYS human-approved.
*This ladder prevents treating "increase memory limit" and "add Salesforce write access" as the same change.*

## The capability compiler (the genuinely novel + hard part)
Input: CapabilityTask + templates + skills + connected systems + runtime inventory + historical traces + evals +
policy. Output: candidate implementations + runtime bindings + test plan + promotion plan + cost estimate + risk
class. It chooses the *shape* of work and assembles a **cascade** (e.g. cache → deterministic parser → browser
→ OCR → LLM → agentic investigation → human review), learning that ~90% of runs take the cheap deterministic
path and agents are reserved for discovery/repair/fallback. **This is the Determinism Factory at the cloud-task
layer** — the economic breakthrough (agents are expensive as the default runtime, powerful as discovery/repair).

## The control loop (a control system, not a chatbot)
`Observe → Diagnose → Propose → Evaluate → Gate → Promote → Monitor → Rollback`. Bounded controller proposes;
deterministic evaluator tests; policy engine gates; promotion controller rolls out gradually; humans approve
boundary changes. "Self-evolving code" is framed for enterprise as **eval-gated implementation evolution** —
every candidate is an artifact with provenance, every promotion has evidence, every boundary change has approval.

## Naming (carry through)
Standard = **Capability Task Specification (CTS)**, vendor-neutral (not named after Baltor). Baltor's
reference runtime = **PurposeTask**. Baltor's existing `CapabilityTask` (FleetLedger) = the LOWER execution
unit; CTS `CapabilityTask` = the higher purpose object ≡ PurposeTask. Product names sound powerful (Baltor
Capability Plane / Intent Runtime / Adaptive Compute); the standard sounds neutral.

## Manifesto
> Cloud architecture should be organized around durable, measurable **capabilities**, not around static
> deployments of code. *A CapabilityTask is a stable, governed, purpose-level contract whose implementations and
> runtimes may evolve through evidence-gated promotion under explicit policy boundaries.*

*Warrant: clear owner intent (an architecture doctrine for intent-native, eval-gated, self-adaptive compute).
Formalizes + is consistent with the shipped CTS CTS-0 + PurposeTask substrate; the core invariant (means/ends)
+ adaptation ladder are the governance backbone. Next concrete increments: encode the adaptation ladder
(L0–L5 + auto-promote-vs-human-approval) as a config artifact + proof; CTS CTS-1 (runtime-class → backend binding).*
