"""src.teleon.compiler.compile — the DETERMINISTIC capability→runtime-unit compiler.

Teleon is the backbone of every runtime/function: it takes a PROMOTED capability (the intent that already
cleared the gate) and compiles it into a deployable RUNTIME UNIT — the per-capability analog of the per-service
``_repos/shared-backend-components/architecture/deploy_topology.json``. This module owns the PURE compile; ``emit.py`` renders the unit into the
three concrete deployable shapes (fly machine / k8s Job / local process).

THE LAW — only promoted capabilities compile. ``compile_capability`` REFUSES a capability whose status is not
``"promoted"`` (raises ``NotPromotedError``). An un-gated capability must never become a runtime; the gate is the
admission boundary and the compiler enforces it structurally (and the schema pins ``gate_evidence.status`` to
``"promoted"``).

DETERMINISM — ``compile_capability`` is PURE: same inputs → byte-identical output. It never reads the clock or
``random``; the caller passes ``now`` (stamped as ``compiled_at``/``promoted_at``) and every id/hash is derived
from the canonicalized inputs. Recompiling the same capability twice yields the identical ``unit_id``.

NO MAGIC VALUES — every field is JOINED from an existing single source, never hand-typed:
  * runtime_class → backend : reused from ``src/teleon/purpose_tasks/runtime_binding`` (``bind_allowed`` — the
    SAME class→backend authority PurposeTask uses; we do not reinvent it).
  * resources{cpu,memory_mb,gpu_required} : ``_repos/shared-backend-components/architecture/worker_resource_classes.json`` keyed by the
    CapabilityTask ``required_resource_class``.
  * budgets.timeout_s : the SLA policy ``target_seconds`` (``_repos/shared-backend-components/architecture/worker_sla_policies.json`` keyed by
    ``sla_policy_id``), else the resource class ``timeout_default_s``.
  * budgets.max_tokens : the OIPS resolved-preference ``budget_policy`` (``max_output_tokens``|``max_tokens``);
    the single named default constant only when the policy omits it (recorded in ``budget_basis``).
  * budgets.max_attempts : the CapabilityTask spec ``max_attempts`` (its declared input).
  * container.image : ``_repos/shared-backend-components/architecture/deploy_topology.json`` ``image.registry_hint`` (one source).

LOSSLESS — the unit carries lineage back to the capability (id+version), the binding decision, the gate evidence,
the receipt refs, and a ``rollback_target`` (the predecessor unit it supersedes). It never discards the source.

HONEST — ``is_truth`` is structurally false; a compiled unit is a deployable plan, not served truth. The
FleetLedger / capability gate remain the source of truth. Demo-grade gaps are labelled in the doc, not hidden.

ARCHITECTURAL LAW — Teleon-layer code: imports only stdlib + ``src.teleon`` siblings + ``scripts`` tooling
(schema validator). It never imports ``src.baltor`` / ``src.openhubforai`` (the portfolio dependency law).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from src.teleon.purpose_tasks import runtime_binding as _rb

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[3])
_A = _resource("architecture")

#: the compiler's own version — changing it changes unit_id, so a recompile under a new compiler is attributable
#: (no-magic-values: one definition, surfaced in provenance + the OTel attrs).
COMPILER_VERSION = "teleon_capability_compiler@v1"
SCHEMA_VERSION = "CompiledRuntimeUnit"
#: the contract schema the produced unit validates against (repo ref form: "<dir>/<Name>", matching the
#: schema's own $id). validate_unit loads schemas/runtime/CompiledRuntimeUnit.schema.json and checks with
#: jsonschema (the unit schema uses union types + const, which the minimal stdlib validator does not cover).
UNIT_SCHEMA_REF = "runtime/CompiledRuntimeUnit"
#: the ONLY capability status that may compile to a runtime (the gate is the admission boundary).
PROMOTED_STATUS = "promoted"
#: the three deployable shapes a unit can emit — PORTABLE by construction (never cloud-locked to one).
EXEC_TARGETS = ("fly_machine", "k8s_job", "local_process")

#: the capability-runner module entrypoint (mirrors deploy_topology's teleon-runtime command shape: a -m module).
#: ONE definition; container.command is built from it, never a parallel literal.
RUNNER_MODULE = "scripts.teleon_local_runtime"
#: budget default ONLY used when neither the OIPS budget_policy nor the SLA policy supplies a token ceiling.
#: A single named constant with a unit + rationale (no-magic-values) — recorded in budget_basis when it fires.
DEFAULT_MAX_OUTPUT_TOKENS = 300   # matches the runtime's per-call max_tokens=300 in _repos/shared-backend-components/scripts/teleon_local_runtime.py
#: env/secret-ref NAMES the capability runtime reads (names only — values never travel in a unit). Joined from
#: the deploy topology's model-plane secret group so the unit and the service plane stay one source.
_DEFAULT_ENV_REF_GROUP = "model-plane"

#: budget_policy token-ceiling keys we accept, in priority order (OIPS budget_policy is intentionally free-form;
#: these are the established token keys — read them, do not invent a new schema field).
_TOKEN_BUDGET_KEYS = ("max_output_tokens", "max_tokens", "token_ceiling")


class CompilerError(Exception):
    """Base for compile refusals (a clear, actionable reason — never a silent wrong unit)."""


class NotPromotedError(CompilerError):
    """THE LAW: a capability whose status is not 'promoted' was handed to the compiler. An un-gated capability
    must never compile to a runtime — the gate is the admission boundary. The message names the offending
    status so a caller (or the CLI) can explain exactly why it was refused."""

    def __init__(self, capability_id: str, status: str) -> None:
        super().__init__(
            f"capability {capability_id!r} has status {status!r}, not {PROMOTED_STATUS!r} — only gate-passed "
            f"(promoted) capabilities compile to a runtime. Run the eval gate to promotion first, then compile.")
        self.capability_id = capability_id
        self.status = status


def _load_json(name: str) -> dict:
    return json.loads((_A / name).read_text(encoding="utf-8"))


def _canonical(obj: Any) -> str:
    """Canonical JSON (sorted keys, tight separators) — the basis for deterministic hashing/ids."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _stable_id(prefix: str, *parts: str) -> str:
    return f"{prefix}_" + hashlib.blake2b("|".join(parts).encode("utf-8"), digest_size=12).hexdigest()


# ── memory parsing (Kubernetes quantity → MB, deterministic; no magic multipliers typed twice) ───────────────
_MEM_UNITS_BYTES = {  # one table: binary (Ki/Mi/Gi/Ti) + decimal (k/M/G/T) SI suffixes → bytes
    "": 1, "k": 10 ** 3, "M": 10 ** 6, "G": 10 ** 9, "T": 10 ** 12,
    "Ki": 2 ** 10, "Mi": 2 ** 20, "Gi": 2 ** 30, "Ti": 2 ** 40,
}
_MB = 10 ** 6  # 1 MB = 10^6 bytes (memory_mb is reported in decimal MB; one definition)
_MEM_RE = re.compile(r"^\s*([0-9]*\.?[0-9]+)\s*([A-Za-z]*)\s*$")


def memory_to_mb(quantity: str) -> int:
    """Parse a Kubernetes memory quantity ('512Mi','2Gi','256M','128') to an integer number of MB, deterministically.
    Binary (Mi/Gi) and decimal (M/G) suffixes both supported (one shared unit table — no duplicated multipliers)."""
    m = _MEM_RE.match(str(quantity))
    if not m:
        raise CompilerError(f"unparseable memory quantity {quantity!r} (expected e.g. '512Mi', '2Gi', '256M')")
    value, suffix = float(m.group(1)), m.group(2)
    if suffix not in _MEM_UNITS_BYTES:
        raise CompilerError(f"unknown memory unit {suffix!r} in {quantity!r}")
    return int(round(value * _MEM_UNITS_BYTES[suffix] / _MB))


# ── resource resolution (_repos/shared-backend-components/architecture/worker_resource_classes.json) ──────────────────────────────────────────
def _resource_class_record(resource_class: str, resource_classes: dict) -> dict:
    rec = next((c for c in resource_classes.get("classes", []) if c["class_id"] == resource_class), None)
    if rec is None:
        known = ", ".join(c["class_id"] for c in resource_classes.get("classes", []))
        raise CompilerError(f"required_resource_class {resource_class!r} not in worker_resource_classes.json "
                            f"(known: {known})")
    return rec


def _resolve_resources(resource_class: str, resource_classes: dict) -> dict:
    rec = _resource_class_record(resource_class, resource_classes)
    return {"resource_class": resource_class, "cpu": rec["cpu_request"],
            "memory_mb": memory_to_mb(rec["memory_request"]), "gpu_required": bool(rec["gpu_required"])}


# ── budget resolution (SLA policy + OIPS budget_policy + CapabilityTask spec) ─────────────────────────────────
def _resolve_timeout(task_spec: dict, resource_rec: dict, sla_policies: dict) -> tuple[int, str]:
    """timeout_s = SLA policy target_seconds (joined by sla_policy_id) else the resource class timeout_default_s.
    Returns (timeout_s, basis)."""
    sla_id = task_spec.get("sla_policy_id")
    if sla_id:
        pol = next((p for p in sla_policies.get("policies", []) if p["sla_policy_id"] == sla_id), None)
        if pol is None:
            known = ", ".join(p["sla_policy_id"] for p in sla_policies.get("policies", []))
            raise CompilerError(f"sla_policy_id {sla_id!r} not in worker_sla_policies.json (known: {known})")
        return int(pol["target_seconds"]), f"worker_sla_policies.json:{sla_id}.target_seconds"
    return int(resource_rec["timeout_default_s"]), f"worker_resource_classes.json:{resource_rec['class_id']}.timeout_default_s"


def _resolve_max_tokens(resolved_preference: dict) -> tuple[int, str]:
    """max_tokens from the OIPS resolved-preference budget_policy (free-form: try the established token keys), else
    the single named platform default. Returns (max_tokens, basis)."""
    budget = (resolved_preference.get("effective", {}) or {}).get("budget_policy", {}) or {}
    for key in _TOKEN_BUDGET_KEYS:
        if budget.get(key) is not None:
            return int(budget[key]), f"oips.budget_policy.{key}"
    return DEFAULT_MAX_OUTPUT_TOKENS, f"compiler.DEFAULT_MAX_OUTPUT_TOKENS({DEFAULT_MAX_OUTPUT_TOKENS})"


def _resolve_budgets(task_spec: dict, resource_rec: dict, resolved_preference: dict, sla_policies: dict) -> dict:
    timeout_s, timeout_basis = _resolve_timeout(task_spec, resource_rec, sla_policies)
    max_tokens, tokens_basis = _resolve_max_tokens(resolved_preference)
    if task_spec.get("max_attempts") is None:
        raise CompilerError("CapabilityTask spec is missing max_attempts (the gate's retry ceiling is a required input)")
    max_attempts = int(task_spec["max_attempts"])
    return {"max_tokens": max_tokens, "max_attempts": max_attempts, "timeout_s": timeout_s,
            "budget_basis": {"max_tokens": tokens_basis, "timeout_s": timeout_basis,
                             "max_attempts": "CapabilityTask.spec.max_attempts"}}


# ── container + logging ──────────────────────────────────────────────────────────────────────────────────────
def _resolve_container(capability_id: str, topology: dict, env_refs: list[str] | None) -> dict:
    image = topology.get("image", {}).get("registry_hint")
    if not image:
        raise CompilerError("deploy_topology.json image.registry_hint missing — container.image has no single source")
    refs = list(env_refs) if env_refs is not None else _default_env_refs(topology)
    return {"image": image,
            # the runner argv = -m module + the capability id (mirrors the topology's -m module commands); the
            # capability is self-describing from the unit alone.
            "command": ["python3", "-m", RUNNER_MODULE, "--run-capability", capability_id],
            "env_refs": refs}


def _default_env_refs(topology: dict) -> list[str]:
    """The model-plane secret-ref NAMES the capability runtime reads — joined from the deploy topology's secret
    group contents (one source) so the unit and the service plane never drift. NAMES only, never values."""
    return list(topology.get("secret_group_contents", {}).get(_DEFAULT_ENV_REF_GROUP, []))


def _otel_attrs(unit_id: str, capability_id: str, capability_version: Any, runtime_class: str, exec_target: str,
                trace_id: str | None, span_id: str | None) -> dict:
    """OpenTelemetry-shaped resource attributes for trace correlation — the standardization + logging the owner
    asked for, wired into EVERY unit. service.name follows the OTel semantic-convention key; trace_id/span_id are
    included only when the caller supplies them (deterministic — never minted here)."""
    attrs = {
        "service.name": f"teleon-capability-{capability_id}",
        "service.version": str(capability_version),
        "capability.id": capability_id,
        "capability.version": capability_version,
        "runtime.class": runtime_class,
        "deployment.exec_target": exec_target,
        "teleon.unit_id": unit_id,
        "teleon.compiler_version": COMPILER_VERSION,
    }
    if trace_id is not None:
        attrs["trace_id"] = trace_id
    if span_id is not None:
        attrs["span_id"] = span_id
    return attrs


# ── gate evidence (from the promoted capability record) ──────────────────────────────────────────────────────
def _gate_evidence(capability: dict, *, gate_basis_default: str) -> dict:
    """Lift the gate evidence off the promoted capability record. status is pinned 'promoted' (we only reach here
    for a promoted capability). Rates are passed through honestly (None when the record did not carry them)."""
    return {
        "train_pass_rate": capability.get("train_pass_rate"),
        "holdout_pass_rate": capability.get("holdout_pass_rate"),
        "gate_basis": capability.get("gate_basis") or gate_basis_default,
        "promoted_at": capability.get("promoted_at"),
        "status": PROMOTED_STATUS,
    }


# ── the pure compile ─────────────────────────────────────────────────────────────────────────────────────────
def compile_capability(
    capability: dict,
    task_spec: dict,
    *,
    exec_target: str,
    policy: dict | None = None,
    now: str | None = None,
    rollback_target: str = "",
    receipt_refs: list[str] | None = None,
    resolved_preference: dict | None = None,
    gate_basis_default: str = "train+holdout",
    # injected single-source data (defaults loaded from _repos/shared-backend-components/architecture/*.json) — overridable for testing/determinism
    resource_classes: dict | None = None,
    sla_policies: dict | None = None,
    topology: dict | None = None,
    runtime_classes: dict | None = None,
    policy_matrix: dict | None = None,
    env_refs: list[str] | None = None,
) -> dict[str, Any]:
    """Compile ONE promoted capability + its CapabilityTask spec into a CompiledRuntimeUnit dict.

    PURE + DETERMINISTIC: identical inputs (including ``now``) → byte-identical output. The compiler never reads
    the clock or random; ``now`` is the caller's timestamp (stamped as ``compiled_at`` and used for nothing else).

    THE LAW: raises ``NotPromotedError`` when ``capability['status'] != 'promoted'`` — an un-gated capability never
    compiles to a runtime.

    Sources (no magic values): runtime_class→backend via ``runtime_binding.bind_allowed``; resources from
    ``worker_resource_classes.json``; timeout from the SLA policy / resource class; max_tokens from the OIPS
    budget_policy; max_attempts from the task spec; image from ``deploy_topology.json``.

    LOSSLESS: the unit carries ``capability_id``+``capability_version``, the binding decision, the gate evidence,
    ``receipt_refs``, and ``rollback_target`` (the predecessor it supersedes).
    """
    status = capability.get("status")
    capability_id = capability.get("id") or capability.get("capability_id")
    if not capability_id:
        raise CompilerError("capability record has no id/capability_id")
    if status != PROMOTED_STATUS:
        raise NotPromotedError(str(capability_id), str(status))
    if exec_target not in EXEC_TARGETS:
        raise CompilerError(f"unknown exec_target {exec_target!r} (one of {EXEC_TARGETS})")

    resource_classes = resource_classes if resource_classes is not None else _load_json("worker_resource_classes.json")
    sla_policies = sla_policies if sla_policies is not None else _load_json("worker_sla_policies.json")
    topology = topology if topology is not None else _load_json("deploy_topology.json")
    policy = policy or {}
    receipt_refs = list(receipt_refs or [])
    resolved_preference = resolved_preference or {}

    required_resource_class = task_spec.get("required_resource_class")
    if not required_resource_class:
        raise CompilerError("CapabilityTask spec is missing required_resource_class (no resource source to join)")
    resource_rec = _resource_class_record(required_resource_class, resource_classes)

    # runtime class: the task's declared allowed classes (priority order), falling back to a single declared class.
    allowed_runtime_classes = (task_spec.get("allowed_runtime_classes")
                               or ([task_spec["runtime_class"]] if task_spec.get("runtime_class") else []))
    if not allowed_runtime_classes:
        raise CompilerError("CapabilityTask spec declares no runtime class "
                            "(allowed_runtime_classes / runtime_class) — nothing to bind a backend from")

    # REUSE the existing class→backend authority (the same one PurposeTask uses) — never reinvented here.
    binding = _rb.bind_allowed(
        allowed_runtime_classes,
        available_creds=set(policy.get("available_creds", []) or []),
        provider_health=policy.get("provider_health"),
        policy_override=policy.get("policy_override"),
        runtime_classes=runtime_classes,
        policy_matrix=policy_matrix,
    )
    runtime_class = binding["runtime_class"]
    backend = binding["backend"]

    resources = _resolve_resources(required_resource_class, resource_classes)
    budgets = _resolve_budgets(task_spec, resource_rec, resolved_preference, sla_policies)
    container = _resolve_container(str(capability_id), topology, env_refs)
    capability_version = capability.get("version")

    # deterministic source_spec_hash over the canonicalized inputs that DEFINE the unit (not now — now is provenance
    # only). A changed input is detectable; the same inputs always hash the same.
    spec_basis = {
        "capability_id": capability_id, "capability_version": capability_version, "status": status,
        "task_spec": task_spec, "exec_target": exec_target, "policy": policy,
        "resolved_preference": resolved_preference, "receipt_refs": receipt_refs,
        "resources": resources, "budgets": budgets, "container": container, "binding": binding,
        "compiler_version": COMPILER_VERSION,
    }
    source_spec_hash = _sha256(_canonical(spec_basis))
    # unit_id is independent of now (a daily recompile of identical inputs collapses to ONE unit) but pins
    # compiler+capability+version+exec_target+hash so any real change forks a new id.
    unit_id = _stable_id("cru", COMPILER_VERSION, str(capability_id), str(capability_version), exec_target,
                         source_spec_hash)

    trace_id = policy.get("trace_id")
    span_id = policy.get("span_id")
    unit = {
        "schema_version": SCHEMA_VERSION,
        "unit_id": unit_id,
        "capability_id": capability_id,
        "capability_version": capability_version,
        "runtime_class": runtime_class,
        "backend": backend,
        "exec_target": exec_target,
        "binding": binding,
        "container": container,
        "resources": resources,
        "budgets": budgets,
        "logging": {"otel_attrs": _otel_attrs(unit_id, str(capability_id), capability_version, runtime_class,
                                              exec_target, trace_id, span_id)},
        "gate_evidence": _gate_evidence(capability, gate_basis_default=gate_basis_default),
        "receipt_refs": receipt_refs,
        "provenance": {"compiler_version": COMPILER_VERSION, "source_spec_hash": source_spec_hash,
                       "compiled_at": now},
        "rollback_target": rollback_target,
        "is_truth": False,
    }
    return unit


def _unit_schema() -> dict:
    """The CompiledRuntimeUnit schema document (single source: schemas/runtime/CompiledRuntimeUnit)."""
    return json.loads((_resource("schemas") / "runtime" / "CompiledRuntimeUnit.schema.json").read_text(encoding="utf-8"))


def validate_unit(unit: dict) -> list[str]:
    """Schema-validate a compiled unit against runtime/CompiledRuntimeUnit. Uses the full ``jsonschema``
    Draft-2020-12 validator (the unit schema uses union types like ``["integer","number"]`` + ``const`` — the same
    keywords the inference receipt schemas rely on, which the minimal stdlib validator does not cover). Returns a
    sorted list of error strings ([] = valid). Raises if ``jsonschema`` is unavailable (the repo ships it)."""
    import jsonschema  # the repo's contract validator for union-typed schemas (_repos/shared-backend-components/scripts/validate.py uses it too)
    validator = jsonschema.Draft202012Validator(_unit_schema())
    return sorted(f"{'.'.join(str(p) for p in e.path) or '$'}: {e.message}" for e in validator.iter_errors(unit))


__all__ = ["compile_capability", "validate_unit", "memory_to_mb", "CompilerError", "NotPromotedError",
           "COMPILER_VERSION", "SCHEMA_VERSION", "UNIT_SCHEMA_REF", "PROMOTED_STATUS", "EXEC_TARGETS",
           "DEFAULT_MAX_OUTPUT_TOKENS", "RUNNER_MODULE"]
