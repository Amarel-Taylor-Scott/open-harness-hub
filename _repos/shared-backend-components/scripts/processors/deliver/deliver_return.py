#!/usr/bin/env python3
"""Backs `processor/deliver-return` (process_kind ``deliver.return_response``).

The DEFAULT outbound: hand the validated result back to the caller as the
synchronous API/function response — no external system, no transport. The
envelope echoes the result byte-faithfully and stamps a content-addressed
``response_id`` so the same result always mints the same receipt (replays
are detectable downstream).

Contract: deterministic; side_effects=none; on_error=raise.
Input result → output response.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/deliver/deliver_return.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

HASH_ALGORITHM = "sha256"
RESPONSE_ID_PREFIX = "resp:"
RESPONSE_ID_HEX_LEN = 24


def _canonical(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"result must be JSON-serializable: {exc}") from exc


def run(*, result: Any) -> dict[str, Any]:
    """Wrap ``result`` as the synchronous response envelope (byte-faithful echo)."""
    canon = _canonical(result)
    rid = RESPONSE_ID_PREFIX + hashlib.new(HASH_ALGORITHM, canon.encode("utf-8")).hexdigest()[:RESPONSE_ID_HEX_LEN]
    return {"response": {"response_id": rid, "result": result,
                         "delivery": "synchronous_return", "delivered": True}}


def _selftest() -> None:
    result = {"answer": "10 business days", "citations": ["12 CFR 1005.11"]}
    out = run(result=result)["response"]
    # Byte-faithful echo + stable content-addressed id.
    assert out["result"] == result and out["delivered"] is True
    assert out["response_id"] == run(result=result)["response"]["response_id"]
    # Different results mint different ids; key order never matters.
    assert run(result={"answer": "x"})["response"]["response_id"] != out["response_id"]
    reordered = {"citations": ["12 CFR 1005.11"], "answer": "10 business days"}
    assert run(result=reordered)["response"]["response_id"] == out["response_id"]
    # Deterministic; on_error=raise for unserializable results.
    assert json.dumps(run(result=result), sort_keys=True) == json.dumps(run(result=result), sort_keys=True)
    raised = False
    try:
        run(result=object())
    except TypeError:
        raised = True
    assert raised
    print("PASS — deliver_return: byte-faithful synchronous envelope with "
          "content-addressed response_id (format-insensitive), deterministic verified")


if __name__ == "__main__":
    _selftest()
