#!/usr/bin/env python3
"""scripts.runtime.envelopes — the five versioned inter-module contract shapes (the C32 contract layer).

Every payload that crosses a module boundary — work to do, facts about what happened, stored objects,
processor results, failures — is one of these envelopes, so CFPB → ESG → contracts → PDFs → customer DBs
→ LLM extractors can be swapped without rewriting the runtime. These are SHAPES, not a bus: the bus stays
``scripts.context_events`` and durability stays ``scripts.durable_store``.

  CommandEnvelope — work to be done (durable queue payload)
  EventEnvelope   — a fact about what happened (CloudEvents 1.0-compatible)
  ArtifactEnvelope— a stored object (lineage + governance + security)
  ProcessorResult — what a processor returns (artifacts/events/commands/metrics)
  ErrorEnvelope   — a classified failure (retryable vs permanent)

Determinism: ids are content-derived and ``created_at`` is INJECTED (never a clock read), so envelopes are
byte-stable in proofs (the C45 lesson). Canonical field names are enforced (see CANONICAL_FIELDS + the
schema validator); no ``customerId``/``job``/``pipelineVersion`` aliases past the boundary.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

EPOCH = "1970-01-01T00:00:00Z"

#: canonical names used everywhere; alternatives must be normalised at the boundary, never leaked inward.
CANONICAL_FIELDS = (
    "tenant_id", "run_id", "step_run_id", "pipeline_id", "pipeline_version", "processor_id",
    "processor_version", "artifact_id", "artifact_type", "source_id", "source_version",
    "source_snapshot_hash", "content_hash", "config_hash", "idempotency_key", "correlation_id",
    "causation_id", "trace_id", "created_at", "started_at", "finished_at", "status",
)


def content_hash(obj: Any) -> str:
    return "sha256:" + hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()[:24]


def _hid(prefix: str, obj: Any) -> str:
    return f"{prefix}-" + content_hash(obj).split(":")[1][:16]


@dataclass
class CommandEnvelope:
    command_type: str
    tenant_id: str
    run_id: str
    queue: str
    pipeline_id: str = ""
    pipeline_version: str = ""
    step_id: str = ""
    processor_id: str = ""
    processor_version: str = ""
    priority: str = "p2"
    idempotency_key: str = ""
    correlation_id: str = ""
    causation_id: str = ""
    payload: dict = field(default_factory=dict)
    created_at: str = EPOCH
    command_id: str = ""
    schema_version: str = "CommandEnvelope"

    def __post_init__(self) -> None:
        if not self.command_id:
            self.command_id = _hid("cmd", {"t": self.command_type, "run": self.run_id, "step": self.step_id,
                                            "idk": self.idempotency_key, "p": self.payload})
        if not self.correlation_id:
            self.correlation_id = self.run_id
        if not self.idempotency_key:
            self.idempotency_key = self.command_id

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "CommandEnvelope":
        return CommandEnvelope(**{k: d[k] for k in d if k in CommandEnvelope.__dataclass_fields__})


@dataclass
class EventEnvelope:
    """CloudEvents 1.0-compatible: specversion/id/source/type/time/datacontenttype/subject/data + baltor fields."""
    type: str
    source: str
    subject: str
    tenant_id: str
    run_id: str
    data: dict = field(default_factory=dict)
    correlation_id: str = ""
    causation_id: str = ""
    trace_id: str = ""
    time: str = EPOCH
    id: str = ""
    specversion: str = "1.0"
    datacontenttype: str = "application/json"
    baltor_schema: str = "EventEnvelope"

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _hid("evt", {"type": self.type, "subject": self.subject, "data": self.data})
        if not self.correlation_id:
            self.correlation_id = self.run_id
        if not self.trace_id:
            self.trace_id = self.run_id

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "EventEnvelope":
        return EventEnvelope(**{k: d[k] for k in d if k in EventEnvelope.__dataclass_fields__})


@dataclass
class ArtifactEnvelope:
    artifact_id: str
    tenant_id: str
    artifact_type: str
    artifact_schema_version: str
    content_hash: str
    payload: dict = field(default_factory=dict)
    payload_ref: str | None = None
    source_artifact_ids: list = field(default_factory=list)
    parent_artifact_ids: list = field(default_factory=list)
    lineage: dict = field(default_factory=dict)       # run_id, pipeline_id/version, processor_id/version, processor_config_hash
    governance: dict = field(default_factory=dict)    # claim_status, promotion_eligible, model_dependent, requires_human_review
    security: dict = field(default_factory=dict)      # classification, kms_key_ref, retention_policy_id
    schema_version: str = "ArtifactEnvelope"

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "ArtifactEnvelope":
        return ArtifactEnvelope(**{k: d[k] for k in d if k in ArtifactEnvelope.__dataclass_fields__})


@dataclass
class ErrorEnvelope:
    error_type: str
    retryable: bool
    message: str
    processor_id: str = ""
    processor_version: str = ""
    run_id: str = ""
    step_id: str = ""
    command_id: str = ""
    failed_schema: str = ""
    details: dict = field(default_factory=dict)
    error_id: str = ""
    schema_version: str = "ErrorEnvelope"

    def __post_init__(self) -> None:
        if not self.error_id:
            self.error_id = _hid("err", {"type": self.error_type, "msg": self.message, "run": self.run_id, "step": self.step_id})

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProcessorResult:
    ok: bool
    run_id: str
    step_id: str
    processor_id: str
    processor_version: str
    artifacts: list = field(default_factory=list)     # list[ArtifactEnvelope|dict]
    events: list = field(default_factory=list)        # list[EventEnvelope|dict]
    commands: list = field(default_factory=list)      # list[CommandEnvelope|dict]
    metrics: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)        # list[ErrorEnvelope|dict]
    schema_version: str = "ProcessorResult"

    @staticmethod
    def make_ok(*, run_id: str, step_id: str, processor_id: str, processor_version: str,
                artifacts=None, events=None, commands=None, metrics=None, warnings=None) -> "ProcessorResult":
        return ProcessorResult(True, run_id, step_id, processor_id, processor_version,
                               artifacts=list(artifacts or []), events=list(events or []),
                               commands=list(commands or []), metrics=dict(metrics or {}), warnings=list(warnings or []))

    @staticmethod
    def make_fail(*, run_id: str, step_id: str, processor_id: str, processor_version: str,
                  errors: list) -> "ProcessorResult":
        return ProcessorResult(False, run_id, step_id, processor_id, processor_version, errors=list(errors))

    def to_dict(self) -> dict:
        def ser(x):
            return x.to_dict() if hasattr(x, "to_dict") else x
        d = asdict(self)
        d["artifacts"] = [ser(a) for a in self.artifacts]
        d["events"] = [ser(e) for e in self.events]
        d["commands"] = [ser(c) for c in self.commands]
        d["errors"] = [ser(e) for e in self.errors]
        return d
