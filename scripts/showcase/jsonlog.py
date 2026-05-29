"""Standardized JSON logging — one structured record per event.

Every record is a flat JSON object: {ts, level, event, ms?, ...fields}. The same schema is used
server-side (emitted to stdout for log aggregation) and returned to the front-end (result['log']),
so the Activity console renders exactly what the backend logged — "what is happening" is one
schema end to end. stdlib only.
"""
from __future__ import annotations

import json
import sys
import time

_LEVELS = ("debug", "info", "ok", "warn", "error")


def emit(event: str, level: str = "info", **fields) -> dict:
    """Write one structured JSON log line to stdout (and return the record)."""
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "level": level if level in _LEVELS else "info", "event": event}
    rec.update({k: v for k, v in fields.items() if v is not None})
    try:
        sys.stdout.write(json.dumps(rec, sort_keys=False, default=str) + "\n")
        sys.stdout.flush()
    except Exception:  # noqa: BLE001 - logging must never break the request
        pass
    return rec


class Trace:
    """Collects the structured events for ONE request (returned as result['log']) and emits each
    to stdout as it happens. ms is relative to the trace start."""

    def __init__(self, request: str = "build") -> None:
        self.request = request
        self.events: list[dict] = []
        self._t0 = time.time()

    def add(self, event: str, level: str = "info", **fields) -> dict:
        ms = int((time.time() - self._t0) * 1000)
        rec = {"ms": ms, "level": level if level in _LEVELS else "info", "event": event}
        rec.update({k: v for k, v in fields.items() if v is not None})
        self.events.append(rec)
        emit(event, level=level, ms=ms, request=self.request, **fields)
        return rec
