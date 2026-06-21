#!/usr/bin/env python3
"""config_ui_server — serve the medium-config UI + SAVE the client's selections to architecture/medium_config.json.

Makes the config UI actually configurable: GET / serves the page (scripts.build_config_ui.render), GET /config returns
the current config, POST /save writes the per-function medium selections AFTER validating every id against the live
registries (no-magic-values; an unknown medium is rejected, never written). Secrets are NOT accepted here — tokens stay
in .env / the secret store (SecretRefs); this only persists the medium ROUTING. Offline; stdlib only. serves_truth=false.

  --self-test   prove save validates + persists + rejects unknown mediums (no server bind)
  --serve [port]   run the local server (default 8765)
CLI: PYTHONPATH=. python3 scripts/config_ui_server.py --serve
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.config.medium_resolver import available_mediums

_CONFIG = REPO / "architecture" / "medium_config.json"


def save_config(payload: dict, *, config_path: Path | None = None) -> dict:
    """Validate + persist a tenant's per-function medium selections. ``payload`` = {tenant, per_function:{fn:{compute,
    llm,search}}}. Rejects any medium id not in the live registries (never writes an invalid config). Returns
    {saved, errors}. Lossless: merges into the existing config (other tenants/functions untouched)."""
    path = config_path or _CONFIG
    cfg = json.loads(path.read_text(encoding="utf-8"))
    avail = available_mediums()
    tenant = payload.get("tenant", "demo")
    pf = payload.get("per_function", {})
    errors = []
    for fn, mediums in pf.items():
        for kind, val in mediums.items():
            if kind in ("compute", "llm", "search") and val and val not in avail.get(kind, []):
                errors.append(f"{fn}.{kind}={val!r} is not a known {kind} medium")
    if errors:
        return {"saved": False, "errors": errors}
    t = cfg.setdefault("tenants", {}).setdefault(tenant, {})
    t_pf = t.setdefault("per_function", {})
    for fn, mediums in pf.items():
        t_pf.setdefault(fn, {}).update({k: v for k, v in mediums.items() if k in ("compute", "llm", "search") and v})
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    return {"saved": True, "tenant": tenant, "functions": sorted(pf), "errors": []}


def _handler():
    from http.server import BaseHTTPRequestHandler

    class H(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body if isinstance(body, bytes) else (json.dumps(body).encode() if ctype == "application/json" else body.encode())
            self.send_response(code); self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data))); self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                from scripts.build_config_ui import render
                self._send(200, render("demo"), "text/html")
            elif self.path == "/config":
                self._send(200, json.loads(_CONFIG.read_text()))
            else:
                self._send(404, {"error": "not found"})

        def do_POST(self):
            if self.path != "/save":
                self._send(404, {"error": "not found"}); return
            n = int(self.headers.get("Content-Length", 0))
            try:
                payload = json.loads(self.rfile.read(n) or b"{}")
                self._send(200, save_config(payload))
            except Exception as e:  # noqa: BLE001
                self._send(400, {"saved": False, "errors": [str(e)]})

        def log_message(self, *a):  # quiet
            pass
    return H


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "medium_config.json"
        p.write_text(_CONFIG.read_text(), encoding="utf-8")
        # valid save persists
        avail = available_mediums()
        valid_compute = "k8s_deployment_worker" if "k8s_deployment_worker" in avail["compute"] else avail["compute"][0]
        r = save_config({"tenant": "acme", "per_function": {"classification": {"compute": valid_compute, "llm": "ollama"}}}, config_path=p)
        ck("a valid selection is saved", r["saved"] is True, str(r))
        saved = json.loads(p.read_text())
        ck("the saved config persists the per-function medium", saved["tenants"]["acme"]["per_function"]["classification"]["compute"] == valid_compute)
        ck("other tenants are untouched (lossless merge)", "demo" in saved["tenants"])
        # invalid medium rejected, not written
        before = p.read_text()
        bad = save_config({"tenant": "acme", "per_function": {"x": {"compute": "made_up_backend"}}}, config_path=p)
        ck("an unknown medium id is REJECTED (never written)", bad["saved"] is False and bad["errors"] and p.read_text() == before)
        ck("the handler class builds (serve path available)", _handler().__name__ == "H")
    print("\n" + ("PASS - config_ui_server: the config UI can SAVE per-function medium selections (POST /save) with "
                  "live-registry validation (unknown mediums rejected) and a lossless merge; secrets stay SecretRefs in "
                  ".env. Run --serve to use it."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    if "--serve" in argv:
        from http.server import ThreadingHTTPServer
        port = next((int(a) for a in argv if a.isdigit()), 8765)
        srv = ThreadingHTTPServer(("127.0.0.1", port), _handler())
        print(f"config UI on http://127.0.0.1:{port}  (GET / · POST /save · GET /config)")
        srv.serve_forever()
        return 0
    print("usage: config_ui_server.py --self-test | --serve [port]")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
