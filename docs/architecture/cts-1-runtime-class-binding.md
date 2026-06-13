# CTS-1 — Runtime-class → backend binding

**Status:** built + proven (`scripts/check_runtime_class_binding.py`, registered in the flywheel).
**Code:** `src/baltor/purpose_tasks/runtime_binding.py` · **Contract:** `schemas/purpose_tasks/RuntimeClassBinding.v1.schema.json`.

CTS-0 let a PurposeTask *declare* `allowed_runtime_classes` from the CTS-portable vocabulary
(`architecture/capability_runtime_classes.json`). **CTS-1 is the binding step:** turn a declared abstract
runtime *class* into a *concrete, runnable backend* — by policy, available credentials, and provider health —
without the contract ever naming a vendor product.

## The rule
> A cloud/K8s vendor is bound **only** when it is credentialed **and** healthy. Otherwise the class binds to
> its **built local equivalent** (always available). Capability never blocks on missing cloud.

This is *cloud-defer-only-after-local-equivalent* applied at the runtime-class layer. Every class in the
vocabulary declares a `local_equivalent`, and every one of those is in the policy matrix's
`local_equivalents_built` (or is a base backend in `backends_enum`) and routes to a real local executor.

## Two id namespaces, one bridge
- **Provider namespace** (`execution.local_job_emulator@v1`, …) — the `ExecutionProviderPort` implementations,
  used in the runtime-class vocabulary and the policy matrix.
- **Selector/dispatch namespace** (`local_job_emulator@v1`, …) — the bare ids the execution selector and
  `execution_dispatch._route_and_drain` understand.

`local_fallback_backend()` bridges them with **one deterministic rule** — strip the leading `execution.`
prefix — so the binding's local fallback is always something the dispatcher can route (job ids → job emulator,
pool ids → worker pool, function/subprocess family → function emulator). No per-class mapping table to drift.

## Behaviour (the proof asserts each)
| Situation | Binding |
|---|---|
| No credentials (offline default) | `bind_local_fallback` → the class's local equivalent |
| A class vendor is credentialed + healthy | `bind_cloud_backend` → that vendor |
| Credentialed but unhealthy | `bind_local_fallback` (cloud deferred) |
| Only credentialed vendor excluded by policy | `bind_local_fallback` |
| Two credentialed vendors + `preferred_backends` | the preferred vendor wins |
| `browser-worker` / `gpu-worker` | never considers a generic cloud function (the **class scopes the hard guard for free** — its vendor list has no serverless family) |
| Unknown / undeclared class | **deny-by-default** → offline default backend, `known_class=false` |

`bind_allowed(allowed_runtime_classes, …)` binds a task that lists several classes in priority order: the
first class with a runnable cloud vendor wins; if none has cloud credentials, the local equivalent of the
**first** class runs (empty list → offline default). `resolve_for_spec(spec, …)` reads a `PurposeTaskSpec.v1`
`allowed_runtime_classes` directly.

## Composition (not replacement)
The binding does **not** duplicate `execution_backend_selector`. `eligible_backends_for_classes()` produces
the union of the allowed classes' concrete backends (cloud vendors + each local equivalent, with a local
fallback guaranteed); feed that to `select_backend(..., policy_override={"eligible": …})` so the selector's
cost/health ranking happens *within* the contract's allowed shapes. Offline, the selector picks a local
backend inside that set — proven in check L.

## Invariants honored
- **No magic values / single source.** The class vocabulary is read from `capability_runtime_classes.json`;
  injecting a custom vocabulary changes the binding (proof check J), confirming no hardcoded class list.
- **Branch on the class + numeric policy**, never a vendor display name.
- **No truth published.** A binding is a routing decision; the FleetLedger remains the source of truth.
- **Pure + deterministic.** All inputs (credentials, health, policy, vocabulary, matrix) are injectable.

## Next on the CTS ladder
CTS-2 observability requirements (the `observability` block on `PurposeTaskSpec.v1`) and the
CapabilityRun/Promotion/evidence ledger that records *which* binding actually ran and at what measured cost.
