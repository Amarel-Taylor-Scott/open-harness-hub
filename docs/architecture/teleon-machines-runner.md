# Teleon Machines Runner — launch a compiled capability unit onto Fly Machines

**Date:** 2026-06-11. **Status:** built + self-tested (41/41), live the moment a `FLY_API_TOKEN` exists.
**Code:** `scripts/deploy/teleon_machines_runner.py` ·
**Consumes:** `src/teleon/compiler/` (`CompiledRuntimeUnit`) + `schemas/runtime/CompiledRuntimeUnit.v1.schema.json` ·
**Reuses:** `scripts/deploy/fly_worker_controller.py` (`MachinesAPI`) ·
**CLI:** `python -m scripts.deploy.teleon_machines_runner`.

## The gap this closes

The compiler turns a **promoted** capability into a `CompiledRuntimeUnit` and `emit()` renders the
`exec_target=fly_machine` shape into a Fly machine config. Until now **nothing launched it**. The worker
controller (`fly_worker_controller.py`) already drives the Fly Machines API for the foundry worker *fleet*
(scale a pool on queue depth). This runner is the missing per-capability counterpart on the same substrate:
given one compiled unit, **create → poll → tear down** a single Fly machine and write a lineage-carrying receipt.

## Why the Machines API is the universal execution substrate

Three different Teleon execution needs collapse to the *same* four Machines-API verbs (create, start/get, stop,
destroy):

| Workload | Driver | Shape on the substrate |
|---|---|---|
| **Worker fleet** (burst, queue-driven) | `fly_worker_controller.py` | a *pool* of long-lived machines, scaled 0→N on Redis `LLEN`, drained on cooldown |
| **Compiled capability** (one bounded run) | **`teleon_machines_runner.py`** (this) | *one* machine per run: create from the unit, poll to its deadline, destroy |
| **Bounded-exploration agent** (sandboxed, time-boxed) | same runner / same client | identical to a capability run — a deadline + a force-destroy is exactly the sandbox boundary |

One API, one HTTP/RESP/backoff client (`MachinesAPI`), three roles. The runner **imports and subclasses** that
client — adding only `get` (poll one machine) and `destroy` (DELETE), the two verbs the fleet controller never
needed — so the HTTP code lives in exactly one place and the controller file is never edited.

## How a launch works (create → poll → teardown → receipt)

1. **Load** the unit — a `--launch <unit.json>` file, or a `unit_id` looked up under
   `dist/local-services-state/teleon-compiler/` (the compiled-unit registry, when present).
2. **Validate at the launch boundary** (`assert_launchable`): the unit must be the right `schema_version`,
   **schema-valid** against `CompiledRuntimeUnit.v1` (the compiler's own `validate_unit`), **promoted**
   (`gate_evidence.status == "promoted"`), targeted at `fly_machine`, and structurally non-truth. Anything else
   is **REFUSED** with a precise reason. **The only-promoted law holds at launch, not just at compile** — a
   hand-rolled unit that skipped the compiler is still caught here.
3. **Build the create config** from the unit (no magic values): `emit_fly_machine(unit)` is the single source of
   the base shape (image · `init.cmd` · env-**ref** placeholders · stop timeout · otel metadata). On top of it the
   runner binds what a *create* needs and the emitter can't know:
   - **`guest.cpus`** — the resource-class CPU (`"500m"`, `"2"`, …) translated to a whole-core integer Fly preset
     (ceil millicores / 1000, floor 1). The emitter passes the raw `"500m"` string through, which is **not** a
     valid create `cpus`; the runner fixes that.
   - **`restart`** — `budgets.max_attempts` → `{policy: on-failure, max_retries: max_attempts-1}` (or `no` when
     `max_attempts==1`). The gate's retry ceiling, bound to the platform.
   - **`metadata.managed_by`** — the runner's marker, so it only ever stops/destroys machines **it** launched.
4. **Poll to completion** (`get` every few seconds, gentle backoff) until a terminal state or the **deadline**.
5. **Teardown** — `destroy(?force=true)` always, so no machine is ever left running after a run.
6. **Receipt** — appended to `dist/local-services-state/teleon-runner/receipts.jsonl`.

## The budget / teardown / receipt model

- **`budgets.timeout_s` → wall-clock deadline, enforced by the runner.** Fly Machines has **no**
  `activeDeadlineSeconds` (that's a k8s Job field the compiler's `k8s_job` emitter uses). So the runner owns the
  deadline: it polls until `started + timeout_s + grace`, then reports `outcome=timeout` and **force-destroys** the
  machine. The receipt records `deadline_enforced_by` honestly.
- **`budgets.max_attempts` → restart policy** on the machine (`on-failure`, `max_retries = max_attempts-1`).
- **`budgets.max_tokens`** is the model token ceiling — carried into the receipt (the runner does not itself meter
  tokens; that's the in-machine runtime's job, and the ceiling rides as an OTel/budget attribute).
- **Teardown is unconditional and runner-owned** (`auto_destroy=false`): the receipt is written *before* destroy,
  and a teardown error is recorded, never swallowed. The runner only ever tears down its own (`managed_by`) machine.
- **Receipt = lossless lineage.** `TeleonRunReceipt.v1` carries: machine id, started/finished/duration, outcome +
  exit code, **and the full lineage** — `unit_id`, `capability_id`, `capability_version`, `backend`,
  `runtime_class`, the unit's **own** `receipt_refs` (the model-call receipts behind it), `rollback_target`,
  `source_spec_hash`, and the unit's **OTel attrs** (trace correlation survives from compile into the run).
  `is_truth` is structurally false — a run record is an operational fact, not served truth.

Outcomes are honest, never faked: `completed` (exit 0) · `nonzero_exit` · `failed` · `timeout` ·
`create_capacity_error` · `create_error` · `poll_error`. Every one still tears the machine down and writes a
receipt with lineage.

## The live-on-token boundary (honest degradation)

With **no `FLY_API_TOKEN`**, the runner does **not** launch. `--launch` validates the unit and prints the
**exact plan** (the same create config a real launch would send, plus the target app/region and the budget basis),
then exits `3` with a clear *"token required"*. There is **no fake launch and no fabricated result** — the moment a
deploy-scoped token exists, `--launch` is real, exactly like `fly_worker_controller.py`. `--plan` prints that same
plan and needs no token at all.

```
python -m scripts.deploy.teleon_machines_runner --self-test          # offline: fake clock + fake Machines API
python -m scripts.deploy.teleon_machines_runner --plan   <unit.json> # the create plan (no launch, no token)
python -m scripts.deploy.teleon_machines_runner --launch <unit.json> # create→poll→complete→teardown (needs token)
```

## Topology addition needed (for the topology owner — NOT applied here)

The runner targets a **new Fly app** that is **not yet** in `architecture/deploy_topology.json`. The runner reads
its app/region from the topology's `fly` block (`<app_prefix>-teleon-runner`, primary region) and an operator can
override with `FLY_RUNNER_APP` / `FLY_RUNNER_REGION` / `FLY_MACHINES_API`. To make it a first-class deploy target,
the **topology owner** (this runner edits no topology) should add a `control`-kind service mirroring
`worker-controller`:

```jsonc
{
  "name": "teleon-runner",
  "kind": "control",
  "providers": ["fly"],
  "command": ["python3", "-m", "scripts.deploy.teleon_machines_runner", "--launch", "<unit_id>"],
  "public": false,
  "cpu_kind": "shared", "cpus": 1, "memory_mb": 256,
  "env": {},
  "secret_groups": ["fly-controller"],   // reuses the FLY_API_TOKEN group; needs machines:write on the runner app
  "notes": "Launches a COMPILED capability unit (exec_target=fly_machine) as a one-shot Fly machine: create from the unit, poll to budgets.timeout_s, destroy. Per-capability analog of worker-controller (which drives the worker FLEET on the SAME Machines API). Needs a deploy-scoped token for app aidr-teleon-runner."
}
```

Notes for whoever applies it: the runner is a **one-shot launcher**, not a long-lived loop — it is invoked per
unit (e.g. by a promotion step or a queue consumer), so the topology entry is mostly for **app provisioning + the
token secret**, not a `[processes]` daemon. The `fly-controller` secret group (`FLY_API_TOKEN`) is reused; the
token must be scoped to the new `aidr-teleon-runner` app with `machines:write`. Because each run is a single
short-lived machine that the runner force-destroys, no volume / no `state_mount` is required on the app (the
receipt sink lives on the *invoking* host, under `dist/local-services-state/teleon-runner/`).

## What's real vs. still demo

- **Real now:** the launch/poll/teardown logic, the schema-gated refusal, the budget binding, the receipt lineage,
  the no-token honest plan, and the import-reuse of the controller's `MachinesAPI`. The runner launches for real
  the instant a token + app exist.
- **Demo / fixture-backed:** the self-test fixture capability (`cap-redact`) and its `local_function_emulator`
  backend come from the compiler's deterministic fixtures; a real promotion would carry a real capability + real
  receipt refs. The exit-code extraction (`_exit_code_of`) is defensive across a few Machines-API payload shapes —
  worth re-confirming against a live machine's `state_exit_event` on first real launch.

## Verification

```
python -m py_compile scripts/deploy/teleon_machines_runner.py
python -m scripts.deploy.teleon_machines_runner --self-test     # 41/41 (run 3×, deterministic)
python scripts/deploy/preflight.py                              # GO — deploy artifacts unaffected
```

The self-test (deterministic: fake clock + fake `MachinesAPI` that raises the controller's **real** typed errors)
proves: launch→poll→complete→teardown; non-zero-exit / failed / timeout each reported honestly and still torn down;
the deadline enforced from `budgets.timeout_s`; capacity + rate-limit on create handled; non-promoted / invalid /
wrong-target / is_truth-flipped / wrong-schema units **REFUSED**; the no-token path an honest plan (exit 3, launches
nothing — guarded by a tripwire); the receipt appended with full lineage; and the client reused (not duplicated)
from the controller.
