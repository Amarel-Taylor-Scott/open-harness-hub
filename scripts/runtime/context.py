#!/usr/bin/env python3
"""scripts.runtime.context — RuntimeContext + lightweight in-memory port adapters for tests/local runs.

A processor receives a frozen RuntimeContext carrying its ids + every capability port. It never imports the
admin server, the global BUS, or a vendor SDK — it calls ``ctx.artifact_store.write(...)``,
``ctx.event_bus.publish_event(...)``, ``ctx.logger.info(...)``, etc. The default adapters here (in-memory
artifact store, buffered event bus, fixed clock) make the harness + processors testable offline; production
swaps in the SQLite/object-store/context_events adapters with no processor change.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from scripts.runtime.logger import RuntimeLogger


@dataclass
class FixedClock:
    value: str = "1970-01-01T00:00:00Z"

    def now_iso(self) -> str:
        return self.value


class InMemoryArtifactStore:
    """Collects ArtifactEnvelopes; load_inputs returns artifacts named by the command payload."""
    def __init__(self) -> None:
        self.artifacts: list = []
        self._by_id: dict = {}

    def write(self, artifact) -> None:
        self.artifacts.append(artifact)
        aid = getattr(artifact, "artifact_id", None) or (artifact.get("artifact_id") if isinstance(artifact, dict) else None)
        if aid:
            self._by_id[aid] = artifact

    def load_inputs(self, command) -> list:
        payload = command.payload if hasattr(command, "payload") else command.get("payload", {})
        if "records" in payload:
            return list(payload["records"])
        if "record" in payload:
            return [payload["record"]]
        ids = payload.get("input_artifact_ids", [])
        return [self._by_id[i] for i in ids if i in self._by_id]


class BufferEventBus:
    """Buffers published EventEnvelopes (the proof's inspection point); not a second bus — a port adapter."""
    def __init__(self) -> None:
        self.events: list = []

    def publish_event(self, event) -> None:
        self.events.append(event)


@dataclass(frozen=True)
class RuntimeContext:
    tenant_id: str
    run_id: str
    trace_id: str
    correlation_id: str
    pipeline_id: str
    pipeline_version: str
    step_id: str
    logger: RuntimeLogger
    artifact_store: Any = None
    object_store: Any = None
    vector_store: Any = None
    event_bus: Any = None
    durable_store: Any = None
    secrets: Any = None
    llm_gateway: Any = None
    clock: Any = field(default_factory=FixedClock)


def build_context(*, tenant_id: str, run_id: str, pipeline_id: str = "", pipeline_version: str = "",
                  step_id: str = "", trace_id: str = "", correlation_id: str = "",
                  artifact_store=None, object_store=None, vector_store=None, event_bus=None,
                  durable_store=None, secrets=None, llm_gateway=None, clock=None) -> RuntimeContext:
    clock = clock or FixedClock()
    trace_id = trace_id or run_id
    correlation_id = correlation_id or run_id
    logger = RuntimeLogger(tenant_id=tenant_id, run_id=run_id, step_id=step_id, trace_id=trace_id,
                           correlation_id=correlation_id, clock=clock)
    return RuntimeContext(
        tenant_id=tenant_id, run_id=run_id, trace_id=trace_id, correlation_id=correlation_id,
        pipeline_id=pipeline_id, pipeline_version=pipeline_version, step_id=step_id, logger=logger,
        artifact_store=artifact_store if artifact_store is not None else InMemoryArtifactStore(),
        object_store=object_store, vector_store=vector_store,
        event_bus=event_bus if event_bus is not None else BufferEventBus(),
        durable_store=durable_store, secrets=secrets, llm_gateway=llm_gateway, clock=clock)
