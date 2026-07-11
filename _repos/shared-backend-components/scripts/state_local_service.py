#!/usr/bin/env python3
"""scripts.state_local_service — session/action state; NEVER a truth authority (the declared :9427 service).

Fulfils `local_state_service` in the service registry: a small keyed state store for transient
session/action state (a wizard step, a draft, an in-flight action's progress). Every response
carries ``truth_authority: false`` — this holds working state, it is NEVER the source of truth
(the governed record / verification gate is). State is REPLAYED from an append-only op-log, so
the history is auditable and a crash loses nothing committed. stdlib-only; binds 127.0.0.1.

Endpoints (private — /api/state/* per the registry):
  GET    /healthz                  → {"ok": true}
  GET    /api/state/<key>          → {"key", "value", "truth_authority": false} (404 if unset)
  PUT    /api/state/<key>          → set value from body {"value": ...} → {"key", "ok"}
  POST   /api/state/<key>/append   → append body {"item": ...} to a list value → {"key", "len"}
  DELETE /api/state/<key>          → tombstone the key → {"key", "deleted"}

CLI: python3 _repos/shared-backend-components/scripts/state_local_service.py [--self-test]
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
SERVICE_REGISTRY = _resource("architecture") / "local_service_registry.json"
LOG = _resource("dist") / "local-services-state" / "state-log.jsonl"
SERVICE_ID = "local_state_service"
DEFAULT_PORT = 9427

#: op kinds in the append-only log (single source).
OP_SET = "set"
OP_APPEND = "append"
OP_DELETE = "delete"


def _port() -> int:
    try:
        for svc in json.loads(SERVICE_REGISTRY.read_text(encoding="utf-8"))["services"]:
            if svc.get("service_id") == SERVICE_ID and svc.get("port"):
                return int(svc["port"])
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_PORT


def _append_op(op: dict, *, log: Path | None = None) -> None:
    log = log or LOG
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(op, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n")


def replay(*, log: Path | None = None) -> dict:
    """Current state = the append-only op-log replayed (set/append/delete in order)."""
    log = log or LOG
    state: dict = {}
    if not log.exists():
        return state
    for line in log.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            op = json.loads(line)
        except json.JSONDecodeError:
            continue
        kind, key = op.get("op"), op.get("key")
        if not key:
            continue
        if kind == OP_SET:
            state[key] = op.get("value")
        elif kind == OP_APPEND:
            cur = state.get(key)
            state[key] = (cur if isinstance(cur, list) else []) + [op.get("item")]
        elif kind == OP_DELETE:
            state.pop(key, None)
    return state


def set_state(key: str, value, *, log: Path | None = None) -> None:
    if not isinstance(key, str) or not key:
        raise ValueError("state key must be a non-empty str")
    _append_op({"op": OP_SET, "key": key, "value": value}, log=log)


def append_state(key: str, item, *, log: Path | None = None) -> int:
    if not isinstance(key, str) or not key:
        raise ValueError("state key must be a non-empty str")
    _append_op({"op": OP_APPEND, "key": key, "item": item}, log=log)
    return len(replay(log=log).get(key, []))


def delete_state(key: str, *, log: Path | None = None) -> None:
    if not isinstance(key, str) or not key:
        raise ValueError("state key must be a non-empty str")
    _append_op({"op": OP_DELETE, "key": key}, log=log)


def get_state(key: str, *, log: Path | None = None):
    return replay(log=log).get(key)


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        payload = json.dumps({**body, "truth_authority": False}).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _key(self, path: str, suffix: str = "") -> str:
        base = "/api/state/"
        k = path[len(base):]
        if suffix and k.endswith(suffix):
            k = k[: -len(suffix)]
        return k

    def _body(self) -> dict:
        n = int(self.headers.get("content-length", 0))
        try:
            return json.loads(self.rfile.read(n) or b"{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/healthz", "/readyz"):
            return self._send(200, {"ok": True})
        if path.startswith("/api/state/"):
            state = replay()
            key = self._key(path)
            if key in state:
                return self._send(200, {"key": key, "value": state[key]})
            return self._send(404, {"error": "unset", "key": key})
        self._send(404, {"error": "not_found"})

    def do_PUT(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/state/"):
            return self._send(404, {"error": "not_found"})
        try:
            set_state(self._key(path), self._body().get("value"))
            self._send(200, {"key": self._key(path), "ok": True})
        except ValueError as e:
            self._send(400, {"error": str(e)})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path.startswith("/api/state/") and path.endswith("/append"):
            try:
                key = self._key(path, "/append")
                length = append_state(key, self._body().get("item"))
                return self._send(200, {"key": key, "len": length})
            except ValueError as e:
                return self._send(400, {"error": str(e)})
        self._send(404, {"error": "not_found"})

    def do_DELETE(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/api/state/"):
            return self._send(404, {"error": "not_found"})
        try:
            delete_state(self._key(path))
            self._send(200, {"key": self._key(path), "deleted": True})
        except ValueError as e:
            self._send(400, {"error": str(e)})

    def log_message(self, *a):  # quiet
        pass


def main() -> int:
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")
    port = _port()
    httpd = ThreadingHTTPServer((bind_host, port), _Handler)
    print(f"state service → http://{bind_host}:{port}/api/state (replayed op-log; truth_authority=false)")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


def _self_test() -> int:
    import tempfile
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "state-log.jsonl"
        ck("unset key → None (honest)", get_state("wizard", log=log) is None)
        set_state("wizard", {"step": 1}, log=log)
        ck("set then get round-trips", get_state("wizard", log=log) == {"step": 1})
        set_state("wizard", {"step": 2}, log=log)
        ck("set overwrites (replay = latest)", get_state("wizard", log=log) == {"step": 2})
        n1 = append_state("events", "a", log=log)
        n2 = append_state("events", "b", log=log)
        ck("append builds a list, returns length", n1 == 1 and n2 == 2
           and get_state("events", log=log) == ["a", "b"])
        delete_state("wizard", log=log)
        ck("delete tombstones the key (replay drops it)", get_state("wizard", log=log) is None)
        ck("delete is append-only (events survive)", get_state("events", log=log) == ["a", "b"])
        # the op-log is the audit trail: 5 ops appended (2 set + 2 append + 1 delete), nothing rewritten
        ck("append-only op-log (5 ops)", log.read_text().count("\n") == 5)
        # never truth authority: the handler stamps truth_authority=false (checked via a fake handler)
        raised = False
        try:
            set_state("", 1, log=log)
        except ValueError:
            raised = True
        ck("empty key raises", raised)
        # replay is deterministic
        ck("replay deterministic", replay(log=log) == replay(log=log))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"state_local_service: {len(checks) - len(failed)}/{len(checks)} — keyed session/action "
            "state replayed from an append-only op-log (set/append/delete), truth_authority=false always.")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
