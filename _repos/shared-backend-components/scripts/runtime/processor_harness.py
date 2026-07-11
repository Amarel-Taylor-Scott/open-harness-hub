#!/usr/bin/env python3
"""scripts.runtime.processor_harness — the one wrapper every processor runs inside.

validate command schema → resolve processor from the registry → open a structured log span → call
``processor.handle()`` → validate the ProcessorResult + every emitted ArtifactEnvelope (envelope AND its
declared artifact schema) → write artifacts / publish events / enqueue follow-up commands through the
ctx ports → classify any failure into an ErrorEnvelope (retryable vs permanent) → return a status the
durable worker uses to ack/nack. Processor authors write only business logic; the harness does the rest.
"""
from __future__ import annotations

from scripts.runtime.envelopes import CommandEnvelope, ErrorEnvelope
from scripts.runtime.processor_registry import ProcessorRegistry, UnavailableProcessor
from scripts.runtime.schema_validator import SCHEMA_DIR, validate_ref


def _fail(error: ErrorEnvelope, ctx) -> dict:
    ctx.logger.error("processor.failed", message=error.message, error_type=error.error_type,
                     retryable=error.retryable)
    return {"ok": False, "status": "failed", "retryable": error.retryable,
            "error": error.to_dict(), "result": None}


def _raw_of(command) -> dict:
    """Coerce ANY incoming command into a plain dict WITHOUT raising. A non-mapping payload (None / list /
    str / int / a bad iterable) must become a clean schema-validation failure, never a worker crash."""
    if isinstance(command, CommandEnvelope):
        return command.to_dict()
    if isinstance(command, dict):
        return dict(command)
    try:
        return dict(command)  # mapping-like or an iterable of key/value pairs
    except (TypeError, ValueError):
        return {}


def run_command(registry: ProcessorRegistry, command, ctx) -> dict:
    # 1) validate the RAW command envelope FIRST (before normalization, so a missing/invalid field is caught
    #    and never masked by dataclass defaults). _raw_of never raises, so a malformed payload fails safely.
    raw = _raw_of(command)
    cerrs = validate_ref(raw, "envelopes/CommandEnvelope")
    if cerrs:
        ctx.logger.error("schema.validation.failed", message="invalid CommandEnvelope", fields={"errors": cerrs})
        # copy every identifier we can salvage from the raw payload so the ErrorEnvelope is traceable even
        # though `cmd` was never safely constructed.
        return _fail(ErrorEnvelope("schema_validation_failed", False, f"invalid CommandEnvelope: {cerrs[:3]}",
                                   failed_schema="CommandEnvelope",
                                   command_id=str(raw.get("command_id", "")), run_id=str(raw.get("run_id", "")),
                                   step_id=str(raw.get("step_id", "")), processor_id=str(raw.get("processor_id", "")),
                                   processor_version=str(raw.get("processor_version", ""))), ctx)
    cmd = command if isinstance(command, CommandEnvelope) else CommandEnvelope.from_dict(raw)

    # 2) resolve the processor (registry only — never a direct import)
    try:
        proc = registry.get(cmd.processor_id, cmd.processor_version)
    except UnavailableProcessor as e:
        return _fail(ErrorEnvelope("unavailable_processor", False, f"no processor {e}",
                                   run_id=cmd.run_id, step_id=cmd.step_id), ctx)

    log = ctx.logger.child(step_id=cmd.step_id, processor_id=cmd.processor_id, processor_version=cmd.processor_version)
    log.info("pipeline.step.started", command_id=cmd.command_id, command_type=cmd.command_type)

    # 3) run business logic
    try:
        result = proc.handle(cmd, ctx)
    except Exception as e:  # noqa: BLE001 — any processor exception becomes a retryable ErrorEnvelope
        return _fail(ErrorEnvelope("processor_exception", True, f"{type(e).__name__}: {e}",
                                   processor_id=cmd.processor_id, processor_version=cmd.processor_version,
                                   run_id=cmd.run_id, step_id=cmd.step_id), ctx)

    # 4) validate the ProcessorResult
    rdict = result.to_dict()
    rerrs = validate_ref(rdict, "envelopes/ProcessorResult")
    if rerrs:
        return _fail(ErrorEnvelope("validation_failed", False, f"invalid ProcessorResult: {rerrs[:3]}",
                                   failed_schema="ProcessorResult", run_id=cmd.run_id, step_id=cmd.step_id), ctx)
    if not result.ok:
        errs = result.errors or [{"message": "processor returned ok=false"}]
        first = errs[0] if isinstance(errs[0], dict) else errs[0].to_dict()
        return _fail(ErrorEnvelope("processor_exception", bool(first.get("retryable", True)),
                                   str(first.get("message", "failed")), run_id=cmd.run_id, step_id=cmd.step_id), ctx)

    # 5) validate every emitted artifact (envelope + its declared artifact schema if one exists)
    for art in result.artifacts:
        ad = art.to_dict() if hasattr(art, "to_dict") else art
        aerrs = validate_ref(ad, "envelopes/ArtifactEnvelope")
        asv = ad.get("artifact_schema_version", "")
        if asv and (SCHEMA_DIR / "artifacts" / f"{asv}.schema.json").exists():
            aerrs += validate_ref(ad.get("payload", {}), f"artifacts/{asv}")
        if aerrs:
            return _fail(ErrorEnvelope("schema_validation_failed", False, f"invalid artifact {ad.get('artifact_id')}: {aerrs[:3]}",
                                       failed_schema=asv or "ArtifactEnvelope", run_id=cmd.run_id, step_id=cmd.step_id), ctx)

    # 6) side effects through ports only
    for art in result.artifacts:
        ctx.artifact_store.write(art)
        log.info("artifact.created", artifact_id=getattr(art, "artifact_id", None), artifact_type=getattr(art, "artifact_type", None))
    if ctx.event_bus is not None:
        for ev in result.events:
            ctx.event_bus.publish_event(ev)
    if ctx.durable_store is not None:
        for c in result.commands:
            cd = c.to_dict() if hasattr(c, "to_dict") else c
            ctx.durable_store.enqueue(cd.get("queue", "runtime.commands"), cd, idempotency_key=cd.get("idempotency_key", ""))

    log.info("pipeline.step.completed", artifact_count=len(result.artifacts), metrics=result.metrics)
    log.info("processor.completed", **{k: v for k, v in result.metrics.items() if isinstance(v, (int, float, str))})
    return {"ok": True, "status": "ok", "retryable": None, "result": rdict, "error": None}
