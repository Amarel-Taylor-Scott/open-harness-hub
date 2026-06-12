#!/usr/bin/env python3
"""Backs `processor/escalate-human` (process_kind ``escalate.human``).

Route the result + the reason it needs eyes (a fired gate, low confidence,
an abstention) to a human review queue. THE governed escalation path: the
ticket is a complete, self-contained review envelope (what fired, the
evidence, the proposed-never-disposed suggestion), and enqueueing goes
through an INJECTED queue (``enqueue(ticket) -> {"ticket_id"|"ref": ...}``).
Without a queue the call RAISES — a fired gate must never silently no-op.

Contract: side_effects=external_call; on_error=raise; deterministic ticket
identity (content-addressed — replays dedupe in the queue).

Inputs result, reason → output ticket.

CLI / self-test: python3 scripts/processors/deliver/escalate_human.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Recognized escalation reasons → queue priority. Unknown reasons raise (a
#: typo'd reason must not land in the slow lane silently).
REASON_PRIORITY = {
    "gate_fired": "high",
    "low_confidence": "normal",
    "abstention": "normal",
    "conflict_detected": "high",
    "policy_review": "low",
}

HASH_ALGORITHM = "sha256"
TICKET_ID_PREFIX = "tkt:"
TICKET_ID_HEX_LEN = 24


def _canonical(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"result must be JSON-serializable: {exc}") from exc


def run(*, result: Any, reason: str | dict[str, Any],
        enqueue: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build the review ticket and enqueue it via the injected queue."""
    if isinstance(reason, str):
        reason_obj: dict[str, Any] = {"kind": reason, "detail": ""}
    elif isinstance(reason, dict) and "kind" in reason:
        reason_obj = {"kind": str(reason["kind"]), "detail": str(reason.get("detail", ""))}
    else:
        raise TypeError("reason must be a kind string or a {'kind', 'detail'} dict")
    if reason_obj["kind"] not in REASON_PRIORITY:
        raise ValueError(f"unknown escalation reason {reason_obj['kind']!r}; "
                         f"known: {sorted(REASON_PRIORITY)}")
    if enqueue is None:
        raise RuntimeError("escalate_human requires an injected queue "
                           "(enqueue=(ticket) -> receipt); a fired gate must never silently no-op")
    body = _canonical({"result": result, "reason": reason_obj})
    tid = TICKET_ID_PREFIX + hashlib.new(HASH_ALGORITHM, body.encode("utf-8")).hexdigest()[:TICKET_ID_HEX_LEN]
    ticket = {
        "ticket_id": tid,
        "reason": reason_obj,
        "priority": REASON_PRIORITY[reason_obj["kind"]],
        "result": result,                       # the FULL envelope — reviewers see everything
        "disposition": "proposed",              # the gate proposes; the human disposes
        "serves_truth": False,
    }
    receipt = enqueue(ticket)
    if not isinstance(receipt, dict) or not (receipt.get("ticket_id") or receipt.get("ref")):
        raise ValueError("queue returned no ticket reference — escalation unconfirmed, not faked")
    return {"ticket": {**ticket, "queue_ref": receipt.get("ticket_id") or receipt.get("ref"),
                       "enqueued": True}}


def _selftest() -> None:
    queue: list[dict] = []

    def enqueue(ticket: dict) -> dict:
        queue.append(ticket)
        return {"ref": f"q-{len(queue):04d}"}

    result = {"answer": "uncertain", "belief": 0.42,
              "evidence_log": [{"source_kind": "opinion", "stance": "supports"}]}
    out = run(result=result, reason={"kind": "low_confidence", "detail": "belief 0.42 < 0.8"},
              enqueue=enqueue)["ticket"]
    # The full envelope reaches the reviewer; priority maps from the reason.
    assert queue[0]["result"] == result and out["priority"] == "normal"
    assert out["enqueued"] is True and out["queue_ref"] == "q-0001"
    # Propose-never-dispose is structural.
    assert out["disposition"] == "proposed" and out["serves_truth"] is False
    # A fired gate gets the high lane.
    gate = run(result=result, reason="gate_fired", enqueue=enqueue)["ticket"]
    assert gate["priority"] == "high"
    # Content-addressed identity: same (result, reason) → same ticket_id (queue dedupes).
    again = run(result=result, reason="gate_fired", enqueue=enqueue)["ticket"]
    assert again["ticket_id"] == gate["ticket_id"]
    # Refusals: no queue, unknown reason, ref-less queue.
    for bad in (
        lambda: run(result=result, reason="gate_fired"),
        lambda: run(result=result, reason="because", enqueue=enqueue),
        lambda: run(result=result, reason="gate_fired", enqueue=lambda t: {}),
    ):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — escalate_human: complete review envelopes (full result + reason + "
          "priority), proposed-never-disposed pinned, content-addressed ticket ids, "
          "no-queue/unknown-reason refusals verified")


if __name__ == "__main__":
    _selftest()
