# /workflows /baltor-open-capability-task-standard (STAGED — Baltor as the reference implementation of CTS)

Build Baltor's **reference implementation** of the **Capability Task Specification (CTS)** — the
vendor-neutral standard for purpose/capability-provisioned, eval-gated, self-adapting cloud work. Spec/vision:
`docs/standards/open-capability-task-specification.md`. **The standard is NOT named after Baltor** (adoption
requires neutrality, like OTel/CloudEvents/OCI); Baltor's conformant runtime is **PurposeTask**.

> **Naming layers (do not conflate):** CTS `kind: CapabilityTask` (governed PURPOSE object) ≡ Baltor
> **`PurposeTask`** (reference impl; `PurposeTaskSpec` built). Baltor's existing **`CapabilityTask`**
> (FleetLedger) is the LOWER execution unit a worker claims — the substrate a PurposeTask dispatches onto.
> **Build on the existing substrate; no second runtime/ledger/registry.** Focused increments; never concurrent
> with another repo-mutating workflow. Lead with the working reference impl, not a committee — a spec without a
> conformant runtime + registry + adapters is a PDF nobody uses.

## CTS IMPLEMENTATION CLAUSE (carry in the North Star loop)
Baltor implements CTS conformance: a CapabilityTask is the stable contract (purpose · I/O · capabilities ·
connected-systems · success_criteria · runtime classes · evals · adaptation · promotion · provenance ·
governance); the implementation/runtime are interchangeable behind it. Promotion is eval-gated (golden +
regression + shadow + canary + policy); a task may self-adapt its IMPLEMENTATION but NEVER its purpose/
permissions/success-criteria/governance without external approval. Standard ≠ Baltor namesake; Baltor = best
conformant runtime.

## Phases (each = JSON/code/proof/docs together; map to existing substrate)
- **P1 — Spec artifacts (CTS-0):** finalize `schemas/purpose_tasks/PurposeTaskSpec` as the conformant
  `CapabilityTask` contract (add the CTS sections it lacks: triggers · capabilities{required/optional/forbidden}
  · connectedSystems · runtimePolicy.allowedRuntimeClasses · evaluations · adaptation · promotion · provenance ·
  governance.policyGates). Add `architecture/capability_runtime_classes.json` (the abstract runtime-class
  vocabulary + vendor mappings — distinct from execution_backend_pricebook; it's the layer ABOVE backends).
  Proof `check_octs_contract_conformance` (a PurposeTaskSpec validates as a CTS CapabilityTask; required
  fields present; forbidden-capability + governance.policyGates honored).
- **P2 — Runtime binding (CTS-1):** map allowedRuntimeClasses → the existing **execution-backend selector**
  (cloud-agnostic, local-emulator-first). Proof `check_octs_runtime_binding` (a class binds to a concrete backend
  by policy; missing-cloud → local fallback; class→backend mapping is config, not code).
- **P3 — Observed execution (CTS-2):** emit the CloudEvents lifecycle events + OTel `capability.task.*` attrs +
  a `TaskRun` record (task·impl·runtimeClass·input/output hash·status·latency·cost·evalResult·traceRef). Reuse
  the observability layer. Proof `check_octs_taskrun_telemetry`.
- **P4 — Eval-gated promotion (CTS-3):** wire PurposeTask adaptation through the **Parallel-Path Engine**
  (already built) — candidate must beat incumbent on golden+regression+shadow+canary+policy before promotion;
  rollback recorded. Proof `check_octs_eval_gated_promotion` (already largely covered by check_purpose_task_poc;
  extend with shadow/canary records).
- **P5 — Runtime optimization (CTS-4):** the task moves across runtime classes (function→job→worker) by
  telemetry/cost, each move winning a side-by-side + recording a BackendDecision. Proof `check_octs_runtime_optimization`.
- **P6 — Bounded self-adaptation (CTS-5):** start SAFE (runtime-rebind · retry/timeout tune · selector/parser
  repair · model fallback · cache) via propose→evals→canary→gate; agents PROPOSE, never amend purpose/permissions/
  criteria/policy. Proof `check_octs_bounded_self_adaptation` + redteam `check_octs_self_corrupt_redteam` (every
  purpose/permission/criteria/policy self-amendment FAILS; promotion-without-eval FAILS; new-domain/secret/system
  without approval FAILS).
- **P7 — Portability (CTS-6) + conformance tests:** publish JSON Schema + OpenAPI(controller) + AsyncAPI/
  CloudEvents + OTel semconv + OCI task-package layout; a conformance test suite; (later) K8s CRDs +
  runtime adapters (K8s Job/KEDA/Knative/Cloud Run/Lambda/Temporal/browser); drive CNCF Sandbox / CD Foundation
  alignment.

## Acceptance
A PurposeTaskSpec is CTS-conformant (CapabilityTask contract) · runtime classes bind to backends by policy ·
TaskRuns emit standard events+telemetry · promotion is eval-gated via the Parallel-Path Engine · runtime
optimization moves a task across classes on evidence · bounded self-adaptation works + the self-corrupt redteam
fails safely · conformance tests + OCI package layout exist · offline demo + flywheel GREEN.

*Warrant: clear owner intent (create an industry standard; Baltor = best implementation). Builds on
PurposeTaskSpec + execution selector + Parallel-Path Engine + FleetLedger CapabilityTask units; reuses CNCF/LF
standards; self-adapt implementation, never purpose/permissions/criteria/policy without approval. The eval
harness is the real moat; lead with the reference impl, not the committee.*
