#!/usr/bin/env python3
"""scripts.portfolio_site_server — one launch site's LOCAL per-port server.

Serves dist/portfolio-public/<site>/ at the root and 302-redirects hub-rooted site paths
(/baltor/…, /aidoneright/…) to that site's OWN port — the local equivalent of how the deployed
sites cross-link by domain. Fixes the E2E crawler finding that sibling links 404 on per-port
servers while resolving on the hub (the generated pages link hub-rooted). Used by
scripts/serve_portfolio_sites.py for every per-site process; the hub (9100) still serves the
whole tree directly. Stdlib-only; exact-pid lifecycle is owned by the caller.
"""
from __future__ import annotations

import http.server
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P  # noqa: E402

# every site slug (including the served site itself) → its port; a hub-rooted path like
# /<slug>/rest redirects to http://127.0.0.1:<port>/rest (self-prefix included: not a loop,
# because the slug is stripped before redirecting)
_SITE_PORTS = {sid: P.PORTS[sid] for sid in P.SITE_ORDER}


def main(site: str, port: int | None = None) -> None:
    bind_port = port or P.PORTS[site]
    root = P.DIST / site

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

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
