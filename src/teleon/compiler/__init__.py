"""src.teleon.compiler — the Teleon capability runtime compiler.

Teleon is the BACKBONE of every runtime/function. This package is the deterministic compiler that turns a
PROMOTED capability (its spec + gate evidence + receipts) into a deployable RUNTIME UNIT — the per-capability
analog of the per-service ``architecture/deploy_topology.json`` plane, built on the SAME proven generator pattern
as ``scripts/deploy/generate_provider_configs.py`` (declarative source → provider configs, drift-gated,
self-tested), but for capabilities instead of services.

  * ``compile_capability(capability, task_spec, *, exec_target, policy, now, ...)`` — PURE + deterministic compile.
    REFUSES a non-promoted capability (``NotPromotedError`` — only gate-passed capabilities become runtimes).
    Reuses ``src/teleon/purpose_tasks/runtime_binding`` for runtime_class→backend, joins resources/budgets from
    the architecture policy files (no magic values), attaches gate evidence + receipt refs (lossless lineage).
  * ``emit(unit, exec_target)`` — render the unit into the concrete deployable text: a Fly machine config (JSON),
    a Kubernetes Job manifest (YAML), or a local process spec. PORTABLE: every unit emits all three; never
    cloud-locked.
  * ``CompiledUnitRegistry`` (``registry.py``) — the durable, append-only REGISTRY of compiled units: the
    per-capability analog of the per-service ``architecture/deploy_topology.json``. It tracks which
    capability-version is compiled to which runtime, preserves full history (superseded units are DEMOTED, not
    deleted — lossless), and makes the unit's ``rollback_target`` field REAL (``rollback_target(cap)`` returns the
    exact prior promoted unit; ``rollback_to(cap)`` re-activates it). Backed by ``scripts._jsonl_store.AppendLog``;
    the JSONL lives under ``dist/local-services-state/teleon-compiler/`` (the Fly volume mount).

ARCHITECTURAL LAW: Teleon-layer code (the runtime compiler is a runtime concern). It imports only stdlib +
``src.teleon`` siblings + ``scripts`` tooling; it must never import ``src.baltor`` / ``src.openharnesshub``.
Doc: ``docs/architecture/teleon-capability-runtime-compiler.md``.
"""
from .compile import (compile_capability, validate_unit, memory_to_mb, CompilerError, NotPromotedError,
                      COMPILER_VERSION, SCHEMA_VERSION, UNIT_SCHEMA_REF, PROMOTED_STATUS, EXEC_TARGETS)
from .emit import emit, emit_fly_machine, emit_k8s_job, emit_local_process, build_k8s_job
from .registry import (CompiledUnitRegistry, open_registry, register_units, RegistryError, RegistryIntegrityError,
                       REGISTRY_RECORD_VERSION, KIND_REGISTER, KIND_DEMOTE, RECORD_KINDS, DEFAULT_STATE_DIR,
                       DEFAULT_LOG_NAME)

__all__ = ["compile_capability", "validate_unit", "memory_to_mb", "CompilerError", "NotPromotedError",
           "COMPILER_VERSION", "SCHEMA_VERSION", "UNIT_SCHEMA_REF", "PROMOTED_STATUS", "EXEC_TARGETS",
           "emit", "emit_fly_machine", "emit_k8s_job", "emit_local_process", "build_k8s_job",
           "CompiledUnitRegistry", "open_registry", "register_units", "RegistryError", "RegistryIntegrityError",
           "REGISTRY_RECORD_VERSION", "KIND_REGISTER", "KIND_DEMOTE", "RECORD_KINDS", "DEFAULT_STATE_DIR",
           "DEFAULT_LOG_NAME"]
