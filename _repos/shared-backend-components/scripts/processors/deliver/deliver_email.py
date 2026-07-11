#!/usr/bin/env python3
"""Backs `processor/deliver-email` (process_kind ``deliver.email``).

Render the validated result into an email template and send it to the
recipients. The RENDER half is deterministic ({{field}} substitution over
the result, strict about unresolved fields); the SEND half goes through an
INJECTED transport (``send(message) -> {"message_id": str}`` — an SMTP/ESP
adapter in production, the repo's local mailbox service in demos, a script
in tests). Without a transport the call RAISES — a message_id is never faked.

Contract: side_effects=external_call; on_error=raise.
Inputs result, recipients, template → output message_id.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/deliver/deliver_email.py
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Template placeholder shape: {{dotted.path}} into the result object.
_FIELD_RE = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")

#: Minimal RFC-ish recipient sanity (full validation is the ESP's job; this
#: catches swapped-argument bugs, not exotic addresses).
_RECIPIENT_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

HASH_ALGORITHM = "sha256"
IDEMPOTENCY_PREFIX = "eml:"
IDEMPOTENCY_HEX_LEN = 24


def _lookup(result: Any, path: str) -> Any:
    cur = result
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise ValueError(f"template field {{{{{path}}}}} not present in result")
        cur = cur[part]
    return cur


def render(template: dict[str, str], result: Any) -> dict[str, str]:
    """Strict deterministic render: every placeholder must resolve."""
    if not isinstance(template, dict) or "subject" not in template or "body" not in template:
        raise TypeError("template must be a dict with subject and body")
    out = {}
    for key in ("subject", "body"):
        out[key] = _FIELD_RE.sub(lambda m: str(_lookup(result, m.group(1))), str(template[key]))
    return out


def run(*, result: Any, recipients: list[str], template: dict[str, str],
        send: Callable[[dict[str, Any]], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Render + send. The message carries a content-addressed idempotency key."""
    if not isinstance(recipients, list) or not recipients:
        raise ValueError("recipients must be a non-empty list of addresses")
    for r in recipients:
        if not isinstance(r, str) or not _RECIPIENT_RE.match(r):
            raise ValueError(f"invalid recipient address: {r!r}")
    rendered = render(template, result)
    if send is None:
        raise RuntimeError("deliver_email requires an injected transport "
                           "(send=(message) -> {'message_id': ...}); a message_id is never faked")
    idem = IDEMPOTENCY_PREFIX + hashlib.new(
        HASH_ALGORITHM,
        json.dumps({"to": sorted(recipients), "subject": rendered["subject"],
                    "body": rendered["body"]},
                   sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:IDEMPOTENCY_HEX_LEN]
    message = {"to": sorted(recipients), "subject": rendered["subject"],
               "body": rendered["body"], "idempotency_key": idem}
    receipt = send(message)
    mid = receipt.get("message_id") if isinstance(receipt, dict) else None
    if not mid:
        raise ValueError("transport returned no message_id — delivery unconfirmed, not faked")
    return {"message_id": {"message_id": str(mid), "idempotency_key": idem,
                           "recipients": sorted(recipients), "subject": rendered["subject"],
                           "delivered": True}}


def _selftest() -> None:
    result = {"answer": {"text": "10 business days", "source": "12 CFR 1005.11"}}
    template = {"subject": "Your answer: {{answer.text}}",
                "body": "Per {{answer.source}}, the answer is {{answer.text}}."}
    sent: list[dict] = []

    def transport(message: dict) -> dict:
        sent.append(message)
        return {"message_id": f"mb-{len(sent):04d}"}

    out = run(result=result, recipients=["a@example.com"], template=template,
              send=transport)["message_id"]
    # Render is exact, dotted paths resolve, delivery confirmed by the transport.
    assert sent[0]["subject"] == "Your answer: 10 business days"
    assert sent[0]["body"] == "Per 12 CFR 1005.11, the answer is 10 business days."
    assert out["delivered"] is True and out["message_id"] == "mb-0001"
    # Same message → same idempotency key (the ESP can dedupe replays).
    again = run(result=result, recipients=["a@example.com"], template=template,
                send=transport)["message_id"]
    assert again["idempotency_key"] == out["idempotency_key"]
    # Unresolved placeholder is an ERROR, never sent blank.
    raised = False
    try:
        run(result={}, recipients=["a@example.com"],
            template={"subject": "{{missing}}", "body": "x"}, send=transport)
    except ValueError:
        raised = True
    assert raised and len(sent) == 2  # nothing extra was sent
    # No transport → honest refusal; bad recipients raise; no-message-id raises.
    for bad in (
        lambda: run(result=result, recipients=["a@example.com"], template=template),
        lambda: run(result=result, recipients=["not-an-address"], template=template, send=transport),
        lambda: run(result=result, recipients=[], template=template, send=transport),
        lambda: run(result=result, recipients=["a@example.com"], template=template,
                    send=lambda m: {}),
    ):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — deliver_email: strict deterministic template render (dotted paths, "
          "unresolved fields raise), injected transport with confirmed message_id, "
          "content-addressed idempotency, honest no-transport refusal verified")


if __name__ == "__main__":
    _selftest()
