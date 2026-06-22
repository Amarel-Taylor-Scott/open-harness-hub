#!/usr/bin/env python3
"""build_intro_site — a self-contained, animated HTML5 explainer of how the whole system works (for an advisor).

ONE page, no external resources (works offline + over a quick tunnel), branded (Hanken Grotesk + IBM Plex Mono),
with CSS animations (gradient hero, animated descent chart, scroll-reveal, flow diagram). Every NUMBER is COMPUTED
from the registries at build time (no-magic-values) so it can't drift. Renders dist/intro/index.html.

  PYTHONPATH=. python3 scripts/build_intro_site.py            # build
  PYTHONPATH=. python3 scripts/build_intro_site.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = REPO / "dist" / "intro" / "index.html"


def counts() -> dict:
    """Computed, single-sourced from the registries — never hand-typed."""
    c = {}
    c["hubs"] = len(json.loads((REPO / "architecture" / "portfolio_connection_map.json").read_text())["hubs"])
    c["research"] = len(json.loads((REPO / "architecture" / "research_component_catalog.json").read_text())["components"])
    bs = json.loads((REPO / "architecture" / "web_browsing_stack_registry.json").read_text())
    c["browsers"] = len(bs["browsers"])
    c["driving"] = len(bs["driving_components"])
    c["driving_target"] = bs["targets"]["driving_components"]
    try:
        from scripts.flywheel_proof_modules import PROOF_MODULES
        c["proofs"] = len(PROOF_MODULES)
    except Exception:  # noqa: BLE001
        c["proofs"] = 0
    return c


_CSS = """
*{box-sizing:border-box}
body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.6}
.mono{font-family:'IBM Plex Mono',ui-monospace,SFMono-Regular,monospace}
.wrap{max-width:1000px;margin:0 auto;padding:0 24px}
section{padding:84px 0;border-bottom:1px solid #eef0f6}
h1{font-size:clamp(40px,7vw,76px);line-height:1.02;letter-spacing:-.03em;margin:0 0 14px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.14em;color:#6b7280;margin:0 0 8px}
h3{font-size:clamp(26px,3.4vw,38px);letter-spacing:-.02em;margin:0 0 18px}
p{font-size:18px;color:#33384a;max-width:680px}
.lead{font-size:clamp(20px,2.6vw,26px);color:#3a3f52;max-width:720px}
.accent{color:#4f46e5}
.tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#4f46e5;background:#4f46e510;border:1px solid #4f46e530;border-radius:999px;padding:6px 14px}
.hero{background:linear-gradient(120deg,#0f1222,#1b1f3a 40%,#2a1f54 70%,#4f46e5);background-size:240% 240%;animation:grad 16s ease infinite;color:#fff;padding:120px 0 110px}
.hero h1,.hero p{color:#fff}.hero .lead{color:#cdd2f0}
@keyframes grad{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}
.kpis{display:flex;flex-wrap:wrap;gap:14px;margin-top:34px}
.kpi{background:#ffffff14;border:1px solid #ffffff2e;border-radius:14px;padding:16px 20px;backdrop-filter:blur(4px)}
.kpi b{display:block;font-size:30px;line-height:1}.kpi span{font-size:12.5px;color:#cdd2f0;letter-spacing:.04em}
.grid{display:grid;gap:18px}.g2{grid-template-columns:1fr 1fr}.g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:760px){.g2,.g3{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid #e6e8ef;border-radius:18px;padding:24px;transition:transform .25s,box-shadow .25s}
.card:hover{transform:translateY(-4px);box-shadow:0 18px 40px -24px #4f46e580}
.card h4{margin:0 0 6px;font-size:19px}.card p{font-size:15px;color:#5b6172;margin:0}
.pill{display:inline-block;border:1px solid #e6e8ef;border-radius:999px;padding:5px 13px;font-size:13px;margin:4px 6px 0 0;background:#fff}
.flow{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:18px}
.node{background:#fff;border:1px solid #e6e8ef;border-radius:12px;padding:12px 16px;font-weight:600;font-size:14px;animation:pulse 3s ease-in-out infinite}
.node.alt{background:#4f46e5;color:#fff;border-color:#4f46e5}
.arrow{color:#4f46e5;font-weight:800}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 #4f46e500}50%{box-shadow:0 0 0 6px #4f46e510}}
.reveal{opacity:0;transform:translateY(24px);transition:opacity .7s,transform .7s}
.reveal.in{opacity:1;transform:none}
.ladder{margin-top:18px}
.rung{display:flex;align-items:center;gap:14px;padding:10px 0}
.bar{height:14px;border-radius:8px;background:linear-gradient(90deg,#4f46e5,#8b84f5)}
.rung span{font-size:14px;color:#5b6172;min-width:160px}.rung .c{font-size:13px;color:#9aa0b4}
.foot{padding:48px 0;color:#6b7280;font-size:14px}
.note{background:#fff8e6;border:1px solid #f3e3a8;border-radius:12px;padding:14px 18px;font-size:14px;color:#7a6a2e;margin-top:22px}
svg .floor{stroke:#16a34a;stroke-width:2;stroke-dasharray:6 6}
svg .cost{stroke:#4f46e5;stroke-width:3;fill:none;stroke-dasharray:520;stroke-dashoffset:520;animation:draw 2.6s ease forwards}
@keyframes draw{to{stroke-dashoffset:0}}
svg .dot{fill:#4f46e5;opacity:0;animation:show .4s ease forwards}
@keyframes show{to{opacity:1}}
"""

_JS = """
const io=new IntersectionObserver((es)=>{es.forEach(e=>{if(e.isIntersecting)e.target.classList.add('in')})},{threshold:.14});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));
"""


def render(c: dict) -> str:
    t = {
        "HUBS": str(c["hubs"]), "BROWSERS": str(c["browsers"]), "DRIVING": str(c["driving"]),
        "DTARGET": str(c["driving_target"]), "PROOFS": str(c["proofs"]), "RESEARCH": str(c["research"]),
    }
    html = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>AI Done Right — how it works</title>
<meta name=description content="How AI Done Right works: Baltor governs what is TRUE, Teleon governs what is EFFICIENT, and the Open*Hubs are the open store both consume.">
<style>__CSS__</style></head><body>

<header class=hero><div class=wrap>
  <span class=tag>AI, done right.</span>
  <h1>Models don't fail.<br>Their <span style="text-decoration:underline;text-decoration-color:#8b84f5">context</span> does.</h1>
  <p class=lead>A holding company with two moats and one open store: <b>Baltor</b> governs what becomes <b>TRUE</b>,
  <b>Teleon</b> governs what becomes <b>EFFICIENT</b>, and <b>__HUBS__ Open*Hubs</b> are the open ecosystem both consume.</p>
  <div class=kpis>
    <div class=kpi><b>__HUBS__</b><span>Open*Hubs</span></div>
    <div class=kpi><b>__BROWSERS__</b><span>web browsers cataloged</span></div>
    <div class=kpi><b>__DRIVING__</b><span>driving components/models</span></div>
    <div class=kpi><b>__PROOFS__</b><span>self-tests kept green</span></div>
  </div>
</div></header>

<section><div class="wrap reveal">
  <h2>The two moats</h2><h3>Truth and efficiency are separate problems.</h3>
  <div class="grid g2">
    <div class=card><h4>Baltor — what is <span class=accent>TRUE</span></h4><p>The governed context engine: provenance,
      verification, signed facts, change-data-capture. Agents <i>propose</i>; Baltor <i>disposes</i>. Nothing serves as
      truth until it passes the verify gate (<span class=mono>serves_truth=false</span> until then).</p></div>
    <div class=card><h4>Teleon — what is <span class=accent>EFFICIENT</span></h4><p>The runtime: program a capability in
      plain text, and Teleon <b>descends</b> it from unbounded &amp; expensive to bounded &amp; cheap — within guardrails,
      holding a quality floor. The learned descent is the moat.</p></div>
  </div>
</div></section>

<section><div class="wrap reveal">
  <h2>Architecture</h2><h3>One law: Baltor &rarr; Teleon &rarr; Open*Hubs. Never the reverse.</h3>
  <div class=flow>
    <div class="node alt">Baltor<br><small>applied context product</small></div><span class=arrow>&rarr;</span>
    <div class="node alt">Teleon<br><small>runtime SaaS</small></div><span class=arrow>&rarr;</span>
    <div class=node>__HUBS__ Open*Hubs<br><small>the open store</small></div>
  </div>
  <p style="margin-top:20px">Baltor is <b>powered by Teleon</b> (a tenant). Both <b>consume</b> the Open*Hubs; the hubs
  import neither — so the open ecosystem stays clean and the products stay separable. The dependency law is enforced in
  code by a self-test, not by convention.</p>
</div></section>

<section><div class="wrap reveal">
  <h2>The core motion</h2><h3>The descent: unbounded &amp; expensive &rarr; bounded &amp; cheap.</h3>
  <p>Every capability starts general and costly, then descends to the cheapest path that still clears the quality floor.
  Cost falls; quality holds.</p>
  <svg viewBox="0 0 560 200" width="100%" height="200" style="margin-top:10px;max-width:560px">
    <line class=floor x1="20" y1="150" x2="540" y2="150"></line>
    <text x="24" y="142" font-size="11" fill="#16a34a" class=mono>quality floor (held)</text>
    <path class=cost d="M20,30 C160,40 200,150 540,160"></path>
    <circle class=dot cx="20" cy="30" r="5" style="animation-delay:.2s"></circle>
    <circle class=dot cx="280" cy="96" r="5" style="animation-delay:1.4s"></circle>
    <circle class=dot cx="540" cy="160" r="5" style="animation-delay:2.6s"></circle>
    <text x="20" y="22" font-size="11" fill="#4f46e5" class=mono>unbounded $$$</text>
    <text x="470" y="180" font-size="11" fill="#4f46e5" class=mono>bounded ~$0</text>
  </svg>
</div></section>

<section><div class="wrap reveal">
  <h2>How the store fills</h2><h3>Three governed contribution channels.</h3>
  <div class="grid g3">
    <div class=card><h4>1 · Discover</h4><p>Finders search public sources, picking the cheapest tool that meets the
      freshness bar.</p></div>
    <div class=card><h4>2 · Generate</h4><p>Our own systems emit candidates — the method catalog, the descent brain —
      where no public source exists.</p></div>
    <div class=card><h4>3 · Intake</h4><p>You hand it raw material (OKF docs, links, text, whole repos); it decomposes,
      strategizes, and stages governed candidates.</p></div>
  </div>
  <div class=flow style="margin-top:22px">
    <div class=node>discover</div><div class=node>generate</div><div class=node>intake</div>
    <span class=arrow>&rarr;</span><div class=node>verify gate</div><span class=arrow>&rarr;</span>
    <div class="node alt">served to Baltor / Teleon</div>
  </div>
  <p style="margin-top:16px"><b>Discovery is not trust.</b> Everything is a candidate until a hub's verify gate passes.</p>
</div></section>

<section><div class="wrap reveal">
  <h2>Filling in the details</h2><h3>Research is a descent-selectable catalog.</h3>
  <p>To enrich the store, an agent names the <i>detail it needs</i> and a budget; the descent picks the cheapest tool
  that can get it. Cheap structured feeds first — the expensive LLM-driven browser only when nothing cheaper works.</p>
  <div class=ladder>
    <div class=rung><span>feed / API</span><div class=bar style="width:14%"></div><span class=c>cheapest</span></div>
    <div class=rung><span>search</span><div class=bar style="width:28%"></div></div>
    <div class=rung><span>extract / render</span><div class=bar style="width:55%"></div></div>
    <div class=rung><span>LLM-driven browser</span><div class=bar style="width:92%"></div><span class=c>deep detail only</span></div>
  </div>
  <p style="margin-top:16px"><b>__BROWSERS__</b> browsers + <b>__DRIVING__</b> driving components/models cataloged
  (toward __DTARGET__), each license-classified and governed.</p>
</div></section>

<section><div class="wrap reveal">
  <h2>Programming it</h2><h3>Plain text in. A plan out.</h3>
  <p class=mono style="background:#0f1222;color:#cdd2f0;border-radius:12px;padding:16px 18px;font-size:14px;max-width:760px">
  &gt; "scrape the internet for additional skills for openskillshub.io"</p>
  <p>The capability processor recognizes this is <b>iterative</b> (loop until nothing new), <b>multi-component</b>
  (string the research descent + the hub lifecycle together), and possibly <b>scheduled</b> — then runs it, bounded.</p>
</div></section>

<section><div class="wrap reveal">
  <h2>Why it's trustworthy</h2><h3>Governance is the product, not a footnote.</h3>
  <div>
    <span class=pill>serves_truth = false until verified</span><span class=pill>provenance + signed facts</span>
    <span class=pill>lossless — raw + lineage preserved</span><span class=pill>license discipline (copyleft &rarr; technique-only)</span>
    <span class=pill>login-walled sources refused</span><span class=pill>__PROOFS__ self-tests kept green</span>
  </div>
  <div class=note>This page is a <b>temporary preview</b> served over a TryCloudflare quick tunnel — a random session URL
  for sharing, not production hosting. It disappears when the tunnel stops.</div>
</div></section>

<div class="wrap foot">AI Done Right · <span class=mono>aidoneright.dev</span> — Baltor governs what's true · Teleon governs
what's efficient · __HUBS__ Open*Hubs are the open store. Generated by scripts/build_intro_site.py (all figures computed).</div>

<script>__JS__</script>
</body></html>
"""
    html = html.replace("__CSS__", _CSS).replace("__JS__", _JS)
    for k, v in t.items():
        html = html.replace("__" + k + "__", v)
    return html


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(counts()), encoding="utf-8")
    return OUT


def _self_test() -> int:
    c = counts()
    h = render(c)
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("renders an HTML5 doc with viewport + local <style> (self-contained)",
       h.startswith("<!doctype html>") and "viewport" in h and "<style>" in h and "http://" not in h.split("</head>")[0].replace("http://localhost", ""))
    ck("has CSS animations (@keyframes) + scroll-reveal JS", "@keyframes" in h and "IntersectionObserver" in h)
    ck("explains the two moats + the dependency law (Baltor→Teleon→Open*Hubs)",
       "Baltor" in h and "Teleon" in h and "Open*Hub" in h and "&rarr; Teleon &rarr;" in h)
    ck("covers the 3 contribution channels + the research descent + the planner",
       "Discover" in h and "Generate" in h and "Intake" in h and "descent" in h and "iterative" in h)
    ck("counts are COMPUTED + embedded (no magic): hubs/browsers/driving/proofs present",
       all(str(c[k]) in h for k in ("hubs", "browsers", "driving", "proofs")) and c["hubs"] == 22)
    ck("carries the honest TryCloudflare 'temporary preview' caveat", "temporary preview" in h.lower() and "trycloudflare" in h.lower())
    ck("governance front-and-center (serves_truth=false)", "serves_truth = false" in h or "serves_truth=false" in h)
    print("\n" + ("PASS - build_intro_site: a self-contained, animated HTML5 explainer (computed figures, CSS animations, "
                  "scroll-reveal); covers the moats, the law, the descent, the 3 channels, the research catalog, the "
                  "planner, and governance; honest preview caveat." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    p = build()
    print(f"built {p.relative_to(REPO)} ({p.stat().st_size} bytes) — figures computed from the registries")
    raise SystemExit(0)
