# Teleon Capability Runtime Compiler — promoted capability → deployable runtime unit

**Date:** 2026-06-11. **Status:** built + self-tested (PoC of the backbone; see "What's still demo vs product").
**Code:** `src/teleon/compiler/` · **Schema:** `schemas/runtime/CompiledRuntimeUnit.schema.json` ·
**CLI:** `python -m src.teleon.compiler`.

**Owner intent (the backbone call):** *"Teleon… take contracts/intents/capabilities and automatically build out
efficient, more deterministic K8 runtimes or cloud functions using appropriate standardization and logging
tools. Teleon is the backbone of all of our runtimes and functions."*

This is that compiler. It takes a **promoted capability** (an intent that already cleared the eval gate — its
spec + gate evidence + receipts) and compiles it, **deterministically**, into a deployable **runtime unit**: a
Fly machine config, a Kubernetes Job, or a local process — your pick, all three from one unit. It is the
per-capability analog of `architecture/deploy_topology.json` (which is the per-**service** plane), built on the
**same proven generator pattern** as `scripts/deploy/generate_provider_configs.py` (one declarative source →
provider configs, drift-gated, self-tested) — but for **capabilities** instead of services.

## Where it sits: intent → build → gate → compile → deploy → registry-of-promoted-runtimes

```
  CapabilityTask / PurposeTask          ← the INTENT (what work, how to know it's good)
        │  (declared, not coded)
        ▼
  build a candidate implementation      ← agents PROPOSE (out-of-band)
        │
        ▼
  EVAL GATE (teleon_local_runtime)      ← train+holdout pass-rates must BOTH clear PROMOTE_AT
        │   status: candidate | rolled-back | PROMOTED
        ▼
  ┌─────────────────────────────────────────────────────────┐
  │  THE COMPILER  (src/teleon/compiler)                     │
  │  compile_capability(promoted_capability, task_spec, …)   │   ← ONLY promoted capabilities reach here
  │     • REFUSES anything not "promoted" (NotPromotedError) │   ← the law, enforced in code AND schema
  │     • runtime_class → backend  via runtime_binding       │   ← REUSED, not reinvented
  │     • resources    from worker_resource_classes.json     │   ← joined, no magic values
  │     • budgets      from SLA policy + OIPS + task spec     │
  │     • gate_evidence + receipt_refs + rollback_target     │   ← lossless lineage
  │     → CompiledRuntimeUnit  (is_truth:false)              │
  └─────────────────────────────────────────────────────────┘
        │
        ▼
  emit(unit, exec_target)               ← fly_machine (JSON) | k8s_job (YAML) | local_process (JSON)
        │                                  PORTABLE: every unit emits all three; never cloud-locked
        ▼
  deploy  (fly machine run / kubectl apply / local subprocess)
        │
        ▼
  registry of compiled units            ← (next step) the per-capability analog of the topology — the set of
                                           promoted capabilities that are now deployable runtimes
```

The compiler is the **boundary between "an intent that passed the gate" and "a thing you can run in prod."** The
gate decides *whether* a capability is good; the compiler turns the good ones into *runnable, logged, bounded*
units — and refuses the rest.

## What a CompiledRuntimeUnit is (`CompiledRuntimeUnit`)

The per-capability analog of `deploy_topology.json`'s per-service entry. One promoted capability → one unit per
`exec_target`:

| Field | Source (single source of truth — never hand-typed) |
|---|---|
| `unit_id` | hash of `compiler_version + capability_id + capability_version + exec_target + source_spec_hash` (deterministic; **independent of `now`** so a daily recompile of identical inputs collapses to one id) |
| `capability_id` / `capability_version` | the promoted capability record (lineage to the source) |
| `runtime_class` | the CTS-portable class the CapabilityTask declared (`architecture/capability_runtime_classes.json`) |
| `backend` | **`src/teleon/purpose_tasks/runtime_binding.bind_allowed`** — the SAME class→backend authority PurposeTask uses |
| `binding` | the full `RuntimeClassBinding` decision (WHY this backend — lineage, not just which) |
| `exec_target` | `fly_machine` \| `k8s_job` \| `local_process` (the deployable shape this unit pins) |
| `container.image` | `deploy_topology.json` `image.registry_hint` |
| `container.command` | the capability runner argv (`-m scripts.teleon_local_runtime --run-capability <id>`) — self-describing |
| `container.env_refs` | secret-ref **names** from the topology's `model-plane` group — **names only, never values** |
| `resources.{cpu,memory_mb,gpu_required}` | `architecture/worker_resource_classes.json` keyed by the task's `required_resource_class` |
| `budgets.timeout_s` | the SLA policy `target_seconds` (`worker_sla_policies.json` by `sla_policy_id`), else the resource class `timeout_default_s` |
| `budgets.max_tokens` | the OIPS resolved-preference `budget_policy` (`max_output_tokens`\|`max_tokens`); a single named default constant only when the policy omits it (recorded in `budget_basis`) |
| `budgets.max_attempts` | the CapabilityTask spec `max_attempts` (the gate's retry ceiling) |
| `budgets.budget_basis` | **where each budget came from** (policy id / spec field / default-constant) — honesty about the join |
| `logging.otel_attrs` | OpenTelemetry-shaped resource attrs on **every** unit — `service.name`, `capability.id/version`, `runtime.class`, `deployment.exec_target`, `teleon.unit_id`, and `trace_id/span_id` when the caller supplies them |
| `gate_evidence` | `train_pass_rate`, `holdout_pass_rate`, `gate_basis`, `promoted_at`, `status` (**pinned `"promoted"`**) from the capability record / its promoting run |
| `receipt_refs[]` | `ModelInvocationReceipt` ids (model-call lineage for a model-mode promotion; `[]` for a deterministic one) |
| `provenance` | `compiler_version`, `source_spec_hash` (sha256 of the canonicalized inputs), `compiled_at` (the **passed-in** timestamp) |
| `rollback_target` | the prior `unit_id` this one supersedes (the reversible target), or `""` for the first compile |
| `is_truth` | structurally `false` (schema `const`) — a compiled unit is a deployable **plan**, not served truth |

## How it reuses, not duplicates, what already exists

The owner's rule is no parallel runtimes/ledgers/registries. The compiler is **glue over the built substrate**:

- **`runtime_binding` (CTS-1)** does the class→backend decision — `bind_allowed(allowed_runtime_classes, …)` with
  cloud-defer-only-after-local-equivalent. The compiler **calls it**; it does not re-derive backends. (Doc:
  `archive/legacy/docs/architecture/cts-1-runtime-class-binding.md`.)
- **`architecture/*.json` policy files** are the single sources for resources, SLA timeouts, the execution
  matrix, and the image — the compiler **joins** them, exactly as `generate_provider_configs.py` joins ports
  from `local_service_registry.json` rather than typing them.
- **OIPS (`src/teleon/inference/oips`)** owns model preference/budget; the compiler reads the resolved
  preference's `budget_policy` for the token ceiling. It does not invent a budget engine.
- **Receipts (`src/teleon/inference/receipts`)** are the provenance envelope; the compiler attaches receipt
  **refs**, mirroring the receipt sink's metadata-and-hashes-only, no-raw-secret discipline.
- **The eval gate (`scripts/teleon_local_runtime.py`)** owns promotion; the compiler **consumes** its
  capability record + run and **refuses** anything it didn't promote.

So the compiler adds exactly one new thing — the **deterministic capability→deployable-unit translation** — and
borrows everything else.

## The two laws

### 1. Only promoted capabilities compile

`compile_capability` raises `NotPromotedError` when `capability["status"] != "promoted"`. An un-gated capability
**must never become a runtime** — the gate is the admission boundary, and the compiler enforces it at the door.
It is also enforced **structurally**: `CompiledRuntimeUnit` pins `gate_evidence.status` to `"promoted"`, so a
unit that claims to deploy a non-promoted capability cannot even validate. A `candidate` or `rolled-back`
capability is refused with a clear, actionable reason ("run the eval gate to promotion first, then compile").

### 2. Deterministic — same inputs → byte-identical output

`compile_capability` is **pure**: it never reads the clock or `random`. The caller passes `now` (stamped only as
`compiled_at`); every id and hash derives from the **canonicalized inputs**. Recompiling the same capability
twice yields the identical `unit_id` and byte-identical unit. `unit_id` is deliberately **independent of `now`**
(a daily recompile of unchanged inputs collapses to one unit) but pins compiler + capability + version +
exec_target + `source_spec_hash`, so any real change forks a new id. This is the `generate_provider_configs.py`
drift-gate property applied to capabilities: the committed example units (`src/teleon/compiler/examples/`) are
recompiled by `--check` and any drift fails loudly.

## Exec-target portability — never cloud-locked

A capability is **not** "a Lambda" or "a K8s job" — it is contract-stable work whose deployable shape is a
reversible choice. `emit(unit, exec_target)` renders **all three**:

- **`fly_machine`** → a Fly Machines config (JSON) for `fly machine run --config <file>` — image, runner cmd,
  ref-name env (real secrets injected by `fly secrets set`, never in the file), guest sized from the resource
  class, deadline from the budget.
- **`k8s_job`** → a `batch/v1` **Job** (YAML) — a capability run is ephemeral bounded work (matches the
  `kubernetes-job` runtime class): `restartPolicy: Never`, `backoffLimit` from `max_attempts`,
  `activeDeadlineSeconds` from `timeout_s`, resource requests from the class, env via `secretKeyRef` (names
  only), OTel attrs as annotations.
- **`local_process`** → a local process spec (JSON) — argv + ref names + the resolved budgets — the
  always-available offline path; no container runtime required.

Same unit, three targets, one decision to switch. That is the "easily switch as needed" the topology doc calls
for, at the capability layer.

## Standardization & logging (the owner's "logging tools")

Every unit carries OpenTelemetry-shaped resource attributes (`logging.otel_attrs`) following OTel semantic
conventions (`service.name`, `service.version`) plus capability/runtime/deployment attrs and the `teleon.unit_id`
— and `trace_id`/`span_id` when the caller threads them in. Each emitter projects these into the target's native
slot (Fly metadata + env, k8s annotations, the local spec) so **trace correlation survives into the runtime**.
One standard set of attributes, three deployable shapes.

## CLI

```bash
python -m src.teleon.compiler --self-test                 # offline invariants (40 checks: determinism, refusal, 3 emitters, schema, drift)
python -m src.teleon.compiler --compile cap-redact        # compile (live runtime state if present, else the fixture)
python -m src.teleon.compiler --compile cap-redact --exec-target fly_machine --emit   # + print the concrete deployable text
python -m src.teleon.compiler --check                     # drift gate over the committed example units
python -m src.teleon.compiler --write-examples            # regen the committed examples (on a deliberate compiler change)
```

`--compile` reads the **live** `teleon_local_runtime` state (`dist/local-services-state/teleon-runtime/`) when
present — enriching the capability record with gate evidence + the promoting run's id as a receipt ref — and
falls back to a deterministic fixture otherwise. It refuses a non-promoted capability with exit code 2.

## Laws honored

- **No magic values** (`docs/codex/no-magic-values.md`): every field is joined from one source; the one numeric
  default (`DEFAULT_MAX_OUTPUT_TOKENS`) is a named constant with a unit + rationale and is recorded in
  `budget_basis` whenever it fires. The compiler version, schema version, runner module, and env-ref group each
  have a single definition.
- **Lossless distillation** (`docs/codex/lossless-distillation.md`): the unit carries lineage back to the
  capability (id + version), the binding decision, the gate evidence, the receipt refs, and a `rollback_target`.
  Compiling **derives** a new layer; it never discards or overwrites the source.
- **Change verification** (`docs/codex/change-verification-contract.md`): the warrant is **clear user intent**
  (the backbone directive quoted above) + an **established repo principle** (the `generate_provider_configs.py`
  generator pattern this mirrors). Demo-grade gaps are labelled below, not hidden.
- **Dependency law** (`architecture/portfolio_dependency_law.json`): Teleon-layer code; the package imports only
  stdlib + `src.teleon` siblings + `scripts` tooling. `check_portfolio_dependency_law.py --self-test` scans it
  (86 teleon files) and confirms no `teleon→baltor` / `teleon→openharnesshub` edge.

## What's still demo vs product (honest)

**Real now:**
- The compile is real, pure, and deterministic; the refusal law holds in code **and** schema.
- All three emitters produce **valid, parseable** configs (the self-test parses the k8s YAML and the fly JSON,
  and `jsonschema`-validates every unit against `CompiledRuntimeUnit`).
- It reads **live** promoted-capability state and compiles `cap-redact` (the live promoted capability) end-to-end.
- Budgets/resources/backends are **joined from policy**, proven by `budget_basis` + the self-test.

**Demo-grade / not yet product:**
- The capability runner is the **local** `teleon_local_runtime` (four deterministic reference capabilities). The
  emitted configs reference the repo image + that runner; a production runner image/entrypoint per capability is
  a follow-up.
- The **cloud/K8s backends are still `@candidate`** (no creds), so the default binding lands on the local
  equivalent — by design (cloud-defer-only-after-local-equivalent). A credentialed run binds the cloud backend
  (proven in the self-test by injecting `aws_lambda@candidate` creds), but no real cloud deploy is wired.
- The live capability record does **not** yet persist `train/holdout/promoted_at` on the capability itself, so
  for a live compile those come through honestly as `null` unless a promoting run carried them. (The fixture
  shows the fully-populated shape.)
- `emit` produces deployable **text**; it does **not** call `fly` / `kubectl` (no side effects — emission is pure).

## Next steps

1. **Registry of compiled units** — the per-capability analog of `deploy_topology.json`: persist the set of
   promoted capabilities that are now compiled runtime units (one row per `unit_id`), so "what's deployable" is a
   queryable plane, not a recompile. This is the natural home for the `--check` drift gate at scale.
2. **Rollback wiring** — `rollback_target` is carried but not yet consumed; a "deploy supersedes prior unit, keep
   the predecessor as the reversible target" flow (mirroring `purpose_task.rollback`) closes the loop.
3. **PurposeTask intake queue** — feed promoted capabilities into the compiler automatically on promotion (the
   gate emits → the compiler compiles → the registry records), so the backbone runs without a manual `--compile`.
4. **Real runner image + a credentialed cloud target** — a production per-capability entrypoint and the first
   real `fly machine run` / `kubectl apply` of an emitted unit (behind the existing candidate-defer gate).

> **Is this the backbone yet?** It is the **compiler core** of the backbone — the deterministic, gated,
> portable, logged translation from a promoted intent to a deployable runtime — built on the proven topology
> generator pattern and reusing (not duplicating) the binding, policy, OIPS, and gate substrate. The remaining
> gap to "the backbone of all runtimes" is the **registry + intake queue + a real runner/cloud deploy** (the
> Next steps) — i.e. wiring this core into the promotion→deploy loop, not rebuilding it.
