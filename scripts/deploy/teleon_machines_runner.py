#!/usr/bin/env python3
"""Teleon Machines runner — LAUNCH a COMPILED CAPABILITY UNIT onto the Fly Machines API.

The compiler (``src/teleon/compiler/``) turns a PROMOTED capability into a ``CompiledRuntimeUnit`` and ``emit()``
renders the ``exec_target=fly_machine`` shape into a Fly machine config. Nothing LAUNCHED it. This runner closes
that gap: it is the per-capability analog of ``scripts/deploy/fly_worker_controller.py`` (which drives the SAME
Machines API for the foundry worker FLEET). The Machines API is the UNIVERSAL execution substrate — the worker
fleet, a compiled capability unit, and a bounded-exploration agent are all just "create a machine, watch it,
tear it down". This file is the compiled-capability launcher on that substrate.

What it does, given a CompiledRuntimeUnit (exec_target=fly_machine):
  1. LOAD the unit (a ``--launch <unit.json>`` path, or by ``unit_id`` from the compiled-unit registry under
     ``dist/local-services-state/teleon-compiler/`` when present) and VALIDATE it against
     ``schemas/runtime/CompiledRuntimeUnit.v1.schema.json`` (the compiler's own ``validate_unit``).
  2. ENFORCE the launch laws: only a PROMOTED, schema-VALID, ``fly_machine`` unit launches. A non-promoted /
     invalid / wrong-target unit is REFUSED with a clear reason (the only-promoted law holds at launch too).
  3. CREATE a Fly machine from the unit's image + command + env-REF names + resources + budgets (the create
     config is built by ``emit_fly_machine`` for fidelity, then the resource-class CPU is translated to a valid
     Fly guest and the budgets are bound to the platform: ``max_attempts`` → restart policy, ``timeout_s`` is the
     wall-clock deadline the runner itself enforces by polling — Fly Machines has no activeDeadlineSeconds).
  4. POLL to completion honoring ``budgets.timeout_s`` (kill + fail on deadline) and capture the exit.
  5. WRITE a RUN RECEIPT carrying full lineage — machine id, started/finished, exit, the ``unit_id`` +
     ``capability_version`` + the unit's ``receipt_refs`` + the OTel attrs — to
     ``dist/local-services-state/teleon-runner/receipts.jsonl`` (lossless: the run is never decoupled from the
     unit it deployed or the unit's own lineage).
  6. DESTROY (or stop) the machine — the runner owns the lifecycle, the platform does not.

REUSE, not duplication: the Machines-API HTTP/RESP/backoff client is IMPORTED from the worker controller
(``MachinesAPI``, ``RateLimited``, ``CapacityError``). This runner only SUBCLASSES it to add the two verbs the
fleet controller never needed — ``get`` (poll one machine) and ``destroy`` (DELETE) — reusing its ``_call``. The
controller file is NOT edited.

HONEST DEGRADATION — no ``FLY_API_TOKEN`` → it does NOT launch. It validates the unit, prints the EXACT plan
(what it WOULD create on the Machines API), and exits with a clear "token required". Never a fake launch, never a
fabricated result. The moment a token exists, ``--launch`` is REAL — exactly like the worker controller.

Run modes::

  python -m scripts.deploy.teleon_machines_runner --self-test          # offline: fake clock + fake Machines API
  python -m scripts.deploy.teleon_machines_runner --plan   <unit.json>  # print the create plan (no launch)
  python -m scripts.deploy.teleon_machines_runner --launch <unit.json>  # launch→poll→complete→teardown (needs token)

LAWS honored: no-magic-values (resources/budgets/image/env-refs all come from the UNIT, never re-typed;
the Fly app/region come from ``architecture/deploy_topology.json``); honest (degrade loudly, never fake a launch
or a result); lossless (the receipt carries lineage to the unit + its receipt_refs + the otel attrs); deterministic
self-test (fake clock + fake API — no wall-clock, no network).

ARCHITECTURAL NOTE — this runner targets a NEW Fly app ``<prefix>-teleon-runner`` that is NOT yet in
``architecture/deploy_topology.json``. The topology addition is DOCUMENTED for the topology owner in
``docs/architecture/teleon-machines-runner.md`` and NOT applied here (this file owns no topology edits). Until the
app exists the runner still validates + plans honestly; it launches the moment the app + token exist.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# REUSE the proven Machines-API client + its typed errors from the worker controller (do NOT duplicate the
# HTTP/RESP/backoff code). We subclass it below to add get/destroy; the controller file is never edited.
from scripts.deploy.fly_worker_controller import MachinesAPI  # noqa: E402
# REUSE the compiler's schema validator, exec-target enum, and the fly_machine emitter (single source of the
# create-config shape) — never reinvent the unit contract here.
from src.teleon.compiler import (  # noqa: E402
    validate_unit,
    emit_fly_machine,
    EXEC_TARGETS,
    PROMOTED_STATUS,
    SCHEMA_VERSION,
)

# ---------------------------------------------------------------- single-source constants (no magic values)

TOPOLOGY_PATH = REPO / "architecture" / "deploy_topology.json"
#: where compiled units are persisted by the compiler/registry, when present (the runner reads a unit by id from
#: here as an alternative to a passed file). One definition — never a parallel literal.
COMPILED_UNIT_REGISTRY_DIR = REPO / "dist" / "local-services-state" / "teleon-compiler"
#: the runner's own receipt sink — operational run records (NOT served truth), append-only JSONL, lineage-carrying.
RUNNER_STATE_DIR = REPO / "dist" / "local-services-state" / "teleon-runner"
RUNNER_RECEIPTS_PATH = RUNNER_STATE_DIR / "receipts.jsonl"

#: the exec_target this runner launches. Units are PORTABLE (the compiler emits all of EXEC_TARGETS); THIS runner
#: is the Fly-Machines launcher, so it only accepts the fly_machine shape (a k8s_job goes to kubectl, a
#: local_process to the local runner). One definition, asserted to be a real member of the compiler's enum.
LAUNCH_EXEC_TARGET = "fly_machine"
assert LAUNCH_EXEC_TARGET in EXEC_TARGETS, "fly_machine must be a compiler exec_target"

#: machine metadata marker — the runner only ever stops/destroys machines IT launched (mirrors the controller's
#: managed_by discipline; a separate value so the two roles never touch each other's machines).
MANAGED_BY_KEY = "managed_by"
MANAGED_BY_VALUE = "teleon_machines_runner"
#: the env key a launched machine self-identifies by (mirrors emit_fly_machine's TELEON_UNIT_ID).
UNIT_ENV_KEY = "TELEON_UNIT_ID"

#: Fly default API base (overridable; on Fly itself use the internal proxy). Mirrors the controller's default so a
#: change is made in ONE conceptual place per role.
FLY_MACHINES_API_DEFAULT = "https://api.machines.dev"

# --- poll cadence + backoff (named constants with a unit + rationale — no bare numbers in the loop) -----------
POLL_INTERVAL_S = 2.0            # how often we GET the machine state while it runs (gentle: ~0.5 rps/machine)
POLL_INTERVAL_MAX_S = 15.0       # cap the interval if we ever back off on transient GET errors
GET_RETRY_BASE_S = 2.0           # first backoff step on a transient GET error (never crash the poll loop)
GET_RETRY_MAX_ATTEMPTS = 5       # consecutive transient GET failures tolerated before we give up the poll
RATE_LIMIT_SLEEP_CAP_S = 30.0    # cap how long we honor a Retry-After during launch/teardown
#: grace added to the unit deadline before the runner declares a hard timeout — covers create→start latency so we
#: do not kill a machine for the platform's own boot time. A small, named slack (seconds).
DEADLINE_GRACE_S = 10.0
#: Fly guest cpu presets are INTEGER counts; a Kubernetes cpu quantity ("500m","2","250m") must be translated to a
#: whole-core count for the guest. 1 core = 1000 millicores (one definition; ceil so we never UNDER-provision).
MILLICORES_PER_CORE = 1000
MIN_FLY_CPUS = 1                 # a Fly machine has at least 1 vCPU

#: Fly machine lifecycle states (from the Machines API). Grouped once so the poll loop reads as intent, not magic
#: strings sprinkled inline.
RUNNING_STATES = {"created", "starting", "started", "replacing"}
DONE_STATES = {"stopped", "stopping", "exited", "destroyed", "destroying", "failed"}
FAILED_STATES = {"failed"}


class LaunchRefused(Exception):
    """A unit was refused at the launch boundary (not promoted / invalid / wrong exec_target). The message names
    the exact reason so a caller (or the CLI) can explain WHY — never a silent wrong launch."""


# ---------------------------------------------------------------- Machines API: add get/destroy by REUSE


class RunnerMachinesAPI(MachinesAPI):
    """The controller's Machines client + the two verbs a per-run launcher needs but the FLEET controller never
    did. We reuse its ``_call`` (all the HTTP/RESP/backoff + RateLimited/CapacityError handling) and add:

      * ``get(id)``     — GET one machine (poll its state to completion)
      * ``destroy(id)`` — DELETE one machine with ?force=true (the runner owns teardown)

    Importing-and-subclassing keeps the HTTP code in ONE place (the controller) and adds nothing it doesn't need.
    """

    def get(self, machine_id: str) -> dict:
        return self._call("GET", f"/machines/{machine_id}")  # type: ignore[return-value]

    def destroy(self, machine_id: str) -> None:
        # ?force=true so a still-running machine is torn down too (the runner enforces its own deadline).
        self._call("DELETE", f"/machines/{machine_id}?force=true")


# ---------------------------------------------------------------- unit loading + launch-law validation


def load_unit(source: str) -> dict:
    """Load a CompiledRuntimeUnit from a file path, or — when ``source`` is not an existing path — treat it as a
    ``unit_id`` and look it up in the compiled-unit registry (``<id>.json`` under COMPILED_UNIT_REGISTRY_DIR).
    Raises ``FileNotFoundError`` with both attempted locations so a typo is obvious."""
    p = Path(source)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    candidate = COMPILED_UNIT_REGISTRY_DIR / f"{source}.json"
    if candidate.is_file():
        return json.loads(candidate.read_text(encoding="utf-8"))
    raise FileNotFoundError(
        f"no compiled unit at {p} and none in the registry at {candidate} — pass a unit JSON file or a unit_id "
        f"present under {COMPILED_UNIT_REGISTRY_DIR.relative_to(REPO)}")


def assert_launchable(unit: dict) -> None:
    """Enforce the launch laws. Raises ``LaunchRefused`` with a precise reason unless the unit is:
      * the right schema version + structurally schema-VALID (CompiledRuntimeUnit.v1),
      * PROMOTED (gate_evidence.status == 'promoted' — the only-promoted law, re-checked at launch),
      * targeted at ``fly_machine`` (this runner's substrate),
      * structurally non-truth (is_truth is false — a unit is a plan, never served truth).
    The schema already pins status='promoted' and is_truth const false; we re-check them EXPLICITLY so the refusal
    message is actionable (and so a hand-rolled unit that skipped the compiler is still caught here, not silently
    launched)."""
    if unit.get("schema_version") != SCHEMA_VERSION:
        raise LaunchRefused(
            f"unit schema_version is {unit.get('schema_version')!r}, not {SCHEMA_VERSION!r} — recompile with the "
            f"current compiler before launching")
    errors = validate_unit(unit)
    if errors:
        head = "; ".join(errors[:4]) + (f" (+{len(errors) - 4} more)" if len(errors) > 4 else "")
        raise LaunchRefused(f"unit fails CompiledRuntimeUnit.v1 schema validation — REFUSED: {head}")
    status = (unit.get("gate_evidence") or {}).get("status")
    if status != PROMOTED_STATUS:
        raise LaunchRefused(
            f"unit gate_evidence.status is {status!r}, not {PROMOTED_STATUS!r} — only a PROMOTED capability's unit "
            f"launches (the only-promoted law holds at launch, not just at compile)")
    if unit.get("exec_target") != LAUNCH_EXEC_TARGET:
        raise LaunchRefused(
            f"unit exec_target is {unit.get('exec_target')!r}; this runner launches {LAUNCH_EXEC_TARGET!r} only. "
            f"Recompile the capability for {LAUNCH_EXEC_TARGET!r} (units are portable — one unit pins one target), "
            f"or deploy the {unit.get('exec_target')!r} shape with its own tool.")
    if unit.get("is_truth") is not False:
        raise LaunchRefused("unit.is_truth is not false — a compiled unit is a deployable plan, never served truth")


# ---------------------------------------------------------------- create-config (build from the UNIT, no magic)


def _cpu_to_fly_cpus(cpu_quantity: str) -> int:
    """Translate a Kubernetes CPU quantity ('500m','2','250m','1') to a whole Fly guest vCPU count. Fly guest
    presets are integer cpu counts; we CEIL millicores to a core (never under-provision) and floor at MIN_FLY_CPUS.
    Deterministic; one millicores-per-core definition (no duplicated multiplier)."""
    s = str(cpu_quantity).strip()
    m = re.fullmatch(r"([0-9]*\.?[0-9]+)(m?)", s)
    if not m:
        # honest fallback: an unexpected CPU shape gets the minimum guest, recorded in the plan basis below.
        return MIN_FLY_CPUS
    value = float(m.group(1))
    millicores = value if m.group(2) == "m" else value * MILLICORES_PER_CORE
    return max(MIN_FLY_CPUS, int(math.ceil(millicores / MILLICORES_PER_CORE)))


def build_create_config(unit: dict) -> dict:
    """Build the Fly Machines *create* config for ``unit`` — sourced ENTIRELY from the unit (image, command,
    env-REF names, resources, budgets, otel). The fly_machine emitter is the single source of the base shape
    (image / init.cmd / env-ref placeholders / metadata / stop timeout); on top of it the runner binds what a
    *create* needs and the emitter can't know:

      * ``guest.cpus`` — translated from the resource-class CPU to an integer Fly preset (the emitter passes the
        raw '500m' string through, which is not a valid create cpus; the runner fixes that for a real create).
      * ``restart``    — ``max_attempts`` → restart policy (>1 ⇒ retry up to max_attempts-1 on failure, else 'no').
        ``timeout_s`` is NOT a Fly field — the runner enforces the wall-clock deadline itself by polling.
      * ``metadata``   — the runner's managed_by marker + the unit_id (so it only ever tears down its OWN machines,
        and a running machine is attributable to this runner + this unit).

    NO secret VALUES travel here — only the env-ref NAMES the unit declared (Fly injects real values via
    ``fly secrets set`` out of band). NO magic numbers — every value is the unit's or a named constant."""
    base = json.loads(emit_fly_machine(unit))  # single-source base shape (image/cmd/env-refs/stop-timeout/otel)
    res = unit["resources"]
    budgets = unit["budgets"]
    max_attempts = int(budgets["max_attempts"])

    # guest: keep the emitter's cpu_kind + memory_mb, fix cpus to a valid integer preset.
    guest = dict(base.get("guest") or {})
    guest["cpus"] = _cpu_to_fly_cpus(res["cpu"])
    if res.get("gpu_required"):
        # surface the GPU need honestly; the operator picks a gpu-capable region/preset. We do not fabricate a
        # specific Fly GPU kind here (that's an account/region capability) — we mark it so it isn't silently lost.
        guest["gpu_required"] = True

    config = dict(base)
    config["guest"] = guest
    # bounded work: retry up to max_attempts-1 times ON FAILURE (the gate's retry ceiling), else never restart.
    config["restart"] = ({"policy": "on-failure", "max_retries": max_attempts - 1}
                         if max_attempts > 1 else {"policy": "no"})
    config["auto_destroy"] = False  # the runner owns teardown (so a receipt is always written before destroy)
    meta = dict(config.get("metadata") or {})
    meta[MANAGED_BY_KEY] = MANAGED_BY_VALUE
    meta[UNIT_ENV_KEY.lower()] = unit["unit_id"]
    config["metadata"] = meta
    return config


def create_plan(unit: dict) -> dict:
    """The EXACT, honest plan of what a launch WOULD create — the same config a real ``--launch`` sends to the
    Machines API, plus the app/region it targets and the budget-binding basis. This is what ``--plan`` prints and
    what the no-token path emits instead of launching (so a dry run is a faithful preview, not a guess)."""
    cfg = _runner_config()
    budgets = unit["budgets"]
    config = build_create_config(unit)
    return {
        "would_create": "fly_machine",
        "fly_app": cfg["app"],
        "fly_region": cfg["region"],
        "machines_api": cfg["api_base"],
        "unit_id": unit["unit_id"],
        "capability_id": unit["capability_id"],
        "capability_version": unit["capability_version"],
        "backend": unit["backend"],
        "image": config["image"],
        "command": config["init"]["cmd"],
        "env_refs": sorted(k for k in config["env"] if k != UNIT_ENV_KEY),  # NAMES only — never values
        "guest": config["guest"],
        "restart": config["restart"],
        # budget binding made explicit + honest about where each number came from (the unit's own basis):
        "deadline_s": int(budgets["timeout_s"]),
        "deadline_enforced_by": "teleon_machines_runner poll loop (Fly Machines has no activeDeadlineSeconds)",
        "max_attempts": int(budgets["max_attempts"]),
        "max_tokens": int(budgets["max_tokens"]),
        "budget_basis": budgets["budget_basis"],
        "otel_attrs": unit["logging"]["otel_attrs"],
        "receipt_refs": unit["receipt_refs"],
        "managed_by": MANAGED_BY_VALUE,
    }


def _cpu_basis(unit: dict, config: dict) -> str:
    return f"{unit['resources']['cpu']}→{config['guest']['cpus']} vCPU (ceil millicores/{MILLICORES_PER_CORE})"


# ---------------------------------------------------------------- the runner (launch → poll → teardown)


class RunReceipt(dict):
    """A run receipt is a plain dict (JSON-serializable); this subclass exists only to name the type at call
    sites. Operational record, not served truth (``is_truth`` is structurally false on it, mirroring the unit)."""


class Runner:
    """Launches ONE compiled unit onto Fly Machines, polls it to completion under the unit's deadline, tears it
    down, and returns a lineage-carrying RunReceipt. ``clock``/``sleep`` are injected so the self-test is fully
    deterministic (fake clock + fake API, no wall-clock, no network)."""

    def __init__(self, api: RunnerMachinesAPI, cfg: dict, *,
                 clock: Callable[[], float] = time.monotonic,
                 sleep: Callable[[float], None] = time.sleep,
                 receipts_path: Path = RUNNER_RECEIPTS_PATH) -> None:
        self.api = api
        self.cfg = cfg
        self.clock = clock
        self.sleep = sleep
        self.receipts_path = receipts_path

    # -- receipts --------------------------------------------------------------------------------------------
    def _write_receipt(self, receipt: RunReceipt) -> None:
        """Append the receipt to the JSONL sink. Receipts must never take a launch down (best-effort write)."""
        line = json.dumps(receipt, separators=(",", ":"), sort_keys=True)
        print(line, flush=True)
        try:
            self.receipts_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.receipts_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError:
            pass

    def _base_receipt(self, unit: dict, config: dict) -> RunReceipt:
        """The lineage spine every run receipt carries — the unit it deployed + that unit's OWN lineage (lossless:
        a run is never decoupled from the compiled unit or the capability/receipts behind it)."""
        return RunReceipt({
            "schema": "TeleonRunReceipt.v1",
            "role": MANAGED_BY_VALUE,
            "exec_target": LAUNCH_EXEC_TARGET,
            "fly_app": self.cfg["app"],
            "fly_region": self.cfg["region"],
            # --- lineage to the compiled unit + its lineage (capability + receipts) ---
            "unit_id": unit["unit_id"],
            "capability_id": unit["capability_id"],
            "capability_version": unit["capability_version"],
            "backend": unit["backend"],
            "runtime_class": unit["runtime_class"],
            "unit_receipt_refs": list(unit["receipt_refs"]),          # the model-call receipts behind the unit
            "rollback_target": unit.get("rollback_target", ""),
            "source_spec_hash": (unit.get("provenance") or {}).get("source_spec_hash"),
            "otel_attrs": unit["logging"]["otel_attrs"],              # trace correlation propagated to the run
            # --- budgets enforced at launch ---
            "deadline_s": int(unit["budgets"]["timeout_s"]),
            "max_attempts": int(unit["budgets"]["max_attempts"]),
            "max_tokens": int(unit["budgets"]["max_tokens"]),
            "cpu_basis": _cpu_basis(unit, config),
            "is_truth": False,                                        # a run record is not served truth
        })

    # -- launch ----------------------------------------------------------------------------------------------
    def launch(self, unit: dict) -> RunReceipt:
        """LAUNCH ``unit`` (already validated by ``assert_launchable``) → poll to completion under its deadline →
        tear it down. Returns the run receipt (also appended to the receipts sink). Never raises on a run failure:
        a failed/timed-out/errored run yields a receipt with the honest outcome (and the machine is still torn
        down). Only a programming/precondition error propagates."""
        config = build_create_config(unit)
        receipt = self._base_receipt(unit, config)
        started_mono = self.clock()
        receipt["started_at_monotonic_s"] = round(started_mono, 3)

        # 1) create -------------------------------------------------------------------------------------------
        try:
            machine = self._create_with_backoff(config)
        except MachinesAPI.CapacityError as exc:
            receipt.update(outcome="create_capacity_error", error=str(exc)[:300],
                           finished_at_monotonic_s=round(self.clock(), 3))
            self._write_receipt(receipt)
            return receipt
        except Exception as exc:  # network/api error on create — honest failure, nothing to tear down
            receipt.update(outcome="create_error", error=str(exc)[:300],
                           finished_at_monotonic_s=round(self.clock(), 3))
            self._write_receipt(receipt)
            return receipt
        machine_id = machine.get("id", "")
        receipt["machine_id"] = machine_id

        # 2) poll to completion under the deadline ------------------------------------------------------------
        deadline_mono = started_mono + receipt["deadline_s"] + DEADLINE_GRACE_S
        outcome, exit_code, last_state = self._poll_to_done(machine_id, deadline_mono)
        receipt.update(outcome=outcome, exit_code=exit_code, machine_state=last_state,
                       finished_at_monotonic_s=round(self.clock(), 3),
                       duration_s=round(self.clock() - started_mono, 3))

        # 3) teardown (always — the runner owns the lifecycle) ------------------------------------------------
        receipt["teardown"] = self._teardown(machine_id)
        self._write_receipt(receipt)
        return receipt

    def _create_with_backoff(self, config: dict) -> dict:
        """Create one machine, honoring a single Retry-After on a rate limit (a launch is one machine, not a fleet
        — we don't loop forever; one polite retry then surface the error). CapacityError propagates to the caller
        (an honest 'no capacity right now', not a fake launch)."""
        try:
            return self.api.create(config, self.cfg["region"])
        except MachinesAPI.RateLimited as exc:
            self.sleep(min(exc.retry_after, RATE_LIMIT_SLEEP_CAP_S))
            return self.api.create(config, self.cfg["region"])

    def _poll_to_done(self, machine_id: str, deadline_mono: float) -> tuple[str, int | None, str]:
        """GET the machine until it reaches a terminal state or the deadline passes. Returns
        (outcome, exit_code, last_state). On deadline the machine is reported 'timeout' (teardown will force-kill).
        Transient GET errors back off and retry up to GET_RETRY_MAX_ATTEMPTS before giving up as 'poll_error'."""
        interval = POLL_INTERVAL_S
        get_failures = 0
        last_state = "unknown"
        while True:
            if self.clock() >= deadline_mono:
                return "timeout", None, last_state
            try:
                machine = self.api.get(machine_id)
                get_failures = 0
            except MachinesAPI.RateLimited as exc:
                self.sleep(min(exc.retry_after, RATE_LIMIT_SLEEP_CAP_S))
                continue
            except Exception:
                get_failures += 1
                if get_failures >= GET_RETRY_MAX_ATTEMPTS:
                    return "poll_error", None, last_state
                self.sleep(min(GET_RETRY_BASE_S * get_failures, POLL_INTERVAL_MAX_S))
                continue
            last_state = machine.get("state", "unknown")
            exit_code = _exit_code_of(machine)
            if last_state in FAILED_STATES:
                return "failed", exit_code, last_state
            if last_state in DONE_STATES or exit_code is not None:
                outcome = "completed" if (exit_code in (0, None) and last_state not in FAILED_STATES) else "nonzero_exit"
                return outcome, exit_code, last_state
            self.sleep(interval)
            interval = min(interval * 1.5, POLL_INTERVAL_MAX_S)  # gentle backoff while it runs

    def _teardown(self, machine_id: str) -> str:
        """Destroy the machine (force) so no machine is ever left running after a run. Best-effort + honest: a
        teardown error is recorded in the receipt, not swallowed silently and not fatal to the receipt write."""
        try:
            self.api.destroy(machine_id)
            return "destroyed"
        except MachinesAPI.RateLimited as exc:
            self.sleep(min(exc.retry_after, RATE_LIMIT_SLEEP_CAP_S))
            try:
                self.api.destroy(machine_id)
                return "destroyed"
            except Exception as exc2:
                return f"destroy_error:{str(exc2)[:120]}"
        except Exception as exc:
            return f"destroy_error:{str(exc)[:120]}"


def _exit_code_of(machine: dict) -> int | None:
    """Pull the process exit code out of a Machines GET payload, tolerant of the API's nesting. Returns None when
    the machine has not exited yet (or the payload doesn't carry one)."""
    for path in (("state_exit_event", "request", "exit_event", "exit_code"),
                 ("exit_event", "exit_code"),
                 ("config", "guest", "exit_code")):  # defensive: differing API shapes
        node: Any = machine
        for key in path:
            if not isinstance(node, dict):
                node = None
                break
            node = node.get(key)
        if isinstance(node, int):
            return node
    code = machine.get("exit_code")
    return code if isinstance(code, int) else None


# ---------------------------------------------------------------- runner config (no magic values)


def _runner_config(topology: dict | None = None) -> dict:
    """The Fly app + region + API base the runner targets. App/region come from
    ``architecture/deploy_topology.json`` (the SAME source the controller + generator use): the runner's app is
    ``<fly.app_prefix>-teleon-runner`` (documented for the topology owner; created out of band). The API base +
    app override env vars mirror the controller's contract so an operator configures BOTH roles the same way."""
    topo = topology if topology is not None else json.loads(TOPOLOGY_PATH.read_text(encoding="utf-8"))
    prefix = topo["fly"]["app_prefix"]
    return {
        "app": os.environ.get("FLY_RUNNER_APP", f"{prefix}-teleon-runner"),
        "region": os.environ.get("FLY_RUNNER_REGION", topo["fly"]["primary_region"]),
        "api_base": os.environ.get("FLY_MACHINES_API", FLY_MACHINES_API_DEFAULT),
    }


# ---------------------------------------------------------------- CLI


def cmd_plan(source: str) -> int:
    """Validate + print the create plan for a unit. No launch, no token needed. Refusal → exit 2; bad unit → 1."""
    try:
        unit = load_unit(source)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"could not load unit: {exc}", file=sys.stderr)
        return 1
    try:
        assert_launchable(unit)
    except LaunchRefused as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 2
    print(f"# launch plan for unit {unit['unit_id']!r} (capability {unit['capability_id']!r} "
          f"v{unit['capability_version']}, backend {unit['backend']!r}) — NO launch")
    print(json.dumps(create_plan(unit), indent=2, sort_keys=True, ensure_ascii=False))
    return 0


def cmd_launch(source: str) -> int:
    """Validate → (with a token) LAUNCH on Fly Machines → poll → teardown → receipt. Without a token: HONEST dry
    run — print the exact plan + 'token required', exit 3 (never a fake launch). Refusal → 2; bad unit → 1."""
    try:
        unit = load_unit(source)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        print(f"could not load unit: {exc}", file=sys.stderr)
        return 1
    try:
        assert_launchable(unit)
    except LaunchRefused as exc:
        print(f"REFUSED — {exc}", file=sys.stderr)
        return 2

    cfg = _runner_config()
    token = os.environ.get("FLY_API_TOKEN", "")
    if not token:
        # HONEST DEGRADATION: validate + show the EXACT plan, then refuse to launch. Not a fake launch.
        print("# NO FLY_API_TOKEN — honest dry run. The unit is VALID + promoted; this is exactly what a real "
              "--launch WOULD create on the Machines API:")
        print(json.dumps(create_plan(unit), indent=2, sort_keys=True, ensure_ascii=False))
        print(f"\ntoken required: set FLY_API_TOKEN (deploy-scoped for app {cfg['app']!r}) to launch. "
              f"The runner is live the moment a token exists — exactly like fly_worker_controller.", file=sys.stderr)
        return 3

    api = RunnerMachinesAPI(cfg["api_base"], token, cfg["app"])
    runner = Runner(api, cfg)
    print(f"# launching unit {unit['unit_id']!r} → Fly app {cfg['app']!r} region {cfg['region']!r}")
    receipt = runner.launch(unit)
    ok = receipt.get("outcome") == "completed"
    print(("PASS — " if ok else "DONE — ") + f"outcome={receipt.get('outcome')} "
          f"exit={receipt.get('exit_code')} machine={receipt.get('machine_id')} "
          f"teardown={receipt.get('teardown')}", file=sys.stderr)
    return 0 if ok else 1


#: how often --watch polls the compiled-unit registry for newly-active units (the deploy lag
#: between a capability promoting and its runtime launching; matches the controller's cadence feel)
WATCH_POLL_SECONDS = 30


def launched_unit_ids(receipts_path: Path = RUNNER_RECEIPTS_PATH) -> set:
    """unit_ids the runner has already launched (a receipt per launch) — watch never re-launches one."""
    if not receipts_path.is_file():
        return set()
    seen = set()
    for line in receipts_path.read_text(encoding="utf-8").splitlines():
        try:
            seen.add(json.loads(line)["unit_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return seen


def watch_once(*, registry_log: Path | None = None, runner: "Runner | None" = None,
               token: str | None = None, cfg: dict | None = None,
               receipts_path: Path = RUNNER_RECEIPTS_PATH, emit=print) -> dict:
    """ONE watch pass: launch every ACTIVE compiled unit not yet launched. With a token → real
    launch + receipt; without → an honest plan log (no fake launch). Returns a summary."""
    from src.teleon.compiler import open_registry
    reg = open_registry(log_path=registry_log) if registry_log else open_registry()
    already = launched_unit_ids(receipts_path)
    # list_active() returns the compiled UNITS directly (the per-capability deploy snapshot)
    pending = [u for u in reg.list_active()
               if u.get("unit_id") not in already and u.get("exec_target") == LAUNCH_EXEC_TARGET]
    launched, planned, refused = [], [], []
    for unit in pending:
        try:
            assert_launchable(unit)
        except LaunchRefused as exc:
            refused.append((unit.get("unit_id"), str(exc)))
            continue
        if runner is not None:                       # token present (or fake API in the self-test)
            runner.launch(unit)
            launched.append(unit["unit_id"])
        else:                                        # honest degradation: plan, never a fake launch
            emit(f"# WOULD launch {unit['unit_id']} (active, promoted, not yet launched) — "
                 f"set FLY_API_TOKEN to make it real")
            planned.append(unit["unit_id"])
    return {"active_pending": [u["unit_id"] for u in pending],
            "launched": launched, "planned": planned, "refused": refused}


def cmd_watch(once: bool = False) -> int:
    """Run as the aidr-teleon-runner app: poll the compiled-unit registry and launch newly-active
    units. With a token → real launches; without → honest plans (live the moment a token exists)."""
    cfg = _runner_config()
    token = os.environ.get("FLY_API_TOKEN", "")
    runner = Runner(RunnerMachinesAPI(cfg["api_base"], token, cfg["app"]), cfg) if token else None
    mode = "LAUNCHING" if runner else "PLANNING (no FLY_API_TOKEN — honest dry-run, live on token)"
    print(f"# teleon-machines-runner --watch [{mode}] app={cfg['app']!r} every {WATCH_POLL_SECONDS}s", flush=True)
    while True:
        summary = watch_once(token=token, runner=runner, cfg=cfg)
        if summary["launched"] or summary["planned"] or summary["refused"]:
            print(json.dumps({"watch_tick": summary}, sort_keys=True), flush=True)
        if once:
            return 0
        time.sleep(WATCH_POLL_SECONDS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true",
                        help="offline invariants: fake clock + fake Machines API (no network)")
    parser.add_argument("--launch", metavar="UNIT", help="launch a compiled unit (unit JSON file or unit_id)")
    parser.add_argument("--plan", metavar="UNIT", help="print the create plan for a unit (no launch, no token)")
    parser.add_argument("--watch", action="store_true",
                        help="run as the aidr-teleon-runner app: poll the registry + launch new active units")
    parser.add_argument("--once", action="store_true", help="with --watch: a single pass, then exit")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.plan:
        return cmd_plan(args.plan)
    if args.launch:
        return cmd_launch(args.launch)
    if args.watch:
        return cmd_watch(once=args.once)
    parser.print_help()
    return 0


# ---------------------------------------------------------------- self-test (offline, deterministic)


def _fixture_unit(exec_target: str = LAUNCH_EXEC_TARGET) -> dict:
    """Compile the deterministic compiler fixture into a unit for the self-test — the SAME promoted-capability
    fixture the compiler's own self-test uses (no parallel hand-built unit to drift). Imported lazily so the
    module's top-level import stays minimal."""
    import importlib
    _c = importlib.import_module("src.teleon.compiler.compile")
    _f = importlib.import_module("src.teleon.compiler.fixtures")
    return _c.compile_capability(
        _f.fixture_promoted_capability(), _f.fixture_task_spec(),
        exec_target=exec_target, now="2026-06-11T00:00:00Z",
        resolved_preference=_f.fixture_resolved_preference(), receipt_refs=["llmrcpt_fixture_0001"])


class _FakeClock:
    """A monotonic clock the test advances by hand AND that ``sleep`` advances — so the deadline is reached
    deterministically by sleeping, never by real time."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


class _FakeMachinesAPI:
    """A Machines-API double mirroring the controller self-test's style. Scriptable per scenario:
      * ``create`` returns a machine id (or raises a scripted RateLimited/CapacityError once);
      * ``get`` walks a scripted state timeline (or runs forever to exercise the deadline);
      * ``destroy`` records the teardown (and can assert the id is one we created).
    It is NOT a subclass of MachinesAPI — it only needs the same method surface (create/get/destroy) + raises the
    REAL imported error types, so it proves the runner handles the controller's typed errors."""

    def __init__(self, *, states: list[str], exit_code: int | None = 0,
                 capacity_on_first_create: bool = False, rate_limit_first_create: bool = False,
                 never_finishes: bool = False) -> None:
        self._states = list(states)
        self._exit_code = exit_code
        self._capacity_on_first_create = capacity_on_first_create
        self._rate_limit_first_create = rate_limit_first_create
        self._never_finishes = never_finishes
        self.created: list[dict] = []
        self.destroyed: list[str] = []
        self.create_calls = 0
        self.get_calls = 0
        self._counter = 0

    def create(self, config: dict, region: str) -> dict:
        self.create_calls += 1
        if self._capacity_on_first_create and self.create_calls == 1:
            raise MachinesAPI.CapacityError("412: insufficient capacity in iad")
        if self._rate_limit_first_create and self.create_calls == 1:
            raise MachinesAPI.RateLimited(0.0)
        assert config["metadata"][MANAGED_BY_KEY] == MANAGED_BY_VALUE, "create config must carry our managed_by"
        assert isinstance(config["guest"]["cpus"], int), "guest.cpus must be an int for a real create"
        assert all(not str(v).startswith(("sk-", "AKIA")) for v in config["env"].values()), "no secret values"
        self._counter += 1
        mid = f"machine-{self._counter}"
        self.created.append({"id": mid, "config": config, "region": region})
        return {"id": mid}

    def get(self, machine_id: str) -> dict:
        self.get_calls += 1
        if self._never_finishes:
            return {"id": machine_id, "state": "started"}  # never terminal → deadline path
        state = self._states[min(self.get_calls - 1, len(self._states) - 1)]
        out: dict[str, Any] = {"id": machine_id, "state": state}
        if state in DONE_STATES or state in FAILED_STATES:
            out["state_exit_event"] = {"request": {"exit_event": {"exit_code": self._exit_code}}}
        return out

    def destroy(self, machine_id: str) -> None:
        assert any(m["id"] == machine_id for m in self.created), "destroyed a machine we never created"
        self.destroyed.append(machine_id)


def self_test() -> int:  # noqa: C901 — a flat checklist reads clearer than helper indirection here
    checks: list[tuple[str, bool]] = []
    cfg = {"app": "aidr-teleon-runner", "region": "iad", "api_base": FLY_MACHINES_API_DEFAULT}
    unit = _fixture_unit()

    # 0. the fixture unit is itself a valid, promoted, fly_machine unit (precondition for the launch tests)
    checks.append(("fixture: compiles to a VALID fly_machine unit (schema-clean)", not validate_unit(unit)))
    checks.append(("fixture: is promoted + fly_machine + non-truth",
                   unit["gate_evidence"]["status"] == "promoted" and unit["exec_target"] == "fly_machine"
                   and unit["is_truth"] is False))

    # 1. assert_launchable ACCEPTS the good unit and REFUSES the bad ones (the launch laws) -------------------
    accepted = True
    try:
        assert_launchable(unit)
    except LaunchRefused:
        accepted = False
    checks.append(("launch-law: a valid promoted fly_machine unit is ACCEPTED", accepted))

    def _refused(u: dict) -> bool:
        try:
            assert_launchable(u)
            return False
        except LaunchRefused:
            return True

    not_promoted = {**unit, "gate_evidence": {**unit["gate_evidence"], "status": "candidate"}}
    checks.append(("launch-law: a NON-PROMOTED unit (status=candidate) is REFUSED", _refused(not_promoted)))
    wrong_target = {**unit, "exec_target": "k8s_job"}
    checks.append(("launch-law: a wrong-exec_target unit (k8s_job) is REFUSED by THIS runner", _refused(wrong_target)))
    truth_flipped = {**unit, "is_truth": True}
    checks.append(("launch-law: an is_truth=true unit is REFUSED (schema const + explicit check)",
                   _refused(truth_flipped)))
    missing_field = {k: v for k, v in unit.items() if k != "budgets"}
    checks.append(("launch-law: a unit missing a required field (budgets) is REFUSED (schema)",
                   _refused(missing_field)))
    wrong_schema = {**unit, "schema_version": "CompiledRuntimeUnit.v0"}
    checks.append(("launch-law: a wrong schema_version is REFUSED", _refused(wrong_schema)))

    # 2. create-config is built from the UNIT, with a valid integer guest + budget-bound restart, no secrets ---
    config = build_create_config(unit)
    checks.append(("create-config: image + command come straight from the unit",
                   config["image"] == unit["container"]["image"]
                   and config["init"]["cmd"] == unit["container"]["command"]))
    checks.append(("create-config: guest.cpus translated '500m'→1 integer vCPU (valid Fly preset)",
                   config["guest"]["cpus"] == 1 and isinstance(config["guest"]["cpus"], int)))
    checks.append(("create-config: max_attempts=3 → restart on-failure max_retries=2 (budget-bound, not magic)",
                   config["restart"] == {"policy": "on-failure", "max_retries": 2}))
    checks.append(("create-config: env carries ref NAMES only, never a secret value",
                   all(str(v).startswith("${") for k, v in config["env"].items() if k != UNIT_ENV_KEY)))
    checks.append(("create-config: carries our managed_by marker (only-our-machines teardown)",
                   config["metadata"][MANAGED_BY_KEY] == MANAGED_BY_VALUE))
    # CPU translation table is correct across resource-class shapes (no duplicated multiplier)
    checks.append(("cpu-translate: 500m→1, 2→2, 250m→1, 1→1, 4→4 (ceil millicores, floor 1)",
                   _cpu_to_fly_cpus("500m") == 1 and _cpu_to_fly_cpus("2") == 2 and _cpu_to_fly_cpus("250m") == 1
                   and _cpu_to_fly_cpus("1") == 1 and _cpu_to_fly_cpus("4") == 4))

    # 3. HAPPY PATH: launch → poll (running then stopped, exit 0) → teardown → receipt with lineage -----------
    clock = _FakeClock()
    api = _FakeMachinesAPI(states=["starting", "started", "started", "stopped"], exit_code=0)
    runner = Runner(api, cfg, clock=clock, sleep=clock.sleep, receipts_path=_throwaway_receipts())
    r = runner.launch(unit)
    checks.append(("launch: a machine was CREATED", api.create_calls == 1 and len(api.created) == 1))
    checks.append(("launch: polled until the machine reached a terminal state", api.get_calls >= 2))
    checks.append(("launch: outcome=completed, exit_code=0", r["outcome"] == "completed" and r["exit_code"] == 0))
    checks.append(("launch: the machine was TORN DOWN (destroyed)",
                   r["teardown"] == "destroyed" and api.destroyed == [r["machine_id"]]))
    # receipt lineage (lossless: run → unit → capability + the unit's receipt_refs + otel)
    checks.append(("receipt: carries unit_id + capability_id + version (lineage to the compiled unit)",
                   r["unit_id"] == unit["unit_id"] and r["capability_id"] == unit["capability_id"]
                   and r["capability_version"] == unit["capability_version"]))
    checks.append(("receipt: carries the unit's OWN receipt_refs (lineage to the model-call receipts)",
                   r["unit_receipt_refs"] == unit["receipt_refs"] == ["llmrcpt_fixture_0001"]))
    checks.append(("receipt: propagates the unit's OTel attrs (trace correlation survives to the run)",
                   r["otel_attrs"] == unit["logging"]["otel_attrs"]
                   and r["otel_attrs"]["teleon.unit_id"] == unit["unit_id"]))
    checks.append(("receipt: budgets recorded (deadline_s/max_attempts/max_tokens from the unit)",
                   r["deadline_s"] == unit["budgets"]["timeout_s"] and r["max_attempts"] == unit["budgets"]["max_attempts"]
                   and r["max_tokens"] == unit["budgets"]["max_tokens"]))
    checks.append(("receipt: is an operational record, not truth (is_truth false)", r["is_truth"] is False))
    checks.append(("receipt: timing present (started + finished + duration)",
                   "started_at_monotonic_s" in r and "finished_at_monotonic_s" in r and "duration_s" in r))

    # 4. NON-ZERO EXIT: a failed run is honestly reported AND still torn down ---------------------------------
    clock2 = _FakeClock()
    api2 = _FakeMachinesAPI(states=["started", "stopped"], exit_code=7)
    r2 = Runner(api2, cfg, clock=clock2, sleep=clock2.sleep, receipts_path=_throwaway_receipts()).launch(unit)
    checks.append(("nonzero-exit: outcome=nonzero_exit, exit_code=7 (honest, not faked success)",
                   r2["outcome"] == "nonzero_exit" and r2["exit_code"] == 7))
    checks.append(("nonzero-exit: machine still torn down after a failed run", r2["teardown"] == "destroyed"))

    # 5. FAILED STATE: a machine that enters 'failed' is reported failed + torn down --------------------------
    clock5 = _FakeClock()
    api5 = _FakeMachinesAPI(states=["started", "failed"], exit_code=1)
    r5 = Runner(api5, cfg, clock=clock5, sleep=clock5.sleep, receipts_path=_throwaway_receipts()).launch(unit)
    checks.append(("failed-state: outcome=failed, machine torn down",
                   r5["outcome"] == "failed" and r5["teardown"] == "destroyed"))

    # 6. DEADLINE: a machine that never finishes is TIMED OUT at budgets.timeout_s and force-torn-down --------
    clock3 = _FakeClock()
    api3 = _FakeMachinesAPI(states=["started"], never_finishes=True)
    r3 = Runner(api3, cfg, clock=clock3, sleep=clock3.sleep, receipts_path=_throwaway_receipts()).launch(unit)
    checks.append(("deadline: a never-finishing run is TIMED OUT (outcome=timeout)", r3["outcome"] == "timeout"))
    checks.append(("deadline: timeout fired within deadline_s + grace (budget enforced, not infinite)",
                   r3["duration_s"] <= unit["budgets"]["timeout_s"] + DEADLINE_GRACE_S + POLL_INTERVAL_MAX_S))
    checks.append(("deadline: the timed-out machine was force-torn-down (no leaked machine)",
                   r3["teardown"] == "destroyed" and api3.destroyed == [r3["machine_id"]]))

    # 7. CAPACITY ERROR on create: honest 'create_capacity_error', NOTHING created/leaked -------------------
    clock4 = _FakeClock()
    api4 = _FakeMachinesAPI(states=["stopped"], capacity_on_first_create=True)
    r4 = Runner(api4, cfg, clock=clock4, sleep=clock4.sleep, receipts_path=_throwaway_receipts()).launch(unit)
    checks.append(("capacity: a create CapacityError → honest outcome, no machine, no teardown",
                   r4["outcome"] == "create_capacity_error" and api4.created == [] and api4.destroyed == []))
    checks.append(("capacity: the failure receipt STILL carries unit lineage", r4["unit_id"] == unit["unit_id"]))

    # 8. RATE LIMIT on create: one polite retry then success (the controller's typed error is handled) -------
    clock6 = _FakeClock()
    api6 = _FakeMachinesAPI(states=["started", "stopped"], exit_code=0, rate_limit_first_create=True)
    r6 = Runner(api6, cfg, clock=clock6, sleep=clock6.sleep, receipts_path=_throwaway_receipts()).launch(unit)
    checks.append(("rate-limit: a 429 on create is retried once then succeeds",
                   api6.create_calls == 2 and r6["outcome"] == "completed"))

    # 9. the create plan is faithful + leaks no secret values + records the deadline-enforcement honesty ------
    plan = create_plan(unit)
    checks.append(("plan: names the target app/region from the topology (aidr-teleon-runner / iad)",
                   plan["fly_app"].endswith("-teleon-runner") and plan["fly_region"] == "iad"))
    checks.append(("plan: deadline_s from the unit + honest 'enforced by the runner' note",
                   plan["deadline_s"] == unit["budgets"]["timeout_s"]
                   and "poll loop" in plan["deadline_enforced_by"]))
    checks.append(("plan: env_refs are NAMES only, no secret values, no TELEON_UNIT_ID noise",
                   all(not str(v).startswith(("sk-", "AKIA")) for v in plan["env_refs"])
                   and UNIT_ENV_KEY not in plan["env_refs"]))
    checks.append(("plan: budget_basis carried through (honest about where each number came from)",
                   plan["budget_basis"] == unit["budgets"]["budget_basis"]))

    # 10. RECEIPT PERSISTENCE: the receipt is actually appended to a JSONL sink (real write, re-readable) -----
    tmp = _throwaway_receipts()
    Runner(_FakeMachinesAPI(states=["started", "stopped"], exit_code=0), cfg,
           clock=_FakeClock(), sleep=_FakeClock().sleep, receipts_path=tmp).launch(unit)
    written = [json.loads(line) for line in tmp.read_text(encoding="utf-8").splitlines() if line.strip()]
    checks.append(("persistence: a receipt line is appended to the JSONL sink with the unit_id",
                   len(written) == 1 and written[0]["unit_id"] == unit["unit_id"]
                   and written[0]["schema"] == "TeleonRunReceipt.v1"))

    # 11. REUSE PROOF: the Machines client is the controller's, only extended (not duplicated) ----------------
    checks.append(("reuse: RunnerMachinesAPI subclasses the controller's MachinesAPI (HTTP/RESP not duplicated)",
                   issubclass(RunnerMachinesAPI, MachinesAPI)
                   and RunnerMachinesAPI.get.__qualname__.startswith("RunnerMachinesAPI")
                   and RunnerMachinesAPI._call is MachinesAPI._call))
    # the runner handles the controller's REAL typed errors (we raised them from the fake above) — proven by 7 & 8
    checks.append(("reuse: the runner handles the controller's typed errors (CapacityError + RateLimited)",
                   r4["outcome"] == "create_capacity_error" and api6.create_calls == 2))

    # 12. NO-TOKEN HONEST DRY RUN: cmd_launch on a valid unit with no token PLANS, exit 3, launches NOTHING ---
    no_token_exit, created_anything = _no_token_probe(unit)
    checks.append(("no-token: --launch without FLY_API_TOKEN is an honest dry-run (exit 3, NO launch)",
                   no_token_exit == 3 and not created_anything))

    # 13. WATCH MODE (the aidr-teleon-runner app): poll the registry, launch each active unit ONCE -------------
    import tempfile as _tempfile
    from src.teleon.compiler import open_registry as _open_reg
    _wd = Path(_tempfile.mkdtemp())
    _reg_log = _wd / "compiled-units.jsonl"
    _open_reg(log_path=_reg_log).register(unit)               # one active, promoted, fly_machine unit
    _wr = _wd / "runner-receipts.jsonl"
    _wclock = _FakeClock()
    _wapi = _FakeMachinesAPI(states=["started", "stopped"], exit_code=0)
    _wrunner = Runner(_wapi, cfg, clock=_wclock, sleep=_wclock.sleep, receipts_path=_wr)
    _s1 = watch_once(registry_log=_reg_log, runner=_wrunner, receipts_path=_wr, emit=lambda *_a: None)
    checks.append(("watch: launches a new active unit (1 launched, 1 machine created)",
                   _s1["launched"] == [unit["unit_id"]] and _wapi.create_calls == 1))
    _s2 = watch_once(registry_log=_reg_log, runner=_wrunner, receipts_path=_wr, emit=lambda *_a: None)
    checks.append(("watch: an already-launched unit is SKIPPED (idempotent — no re-launch)",
                   _s2["launched"] == [] and _wapi.create_calls == 1))
    _s3 = watch_once(registry_log=_reg_log, runner=None,
                     receipts_path=_wd / "fresh.jsonl", emit=lambda *_a: None)
    checks.append(("watch: a NO-TOKEN pass PLANS the active unit, never launches (honest dry-run)",
                   _s3["planned"] == [unit["unit_id"]] and _s3["launched"] == []))

    failed = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
    print(("PASS — " if not failed else "FAIL — ") + f"{len(checks) - len(failed)}/{len(checks)} runner self-test checks")
    return 1 if failed else 0


def _throwaway_receipts() -> Path:
    """A unique temp receipts path for a self-test launch (real append-write, never touches the live sink)."""
    import tempfile
    fd, name = tempfile.mkstemp(prefix="teleon-runner-selftest-", suffix=".jsonl")
    os.close(fd)
    return Path(name)


def _no_token_probe(unit: dict) -> tuple[int, bool]:
    """Run cmd_launch on a written-out valid unit with FLY_API_TOKEN cleared, asserting it never reaches the API.
    Returns (exit_code, created_anything). Uses a sentinel API factory that would explode if a real launch were
    attempted — proving the no-token path is a PLAN, not a launch."""
    import tempfile
    fd, name = tempfile.mkstemp(prefix="teleon-runner-unit-", suffix=".json")
    os.close(fd)
    Path(name).write_text(json.dumps(unit), encoding="utf-8")
    saved = os.environ.pop("FLY_API_TOKEN", None)
    # a tripwire: if the no-token path ever constructed a live client + created a machine, this would flip True.
    tripwire = {"created": False}
    orig_create = RunnerMachinesAPI.create

    def _boom(self, config, region):  # pragma: no cover - must never run in the no-token path
        tripwire["created"] = True
        raise AssertionError("no-token path attempted a REAL launch")

    RunnerMachinesAPI.create = _boom  # type: ignore[assignment]
    try:
        rc = cmd_launch(name)
    finally:
        RunnerMachinesAPI.create = orig_create  # type: ignore[assignment]
        if saved is not None:
            os.environ["FLY_API_TOKEN"] = saved
        try:
            os.unlink(name)
        except OSError:
            pass
    return rc, tripwire["created"]


if __name__ == "__main__":
    raise SystemExit(main())
