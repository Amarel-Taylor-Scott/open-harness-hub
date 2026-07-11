# Teleon — the Self-Improving Capability Runtime (the definitive account)

**Status:** synthesis / vision reconciliation, 2026-06-11. READ-ONLY sweep of all
`.research-notes/`, `_repos/shared-backend-components/docs/{strategy,concepts,codex,architecture}/`, and the Teleon
source surface (`_repos/teleon/backend/src/teleon/`, `_repos/shared-backend-components/scripts/teleon_local_runtime.py`,
`_repos/shared-backend-components/schemas/{workers,agents,runtime}/`). Every claim cites a path. This doc connects
scattered pieces into ONE story and flags, per stage, **what is BUILT vs DESIGNED
vs MISSING** — honestly. It does not change strategy; it reconciles it. Where it
asserts a brand/positioning sentence, that is owner-approvable, not owner-decided.

The owner's intuition that we "missed things" is **correct and specific**: the
capability→runtime **compiler now exists in code** (`_repos/teleon/backend/src/teleon/compiler/compile.py`,
`emit.py`, `_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json` — **untracked `??`** at the time of this
2026-06-11 synthesis, **since committed and tracked; this finding is RESOLVED (2026-07-03)**), but at
synthesis time **every doc, ledger entry, and rubric still said it was missing / "NEXT P2"** (`_repos/_shared/archive/legacy/docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md`
§"is Teleon the backbone yet?" → *"NO — about 40% of the substrate exists, and none
of the compiler"*; `.research-notes/autonomous-session-ledger.md` cont 5/6 →
*"P2 capability→runtime compiler (the Teleon backbone)"* as the NEXT item). The
self-improving-runtime story is now ~**75–80% built and ~40% documented**. That gap
*is* the thing we overlooked.

---

## 0. The vision, in the owner's words

> "Nobody programs a K8s or cloud function anymore; they describe the capability
> they want, the requirements, the benchmarks/evaluation systems, and it lives
> self-improving, self-running, all the time."

Mapped to the canon: this is **PurposeTask** — declared by INTENT, not code
(`_repos/teleon/backend/src/teleon/purpose_tasks/purpose_task.py` module docstring: *"A PurposeTask is
declared by INTENT, not code"*) — plus a **deterministic gate** (the eval/benchmark
IS the spec), plus a **compiler** to a runnable unit, plus a **governed
self-adaptation loop** (`_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md`).
The category line already exists: *"Serverless runs code. Kubernetes runs workloads.
**Teleon runs purpose.**"* (`_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md`).

The discipline that keeps "self-rewriting production infra" from being reckless is
three standing laws, carried in every workflow:
- **Agents PROPOSE; the gate DISPOSES** (`purpose_task.py`, `experiments/path_promotion.py`).
- **Distillation is never replacement** — preserve raw + lineage + held-out +
  rollback (`_repos/shared-backend-components/docs/codex/lossless-distillation.md`).
- **Self-improve from VERIFIED outcomes only** — the Determinism Factory principle
  (`_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md`; memory
  [[determinism-factory-distill-from-verified]]).

---

## A. The end-to-end lifecycle — stage by stage, mapped to REAL repo pieces

A capability's life is ten stages. Honesty tag per stage: **BUILT** (real code +
self-test), **DESIGNED** (doc/spec, no/partial code), **MISSING** (neither, or only
a sequenced plan).

```
 (1) INTENT      → (2) SPEC = requirements+evals → (3) BUILD (model proposes, reuses
 substrate) → (4) GATE (lift+durability+train/holdout) → (5) COMPILE to a runtime unit
 → (6) DEPLOY+RUN (scale-to-zero, FleetLedger) → (7) OBSERVE (receipts/OTel/evidence)
 → (8) DIAGNOSE → (9) TUNE/ADAPT (adaptation ladder) → (10) RE-GATE+RE-PROMOTE
        ↘──────────────── DISTILL (LLM behavior → deterministic rules) ───────────────↗
```

### Stage 1 — Intent / contract intake (PurposeTask / CapabilityTask) — **BUILT (controller) + DESIGNED (intake queue)**
- A `PurposeTaskSpec` declares purpose · `input_contract` · `output_contract` ·
  `connected_to` (the blast radius) · `success_criteria` (MEASURABLE) ·
  `promotion_criteria` · `allowed_runtime_classes` (vendor-neutral) · `safety_class`
  · `tenant_scope` (`_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md` §"What
  a PurposeTask is").
- `CapabilityTask` is the durable-ledger row (`_repos/shared-backend-components/schemas/workers/CapabilityTask.schema.json`):
  `task_id, tenant_id, capability_id, required_resource_class, sla_policy_id,
  max_attempts, …`. **PurposeTask = product language; CapabilityTask = the formal/spec
  name** (`_repos/shared-backend-components/docs/strategy/teleon-baltor-openhubforai-portfolio.md` §Vocabulary).
- **BUILT:** the controller surface `provision()` binds an impl FOR a capability_slot
  by NUMERIC priority FROM a registry — *"no per-task wiring code"* (`purpose_task.py::provision`).
- **GAP (DESIGNED→MISSING):** there is **no running intake queue** that takes a fresh
  intent → queues a build attempt. The rubric names it: *"Intent intake = PurposeTask
  contracts queued → build attempts → gate → registry of promoted runtimes"*
  (`_repos/_shared/archive/legacy/docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md` step 4) — that
  queue does not exist yet. The fleet ledger (`enqueue_task`) is task-execution, not
  capability-build intake.

### Stage 2 — Requirements + benchmarks/evals AS the spec — **BUILT (gate suite + declared `eval_suite` field) + DESIGNED (named-suite registry)**
The owner's "the benchmark IS the spec" is realized as `success_criteria` +
`promotion_criteria` that a variant must beat — and, since 2026-06-11, as a declared
`eval_suite` field the user hands to Teleon (see `_repos/shared-backend-components/docs/architecture/eval-as-contract.md`).
The two expressions are converging (see Gap D-2):
- The live runtime hardcodes per-capability example suites with a real
  train/holdout split (`_repos/shared-backend-components/scripts/teleon_local_runtime.py`, `CAPABILITIES` + `_suite`).
- **RESOLVED (2026-06-11):** `PurposeTaskSpec` + `CapabilityTask` now carry a
  first-class, validated **`eval_suite`** (inline `examples` XOR `benchmark_ref`,
  `gate_threshold`/`holdout_policy` single-sourced from `teleon_local_runtime`
  PROMOTE_AT/TRAIN_PARITY, judge). The runtime-gate seam
  (`src.teleon.purpose_tasks.eval_suite_for` → `eval_pairs`) is built + proven
  (`_repos/shared-backend-components/scripts/check_eval_suite_contract.py`); flipping the live gate to read it and the
  named-suite registry are the remaining follow-ups. The Stage-2 confirm tool that
  binds here exists (`_repos/shared-backend-components/scripts/eval/measured_lift_headtohead.py`,
  paired/held-out/separate-judge — per M4 in `_repos/_shared/codex/north-star.md`) but is still
  **not wired into promotion** (`capability-rubric-and-deep-dive-2026-06-11.md` step 3).

### Stage 3 — Capability BUILD (model proposes, reusing the substrate) — **BUILT (model-built path + digestion) + DESIGNED (open-ended synthesis)**
- The live runtime's `mode="model"` path makes **the MODEL perform the capability**
  per example, with **one self-refine round** when the gate isn't cleared, both
  attempts receipted (`_repos/shared-backend-components/scripts/teleon_local_runtime.py::_run_to_completion`).
- Reuse feeds the build (full detail in §C): the **Shared Template Registry**
  renders CANDIDATE shapes only (`_repos/teleon/backend/src/teleon/templates/instantiator.py`,
  `CANDIDATE_STATUS=200`); **skills are digested** into a cheaper runtime candidate
  with the original kept as fallback (`_repos/teleon/backend/src/teleon/digestion/digester.py::digest_skill`,
  `RUNTIME_CASCADE = [cache, deterministic, browser, llm, human]`); **imported
  workloads** are lifted to PurposeTask/CapabilityTask drafts
  (`_repos/teleon/backend/src/teleon/lift/pipeline.py::lift_workload`).
- **HONEST CAVEAT (the rubric flags it):** *"'model-BUILT capabilities' overstates
  (spec is hardcoded; refined instruction discarded)"*
  (`capability-rubric-and-deep-dive-2026-06-11.md` §Requirements fit). The build is
  real but constrained to a fixed capability set; there is no open-ended "synthesize
  a brand-new capability from an arbitrary intent" builder yet.

### Stage 4 — Deterministic GATE (lift + durability + train/holdout) — **BUILT (both halves) — the strongest part of the system**
Two gates, both real and both forgery-resistant:
1. **The runtime promotion gate** (`_repos/shared-backend-components/scripts/teleon_local_runtime.py`): promotion
   requires **BOTH** the train and the holdout pass-rate ≥ `PROMOTE_AT=0.90`; the
   self-refine prompt may quote failed TRAIN inputs but **never any expected output**
   (`_refined_instruction`), and an **answer-key-parrot regression test** proves the
   old gate promoted 4/4 by copying the key and the new one rolls back. This is the
   de-contamination the 2026-06-11 fix wave landed (ledger cont 4:
   *"teleon gate DE-CONTAMINATED"*).
2. **The side-by-side promotion gate** for adaptation
   (`_repos/teleon/backend/src/teleon/experiments/path_promotion.py::decide`): a candidate promotes ONLY if
   **all seven gates** pass — `same_input ∧ same_output_contract ∧ output_equivalent ∧
   source_handles_preserved ∧ held_out_not_leaked ∧ safety_ok ∧ cost_acceptable` — and
   `is_promote_authorized()` **re-derives** the gates from the decision's own fields so
   a "schema-valid forgery" (label says promote, gates false) yields no serve.
   `rollback_target` is ALWAYS the baseline (a promotion is always reversible).
- **Durability** (the second admission axis) is the capability-valleys theory:
  admit on lift AND structural durability (`_repos/shared-backend-components/docs/concepts/capability-valleys.md`;
  single source `_repos/shared-backend-components/scripts/eval/reason_codes.py`; sorter
  `_repos/shared-backend-components/scripts/eval/durable_gap_harness.py`). **GAP:** durability gating is enforced for
  *corpus/component* intake, but is **not yet wired into the PurposeTask/runtime
  promotion path** — a promoted runtime is gated on lift+train/holdout, not on a
  durability_class. (Connecting them is a clean, named next step.)

### Stage 5 — COMPILE to a runtime unit (the "new compiler") — **BUILT (pure compile + emit); COMMITTED + tracked as of 2026-07-03 (was UNTRACKED at the 2026-06-11 synthesis)**
This is the headline finding. **The compiler exists** and is faithful to every law:
- `_repos/teleon/backend/src/teleon/compiler/compile.py::compile_capability` — PURE + DETERMINISTIC (same
  inputs incl. `now` → byte-identical `unit_id`); **THE LAW: only a `status ==
  "promoted"` capability compiles** (else `NotPromotedError`); **no magic values**
  (runtime_class→backend reuses `purpose_tasks/runtime_binding.bind_allowed`; resources
  from `_repos/shared-backend-components/architecture/worker_resource_classes.json`; budgets from the SLA policy +
  OIPS `budget_policy` + the task's `max_attempts`; image from
  `_repos/shared-backend-components/architecture/deploy_topology.json`); **lossless** (`unit` carries `capability_id`,
  `capability_version`, the binding decision, `gate_evidence`, `receipt_refs`,
  `rollback_target`); **honest** (`is_truth: False`).
- `_repos/teleon/backend/src/teleon/compiler/emit.py` renders ONE unit to **all three deployable shapes**
  so a capability is never cloud-locked: `emit_fly_machine` (Fly Machines JSON),
  `emit_k8s_job` (a `batch/v1` **Job** — bounded work, `backoffLimit` from the gate's
  retry ceiling, `activeDeadlineSeconds`/`ttl` from the budget), `emit_local_process`
  (always-available offline). Every emitter stamps **OTel attrs** onto env/labels/
  annotations and **never writes a secret value** — only secret-ref names.
- Contract: `_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json` (registered shape).
- `EXEC_TARGETS = ("fly_machine", "k8s_job", "local_process")`; `RUNNER_MODULE =
  "scripts.teleon_local_runtime"` (the unit's argv = `-m` that module + the capability id).
- **The owner's exact sentence is now answerable YES in code:** *"take contracts/
  intents/capabilities and automatically build out efficient more deterministic K8
  runtimes or cloud functions using appropriate standardization and logging tools"* —
  the standardization is the single-source resource/SLA/budget joins, the logging is
  the OTel attrs on every unit. (`capability-rubric-and-deep-dive-2026-06-11.md` posed
  this as unanswered; the compiler closes it.)
- **GAPS (the documentation/wiring debt):** (a) the module + schema were **untracked
  `??`** at synthesis time — **now committed and tracked (2026-07-03), resolving the rubric contradiction**;
  (b) **no proof script** (`_repos/shared-backend-components/scripts/check_*capability_compil*` does not exist — only
  the in-module fixtures `_repos/teleon/backend/src/teleon/compiler/fixtures.py`); (c) **no CLI** wired
  (`_repos/shared-backend-components/scripts/teleon_local_runtime.py --run-capability` is referenced as the unit's
  argv but the compiler itself has no `python3 -m … --compile` entrypoint registered);
  (d) nothing **persists** the compiled unit to the FleetLedger as a versioned
  rollbackable runtime row (Stage 6's promised "registry of promoted runtimes").

### Stage 6 — DEPLOY + RUN (scale-to-zero, FleetLedger) — **BUILT (ledger + local execution + topology compiler) + DESIGNED (compiled-unit → live machine)**
- `runtime_binding.bind` / `bind_allowed` (`_repos/teleon/backend/src/teleon/purpose_tasks/runtime_binding.py`)
  is **CTS-1**: bind a declared abstract runtime **class** to a concrete backend by
  policy + credentials + provider health — *cloud-defer-only-after-local-equivalent*.
  The vocabulary (`_repos/shared-backend-components/architecture/capability_runtime_classes.json`) maps **every K8s/
  cloud shape to a BUILT local equivalent**: `cloud-function`→`local_function_emulator`,
  `kubernetes-job`→`local_job_emulator`, `kubernetes-worker`/`queue-worker`/`gpu-worker`/
  `browser-worker`→`local_worker_pool`, `durable-workflow`→`local_job_emulator`, etc.
  **Capability never blocks on missing cloud** (`archive/legacy/docs/architecture/cts-1-runtime-class-binding.md`).
- The **execution backend selector** (`_repos/teleon/backend/src/teleon/runtime/execution_backend_selector.py`)
  picks local↔k8s↔cloud-function **by policy/pricebook/health, not code**, with **hard
  guards** keeping browser/GPU/open-ended/control-plane work off generic cloud
  functions unless a policy override asserts a proof.
- The **durable FleetLedger** (`_repos/teleon/backend/src/teleon/workers/durable_fleet_ledger.py`) is the
  cross-process SQLite truth: atomic `claim_task` via `BEGIN IMMEDIATE` (the SQLite
  analog of `FOR UPDATE SKIP LOCKED`), leases, idempotency, dependency ordering. The
  flywheel operating model is *lightweight control plane always-on; expensive workers
  scale-to-zero* (`_repos/baltor/context/architecture/durable-runtime-plan.md`; memory
  [[flywheel-operating-model]]).
- The **deploy topology generator** is already a *working deterministic compiler* at
  the per-SERVICE plane (`_repos/shared-backend-components/scripts/deploy/generate_provider_configs.py`: declarative
  JSON → fly.toml/k8s/compose, drift-gated — verified TRUE in
  `_repos/shared-backend-components/docs/status/full-verification-sweep-2026-06-11.md` claim 1). The new
  per-CAPABILITY compiler is the same pattern one level down.
- **GAP:** nothing actually launches a CompiledRuntimeUnit onto a Fly Machine / K8s
  Job in production — all cloud vendors are `@candidate` cards, never imported/executed
  (`_repos/teleon/backend/src/teleon/runtime/capability_binding.py::TARGETS`). The local-process path is the
  only ACTIVE execution. Real-cloud activation is owner-gated by design.

### Stage 7 — OBSERVE (receipts, OTel, evidence ledger) — **BUILT (receipts) + DESIGNED (one envelope + OTel transport)**
- Every model call mints a **ModelInvocationReceipt** with `is_truth:false` and an
  **allowed-use ladder** (`blocked < draft < non_serving_explanation < candidate <
  promotable < served`; the gateway never emits `served` — Baltor governs serving)
  (`_repos/teleon/backend/src/teleon/inference/oips.py`, `ALLOWED_USE_ORDER`). Receipts persist to ONE
  durable JSONL sink, **hashes/metadata only**, raw prompts/keys scrubbed
  (`_repos/teleon/backend/src/teleon/inference/receipts.py`, `_FORBIDDEN_RECEIPT_KEYS`).
- The runtime's per-example **receipts** carry input/output/expected hashes, the
  train/holdout split, pass/fail, duration, and the run's gate evidence
  (`_repos/shared-backend-components/scripts/teleon_local_runtime.py::_suite`, persisted to `receipts.jsonl`).
- The compiled unit carries **OTel `service.name/version`, `capability.id/version`,
  `trace_id/span_id`** attrs (`compiler/compile.py::_otel_attrs`).
- **GAP (the rubric's headline observability finding):** there are **FOUR model-call
  planes and four receipt shapes; only OIPS mints receipts**; none is yet a single
  OTel-emitting envelope on the wire (`capability-rubric-and-deep-dive-2026-06-11.md`
  §model plane; step 2). The 2026-06-11 fix wave made `ChatRoute` a shim over OIPS
  (ledger cont 4), but the *one receipt envelope + :9426 projection + OTel transport*
  is still sequenced, not done.

### Stage 8 — DIAGNOSE (what failed, why) — **BUILT (drift detection) + DESIGNED (agent self-diagnosis)**
- `purpose_task.py::evaluate_health` deterministically checks a hot-path result vs
  `success_criteria` and returns `{meets, drift:[dims]}` — drift dims are `error`,
  `cost`, `source_handles`, `held_out_leak`. `run_current_guarded` converts a crashing
  or non-compliant handler into a **structured DRIFT** result (never a fabricated
  success), so a broken impl trips `meets=False`.
- **GAP:** the *agent self-diagnosis* step ("read telemetry → propose the RIGHT
  variant: new handler / decomposition / backend / skill") is DESIGNED
  (`purpose-task-self-adapting-execution.md` §self-adaptation loop, "self-diagnose
  (agent) → PROPOSE variant") but the proposer is a stub — `adapt()` simply tries the
  *next pre-registered alternative* (`spec["alternatives"][0]`), it does not yet
  GENERATE a new candidate from a template/skill in response to the specific drift.

### Stage 9 — TUNE / ADAPT (the adaptation ladder; self-improve from VERIFIED only) — **BUILT (ladder classifier + side-by-side adapt) + DESIGNED (variant generation)**
- `purpose_task.py::adapt` runs the next candidate **SIDE-BY-SIDE** vs the current
  impl through the Parallel-Path Engine (`experiments/parallel_paths.run_parallel` —
  baseline + candidates on the IDENTICAL `input_snapshot`, `input_snapshot_hash`
  proves it, **a candidate is NEVER served**) and promotes ONLY on a passing
  `PathPromotionDecision`, keeping the prior impl as a fallback (rollback_target).
- The **risk-tiered ADAPTATION LADDER** (`purpose_tasks/adaptation_ladder.py` over
  `_repos/shared-backend-components/architecture/capability_adaptation_ladder.json`) decides what may auto-promote.
  This is the precise encoding of "self-tuning without going rogue":
  - **L0 runtime_tuning** (timeout/memory/concurrency/retry/batch/cache patches) — `gate=auto_on_metrics`, auto.
  - **L1 runtime_rebind** (function↔K8s shape switch) — `gate=cost_latency_reliability_evals`, auto.
  - **L2 config_repair** (selector/parser/prompt/schema-map patches) — `gate=regression_plus_shadow`, auto.
  - **L3 implementation_candidate** (generate candidate / model swap within allowed) — `gate=full_eval_provenance_canary_rollback`, auto.
  - **L4 capability_decomposition** (add validator/fallback/human-review task) — **human**.
  - **L5 boundary_expansion** (change purpose/permissions/connected systems/secrets/model provider/risk) — **human**.
  - **CORE INVARIANT:** a task may adapt its **MEANS (L0–L3, auto if the gate passes)**
    but may NEVER autonomously change its **ENDS (L5, always human)** or make a
    `forbidden_autonomous` change — `success_criteria.weaken, eval_suite.remove,
    observability.disable, rollback.remove, regression_test.remove, source_handle.drop,
    tenant_isolation.change`. **Deny-by-default:** an unknown change type → L5/human.
- "Improve from VERIFIED outcomes only" is the Determinism-Factory principle stated in
  `purpose-task-self-adapting-execution.md` (*"an out-of-band evolution loop spends
  intelligence ONCE … proves it side-by-side, and promotes it only if it wins"*),
  upheld by lossless distillation (`_repos/shared-backend-components/docs/codex/lossless-distillation.md`).
- **GAP:** same as Stage 8 — the ladder + side-by-side + rollback are BUILT; the piece
  that *generates the L2/L3 candidate to feed them* is the DESIGNED-not-built proposer.

### Stage 10 — RE-GATE + RE-PROMOTE (versioned, rollbackable) — **BUILT**
- `purpose_task.py::rollback` reverts to any preserved target and **demotes (never
  deletes)** the regressed impl to the front of `alternatives` — lossless and
  re-promotable; fails CLOSED (never blanks `current_impl_id`).
- The live runtime reserves and commits **monotonic, contiguous, race-free versions**
  per capability (`teleon_local_runtime.py::submit_run` version reservation; concurrency
  self-test proves no double-bump). Demotion to `candidate`/`rolled-back` is a real
  status transition persisted to disk.

### DISTILL (LLM behavior → deterministic rules over time) — **BUILT (skill digestion) + DESIGNED (M0→M8 facts lane)**
- `_repos/teleon/backend/src/teleon/digestion/digester.py` parses a SKILL.md (parse-only, never executes),
  **extracts deterministic substeps**, and builds a **cheaper runtime candidate** down
  the `RUNTIME_CASCADE` (cache→deterministic→browser→llm→human) **with the original kept
  as fallback** and a `proof_to_promote` ladder (sandbox + eval + redteam). Unsafe
  skills (secret reads/exfil) are **quarantined**. This is "LLM→deterministic rule"
  done losslessly.
- **GAP:** the broader Determinism-Factory **M0→M8 distillation lane** that converts
  *stable verified LLM decisions* into deterministic rules (the consumption path's
  reconciliation, per `_repos/baltor/context/architecture/consumption-runtime.md` + memory
  [[determinism-factory-distill-from-verified]]) is DESIGNED as a sequenced lane after
  the compiler, not yet a running subsystem.

### How each "self-*" property is realized (the crux table)

| Self-property | Realized by | Status |
|---|---|---|
| **self-programming** | model performs/refines the capability + reuse of templates/skills/imported workloads → candidate impls | BUILT (constrained set) / DESIGNED (open-ended synthesis) |
| **self-diagnosing** | `evaluate_health` drift dims + guarded hot path turns crashes into drift | BUILT (detection) / DESIGNED (agent proposer) |
| **self-tuning** | adaptation ladder L0–L2 auto (`auto_on_metrics` / `regression_plus_shadow`) | BUILT (classifier+gate) / DESIGNED (variant generation) |
| **self-improving** | side-by-side `adapt` → 7-gate `path_promotion` → versioned promote, prior kept as rollback | BUILT |
| **self-running, all the time** | scale-to-zero FleetLedger control plane + local-equivalent fallback so nothing blocks | BUILT (local) / DESIGNED (live-cloud launch of compiled units) |
| **describe-don't-program** | PurposeTask/CapabilityTask intent contract + runtime-class vocabulary (vendor-neutral) | BUILT (contract+binding) / MISSING (intake queue + eval-as-declared-spec) |

---

## B. The self-improvement loop — how it tunes itself WITHOUT drifting

The loop (`_repos/teleon/context/architecture/purpose-task-self-adapting-execution.md` §self-adaptation):

```
run (cheap, deterministic hot path; NO LLM) → telemetry → meets success_criteria?
  └ yes → keep running
  └ no (drift: site changed / cost spike / fail-rate up)
       → self-diagnose → PROPOSE variant → generate from TEMPLATE
       → run SIDE-BY-SIDE vs current impl (same input snapshot)
       → score on dimensions → meets promotion_criteria (hard gates + better)?
            ├ yes → PROMOTE variant to hot path; keep prior impl as fallback; receipt
            └ no  → keep current impl; record learning; escalate to human if repeated
```

Six mechanisms keep it from drifting — each is a real artifact:

1. **Evals/benchmarks are the fitness function.** Promotion is decided by
   `success_criteria` + `promotion_criteria`, not by the proposer's confidence. The
   runtime's fitness is the **train+holdout pass-rate**; the adaptation engine's
   fitness is the **7 hard gates** (`path_promotion.GATES`). "It's green" is necessary,
   not sufficient — the gate checks the *warrant* (`_repos/shared-backend-components/docs/codex/change-verification-contract.md`).
2. **Distill from VERIFIED only.** A candidate is judged on real runs against the
   held-out set; the self-refine prompt is **leak-controlled** (no expected output
   ever enters a prompt — `_refined_instruction`), and the **answer-key-parrot
   regression test** is the standing proof the gate can't be gamed by parroting.
3. **Held-out guards against gaming.** Even/odd parity split: even-index examples are
   TRAIN (inputs may be shown), odd-index are HOLDOUT (never shown in ANY prompt);
   promotion needs BOTH splits ≥ 0.90 (`teleon_local_runtime.py`,
   `_example_split`/`_split_rates`). At the adaptation layer, `held_out_not_leaked`
   is one of the 7 gates and `same_input` is the *first* gate (a candidate that didn't
   provably run on the baseline's input is never promotable —
   `experiments/parallel_paths.py` refuses a divergent `input_snapshot_hash` at the input).
4. **Rollback targets always exist.** `path_promotion.decide` sets `rollback_target =
   baseline_path_id` on EVERY decision (there is no branch that omits it);
   `purpose_task.rollback` demotes-not-deletes; the compiled unit carries a
   `rollback_target` (predecessor unit). Promotion is *always* reversible.
5. **Promotion/demotion of versions is monotonic + lossless.** Versions reserve
   contiguously and never double-bump under concurrency; a regressed impl is demoted
   to `alternatives`, re-promotable through the gate — never erased
   (`lossless-distillation.md`: *"Superseded version ≠ prior version deleted"*).
6. **MEANS-auto / ENDS-human / forbidden-never.** The adaptation ladder is the
   anti-drift backbone: the system can cheapen/repair/re-implement itself (L0–L3) but
   can NEVER autonomously widen its purpose, permissions, data class, or weaken its own
   evals/observability/rollback (`adaptation_ladder.py` + the ladder JSON's
   `ends_change_types` + `forbidden_autonomous`). Deny-by-default on unknowns.

**Net:** the loop is safe *because adaptation is out-of-band, gated, proven
side-by-side, rollback-ready, lossless, and human-gated for ends-changes* — not
because the proposer is trusted. (`purpose-task-self-adapting-execution.md` §"Honest
framing": robustness comes from the gates, not magic.)

---

## C. Reuse & composition — local components + imported frameworks feed the build

The owner's "reusable templates LOCALLY + imported, frameworks from other systems"
maps onto a **discovery≠trust** funnel: everything imported enters as a **CANDIDATE**
behind a port and must pass a gate before it can serve.

### The seven-primitive model composes a capability
Everything reduces to **seven primitives** extending one shell
(`_repos/shared-backend-components/scripts/primitives/base.py::Primitive`, contract `run(po)->po`):
**Input · Knowledge Corpus · If Statement · Action · Loop · Stop/End · Output**
(`_repos/shared-backend-components/docs/concepts/component-taxonomy-and-stages.md`). Product vocabulary is enforced:
**Knowledge Corpus** (not "knowledge pack"), **If Statement** (not "rule pack"),
**Action** (a persona/tool/processor/harness/rubric is an Action). A capability is a
left-to-right arrangement of these primitives; the compiler's job is to turn the
promoted arrangement into a runtime unit.

### Local reusable substrate (BUILT)
- **Shared Template Registry** — a 14-section canonical shell + mixins; the
  instantiator renders **CANDIDATE** shapes only (`_repos/teleon/backend/src/teleon/templates/instantiator.py`,
  `CANDIDATE_STATUS=200`, `_ACTIVE_STATUS=400`; memory [[shared-template-registry]]).
  Generated objects are never born active.
- **Component / subcomponent registry** — the ⟦computed: 2,678⟧-component substrate
  (`build_component_id_index.py --check-fresh`); pre-LLM / LLM / post-LLM / runtime
  components are the building blocks (`CLAUDE.md` North Star).
- **Knowledge Corpus / context packs** — facts with a `retrieval` trigger (keyword/
  regex/rag/exact-id/classifier/graph), static or dynamic, governed by Baltor
  (`component-taxonomy-and-stages.md` §Knowledge Corpus; OpenHubForAI supplies
  reference context, *"reference context is not served truth — Baltor governs it"* —
  `teleon-baltor-openhubforai-portfolio.md`).
- **Pipelines** — orchestrated DAGs (the Loop primitive); the showcase pipelines and
  the agentic-RAG shapes mined in `.research-notes/stream-7/stream-9` are the catalog
  seed (deep-research, self-RAG, CRAG, GraphRAG, ToT, Reflexion, STORM, SWE-agent…).

### Imported "frameworks from other systems" — governed as CANDIDATES (BUILT intake, never trusted)
- **Skills → deterministic runtimes** via the digester (§A DISTILL): a SKILL.md is
  parsed (never executed), its deterministic substeps extracted, a cheaper runtime
  candidate built with the original as fallback (`digestion/digester.py`).
- **Imported workloads** (a provider-native cloud function, a cron) → PurposeTask +
  CapabilityTask drafts with the imported baseline as the **rollback target**
  (`_repos/teleon/backend/src/teleon/lift/pipeline.py::lift_workload`; `RuntimeProfile` built ONLY from
  supplied telemetry, never fabricated).
- **Wrap-candidate adapters** (the owner's "ktx, litellm, etc.") live in
  `catalog/adapters/` and as catalog rows admitted 2026-06-11 (ledger cont 2): **ktx
  ×3, litellm, zep-graphiti, reducto, exa, firecrawl, recall-ai, deepeval, ijfw ×2,
  hud** — all `experimental`, `candidate`/`wrap` tags, *"lift PENDING stated in every
  description (discovery ≠ trust)"* (`archive/legacy/docs/strategy/yc-context-landscape-2026-06.md`).
  Binding targets (Nitric/Score/Temporal/Knative/KEDA/Kratix) are **candidate cards
  only — never imported/executed/reached** (`runtime/capability_binding.py::TARGETS`).
- **RAG/eval framework primitives** (LangChain/LlamaIndex/Haystack/DSPy; lm-eval/
  promptfoo/Ragas/garak) are *referenced/adapted, not imported* — generate an adapter,
  don't depend (`.research-notes/stream-3`, `stream-5`). DSPy's teleprompters and
  Reflexion's verbal-memory loop are the closest external analogs to our adaptation
  loop — but ours is **evidence-gated + receipted + rollbackable**, theirs is not.

### The composition rule
Local templates + Knowledge Corpus + imported candidates feed Stage 3 (BUILD); the
seven primitives are the grammar; the gate (Stage 4) is the only door to active; the
compiler (Stage 5) turns the promoted composition into a portable runtime unit. **One
governed object, two doors** (OHH free funnel + the governed live layer — memory
[[two-services-ohh-and-ceaas]]).

---

## D. What we MISSED / gaps, contradictions, and the competitive read

### D-1. The compiler exists but the whole record said it doesn't — **RESOLVED 2026-07-03 (now committed)**
`_repos/teleon/backend/src/teleon/compiler/{compile,emit,fixtures}.py` + `_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json`
were **untracked `??`** and absent from `.research-notes/autonomous-session-ledger.md` at the 2026-06-11
synthesis, while `_repos/_shared/archive/legacy/docs/architecture/capability-rubric-and-deep-dive-2026-06-11.md` and the ledger
(cont 5/6) still called the compiler **"none of the compiler"** / **"NEXT P2"**. **RESOLVED (2026-07-03):**
the compiler modules + schema are **now committed and tracked** (the schema at
`_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json`); the positioning and the
narrative have caught up. **Remaining action:**
add a proof script (`_repos/shared-backend-components/scripts/check_capability_runtime_compiler.py`), update
the rubric's "is Teleon the backbone yet?" verdict from *"NO — ~40%"* toward *"the
compiler now exists; what remains is intake + live launch + one receipt envelope"*,
and add the ledger entry. (Owner-gated where outward-facing.)

### D-2. The "benchmark/eval IS the spec" promise as a declared contract field — **FIELD BUILT 2026-06-11; live-gate wire-in + named-suite registry remain**
The vision is "describe the requirements, the benchmarks/evaluation systems." A
first-class **`eval_suite`** field now exists on `PurposeTaskSpec` AND
`CapabilityTask.schema.json` (inline `examples` XOR `benchmark_ref`,
`gate_threshold`/`holdout_policy` single-sourced from `teleon_local_runtime`, judge;
`_repos/shared-backend-components/docs/architecture/eval-as-contract.md`, proof `_repos/shared-backend-components/scripts/check_eval_suite_contract.py`).
A user **can now hand Teleon the evaluation system** as a declared, validated input
(inline suites are end-to-end usable). The remaining work: (1) flip the live runtime
gate to read `eval_suite_for(spec)` instead of the hardcoded `CAPABILITIES[...]`
suite (the seam is built — a one-line source swap, documented); (2) a persistent
named-suite registry so `benchmark_ref` resolves from a store (the honest resolver
seam exists; it raises `BenchmarkNotRegisteredError` until then — never a fabricated
suite); (3) wire the separate Stage-2 scorer (`measured_lift_headtohead.py`) to the
declared judge/threshold so its paired/held-out lift gates promotion
(`capability-rubric-and-deep-dive-2026-06-11.md` step 3).

### D-3. The self-PROGRAMMING proposer is a stub
`adapt()` tries the *next pre-registered alternative*; it does not generate a new
variant from a template/skill in response to the diagnosed drift (Stages 8–9 GAP). The
"model proposes a fix" arrow is DESIGNED, not built. Without it, "self-improving" means
"selects among pre-built alternatives," not "writes a better one."

### D-4. Intent intake queue + live-cloud launch are missing
No queue takes a fresh intent → build attempt (Stage 1 GAP), and no path launches a
CompiledRuntimeUnit onto a real Fly Machine / K8s Job (Stage 6 GAP — all cloud is
`@candidate`). The loop is fully real **locally**; "lives self-running all the time in
the cloud" is the unbuilt mile.

### D-5. Durability gate is not wired into runtime promotion
Capability-valleys durability (`reason_codes.py`/`durable_gap_harness.py`) gates
corpus/component intake but not the PurposeTask/runtime promotion path (Stage 4 GAP).
The two-axis "lift AND durable" admission is half-applied at the runtime layer.

### D-6. Observability is fragmented (rubric's own headline)
FOUR model-call planes, four receipt shapes, only OIPS mints receipts; no single
OTel-on-the-wire envelope yet (Stage 7 GAP). The compiler already emits OTel attrs, so
the unit side is ready and the transport side is the lag.

### D-7. A migration-leftover contradiction (small but real)
`_repos/teleon/backend/src/teleon/workers/durable_fleet_ledger.py` line 1 still says
`"""src.baltor.workers.durable_fleet_ledger …"""` and honors `BALTOR_DURABLE_DB` —
a stale header from the Baltor→Teleon extraction (the law file's `migration_status`,
`portfolio-dependency-law`). Functionally fine, but a doc-claims-a-past-state
contradiction the change-verification contract says to reconcile in the same change.
(Same pattern: `path_promotion.py`/`parallel_paths.py` correctly note their Baltor
re-export shim — those are intended, not stale.)

### D-8. Two "this is the capstone, build it LAST" vs "it now exists" timing tension
`purpose-task-self-adapting-execution.md` and memory
[[cloud-task-self-adapting-execution]] frame PurposeTask self-adaptation as the
**capstone to build LAST**, after Parallel-Path + template-factory + skill-graph. But
PurposeTask, the ladder, the side-by-side engine, AND now the compiler are all built,
while the *proposer* and *intake* (earlier in the dependency order) are not. The build
order inverted: we built the safe capstone scaffolding before the risky generative
middle. Not wrong — but the docs imply a sequence reality contradicts.

### Competitive read — who is closest, and how Teleon differs
The defensible white space holds and now has a clock (`yc-context-landscape-2026-06.md`:
*"No YC company (through W26) does continuous verification + portable signed receipts +
governed promotion of context to truth status"*). On the **self-programming-runtime**
axis specifically:

- **CodeStrap X-Reason** (memory [[codestrap-x-reason-competitor]]) is the **closest
  thesis-foil**: NL → Solver → Programmer → Evaluator that **compiles canonical XState
  machines** ("LLMs as deterministic programmers"), durable/observable, Palantir-Foundry
  coupled, services-led. It **validates** the determinism thesis. **Teleon goes
  further:** evidence-GATED promotion + 7-gate side-by-side + rollback-as-contract +
  the governed context layer (Baltor) + provider-neutrality. *They orchestrate work; we
  govern what the work is allowed to claim, and we only promote a variant that beats a
  held-out gate.* Treat their NL→DSL→compiled-machine pattern as an **adapter candidate
  for PurposeTask compilation**, never a second ledger.
- **Respan (fka Keywords AI)** — *"self-driving" obs+evals+gateway that lets the loop
  fix itself* — is the **foil to name**: *agents dispose; no receipts*. Teleon's line:
  *"self-driving loops fix themselves; governed loops PROVE themselves."*
- **Mastra / Trigger.dev / Hatchet / Temporal / DBOS / Inngest** — runtime/durable-
  workflow frameworks. **Teleon sits ABOVE them:** each is a `runtime_class` vendor
  candidate / `ExecutionProviderPort` behind the binding; the receipts+gates plane works
  over any (`yc-context-landscape-2026-06.md` action 2; runtime_classes vocabulary lists
  `temporal@candidate`, `hatchet@candidate`, `inngest@candidate`, `dapr_workflow@candidate`).
- **Composio ("skills that evolve") / IJFW ("dream-cycle" memory promotion)** — *ungoverned*
  capability evolution; IJFW's memory pruning **violates our lossless law** (clean
  differentiation line); its "receipts" are cost telemetry, not evidence
  (`yc-context-landscape-2026-06.md` §IJFW).
- **Airbyte / ktx / Mem0 / Zep** — movement / SQL-shape / memory, not gated
  self-improvement. *"Trusted SQL shape ≠ verified facts"; "memory is what agents
  believe; Baltor is what's verified."*

**No competitor does deterministic + receipted + eval-gated + rollbackable
self-improvement of a runtime unit.** That specific quadruple is the moat — and it is
mostly BUILT, which is the under-told story.

---

## E. The crisp positioning — owner-approvable

**One-liner (extends the existing category line):**
> **Serverless runs code. Kubernetes runs workloads. Teleon runs purpose — and keeps
> it correct.** You describe the capability, its requirements, and the evals that prove
> it; Teleon builds it, gates it on a held-out benchmark, compiles it to a runtime unit
> (Fly Machine / K8s Job / local), runs it scale-to-zero, and improves it from verified
> outcomes — every change proven side-by-side and rollback-ready, ends-changes always
> human-gated.

**The differentiated sentence (vs the field):**
> Everyone is building self-driving agent loops. Teleon is the only one where the loop
> **proves itself instead of trusting itself**: deterministic hot path, evidence-gated
> promotion, signed receipts, and a rollback target on every version — the loop can
> cheapen, repair, and re-implement its MEANS automatically, but can never widen its
> ENDS or weaken its own evals.

**The honest internal sentence (for the team, not the market):**
> The safe scaffolding is built — PurposeTask, the adaptation ladder, the side-by-side
> 7-gate promotion, the train/holdout runtime gate, and (newly committed 2026-07-03) the
> capability→runtime compiler. What remains to make the vision real: the eval-as-declared-
> contract field, the variant-generating proposer, the intent intake queue, live-cloud
> launch of compiled units, and one OTel receipt envelope. We are ~75% of the way to
> "describe it and it lives self-improving," and ~40% of the way to *saying* so.

---

## Appendix — primary sources cited
Source (BUILT): `_repos/teleon/backend/src/teleon/purpose_tasks/{purpose_task,adaptation_ladder,runtime_binding,projections}.py` ·
`_repos/teleon/backend/src/teleon/compiler/{compile,emit,fixtures}.py` (COMMITTED 2026-07-03) · `_repos/shared-backend-components/schemas/runtime/CompiledRuntimeUnit.schema.json` (COMMITTED 2026-07-03) ·
`_repos/teleon/backend/src/teleon/experiments/{parallel_paths,path_promotion}.py` · `_repos/teleon/backend/src/teleon/runtime/{execution_backend_selector,capability_binding}.py` ·
`_repos/teleon/backend/src/teleon/workers/durable_fleet_ledger.py` · `_repos/teleon/backend/src/teleon/templates/instantiator.py` · `_repos/teleon/backend/src/teleon/digestion/digester.py` ·
`_repos/teleon/backend/src/teleon/lift/pipeline.py` · `_repos/teleon/backend/src/teleon/inference/{oips,receipts}.py` · `_repos/teleon/backend/src/teleon/agent_gateway/gateway.py` ·
`_repos/shared-backend-components/scripts/teleon_local_runtime.py` · `_repos/shared-backend-components/architecture/{capability_adaptation_ladder,capability_runtime_classes}.json` ·
`_repos/shared-backend-components/schemas/workers/CapabilityTask.schema.json`.
Docs: `_repos/shared-backend-components/docs/strategy/{teleon-baltor-openhubforai-portfolio,north-stars,yc-context-landscape-2026-06}.md` ·
`_repos/shared-backend-components/docs/concepts/{component-taxonomy-and-stages,capability-valleys}.md` ·
`_repos/shared-backend-components/docs/codex/{master-goal,north-star,lossless-distillation,change-verification-contract}.md` ·
`_repos/shared-backend-components/docs/architecture/{purpose-task-self-adapting-execution,cts-1-runtime-class-binding,consumption-runtime,durable-runtime-plan,flexible-inference-lanes,capability-rubric-and-deep-dive-2026-06-11}.md` ·
`_repos/shared-backend-components/docs/status/full-verification-sweep-2026-06-11.md` · `.research-notes/{autonomous-session-ledger,stream-3,stream-5,stream-7,stream-9}.md`.
Memory: [[determinism-factory-distill-from-verified]] · [[codestrap-x-reason-competitor]] · [[teleon-competitive-landscape]] ·
[[shared-template-registry]] · [[flywheel-operating-model]] · [[two-services-ohh-and-ceaas]] · [[cloud-task-self-adapting-execution]].
