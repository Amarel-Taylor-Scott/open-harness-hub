"""src.teleon.io.event_io — project an internal EventBus event into a CloudEvents-compatible EventEnvelope.

The bus (scripts/context_events) emits {seq, kind, stage, component, correlation_id, causation_id, object_ref,
payload}. This pure projector maps that to a CloudEvents 1.0 envelope (EventEnvelope / CloudEventProjection),
enforcing the spine's guarantees: specversion 1.0, deterministic id from (source,type,seq) [never wall-clock],
type in the allowed kind set (single source), correlation_id present (causation defaults to it for root events),
and NO raw secret in data (redacted). Pure + deterministic; no src.baltor import (inputs are plain dicts).
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

# raw secret patterns (prefix + long token, or a credentialed DSN) — redacted out of projected event data
_KEY_PREFIXES = ("sk-", "gsk_", "hf_", "AIza", "nvapi-")
_DSN_RE = re.compile(r"(postgres|postgresql|mysql|mongodb|redis|amqp)://[^ \"']+:[^ \"']+@", re.IGNORECASE)
_REDACTED = "[REDACTED]"


def _looks_secret(s: str) -> bool:
    if any(re.search(re.escape(p) + r"[A-Za-z0-9_\-]{16,}", s) for p in _KEY_PREFIXES):
        return True
    return bool(_DSN_RE.search(s))


def redact_secrets(obj: Any) -> Any:
    """Deep-copy obj with any string value that looks like a raw secret replaced by [REDACTED]."""
    if isinstance(obj, str):
        return _REDACTED if _looks_secret(obj) else obj
    if isinstance(obj, dict):
        return {k: redact_secrets(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact_secrets(v) for v in obj]
    return obj


def project_event_envelope(internal_event: dict, *, source: str, now: str, tenant_id: str = "",
                           trace_id: str = "", valid_kinds: set | frozenset | None = None) -> dict:
    """Project a bus event to a CloudEvents 1.0 envelope. Raises ValueError on an unknown kind (when valid_kinds
    is given) or a missing correlation_id (the spine requires every projected event to carry one)."""
    kind = internal_event["kind"]
    if valid_kinds is not None and kind not in valid_kinds:
        raise ValueError(f"unknown event kind {kind!r} — not in the allowed kind set (single source)")
    correlation_id = internal_event.get("correlation_id")
    if not correlation_id:
        raise ValueError("projected event must carry a correlation_id (tracing guarantee)")
    causation_id = internal_event.get("causation_id") or correlation_id  # root event: self-causation
    seq = int(internal_event["seq"])
    ce_id = "ce_" + hashlib.blake2b(f"{source}|{kind}|{seq}".encode(), digest_size=12).hexdigest()
    return {
        "specversion": "1.0", "id": ce_id, "source": source, "type": kind, "time": now,
        "datacontenttype": "application/json", "subject": internal_event.get("object_ref") or "",
        "tenant_id": tenant_id, "run_id": correlation_id,
        "correlation_id": correlation_id, "causation_id": causation_id, "trace_id": trace_id,
        "source_event_kind": kind, "source_event_seq": seq,
        "data": redact_secrets(internal_event.get("payload") or {}),
    }


__all__ = ["project_event_envelope", "redact_secrets"]
