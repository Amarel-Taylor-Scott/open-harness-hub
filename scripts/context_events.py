#!/usr/bin/env python3
"""scripts.context_events — the ONE in-process event bus every Baltor component emits onto.

The realtime dashboard's substrate: components publish lifecycle events here; the admin server's
SSE route (`/api/events/stream`) and `log_event(...)` drain from the same bus so a user can watch
the system fire live. Deterministic + stdlib-only: events carry a MONOTONIC `seq` (NOT wall-clock),
so an offline run is byte-identical and self-tests can assert exact ordering.

`EVENT_KINDS` is the single source of truth for event types (no-magic-values) — the bus rejects
anything not in it. Use `emit(bus, kind, ...)` from a component: it no-ops when `bus is None`, so
wiring a module is non-breaking (default off = unchanged behavior + determinism).

CLI / self-test (offline, deterministic):
    python3 scripts/context_events.py --self-test
"""
from __future__ import annotations

import argparse
import threading
from typing import Any, Callable

#: Single source of truth for event types (mirror into schemas/events/* when added). The dashboard
#: maps these to stages/colors. Extend HERE; the bus rejects unknown kinds.
EVENT_KINDS: frozenset[str] = frozenset({
    "component.started", "component.progressed", "component.finished",
    "source.received", "source_handle.created", "source_handle.expanded",
    "context_object.created", "relationship.created",
    "contradiction_found", "rot.detected",
    "review.requested", "review.decided",
    "context_pack.created", "receipt_issued",
    "inference.requested", "inference.completed",
    "verification.started", "verification.completed",
    "eval.started", "eval.completed", "context_lift.calculated",
    "swarm.started", "swarm.agent.completed", "swarm.consensus.created",
    "pipeline.started", "pipeline.completed", "pipeline.failed",
    # Context Auditor (src/baltor/context_audit) — pre-LLM-call audit-manifest signals (Optimization stage);
    # conflict→contradiction_found and stale→rot.detected reuse the existing kinds above.
    "context.audited", "context.duplicate_found", "context.tool_bloat", "context.optimized",
    "context.poisoning_suspected",
})

#: macro stage a kind belongs to (for the dashboard stage board). Optional per event.
STAGES: tuple[str, ...] = (
    "Source Systems", "Reconciliation", "Anti-Fragility", "Enhancement",
    "Optimization", "Consumption", "Verification rail",
)


class EventBus:
    """Minimal synchronous pub/sub with a monotonic seq + bounded recent buffer. No clock, no IO.

    Thread-safe: a Lock guards the seq counter, the events buffer, and the subscriber list because
    the bus is driven concurrently by ThreadingHTTPServer request threads (multiple dashboard viewers
    + active runs publishing at once). Subscriber callbacks are SNAPSHOTTED under the lock and invoked
    OUTSIDE it, so a slow subscriber never holds the lock and a re-entrant publish can't deadlock."""

    def __init__(self, *, buffer: int = 1000) -> None:
        self._subs: list[Callable[[dict], None]] = []
        self._events: list[dict] = []
        self._seq = 0
        self._buffer = buffer
        self._lock = threading.Lock()

    def publish(self, kind: str, *, stage: str | None = None, component: str | None = None,
                correlation_id: str | None = None, causation_id: str | None = None,
                object_ref: str | None = None, payload: dict | None = None) -> dict:
        if kind not in EVENT_KINDS:
            raise ValueError(f"unknown event kind {kind!r}; add it to EVENT_KINDS (single source)")
        with self._lock:
            self._seq += 1
            ev = {
                "seq": self._seq, "kind": kind, "stage": stage, "component": component,
                "correlation_id": correlation_id, "causation_id": causation_id,
                "object_ref": object_ref, "payload": payload or {},
            }
            self._events.append(ev)
            if len(self._events) > self._buffer:
                self._events = self._events[-self._buffer:]
            subs = list(self._subs)  # snapshot under the lock; invoke below WITHOUT holding it
        for cb in subs:
            try:
                cb(ev)
            except Exception:  # a bad subscriber must never break publishing
                pass
        return ev

    def subscribe(self, cb: Callable[[dict], None]) -> Callable[[], None]:
        with self._lock:
            self._subs.append(cb)

        def _unsub() -> None:
            with self._lock:
                if cb in self._subs:
                    self._subs.remove(cb)
        return _unsub

    def recent(self, n: int = 50) -> list[dict]:
        with self._lock:
            return self._events[-n:]

    def clear(self) -> None:
        """Drop the buffered events (the seq counter stays monotonic so ids never repeat)."""
        with self._lock:
            self._events = []

    def restore(self, events: list[dict]) -> None:
        """Re-seed the buffer from a durable log (e.g. on restart) — events are NOT re-published
        (no duplicate side effects); seq continues past the highest restored id so it stays monotonic."""
        with self._lock:
            self._events = list(events)[-self._buffer:]
        self._seq = max((int(e.get("seq") or 0) for e in self._events), default=self._seq)

    def by_correlation(self, correlation_id: str) -> list[dict]:
        return [e for e in self._events if e.get("correlation_id") == correlation_id]


def emit(bus: EventBus | None, kind: str, **kw: Any) -> dict | None:
    """Publish if a bus is wired, else no-op — so a component can emit unconditionally and stay
    non-breaking/deterministic when no bus is passed."""
    return bus.publish(kind, **kw) if bus is not None else None


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    bus = EventBus()
    seen: list[dict] = []
    unsub = bus.subscribe(seen.append)

    cid = "corr-1"
    bus.publish("pipeline.started", correlation_id=cid, component="pipeline")
    bus.publish("context_object.created", correlation_id=cid, component="seeder", object_ref="obj-x")
    bus.publish("contradiction_found", correlation_id=cid, component="context_graph",
                stage="Reconciliation", payload={"predicate": "max_retries"})
    bus.publish("pipeline.completed", correlation_id="corr-2", component="pipeline")

    check("subscriber received all 4 events in order",
          [e["kind"] for e in seen] == ["pipeline.started", "context_object.created", "contradiction_found", "pipeline.completed"])
    check("seq is monotonic 1..4", [e["seq"] for e in seen] == [1, 2, 3, 4])
    check("recent(2) returns the last two", [e["kind"] for e in bus.recent(2)] == ["contradiction_found", "pipeline.completed"])
    check("by_correlation groups exactly corr-1's 3 events", len(bus.by_correlation(cid)) == 3)
    check("emit(None, ...) is a no-op (returns None)", emit(None, "pipeline.started") is None)
    check("emit(bus, ...) publishes (returns the event)", emit(bus, "review.requested", component="x")["kind"] == "review.requested")

    raised = False
    try:
        bus.publish("not.a.real.kind")
    except ValueError:
        raised = True
    check("unknown event kind is rejected", raised)

    # unsubscribe stops delivery
    unsub()
    before = len(seen)
    bus.publish("rot.detected", component="rot")
    check("unsubscribe stops further delivery", len(seen) == before)

    # determinism: a fresh identical run yields identical seqs/kinds
    b2 = EventBus(); got = []
    b2.subscribe(got.append)
    for k in ("pipeline.started", "contradiction_found", "pipeline.completed"):
        b2.publish(k, correlation_id="c")
    check("deterministic seqs on a fresh bus", [e["seq"] for e in got] == [1, 2, 3])

    # restore() re-seeds from a durable log without re-publishing; seq continues monotonic
    b3 = EventBus()
    b3.restore([{"seq": 7, "kind": "receipt_issued", "correlation_id": "c"},
                {"seq": 8, "kind": "pipeline.completed", "correlation_id": "c"}])
    check("restore re-seeds the buffer (no re-publish)", [e["kind"] for e in b3.recent(5)] == ["receipt_issued", "pipeline.completed"])
    nxt = b3.publish("rot.detected", component="x")
    check("restore keeps seq monotonic past the highest restored id", nxt["seq"] == 9)

    print(f"\n{'all context_events self-tests passed (ordered, monotonic seq, correlation grouping, kind-validated, no clock).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Baltor in-process event bus (the realtime dashboard substrate).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    print(f"EVENT_KINDS ({len(EVENT_KINDS)}): {sorted(EVENT_KINDS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
