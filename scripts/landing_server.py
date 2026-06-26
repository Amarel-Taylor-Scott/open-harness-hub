#!/usr/bin/env python3
"""scripts.landing_server — ONE branded "AI Done Right" landing page linking ALL live surfaces.

Reads the launchers' tunnel-URL outputs (dist/service-plane-tunnel-urls.json, dist/portfolio-share-urls.json) + the
design-bundle tunnel + architecture/surface_capability_spec.json, and renders a single page with links to every
live surface (the 5 pillars' apps, the design portfolio, the demos). URLs are read PER REQUEST, so the page stays
correct when ephemeral TryCloudflare tunnels restart. serves_truth=false.

  python3 scripts/landing_server.py [--port 8099]    then tunnel it for a public URL
  --self-test
"""
from __future__ import annotations

import http.server
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SPEC = REPO / "architecture" / "surface_capability_spec.json"
SVC = REPO / "dist" / "service-plane-tunnel-urls.json"
OHD_LOG = REPO / "data" / "dev-intel" / "ohd-tunnel.log"
#: pillar id → the service-plane target id whose live tunnel is that pillar's app
PILLAR_APP = {"ai-done-right": "context_is_everything_app", "teleon": "teleon_app", "aidevobserver": "aidevobserver_demo",
              "baltor": "baltor_app", "open-star-hubs": "harness_hub_app"}


def _json(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _live_svc_urls() -> dict:
    d = _json(SVC).get("targets", {})
    return {k: v.get("public_url") for k, v in d.items() if isinstance(v, dict) and v.get("status") == "LIVE" and v.get("public_url")}


def _design_url() -> str | None:
    try:
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", OHD_LOG.read_text(encoding="utf-8"))
        return m.group(0) if m else None
    except Exception:
        return None


def render() -> str:
    spec = _json(SPEC)
    svc = _live_svc_urls()
    design = _design_url()
    cards = []
    for p in spec.get("pillars", []):
        app = PILLAR_APP.get(p["id"])
        url = svc.get(app) if app else None
        caps = " · ".join(p.get("capabilities", [])[:5])
        badge = "" if url else " <span class='warn'>· needs its own page</span>"
        link = f'<a class="go" href="{url}" target="_blank" rel="noopener">Open the app →</a>' if url else \
            '<span class="warn">backend ready; web surface queued</span>'
        cards.append(f'<div class="card"><h2>{p["brand"]}{badge}</h2><p class="role">{p.get("role", "")}</p>'
                     f'<p class="caps">{caps}</p>{link}</div>')
    extra = []
    if design:
        extra.append(f'<a href="{design}" target="_blank" rel="noopener">Design Portfolio (full fidelity)</a>')
    for tid, label in [("byo_demos", "Demos · bring your own key"), ("registry_api", "Registry REST API (programmatic)"),
                       ("baltor_admin_demo_server", "Baltor Control Tower")]:
        if svc.get(tid):
            extra.append(f'<a href="{svc[tid]}" target="_blank" rel="noopener">{label}</a>')
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><meta name=robots content=noindex>
<title>AI Done Right — all surfaces</title><style>
body{{font-family:'Hanken Grotesk',system-ui,-apple-system,sans-serif;max-width:1040px;margin:2.5rem auto;padding:0 1.25rem;background:linear-gradient(180deg,#0b0e14,#0d1117 40%);color:#e6edf3;line-height:1.55}}
h1{{font-size:2rem;margin:0 0 .25rem;letter-spacing:-.5px}}.tag{{display:inline-block;border:1px solid #21262d;border-radius:999px;padding:4px 12px;color:#9aa7b4;font-size:12px;margin-bottom:1rem}}
.sub{{color:#9aa7b4;margin:0 0 2rem;max-width:760px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:1rem}}
.card{{border:1px solid #21262d;border-radius:14px;background:#11161d;padding:1.1rem 1.2rem;display:flex;flex-direction:column}}
.card h2{{font-size:1.15rem;margin:0 0 .25rem;color:#5a6b87}}.role{{color:#9aa7b4;font-size:.86rem;margin:.1rem 0 .6rem}}
.caps{{color:#cdd6e0;font-size:.82rem;margin:0 0 1rem;flex:1}}
a.go,.extra a{{display:inline-block;color:#0b0e14;background:#5a6b87;border-radius:9px;padding:.5rem .85rem;font-weight:600;text-decoration:none;font-size:.85rem}}
.extra{{margin-top:1.8rem;display:flex;gap:.6rem;flex-wrap:wrap}}.extra a{{background:#161b22;color:#5a6b87;border:1px solid #2a3340}}
.warn{{color:#e0a458;font-size:.74rem}}.foot{{color:#6b7682;font-size:.78rem;margin-top:2.2rem;border-top:1px solid #21262d;padding-top:1rem}}</style></head>
<body><h1>AI Done Right</h1><div class=tag>the holding company · every surface, live</div>
<p class=sub><b>Teleon</b> runs your capability on the cheapest bounded path that still passes (efficiency) · <b>Baltor</b> serves managed, verified, provable context (truth) · <b>Open*Hubs</b> is the open store both consume · <b>AIDevObserver</b> watches AI usage (the wedge).</p>
<div class=grid>{''.join(cards)}</div>
<div class=extra>{''.join(extra)}</div>
<p class=foot>Links are read live each load from the running tunnels. TryCloudflare quick tunnels are temporary URLs. serves_truth=false · prototypes + mock data.</p></body></html>"""


class _H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        body = render().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def self_test() -> int:
    h = render()
    assert "AI Done Right" in h and 'class=grid' in h, "renders the branded landing"
    assert isinstance(_live_svc_urls(), dict), "reads live service URLs without raising"
    assert set(PILLAR_APP) == {"ai-done-right", "teleon", "aidevobserver", "baltor", "open-star-hubs"}, "5 pillars mapped"
    print("landing_server self-test: OK (renders branded landing, reads live tunnel URLs, 5 pillars mapped)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8099
    print(f"AI Done Right landing on http://127.0.0.1:{port}")
    http.server.HTTPServer(("127.0.0.1", port), _H).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
