#!/usr/bin/env python3
"""scripts.runtime.logger — structured JSON logging with stable event names + correlation fields.

Every log record is one JSON object with the canonical correlation fields (tenant_id, run_id, step_id,
processor_id/version, trace_id, correlation_id) and a STABLE, searchable ``event`` name (runtime.command.*,
pipeline.step.*, artifact.created, schema.validation.failed, …) — no ad-hoc "done"/"ok"/"processed 5".
Values are redacted so a secret can never land in a log line.
"""
from __future__ import annotations

import json
import re
import sys

# stable, searchable log event names
EVENTS = (
    "runtime.command.claimed", "runtime.command.acked", "runtime.command.nacked",
    "pipeline.run.started", "pipeline.step.started", "pipeline.step.completed",
    "artifact.created", "vector.created", "graph.edge.created", "conflict.detected",
    "reconciliation.completed", "llm.request.started", "llm.request.completed", "llm.request.failed",
    "schema.validation.failed", "processor.completed", "processor.failed",
)
_SECRET = re.compile(r"\bsk-[A-Za-z0-9_\-]{12,}\b")


def _redact(value):
    if isinstance(value, str):
        return _SECRET.sub("sk-***REDACTED***", value)
    if isinstance(value, dict):
        return {k: ("***REDACTED***" if ("key" in k.lower() or "secret" in k.lower() or "token" in k.lower())
                    else _redact(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(v) for v in value]
    return value


class RuntimeLogger:
    def __init__(self, *, tenant_id: str = "", run_id: str = "", step_id: str = "",
                 processor_id: str = "", processor_version: str = "", trace_id: str = "",
                 correlation_id: str = "", clock=None, sink=None) -> None:
        self.base = {"tenant_id": tenant_id, "run_id": run_id, "step_id": step_id,
                     "processor_id": processor_id, "processor_version": processor_version,
                     "trace_id": trace_id, "correlation_id": correlation_id}
        self.clock = clock
        self.records: list[dict] = []           # in-memory tail (also the proof's inspection point)
        self._sink = sink                       # callable(line:str); default stderr

    def _emit(self, level: str, event: str, message: str, fields: dict) -> dict:
        ts = self.clock.now_iso() if self.clock else "1970-01-01T00:00:00Z"
        rec = {"timestamp": ts, "level": level, "event": event, **self.base,
               "message": _redact(message), "fields": _redact(fields)}
        self.records.append(rec)
        line = json.dumps(rec, sort_keys=True)
        (self._sink or (lambda s: print(s, file=sys.stderr)))(line)
        return rec

    def info(self, event: str, message: str = "", **fields) -> dict:
        return self._emit("INFO", event, message, fields)

    def warn(self, event: str, message: str = "", **fields) -> dict:
        return self._emit("WARN", event, message, fields)

    def error(self, event: str, message: str = "", **fields) -> dict:
        return self._emit("ERROR", event, message, fields)

    def child(self, **overrides) -> "RuntimeLogger":
        b = {**self.base, **overrides}
        lg = RuntimeLogger(clock=self.clock, sink=self._sink, **b)
        lg.records = self.records  # share the tail
        return lg
