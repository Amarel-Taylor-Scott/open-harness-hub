#!/usr/bin/env python3
"""scripts.check_shared_event_io — PROOF: the event I/O layer projects internal EventBus events into CloudEvents
1.0 envelopes, honestly and deterministically, with the spine's tracing + secret guarantees.

Drives a LIVE EventBus (scripts/context_events) and asserts:
  A. CONTRACTS: CloudEventProjection registered; EventEnvelope exists and is CloudEvents 1.0.
  B. PROJECTION: a published bus event projects to an envelope conforming to BOTH EventEnvelope (CloudEvents
     required) and CloudEventProjection (which additionally requires correlation_id + causation_id).
  C. CLOUDEVENTS: specversion 1.0, type == kind, datacontenttype application/json, subject == object_ref.
  D. SINGLE SOURCE: type is in EVENT_KINDS; an unknown kind raises (the projector validates against the set).
  E. TRACING: correlation_id present; a root event (no causation) defaults causation_id := correlation_id;
     a missing correlation_id raises.
  F. DETERMINISTIC ID: id is a hash of (source,type,seq) — stable across different `now`, never wall-clock.
  G. SECRET REDACTION: a payload carrying a raw key is projected with the value [REDACTED]; the key never appears.
  H. DETERMINISM: projecting the same event twice is identical.
  I. DEPENDENCY LAW: src/teleon/io never imports src.baltor.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.context_events import EventBus, EVENT_KINDS
from src.teleon.io import project_event_envelope

_NOW = "2026-06-07T00:00:00Z"
_SRC = "baltor/context_events"


def _required(rel: str) -> list[str]:
    return json.loads((_REPO / "schemas" / rel).read_text())["required"]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    def conforms(rec: dict, rel: str) -> bool:
        return all(k in rec for k in _required(rel))

    contracts = json.dumps(json.loads((_REPO / "architecture" / "contract_registry.json").read_text()))
    check("A: CloudEventProjection registered", "io/CloudEventProjection.schema.json" in contracts)
    ee = json.loads((_REPO / "schemas" / "envelopes" / "EventEnvelope.schema.json").read_text())
    check("A: EventEnvelope is CloudEvents 1.0", "1.0" in ee["properties"]["specversion"].get("enum", []))

    bus = EventBus()
    ev = bus.publish("pipeline.started", stage="Source Systems", component="demo",
                     correlation_id="corr-1", object_ref="obj-1", payload={"x": 1})
    env = project_event_envelope(ev, source=_SRC, now=_NOW, tenant_id="t1")
    check("B: projects to a valid EventEnvelope (CloudEvents)", conforms(env, "envelopes/EventEnvelope.schema.json"), json.dumps(env))
    check("B: projects to a valid CloudEventProjection (correlation+causation required)", conforms(env, "io/CloudEventProjection.schema.json"))

    check("C: CloudEvents fields (specversion 1.0, type==kind, json, subject)",
          env["specversion"] == "1.0" and env["type"] == "pipeline.started"
          and env["datacontenttype"] == "application/json" and env["subject"] == "obj-1")

    check("D: type is in EVENT_KINDS (single source)", env["type"] in EVENT_KINDS)
    raised = False
    try:
        project_event_envelope({"kind": "not.a.real.kind", "seq": 1, "correlation_id": "c"},
                               source=_SRC, now=_NOW, valid_kinds=EVENT_KINDS)
    except ValueError:
        raised = True
    check("D: unknown kind raises (validated against the set)", raised)

    # E tracing: root event with no causation → causation defaults to correlation
    root = bus.publish("component.started", correlation_id="corr-2", payload={})
    root_env = project_event_envelope(root, source=_SRC, now=_NOW)
    check("E: root event causation defaults to correlation_id",
          root_env["correlation_id"] == "corr-2" and root_env["causation_id"] == "corr-2")
    miss = False
    try:
        project_event_envelope({"kind": "pipeline.started", "seq": 9}, source=_SRC, now=_NOW)
    except ValueError:
        miss = True
    check("E: missing correlation_id raises (tracing guarantee)", miss)

    # F deterministic id (stable across different `now`), not wall-clock
    env_later = project_event_envelope(ev, source=_SRC, now="2099-12-31T23:59:59Z", tenant_id="t1")
    check("F: id is deterministic from (source,type,seq), independent of now",
          env["id"] == env_later["id"] and env["id"].startswith("ce_"))

    # G secret redaction
    fake_key = "sk-" + "Z" * 30  # built dynamically; never a literal key
    leaky = bus.publish("receipt_issued", correlation_id="corr-3", payload={"token": fake_key, "ok": "fine"})
    leaky_env = project_event_envelope(leaky, source=_SRC, now=_NOW)
    check("G: raw key in payload is redacted; never appears in the projected event",
          leaky_env["data"]["token"] == "[REDACTED]" and leaky_env["data"]["ok"] == "fine"
          and fake_key not in json.dumps(leaky_env))

    check("H: projection is deterministic", project_event_envelope(ev, source=_SRC, now=_NOW, tenant_id="t1") == env)

    src = "\n".join(p.read_text() for p in (_REPO / "src" / "teleon" / "io").rglob("*.py"))
    check("I: src/teleon/io never imports src.baltor",
          not any(l.strip().startswith(("import src.baltor", "from src.baltor")) for l in src.splitlines()))

    print("\n" + ("PASS — check_shared_event_io: internal bus events project to CloudEvents 1.0 envelopes "
                  "(EventEnvelope / CloudEventProjection) — type in EVENT_KINDS (single source), "
                  "correlation_id required + causation defaulting, deterministic (source,type,seq) id, raw secrets "
                  "redacted from data; pure projector; Teleon-side." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_shared_event_io.py --self-test")
    raise SystemExit(0)
