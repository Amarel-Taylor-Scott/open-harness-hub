#!/usr/bin/env python3
"""scripts.pipeline_runtime.envelope — C26 event-envelope contract (durable causality, stdlib only).

One envelope for every event + command so the whole chain is traceable + idempotent:
  owner-ask → backlog → tick → command → engine-run → proof → pass → review-pack → projection.
Deterministic event_id (content-hash, no clock/RNG) so re-emitting the same logical event is the same
id. `validate_envelope` enforces the contract; `validate_causality_chain` checks every non-root event's
`causation_id` references a known event_id (no dangling causality). `envelope_from_event` lifts an
existing bus event onto the envelope so the contract applies to REAL emits without a 2nd bus.
"""
from __future__ import annotations

import json
from typing import Any

from scripts.foundry.scrapers import content_hash

SCHEMA_VERSION = "v1"
PRIORITIES = ("p0", "p1", "p2", "bulk")
#: load-bearing fields every envelope must carry (the rest are optional metadata).
REQUIRED = ("event_id", "event_type", "schema_version", "correlation_id", "idempotency_key",
            "priority", "attempt", "payload", "evidence")


def make_envelope(event_type: str, *, payload: dict | None = None, correlation_id: str = "",
                  causation_id: str = "", pass_id: str = "", tick_id: str = "", engine: str = "",
                  engine_version: str = "", subject_type: str = "event", subject_id: str = "",
                  trace_id: str = "", idempotency_key: str = "", priority: str = "p2", attempt: int = 1,
                  evidence: dict | None = None, schema_version: str = SCHEMA_VERSION) -> dict:
    payload = payload or {}
    idk = idempotency_key or f"{correlation_id}:{event_type}:{subject_id}"
    # deterministic id over the IDENTITY fields (no clock, no RNG) → same logical event = same id
    identity = json.dumps({"event_type": event_type, "correlation_id": correlation_id,
                           "causation_id": causation_id, "subject_id": subject_id,
                           "idempotency_key": idk, "payload": payload}, sort_keys=True, default=str)
    return {
        "event_id": "evt-" + content_hash(identity)[:16], "event_type": event_type,
        "schema_version": schema_version, "pass_id": pass_id, "tick_id": tick_id, "engine": engine,
        "engine_version": engine_version, "subject_type": subject_type, "subject_id": subject_id,
        "causation_id": causation_id, "correlation_id": correlation_id, "trace_id": trace_id or correlation_id,
        "idempotency_key": idk, "priority": priority, "attempt": int(attempt),
        "payload": payload, "evidence": evidence or {},
    }


def validate_envelope(env: dict) -> list[str]:
    errs: list[str] = []
    for k in REQUIRED:
        if k not in env:
            errs.append(f"missing required field {k!r}")
    if errs:
        return errs
    if not str(env["event_id"]).startswith("evt-"):
        errs.append("event_id must be content-addressed (evt-…)")
    if env["schema_version"] != SCHEMA_VERSION:
        errs.append(f"unknown schema_version {env['schema_version']!r}")
    if env["priority"] not in PRIORITIES:
        errs.append(f"invalid priority {env['priority']!r}")
    if not isinstance(env["attempt"], int) or env["attempt"] < 1:
        errs.append("attempt must be an int >= 1")
    if not isinstance(env["payload"], dict) or not isinstance(env["evidence"], dict):
        errs.append("payload and evidence must be objects")
    if not env["idempotency_key"]:
        errs.append("idempotency_key must be non-empty")
    return errs


def validate_causality_chain(events: list[dict]) -> list[str]:
    """Every non-root event's causation_id must reference a known event_id (no dangling causality)."""
    errs: list[str] = []
    ids = {e.get("event_id") for e in events}
    for e in events:
        ev_errs = validate_envelope(e)
        if ev_errs:
            errs.append(f"{e.get('event_id', '?')}: {ev_errs}")
        cau = e.get("causation_id")
        if cau and cau not in ids:
            errs.append(f"{e.get('event_id')}: causation_id {cau!r} references no known event")
    return errs


def envelope_from_event(ev: dict, *, pass_id: str = "", tick_id: str = "", causation_id: str = "",
                        engine_version: str = "", priority: str = "p2", evidence: dict | None = None) -> dict:
    """Lift a bus event (kind/stage/component/correlation_id/object_ref/payload/seq) onto the envelope."""
    return make_envelope(
        ev.get("kind", "event"), payload=ev.get("payload") or {}, correlation_id=ev.get("correlation_id") or "",
        causation_id=causation_id, pass_id=pass_id, tick_id=tick_id, engine=ev.get("component") or "",
        engine_version=engine_version, subject_type=ev.get("stage") or "event", subject_id=ev.get("object_ref") or "",
        idempotency_key=f"{ev.get('correlation_id') or ''}:{ev.get('kind')}:{ev.get('seq')}",
        priority=priority, evidence=evidence)


def chain_events(events: list[dict], **kw: Any) -> list[dict]:
    """Lift a SEQUENCE of bus events onto envelopes, chaining causation_id = previous event's id."""
    out: list[dict] = []
    prev = ""
    for ev in events:
        env = envelope_from_event(ev, causation_id=prev, **kw)
        out.append(env)
        prev = env["event_id"]
    return out
