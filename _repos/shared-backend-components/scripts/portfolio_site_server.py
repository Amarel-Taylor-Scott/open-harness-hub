#!/usr/bin/env python3
"""scripts.portfolio_site_server — one launch site's LOCAL per-port server.

Serves dist/portfolio-public/<site>/ at the root and 302-redirects hub-rooted site paths
(/baltor/…, /aidoneright/…) to that site's OWN port — the local equivalent of how the deployed
sites cross-link by domain. Fixes the E2E crawler finding that sibling links 404 on per-port
servers while resolving on the hub (the generated pages link hub-rooted). Used by
_repos/shared-backend-components/scripts/serve_portfolio_sites.py for every per-site process; the hub (9100) still serves the
whole tree directly. Stdlib-only; exact-pid lifecycle is owned by the caller.
"""
from __future__ import annotations

import http.server
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import json  # noqa: E402

from scripts import portfolio_lib as P  # noqa: E402
from scripts.byo_demo_server import _page as _byo_page  # noqa: E402  (reuse the ONE per-surface demo renderer)
from src.teleon.demos.byo_key_demo import run_byo_demo  # noqa: E402

# every site slug (including the served site itself) → its port; a hub-rooted path like
# /<slug>/rest redirects to http://127.0.0.1:<port>/rest (self-prefix included: not a loop,
# because the slug is stripped before redirecting)
_SITE_PORTS = {sid: P.PORTS[sid] for sid in P.SITE_ORDER}

# Each surface serves its OWN /demo (owner 2026-06-25: demos are /demo PAGES on the main surfaces, NOT a
# separate demo website). Map the portfolio site slug → its BYO-key demo surface; the parent (aidoneright)
# lists every surface's /demo. /run is the same-origin POST the demo page calls.
_DEMO_SURFACE = {"teleon.dev": "teleon", "baltor": "baltor", "opencontexthub": "open-star-hubs",
                 "openskillshub": "open-star-hubs", "opentoolshub": "open-star-hubs",
                 "openhubforai": "open-star-hubs"}


def main(site: str, port: int | None = None) -> None:
    bind_port = port or P.PORTS[site]
    root = P.DIST / site

    surface = _DEMO_SURFACE.get(site)  # this site's /demo surface (None for the parent → a demo index)

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def _send(self, code: int, body: str, ctype: str = "text/html; charset=utf-8") -> None:
            b = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):  # noqa: N802 — /demo is a PAGE on this surface (not a separate site)
            if self.path.split("?")[0].rstrip("/") == "/demo":
                if surface:
                    self._send(200, _byo_page(surface))  # this surface's own BYO-key demo, same origin
                else:  # parent: link every surface's own /demo (the redirect resolves /<slug>/demo → its port)
                    links = "".join(f'<li><a href="/{s}/demo">{s}</a></li>' for s in _DEMO_SURFACE)
                    self._send(200, "<!doctype html><meta charset=utf-8><title>Demos — one per surface</title>"
                               "<style>body{font-family:system-ui;background:#0b0e14;color:#e6edf3;padding:2rem}"
                               "a{color:#6d5ef0}</style><h1>Demos — one <code>/demo</code> per surface</h1>"
                               f"<ul>{links}</ul>")
                return
            super().do_GET()

        def do_POST(self):  # noqa: N802 — the same-origin BYO run endpoint the /demo page calls
            if self.path.split("?")[0] != "/run":
                self._send(404, "not found")
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(n) or b"{}")
                out = run_byo_demo(req.get("demo", ""), byo_key=req.get("byo_key") or None,
                                   inputs=req.get("inputs") or {})
            except Exception as e:  # noqa: BLE001
                out = {"ok": False, "error": str(e)}
            self._send(200, json.dumps(out), "application/json")

        def send_head(self):  # noqa: N802 (http.server API)
            head, _, rest = self.path.lstrip("/").partition("/")
            if head in _SITE_PORTS:
                self.send_response(302)
                self.send_header("Location", f"http://127.0.0.1:{_SITE_PORTS[head]}/{rest}")
                self.end_headers()
                return None
            return super().send_head()

        def log_message(self, fmt, *args):  # caller owns the log file; keep stderr quiet
            pass

    http.server.ThreadingHTTPServer(("127.0.0.1", bind_port), Handler).serve_forever()


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in P.SITE_ORDER:
        print(f"usage: python3 -m scripts.portfolio_site_server <site> [port]; sites: {P.SITE_ORDER}")
        raise SystemExit(2)
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else None)
