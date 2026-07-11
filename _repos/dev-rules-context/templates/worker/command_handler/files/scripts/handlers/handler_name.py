#!/usr/bin/env python3
"""scripts.handlers.{{handler_name}} — durable command handler for {{title}} ({{command_type}}).

GENERATED STUB (standard.durable_command). A handler is `handle(store, job) -> dict`: it runs against the
ONE durable store (no second queue/bus/worker framework), is idempotent (records its identity once so a
double-process is detectable), and distinguishes permanent vs retryable failure (PermanentJobError ->
immediate DLQ; raise RuntimeError -> nack -> retry -> DLQ). The flywheel_worker default handler routes
{{command_type}} here. Deterministic: idempotency key is content-addressed, no wall-clock.

TODO(stub): implement the real {{command_type}} effect, then delete the NotImplemented guard.
"""
from __future__ import annotations

import hashlib
import json

COMMAND_TYPE = "{{command_type}}"
QUEUE_NAME = "{{queue_name}}"


class PermanentJobError(Exception):
    """A job that can never succeed (e.g. schema-invalid payload). Dead-letters immediately."""


def idempotency_key(payload: dict) -> str:
    """Content-addressed (NOT wall-clock) so a duplicate command does not re-run the effect."""
    body = {"command_type": COMMAND_TYPE, "tenant_id": payload.get("tenant_id"),
            "subject": payload.get("subject_id") or payload.get("object_ref")}
    return "idem-" + hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]


def handle(store, job: dict) -> dict:
    p = job.get("payload") or {}
    if p.get("command_type") != COMMAND_TYPE:
        raise PermanentJobError(f"{{handler_name}}: wrong command_type {p.get('command_type')!r}")
    key = idempotency_key(p)
    first = store.mark_processed("{{handler_name}}", key)  # idempotency guard
    if not first:
        return {"command_type": COMMAND_TYPE, "ok": True, "skipped": True, "idempotency_key": key}
    # TODO(stub): perform the real {{command_type}} effect here, then emit a durable event.
    raise NotImplementedError("{{handler_name}}.handle is a generated stub — implement the {{command_type}} effect")
