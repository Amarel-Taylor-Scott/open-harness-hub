"""HTTP server for the paste-to-flow showcase (zero-dependency stdlib)."""
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from pathlib import Path

from scripts.model_routes import resolve_route
from scripts.primitives import label_for_type
from scripts.showcase.builder import build_flow
from scripts.showcase.export import export_flow
from scripts.showcase.index import Index
from scripts.showcase.pages import BROWSE_HTML, HTML

# The product front-end (the Claude Design handoff implementation). Served at root;
# the classic paste-to-flow UI stays reachable at /classic. See web/README.md.
# A server instance serves ONE product's FRONT-END folder (web/<product>/). The front-end is fully
# per-product; only the BACKEND (/api/*, the engine, the catalog) is shared. OH_PRODUCT picks the
# folder (default harness-hub). See docs/strategy/two-services-shared-infrastructure.md.
OH_PRODUCT = os.environ.get("OH_PRODUCT", "").strip() or "harness-hub"
WEB_DIR = Path(__file__).resolve().parents[2] / "web" / OH_PRODUCT
_STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json",
                 ".png": "image/png", ".woff2": "font/woff2", ".ico": "image/x-icon", ".map": "application/json"}


class Handler(BaseHTTPRequestHandler):
    index: Index = None  # type: ignore
    token: str = ""  # if set, the compute endpoints require it (?token= or X-OHH-Token header)

    def _authed(self, parsed) -> bool:
        if not self.token:
            return True
        supplied = (parse_qs(parsed.query).get("token") or [None])[0] or self.headers.get("X-OHH-Token")
        return supplied == self.token

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        # fast-iterating demo: never let the browser serve a stale app.js/data.js/page bundle
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(body)

    def _serve_static(self, rel: str) -> bool:
        """Serve a file from web/ (the product front-end). Returns False if missing/unsafe."""
        base = WEB_DIR.resolve()
        target = (base / rel.lstrip("/")).resolve()
        if not (target == base or base in target.parents) or not target.is_file():
            return False
        self._send(200, target.read_bytes(), _STATIC_TYPES.get(target.suffix, "application/octet-stream"))
        return True

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            if self._serve_static("index.html"):
                return
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")  # fallback if web/ absent
        elif parsed.path in ("/app.js", "/data.js") or parsed.path.startswith("/styles/") or parsed.path.startswith("/pages/"):
            if not self._serve_static(parsed.path):
                self._send(404, b"not found", "text/plain")
        elif parsed.path == "/classic":
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")  # the classic paste-to-flow UI
        elif parsed.path == "/api/health":
            route = resolve_route()
            payload = {"embedding": self.index.backend.provenance(),
                       "components": len(self.index.items),
                       "llm": route.summary(), "llm_reachable": route.health()}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif parsed.path == "/api/build":
            if not self._authed(parsed):
                self._send(401, b'{"error":"token required"}', "application/json")
                return
            qs = parse_qs(parsed.query)
            task = (qs.get("task") or [""])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            narrate = (qs.get("narrate") or ["1"])[0] != "0"   # preview passes narrate=0 → skip the prose LLM call
            self._send(200, json.dumps(build_flow(task, self.index, narrate=narrate)).encode(), "application/json")
        elif parsed.path == "/api/export":
            if not self._authed(parsed):
                self._send(401, b'{"error":"token required"}', "application/json")
                return
            qs = parse_qs(parsed.query)
            task = (qs.get("task") or [""])[0]
            fmt = (qs.get("format") or ["yaml"])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            spec = export_flow(build_flow(task, self.index))
            slug = spec["id"].split("/")[-1]
            if fmt == "json":
                self._send(200, json.dumps(spec, indent=2).encode(), "application/json")
            else:
                import yaml as _yaml
                body = _yaml.safe_dump(spec, sort_keys=False, allow_unicode=True).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/yaml; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="{slug}.yaml"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        elif parsed.path == "/browse":
            self._send(200, BROWSE_HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif parsed.path == "/api/components":
            qs = parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0].lower()
            typ = (qs.get("type") or [""])[0]
            limit = int((qs.get("limit") or ["300"])[0])
            items = self.index.items
            res = [{"id": it["id"], "type": it["type"], "label": label_for_type(it["type"]),
                    "name": it["name"], "desc": it["desc"][:160]}
                   for it in items
                   if (not typ or it["type"] == typ)
                   and (not q or q in it["name"].lower() or q in it["id"].lower() or q in it["desc"].lower())]
            counts = dict(sorted(Counter(i["type"] for i in items).items()))
            payload = {"total": len(items), "by_type": counts,
                       "labels": {t: label_for_type(t) for t in counts},
                       "matched": len(res), "results": res[:limit]}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif parsed.path == "/api/primitives":
            from scripts.primitives import PRIMITIVE_CLASSES

            def _subs(c) -> list[str]:
                ns = getattr(c, "node_subtypes", None)  # display-only node subtypes (e.g. Conditional)
                if ns:
                    return list(ns)
                s = getattr(c, "subtypes", None)
                if isinstance(s, dict):
                    return list(s.keys())
                if isinstance(s, (list, tuple)):
                    return list(s)
                return []

            payload = [{"kind": c.kind, "label": getattr(c, "label", c.kind),
                        "stage": getattr(c, "stage", ""), "description": getattr(c, "description", ""),
                        "subtypes": _subs(c), "schema_types": list(getattr(c, "schema_types", ()))}
                       for c in PRIMITIVE_CLASSES]
            self._send(200, json.dumps(payload).encode(), "application/json")
        else:
            self._send(404, b"not found", "text/plain")

    def log_message(self, *args) -> None:  # quiet
        pass


def serve(port: int = 8000) -> None:
    Handler.index = Index()
    Handler.token = os.environ.get("OH_SHOWCASE_TOKEN", "")
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    gate = "token-gated" if Handler.token else "OPEN (set OH_SHOWCASE_TOKEN to gate)"
    print(f"Open Harness Hub showcase → http://127.0.0.1:{port}  "
          f"({len(Handler.index.items)} components, embeddings={Handler.index.backend.name}, "
          f"promotable={Handler.index.backend.promotable}, /api/build {gate})")
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def _self_test() -> int:
    idx = Index()
    assert idx.items, "no components loaded"
    res = build_flow("screen supplier disclosures for forced labor and cite regulations", idx)
    assert res["flow"]["steps"], "empty flow"
    assert res["cost"]["balanced"]["per_task_usd"]
    spec = export_flow(res)
    assert spec["type"] == "pipeline" and spec["steps"], "export produced no pipeline"
    print(json.dumps({
        "ok": True, "components": len(idx.items),
        "embedding_backend": idx.backend.name, "promotable": idx.backend.promotable,
        "selection_by_model": res["selection_by_model"], "llm_used": res["llm_used"],
        "stages": [s["stage"] for s in res["flow"]["stages"]],
        "kept": [f"{s['type']}/{s['id'].split('/')[-1]}" for s in res["flow"]["steps"]],
        "export_steps": len(spec["steps"]),
    }, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Local paste-to-flow showcase site.")
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    serve(args.port)
    return 0
