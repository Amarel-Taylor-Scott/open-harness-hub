#!/usr/bin/env python3
"""build_hub_sites — render the standardized page for every Open*Hub (one template, 22 consistent surfaces) + an index.

Pulls each hub's real data — roster (portfolio_connection_map), strategy (sources/mode/generator/bars), settings, and
the served components + funnel from the ComponentStore — and renders _repos/openhubforai/backend/src/openhubforai/hub_site.render_hub_page into
dist/sites/<slug>/index.html, plus a dist/sites/index.html directory. Counts are COMPUTED. serves_truth=false.

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_hub_sites.py --all
  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_hub_sites.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
SITE_DIR = _resource("dist/sites")
STRATEGY = _resource("architecture") / "hub_population_strategy.json"
PROFILES = _resource("architecture") / "hub_profiles.json"


def _strategy() -> dict:
    try:
        return json.loads(STRATEGY.read_text(encoding="utf-8")).get("hubs", {})
    except Exception:  # noqa: BLE001
        return {}


def _profiles() -> dict:
    """hub_id -> profile (incl. model-authored one_liner + use_cases). Single source of hub display copy."""
    try:
        return json.loads(PROFILES.read_text(encoding="utf-8")).get("profiles", {})
    except Exception:  # noqa: BLE001
        return {}


#: legacy portfolio hub site id -> roster hub id (the convergence map).
_PORTFOLIO_HUB_MAP = {"opencontexthub": "OpenContextHub", "openskillshub": "OpenSkillsHub",
                      "opentoolshub": "OpenToolsHub", "openhubforai": "OpenHubForAI"}


def portfolio_hub_section(portfolio_id: str):
    """The ONE shared operational summary for a legacy portfolio hub page — computed from the SAME registries the 22
    standardized hub pages use (hub_specs + strategy + settings). The convergence: the portfolio hub page's operational
    content is single-sourced with build_hub_sites and can't drift. Returns (title, plain-text body) or None."""
    rid = _PORTFOLIO_HUB_MAP.get(portfolio_id)
    if not rid:
        return None
    try:
        from src.openhubforai.hub_engine import hub_specs
        from src.openhubforai.hub_settings import load_settings
        spec = next((s for s in hub_specs() if s.hub_id == rid), None)
        if not spec:
            return None
        strat = _strategy().get(rid, {})
        st = load_settings(rid)
        srcs = []
        for k, v in (strat.get("sources") or {}).items():
            srcs += [f"{k}:{x}" for x in (v if isinstance(v, list) else [v])]
        gen = strat.get("generator") or "—"
        n = len(hub_specs())
        body = (f"Rendered by the same standardized hub engine as all {n} Open*Hubs (one template, no duplicate). "
                f"Stores {spec.component_kind}. Populated by three governed channels: discover (public sources: "
                f"{', '.join(srcs[:4]) or 'curated'}), generate ({gen}), and intake (owner OKF/links/text). "
                f"Bar to serve: {strat.get('verify_bar', 'verified + named + sourced')}. Served only after the verify "
                f"gate — discovery is not trust (serves_truth=false). Consumed by {spec.consumed_by or 'Teleon/Baltor'}; "
                f"cadence {st.cadence} cycles. Users keep their own versioned components; opt-in contribute promotes to global.")
        return (f"How {rid} is populated & governed", body)
    except Exception:  # noqa: BLE001
        return None


def render_all(out_dir: Path = SITE_DIR, store=None) -> list[tuple[str, str]]:
    """Render every roster hub. Returns [(hub_id, html)]; writes <slug>/index.html + an index page."""
    from src.openhubforai.component_store import ComponentStore
    from src.openhubforai.hub_engine import hub_specs
    from src.openhubforai.hub_settings import load_settings
    from src.openhubforai.hub_site import render_hub_page, slugify
    store = store or ComponentStore()
    strat = _strategy()
    profs = _profiles()
    pages = []
    for s in hub_specs():
        cfg = strat.get(s.hub_id, {})
        prof = profs.get(s.hub_id, {})
        # Model-authored value-prop from hub_profiles (single source); fall back to the generic computed line.
        one_liner = prof.get("one_liner") or (s.component_kind and f"{s.component_kind.capitalize()} — governed, continuously updated, verify-gated.")
        try:
            served = store.serve(s.hub_id, "_global")
            funnel = store.funnel_summary(s.hub_id)
        except Exception:  # noqa: BLE001
            served, funnel = [], {"signals": 0}
        page = render_hub_page(
            s.hub_id, content_kind=s.component_kind, one_liner=one_liner,
            tier=s.tier, consumed_by=s.consumed_by, contribution_mode=cfg.get("contribution_mode", "both"),
            sources=cfg.get("sources", {}), generator=cfg.get("generator", ""), settings=load_settings(s.hub_id),
            served=served, funnel=funnel, verify_bar=cfg.get("verify_bar", ""))
        pages.append((s.hub_id, page))
        p = out_dir / slugify(s.hub_id) / "index.html"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(page, encoding="utf-8")
    _write_index(out_dir, [h for h, _ in pages], profs)
    return pages


def _write_index(out_dir: Path, hub_ids: list[str], profs: dict | None = None) -> None:
    from src.openhubforai.hub_site import slugify
    profs = profs or {}

    def esc(t: object) -> str:
        return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    def card(h: str) -> str:
        prof = profs.get(h, {})
        blurb = prof.get("one_liner") or "open registry · powered by Teleon"
        ucs = prof.get("use_cases") or []
        uc = f"<span class=uc>e.g. {esc(ucs[0])}</span>" if ucs else ""
        return (f"<a class=card href='./{slugify(h)}/index.html'><h3>{esc(h)}</h3>"
                f"<p>{esc(blurb)}</p>{uc}</a>")

    cards = "".join(card(h) for h in hub_ids)
    htmlx = (
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Open*Hubs</title><style>"
        "body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,sans-serif}"
        ".wrap{max-width:980px;margin:0 auto;padding:56px 24px}h1{font-size:40px;letter-spacing:-.02em}"
        ".tag{color:#4f46e5;font-weight:700;text-transform:uppercase;letter-spacing:.1em;font-size:12px}"
        ".grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-top:24px}@media(max-width:680px){.grid{grid-template-columns:1fr}}"
        ".card{display:block;border:1px solid #e6e8ef;border-radius:14px;padding:18px;background:#fff;text-decoration:none;color:inherit}"
        ".card h3{margin:0 0 4px;font-size:16px}.card p{margin:0;font-size:13px;color:#6b7280}"
        ".card .uc{display:block;margin-top:8px;font-size:12px;color:#9aa0ad}"
        f"</style></head><body><div class=wrap><div class=tag>OpenHubForAI</div><h1>The Open*Hubs ({len(hub_ids)})</h1>"
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
        page_map = dict(pages)
        ck("every hub renders its model-authored value-prop (no generic fallback line)",
           not any("continuously updated, verify-gated" in pg for _, pg in pages))
        ck("a known hub's real one_liner is rendered",
           "Reliability-weighted model-routing" in page_map.get("OpenRoutingHub", ""))
        idx = (Path(d) / "index.html").read_text() if (Path(d) / "index.html").exists() else ""
        ck("the index lists all 22 hubs", "(22)" in idx)
        ck("the index surfaces per-hub use-cases", "e.g." in idx)
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
