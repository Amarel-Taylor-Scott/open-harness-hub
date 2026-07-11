#!/usr/bin/env python3
"""Backs `processor/deliver-notify` (process_kind ``deliver.notify``).

Post a notification summarizing the result to a channel (Slack / Teams /
SMS). The SUMMARY is deterministic (severity prefix + headline + capped
detail); the POST goes through an INJECTED channel poster
(``post_message(channel, text) -> {"ack": ...}``). Without one the call
RAISES — an ack is never faked.

Contract: side_effects=external_call; on_error=raise.
Inputs result, channel → output ack.

CLI / self-test: python3 _repos/shared-backend-components/scripts/processors/deliver/deliver_notify.py
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

# ── Constants (No-Magic-Values) ───────────────────────────────────────────────

#: Severity → message prefix. Unknown severities raise (a silent default
#: prefix would hide a paging mistake).
SEVERITY_PREFIX = {"info": "ℹ️", "warning": "⚠️", "critical": "🚨"}
DEFAULT_SEVERITY = "info"

#: Notification body cap — channels truncate; we do it deterministically and
#: say so instead of letting Slack cut mid-word.
MAX_TEXT_CHARS = 400
TRUNCATION_MARK = " …[truncated]"

HASH_ALGORITHM = "sha256"
NOTIFY_ID_PREFIX = "ntf:"
NOTIFY_ID_HEX_LEN = 24


def summarize(result: dict[str, Any]) -> tuple[str, str]:
    """(severity, text) — deterministic summary of a result envelope."""
    if not isinstance(result, dict):
        raise TypeError(f"result must be a dict, got {type(result).__name__}")
    severity = str(result.get("severity", DEFAULT_SEVERITY))
    if severity not in SEVERITY_PREFIX:
        raise ValueError(f"unknown severity {severity!r}; known: {sorted(SEVERITY_PREFIX)}")
    headline = str(result.get("headline") or result.get("answer") or "result ready")
    detail = result.get("detail", "")
    text = f"{SEVERITY_PREFIX[severity]} {headline}" + (f" — {detail}" if detail else "")
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS - len(TRUNCATION_MARK)] + TRUNCATION_MARK
    return severity, text


def run(*, result: dict[str, Any], channel: str,
        post_message: Callable[[str, str], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Summarize + post to ``channel`` via the injected poster."""
    if not isinstance(channel, str) or not channel:
        raise ValueError("channel must be a non-empty str")
    severity, text = summarize(result)
    if post_message is None:
        raise RuntimeError("deliver_notify requires an injected poster "
                           "(post_message=(channel, text) -> {'ack': ...}); an ack is never faked")
    nid = NOTIFY_ID_PREFIX + hashlib.new(
        HASH_ALGORITHM, f"{channel}|{text}".encode("utf-8")).hexdigest()[:NOTIFY_ID_HEX_LEN]
    receipt = post_message(channel, text)
    if not isinstance(receipt, dict) or "ack" not in receipt:
        raise ValueError("poster returned no ack — delivery unconfirmed, not faked")
    return {"ack": {"notify_id": nid, "channel": channel, "severity": severity,
                    "text": text, "ack": receipt["ack"], "delivered": True}}


def _selftest() -> None:
    posted: list[tuple[str, str]] = []

    def poster(channel: str, text: str) -> dict:
        posted.append((channel, text))
        return {"ack": f"ts-{len(posted)}"}

    out = run(result={"severity": "critical", "headline": "lift gate failed",
                      "detail": "pipeline_score 0.41 < bare 0.55"},
              channel="#alerts", post_message=poster)["ack"]
    assert out["delivered"] is True and out["channel"] == "#alerts"
    assert posted[0][1].startswith(SEVERITY_PREFIX["critical"])
    assert "lift gate failed" in posted[0][1] and "0.41" in posted[0][1]
    # Defaults: severity info, headline fallback to answer.
    info = run(result={"answer": "10 business days"}, channel="#ops", post_message=poster)["ack"]
    assert info["severity"] == "info" and "10 business days" in info["text"]
    # Deterministic truncation, marked.
    long = run(result={"headline": "h", "detail": "d" * 600}, channel="#x",
               post_message=poster)["ack"]
    assert len(long["text"]) == MAX_TEXT_CHARS and long["text"].endswith(TRUNCATION_MARK)
    # Same (channel, text) → same notify_id.
    assert info["notify_id"] == run(result={"answer": "10 business days"}, channel="#ops",
                                    post_message=poster)["ack"]["notify_id"]
    # Refusals: no poster, unknown severity, empty channel, ack-less poster.
    for bad in (
        lambda: run(result={"answer": "x"}, channel="#a"),
        lambda: run(result={"severity": "loud"}, channel="#a", post_message=poster),
        lambda: run(result={"answer": "x"}, channel="", post_message=poster),
        lambda: run(result={"answer": "x"}, channel="#a", post_message=lambda c, t: {}),
    ):
        raised = False
        try:
            bad()
        except (RuntimeError, ValueError):
            raised = True
        assert raised
    print("PASS — deliver_notify: severity-prefixed deterministic summaries with marked "
          f"truncation at {MAX_TEXT_CHARS} chars, injected poster with confirmed ack, "
          "honest refusals verified")


if __name__ == "__main__":
    _selftest()
