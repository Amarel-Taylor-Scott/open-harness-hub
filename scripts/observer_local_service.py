#!/usr/bin/env python3
"""scripts.observer_local_service — the LOCAL backend for the AIDevObserver surface (web/aidevobserver).

This is the service-plane peer the AIDevObserver showcase reaches through a same-origin seam (the
showcase server proxies ``/api/observer/*`` here, exactly like ``/api/teleon/*`` → teleon_local_runtime).
It is a THIN HTTP front-end over the EXISTING observer engine (src/teleon/observer) — it rebuilds
NOTHING: review is ``review.review_session``, live spotting is ``router.route_session``, transcript
intake is ``capture.from_transcript``, and zero-install discovery is ``sessions.discover_sessions``.

  GET  /health                      → {"ok": true, "service": "observer"}   (also /healthz /readyz)
  GET  /sessions[?cwd=PATH]         → {"sessions": discover_sessions(cwd)}    (tolerates none → [])
  POST /review  {messages:[...]}    → the governed POST-SESSION report (review_session)
        OR      {transcript_path:…} → review_session(from_transcript(path))
  POST /live    {messages:[...],    → route_session(events, mode) → {surfaced, summary}
                 mode?:"advisory"}

The seam forwards the FULL path (strip=""), so the service answers both the bare paths above AND the
seam-prefixed ``/api/observer/<path>`` (an internal prefix strip) — so a direct ``curl :PORT/review``
and a same-origin ``/api/observer/review`` both work. CORS is open for local preview.

LAW (mirrors the engine): serves_truth=false on EVERY response; read-only (it reads a session to
write a report and stores nothing); every finding is a governed CANDIDATE a human triages (discovery
≠ trust). Synthetic/public session text only. Offline, stdlib-only. Port comes from the local service
registry (architecture/local_service_registry.json — single source; drift-gated by the proof).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# REUSE the existing observer engine — this service rebuilds nothing of it.
from src.teleon.observer import review_session            # noqa: E402  governed post-session reviewer
from src.teleon.observer.router import MODES, route_session  # noqa: E402  live spotter router + modes
from src.teleon.observer.capture import from_transcript   # noqa: E402  transcript JSONL → events
from src.teleon.observer.sessions import discover_sessions  # noqa: E402  zero-install session discovery

SERVICE_ID = "observer_runtime"
REGISTRY_PATH = REPO_ROOT / "architecture" / "local_service_registry.json"
VERSION = "1.0"
DEFAULT_LIVE_MODE = "advisory"          # the WHEN axis default for /live (graduated-restraint mode)
MAX_BODY_BYTES = 4 * 1024 * 1024        # bounded: pasted sessions/transcripts can be large, not unbounded
_API_PREFIX = "/api/observer"           # the same-origin seam prefix the showcase forwards (strip="")


def _registry_port() -> int:
    reg = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    svc = next(s for s in reg["services"] if s["service_id"] == SERVICE_ID)
    return int(svc["port"])


def _route_path(path: str) -> str:
    """Normalize an incoming path to the bare route. The seam forwards the full ``/api/observer/…``
    (strip=""), while a direct caller hits ``/review`` — both resolve to the same handler here."""
    if path == _API_PREFIX or path.startswith(_API_PREFIX + "/"):
        return path[len(_API_PREFIX):] or "/"
    return path


def _coerce_messages(items) -> list[dict]:
    """Tolerate either engine-shaped message dicts or bare strings (a string → a user turn). The
    router reads ``content``/``text`` off dicts, so a non-dict item would crash it — coerce first."""
    out: list[dict] = []
    for m in items or []:
        if isinstance(m, dict):
            out.append(m)
        elif isinstance(m, str) and m.strip():
            out.append({"role": "user", "content": m})
    return out


def _messages_from_body(body: dict) -> tuple[list[dict], str | None]:
    """Resolve a /review or /live body into the engine's message list. Accepts {messages:[...]} or
    {transcript_path:"…"} (read via capture.from_transcript). Returns (messages, error_or_None)."""
    if not isinstance(body, dict):
        return [], "body must be a JSON object"
    if body.get("transcript_path"):
        try:
            return from_transcript(str(body["transcript_path"])), None
        except FileNotFoundError:
            return [], f"transcript not found: {body['transcript_path']}"
        except OSError as exc:
            return [], f"cannot read transcript: {exc}"
    msgs = body.get("messages")
    if not isinstance(msgs, list):
        return [], "provide messages:[...] or transcript_path:'…'"
    coerced = _coerce_messages(msgs)
    if not coerced:
        return [], "messages is empty — nothing to review"
    return coerced, None


# --- the three operations (pure functions → the proof calls them directly, no socket) ---------------
def sessions_list(cwd: str | None) -> tuple[int, dict]:
    """GET /sessions — discovered Claude Code sessions for a cwd, newest first. Tolerates none → []."""
    try:
        found = discover_sessions(cwd) if cwd else discover_sessions()
    except Exception:           # discovery must never fail the surface — honest empty list
        found = []
    return 200, {"service": SERVICE_ID, "sessions": found or [], "serves_truth": False}


def review_report(body: dict) -> tuple[int, dict]:
    """POST /review — the governed post-session report (review_session over the full taxonomy)."""
    messages, err = _messages_from_body(body)
    if err:
        return 400, {"error": err, "serves_truth": False}
    rep = review_session(messages)
    return 200, {**rep, "service": SERVICE_ID, "serves_truth": False}


def live_report(body: dict) -> tuple[int, dict]:
    """POST /live — the live spotter (route_session) → what WOULD interrupt + the summary."""
    messages, err = _messages_from_body(body)
    if err:
        return 400, {"error": err, "serves_truth": False}
    mode = str(body.get("mode") or DEFAULT_LIVE_MODE)
    if mode not in MODES:
        return 400, {"error": f"mode must be one of {sorted(MODES)}", "serves_truth": False}
    r = route_session(messages, mode=mode)
    return 200, {"service": SERVICE_ID, "mode": r["mode"], "surfaced": r["surfaced"],
                 "summary": r["summary"], "governed": r["governed"], "serves_truth": False}


# --- HTTP surface -----------------------------------------------------------------------------------
class _Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, payload: dict, headers: dict[str, str] | None = None) -> None:
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")   # local preview / same-origin seam
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-AIDR-Request-Id")
        self.send_header("Cache-Control", "no-store")
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = min(int(self.headers.get("Content-Length") or 0), MAX_BODY_BYTES)
        raw = self.rfile.read(length).decode("utf-8") if length else "{}"
        return json.loads(raw or "{}")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = _route_path(parsed.path)
        if path in ("/health", "/healthz", "/readyz"):
            return self._send(200, {"ok": True, "service": "observer", "engine": "teleon.observer",
                                    "serves_truth": False})
        if path == "/version":
            return self._send(200, {"service": SERVICE_ID, "version": VERSION, "serves_truth": False})
        if path == "/sessions":
            cwd = (parse_qs(parsed.query).get("cwd") or [None])[0]
            return self._send(*sessions_list(cwd))
        return self._send(404, {"error": "unknown path", "serves_truth": False})

    def do_POST(self) -> None:  # noqa: N802
        path = _route_path(urlparse(self.path).path)
        if path not in ("/review", "/live"):
            return self._send(404, {"error": "unknown path", "serves_truth": False})
        try:
            body = self._read_json()
        except json.JSONDecodeError:
            return self._send(400, {"error": "invalid JSON", "serves_truth": False})
        return self._send(*(review_report(body) if path == "/review" else live_report(body)))

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._send(200, {"ok": True})

    def log_message(self, *args) -> None:  # the engine output is the record; keep the console quiet
        pass


def start_service(port: int = 0):
    """Bind a ThreadingHTTPServer on 127.0.0.1 (ephemeral port when 0) and serve in a daemon thread.
    Returns (server, thread, bound_port) — the same shape as events_local_service.start_service."""
    server = ThreadingHTTPServer(("127.0.0.1", port), _Handler)
    thread = threading.Thread(target=server.serve_forever, name=SERVICE_ID, daemon=True)
    thread.start()
    return server, thread, server.server_address[1]


def serve(port: int | None = None) -> None:
    port = port or _registry_port()
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")   # 0.0.0.0 only in container deploys
    server = ThreadingHTTPServer((bind_host, port), _Handler)
    pid_file = REPO_ROOT / ".agent" / "local-services" / f"{SERVICE_ID}.pid"
    pid_file.parent.mkdir(parents=True, exist_ok=True)
    pid_file.write_text(str(os.getpid()), encoding="utf-8")
    print(f"{SERVICE_ID} on http://{bind_host}:{port} — AIDevObserver session review "
          f"(review/live/sessions over the observer engine; serves_truth=false, read-only) "
          f"(stop by exact pid {os.getpid()})")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        pid_file.unlink(missing_ok=True)


# --- offline proof of the wire (the cross-cutting seam/registry proof is check_observer_local_service) ---
def _self_test() -> int:
    """In-process + loopback-HTTP proof: review yields a governed report (serves_truth=false,
    candidate findings) over a synthetic session AND a synthetic transcript file; live yields
    surfaced+summary; sessions tolerates none; a bad body 400s; the wire keeps serves_truth=false
    and CORS open. Ephemeral port, temp files, stdlib-only. Exit 0/1."""
    import tempfile
    import urllib.error
    import urllib.request

    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # synthetic session (no real PII): a grounded reinvention + a destructive-command footgun
    messages = [
        {"role": "user", "content": "let me write my own pdf parser from scratch"},
        {"role": "assistant", "content": "ok — first: git push --force origin main"},
    ]

    # in-process: review
    st, rep = review_report({"messages": messages})
    findings = rep.get("report", [])
    ck("review → 200 governed report (serves_truth=false)", st == 200 and rep["serves_truth"] is False)
    ck("review surfaces candidate findings", len(findings) >= 1
       and all(f.get("candidate") and f.get("serves_truth") is False for f in findings))

    # in-process: review over a synthetic TRANSCRIPT file (capture.from_transcript path)
    tmp = Path(tempfile.mkdtemp(prefix="observer-svc-selftest-"))
    try:
        tpath = tmp / "session.jsonl"
        tpath.write_text("\n".join(json.dumps(
            {"type": "user", "message": {"role": "user", "content": c}}) for c in
            ["let me build a custom retry with exponential backoff", "and my own oauth login"]) + "\n",
            encoding="utf-8")
        st_t, rep_t = review_report({"transcript_path": str(tpath)})
        ck("review over a transcript_path → 200 governed report",
           st_t == 200 and rep_t["serves_truth"] is False and len(rep_t.get("report", [])) >= 1)
        st_miss, _ = review_report({"transcript_path": str(tmp / "nope.jsonl")})
        ck("a missing transcript → honest 400 (not a crash)", st_miss == 400)

        # in-process: live + sessions tolerance + bad body
        st_l, live = live_report({"messages": messages, "mode": "advisory"})
        ck("live → 200 with surfaced + summary (serves_truth=false)",
           st_l == 200 and "surfaced" in live and "summary" in live and live["serves_truth"] is False)
        st_s, sess = sessions_list("/no/such/project/here")
        ck("sessions tolerates none → 200 with []", st_s == 200 and sess["sessions"] == []
           and sess["serves_truth"] is False)
        st_bad, _ = review_report({})
        ck("a body with neither messages nor transcript → 400", st_bad == 400)

        # over the WIRE: ephemeral loopback server, both bare and seam-prefixed paths
        server, thread, port = start_service(port=0)
        try:
            def call(method: str, path: str, body: dict | None = None):
                data = json.dumps(body).encode() if body is not None else None
                req = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data,
                                             method=method, headers={"Content-Type": "application/json"})
                try:
                    with urllib.request.urlopen(req, timeout=10) as r:
                        return r.status, json.loads(r.read() or b"{}"), dict(r.headers)
                except urllib.error.HTTPError as e:
                    return e.code, json.loads(e.read() or b"{}"), dict(e.headers)

            hs, hb, hh = call("GET", "/health")
            ck("wire GET /health → {ok, service:'observer'} + CORS open",
               hs == 200 and hb.get("service") == "observer"
               and hh.get("Access-Control-Allow-Origin") == "*")
            rs, rb, _ = call("POST", "/review", {"messages": messages})
            ck("wire POST /review → governed report (bare path)",
               rs == 200 and rb["serves_truth"] is False and len(rb.get("report", [])) >= 1)
            ps, pb, _ = call("POST", "/api/observer/review", {"messages": messages})
            ck("wire POST /api/observer/review → same report (seam-prefixed path)",
               ps == 200 and pb.get("summary", {}).get("findings") == rb.get("summary", {}).get("findings"))
            ls, lb, _ = call("POST", "/live", {"messages": messages})
            ck("wire POST /live → surfaced + summary", ls == 200 and "surfaced" in lb and "summary" in lb)
            ss, sb, _ = call("GET", "/sessions?cwd=/no/such/project")
            ck("wire GET /sessions tolerates none → []", ss == 200 and sb["sessions"] == [])
        finally:
            server.shutdown()
            thread.join(timeout=5)
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    print("\n" + ("PASS — observer_local_service: a thin HTTP front-end over the observer engine "
                  "(review_session / route_session / from_transcript / discover_sessions) — review "
                  "returns a governed report (serves_truth=false, candidate findings) over both inline "
                  "messages and a synthetic transcript, live returns surfaced+summary, sessions "
                  "tolerates none, bare and /api/observer-prefixed paths both resolve; CORS open, "
                  "read-only, stdlib-only."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="AIDevObserver session-review local service.")
    ap.add_argument("--serve", action="store_true", help="run the HTTP service")
    ap.add_argument("--port", type=int, default=None, help="override the registry port")
    ap.add_argument("--self-test", action="store_true", help="run the offline proof")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.serve:
        serve(args.port)
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
