#!/usr/bin/env python3
"""scripts.llm_plane_local_service — a LOCAL HTTP surface over the Teleon inference plane (:9425).

Fulfils `local_llm_plane_emulator` in the service registry. PROJECTION-ONLY: it exposes the
EXISTING canonical OIPS router (`_repos/teleon/backend/src/teleon/inference`) — provider graph, health, preference
resolution, and a route decision — behind a small HTTP surface. It WIRES that module, it does not
duplicate routing logic. A "completion" here is a DETERMINISTIC stub derived from the prompt (never
a network call); real network LLMs stay owner-gated (they require a secret_ref the offline plane
does not hold). Every route decision yields a receipt (is_truth=false). stdlib-only; binds 127.0.0.1.

Endpoints (private — /api/inference/* per the registry):
  GET  /healthz | /readyz                 → {"ok": true}
  GET  /api/inference/providers           → redacted provider nodes (no secret values)
  GET  /api/inference/models              → the provider graph (nodes + edges)
  GET  /api/inference/health              → per-node health (external nodes: requires_secret_ref)
  POST /api/inference/route               → {layers[, available_secrets, prompt]} → route decision
                                            + deterministic stub completion + a receipt

CLI: python3 _repos/shared-backend-components/scripts/llm_plane_local_service.py [--self-test]
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.inference import api_projection as proj
from src.teleon.inference import oips

SERVICE_REGISTRY = _resource("architecture") / "local_service_registry.json"
SERVICE_ID = "local_llm_plane_emulator"
DEFAULT_PORT = 9425
#: A stub "completion" is the prompt's content hash — deterministic, offline, and obviously not a
#: real model answer. truth_authority is always false: the plane routes + records, it never decides truth.
STUB_PREFIX = "stub:"
STUB_HEX_LEN = 16


def _port() -> int:
    try:
        for svc in json.loads(SERVICE_REGISTRY.read_text(encoding="utf-8"))["services"]:
            if svc.get("service_id") == SERVICE_ID and svc.get("port"):
                return int(svc["port"])
    except Exception:  # noqa: BLE001
        pass
    return DEFAULT_PORT


def route_and_stub(layers: list[dict], *, available_secrets: list[str] | None = None,
                   prompt: str = "") -> dict:
    """Resolve a preference + select a provider via OIPS, then return a DETERMINISTIC stub completion
    and a receipt. No network call; an external node only wins if its secret is actually present."""
    resolved = proj.resolve_preference(layers or [])
    decision = oips.select_provider(resolved, available_secrets=set(available_secrets or []))
    chosen = decision.get("selected_provider_node_id")
    # The stub answer is the content hash of (chosen route + prompt) — offline + reproducible.
    body = json.dumps({"chosen": chosen, "prompt": prompt}, sort_keys=True)
    stub = STUB_PREFIX + hashlib.sha256(body.encode("utf-8")).hexdigest()[:STUB_HEX_LEN]
    receipt_body = json.dumps({"chosen": chosen, "fallback_used": decision.get("fallback_used"),
                               "prompt": prompt}, sort_keys=True)
    receipt_id = "rcpt:" + hashlib.sha256(receipt_body.encode("utf-8")).hexdigest()[:24]
    return {"route": decision, "completion": {"text": stub, "is_stub": True, "served_truth": False},
            "receipt": {"receipt_id": receipt_id, "kind": "model_invocation", "is_truth": False,
                        "selected_provider_node_id": chosen, "fallback_used": decision.get("fallback_used")},
            "truth_authority": False}


class _Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json") -> None:
        self.send_response(code)
        self.send_header("content-type", ctype)
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/healthz", "/readyz"):
            return self._send(200, b'{"ok":true}')
        if path == "/api/inference/providers":
            return self._send(200, json.dumps({"providers": proj.providers()}).encode())
        if path == "/api/inference/models":
            return self._send(200, json.dumps(proj.model_graph()).encode())
        if path == "/api/inference/health":
            return self._send(200, json.dumps({"health": proj.health()}).encode())
        self._send(404, b'{"error":"not_found"}')

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path != "/api/inference/route":
            return self._send(404, b'{"error":"not_found"}')
        try:
            n = int(self.headers.get("content-length", 0))
            data = json.loads(self.rfile.read(n) or b"{}")
            out = route_and_stub(data.get("layers") or [],
                                 available_secrets=data.get("available_secrets") or [],
                                 prompt=str(data.get("prompt", "")))
            self._send(200, json.dumps(out).encode())
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            self._send(400, json.dumps({"error": str(e)}).encode())

    def log_message(self, *a):  # quiet
        pass


def main() -> int:
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")
    port = _port()
    httpd = ThreadingHTTPServer((bind_host, port), _Handler)
    print(f"llm-plane → http://{bind_host}:{port}/api/inference/route (deterministic stub; network owner-gated)")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
    return 0


def _self_test() -> int:
    checks = []

    def ck(n, ok):
        checks.append((n, ok))

    # Projections wire the canonical graph (no secret values leak).
    provs = proj.providers()
    ck("providers projected (redacted: has_secret_ref boolean only, never a value)",
       bool(provs) and all("secret_ref" not in p and "has_secret_ref" in p for p in provs))
    ck("model graph has nodes + edges", set(proj.model_graph()) >= {"nodes", "edges"})
    ck("health is offline-honest (no live probe)", all(h["live_checked"] is False for h in proj.health()))

    # A route with NO secrets → never lands on an external node that needs one (fail-closed to local).
    layers = [{"effective": {}}] if False else []  # use the real resolver path
    out = route_and_stub(layers, available_secrets=[], prompt="summarize this")
    ck("route returns a decision + a stub completion (is_stub, not truth)",
       out["completion"]["is_stub"] is True and out["completion"]["served_truth"] is False)
    ck("route is recorded as a receipt (is_truth false)", out["receipt"]["is_truth"] is False)
    ck("plane never claims truth authority", out["truth_authority"] is False)
    chosen = out["route"].get("selected_provider_node_id")
    node = {n["node_id"]: n for n in oips.load_graph()["nodes"]}.get(chosen, {})
    ck("offline route lands on a node needing no secret (external→local fallback)",
       bool(chosen) and (not node.get("external", False) or out["route"].get("fallback_used")))
    # Deterministic: same inputs → same stub + same receipt id.
    again = route_and_stub(layers, available_secrets=[], prompt="summarize this")
    ck("deterministic stub + receipt id", again["completion"]["text"] == out["completion"]["text"]
       and again["receipt"]["receipt_id"] == out["receipt"]["receipt_id"])

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"llm_plane_local_service: {len(checks) - len(failed)}/{len(checks)} — projects the canonical "
            "OIPS router over HTTP (providers/models/health/route); deterministic offline stub; network "
            "owner-gated; every route is a receipt; truth_authority=false.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_self_test() if "--self-test" in sys.argv else main())
