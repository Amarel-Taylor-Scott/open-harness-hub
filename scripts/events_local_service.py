#!/usr/bin/env python3
"""scripts.events_local_service — the LOCAL analytics events + A/B plane (native recreation).

Implements the platform handoff's EVENTS.md contract in the repo's own patterns (the bundle's
Node core is reference-only): one event shape across all surfaces, a local sink, and the A/B
summary — projection/evidence only, NOT the platform event bus and never truth.

  POST /api/events            one event, an array, or {"events":[...]}
  GET  /api/events/summary    counts by site · event type · experiment:variant
  GET  /healthz /readyz /version /api/status     (Cloud-Run-like service contract)

Event shape (EVENTS.md): {site, event: page|action|exposure|conversion|llm, name,
experiment?, variant?, anon, props?}. Guards: `anon` is a random per-browser id — events
carrying an email-shaped anon or obvious PII/keys are REJECTED (400), never stored.
Persistence: dist/analytics/events.jsonl (append-only, capped) — counters rebuild on start.
Offline, stdlib-only; CORS open for local preview. Port comes from the local service registry
(architecture/local_service_registry.json — single source; drift-gated by the proof).
"""
from __future__ import annotations

import json
import os
import re
import sys
import threading
import time
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SERVICE_ID = "local_event_tracking_service"
REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
VERSION = "1.0"
EVENT_TYPES = {"page", "action", "exposure", "conversion", "llm"}
MAX_EVENTS = 50_000            # EVENTS.md cap for the local sink
MAX_BODY_BYTES = 256 * 1024
_PII_RE = re.compile(r"@|sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|\bak_[a-z0-9]+_[0-9a-f]{16,}")


def _registry_port() -> int:
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    svc = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    return int(svc["port"])


class EventsPlane:
    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = Path(state_dir) if state_dir else (REPO_ROOT / "dist" / "analytics")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.state_dir / "events.jsonl"
        self.lock = threading.Lock()
        self.count = 0
        self.by_site: Counter[str] = Counter()
        self.by_type: Counter[str] = Counter()
        self.by_variant: Counter[str] = Counter()      # "experiment:variant:event"
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                try:
                    self._tally(json.loads(line))
                except json.JSONDecodeError:
                    continue

    def _tally(self, evt: dict) -> None:
        self.count += 1
        self.by_site[str(evt.get("site"))] += 1
        self.by_type[str(evt.get("event"))] += 1
        if evt.get("experiment"):
            self.by_variant[f"{evt['experiment']}:{evt.get('variant')}:{evt.get('event')}"] += 1

    def validate(self, evt: dict) -> str | None:
        if not isinstance(evt, dict):
            return "event must be an object"
        if evt.get("event") not in EVENT_TYPES:
            return f"event must be one of {sorted(EVENT_TYPES)}"
        if not evt.get("site") or not evt.get("name"):
            return "site and name are required"
        if evt["event"] in ("exposure", "conversion") and not (evt.get("experiment") and evt.get("variant")):
            return "exposure/conversion require experiment and variant"
        blob = json.dumps(evt)
        if _PII_RE.search(str(evt.get("anon", ""))) or _PII_RE.search(blob):
            return "rejected: event carries PII/email/key-shaped material (anon ids only)"
        return None

    def ingest(self, payload) -> tuple[int, dict]:
        events = payload.get("events") if isinstance(payload, dict) and "events" in payload \
            else (payload if isinstance(payload, list) else [payload])
        accepted, errors = [], []
        for evt in events:
            err = self.validate(evt)
            if err:
                errors.append(err)
                continue
            evt = dict(evt)
            evt["ts"] = int(time.time())
            accepted.append(evt)
        if errors:
            return 400, {"accepted": 0, "errors": errors[:5]}
        with self.lock:
            if self.count + len(accepted) > MAX_EVENTS:
                return 429, {"error": f"local sink cap reached ({MAX_EVENTS})"}
            with self.path.open("a", encoding="utf-8") as fh:
                for evt in accepted:
                    fh.write(json.dumps(evt, sort_keys=True) + "\n")
                    self._tally(evt)
        return 202, {"accepted": len(accepted)}

    def summary(self) -> dict:
        with self.lock:
            variants: dict[str, dict] = {}
            for key, n in self.by_variant.items():
                experiment, variant, etype = key.rsplit(":", 2)
                slot = variants.setdefault(f"{experiment}:{variant}", {"exposure": 0, "conversion": 0})
                if etype in slot:
                    slot[etype] = n
            for slot in variants.values():
                slot["conversion_rate"] = round(slot["conversion"] / slot["exposure"], 4) if slot["exposure"] else None
            return {"total": self.count, "by_site": dict(self.by_site),
                    "by_type": dict(self.by_type), "experiments": variants}


class _Handler(BaseHTTPRequestHandler):
    plane: EventsPlane = None  # type: ignore[assignment]

    def _send(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")   # local preview only
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.partition("?")[0]
        if path == "/healthz":
            return self._send(200, {"ok": True, "service": SERVICE_ID})
        if path == "/readyz":
            return self._send(200, {"ready": True, "events": self.plane.count})
        if path == "/version":
            return self._send(200, {"service": SERVICE_ID, "version": VERSION})
        if path == "/api/status":
            return self._send(200, {"ok": True, "service": SERVICE_ID, "events": self.plane.count,
                                    "truth_authority": False, "note": "projection/evidence only"})
        if path == "/api/events/summary":
            return self._send(200, self.plane.summary())
        return self._send(404, {"error": "unknown path"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.partition("?")[0] != "/api/events":
            return self._send(404, {"error": "unknown path"})
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON"})
        status, out = self.plane.ingest(payload)
        return self._send(status, out)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def log_message(self, fmt, *args):  # the JSONL is the record
        pass


def start_service(port: int = 0, state_dir: Path | None = None):
    plane = EventsPlane(state_dir=state_dir)
    handler = type("BoundHandler", (_Handler,), {"plane": plane})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_ID, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def main() -> int:
    port = _registry_port()
    plane = EventsPlane()
    handler = type("BoundHandler", (_Handler,), {"plane": plane})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    pid_file = REPO_ROOT / ".agent" / "local-services" / f"{SERVICE_ID}.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    print(f"{SERVICE_ID} on http://127.0.0.1:{port} — {plane.count} events loaded "
          f"(stop by exact pid {os.getpid()})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        pid_file.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
