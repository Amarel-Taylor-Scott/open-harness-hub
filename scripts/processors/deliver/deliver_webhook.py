#!/usr/bin/env python3
"""Backs `processor/deliver-webhook` (process_kind ``deliver.webhook``).

POST the validated result to a configured webhook endpoint with a SIGNED
payload and bounded retries. The signature is real (HMAC-SHA256 over the
canonical body, hex digest in ``X-OHH-Signature``); the HTTP transport is
INJECTED (``post(url, body, headers) -> {"status": int}``) so the same code
runs against urllib in production and a scripted transport in tests. Without
a transport the call RAISES — a delivery receipt is never faked.

Retries: bounded attempts with deterministic (injected-sleep) backoff; every
attempt is echoed in the receipt (lossless — failures are data, not noise).

Contract: side_effects=external_call; on_error=raise; idempotent at the
receiver via the content-addressed ``delivery_id`` header.

Inputs result, endpoint, signing_key → output delivery_receipt.

CLI / self-test: python3 scripts/processors/deliver/deliver_webhook.py
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Bounded retries: 3 attempts total covers transient 5xx/timeouts without
#: hammering a broken receiver.
MAX_ATTEMPTS = 3

#: Backoff seconds per retry gap (deterministic ladder, applied via the
#: injected sleep so tests run instantly and replays are exact).
BACKOFF_LADDER_SECONDS = (1.0, 5.0)

#: Header names (single definition; receivers/tests read these).
SIGNATURE_HEADER = "X-OHH-Signature"
DELIVERY_ID_HEADER = "X-OHH-Delivery"

HASH_ALGORITHM = "sha256"
DELIVERY_ID_PREFIX = "whd:"
DELIVERY_ID_HEX_LEN = 24

#: HTTP statuses that mean "delivered" (2xx).
_OK_RANGE = range(200, 300)


def _canonical(obj: Any) -> str:
    try:
        return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"result must be JSON-serializable: {exc}") from exc


def sign(body: str, signing_key: str) -> str:
    return hmac.new(signing_key.encode("utf-8"), body.encode("utf-8"),
                    HASH_ALGORITHM).hexdigest()


def run(*, result: Any, endpoint: str, signing_key: str,
        post: Callable[[str, str, dict], dict] | None = None,
        sleep: Callable[[float], None] | None = None) -> dict[str, Any]:
    """Deliver ``result`` to ``endpoint`` signed with ``signing_key`` via the
    injected transport, retrying on failure up to ``MAX_ATTEMPTS``."""
    if not isinstance(endpoint, str) or not endpoint.startswith(("https://", "http://")):
        raise ValueError(f"endpoint must be an http(s) URL, got {endpoint!r}")
    if not isinstance(signing_key, str) or not signing_key:
        raise ValueError("signing_key must be a non-empty str")
    if post is None:
        raise RuntimeError("deliver_webhook requires an injected transport "
                           "(post=(url, body, headers) -> {'status': int}); "
                           "a delivery receipt is never faked")
    body = _canonical(result)
    delivery_id = DELIVERY_ID_PREFIX + hashlib.new(
        HASH_ALGORITHM, (endpoint + "|" + body).encode("utf-8")).hexdigest()[:DELIVERY_ID_HEX_LEN]
    headers = {"Content-Type": "application/json",
               SIGNATURE_HEADER: sign(body, signing_key),
               DELIVERY_ID_HEADER: delivery_id}
    attempts: list[dict[str, Any]] = []
    delivered = False
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = post(endpoint, body, headers)
            status = int(resp.get("status", 0))
            attempts.append({"attempt": attempt, "status": status, "error": None})
            if status in _OK_RANGE:
                delivered = True
                break
        except Exception as exc:  # noqa: BLE001 — transport faults are retryable data
            attempts.append({"attempt": attempt, "status": None,
                             "error": f"{type(exc).__name__}: {exc}"})
        if attempt < MAX_ATTEMPTS and sleep is not None:
            sleep(BACKOFF_LADDER_SECONDS[min(attempt - 1, len(BACKOFF_LADDER_SECONDS) - 1)])
    return {"delivery_receipt": {"delivery_id": delivery_id, "endpoint": endpoint,
                                 "delivered": delivered, "attempts": attempts,
                                 "signature_scheme": f"hmac-{HASH_ALGORITHM}",
                                 "signed_with_header": SIGNATURE_HEADER}}


def _selftest() -> None:
    result = {"answer": "10 business days"}
    key = "demo-signing-key"
    calls: list[dict] = []

    def ok_post(url: str, body: str, headers: dict) -> dict:
        calls.append({"url": url, "body": body, "headers": headers})
        return {"status": 200}

    out = run(result=result, endpoint="https://receiver.example/hook",
              signing_key=key, post=ok_post)["delivery_receipt"]
    assert out["delivered"] is True and len(out["attempts"]) == 1
    # The signature is REAL and verifiable by the receiver.
    sent = calls[0]
    expect = hmac.new(key.encode(), sent["body"].encode(), "sha256").hexdigest()
    assert sent["headers"][SIGNATURE_HEADER] == expect
    assert sent["headers"][DELIVERY_ID_HEADER] == out["delivery_id"]
    # Retry ladder: two 503s then success → 3 echoed attempts, backoff slept.
    slept: list[float] = []
    seq = iter([{"status": 503}, {"status": 503}, {"status": 200}])
    retry = run(result=result, endpoint="https://receiver.example/hook", signing_key=key,
                post=lambda u, b, h: next(seq), sleep=slept.append)["delivery_receipt"]
    assert retry["delivered"] is True and [a["status"] for a in retry["attempts"]] == [503, 503, 200]
    assert slept == [BACKOFF_LADDER_SECONDS[0], BACKOFF_LADDER_SECONDS[1]]
    # Permanent failure: honest delivered=False with every attempt preserved.
    dead = run(result=result, endpoint="https://receiver.example/hook", signing_key=key,
               post=lambda u, b, h: {"status": 500})["delivery_receipt"]
    assert dead["delivered"] is False and len(dead["attempts"]) == MAX_ATTEMPTS
    # Transport exceptions are retryable data, not crashes.
    flaky = iter([ConnectionError("reset"), {"status": 200}])
    def flaky_post(u, b, h):
        item = next(flaky)
        if isinstance(item, Exception):
            raise item
        return item
    fr = run(result=result, endpoint="https://r.example/h", signing_key=key,
             post=flaky_post)["delivery_receipt"]
    assert fr["delivered"] is True and "ConnectionError" in fr["attempts"][0]["error"]
    # Same (endpoint, result) → same delivery_id (receiver-side idempotency).
    assert out["delivery_id"] == run(result=result, endpoint="https://receiver.example/hook",
                                     signing_key=key, post=ok_post)["delivery_receipt"]["delivery_id"]
    # No transport → honest refusal; bad endpoint/key raise.
    for bad_call in (
        lambda: run(result=result, endpoint="https://r.example/h", signing_key=key),
        lambda: run(result=result, endpoint="ftp://nope", signing_key=key, post=ok_post),
        lambda: run(result=result, endpoint="https://r.example/h", signing_key="", post=ok_post),
    ):
        raised = False
        try:
            bad_call()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print(f"PASS — deliver_webhook: HMAC-{HASH_ALGORITHM} signed payloads, content-addressed "
          f"delivery ids, {MAX_ATTEMPTS}-attempt bounded retry with echoed attempts, honest "
          "no-transport refusal verified")


if __name__ == "__main__":
    _selftest()
