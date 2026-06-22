#!/usr/bin/env python3
"""build_hub_sites — render the standardized page for every Open*Hub (one template, 22 consistent surfaces) + an index.

Pulls each hub's real data — roster (portfolio_connection_map), strategy (sources/mode/generator/bars), settings, and
the served components + funnel from the ComponentStore — and renders src/openharnesshub/hub_site.render_hub_page into
dist/sites/<slug>/index.html, plus a dist/sites/index.html directory. Counts are COMPUTED. serves_truth=false.

  PYTHONPATH=. python3 scripts/build_hub_sites.py --all
  PYTHONPATH=. python3 scripts/build_hub_sites.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
SITE_DIR = REPO / "dist" / "sites"
STRATEGY = REPO / "architecture" / "hub_population_strategy.json"


def _strategy() -> dict:
    try:
        return json.loads(STRATEGY.read_text(encoding="utf-8")).get("hubs", {})
    except Exception:  # noqa: BLE001
        return {}


def render_all(out_dir: Path = SITE_DIR, store=None) -> list[tuple[str, str]]:
    """Render every roster hub. Returns [(hub_id, html)]; writes <slug>/index.html + an index page."""
    from src.openharnesshub.component_store import ComponentStore
    from src.openharnesshub.hub_engine import hub_specs
    from src.openharnesshub.hub_settings import load_settings
    from src.openharnesshub.hub_site import render_hub_page, slugify
    store = store or ComponentStore()
    strat = _strategy()
    pages = []
    for s in hub_specs():
        cfg = strat.get(s.hub_id, {})
        try:
            served = store.serve(s.hub_id, "_global")
            funnel = store.funnel_summary(s.hub_id)
        except Exception:  # noqa: BLE001
            served, funnel = [], {"signals": 0}
        page = render_hub_page(
            s.hub_id, content_kind=s.component_kind, one_liner=s.component_kind and f"{s.component_kind.capitalize()} — governed, continuously updated, verify-gated.",
            tier=s.tier, consumed_by=s.consumed_by, contribution_mode=cfg.get("contribution_mode", "both"),
            sources=cfg.get("sources", {}), generator=cfg.get("generator", ""), settings=load_settings(s.hub_id),
            served=served, funnel=funnel, verify_bar=cfg.get("verify_bar", ""))
        pages.append((s.hub_id, page))
        p = out_dir / slugify(s.hub_id) / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page, encoding="utf-8")
    _write_index(out_dir, [h for h, _ in pages])
    return pages


def _write_index(out_dir: Path, hub_ids: list[str]) -> None:
    from src.openharnesshub.hub_site import slugify
    cards = "".join(
        f"<a class=card href='./{slugify(h)}/index.html'><h3>{h}</h3><p>open registry · powered by Teleon</p></a>"
        for h in hub_ids)
    htmlx = (
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Open*Hubs</title><style>"
        "body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,sans-serif}"
        ".wrap{max-width:980px;margin:0 auto;padding:56px 24px}h1{font-size:40px;letter-spacing:-.02em}"
        ".tag{color:#4f46e5;font-weight:700;text-transform:uppercase;letter-spacing:.1em;font-size:12px}"
        ".grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"
        ".card{display:block;border:1px solid #e6e8ef;border-radius:14px;padding:18px;background:#fff;text-decoration:none;color:inherit}"
        ".card h3{margin:0 0 4px;font-size:16px}.card p{margin:0;font-size:13px;color:#6b7280}"
        f"</style></head><body><div class=wrap><div class=tag>Open Harness Hub</div><h1>The Open*Hubs ({len(hub_ids)})</h1>"
        "<p style='color:#6b7280;max-width:640px'>The open ecosystem both Teleon and Baltor consume. Each hub is "
        f"continuously populated (discover · generate · intake), governed, and verify-gated.</p><div class=grid>{cards}</div></div></body></html>\n")
    (out_dir / "index.html").write_text(htmlx, encoding="utf-8")


def _self_test() -> int:
    import tempfile
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)
    with tempfile.TemporaryDirectory() as d:
        pages = render_all(out_dir=Path(d))
        ck("renders all 22 hub surfaces from ONE template", len(pages) == 22)
        sections = ["What it stores", "How it's populated", "Browse", "Settings", "Substrate"]
        ok_sections = all(all(sec in pg for sec in sections) for _, pg in pages)
        ck("every surface has the SAME standard sections (consistent UX)", ok_sections)
        ck("every surface uses the design system (Hanken Grotesk + IBM Plex Mono)",
           all("Hanken Grotesk" in pg and "IBM Plex Mono" in pg for _, pg in pages))
        ck("every surface carries the governance badge (serves_truth=false)",
           all("serves_truth=false" in pg for _, pg in pages))
        ck("the index lists all 22 hubs", (Path(d) / "index.html").exists() and "(22)" in (Path(d) / "index.html").read_text())
        ck("per-hub files written (slug/index.html)", (Path(d) / "openskillshub" / "index.html").exists())
    print("\n" + ("PASS - build_hub_sites: ONE standardized template renders all 22 Open*Hub surfaces with the same "
                  "sections + design system + governance badge, plus an index. Counts computed; serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    n = len(render_all())
    print(f"rendered {n} Open*Hub surfaces -> {SITE_DIR}/ (index at {SITE_DIR}/index.html)")
    raise SystemExit(0)
