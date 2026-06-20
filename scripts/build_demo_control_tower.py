#!/usr/bin/env python3
"""scripts.build_demo_control_tower — render ONE start-here page (dist/sites/demo-control-tower/index.html) + ONE
consolidated all-URLs manifest (dist/demo-all-urls.{json,md,txt}) aggregating every demo surface.

Reuses: architecture/demo_surface_registry.json (the honest surface list) + scripts/portfolio_lib.py (titles/
ports/CSS) + .agent/portfolio-sites/urls.json (the REAL TryCloudflare URLs already captured by the portfolio
launcher). No external CDN/JS/analytics/secrets. Local-CSS only. --self-test builds + asserts.
"""
from __future__ import annotations

import html
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts import portfolio_lib as P

_REG = P.REPO / "architecture" / "demo_surface_registry.json"
_TUNNELS = P.REPO / ".agent" / "portfolio-sites" / "urls.json"
_CT_TUNNEL = P.REPO / "dist" / "demo-control-tower-url.txt"   # the control tower's own public URL (written post-launch)
_PAGE = P.DIST / "demo-control-tower" / "index.html"
_CAVEAT = ("TryCloudflare URLs are TEMPORARY, random session URLs — preview/demo, not production hosting. "
           "Surfaces marked CANDIDATE/INTERNAL are not live web pages yet (shown honestly). No paid cloud.")
_CFPB = "Baltor CFPB e2e (offline, PROVEN): answer = 10 business days · FAQ '30 days' held out · receipt + source handles."
_GROUP = {"static_site": "Portfolio sites", "interactive_demo": "Product demos", "dashboard": "Dashboards",
          "registry": "Open-hub registries", "internal_tool": "Internal tools"}


def _tunnel_urls() -> dict:
    if not _TUNNELS.exists():
        return {}
    return {sid: r.get("public_url") for sid, r in json.loads(_TUNNELS.read_text()).items() if r.get("public_url")}


def _extra_tunnels() -> dict:
    """Port-level tunnels (dist/cloudflare-extra-tunnels.json) — the SAME seam
    cloudflare_handoff consumes, so the two manifests can never disagree about
    which surfaces are publicly reachable."""
    f = P.REPO / "dist" / "cloudflare-extra-tunnels.json"
    return {str(k): v for k, v in json.loads(f.read_text()).items()} if f.exists() else {}


def _unified() -> list[dict]:
    reg = json.loads(_REG.read_text())["surfaces"]
    tcf = _tunnel_urls()
    extra = _extra_tunnels()
    ct_pub = _CT_TUNNEL.read_text().strip() if _CT_TUNNEL.exists() else None
    out = []
    for s in reg:
        port = s["local_port"]
        local = f"http://127.0.0.1:{port}{s['local_path']}" if port else None
        pub = None
        if s["surface_id"] == "demo-control-tower":
            pub = ct_pub
        elif s["surface_id"].startswith("site."):
            pub = tcf.get(s["surface_id"][len("site."):])  # map site.<pid> → portfolio tunnel
        if not pub and port and str(port) in extra and s["status"] == "active":
            pub = extra[str(port)].rstrip("/") + s["local_path"]  # port-level tunnel + route
        group = "Start here" if s["surface_id"] == "demo-control-tower" else _GROUP.get(s["surface_type"], "Other")
        out.append({"surface_id": s["surface_id"], "display_name": s["display_name"], "group": group,
                    "type": s["surface_type"], "status": s["status"], "local_url": local,
                    "trycloudflare_url": pub, "brand": s.get("brand_boundary", "")})
    return out


_GROUP_ORDER = ["Start here", "Portfolio sites", "Product demos", "Dashboards", "Open-hub registries", "Internal tools", "Other"]


def build() -> dict:
    surfaces = _unified()
    # ── consolidated manifests ──
    (P.REPO / "dist").mkdir(exist_ok=True)
    (P.REPO / "dist" / "demo-all-urls.json").write_text(json.dumps(
        {"caveat": _CAVEAT, "cfpb": _CFPB, "surfaces": surfaces}, indent=2))
    md = ["# Demo — all URLs (start here)", "", f"> {_CAVEAT}", "", f"_{_CFPB}_", ""]
    txt = [f"# {_CAVEAT}", ""]
    for grp in _GROUP_ORDER:
        items = [s for s in surfaces if s["group"] == grp]
        if not items:
            continue
        md.append(f"## {grp}")
        for s in items:
            pub = s["trycloudflare_url"] or ("—" if s["status"] != "active" else "(launch a tunnel)")
            loc = s["local_url"] or "(no web surface)"
            md.append(f"- **{s['display_name']}** [{s['status']}] — local: {loc} · public: {pub}")
            txt.append(f"{s['display_name']}\t[{s['status']}]\t{loc}\t{pub}")
        md.append("")
    (P.REPO / "dist" / "demo-all-urls.md").write_text("\n".join(md) + "\n")
    (P.REPO / "dist" / "demo-all-urls.txt").write_text("\n".join(txt) + "\n")
    # ── start-here page ──
    _PAGE.parent.mkdir(parents=True, exist_ok=True)
    _PAGE.write_text(_render(surfaces), encoding="utf-8")
    return {"surfaces": len(surfaces), "active": sum(1 for s in surfaces if s["status"] == "active"),
            "with_public_url": sum(1 for s in surfaces if s["trycloudflare_url"]),
            "page": str(_PAGE.relative_to(P.REPO))}


def _render(surfaces: list[dict]) -> str:
    css = P.SHARED_CSS.replace("__ACCENT__", "#5b6cff")
    badge = {"active": "#21c7a8", "candidate": "#f6c945", "internal_only": "#9aa7b4"}
    sections = []
    for grp in _GROUP_ORDER:
        items = [s for s in surfaces if s["group"] == grp]
        if not items:
            continue
        cards = []
        for s in items:
            b = badge.get(s["status"], "#9aa7b4")
            links = []
            if s["local_url"]:
                links.append(f'<a href="{html.escape(s["local_url"])}">local</a>')
            if s["trycloudflare_url"]:
                links.append(f'<a href="{html.escape(s["trycloudflare_url"])}">public ↗</a>')
            linkhtml = " · ".join(links) or '<span class="rel">no web surface</span>'
            cards.append(
                f'<div class="card"><h3>{html.escape(s["display_name"])} '
                f'<span style="font-size:11px;color:{b};border:1px solid {b};border-radius:6px;padding:1px 6px">{s["status"]}</span></h3>'
                f'<p class="rel" style="font-size:13px">{html.escape(s["brand"])}</p>{linkhtml}</div>')
        sections.append(f'<section id="{grp.lower().replace(" ", "-")}"><h2>{html.escape(grp)}</h2>'
                        f'<div class="grid2">{"".join(cards)}</div></section>')
    script = "".join(f"<li>{html.escape(x)}</li>" for x in [
        "Open this Demo Control Tower (start here).",
        "Open AI Done Right → Teleon → Baltor (the portfolio thesis: OpenContextHub→Teleon→Baltor).",
        "Run the Baltor CFPB demo: PYTHONPATH=. python3 scripts/demo_offline_full_baltor.py --self-test",
        "Show the result: answer 10 business days, FAQ-30 held out, receipt + source handles.",
        "Open the public open-hub spine: Context, Skills, Tools, MCP, Compression, Benchmark, Harness.",
        "Explain: hubs supply context/skills/tools/proof · Teleon runs capabilities · Baltor governs truth.",
    ])
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="icon" href="data:,">
<meta name="robots" content="noindex"><title>Demo Control Tower — AI Done Right portfolio</title>
<style>{css}</style></head><body>
<header class="top"><div class="wrap brand"><span class="dot"></span>Demo Control Tower
<span class="kind">AI Done Right portfolio · start here</span></div></header>
<main class="wrap">
<div class="hero"><h1>Demo everything, end to end.</h1>
<p class="lead">One page for every portfolio surface — local + TryCloudflare URLs, honest status, and a guided
demo script. {html.escape(_CFPB)}</p></div>
{"".join(sections)}
<section id="demo-script"><h2>Demo script (end to end)</h2><ol class="clean">{script}</ol></section>
<section id="caveats"><h2>Caveats</h2><div class="disclaimer">{html.escape(_CAVEAT)}</div></section>
</main>
<footer><div class="wrap">Consolidated URLs: <code>dist/demo-all-urls.md</code> · generated by build_demo_control_tower.</div></footer>
</body></html>
"""


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    res = build()
    page = _PAGE.read_text()
    md = (P.REPO / "dist" / "demo-all-urls.md").read_text()
    check("start-here page built", _PAGE.exists() and "Demo Control Tower" in page)
    check("consolidated manifests written (json/md/txt)", all((P.REPO / "dist" / f"demo-all-urls.{e}").exists() for e in ("json", "md", "txt")))
    check("every active surface appears on the page", all(s["display_name"] in page for s in _unified() if s["status"] == "active"))
    check(f"{len(P.SITE_ORDER)} static portfolio sites + hub present",
          sum(1 for s in _unified() if s["surface_id"].startswith("site.")) == len(P.SITE_ORDER) + 1)
    check("CFPB e2e invariant shown (10 business days + held-out)", "10 business days" in page and "held out" in page)
    check("demo script present", "Demo script" in page)
    check("caveat present (temporary URLs)", "TEMPORARY" in page or "temporary" in page.lower())
    check("no external scripts/CDN", not any(m in page for m in ('src="http', "<script", "cdn.", "googleapis")))
    check("candidate/internal surfaces shown honestly", "candidate" in page and "internal_only" in page)
    print("\n" + (f"PASS — build_demo_control_tower: {res['surfaces']} surfaces ({res['active']} active, "
                  f"{res['with_public_url']} with public URLs) on one start-here page + dist/demo-all-urls.*; "
                  f"CFPB invariant shown; no external scripts; honest status." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    r = build()
    print(f"built demo control tower: {r['surfaces']} surfaces → {r['page']} + dist/demo-all-urls.*")
    raise SystemExit(0)
