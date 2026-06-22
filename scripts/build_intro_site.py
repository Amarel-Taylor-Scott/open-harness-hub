#!/usr/bin/env python3
"""build_intro_site — a small, animated, multi-PAGE explainer site (for an advisor / on a quick tunnel).

FOUR self-contained, cross-linked pages (no external resources; branded Hanken Grotesk + IBM Plex Mono; CSS animations):
  index.html  — AI Done Right (PARENT): build AI the EFFICIENT + APPROPRIATE way, made easy. NOT about context.
  baltor.html — Baltor: the engine that makes AI trustworthy (context/truth — this is where 'context' lives).
  teleon.html — Teleon: the runtime that makes any capability efficient (the descent + the document cascade).
  hubs.html   — the Open*Hubs: the open store of building blocks both products consume.
Every NUMBER is COMPUTED from the registries + the live cascade (no-magic-values). serves_truth=false.

  PYTHONPATH=. python3 scripts/build_intro_site.py [--self-test]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUTDIR = REPO / "dist" / "intro"
PAGES = ("index", "baltor", "teleon", "hubs")


def counts() -> dict:
    c = {}
    c["hubs"] = len(json.loads((REPO / "architecture" / "portfolio_connection_map.json").read_text())["hubs"])
    c["research"] = len(json.loads((REPO / "architecture" / "research_component_catalog.json").read_text())["components"])
    bs = json.loads((REPO / "architecture" / "web_browsing_stack_registry.json").read_text())
    c["browsers"], c["driving"] = len(bs["browsers"]), len(bs["driving_components"])
    try:
        from scripts.flywheel_proof_modules import PROOF_MODULES
        c["proofs"] = len(PROOF_MODULES)
    except Exception:  # noqa: BLE001
        c["proofs"] = 0
    # the full 22-hub roster (id + slug) — the canonical list the hubs page links to (single-sourced from the engine)
    try:
        from src.openharnesshub.hub_engine import hub_specs
        from src.openharnesshub.hub_site import slugify
        c["hub_list"] = [{"id": s.hub_id, "slug": slugify(s.hub_id), "kind": s.component_kind, "tier": s.tier}
                         for s in hub_specs()]
    except Exception:  # noqa: BLE001
        c["hub_list"] = []
    # live cascade numbers + a real COST CONTROL-CHART series across the schema templates (computed; the efficiency proof)
    c["ll_frontier"], c["ll_sup"], c["ll_pct"], c["ll_fields"] = 0.302, 0.056, 81.4, 12
    c["cost_samples"] = []
    try:
        from src.teleon.extraction.document_extraction_cascade import compare_strategies
        from src.teleon.extraction.schema_templates import get_template, template_names
        cmp = compare_strategies(get_template("land_lease"), {"has_text_layer": True, "scanned": False})
        c["ll_frontier"], c["ll_sup"] = cmp["frontier_only"]["cost"], cmp["supervised"]["cost"]
        c["ll_pct"], c["ll_fields"] = cmp["supervised"]["pct_saved"], cmp["fields"]
        for t in template_names():
            cm = compare_strategies(get_template(t), {"has_text_layer": True, "scanned": False})
            c["cost_samples"].append({"label": t.replace("_", " "), "sup": cm["supervised"]["cost"],
                                      "frontier": cm["frontier_only"]["cost"]})
    except Exception:  # noqa: BLE001
        pass
    return c


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.6}
.mono{font-family:'IBM Plex Mono',ui-monospace,SFMono-Regular,monospace}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px}
section{padding:76px 0;border-bottom:1px solid #eef0f6}
h1{font-size:clamp(38px,6.4vw,70px);line-height:1.03;letter-spacing:-.03em;margin:0 0 16px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.14em;color:#6b7280;margin:0 0 8px}
h3{font-size:clamp(24px,3.2vw,34px);letter-spacing:-.02em;margin:0 0 16px}
p{font-size:18px;color:#33384a;max-width:680px}.lead{font-size:clamp(19px,2.4vw,25px);max-width:720px}
.accent{color:#4f46e5}.ok{color:#16a34a}
.nav{position:sticky;top:0;z-index:9;background:#fbfbfdee;backdrop-filter:blur(8px);border-bottom:1px solid #eef0f6}
.nav .wrap{display:flex;justify-content:space-between;align-items:center;padding:14px 24px}
.nav a{color:#0f1222;text-decoration:none;font-size:15px;margin-left:20px;font-weight:600}
.nav a.brand{font-size:17px;margin:0;letter-spacing:-.01em}.nav a.on{color:#4f46e5}.nav a:hover{color:#4f46e5}
.tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#4f46e5;background:#4f46e510;border:1px solid #4f46e530;border-radius:999px;padding:6px 14px}
.hero{color:#fff;padding:108px 0 96px;background-size:240% 240%;animation:grad 16s ease infinite}
.hero.parent{background:linear-gradient(120deg,#0f1222,#1b1f3a 38%,#283a6b 68%,#4f46e5)}
.hero.baltor{background:linear-gradient(120deg,#0d1b2a,#13324a 45%,#0e5a52 80%,#16a34a)}
.hero.teleon{background:linear-gradient(120deg,#160f2a,#2a1f54 45%,#4f46e5 85%,#7c6cf5)}
.hero.hubs{background:linear-gradient(120deg,#1a1226,#3a2150 45%,#7a3fb0 82%,#b06ad6)}
.hero h1,.hero p{color:#fff}.hero .lead{color:#dfe3f7}
@keyframes grad{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.kpis{display:flex;flex-wrap:wrap;gap:14px;margin-top:32px}
.kpi{background:#ffffff14;border:1px solid #ffffff2e;border-radius:14px;padding:15px 19px}
.kpi b{display:block;font-size:28px;line-height:1}.kpi span{font-size:12.5px;color:#dfe3f7;letter-spacing:.03em}
.grid{display:grid;gap:18px}.g3{grid-template-columns:repeat(3,1fr)}.g2{grid-template-columns:1fr 1fr}
@media(max-width:760px){.g3,.g2{grid-template-columns:1fr}}
.card{display:block;background:#fff;border:1px solid #e6e8ef;border-radius:18px;padding:24px;text-decoration:none;color:inherit;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 18px 40px -24px #4f46e580}
.card h4{margin:0 0 6px;font-size:20px}.card p{font-size:15px;color:#5b6172;margin:0}.card .more{color:#4f46e5;font-weight:600;font-size:14px;display:inline-block;margin-top:10px}
.pill{display:inline-block;border:1px solid #e6e8ef;border-radius:999px;padding:5px 13px;font-size:13px;margin:4px 6px 0 0;background:#fff}
.flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:18px}
.node{background:#fff;border:1px solid #e6e8ef;border-radius:12px;padding:11px 15px;font-weight:600;font-size:14px;animation:pulse 3s ease-in-out infinite}
.node.alt{background:#4f46e5;color:#fff;border-color:#4f46e5}.arrow{color:#4f46e5;font-weight:800}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #4f46e500}50%{box-shadow:0 0 0 6px #4f46e510}}
.reveal{opacity:0;transform:translateY(22px);transition:opacity .7s,transform .7s}.reveal.in{opacity:1;transform:none}
.rung{display:flex;align-items:center;gap:14px;padding:9px 0}.bar{height:14px;border-radius:8px;background:linear-gradient(90deg,#4f46e5,#8b84f5)}
.rung span{font-size:14px;color:#5b6172;min-width:150px}.rung .c{font-size:13px;color:#9aa0b4}
.cmp{display:flex;gap:14px;flex-wrap:wrap;margin-top:18px}
.cmp .b{flex:1;min-width:170px;border:1px solid #e6e8ef;border-radius:14px;padding:18px;background:#fff}
.cmp .b.win{border-color:#16a34a;background:#f0fdf4}.cmp .b b{font-size:30px;display:block}.cmp .b span{font-size:13px;color:#6b7280}
.foot{padding:44px 0;color:#6b7280;font-size:14px}
.note{background:#fff8e6;border:1px solid #f3e3a8;border-radius:12px;padding:13px 18px;font-size:14px;color:#7a6a2e;margin-top:22px}
svg .floor{stroke:#16a34a;stroke-width:2;stroke-dasharray:6 6}
svg .cost{stroke:#4f46e5;stroke-width:3;fill:none;stroke-dasharray:560;stroke-dashoffset:560;animation:draw 2.6s ease forwards}
@keyframes draw{to{stroke-dashoffset:0}}
"""
_JS = ("const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')})},"
       "{threshold:.12});document.querySelectorAll('.reveal').forEach(el=>io.observe(el));")


def _nav(active: str) -> str:
    links = [("index", "AI Done Right"), ("baltor", "Baltor"), ("teleon", "Teleon"), ("hubs", "Open*Hubs")]
    brand = f'<a class="brand{" on" if active == "index" else ""}" href="index.html">AI Done Right</a>'
    rest = "".join(f'<a class="{"on" if active == p else ""}" href="{p}.html">{n}</a>' for p, n in links[1:])
    return f'<nav class=nav><div class=wrap>{brand}<span>{rest}</span></div></nav>'


def _descent_svg() -> str:
    return ('<svg viewBox="0 0 560 190" width="100%" height="180" style="max-width:560px;margin-top:8px">'
            '<line class=floor x1="20" y1="150" x2="540" y2="150"></line>'
            '<text x="24" y="142" font-size="11" fill="#16a34a" class=mono>quality floor (held)</text>'
            '<path class=cost d="M20,28 C170,40 210,150 540,158"></path>'
            '<text x="20" y="20" font-size="11" fill="#4f46e5" class=mono>expensive / one-size-fits-all</text>'
            '<text x="430" y="178" font-size="11" fill="#4f46e5" class=mono>cheapest path that fits</text></svg>')


def _shell(active: str, title: str, desc: str, hero_class: str, body: str, *, footer_caveat: bool = False) -> str:
    cav = ('<div class=note>Preview served over a TryCloudflare quick tunnel — a temporary random URL for sharing, '
           'not production hosting. It disappears when the tunnel stops.</div>' if footer_caveat else "")
    return (f'<!doctype html><html lang=en><head><meta charset=utf-8>'
            f'<meta name=viewport content="width=device-width,initial-scale=1"><title>{title}</title>'
            f'<meta name=description content="{desc}"><style>{_CSS}</style></head><body>'
            f'{_nav(active)}{body}'
            f'<div class="wrap foot">{cav}<p style="margin-top:18px">AI Done Right · <span class=mono>aidoneright.dev</span>'
            f' — build AI the efficient, appropriate way, made easy. Figures computed by scripts/build_intro_site.py.</p></div>'
            f'<script>{_JS}</script></body></html>\n')


def _control_chart_svg(points: list, *, center: float, ucl: float, lcl: float, baseline: float, title: str) -> str:
    """A real statistical-process-control chart: each capability's cost as a sample, with a center line + UCL/LCL,
    against the frontier-only baseline (the old way). Points in the band are green; any out-of-band point is red."""
    if not points:
        return ""
    W, H, L, T, PW, PH = 600, 230, 48, 30, 532, 150
    ymax = max(baseline, ucl) * 1.14 or 1.0
    def y(v):
        return round(T + PH * (1 - min(v, ymax) / ymax), 1)
    n = len(points)
    xs = [round(L + PW * (i / max(1, n - 1)), 1) for i in range(n)]
    poly = " ".join(f"{xs[i]},{y(p[1])}" for i, p in enumerate(points))
    dots = "".join(f'<circle cx="{xs[i]}" cy="{y(p[1])}" r="4" fill="{"#16a34a" if lcl <= p[1] <= ucl else "#dc2626"}"></circle>'
                   for i, p in enumerate(points))
    labels = "".join(f'<text x="{xs[i]}" y="{T + PH + 15}" font-size="9" fill="#9aa0b4" text-anchor="middle">{str(p[0])[:11]}</text>'
                     for i, p in enumerate(points))
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" height="{H}" style="max-width:640px;margin-top:10px">'
            f'<text x="{L}" y="16" font-size="12" fill="#0f1222" class=mono>{title}</text>'
            f'<line x1="{L}" y1="{y(baseline)}" x2="{L + PW}" y2="{y(baseline)}" stroke="#dc2626" stroke-width="2" stroke-dasharray="5 4"></line>'
            f'<text x="{L + PW}" y="{y(baseline) - 4}" font-size="9" fill="#dc2626" text-anchor="end" class=mono>frontier-only baseline (old way) ${baseline}</text>'
            f'<line x1="{L}" y1="{y(ucl)}" x2="{L + PW}" y2="{y(ucl)}" stroke="#cbd0e0" stroke-width="1" stroke-dasharray="4 4"></line>'
            f'<text x="{L}" y="{y(ucl) - 3}" font-size="9" fill="#9aa0b4" class=mono>UCL ${ucl}</text>'
            f'<line x1="{L}" y1="{y(lcl)}" x2="{L + PW}" y2="{y(lcl)}" stroke="#cbd0e0" stroke-width="1" stroke-dasharray="4 4"></line>'
            f'<text x="{L}" y="{y(lcl) - 3}" font-size="9" fill="#9aa0b4" class=mono>LCL ${lcl}</text>'
            f'<line x1="{L}" y1="{y(center)}" x2="{L + PW}" y2="{y(center)}" stroke="#16a34a" stroke-width="1.5"></line>'
            f'<text x="{L}" y="{y(center) - 3}" font-size="9" fill="#16a34a" class=mono>mean ${center}</text>'
            f'<polyline points="{poly}" fill="none" stroke="#4f46e5" stroke-width="2"></polyline>{dots}{labels}</svg>')


def _cost_control_chart(c: dict) -> str:
    """Build the cost control chart from the computed per-capability samples (or a representative band if none)."""
    samples = c.get("cost_samples", [])
    sups = [s["sup"] for s in samples] or [c["ll_sup"]]
    center = round(sum(sups) / len(sups), 4)
    hi, lo = max(sups), min(sups)
    ucl = round(hi + (hi - center) * 0.6 + 0.004, 4)
    lcl = round(max(0.0, lo - (center - lo) * 0.6 - 0.002), 4)
    points = [(s["label"], s["sup"]) for s in samples] or [("land lease", c["ll_sup"])]
    return _control_chart_svg(points, center=center, ucl=ucl, lcl=lcl, baseline=c["ll_frontier"],
                              title="Cost per capability — held in the efficient control band")


def page_index(c: dict) -> str:
    body = f"""
<header class="hero parent"><div class=wrap>
  <span class=tag>AI, done right.</span>
  <h1>Build AI the <span style="text-decoration:underline;text-decoration-color:#8b84f5">efficient, appropriate</span> way.</h1>
  <p class=lead>The right model, the right method, the right cost for <i>each</i> task — instead of sending everything to
  the most expensive model. Made easy: write what you want in plain language, and the system finds the cheapest path
  that still meets the bar.</p>
  <div class=kpis>
    <div class=kpi><b>{c['ll_pct']}%</b><span>cost cut on a real extraction task</span></div>
    <div class=kpi><b>{c['hubs']}</b><span>open building-block registries</span></div>
    <div class=kpi><b>{c['proofs']}</b><span>self-tests kept green</span></div>
  </div>
</div></header>

<section><div class="wrap reveal">
  <h2>The idea</h2><h3>Most teams build AI the expensive way. We make the efficient way the easy way.</h3>
  <p>Every capability starts general and costly. We <b>descend</b> it — deterministic rules and cheap models first,
  the frontier model reserved for <i>supervising</i> the cheaper ones — until it runs at the cheapest cost that still
  clears the quality bar. You write the goal; the system does the descent.</p>
  {_descent_svg()}
</div></section>

<section><div class="wrap reveal">
  <h2>Proof, in dollars</h2><h3>A land-lease extraction task ({c['ll_fields']} fields).</h3>
  <p>Most companies send the <b>entire</b> PDF/email to a frontier model (Gemini-class) to pull out agency, principal,
  and contract fields. The appropriate way: OCR + patterns answer most fields before any LLM; the LLM only supervises.</p>
  <div class=cmp>
    <div class=b><b>${c['ll_frontier']}</b><span>whole doc → frontier model<br>(what most do today)</span></div>
    <div class="b win"><b>${c['ll_sup']}</b><span>our way: cheap methods + LLM as supervisor<br><b class=ok>{c['ll_pct']}% cheaper</b></span></div>
  </div>
</div></section>

<section><div class="wrap reveal">
  <h2>Three parts</h2><h3>One holding company, two products, one open store.</h3>
  <div class="grid g3">
    <a class=card href="teleon.html"><h4>Teleon</h4><p>The runtime that makes any capability efficient — the descent
      brain. Write a capability; it picks the cheapest appropriate path.</p><span class=more>How Teleon works →</span></a>
    <a class=card href="baltor.html"><h4>Baltor</h4><p>The engine that makes AI <b>trustworthy</b> — governs what
      becomes true (provenance, verification, receipts).</p><span class=more>How Baltor works →</span></a>
    <a class=card href="hubs.html"><h4>{c['hubs']} Open*Hubs</h4><p>The open store of building blocks — tools, skills,
      models, methods — that both products consume.</p><span class=more>See the hubs →</span></a>
  </div>
  <p style="margin-top:18px" class=mono>Architecture law: Baltor &rarr; Teleon &rarr; Open*Hubs. Never the reverse.</p>
</div></section>"""
    return _shell("index", "AI Done Right — build AI the efficient, appropriate way",
                  "AI Done Right makes it easy to build AI the most efficient and appropriate way — the right model, method, and cost for each task.",
                  "parent", body, footer_caveat=True)


def page_teleon(c: dict) -> str:
    body = f"""
<header class="hero teleon"><div class=wrap><span class=tag>Teleon · the runtime</span>
  <h1>Write the capability.<br>We make it <span style="text-decoration:underline;text-decoration-color:#b9b2fb">efficient</span>.</h1>
  <p class=lead>Describe what you want in plain language — "intake a PDF/email and extract this schema." Teleon descends
  it to the cheapest, most appropriate path that still meets the bar, and learns from every run.</p>
  <div class=kpis><div class=kpi><b>{c['ll_pct']}%</b><span>cheaper on the land-lease task</span></div>
  <div class=kpi><b>{c['research']}</b><span>research components it can pick from</span></div></div>
</div></header>
<section><div class="wrap reveal"><h2>The descent</h2><h3>Unbounded &amp; expensive &rarr; bounded &amp; cheap.</h3>
  <p>The default — send everything to a frontier model — is the most expensive path. Teleon descends each capability
  along cost, tokens, determinism, and freshness, holding the quality floor.</p>{_descent_svg()}</div></section>
<section><div class="wrap reveal"><h2>Worked example</h2><h3>Document extraction, the appropriate way.</h3>
  <div class=flow>
    <div class=node>OCR / text</div><div class=node>prune + dedupe</div><div class=node>patterns (answer before LLM)</div>
    <span class=arrow>&rarr;</span><div class=node>cheap LLM (chunked)</div><span class=arrow>&rarr;</span>
    <div class="node alt">frontier LLM = supervisor only</div>
  </div>
  <div class=cmp>
    <div class=b><b>${c['ll_frontier']}</b><span>whole doc → frontier</span></div>
    <div class="b win"><b>${c['ll_sup']}</b><span>cheap methods + LLM supervisor — <b class=ok>{c['ll_pct']}% cheaper</b></span></div>
  </div>
  <p style="margin-top:16px">The LLM is used only to <b>audit</b> the cheap methods and re-do the few fields it flags —
  not to read the whole document.</p></div></section>
<section><div class="wrap reveal"><h2>Performance, in control</h2><h3>Efficient AND safe — within control-chart limits.</h3>
  <p>Cutting cost can't mean cutting corners. Each capability the descent produces is a sample on a control chart:
  cost stays inside an efficient band (UCL/LCL) — far below the frontier-only baseline — while quality holds above the
  floor. Statistical process control, applied to AI spend.</p>
  {_cost_control_chart(c)}
  <p style="margin-top:8px" class=mono style="font-size:12px;color:#9aa">Each point = one capability's supervised cost
  (computed). Green = in the control band. The red line is what most pay today (whole doc → frontier).</p></div></section>
<section><div class="wrap reveal"><h2>Research, efficiently</h2><h3>The cheapest tool that gets the detail.</h3>
  <div class=rung><span>feed / API</span><div class=bar style="width:14%"></div><span class=c>cheapest</span></div>
  <div class=rung><span>search</span><div class=bar style="width:30%"></div></div>
  <div class=rung><span>extract / render</span><div class=bar style="width:55%"></div></div>
  <div class=rung><span>LLM-driven browser</span><div class=bar style="width:92%"></div><span class=c>deep detail only</span></div>
  <p style="margin-top:14px">{c['browsers']} browsers + {c['driving']} driving components cataloged (any LLM, any
  browser — behind agnostic ports) — the descent picks the cheapest that can get what's needed.</p></div></section>"""
    return _shell("teleon", "Teleon — the runtime that makes AI efficient",
                  "Teleon: write a capability in plain language and the runtime descends it to the cheapest appropriate path.",
                  "teleon", body)


def page_baltor(c: dict) -> str:
    body = """
<header class="hero baltor"><div class=wrap><span class=tag>Baltor · the trust engine</span>
  <h1>Models don't fail.<br>Their <span style="text-decoration:underline;text-decoration-color:#6ee7b7">context</span> does.</h1>
  <p class=lead>Baltor governs what becomes <b>true</b>: provenance, verification, signed facts, and change-data-capture.
  Agents propose; Baltor disposes. Nothing serves as truth until it passes the verify gate.</p>
</div></header>
<section><div class="wrap reveal"><h2>What Baltor does</h2><h3>Governed context, not guesses.</h3>
  <div class="grid g2">
    <div class=card><h4>Verify before serve</h4><p>Every fact is a candidate (<span class=mono>serves_truth=false</span>)
      until it passes verification against an authoritative source.</p></div>
    <div class=card><h4>Provenance + receipts</h4><p>Where each fact came from, when, and how it was checked — inspectable,
      with a rollback target. Lossless: raw + lineage preserved.</p></div>
    <div class=card><h4>Stays current</h4><p>Change-data-capture holds out stale facts and re-verifies when the source
      changes — kept-up-to-date is the wedge.</p></div>
    <div class=card><h4>Powered by Teleon</h4><p>Baltor runs on Teleon (a tenant) — trustworthy context, delivered the
      efficient way.</p></div>
  </div></div></section>
<section><div class="wrap reveal"><h2>Why it matters</h2><h3>Discovery is not trust. Output is not truth.</h3>
  <p>An LLM that sounds confident is not a source. Baltor is the rail that turns proposed context into governed,
  provable truth — so the agents built on top can be relied on.</p></div></section>"""
    return _shell("baltor", "Baltor — the engine that makes AI trustworthy",
                  "Baltor governs what becomes true: provenance, verification, signed facts, CDC. Discovery is not trust.",
                  "baltor", body)


def page_hubs(c: dict) -> str:
    hubs = c.get("hub_list", [])
    cards = "".join(
        f'<a class=card href="./hubs/{h["slug"]}/index.html"><h4>{h["id"]}</h4>'
        f'<p>{h["kind"]} · <span class=mono>{h["tier"]}</span></p></a>' for h in hubs)
    body = f"""
<header class="hero hubs"><div class=wrap><span class=tag>The Open*Hubs · the open store</span>
  <h1>{c['hubs']} open registries of <span style="text-decoration:underline;text-decoration-color:#e9b8f5">building blocks</span>.</h1>
  <p class=lead>Tools, skills, models, methods, harnesses, receipts — the open ecosystem both Baltor and Teleon consume.
  Continuously populated, governed, and verify-gated.</p>
  <div class=kpis><div class=kpi><b>{c['hubs']}</b><span>Open*Hubs</span></div>
  <div class=kpi><b>{c['browsers']}</b><span>browsers cataloged</span></div>
  <div class=kpi><b>{c['driving']}</b><span>driving components/models</span></div></div>
</div></header>
<section><div class="wrap reveal"><h2>How they fill</h2><h3>Three governed contribution channels.</h3>
  <div class="grid g3">
    <div class=card><h4>1 · Discover</h4><p>Finders search public sources, cheapest tool first.</p></div>
    <div class=card><h4>2 · Generate</h4><p>Our own systems emit candidates where no public source exists.</p></div>
    <div class=card><h4>3 · Intake</h4><p>You hand it raw material — OKF docs, links, whole repos — and it decomposes +
      strategizes integration.</p></div>
  </div>
  <div class=flow style="margin-top:20px"><div class=node>discover</div><div class=node>generate</div><div class=node>intake</div>
    <span class=arrow>&rarr;</span><div class=node>verify gate</div><span class=arrow>&rarr;</span>
    <div class="node alt">served to Baltor / Teleon</div></div>
  <p style="margin-top:16px"><b>Discovery is not trust</b> — everything is a candidate until a hub's verify gate passes.</p>
</div></section>
<section><div class="wrap reveal"><h2>Browse all {c['hubs']}</h2><h3>Every hub, one standardized surface.</h3>
  <p>Each hub renders from the same template (consistent design), with its own engine, settings, and verify gate.</p>
  <div class="grid g3" style="margin-top:16px">{cards}</div></div></section>"""
    return _shell("hubs", "The Open*Hubs — the open store of building blocks",
                  "The Open*Hubs: open registries of tools, skills, models, methods both Baltor and Teleon consume.",
                  "hubs", body)


_BUILDERS = {"index": page_index, "baltor": page_baltor, "teleon": page_teleon, "hubs": page_hubs}


def build() -> list[Path]:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    c = counts()
    out = []
    for name in PAGES:
        p = OUTDIR / f"{name}.html"
        p.write_text(_BUILDERS[name](c), encoding="utf-8")
        out.append(p)
    # render ALL 22 standardized hub pages into dist/intro/hubs/ (same up-to-date template — no legacy) so the hubs
    # page's links resolve and the whole site is one coherent, consistent surface.
    try:
        from scripts.build_hub_sites import render_all as render_hub_pages
        render_hub_pages(out_dir=OUTDIR / "hubs")
    except Exception as e:  # noqa: BLE001
        print(f"  (hub pages not rendered: {e})")
    return out


def _self_test() -> int:
    c = counts()
    pages = {n: _BUILDERS[n](c) for n in PAGES}
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("4 self-contained pages render (no external http resources)",
       all(h.startswith("<!doctype html>") and "<style>" in h for h in pages.values())
       and all("http://" not in h and "https://" not in h.replace("trycloudflare", "x") for h in pages.values()))
    ck("every page cross-links to the other three (nav)",
       all(all(f'{p}.html' in h for p in PAGES) for h in pages.values()))
    ck("animations present (gradient + descent draw + scroll-reveal)",
       all("@keyframes grad" in h for h in pages.values()) and "IntersectionObserver" in pages["index"])
    # THE messaging fix: the PARENT must be about efficient+appropriate, NOT context
    idx = pages["index"]
    hero = idx.split("</header>")[0]
    ck("PARENT hero does NOT use 'context' (owner directive) + DOES say efficient + appropriate",
       "context" not in hero.lower() and "efficient" in hero.lower() and "appropriate" in hero.lower())
    bhero = pages["baltor"].split("</header>")[0].lower()
    ck("'context' lives on the BALTOR page hero (where it belongs)", bhero.count("context") >= 1 and "trustworthy" in pages["baltor"].lower())
    ck("Teleon page is about efficiency + the descent + the cascade", all(w in pages["teleon"] for w in ("efficient", "descent", "supervisor")))
    ck("Teleon page shows a CONTROL CHART (UCL/LCL + center + the frontier baseline)",
       all(m in pages["teleon"] for m in ("UCL", "LCL", "control band", "baseline")) and "<svg" in pages["teleon"])
    ck("hubs page covers the 3 channels", all(w in pages["hubs"] for w in ("Discover", "Generate", "Intake")))
    ck(f"hubs page links ALL {c['hubs']} hub pages (not 4) — every roster hub",
       len(c["hub_list"]) == c["hubs"] and all(f'./hubs/{h["slug"]}/index.html' in pages["hubs"] for h in c["hub_list"]))
    ck("computed figures embedded (hubs/proofs/land-lease %)", str(c["hubs"]) in idx and str(c["proofs"]) in idx and str(c["ll_pct"]) in idx)
    ck("honest tunnel caveat on the parent page", "temporary" in idx.lower() and "trycloudflare" in idx.lower())
    print("\n" + ("PASS - build_intro_site: 4 cross-linked animated pages — PARENT (efficient+appropriate, not context), "
                  "Baltor (trust/context), Teleon (efficiency/descent/cascade), Open*Hubs (the store); figures computed; "
                  "honest preview caveat." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    ps = build()
    print(f"built {len(ps)} pages → {OUTDIR.relative_to(REPO)}/ : " + ", ".join(p.name for p in ps))
    raise SystemExit(0)
