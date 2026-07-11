#!/usr/bin/env python3
"""scripts.run_browser_fixture_lab — a LOCAL, OFFLINE, stdlib-only fixture lab: a tiny ``http.server`` that serves
the web surfaces a browser/scraping tool must handle, so browser-control tooling can be probed WITHOUT touching the
public internet (no network egress, no third-party site, no robots/rate-limit concern, no PII). It is the
deterministic target that the capability probe (``scripts.probe_browser_control_tools``) drives to produce
EVIDENCE instead of assertions.

On the one page ``/`` it serves everything a scraper/browser must cope with:
  - static, server-rendered TEXT + a data TABLE (exactly what a raw-HTTP fetch sees, no JS),
  - a FORM: a text field + a hidden field + a **no-op** submit button + a button that ``window.open()``\\s a popup,
  - a link to a downloadable ``.txt``,
  - JS-RENDERED content (a ``<div>`` filled by an inline ``<script>`` — INVISIBLE to a static fetch, VISIBLE only to
    a real browser), which is the single cleanest discriminator between "raw HTTP" and "renders JS",
  - a DELAYED element (``setTimeout``) — the discriminator for "waits for late render",
  - a simulated ERROR banner.
And these mock endpoints for the API-first discovery lane:
  ``/api/items`` (JSON) · ``/openapi.json`` (a valid OpenAPI 3 doc, 2 paths) · ``/graphql`` (SDL on GET, an
  introspection stub on POST) · ``/download/sample.txt`` · ``/robots.txt`` · ``/sitemap.xml``.

It is dependency-free ON PURPOSE (stdlib ``http.server`` only) so it is the reliable offline anchor of the probe's
``--self-test``. NOTHING here mutates real state: the POST endpoints (``/submitted``, ``/graphql``) are harmless
no-ops, and the probe never submits the form for real anyway.

    python3 scripts/run_browser_fixture_lab.py --serve --port 8917   # blocking; open http://127.0.0.1:8917/ in a browser
    python3 scripts/run_browser_fixture_lab.py --self-test           # offline, in-thread, deterministic
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import urlparse

# ── content markers (SINGLE SOURCE — the probe imports these to assert render-vs-static, never re-types the literal)
STATIC_TEXT_MARKER = "FIXTURE_STATIC_TEXT_MARKER"          # present in the RAW html (a static fetch sees it)
JS_RENDERED_MARKER = "JS_RENDERED_CONTENT_OK"              # written by inline JS — ONLY a JS-rendering browser sees it
DELAYED_MARKER = "DELAYED_ELEMENT_APPEARED"               # written by setTimeout — needs "wait for render"
ERROR_BANNER_MARKER = "SIMULATED_ERROR_BANNER"            # a mock error surface a scraper must recognise, not crash on
PENDING_JS_PLACEHOLDER = "PENDING_JAVASCRIPT_RENDER"     # what the js div holds in RAW html (before JS runs)
PENDING_DELAY_PLACEHOLDER = "PENDING_DELAYED_ELEMENT"    # what the delayed div holds in RAW html
DELAYED_MS = 600                                          # setTimeout delay (ms) for the late element
TABLE_ID = "capability-table"
FORM_ID = "demo-form"
DOWNLOAD_PATH = "/download/sample.txt"
DOWNLOAD_BODY = ("sample fixture download\nline-2 alpha\nline-3 beta\nline-4 gamma\n"
                 "this is a fake, harmless .txt served so a scraper can exercise file downloads offline.\n")


def _home_html() -> str:
    """The single fixture page — carries every surface listed in the module docstring. Kept as one f-string so the
    markers above are the only source of the literals a probe checks."""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Browser Control Fixture Lab</title>
  <meta name="description" content="Offline fixture page for probing browser/scraping tooling.">
</head>
<body>
  <header><h1>Browser Control Fixture Lab</h1></header>

  <section id="static-text">
    <p>{STATIC_TEXT_MARKER}: this paragraph is server-rendered plain text — a raw HTTP fetch reads it with no
       browser. Readable-text extraction and BM25/keyword scraping operate on exactly this.</p>
  </section>

  <section id="data">
    <h2>Server-rendered data table</h2>
    <table id="{TABLE_ID}" border="1">
      <thead><tr><th>id</th><th>name</th><th>status</th></tr></thead>
      <tbody>
        <tr><td>1</td><td>alpha</td><td>active</td></tr>
        <tr><td>2</td><td>beta</td><td>pending</td></tr>
        <tr><td>3</td><td>gamma</td><td>retired</td></tr>
      </tbody>
    </table>
  </section>

  <section id="interactive">
    <h2>Form (read-only probe target — never submitted for real)</h2>
    <form id="{FORM_ID}" action="/submitted" method="post">
      <label>Query <input type="text" name="query" id="query-field" placeholder="type a query"></label>
      <input type="hidden" name="csrf_token" id="csrf-field" value="fixture-fixed-token">
      <button type="submit" id="submit-btn">Submit</button>
      <button type="button" id="popup-btn"
              onclick="window.open('/popup','fixture_popup','width=420,height=320')">Open popup window</button>
    </form>
  </section>

  <section id="resources">
    <h2>Links</h2>
    <a id="download-link" href="{DOWNLOAD_PATH}" download>Download sample.txt</a> ·
    <a id="openapi-link" href="/openapi.json">OpenAPI spec</a> ·
    <a id="graphql-link" href="/graphql">GraphQL endpoint</a> ·
    <a id="api-link" href="/api/items">JSON API</a>
  </section>

  <section id="dynamic">
    <h2>Dynamic content</h2>
    <div id="js-rendered">{PENDING_JS_PLACEHOLDER}</div>
    <div id="delayed-content">{PENDING_DELAY_PLACEHOLDER}</div>
    <div id="error-banner" role="alert" style="display:none"></div>
  </section>

  <script>
    // synchronous: a JS-rendering browser replaces the placeholder immediately; a raw fetch never runs this.
    document.getElementById('js-rendered').textContent = '{JS_RENDERED_MARKER}';
    // a mock error banner a scraper must recognise (and not treat as a crash)
    (function () {{
      var e = document.getElementById('error-banner');
      if (e) {{ e.style.display = 'block'; e.textContent = '{ERROR_BANNER_MARKER}: mock failure — HTTP 500 (simulated)'; }}
    }})();
    // late render: only a tool that WAITS for the DOM to settle sees this
    setTimeout(function () {{
      var d = document.getElementById('delayed-content');
      if (d) d.textContent = '{DELAYED_MARKER}';
    }}, {DELAYED_MS});
  </script>
</body>
</html>"""


_POPUP_HTML = ("<!doctype html><html><head><title>Fixture Popup</title></head>"
               "<body><h1>FIXTURE_POPUP_WINDOW</h1><p>Opened via window.open() — proves tab/popup creation.</p>"
               "</body></html>")
_PRIVATE_HTML = ("<!doctype html><html><head><title>Private</title></head>"
                 "<body><p>ROBOTS_DISALLOWED_AREA — a well-behaved crawler must not fetch this (see /robots.txt).</p>"
                 "</body></html>")


def _openapi_doc(base_url: str) -> dict:
    """A minimal but structurally VALID OpenAPI 3.0 document with 2 paths (the api-discovery lane parses this)."""
    return {
        "openapi": "3.0.3",
        "info": {"title": "Fixture Lab API", "version": "1.0.0",
                 "description": "Offline mock API for exercising OpenAPI discovery."},
        "servers": [{"url": base_url}],
        "paths": {
            "/api/items": {
                "get": {"operationId": "listItems", "summary": "List fixture items",
                        "responses": {"200": {"description": "an array of items"}}}
            },
            "/api/items/{itemId}": {
                "get": {"operationId": "getItem", "summary": "Get one item",
                        "parameters": [{"name": "itemId", "in": "path", "required": True,
                                        "schema": {"type": "integer"}}],
                        "responses": {"200": {"description": "one item"}, "404": {"description": "not found"}}}
            },
        },
    }


_GRAPHQL_SDL = ("type Query {\n  items: [Item!]!\n  item(id: ID!): Item\n}\n\n"
                "type Item {\n  id: ID!\n  name: String!\n  status: String\n}\n")


def _graphql_introspection_stub() -> dict:
    """A tiny introspection response — enough for a GraphQL detector/parser to confirm the endpoint + read the root."""
    return {"data": {"__schema": {
        "queryType": {"name": "Query"},
        "mutationType": None,
        "types": [
            {"kind": "OBJECT", "name": "Query", "fields": [
                {"name": "items", "type": {"kind": "LIST", "name": None}},
                {"name": "item", "type": {"kind": "OBJECT", "name": "Item"}}]},
            {"kind": "OBJECT", "name": "Item", "fields": [
                {"name": "id", "type": {"kind": "SCALAR", "name": "ID"}},
                {"name": "name", "type": {"kind": "SCALAR", "name": "String"}},
                {"name": "status", "type": {"kind": "SCALAR", "name": "String"}}]},
        ],
    }}}


_API_ITEMS = {"items": [{"id": 1, "name": "alpha", "status": "active"},
                        {"id": 2, "name": "beta", "status": "pending"},
                        {"id": 3, "name": "gamma", "status": "retired"}],
              "count": 3}


class _FixtureHandler(BaseHTTPRequestHandler):
    """Read-only fixture routes. GET serves every surface; POST endpoints are harmless no-ops."""

    server_version = "FixtureLab/1.0"
    protocol_version = "HTTP/1.1"  # keep-alive so a browser can pull sub-resources on one connection

    # silence the default stderr access log so --self-test / the probe stay clean
    def log_message(self, *_a) -> None:  # noqa: D401
        return

    def _base_url(self) -> str:
        return f"http://{self.headers.get('Host') or self.server.server_address[0]}"

    def _send(self, status: int, content_type: str, body: bytes, extra: Optional[dict] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _text(self, status: int, ctype: str, text: str, extra: Optional[dict] = None) -> None:
        self._send(status, ctype, text.encode("utf-8"), extra)

    def _json(self, obj: object, status: int = 200) -> None:
        self._send(status, "application/json; charset=utf-8",
                   json.dumps(obj, indent=2, sort_keys=True).encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802 (http.server API)
        path = urlparse(self.path).path
        base = self._base_url()
        if path in ("/", "/index.html"):
            self._text(200, "text/html; charset=utf-8", _home_html())
        elif path == "/popup":
            self._text(200, "text/html; charset=utf-8", _POPUP_HTML)
        elif path == "/private":
            self._text(200, "text/html; charset=utf-8", _PRIVATE_HTML)
        elif path == "/api/items":
            self._json(_API_ITEMS)
        elif path == "/openapi.json":
            self._json(_openapi_doc(base))
        elif path == "/graphql":
            self._text(200, "application/graphql; charset=utf-8", _GRAPHQL_SDL)
        elif path == DOWNLOAD_PATH:
            self._text(200, "text/plain; charset=utf-8", DOWNLOAD_BODY,
                       extra={"Content-Disposition": 'attachment; filename="sample.txt"'})
        elif path == "/robots.txt":
            self._text(200, "text/plain; charset=utf-8",
                       f"User-agent: *\nAllow: /\nDisallow: /private\nSitemap: {base}/sitemap.xml\n")
        elif path == "/sitemap.xml":
            self._text(200, "application/xml; charset=utf-8",
                       ('<?xml version="1.0" encoding="UTF-8"?>\n'
                        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                        f'  <url><loc>{base}/</loc></url>\n'
                        f'  <url><loc>{base}/api/items</loc></url>\n'
                        '</urlset>\n'))
        elif path == "/favicon.ico":
            self._send(204, "image/x-icon", b"")
        else:
            self._text(404, "text/html; charset=utf-8", "<h1>404 fixture route not found</h1>")

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        # drain the request body (harmless) so keep-alive stays in sync
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            try:
                self.rfile.read(length)
            except Exception:  # noqa: BLE001
                pass
        if path == "/graphql":
            self._json(_graphql_introspection_stub())
        elif path == "/submitted":
            # NO-OP acknowledgment: the harness/probe never submit for real; if hit, nothing is mutated.
            self._text(200, "text/html; charset=utf-8",
                       "<h1>FORM_RECEIVED_NOOP</h1><p>Fixture no-op — no state was changed.</p>")
        else:
            self._text(404, "text/html; charset=utf-8", "<h1>404 fixture route not found</h1>")


def serve_in_thread(port: int = 0, host: str = "127.0.0.1") -> "tuple[ThreadingHTTPServer, str]":
    """Start the fixture lab in a daemon thread and return ``(httpd, base_url)``.

    ``port=0`` binds an ephemeral OS-assigned port (the deterministic-offline choice for tests). Stop it with
    ``httpd.shutdown(); httpd.server_close()``.
    """
    httpd = ThreadingHTTPServer((host, port), _FixtureHandler)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, name="fixture-lab", daemon=True)
    thread.start()
    return httpd, f"http://{host}:{actual_port}"


def _fetch(url: str, timeout: float = 5.0) -> "tuple[int, str]":
    """Offline GET → (status_code, text). Local loopback only."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:  # noqa: S310 (loopback fixture only)
            return resp.getcode(), resp.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as http_err:          # a 4xx/5xx IS the answer — keep the status, don't zero it
        try:
            return http_err.code, http_err.read().decode("utf-8", "ignore")
        except Exception:  # noqa: BLE001
            return http_err.code, ""
    except Exception as exc:  # noqa: BLE001
        return 0, f"{type(exc).__name__}: {exc}"


def self_test() -> int:
    """Start on an ephemeral port in-thread, fetch key routes offline, assert content, shut down. Deterministic.

    MUTATION-GATED: each check asserts real served content, so breaking a route/marker turns it red."""
    checks: list[tuple[str, bool]] = []
    httpd, url = serve_in_thread(0)
    try:
        code_home, home = _fetch(url + "/")
        checks.append(("GET / -> 200", code_home == 200))
        checks.append(("home carries static text + table + form (raw, no JS run)",
                       STATIC_TEXT_MARKER in home and f'id="{TABLE_ID}"' in home
                       and f'id="{FORM_ID}"' in home and 'type="hidden"' in home))
        checks.append(("home exposes the JS/delayed placeholders in RAW html (a static fetch does NOT run JS)",
                       PENDING_JS_PLACEHOLDER in home and JS_RENDERED_MARKER not in home.split("<script>")[0]))
        checks.append(("home has popup button (window.open) + download/openapi/graphql links",
                       "window.open(" in home and DOWNLOAD_PATH in home
                       and "/openapi.json" in home and "/graphql" in home))

        code_oa, oa = _fetch(url + "/openapi.json")
        try:
            oa_doc = json.loads(oa)
        except Exception:  # noqa: BLE001
            oa_doc = {}
        checks.append(("GET /openapi.json -> 200 valid OpenAPI 3 with >=2 paths",
                       code_oa == 200 and str(oa_doc.get("openapi", "")).startswith("3.")
                       and len(oa_doc.get("paths", {})) >= 2))

        code_items, items = _fetch(url + "/api/items")
        checks.append(("GET /api/items -> 200 JSON list", code_items == 200 and '"items"' in items))

        code_gql, gql = _fetch(url + "/graphql")
        checks.append(("GET /graphql -> 200 SDL (type Query)", code_gql == 200 and "type Query" in gql))

        code_robots, robots = _fetch(url + "/robots.txt")
        checks.append(("GET /robots.txt -> 200 with Sitemap + Disallow",
                       code_robots == 200 and "Sitemap:" in robots and "Disallow: /private" in robots))

        code_dl, dl = _fetch(url + DOWNLOAD_PATH)
        checks.append(("GET download/sample.txt -> 200 text body", code_dl == 200 and "sample fixture download" in dl))

        code_404, _ = _fetch(url + "/no-such-route")
        checks.append(("unknown route -> 404", code_404 == 404))
    finally:
        httpd.shutdown()
        httpd.server_close()

    ok = all(v for _, v in checks)
    for name, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {name}")
    print(("PASS" if ok else "FAIL") + " - run_browser_fixture_lab: offline stdlib fixture lab (static text/table/"
          "form/popup/download + JS-rendered/delayed/error surfaces + /api/items /openapi.json /graphql /robots.txt "
          "/sitemap.xml), served in-thread on an ephemeral port; deterministic, no network.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Local offline stdlib fixture lab for browser/scraping capability probes.")
    ap.add_argument("--serve", action="store_true", help="serve blocking (Ctrl-C to stop)")
    ap.add_argument("--port", type=int, default=8917, help="port for --serve (default 8917; 0 = ephemeral)")
    ap.add_argument("--self-test", action="store_true", help="offline in-thread self-test")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.serve:
        httpd, url = serve_in_thread(args.port)
        print(f"fixture lab serving at {url}/  (routes: / /popup /api/items /openapi.json /graphql "
              f"{DOWNLOAD_PATH} /robots.txt /sitemap.xml) — Ctrl-C to stop")
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            print("\nstopping fixture lab")
        finally:
            httpd.shutdown()
            httpd.server_close()
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
