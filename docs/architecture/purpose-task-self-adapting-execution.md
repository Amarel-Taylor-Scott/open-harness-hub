# PurposeTask — purpose-driven, self-adapting execution units

**Date:** 2026-06-06. **Status:** vision + architecture (build spec: `prompts/baltor-purpose-task-self-adapting.md`).
**Owner intent:** abstract cloud functions and cloud/K8s workers into **Purpose-Driven PurposeTasks** so the
system declares *what work to do and how to know it's good*, then **self-manages and self-adapts** — switching
execution shape (function ↔ K8s worker) and improving its own implementation when it stops meeting success
criteria — **without a human DevOps CI/CD cycle**, and **without** paying full-agent token costs on every run.

## The gap PurposeTask fills

| | Flexibility | Cost / latency | Determinism | Safety for prod effects | Adapts to change |
|---|---|---|---|---|---|
| **Unbounded AI agent** | high | **expensive** (tokens every run) | low | low | yes, but unsafely |
| **Traditional CI/CD** | low | cheap at runtime | high | high | **slow** (human cycle) |
| **/skill /tool call** | medium | **token-heavy per call** | medium | medium | no |
| **PurposeTask** | high | **cheap deterministic hot path** | high | high (gated) | **yes — governed self-evolution out-of-band** |

The insight: **keep the hot path cheap and deterministic; move the intelligence out-of-band.** A PurposeTask
runs as compiled/templated code (no LLM in the hot path). When telemetry shows it no longer meets its success
criteria, an *out-of-band* evolution loop spends intelligence ONCE to produce a better deterministic variant,
proves it side-by-side, and promotes it only if it wins — exactly the **Determinism Factory** principle applied
to cloud execution units. Adaptation cost is amortized across thousands of cheap runs.

## What a PurposeTask is (declared by intent)
```
PurposeTaskSpec
  task_id:            purpose_tasks.pull_sample_info@v1
  purpose:            "Go to sample.com and pull down X information."
  input_contract:     X            # e.g. SampleQuery
  output_contract:    Y            # e.g. SampleRecord
  connected_to:       [systems/consumers that depend on Y]   # the blast radius
  success_criteria:   Z            # MEASURABLE thresholds: correctness, freshness, cost ceiling,
                                   #   latency SLA, source-handle coverage, safety = 0 leaks
  promotion_criteria: [I, J, K]    # what a MODIFIED variant must beat to replace the current impl
  resources:          {templates, skill_slots, capability_slots, provider_graph}  # what it may draw on
  safety_class:       ...          # gates required (human approval for real cloud / write effects)
  tenant_scope:       ...
  execution_policy:   <- ExecutionProviderPort (function | k8s_worker | k8s_job | local; switchable)
  current_impl:       <- a generated worker (template factory) running behind WorkerAppContract
  alternatives:       [previous impls kept as fallbacks]      # wrapped redundancy
```

## How it composes the existing substrate (NOT a new framework)
PurposeTask is a thin declarative + controller layer over proven pieces — it invents no second runtime/ledger/
registry:

| PurposeTask concern | Reused substrate |
|---|---|
| *what to do* (intent + I/O) | `CapabilityTask` + `WorkerAppSpec` (template factory) |
| *how it runs / shape-switching (function ↔ K8s)* | **`ExecutionProviderPort` + execution_backend_selector** (cloud-agnostic, policy/pricebook/health-driven, switchable side-by-side) |
| *lifecycle / logging / telemetry / resources* | **BaseWorkerApp** + WorkerLifecycleSpec + JSON-logging + telemetry-DB + ResourceManagerPort (worker-template factory) |
| *is it still good?* (success criteria) | telemetry vs `success_criteria` thresholds (observability layer) |
| *self-diagnose + propose a better variant* | agent PROPOSES (path_reviewer / Determinism Factory) — never promotes |
| *prove the variant side-by-side* | **Parallel-Path Engine** (baseline vs candidate on same input snapshot) |
| *rate it across dimensions* | the rating rubric (correctness · fidelity · cost · runtime · safety · UX) |
| *promote only if it wins; keep original* | the **promotion gate** + wrapped-redundancy (baseline preserved as fallback) |
| *where do new building blocks come from* | the **SkillGraph RAG** + template factory (Resources) |
| *truth + receipts + lineage* | the governance spine (no-truth-bypass, receipts, promotion boundary) |

So: **PurposeTask = CapabilityTask (intent) + ExecutionProviderPort (shape) + WorkerAppContract (lifecycle) +
Parallel-Path rating/promotion (self-evolution) + success/promotion criteria (governance).**

## The self-adaptation loop (governed — NOT unbounded self-rewrite)
```
run (cheap, deterministic) ──► telemetry ──► meets success_criteria? ──yes──► keep running
                                                  │ no (drift: site changed, cost spike, fail-rate up)
                                                  ▼
   self-diagnose (agent) ──► PROPOSE variant (new handler / decomposition / backend / skill)
        ──► generate from TEMPLATE ──► run SIDE-BY-SIDE vs current impl (same input snapshot)
        ──► score on dimensions ──► meets promotion_criteria (hard gates + better)? 
              ├─ yes ──► PROMOTE variant to hot path; keep prior impl as fallback alternative; receipt
              └─ no  ──► keep current impl; record learning; (escalate to human if repeatedly failing)
```
This includes **switching execution shape**: if telemetry shows a function hitting timeout/cold-start limits,
the selector can propose a K8s-worker variant; the variant must still win the side-by-side before it's promoted.

## Why this is robust (the safety story — what makes "self-adapting code" not reckless)
The strength is **not** that code rewrites itself freely — it's that **every adaptation passes the same gates**:
- **Agents PROPOSE; the promotion gate DISPOSES.** No variant reaches the hot path without winning side-by-side.
- **Hard gates are non-negotiable:** correctness · output-contract fidelity · source-handles · held-out-not-leaked
  · tenant isolation · no-truth-bypass. A cheaper/faster variant that fails any hard gate is rejected, period.
- **Original always preserved** as a fallback alternative (wrapped redundancy) → instant rollback.
- **Real cloud / write-effect activation requires human approval**; local-emulator-first (cloud-defer-only-
  after-local-equivalent). Generated variants run in sandbox first; redteam must pass.
- **Receipts + lineage** on every promotion: who proposed, what it beat, on what evidence, rollback target.
- **Bounded blast radius:** `connected_to` makes consumers explicit; a PurposeTask can't silently change output
  shape for systems depending on it (output_contract is stable across variants).

## Honest framing of the strong claims
"10,000× more robust" and "an entirely new cloud service" are the right *direction*, stated as ambition, not a
measured fact. Grounded: PurposeTask is a **powerful unifying abstraction layered over existing cloud primitives
+ Baltor's governance** — it is not a new cloud provider, and the robustness comes from the gates, not magic.
Self-modifying production infrastructure is inherently high-risk; this design is defensible *only because*
adaptation is out-of-band, gated, proven side-by-side, rollback-ready, and human-approved for real-cloud/write
effects. Per the assurance-brand discipline: claim what the proofs show.

## Relationship to the build queue
PurposeTask is the **capstone** that sits on top of, and depends on, the queued subsystems — build them first,
then PurposeTask composes them:
1. Parallel-Path Engine (building now) — the side-by-side + promotion core.
2. K8s/Cloud-Function Template Factory — generates the worker variants + enforces lifecycle/logging/telemetry/resources.
3. Path Improvement + Skill Intake Factory + SkillGraph RAG — where better variants/skills come from + how they're rated.
4. **PurposeTask** — the declarative purpose-driven layer + the self-adaptation controller that orchestrates all of the above.

*Warrant: clear owner intent (purpose-driven self-adapting PurposeTask abstraction). Composes proven substrate
(ExecutionProviderPort, worker-template factory, Parallel-Path Engine, SkillGraph) under the governance spine;
invents no second runtime/ledger/registry. Self-adaptation is governed (propose→side-by-side→promote-if-criteria
→keep-original→human-approval-for-real-cloud), never unbounded self-rewrite. Strong claims framed as ambition,
not measured fact.*
