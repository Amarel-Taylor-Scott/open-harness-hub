#!/usr/bin/env python3
"""demo_dashboard — a dashboard of the Teleon DESCENT demos (descend off the expensive default).

Reads _repos/shared-backend-components/architecture/teleon_demo_catalog.json, computes LIVE savings for the built ('live') demos from their real
modules (never hand-typed), shows the designed estimate for 'ideated' ones, and emits a self-contained HTML dashboard
+ a console summary. Each card shows: what most people do (the expensive default) -> the descended DAG over the shared
step library -> the measured/estimated saving -> the governance. serves_truth=false.

  --self-test   prove the catalog loads, live demos compute positive savings, the dashboard renders them
  --emit        write dist/teleon-demos/index.html
  --print       print the console summary
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/demo_dashboard.py --emit --print
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CATALOG = _resource("architecture") / "teleon_demo_catalog.json"
OUT = _resource("dist") / "teleon-demos" / "index.html"


def load_catalog() -> dict:
    return json.loads(CATALOG.read_text(encoding="utf-8"))


def live_savings() -> dict:
    """Compute the real saving for each 'live' demo from its module (computed, not typed)."""
    out: dict = {}
    try:
        from src.teleon.extraction import document_extraction_cascade as dx
        s8 = dx.extraction_savings(confidence_floor=0.8)
        s5 = dx.extraction_savings(confidence_floor=0.5)
        out["doc_schema_extraction"] = {
            "baseline": s8["frontier_only_cost"], "descended": s8["cascade_cost"],
            "headline_pct": s8["pct_saved"], "lenient_pct": s5["pct_saved"],
            "detail": f"${s8['frontier_only_cost']} frontier-only → ${s8['cascade_cost']} (strict {s8['pct_saved']}% / lenient {s5['pct_saved']}% saved); cheap model {s8['model_lineage'].get('cheap_llm')}"}
    except Exception as e:  # noqa: BLE001
        out["doc_schema_extraction"] = {"error": str(e)}
    try:
        from src.teleon.enrichment import search_enrich as se
        e = se.demonstrate()
        out["search_enrichment"] = {
            "baseline": e["baseline_cost"], "descended": e["descended_cost"], "headline_pct": e["pct_saved"],
            "detail": f"${e['baseline_cost']} {e['baseline_provider']} → ${e['descended_cost']} ({e['descended_provider']}+{e['synth_model']}); {e['pct_saved']}% saved"}
    except Exception as e:  # noqa: BLE001
        out["search_enrichment"] = {"error": str(e)}
    return out


def _saving_for(demo: dict, live: dict) -> tuple[str, str]:
    """(big number, label) for a demo card."""
    if demo["status"] == "live":
        s = live.get(demo["id"], {})
        if "error" in s:
            return ("—", f"live (error: {s['error'][:40]})")
        return (f"{s.get('headline_pct', '?')}%", "measured saving (live)")
    return (f"~{demo.get('expected_pct_saved', '?')}%", "designed estimate (ideated)")


def render_html(catalog: dict, live: dict) -> str:
    demos = catalog["demos"]
    n_live = sum(1 for d in demos if d["status"] == "live")
    cards = []
    for d in sorted(demos, key=lambda x: (x["status"] != "live", x["id"])):
        big, label = _saving_for(d, live)
        badge = "LIVE" if d["status"] == "live" else "IDEATED"
        badge_cls = "live" if d["status"] == "live" else "ideated"
        dag = " → ".join(d.get("descended_dag", []))
        axes = "".join(f"<span class=chip>{a}</span>" for a in d.get("axes", []))
        detail = live.get(d["id"], {}).get("detail", "") if d["status"] == "live" else ""
        cards.append(f"""
      <div class="card">
        <div class="card-h"><span class="badge {badge_cls}">{badge}</span><h3>{d['title']}</h3></div>
        <div class="big">{big}<span class="big-l">{label}</span></div>
        <p class="row"><b>Most people:</b> {d['expensive_default']}</p>
        <p class="row"><b>Teleon descends to:</b> <code>{dag}</code></p>
        <p class="axes">{axes}</p>
        {f'<p class="detail">{detail}</p>' if detail else ''}
        <p class="gov">⛓ {d.get('governance','')}</p>
      </div>""")
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Teleon Demos — descend off the expensive default</title>
<style>
  :root{{--ink:#0d1117;--mut:#5b6470;--line:#e6e8eb;--live:#0a7d3c;--ide:#6b7280;--bg:#fafbfc;--acc:#1f6feb}}
  *{{box-sizing:border-box}} body{{margin:0;font-family:'Hanken Grotesk',system-ui,sans-serif;color:var(--ink);background:var(--bg)}}
  header{{padding:40px 32px 8px}} h1{{margin:0;font-size:30px;letter-spacing:-.02em}}
  .sub{{color:var(--mut);max-width:760px;margin:10px 0 0;font-size:15px;line-height:1.5}}
  .meta{{color:var(--mut);font-size:13px;margin:18px 32px}}
  .grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:16px;padding:8px 32px 48px}}
  .card{{background:#fff;border:1px solid var(--line);border-radius:14px;padding:18px 18px 14px}}
  .card-h{{display:flex;align-items:center;gap:10px}} h3{{margin:0;font-size:17px}}
  .badge{{font:600 10px/1 'IBM Plex Mono',ui-monospace,monospace;padding:4px 7px;border-radius:6px;color:#fff;letter-spacing:.06em}}
  .badge.live{{background:var(--live)}} .badge.ideated{{background:var(--ide)}}
  .big{{font-size:34px;font-weight:700;margin:12px 0 2px;letter-spacing:-.02em}}
  .big-l{{font-size:12px;font-weight:500;color:var(--mut);margin-left:8px}}
  .row{{font-size:13.5px;margin:8px 0;line-height:1.45}} .row b{{color:var(--ink)}}
  code{{font-family:'IBM Plex Mono',ui-monospace,monospace;font-size:11.5px;color:var(--acc);background:#f3f6fb;padding:2px 5px;border-radius:5px;display:inline-block;line-height:1.5}}
  .chip{{font:500 11px 'IBM Plex Mono',monospace;color:var(--mut);border:1px solid var(--line);border-radius:20px;padding:2px 9px;margin:2px 4px 2px 0;display:inline-block}}
  .axes{{margin:6px 0}} .detail{{font-size:12px;color:var(--mut);font-family:'IBM Plex Mono',monospace;margin:6px 0}}
  .gov{{font-size:12px;color:var(--live);margin:8px 0 0}}
</style></head><body>
<header>
  <h1>Teleon — descend off the expensive default</h1>
  <p class=sub>Most teams send everything to the most expensive frontier model. Teleon composes a flexible DAG of
  reusable steps (route · filter · chunk · retrieve · rerank · extract · synthesize · merge) and picks the
  <b>cheapest viable path that still meets the requirement</b> — recording every choice, never serving truth it can't ground.</p>
</header>
<p class=meta>{len(demos)} demos · {n_live} live (measured) · {len(demos)-n_live} ideated · savings computed from the modules, never hand-typed.</p>
{_mediums_panel()}
<div class=grid>{''.join(cards)}</div>
</body></html>"""


def _mediums_panel() -> str:
    """A panel of the configurable MEDIUMS — clients connect their preferred compute/LLM/search per function."""
    try:
        from src.teleon.config.medium_resolver import available_mediums
        a = available_mediums()
    except Exception:
        return ""
    def chips(xs):
        return "".join(f'<span class=chip>{x}</span>' for x in xs)
    return (f'<div style="margin:8px 32px 24px;padding:16px 18px;background:#fff;border:1px solid #e6e8eb;border-radius:14px">'
            f'<b>Configurable mediums</b> <span style="color:#5b6470;font-size:13px">— connect your own; set different mediums per function '
            f'(config UI: dist/teleon-config/index.html). Teleon orchestrates; compute runs on your infra.</span>'
            f'<p class=row><b>Compute</b> ({len(a.get("compute",[]))}): {chips(a.get("compute",[]))}</p>'
            f'<p class=row><b>Ownership</b>: {chips(a.get("compute_ownership",[]))}</p>'
            f'<p class=row><b>LLM lanes</b>: {chips(a.get("llm",[]))}</p>'
            f'<p class=row><b>Search</b>: {chips(a.get("search",[]))}</p></div>')


def console(catalog: dict, live: dict) -> str:
    lines = ["Teleon descent demos:"]
    for d in catalog["demos"]:
        big, label = _saving_for(d, live)
        lines.append(f"  [{d['status']:>7}] {d['title']:<38} {big:>6}  {label}")
    return "\n".join(lines)


def _self_test() -> int:
    fails = []
    def ck(name, ok, detail=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': '+detail) if detail and not ok else ''}")
        if not ok: fails.append(name)
    cat = load_catalog()
    live = live_savings()
    n_live = sum(1 for d in cat["demos"] if d["status"] == "live")
    ck("catalog has >=2 live demos + several ideated", n_live >= 2 and len(cat["demos"]) >= 6, f"{n_live} live / {len(cat['demos'])} total")
    ck("the doc-extraction live demo computes a positive measured saving", live["doc_schema_extraction"].get("headline_pct", 0) > 0, str(live["doc_schema_extraction"]))
    ck("the enrichment live demo computes a positive measured saving", live["search_enrichment"].get("headline_pct", 0) > 0, str(live["search_enrichment"]))
    html = render_html(cat, live)
    ck("the dashboard renders every demo title", all(d["title"] in html for d in cat["demos"]))
    ck("live demos show their MEASURED saving (computed, not typed)", f"{live['search_enrichment']['headline_pct']}%" in html)
    ck("ideated demos are clearly labeled designed estimates", "designed estimate (ideated)" in html)
    ck("the dashboard states serves_truth governance", "never serving truth" in html or "serves_truth" in html.lower() or "ground" in html.lower())
    print("\n" + ("PASS - demo_dashboard --self-test: a dashboard of Teleon descent demos — live demos compute their "
                  "measured savings from the modules (extraction + enrichment), ideated demos carry a labeled designed "
                  "estimate; every card shows the expensive default → the descended DAG → the saving → the governance."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    cat, live = load_catalog(), live_savings()
    if "--emit" in argv:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(render_html(cat, live), encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)}")
    print(console(cat, live))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
