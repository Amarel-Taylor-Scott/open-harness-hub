#!/usr/bin/env python3
"""scripts.receipt_local_service — records receipts for important flows (the declared :9426 service).

Fulfils `local_receipt_service` in the service registry: an append-only receipt store for the
flows that matter (promotions, model invocations, deliveries, escalations). A receipt is
content-addressed and ``is_truth: false`` — it RECORDS what happened, it never decides truth
(the verification gate does). Append-only: a receipt is never mutated or deleted, so the log is
an audit trail. stdlib-only; binds 127.0.0.1 (OH_BIND_HOST=0.0.0.0 in containers).

Endpoints (private — /api/receipts/* per the registry):
  GET  /healthz                       → {"ok": true}
  POST /api/receipts                  → append {kind, payload[, flow_id]} → {receipt_id}
  GET  /api/receipts                  → list (newest first; optional ?kind= / ?flow_id=)
  GET  /api/receipts/<receipt_id>     → one receipt, or 404

CLI: python3 scripts/receipt_local_service.py [--self-test]
"""
from __future__ import annotations

import hashlib
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

REPO = Path(__file__).resolve().parents[1]
SERVICE_REGISTRY = REPO / "architecture" / "local_service_registry.json"
STORE = REPO / "dist" / "local-services-state" / "receipts.jsonl"
SERVICE_ID = "local_receipt_service"
DEFAULT_PORT = 9426
HASH_ALGORITHM = "sha256"
RECEIPT_ID_PREFIX = "rcpt:"
RECEIPT_ID_HEX_LEN = 24


def _port() -> int:
    try:
        for svc in json.loads(SERVICE_REGISTRY.read_text(encoding="utf-8"))["services"]:
            if svc.get("service_id") == SERVICE_ID and svc.get("port"):
                return int(svc["port"])
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_PORT


def _canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def append_receipt(kind: str, payload: dict, *, flow_id: str | None = None,
                   now: float = 0.0, store: Path | None = None) -> dict:
    """Append a content-addressed receipt. is_truth is always False. now is injected (no wall clock)."""
    if not isinstance(kind, str) or not kind:
        raise ValueError("receipt kind must be a non-empty str")
    if not isinstance(payload, dict):
        raise ValueError("receipt payload must be a dict")
    store = store or STORE
    body = _canonical({"kind": kind, "payload": payload, "flow_id": flow_id})
    rid = RECEIPT_ID_PREFIX + hashlib.new(HASH_ALGORITHM, body.encode("utf-8")).hexdigest()[:RECEIPT_ID_HEX_LEN]
    receipt = {"receipt_id": rid, "kind": kind, "flow_id": flow_id, "payload": payload,
               "recorded_at": float(now), "is_truth": False}
    store.parent.mkdir(parents=True, exist_ok=True)
    with store.open("a", encoding="utf-8") as fh:
        fh.write(_canonical(receipt) + "\n")
    return receipt


def list_receipts(*, kind: str | None = None, flow_id: str | None = None,
                  store: Path | None = None) -> list[dict]:
    store = store or STORE
    if not store.exists():
        return []
    out = []
    for line in store.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if kind is not None and r.get("kind") != kind:
            continue
        if flow_id is not None and r.get("flow_id") != flow_id:
            continue
        out.append(r)
    out.reverse()  # newest first
    return out


def get_receipt(receipt_id: str, *, store: Path | None = None) -> dict | None:
    for r in list_receipts(store=store):
        if r.get("receipt_id") == receipt_id:
            return r
    return None


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path in ("/healthz", "/readyz"):
            return self._send(200, b'{"ok":true}')
        if parsed.path == "/api/receipts":
            recs = list_receipts(kind=(qs.get("kind") or [None])[0],
                                 flow_id=(qs.get("flow_id") or [None])[0])
            return self._send(200, json.dumps({"receipts": recs, "count": len(recs)}).encode())
        if parsed.path.startswith("/api/receipts/"):
            rid = parsed.path[len("/api/receipts/"):]
            r = get_receipt(rid)
            return self._send(200 if r else 404, json.dumps(r or {"error": "not_found"}).encode())
        self._send(404, b'{"error":"not_found"}')

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/receipts":
            return self._send(404, b'{"error":"not_found"}')
        try:
            n = int(self.headers.get("content-length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            r = append_receipt(str(data.get("kind", "")), data.get("payload") or {},
                               flow_id=data.get("flow_id"), now=float(data.get("now", 0.0)))
            self._send(201, json.dumps({"receipt_id": r["receipt_id"], "is_truth": False}).encode())
        except (ValueError, json.JSONDecodeError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode())

    def log_message(self, *a):  # quiet
        pass


def main() -> int:
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")
    port = _port()
    httpd = ThreadingHTTPServer((bind_host, port), _Handler)
    print(f"receipt service → http://{bind_host}:{port}/api/receipts (append-only; is_truth=false)")
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
        st = Path(tmp) / "receipts.jsonl"
        ck("empty store → no receipts (honest)", list_receipts(store=st) == [])
        r1 = append_receipt("promotion", {"unit": "cap-1", "decision": "promoted"}, flow_id="f1", now=100.0, store=st)
        ck("append returns a content-addressed receipt, is_truth false",
           r1["receipt_id"].startswith(RECEIPT_ID_PREFIX) and r1["is_truth"] is False)
        # content-addressed: identical content → identical id (replay-detectable)
        r1b = append_receipt("promotion", {"unit": "cap-1", "decision": "promoted"}, flow_id="f1", now=200.0, store=st)
        ck("same content → same receipt_id (replay-detectable)", r1b["receipt_id"] == r1["receipt_id"])
        append_receipt("delivery", {"to": "x"}, flow_id="f2", now=300.0, store=st)
        ck("list newest-first", [r["kind"] for r in list_receipts(store=st)][0] == "delivery")
        ck("filter by kind", len(list_receipts(kind="promotion", store=st)) == 2)
        ck("filter by flow_id", len(list_receipts(flow_id="f2", store=st)) == 1)
        ck("get by id", get_receipt(r1["receipt_id"], store=st)["payload"]["unit"] == "cap-1")
        ck("get unknown → None", get_receipt("rcpt:nope", store=st) is None)
        # append-only: nothing deleted; bad input raises
        ck("append-only audit trail (3 lines for 3 appends)", st.read_text().count("\n") == 3)
        raised = False
        try:
            append_receipt("", {}, store=st)
        except ValueError:
            raised = True
        ck("empty kind raises (no fabricated receipt)", raised)

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"receipt_local_service: {len(checks) - len(failed)}/{len(checks)} — append-only "
            "content-addressed receipts (is_truth=false), filter by kind/flow, get by id; the gate promotes, not this.")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
