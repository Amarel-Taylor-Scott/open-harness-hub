#!/usr/bin/env python3
"""local_emulators.source_of_truth_emulator — emulate a LIVE regulated-fact source (eCFR / Federal Register) for
local dev (Docker / Tilt). Closes the go-live "live source fetch + CDC freshness" seam locally.

  GET  /value    -> {source, value, version}     (the current authoritative value the freshness runtime serves)
  GET  /version  -> {source, version}
  POST /change   {value, version}  -> changes the value and returns a freshness CDC event
                                      {kind:'changed', source, version} — the shape self_healing.reheal_on_source_change
                                      and FreshnessSyncedCapability.on_source_change consume.

So locally you can: bind a capability to this emulator, serve the current value, POST /change to "amend the
regulation", watch the stale answer get held out, then re-sync to the new value. Importable (in-process testable)
+ runnable (stdlib http.server only — no deps, so it runs in a tiny container). Never serves truth.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer


class SourceOfTruthEmulator:
    """In-process emulator of a single authoritative source. ``change`` returns the freshness CDC event."""

    def __init__(self, source_id: str = "ecfr://12/1005.11", value: str = "10 business days",
                 version: str = "2025-edition") -> None:
        self.source_id = source_id
        self._value = value
        self._version = version
        self._changes = 0

    def current(self) -> dict:
        return {"source": self.source_id, "value": self._value, "version": self._version, "serves_truth": False}

    def change(self, value: str, version: str) -> dict:
        """Amend the source and return the freshness CDC 'changed' event (the reheal trigger)."""
        self._value, self._version = value, version
        self._changes += 1
        return {"kind": "changed", "source": self.source_id, "version": version, "serves_truth": False}

    @property
    def change_count(self) -> int:
        return self._changes


def _make_handler(emu: SourceOfTruthEmulator):
    class _H(BaseHTTPRequestHandler):
        def _send(self, code: int, body: dict) -> None:
            data = json.dumps(body).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            if self.path.rstrip("/") == "/value":
                self._send(200, emu.current())
            elif self.path.rstrip("/") == "/version":
                self._send(200, {"source": emu.source_id, "version": emu.current()["version"]})
            elif self.path.rstrip("/") in ("", "/health", "/healthz"):
                self._send(200, {"ok": True, "source": emu.source_id, "changes": emu.change_count})
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):  # noqa: N802
            if self.path.rstrip("/") != "/change":
                self._send(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
            event = emu.change(body.get("value", emu.current()["value"]), body.get("version", "amended"))
            self._send(200, event)

        def log_message(self, *_args):  # quiet
            return
    return _H


def serve(emu: SourceOfTruthEmulator | None = None, *, host: str = "0.0.0.0", port: int = 8081) -> None:  # pragma: no cover
    emu = emu or SourceOfTruthEmulator()
    HTTPServer((host, port), _make_handler(emu)).serve_forever()


if __name__ == "__main__":  # pragma: no cover
    serve(host=os.environ.get("EMU_HOST", "0.0.0.0"), port=int(os.environ.get("EMU_SOURCE_PORT", "8081")))
