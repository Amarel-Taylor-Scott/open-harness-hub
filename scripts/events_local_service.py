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
Persistence: dist/analytics/events.jsonl (append-only within a generation; at MAX_EVENTS the
file ROTATES to events.jsonl.1, one previous generation kept — never a permanent 429) —
counters rebuild from the live file on start. Floods get a transient 429 + Retry-After.
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
from collections import Counter, deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SERVICE_ID = "local_event_tracking_service"
REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
VERSION = "1.0"
EVENT_TYPES = {"page", "action", "exposure", "conversion", "llm"}
MAX_EVENTS = 50_000            # ring-GENERATION size (EVENTS.md cap): reaching it ROTATES the live
                               # file instead of bricking ingest forever (no fill-to-DoS 429)
ROTATED_SUFFIX = ".1"          # the single kept previous generation (events.jsonl.1): rotation
                               # RENAMES the full live file here — lossless law: the data being
                               # rotated is preserved, never deleted; only the prior .1 ages out
PER_MINUTE_INGEST_CAP = 600    # process-wide accepted events/min (~10/s): far above legit local
                               # beacon traffic, so a runaway client gets a TRANSIENT 429 +
                               # Retry-After instead of filling generations
INGEST_WINDOW_S = 60           # the sliding window the per-minute cap is measured over
MAX_BODY_BYTES = 256 * 1024
_PII_RE = re.compile(r"@|sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|\bak_[a-z0-9]+_[0-9a-f]{16,}")


def _registry_port() -> int:
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    svc = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    return int(svc["port"])


class EventsPlane:
    def __init__(self, state_dir: Path | None = None, clock: Callable[[], float] | None = None,
                 max_events: int = MAX_EVENTS, per_minute_cap: int = PER_MINUTE_INGEST_CAP) -> None:
        self.state_dir = Path(state_dir) if state_dir else (REPO_ROOT / "dist" / "analytics")
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.state_dir / "events.jsonl"
        self.rotated_path = self.path.with_name(self.path.name + ROTATED_SUFFIX)
        self.lock = threading.Lock()
        # clock + limits are PARAMETERS (not env) so the self-test runs fast with no sleeps
        self._clock = clock or time.time
        self.max_events = int(max_events)
        self.per_minute_cap = int(per_minute_cap)
        self._ingest_window: deque[float] = deque()    # accepted-event times inside INGEST_WINDOW_S;
        #                                                in-memory on purpose: transient flood state,
        #                                                not durable truth (single-process service)
        self.count = 0
        self.by_site: Counter[str] = Counter()
        self.by_type: Counter[str] = Counter()
        self.by_variant: Counter[str] = Counter()      # "experiment:variant:event"
        # counters rebuild from the LIVE generation only — the rotated .1 file is preserved
        # evidence (lossless law), not part of the live counts
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

    def _rotate(self) -> None:
        """Ring rotation at the generation cap (caller holds the lock): the FULL live file is
        atomically RENAMED to the one kept previous generation — lossless law: rotation preserves
        the data being rotated, never deletes the live file; only the prior .1 generation ages out.
        Live counters then restart: they always describe the live generation only."""
        if self.path.exists():
            os.replace(self.path, self.rotated_path)   # atomic; replaces the older .1 (exactly one kept)
        self.count = 0
        self.by_site.clear()
        self.by_type.clear()
        self.by_variant.clear()

    def ingest(self, payload) -> tuple[int, dict]:
        events = payload.get("events") if isinstance(payload, dict) and "events" in payload \
            else (payload if isinstance(payload, list) else [payload])
        now = self._clock()
        accepted, errors = [], []
        for evt in events:
            err = self.validate(evt)
            if err:
                errors.append(err)
                continue
            evt = dict(evt)
            evt["ts"] = int(now)
            accepted.append(evt)
        if errors:
            return 400, {"accepted": 0, "errors": errors[:5]}
        with self.lock:
            # transient flood control (sliding window) — NOT a permanent state: callers get a
            # Retry-After and succeed once the window drains; within a generation stays append-only
            while self._ingest_window and self._ingest_window[0] <= now - INGEST_WINDOW_S:
                self._ingest_window.popleft()
            if len(accepted) > self.per_minute_cap:
                # honest fail-closed: this batch could NEVER pass the window — say so, no fake retry
                return 400, {"accepted": 0,
                             "errors": [f"batch of {len(accepted)} exceeds the "
                                        f"{self.per_minute_cap}/min ingest cap — split it"]}
            if len(self._ingest_window) + len(accepted) > self.per_minute_cap:
                retry_after = max(1, int(INGEST_WINDOW_S - (now - self._ingest_window[0])))
                return 429, {"error": f"ingest cap {self.per_minute_cap}/min reached — transient, "
                                      "retry after the window drains",
                             "retry_after_s": retry_after}
            if self.count + len(accepted) > self.max_events:
                self._rotate()                         # un-bricks the sink: rotate, never reject forever
            with self.path.open("a", encoding="utf-8") as fh:
                for evt in accepted:
                    fh.write(json.dumps(evt, sort_keys=True) + "\n")
                    self._tally(evt)
                    self._ingest_window.append(now)
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

    def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")   # local preview only
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
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
        retry = {"Retry-After": str(out["retry_after_s"])} if status == 429 else None
        return self._send(status, out, retry)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def log_message(self, fmt, *args):  # the JSONL is the record
        pass


def start_service(port: int = 0, state_dir: Path | None = None,
                  clock: Callable[[], float] | None = None,
                  max_events: int = MAX_EVENTS, per_minute_cap: int = PER_MINUTE_INGEST_CAP):
    plane = EventsPlane(state_dir=state_dir, clock=clock,
                        max_events=max_events, per_minute_cap=per_minute_cap)
    handler = type("BoundHandler", (_Handler,), {"plane": plane})
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_ID, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def _self_test() -> int:
    """Offline proof of the ring + flood posture: the generation cap ROTATES (old generation
    preserved, exactly one kept, ingest continues — never a permanent 429), counters rebuild from
    the live generation only, the per-minute cap 429s with Retry-After and RECOVERS (injected
    clock — no sleeps), oversized batches fail honestly, and the wire keeps truth_authority:false.
    Temp state dirs, ephemeral port, stdlib-only. Exit 0/1."""
    import shutil
    import tempfile
    import urllib.error
    import urllib.request

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    def evt(i: int) -> dict:
        return {"site": "baltor", "event": "page", "name": f"p{i}", "anon": f"a_{i:04x}"}

    def lines(path: Path) -> int:
        return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0

    root = Path(tempfile.mkdtemp(prefix="events-proof-"))
    server = thread = None
    try:
        # A+B: rotation at the generation cap — old generation PRESERVED, ingest continues
        rot = EventsPlane(state_dir=root / "rot", max_events=5)
        st, out = rot.ingest({"events": [evt(i) for i in range(5)]})
        ck("A: a full generation ingests (202)", st == 202 and out["accepted"] == 5, f"{st} {out}")
        ck("A: no rotation below the cap", not rot.rotated_path.exists())
        st, out = rot.ingest(evt(5))
        ck("A: the cap does NOT brick ingest — the next event is still 202 (was a permanent 429)",
           st == 202 and out["accepted"] == 1, f"{st} {out}")
        ck("B: rotation preserved the full previous generation (5 lines in events.jsonl.1)",
           lines(rot.rotated_path) == 5, str(lines(rot.rotated_path)))
        ck("B: the live generation restarted (1 line, count 1)",
           lines(rot.path) == 1 and rot.count == 1 and rot.summary()["total"] == 1)
        st, _ = rot.ingest({"events": [evt(i) for i in range(6, 11)]})
        ck("B: a later rotation keeps exactly ONE previous generation (older replaced)",
           st == 202 and lines(rot.rotated_path) == 1 and lines(rot.path) == 5,
           f"{st} .1={lines(rot.rotated_path)} live={lines(rot.path)}")
        reborn = EventsPlane(state_dir=root / "rot")
        ck("B: counters rebuild from the LIVE generation only", reborn.count == 5, str(reborn.count))

        # C: per-minute cap — transient 429 with Retry-After, then recovery (injected clock)
        clock = [2_000_000.0]
        cap = EventsPlane(state_dir=root / "cap", clock=lambda: clock[0], per_minute_cap=3)
        for i in range(3):
            cap.ingest(evt(i))
        st, out = cap.ingest(evt(3))
        ck("C: the per-minute cap returns 429 with retry_after_s",
           st == 429 and 1 <= out.get("retry_after_s", 0) <= INGEST_WINDOW_S, f"{st} {out}")
        ck("C: a 429 stores nothing", lines(cap.path) == 3, str(lines(cap.path)))
        clock[0] += INGEST_WINDOW_S + 1
        st, out = cap.ingest(evt(3))
        ck("C: ingest RECOVERS once the window drains (transient, not permanent)",
           st == 202 and out["accepted"] == 1, f"{st} {out}")
        st, out = cap.ingest({"events": [evt(i) for i in range(10, 14)]})
        ck("C: a batch larger than the cap fails honestly (400, no fake retry)",
           st == 400 and "split" in json.dumps(out), f"{st} {out}")

        # D: over HTTP — Retry-After header on 429; the honest non-truth posture survives
        server, thread, port = start_service(port=0, state_dir=root / "http", per_minute_cap=2)

        def post(payload: dict) -> tuple[int, dict, dict]:
            req = urllib.request.Request(f"http://127.0.0.1:{port}/api/events", method="POST",
                                         data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.status, json.loads(r.read() or b"{}"), dict(r.headers)
            except urllib.error.HTTPError as e:
                return e.code, json.loads(e.read() or b"{}"), dict(e.headers)

        ok = [post(evt(i))[0] for i in range(2)]
        st, out, headers = post(evt(2))
        ck("D: the wire 429 carries a Retry-After header matching the payload",
           ok == [202, 202] and st == 429
           and headers.get("Retry-After") == str(out.get("retry_after_s")), f"{ok} {st} {headers}")
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status", timeout=10) as r:
            status_body = json.loads(r.read())
        ck("D: the plane still declares truth_authority:false",
           status_body.get("truth_authority") is False)
    finally:
        if server is not None:
            server.shutdown()
            thread.join(timeout=5)
        shutil.rmtree(root, ignore_errors=True)

    print("\n" + ("PASS — events_local_service --self-test: generation cap rotates (previous "
                  "generation preserved, exactly one kept, ingest never bricked), live-only "
                  f"counters, transient {PER_MINUTE_INGEST_CAP}/min-style cap with Retry-After that "
                  "recovers, honest oversized-batch 400, truth_authority:false intact."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main() -> int:
    port = _registry_port()
    plane = EventsPlane()
    handler = type("BoundHandler", (_Handler,), {"plane": plane})
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")  # 0.0.0.0 only in container deploys
    server = ThreadingHTTPServer((bind_host, port), handler)
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
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    raise SystemExit(main())
