"""HTTP server for the paste-to-flow showcase (zero-dependency stdlib)."""
from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlparse

from pathlib import Path

from scripts.model_routes import resolve_route
from scripts.primitives import label_for_type
from scripts.showcase.admin_demo.routes import handle_admin_demo_get, handle_admin_demo_post
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
_REPO_DIR = Path(__file__).resolve().parents[2]
WEB_DIR = _REPO_DIR / "web" / OH_PRODUCT
ADMIN_DEMO_WEB_DIR = _REPO_DIR / "web" / "harness-hub"
# Shared pinned runtime (React/Babel UMD) for the full-design front-ends — one copy, every product.
VENDOR_DIR = _REPO_DIR / "web" / "vendor"
# Read-only mount of the design handoff bundle: every prototype surface (Demo Control Tower,
# Teleon, the 21 Open*Hubs, screens/) stays reachable from any product origin at /design/.
DESIGN_BUNDLE_DIR = _REPO_DIR / "dist" / "sites" / "openharness-design"
# The bundle's top-level folders are ALSO mounted at the origin root (/teleon/…, /opencontexthub/…,
# /shared/…). The full-design surfaces ported into web/ keep their cross-surface links VERBATIM
# (e.g. '../teleon/Teleon Prototype.html' in shared/products.js); resolved from '/', those links
# land on '/<bundle-folder>/…' and must serve the canonical prototype neighbors.
_BUNDLE_TOP_DIRS = (frozenset(p.name for p in DESIGN_BUNDLE_DIR.iterdir() if p.is_dir())
                    if DESIGN_BUNDLE_DIR.is_dir() else frozenset())
_ARCH_DIR = _REPO_DIR / "architecture"
_STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "application/javascript; charset=utf-8",
                 ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml", ".json": "application/json",
                 ".png": "image/png", ".woff2": "font/woff2", ".ico": "image/x-icon", ".map": "application/json",
                 ".md": "text/markdown; charset=utf-8", ".txt": "text/plain; charset=utf-8",
                 ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".webp": "image/webp"}

#: The shared pinned runtime files this server mounts at /vendor/ (web/vendor/). The design-bundle
#: prototypes load these from unpkg's CDN; we repoint them here so they load OFFLINE.
_VENDOR_RUNTIME_FILES = ("react.development.js", "react-dom.development.js", "babel.min.js")
_UNPKG_RE = re.compile(r'https://unpkg\.com/(?:@babel/standalone|react-dom|react)@[^/"\']+/(?:umd/)?([\w.-]+\.js)')
_FONT_LINK_RE = re.compile(r'<link\b[^>]*fonts\.g(?:oogleapis|static)\.com[^>]*>\s*')


def rewrite_bundle_html(html_text: str) -> str:
    """Make a design-bundle prototype load OFFLINE from the local /vendor/ mount instead of external
    CDNs (the cause of the blank cross-product screen a confused user hits, and a no-external-CDN
    violation). Repoint the pinned React/Babel runtime to /vendor/, drop the subresource integrity
    (the local copy hashes differently than unpkg's) + the now-orphaned crossorigin, and drop the
    Google-Fonts CDN links (the page degrades to its declared font stack — never blank)."""
    text = _UNPKG_RE.sub(r"/vendor/\1", html_text)
    text = re.sub(r'\s+integrity="[^"]*"', "", text)
    text = re.sub(r'\s+crossorigin(?:="[^"]*")?', "", text)
    text = _FONT_LINK_RE.sub("", text)
    return text


def _local_service_port(service_id: str) -> int | None:
    """Port for a local service from architecture/local_service_registry.json (the single source
    of local ports — see that file's port_sources). None → the seam stays disabled, honestly."""
    try:
        services = json.loads((_ARCH_DIR / "local_service_registry.json").read_text(encoding="utf-8"))["services"]
        for svc in services:
            if svc.get("service_id") == service_id and svc.get("port"):
                return int(svc["port"])
    except Exception:
        return None
    return None


def _identity_service_port() -> int | None:
    """Identity port from architecture/identity_realm_registry.json defaults (its single source)."""
    try:
        return int(json.loads((_ARCH_DIR / "identity_realm_registry.json").read_text(encoding="utf-8"))["defaults"]["port"])
    except Exception:
        return None


def _seam_base(env_key: str, port: int) -> str:
    """Seam target base URL. Default = the local plane (http://127.0.0.1:<port> with the port
    from the architecture registries); a non-empty OH_SEAM_*_BASE env overrides it for cloud
    deploys where peers live on other hosts (e.g. http://aidr-identity.internal:9410 on Fly,
    http://identity:9410 on K8s). This env seam is THE provider switch — same image everywhere,
    only these bases change (set by scripts/deploy/generate_provider_configs.py, never by hand)."""
    override = (os.environ.get(env_key) or "").strip().rstrip("/")
    return override if override else f"http://127.0.0.1:{port}"


def _seam_proxies() -> list[tuple[str, str, str]]:
    """Same-origin seams (url_prefix, strip_prefix, target_base) to the service plane.

    The full-design kit (web/<product>/kit/oh-identity.js, oh-registry.js) is pointed at these
    relative bases by the ported entry HTMLs, so identity/registry/analytics/live-ops calls work
    both on 127.0.0.1 and through a tunnel. Ports come from the architecture registries only;
    cloud deploys override the host via OH_SEAM_*_BASE (see _seam_base).
    """
    table: list[tuple[str, str, str]] = []
    identity = _identity_service_port()
    if identity:
        table.append(("/api/identity/", "", _seam_base("OH_SEAM_IDENTITY_BASE", identity)))
    registry = _local_service_port("local_openhub_projection_api")
    if registry:
        table.append(("/registry/", "/registry", _seam_base("OH_SEAM_REGISTRY_BASE", registry)))
    events = _local_service_port("local_event_tracking_service")
    if events:
        table.append(("/analytics/", "/analytics", _seam_base("OH_SEAM_ANALYTICS_BASE", events)))
    mailbox = _local_service_port("mailbox_local_service")
    if mailbox:  # the visible transactional-email inbox (registration → verify-email click, same-origin)
        mailbox_base = _seam_base("OH_SEAM_MAILBOX_BASE", mailbox)
        table.append(("/mailbox", "", mailbox_base))
        table.append(("/api/mailbox/", "", mailbox_base))
    teleon_runtime = _local_service_port("teleon_local_runtime")
    if teleon_runtime:
        table.append(("/api/teleon/", "", _seam_base("OH_SEAM_TELEON_RUNTIME_BASE", teleon_runtime)))
    live_ops = _local_service_port("baltor_admin_demo_server")
    if live_ops:
        live_ops_base = _seam_base("OH_SEAM_LIVEOPS_BASE", live_ops)
        # deep-dive 2026-06-11: memory/pipeline/determinism/runtime were served by the backend
        # but missing here — four shipped page families 404'd through the public origin
        for prefix in ("/api/demo/", "/api/context/", "/api/dev/", "/api/fleet",
                       "/api/admin-dashboard/", "/api/inference/", "/api/native/",
                       "/api/standards/", "/api/graph/", "/api/context-gateway/", "/api/events",
                       "/api/memory/", "/api/pipeline/", "/api/determinism/", "/api/runtime/"):
            table.append((prefix, "", live_ops_base))
    return table


_SEAM_PROXIES = _seam_proxies()

_GOVERNANCE_CACHE: dict[str, dict] | None = None
_GOVERNANCE_LOCK = __import__("threading").Lock()


def _governance_metadata() -> dict[str, dict]:
    """Real per-component governance fields from the catalog YAMLs (license, provenance,
    lifecycle, industry, modality), keyed by component id. Built once, lazily — the embedding
    store the Index reads doesn't carry these, and the front-end must never invent them.
    The build sweeps every catalog YAML (~30s pure-python / a few s with libyaml), so it runs
    under a lock and serve() pre-warms it on a background thread — the port binds immediately
    and concurrent requests wait on the one build instead of racing it."""
    global _GOVERNANCE_CACHE
    if _GOVERNANCE_CACHE is not None:
        return _GOVERNANCE_CACHE
    import yaml as _yaml
    loader = getattr(_yaml, "CSafeLoader", _yaml.SafeLoader)
    with _GOVERNANCE_LOCK:
        if _GOVERNANCE_CACHE is not None:  # built while we waited
            return _GOVERNANCE_CACHE
        out: dict[str, dict] = {}
        first = lambda v: (v[0] if isinstance(v, list) and v else v) or None  # noqa: E731
        for path in (_REPO_DIR / "catalog").rglob("*.yaml"):
            try:
                doc = _yaml.load(path.read_text(encoding="utf-8"), Loader=loader)
            except Exception:
                continue
            if not isinstance(doc, dict) or not doc.get("id"):
                continue
            prov = doc.get("provenance") or {}
            sources = prov.get("sources") if isinstance(prov, dict) else None
            meta = {
                "license": doc.get("license"),
                "lifecycle": doc.get("lifecycle"),
                "industry": first(doc.get("industry")),
                "modality": first(doc.get("modality")),
                # 'sourced' ONLY when the catalog actually records provenance sources
                "prov": "sourced" if sources else None,
                "src": (str(sources[0])[:60] if sources else None),
                "verified": (prov.get("collected_through") if isinstance(prov, dict) else None),
            }
            out[str(doc["id"])] = {k: v for k, v in meta.items() if v is not None}
        _GOVERNANCE_CACHE = out
        return out


def _seam_for(path: str) -> tuple[str, str] | None:
    """The (strip_prefix, base) seam owning this path, if any. A prefix without a trailing slash
    matches itself or nested paths; with a trailing slash it matches nested paths only."""
    for prefix, strip, base in _SEAM_PROXIES:
        if prefix.endswith("/"):
            if path.startswith(prefix):
                return strip, base
        elif path == prefix or path.startswith(prefix + "/"):
            return strip, base
    return None
_ADMIN_DEMO_VIEWS = {"sources", "monitoring", "outputs", "download", "explore", "testing"}
_ADMIN_DEMO_TITLES = {
    "sources": "Load data",
    "monitoring": "Processing",
    "outputs": "Outputs",
    "download": "Download",
    "explore": "Explore context",
    "testing": "Integration testing",
}


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

    def _serve_static_from(self, base_dir: Path, rel: str) -> bool:
        """Serve a file from a product front-end folder. Returns False if missing/unsafe."""
        base = base_dir.resolve()
        target = (base / rel.lstrip("/")).resolve()
        if not (target == base or base in target.parents) or not target.is_file():
            return False
        # Design-bundle prototypes (DESIGN_BUNDLE_DIR) load React/Babel/fonts from external CDNs, so
        # they go BLANK offline (the cross-product dead-end). Rewrite them on serve to the local
        # /vendor/ runtime this server already mounts.
        if target.suffix == ".html" and base == DESIGN_BUNDLE_DIR.resolve():
            body = rewrite_bundle_html(target.read_text(encoding="utf-8")).encode("utf-8")
        else:
            body = target.read_bytes()
        self._send(200, body, _STATIC_TYPES.get(target.suffix, "application/octet-stream"))
        return True

    def _serve_static(self, rel: str) -> bool:
        """Serve a file from the active product front-end."""
        return self._serve_static_from(WEB_DIR, rel)

    def _proxy_seam(self, parsed, strip: str, base: str) -> None:
        """Forward this request to a service-plane peer (same-origin seam; base from the
        architecture registries locally, OH_SEAM_*_BASE in cloud deploys).

        When the backing service is down we answer an honest 502 — the full-design kit treats
        that as service-unavailable and falls back to its in-file design data, never
        fabricating state.
        """
        rel = parsed.path[len(strip):] if strip and parsed.path.startswith(strip) else parsed.path
        target = f"{base}{rel}" + (f"?{parsed.query}" if parsed.query else "")
        body = None
        if self.command == "POST":
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
        req = urllib.request.Request(target, data=body, method=self.command)
        for header in ("Content-Type", "X-AIDR-Request-Id"):
            if self.headers.get(header):
                req.add_header(header, self.headers[header])
        try:
            # generous: model-built runs (Teleon) and LLM-selected builds legitimately take
            # minutes on a local CPU route; the seam must outlive them
            with urllib.request.urlopen(req, timeout=360) as resp:
                ctype = resp.headers.get("Content-Type") or "application/json"
                if "text/event-stream" in ctype:
                    # SSE pass-through: stream chunks until either side disconnects, so live
                    # dashboards get real-time events through this origin (and tunnels) too
                    self.send_response(resp.status)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    try:
                        while True:
                            chunk = resp.read1(8192)
                            if not chunk:
                                break
                            self.wfile.write(chunk)
                            self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    return
                self._send(resp.status, resp.read(), ctype)
        except urllib.error.HTTPError as exc:  # backend answered — pass its status/body through honestly
            self._send(exc.code, exc.read(), exc.headers.get("Content-Type") or "application/json")
        except Exception:
            self._send(502, json.dumps({
                "error": "local service unreachable", "target": base,
                "hint": "python3 scripts/start_local_services.py",
            }).encode(), "application/json")

    def _serve_admin_demo_static(self, rel: str) -> bool:
        """Serve the Baltor context-control demo from its canonical front-end bundle.

        The demo currently lives under web/harness-hub because it was first built
        with that static shell, but product-wise it is Baltor's backbone. Serving
        it from a fixed bundle keeps /admin-demo available on all three product
        servers while the front-end folders are being consolidated.
        """
        return self._serve_static_from(ADMIN_DEMO_WEB_DIR, rel)

    def _serve_admin_demo_page(self, path: str) -> bool:
        """Serve an admin-demo route with its section visible before JS hydration."""
        target = (ADMIN_DEMO_WEB_DIR / "admin-demo.html").resolve()
        if not target.is_file():
            return False
        view = "home"
        parts = [part for part in path.split("/") if part]
        if len(parts) >= 2 and parts[0] == "admin-demo" and parts[1] in _ADMIN_DEMO_VIEWS:
            view = parts[1]
        html = target.read_text(encoding="utf-8")
        if view != "home":
            return self._send_admin_demo_section(html, view)
        html = html.replace('data-admin-view="home"', f'data-admin-view="{view}"', 1)
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
        return True

    def _send_admin_demo_section(self, html: str, view: str) -> bool:
        marker = f'data-view-section="{view}"'
        marker_pos = html.find(marker)
        if marker_pos == -1:
            return False
        section_start = html.rfind("    <section", 0, marker_pos)
        section_end = html.find("\n\n    <section", marker_pos)
        if section_end == -1:
            section_end = html.find("\n  </main>", marker_pos)
        if section_start == -1 or section_end == -1:
            return False
        section = html[section_start:section_end]
        section = section.replace(" hidden", "")
        head = html[html.find("<head>") + len("<head>"):html.find("</head>")]
        topbar = html[html.find("  <header"):html.find("\n\n  <main")]
        body = (
            "<!doctype html>\n<html lang=\"en\">\n<head>"
            + head.replace("Baltor | Context Control Demo", f"Baltor | {_ADMIN_DEMO_TITLES.get(view, view)}")
            + "<style>body.admin-demo [data-view-section]{display:grid!important;visibility:visible!important;opacity:1!important;}"
            + ".ad-shell{display:block!important;min-height:auto!important;}"
            + "</style>\n</head>\n"
            + f"<body class=\"admin-demo\" data-admin-view=\"{view}\">\n"
            + topbar
            + "\n\n  <main class=\"ad-shell\">\n"
            + section
            + "\n  </main>\n"
            + "</body>\n</html>\n"
        )
        self._send(200, body.encode("utf-8"), "text/html; charset=utf-8")
        return True

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            if self._serve_static("index.html"):
                return
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")  # fallback if web/ absent
        elif parsed.path.startswith("/vendor/"):
            # shared pinned React/Babel runtime for the full-design front-ends (web/vendor/README.md)
            if not self._serve_static_from(VENDOR_DIR, unquote(parsed.path[len("/vendor/"):])):
                self._send(404, b"not found", "text/plain")
        elif parsed.path in ("/design", "/design/"):
            if not self._serve_static_from(DESIGN_BUNDLE_DIR, "index.html"):
                self._send(404, b"not found", "text/plain")
        elif parsed.path.startswith("/design/"):
            # read-only mount of the design handoff bundle (prototype surfaces keep their
            # space-containing filenames, hence the unquote)
            if not self._serve_static_from(DESIGN_BUNDLE_DIR, unquote(parsed.path[len("/design/"):])):
                self._send(404, b"not found", "text/plain")
        elif parsed.path.split("/", 2)[1] in _BUNDLE_TOP_DIRS:
            # root mounts of the bundle's folders, so verbatim '../<sibling>/…' cross-surface
            # links inside the ported full-design apps resolve to the canonical prototypes
            if not self._serve_static_from(DESIGN_BUNDLE_DIR, unquote(parsed.path.lstrip("/"))):
                self._send(404, b"not found", "text/plain")
        elif parsed.path == "/admin-demo" or parsed.path.startswith("/admin-demo/"):
            if not self._serve_admin_demo_page(parsed.path):
                self._send(404, b"not found", "text/plain")
        elif parsed.path == "/admin-demo.js" or parsed.path.startswith("/admin-demo-assets/"):
            if not self._serve_admin_demo_static(parsed.path):
                self._send(404, b"not found", "text/plain")
        elif parsed.path.startswith("/styles/") and parsed.path in (
            "/styles/admin-demo.css",
            "/styles/oh-tokens.css",
            "/styles/oh-components.css",
        ):
            if not (self._serve_static(parsed.path) or self._serve_admin_demo_static(parsed.path)):
                self._send(404, b"not found", "text/plain")
        elif parsed.path.startswith("/styles/admin-demo/"):
            if not (self._serve_static(parsed.path) or self._serve_admin_demo_static(parsed.path)):
                self._send(404, b"not found", "text/plain")
        elif parsed.path in ("/app.js", "/data.js") or parsed.path.startswith("/styles/") or parsed.path.startswith("/pages/"):
            if not self._serve_static(parsed.path):
                self._send(404, b"not found", "text/plain")
        elif parsed.path.endswith(".html"):
            # unquote: full-design pages keep the bundle's space-containing filenames
            if not self._serve_static(unquote(parsed.path)):
                self._send(404, b"not found", "text/plain")
        elif parsed.path == "/classic":
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")  # the classic paste-to-flow UI
        elif parsed.path == "/api/health":
            route = resolve_route()
            payload = {"embedding": self.index.backend.provenance(),
                       "components": len(self.index.items),
                       "llm": route.summary(), "llm_reachable": route.health()}
            self._send(200, json.dumps(payload).encode(), "application/json")
        elif handle_admin_demo_get(self, parsed):
            return
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
        elif parsed.path == "/api/run":
            if not self._authed(parsed):
                self._send(401, b'{"error":"token required"}', "application/json")
                return
            qs = parse_qs(parsed.query)
            task = (qs.get("task") or [""])[0]
            if not task.strip():
                self._send(400, b'{"error":"task required"}', "application/json")
                return
            from scripts.showcase.builder import run_trace
            self._send(200, json.dumps(run_trace(task, self.index)).encode(), "application/json")
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
            governance = _governance_metadata()
            res = [{"id": it["id"], "type": it["type"], "label": label_for_type(it["type"]),
                    "name": it["name"], "desc": it["desc"][:160],
                    "labels": it.get("labels", []), **governance.get(it["id"], {})}
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
            seam = _seam_for(parsed.path)
            if seam:
                self._proxy_seam(parsed, seam[0], seam[1])
                return
            # fall back to any real static file under web/<product>/ (e.g. /how-it-works.html, images).
            # _serve_static is path-traversal-guarded; /api/* never falls through here.
            if not parsed.path.startswith("/api/") and self._serve_static(unquote(parsed.path)):
                return
            self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if handle_admin_demo_post(self, parsed):
            return
        seam = _seam_for(parsed.path)
        if seam:
            self._proxy_seam(parsed, seam[0], seam[1])
            return
        self._send(404, b'{"error":"not found"}', "application/json")

    def log_message(self, *args) -> None:  # quiet
        pass


def serve(port: int = 8000) -> None:
    Handler.index = Index()
    Handler.token = os.environ.get("OH_SHOWCASE_TOKEN", "")
    # pre-warm the catalog governance cache off-thread: the port binds immediately and the
    # first /api/components hit never pays the ~seconds-long catalog sweep
    __import__("threading").Thread(target=_governance_metadata, daemon=True).start()
    bind_host = os.environ.get("OH_BIND_HOST", "127.0.0.1")  # 0.0.0.0 only in container deploys
    httpd = ThreadingHTTPServer((bind_host, port), Handler)
    gate = "token-gated" if Handler.token else "OPEN (set OH_SHOWCASE_TOKEN to gate)"
    seams = sorted({base for _, _, base in _SEAM_PROXIES})
    print(f"{OH_PRODUCT} showcase → http://{bind_host}:{port}  "
          f"({len(Handler.index.items)} components, embeddings={Handler.index.backend.name}, "
          f"promotable={Handler.index.backend.promotable}, /api/build {gate}, "
          f"service seams → {seams or 'none (registries unreadable)'})")
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
