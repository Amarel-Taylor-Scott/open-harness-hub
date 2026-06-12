#!/usr/bin/env python3
"""Backs `processor/offline-queue-sync-on-reconnect` (process_kind ``agent_loop.queue_flush``).

Store-and-forward for field deployments (the AfyaEdge pattern): buffer alert
records in an injected local queue while offline, and flush FIFO to the
upstream endpoint as soon as a connection exists. One call does ONE
operation: ``enqueue`` (always local, never lost) or ``flush`` (drain via
the injected transport; the first failure STOPS the drain so order is
preserved, and failed records stay queued — nothing is dropped on a bad
link). Time is injected; receipts report exact depths and ages.

Contract: deterministic given injected queue/transport/now; side_effects=
write (the injected queue only); on_error=raise.

Inputs operation, record, endpoint_url, auth_token, max_batch_size →
queue_depth, synced_count, failed_count, oldest_pending_age_s, last_sync_ts,
sync_status.

CLI / self-test: python3 scripts/processors/offline_queue_sync_on_reconnect.py
"""
from __future__ import annotations

import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

OP_ENQUEUE = "enqueue"
OP_FLUSH = "flush"
OPERATIONS = (OP_ENQUEUE, OP_FLUSH)

#: Flush batch ceiling — small batches keep a flaky link from re-sending much.
DEFAULT_MAX_BATCH_SIZE = 50

STATUS_QUEUED = "queued_local"
STATUS_SYNCED = "synced"
STATUS_PARTIAL = "partial_failure_order_preserved"
STATUS_NOTHING = "nothing_pending"


def run(*, operation: str, queue: list[dict[str, Any]], now: float,
        record: dict[str, Any] | None = None,
        endpoint_url: str | None = None, auth_token: str | None = None,
        max_batch_size: int = DEFAULT_MAX_BATCH_SIZE,
        send: Callable[[str, dict[str, Any], str | None], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Enqueue locally or flush FIFO via the injected transport."""
    if operation not in OPERATIONS:
        raise ValueError(f"operation must be one of {OPERATIONS}, got {operation!r}")
    if not isinstance(queue, list):
        raise TypeError("queue must be the injected local queue (a list)")
    if not isinstance(max_batch_size, int) or max_batch_size < 1:
        raise ValueError(f"max_batch_size must be a positive int, got {max_batch_size!r}")

    def _receipt(synced: int, failed: int, status: str, last_sync: float | None) -> dict[str, Any]:
        oldest = min((r["enqueued_at"] for r in queue), default=None)
        return {"queue_depth": len(queue), "synced_count": synced, "failed_count": failed,
                "oldest_pending_age_s": (float(now) - oldest) if oldest is not None else 0.0,
                "last_sync_ts": last_sync, "sync_status": status}

    if operation == OP_ENQUEUE:
        if not isinstance(record, dict) or not record:
            raise ValueError("enqueue needs a non-empty record dict")
        queue.append({"record": record, "enqueued_at": float(now)})
        return _receipt(0, 0, STATUS_QUEUED, None)

    # flush
    if not endpoint_url or not isinstance(endpoint_url, str):
        raise ValueError("flush needs endpoint_url")
    if send is None:
        raise RuntimeError("flush requires an injected transport "
                           "(send=(url, record, auth_token) -> {'ok': bool}); "
                           "a sync receipt is never faked")
    if not queue:
        return _receipt(0, 0, STATUS_NOTHING, float(now))
    synced = failed = 0
    batch = list(queue[:max_batch_size])     # FIFO head
    for entry in batch:
        try:
            resp = send(endpoint_url, entry["record"], auth_token)
            ok = bool(isinstance(resp, dict) and resp.get("ok"))
        except Exception:  # noqa: BLE001 — a link fault is data, not a crash
            ok = False
        if ok:
            queue.remove(entry)              # only on confirmed receipt
            synced += 1
        else:
            failed = 1                       # first failure STOPS the drain (order preserved)
            break
    status = STATUS_SYNCED if failed == 0 and not queue else \
        (STATUS_SYNCED if failed == 0 else STATUS_PARTIAL)
    return _receipt(synced, failed, status, float(now))


def _selftest() -> None:
    q: list[dict[str, Any]] = []
    # Offline enqueues buffer locally with injected timestamps; nothing lost.
    for i, t in enumerate((100.0, 160.0, 220.0)):
        r = run(operation=OP_ENQUEUE, queue=q, now=t, record={"alert_id": f"a{i}", "msg": "case"})
        assert r["sync_status"] == STATUS_QUEUED
    assert len(q) == 3
    aged = run(operation=OP_ENQUEUE, queue=q, now=400.0, record={"alert_id": "a3"})
    assert aged["oldest_pending_age_s"] == 300.0  # 400 - 100
    # Reconnect: full FIFO drain via the transport, in order, with receipts.
    sent: list[str] = []
    ok_send = lambda url, rec, tok: (sent.append(rec["alert_id"]), {"ok": True})[1]
    fl = run(operation=OP_FLUSH, queue=q, now=500.0, endpoint_url="https://moh.example/sync",
             auth_token="tok", send=ok_send)
    assert fl["sync_status"] == STATUS_SYNCED and fl["synced_count"] == 4
    assert fl["queue_depth"] == 0 and sent == ["a0", "a1", "a2", "a3"]  # FIFO
    # Mid-drain failure: drain STOPS, failed record + successors stay queued.
    q2: list[dict[str, Any]] = []
    for i in range(3):
        run(operation=OP_ENQUEUE, queue=q2, now=float(i), record={"alert_id": f"b{i}"})
    flaky_calls = iter([{"ok": True}, ConnectionError("drop"), {"ok": True}])
    def flaky(url, rec, tok):
        item = next(flaky_calls)
        if isinstance(item, Exception):
            raise item
        return item
    pf = run(operation=OP_FLUSH, queue=q2, now=10.0, endpoint_url="https://x", send=flaky)
    assert pf["sync_status"] == STATUS_PARTIAL and pf["synced_count"] == 1
    assert [e["record"]["alert_id"] for e in q2] == ["b1", "b2"]  # order preserved
    # Batch ceiling respected; empty flush honest.
    q3 = [{"record": {"alert_id": f"c{i}"}, "enqueued_at": 0.0} for i in range(5)]
    b = run(operation=OP_FLUSH, queue=q3, now=1.0, endpoint_url="https://x",
            max_batch_size=2, send=lambda u, r, t: {"ok": True})
    assert b["synced_count"] == 2 and b["queue_depth"] == 3
    empty = run(operation=OP_FLUSH, queue=[], now=1.0, endpoint_url="https://x",
                send=lambda u, r, t: {"ok": True})
    assert empty["sync_status"] == STATUS_NOTHING
    # Refusals: flush without transport, bad operation, empty record.
    for bad in (lambda: run(operation=OP_FLUSH, queue=q, now=1.0, endpoint_url="https://x"),
                lambda: run(operation="peek", queue=q, now=1.0),
                lambda: run(operation=OP_ENQUEUE, queue=q, now=1.0, record={})):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — offline_queue_sync_on_reconnect: local-first enqueue (never lost), "
          "FIFO drain with confirmed-receipt removal, first-failure stops the drain "
          "(order preserved), batch ceiling, injected time/transport verified")


if __name__ == "__main__":
    _selftest()
