#!/usr/bin/env python3
"""scripts.surface_server — the ONE standardized, config-driven website server for the whole family.

Owner 2026-06-25/26: replaces the fragmented per-surface site systems with a SINGLE canonical scaffolding that
renders ALL FIVE product surfaces (AI Done Right · Teleon.dev · AIDevObserver · Baltor.ai · Open*Hubs) from ONE
template — every surface ships BYTE-IDENTICAL CSS, differing only by the per-surface `--accent` and the copy read
from config. Nothing here is hand-typed that lives elsewhere (No-Magic-Values):

  * surface ids + brand + role + capabilities  ← architecture/surface_capability_spec.json (pillars[])
  * the per-surface accent                      ← scripts._surface_accents.accent()
  * the BYO-key demos + their runner            ← src.teleon.demos.byo_key_demo (DEMOS, run_byo_demo)
  * the demo example prompts                     ← scripts.byo_demo_server.EXAMPLE (existing copy, not re-invented)
  * the faceted browse data + counts            ← src.teleon.registry.browse (browse, FACET_DIMS)
  * cross-surface nav URLs                       ← dist/surface-urls.json (written later by the launcher; robust if absent)

Routes (ONE handler, every surface): GET / (home — hub portfolio index for ai-done-right), GET /demo
(the surface's BYO-key demo in the canonical design), POST /run ({demo,byo_key,inputs} → run_byo_demo → JSON,
governed: key never stored/echoed), GET /browse (open-star-hubs only — the faceted browse), GET /favicon.ico (204).
serves_truth=false everywhere (candidate output; only Baltor's governed source answers serve truth).

  python3 scripts/surface_server.py <surface-id> [--port N]      # surface-id ∈ the 5 ids
"""
from __future__ import annotations

import http.server
import html as _html
import json
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts._surface_accents import accent as _acc  # noqa: E402  (single-source per-surface accent)
from scripts.byo_demo_server import EXAMPLE as _EXAMPLES  # noqa: E402  (reuse existing demo example copy)
from src.teleon.demos.byo_key_demo import DEMOS, run_byo_demo  # noqa: E402  (reuse the governed BYO-key plane)
from src.teleon.registry.browse import FACET_DIMS, browse  # noqa: E402  (reuse the faceted browse + counts)

SPEC = REPO / "architecture" / "surface_capability_spec.json"
SURFACE_URLS_FILE = REPO / "dist" / "surface-urls.json"

# Cross-surface nav FALLBACK ports — used only when dist/surface-urls.json (the public/tunnel URLs) is absent and a
# surface link would otherwise have nowhere to point. One default per surface id; the launcher's real URLs win.
DEFAULT_PORTS: dict[str, int] = {
    "ai-done-right": 8001, "teleon": 8002, "aidevobserver": 8003, "baltor": 8004, "open-star-hubs": 8005,
}
HTML = "text/html; charset=utf-8"
PARENT_ID = "ai-done-right"  # the holding/portfolio brand whose home is the portfolio index


# ───────────────────────────── config (single source) ─────────────────────────────
def _spec() -> dict:
    return json.loads(SPEC.read_text(encoding="utf-8"))


def pillars() -> list[dict]:
    return _spec().get("pillars", [])


def surface_ids() -> list[str]:
    return [p["id"] for p in pillars()]


def pillar(surface_id: str) -> dict:
    return next((p for p in pillars() if p["id"] == surface_id), {})


def demo_key(surface_id: str) -> str | None:
    """The byo_key_demo key for a surface (== the surface id for the 4 product surfaces; None for the parent hub)."""
    return surface_id if surface_id in DEMOS else None


def _surface_urls() -> dict:
    """The public/tunnel URL per surface id, written later by the launcher. {} if not present yet (robust)."""
    try:
        data = json.loads(SURFACE_URLS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 — absent/partial file must never break a page
        return {}


def surface_href(target_id: str, current_id: str, urls: dict | None = None) -> str:
    """Where a nav/footer link to `target_id` points: same-origin '/' for the current surface, else its public URL
    from surface-urls.json, else the localhost fallback port. Robust to a missing file/key."""
    if target_id == current_id:
        return "/"
    urls = _surface_urls() if urls is None else urls
    return urls.get(target_id) or f"http://localhost:{DEFAULT_PORTS.get(target_id, 8000)}/"


# ───────────────────────────── the ONE shared stylesheet ─────────────────────────────
# This is THE standardization point: every surface embeds surface_css(accent), which is this template with the single
# `__ACCENT__` token replaced by the per-surface hex. The accent appears EXACTLY once, so the rendered CSS is
# byte-identical across all five surfaces except that one value (asserted by check_surface_server.py). Canonical
# light/Inter tokens from dist/sites/aidoneright-design/shared/oh-tokens.css (dir-a, theme-light).
_CSS_TEMPLATE = """
:root{
  --bg:#faf7f0; --bg-subtle:#f3eee2; --surface:#fffdf8; --fg:#1c1b19;
  --fg-muted:#6b675e; --fg-faint:#868074; --border:#e7e0d2;
  --accent:__ACCENT__; --accent-ink:#ffffff;
  --r-sm:8px; --r-md:12px; --r-lg:18px; --maxw:1080px;
  --shadow-sm:0 1px 2px rgba(60,40,20,.05); --shadow-md:0 14px 38px rgba(60,40,20,.12);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:"Inter",-apple-system,"Segoe UI",system-ui,sans-serif;background:var(--bg);color:var(--fg);
  line-height:1.6;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
.mono{font-family:ui-monospace,SFMono-Regular,monospace}
.wrap{max-width:var(--maxw);margin:0 auto;padding:0 1.4rem}

/* sticky top nav */
.nav{position:sticky;top:0;z-index:50;background:rgba(250,247,240,.82);
  backdrop-filter:saturate(180%) blur(12px);-webkit-backdrop-filter:saturate(180%) blur(12px);
  border-bottom:1px solid var(--border)}
.nav-inner{max-width:var(--maxw);margin:0 auto;padding:.7rem 1.4rem;display:flex;align-items:center;
  justify-content:space-between;gap:1rem;flex-wrap:wrap}
.nav-brand{font-weight:800;font-size:1.02rem;letter-spacing:-.01em;color:var(--fg);display:flex;align-items:center;gap:.5rem}
.nav-brand:hover{text-decoration:none}
.nav-dot{width:11px;height:11px;border-radius:3px;background:var(--accent);display:inline-block}
.nav-links{display:flex;gap:.25rem;flex-wrap:wrap}
.nav-link{padding:.4rem .72rem;border-radius:var(--r-sm);color:var(--fg-muted);font-size:.88rem;font-weight:500}
.nav-link:hover{background:var(--bg-subtle);color:var(--fg);text-decoration:none}
.nav-link.active{color:var(--accent);background:var(--surface);border:1px solid var(--border)}

/* hero */
.hero{padding:4.6rem 0 3rem}
.eyebrow{display:inline-block;font-family:ui-monospace,SFMono-Regular,monospace;font-size:.72rem;
  text-transform:uppercase;letter-spacing:.16em;color:var(--accent);border:1px solid var(--border);
  background:var(--surface);border-radius:999px;padding:.35rem .85rem;margin-bottom:1.4rem}
.hero h1{font-size:clamp(2.3rem,5.2vw,3.7rem);line-height:1.04;letter-spacing:-.028em;margin:0 0 1rem;font-weight:800}
.hero .lede{font-size:clamp(1.05rem,2vw,1.3rem);color:var(--fg-muted);max-width:46ch;margin:0 0 2rem}
.cta-row{display:flex;gap:.8rem;flex-wrap:wrap;align-items:center}
.pills{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:1.8rem}
.pill{font-size:.78rem;color:var(--fg-muted);background:var(--surface);border:1px solid var(--border);
  border-radius:999px;padding:.3rem .75rem}

/* buttons */
.btn{display:inline-flex;align-items:center;gap:.45rem;font-weight:600;font-size:.96rem;padding:.74rem 1.35rem;
  border-radius:var(--r-sm);border:1px solid transparent;cursor:pointer;transition:transform .05s ease,box-shadow .15s ease}
.btn:hover{text-decoration:none;transform:translateY(-1px)}
.btn:active{transform:translateY(0)}
.btn-accent{background:var(--accent);color:var(--accent-ink);box-shadow:var(--shadow-sm)}
.btn-accent:hover{box-shadow:var(--shadow-md)}
.btn-ghost{background:var(--surface);color:var(--fg);border-color:var(--border)}

/* sections + cards */
.section{padding:1.4rem 0 3.2rem}
.section-head{margin:0 0 1.5rem}
.section-head h2{font-size:1.55rem;letter-spacing:-.02em;margin:0 0 .35rem;font-weight:700}
.section-head p{color:var(--fg-muted);margin:0;max-width:62ch}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(252px,1fr));gap:1rem}
.card{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:1.35rem;
  box-shadow:var(--shadow-sm);transition:box-shadow .15s ease,border-color .15s ease,transform .05s ease;display:block}
.card:hover{box-shadow:var(--shadow-md);border-color:var(--accent);text-decoration:none}
a.card:hover{transform:translateY(-2px)}
.card .idx{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.72rem;color:var(--accent);font-weight:700;
  letter-spacing:.03em;text-transform:lowercase}
.card h3{font-size:1.1rem;margin:.5rem 0 .35rem;color:var(--fg);letter-spacing:-.01em;line-height:1.25}
.card p{margin:0;color:var(--fg-muted);font-size:.93rem}
.card .role{margin:.45rem 0 0;color:var(--fg-muted);font-size:.93rem;line-height:1.5}
.card .arrow{color:var(--accent);font-weight:600;font-size:.88rem;margin-top:.85rem;display:inline-block}

/* demo */
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-lg);padding:1.9rem;
  box-shadow:var(--shadow-sm);max-width:700px}
.field{margin:1.15rem 0 0}
label{display:block;font-size:.82rem;font-weight:600;color:var(--fg-muted);margin:0 0 .4rem}
input,textarea{width:100%;background:var(--bg);color:var(--fg);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:.72rem .82rem;font:14px "Inter",-apple-system,system-ui,sans-serif}
input:focus,textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px var(--bg-subtle)}
textarea{min-height:108px;resize:vertical}
.mono-in{font-family:ui-monospace,SFMono-Regular,monospace;font-size:13px}
.note{font-size:.77rem;color:var(--fg-faint);margin:.5rem 0 0;line-height:1.5}
.out{margin-top:1.4rem;border:1px solid var(--border);border-radius:var(--r-md);background:var(--bg-subtle);
  padding:1rem 1.1rem;display:none;white-space:pre-wrap;word-break:break-word;
  font:12.5px ui-monospace,SFMono-Regular,monospace;color:var(--fg)}

/* browse */
.search-row{display:flex;gap:.6rem;margin:0 0 1.5rem;flex-wrap:wrap}
.search-row input{flex:1;min-width:220px}
.active-filters{display:flex;flex-wrap:wrap;gap:.4rem;margin:0 0 1.2rem}
.browse-layout{display:grid;grid-template-columns:248px 1fr;gap:1.7rem;align-items:start}
.facets{display:flex;flex-direction:column;gap:1.4rem;position:sticky;top:5rem}
.facet h3{font-size:.71rem;text-transform:uppercase;letter-spacing:.09em;color:var(--fg-faint);margin:0 0 .55rem}
.fvals{display:flex;flex-direction:column;gap:1px}
.fv{display:flex;justify-content:space-between;gap:.6rem;align-items:center;padding:.3rem .55rem;border-radius:var(--r-sm);
  color:var(--fg-muted);font-size:.86rem;border:1px solid transparent}
.fv:hover{background:var(--surface);color:var(--fg);text-decoration:none}
.fv.on{background:var(--surface);border-color:var(--accent);color:var(--accent);font-weight:600}
.fv .ct{font-family:ui-monospace,SFMono-Regular,monospace;font-size:.74rem;color:var(--fg-faint)}
.fv.on .ct{color:var(--accent)}
.fmore{font-size:.74rem;color:var(--fg-faint);padding:.2rem .55rem}
.rcount{color:var(--fg-muted);font-size:.9rem;margin:0 0 .9rem}
.rcount b{color:var(--fg)}
.reclist{display:grid;grid-template-columns:repeat(auto-fill,minmax(244px,1fr));gap:.85rem}
.rec{background:var(--surface);border:1px solid var(--border);border-radius:var(--r-md);padding:1rem 1.1rem}
.rec:hover{border-color:var(--accent)}
.rec-head{display:flex;justify-content:space-between;gap:.6rem;align-items:flex-start;margin-bottom:.4rem}
.rid{font-family:ui-monospace,SFMono-Regular,monospace;font-weight:700;font-size:.86rem;word-break:break-word;color:var(--fg)}
.holds{color:var(--fg-muted);font-size:.85rem;margin-bottom:.45rem}
.badge{font-size:.63rem;text-transform:uppercase;letter-spacing:.05em;padding:.16rem .5rem;border-radius:999px;
  border:1px solid var(--border);color:var(--fg-muted);white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:.3rem}
.chip{font-size:.72rem;background:var(--bg-subtle);color:var(--fg-muted);border-radius:999px;padding:.16rem .58rem}
.chip a{color:var(--fg-muted)}

/* footer */
.footer{border-top:1px solid var(--border);margin-top:3rem;padding:2.2rem 0 3rem;color:var(--fg-faint);font-size:.85rem}
.foot-links{display:flex;gap:1.1rem;flex-wrap:wrap;margin-top:.7rem}
.foot-links a{color:var(--fg-muted);font-size:.86rem}
.foot-truth{margin-top:1.1rem;font-size:.76rem}

@media(max-width:760px){
  .browse-layout{grid-template-columns:1fr}
  .facets{position:static}
  .hero{padding:3.1rem 0 2rem}
}
"""

_GOOGLE_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">'
)

# the /demo run script — built by .replace (brace-safe) so the surface key + observer input-shape are injected.
_RUN_JS = r"""
async function run(){
  var o=document.getElementById('out'); o.style.display='block'; o.textContent='Running…';
  var prompt=document.getElementById('prompt').value;
  var keyEl=document.getElementById('key'); var byo_key=keyEl?keyEl.value:'';
  var inputs = __OBS__ ? {messages:[{role:'user',content:prompt}]} : {prompt:prompt};
  try{
    var r=await fetch('/run',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({demo:'__KEY__',byo_key:byo_key,inputs:inputs})});
    var j=await r.json(); o.textContent=JSON.stringify(j,null,2);
  }catch(e){ o.textContent='Error: '+e; }
}
"""


def esc(s: object) -> str:
    return _html.escape("" if s is None else str(s), quote=True)


def surface_css(accent: str) -> str:
    """The ONE canonical stylesheet with this surface's accent injected (the only per-surface difference)."""
    return _CSS_TEMPLATE.replace("__ACCENT__", accent)


def _cap(text: str) -> str:
    """Capitalize the first letter of a capability label for display, without mangling the rest (CamelCase, slashes)."""
    return text[:1].upper() + text[1:] if text else text


# ───────────────────────────── shared chrome (nav · footer · page) ─────────────────────────────
def nav(current_id: str) -> str:
    urls = _surface_urls()
    cur = pillar(current_id)
    links = "".join(
        f'<a class="nav-link{" active" if p["id"] == current_id else ""}" '
        f'href="{esc(surface_href(p["id"], current_id, urls))}">{esc(p["brand"])}</a>'
        for p in pillars()
    )
    return (
        '<nav class="nav"><div class="nav-inner">'
        f'<a class="nav-brand" href="/"><span class="nav-dot"></span>{esc(cur.get("brand", current_id))}</a>'
        f'<div class="nav-links">{links}</div>'
        "</div></nav>"
    )


def footer(current_id: str) -> str:
    urls = _surface_urls()
    parent = pillar(PARENT_ID).get("brand", "AI Done Right")
    fl = "".join(
        f'<a href="{esc(surface_href(p["id"], current_id, urls))}">{esc(p["brand"])}</a>' for p in pillars()
    )
    return (
        '<footer class="footer"><div class="wrap">'
        f"<div>{esc(parent)} — one standardized surface server · five product surfaces, one design system.</div>"
        f'<div class="foot-links">{fl}</div>'
        '<div class="foot-truth mono">serves_truth = false · candidate output, not verified truth · '
        "a BYO key is used only for the request, never stored or logged.</div>"
        "</div></footer>"
    )


def page(current_id: str, title: str, body: str) -> str:
    accent = _acc(current_id)
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        f"<title>{esc(title)}</title>{_GOOGLE_FONTS}"
        f"<style>{surface_css(accent)}</style></head><body>"
        f"{nav(current_id)}{body}{footer(current_id)}"
        "</body></html>"
    )


def _hero(eyebrow: str, h1: str, lede: str, cta: str, pills: str = "") -> str:
    return (
        '<header class="hero"><div class="wrap">'
        f'<span class="eyebrow">{esc(eyebrow)}</span>'
        f"<h1>{esc(h1)}</h1><p class=\"lede\">{esc(lede)}</p>"
        f'<div class="cta-row">{cta}</div>{pills}'
        "</div></header>"
    )


def _section(title: str, sub: str, inner: str, anchor: str = "") -> str:
    aid = f' id="{esc(anchor)}"' if anchor else ""
    return (
        f'<section class="section"{aid}><div class="wrap">'
        f'<div class="section-head"><h2>{esc(title)}</h2><p>{esc(sub)}</p></div>'
        f"{inner}</div></section>"
    )


# ───────────────────────────── home ─────────────────────────────
def _cap_cards(caps: list[str]) -> str:
    cards = "".join(
        f'<div class="card"><div class="idx">{i:02d}</div><h3>{esc(_cap(c))}</h3></div>'
        for i, c in enumerate(caps, 1)
    )
    return f'<div class="cards">{cards}</div>'


def _render_hub_home(p: dict) -> str:
    """ai-done-right home = the PORTFOLIO INDEX: a card per other surface + a short parent intro."""
    urls = _surface_urls()
    others = [q for q in pillars() if q["id"] != PARENT_ID]
    cards = "".join(
        f'<a class="card surface-card" href="{esc(surface_href(q["id"], PARENT_ID, urls))}">'
        f'<div class="idx">{esc(q["id"])}</div><h3>{esc(q["brand"])}</h3>'
        f'<p class="role">{esc(q["role"])}</p>'
        f'<span class="arrow">Visit {esc(q["brand"])} &rarr;</span></a>'
        for q in others
    )
    pills = "".join(f'<span class="pill">{esc(_cap(c))}</span>' for c in p.get("capabilities", []))
    cta = (
        '<a class="btn btn-accent" href="#portfolio">Explore the portfolio &darr;</a>'
        '<a class="btn btn-ghost" href="/demo">See the demos &rarr;</a>'
    )
    hero = _hero("The portfolio", p["brand"], p["role"], cta,
                 f'<div class="pills">{pills}</div>' if pills else "")
    portfolio = _section("The portfolio", "Four product surfaces, one design system — pick where to go.",
                         f'<div class="cards">{cards}</div>', anchor="portfolio")
    return page(PARENT_ID, f'{p["brand"]} — the portfolio', hero + portfolio)


def render_home(surface_id: str) -> str:
    p = pillar(surface_id)
    if surface_id == PARENT_ID:
        return _render_hub_home(p)
    parent_brand = pillar(PARENT_ID).get("brand", "AI Done Right")
    has_demo = demo_key(surface_id) is not None
    is_hubs = surface_id == "open-star-hubs"
    cta_parts = []
    if has_demo:
        cta_parts.append('<a class="btn btn-accent" href="/demo">Try the live demo &rarr;</a>')
    if is_hubs:
        cta_parts.append('<a class="btn btn-ghost" href="/browse">Browse the catalog &rarr;</a>')
    cta_parts.append('<a class="btn btn-ghost" href="#capabilities">What it does &darr;</a>')
    hero = _hero(parent_brand, p["brand"], p["role"], "".join(cta_parts))
    caps = _section("Capabilities", f'The surfaces and functions {p["brand"]} ships.',
                    _cap_cards(p.get("capabilities", [])), anchor="capabilities")
    extra = ""
    if is_hubs:
        extra = _section(
            "Browse every record",
            "One catalog, the registry/record is the unit, hubs are flexible facets — "
            "filter by category, type, kind, layer, and status.",
            '<a class="btn btn-accent" href="/browse">Open the faceted browse &rarr;</a>',
        )
    return page(surface_id, f'{p["brand"]} — {p["role"][:60]}', hero + caps + extra)


# ───────────────────────────── demo ─────────────────────────────
def _render_demo_index(p: dict) -> str:
    """ai-done-right /demo = a 'pick a surface' index linking each surface's own /demo (governed copy included)."""
    urls = _surface_urls()
    cards = "".join(
        f'<a class="card" href="{esc(surface_href(sid, PARENT_ID, urls).rstrip("/") + "/demo")}">'
        f'<div class="idx">/demo</div><h3>{esc(pillar(sid)["brand"])}</h3>'
        f'<p>{esc(DEMOS[sid]["label"])}</p><span class="arrow">Open the demo &rarr;</span></a>'
        for sid in surface_ids() if sid in DEMOS
    )
    hero = _hero("Demos", "Pick a surface to try",
                 "Every surface ships a demo you can run with your own API key. "
                 "Keys are used only for the request and are never stored.",
                 '<a class="btn btn-ghost" href="/">&larr; Back to the portfolio</a>')
    return page(PARENT_ID, f'{p["brand"]} — demos', hero + _section(
        "Live demos", "Bring your own key — never stored.", f'<div class="cards">{cards}</div>'))


def render_demo(surface_id: str) -> str:
    p = pillar(surface_id)
    key = demo_key(surface_id)
    if key is None:  # parent hub → pick-a-surface index
        return _render_demo_index(p)
    d = DEMOS[key]
    needs = bool(d["needs_key"])
    example = _EXAMPLES.get(key, "")
    is_obs = key == "aidevobserver"
    keyfield = ""
    if needs:
        keyfield = (
            '<div class="field"><label>Your API key (required)</label>'
            '<input class="mono-in" id="key" type="password" autocomplete="off" '
            'placeholder="sk-… or your provider key"></div>'
        )
    governed = (
        '<p class="note">Used only for this request &middot; never stored &middot; never logged. '
        "Only a redacted status (sk-…1234) is ever shown.</p>"
    )
    if not needs:
        governed = (
            '<p class="note">No API key needed — this reviews a sample AI session. '
            "Your input is used only for this request &middot; never stored &middot; never logged.</p>"
        )
    run_label = "Run with my key &rarr;" if needs else "Run the demo &rarr;"
    eyebrow = "/demo · bring your own key" if needs else "/demo · no key needed"
    panel = (
        '<div class="panel">'
        f"{keyfield}"
        '<div class="field"><label>Prompt</label>'
        f'<textarea class="mono-in" id="prompt">{esc(example)}</textarea></div>'
        f"{governed}"
        f'<button class="btn btn-accent" style="margin-top:1.2rem" onclick="run()">{run_label}</button>'
        '<div class="out" id="out"></div>'
        "</div>"
    )
    js = _RUN_JS.replace("__OBS__", "true" if is_obs else "false").replace("__KEY__", key)
    hero = _hero(eyebrow, p["brand"], d["label"] + ".",
                 '<a class="btn btn-ghost" href="/">&larr; Back to ' + esc(p["brand"]) + "</a>")
    body = hero + _section("Try it", "Bring your own key — it never leaves this request.", panel) + f"<script>{js}</script>"
    return page(surface_id, f'{p["brand"]} — /demo', body)


def _run_request(req: dict) -> dict:
    """The POST /run logic (factored so the self-test exercises it without a socket): run the GOVERNED BYO-key plane.
    Never stores or echoes the raw key — run_byo_demo returns only a redacted status."""
    try:
        return run_byo_demo(req.get("demo", ""), byo_key=req.get("byo_key") or None, inputs=req.get("inputs") or {})
    except Exception as e:  # noqa: BLE001 — a demo error is a JSON result, never a 500
        return {"ok": False, "error": str(e), "serves_truth": False}


# ───────────────────────────── browse (open-star-hubs only) ─────────────────────────────
_FACET_MAX = 15  # values shown per facet group (type has 240+; the rest are short)


def _qs(query: str, filters: dict) -> str:
    parts: list[tuple[str, str]] = []
    if query:
        parts.append(("query", query))
    for d in FACET_DIMS:
        if filters.get(d):
            parts.append((d, filters[d]))
    return urllib.parse.urlencode(parts)


def _facet_href(query: str, filters: dict, dim: str, value: str) -> str:
    nf = dict(filters)
    if nf.get(dim) == value:
        nf.pop(dim, None)
    else:
        nf[dim] = value
    qs = _qs(query, nf)
    return "/browse" + (f"?{qs}" if qs else "")


def parse_browse_qs(query: str) -> tuple[str, dict]:
    qs = urllib.parse.parse_qs(query)
    q = (qs.get("query") or [""])[0]
    filters = {d: qs[d][0] for d in FACET_DIMS if qs.get(d) and qs[d][0]}
    return q, filters


def render_browse(surface_id: str, query: str = "", filters: dict | None = None) -> str:
    filters = filters or {}
    p = pillar(surface_id)
    b = browse(query, filters)

    facet_html = ""
    for dim in FACET_DIMS:
        values = list((b["facets"].get(dim) or {}).items())
        rows = "".join(
            f'<a class="fv{" on" if filters.get(dim) == val else ""}" '
            f'href="{esc(_facet_href(query, filters, dim, val))}">'
            f'<span>{esc(val)}</span><span class="ct">{n}</span></a>'
            for val, n in values[:_FACET_MAX]
        )
        more = f'<div class="fmore">+{len(values) - _FACET_MAX} more</div>' if len(values) > _FACET_MAX else ""
        facet_html += f'<div class="facet"><h3>{dim.capitalize()}</h3><div class="fvals">{rows or "—"}</div>{more}</div>'

    active = "".join(
        f'<span class="chip"><a href="{esc(_facet_href(query, filters, d, filters[d]))}">'
        f"{esc(d)}: {esc(filters[d])} &times;</a></span>"
        for d in FACET_DIMS if filters.get(d)
    )
    active_html = f'<div class="active-filters">{active}</div>' if active else ""

    recs = "".join(
        '<div class="rec"><div class="rec-head">'
        f'<span class="rid">{esc(it["id"])}</span>'
        f'<span class="badge">{esc(it.get("status") or "unknown")}</span></div>'
        + (f'<div class="holds">{esc(it["holds"])}</div>' if it.get("holds") else "")
        + '<div class="chips">'
        + "".join(f'<span class="chip">{esc(c)}</span>' for c in (it.get("categories") or [])[:4])
        + "</div></div>"
        for it in b["items"][:30]
    )

    hidden = "".join(
        f'<input type="hidden" name="{esc(d)}" value="{esc(filters[d])}">' for d in FACET_DIMS if filters.get(d)
    )
    search = (
        '<form class="search-row" method="get" action="/browse">'
        f'<input type="search" name="query" value="{esc(query)}" '
        'placeholder="Search records — id, what it holds, category…" autocomplete="off">'
        f'{hidden}<button class="btn btn-accent" type="submit">Search</button></form>'
    )
    layout = (
        f"{search}{active_html}"
        f'<div class="rcount"><b>{b["count"]}</b> registr{"y" if b["count"] == 1 else "ies"} match'
        + (f' &ldquo;{esc(query)}&rdquo;' if query else "") + "</div>"
        '<div class="browse-layout">'
        f'<aside class="facets">{facet_html}</aside>'
        f'<section><div class="reclist">{recs or "<div class=holds>No records match these filters.</div>"}</div></section>'
        "</div>"
    )
    hero = _hero("Faceted browse", p["brand"], p["role"],
                 '<a class="btn btn-ghost" href="/">&larr; Back to ' + esc(p["brand"]) + "</a>")
    return page(surface_id, f'{p["brand"]} — browse', hero + _section(
        "Browse every record",
        "One catalog · the registry/record is the unit · hubs are flexible facets. serves_truth=false.",
        layout))


def render_404(surface_id: str) -> str:
    hero = _hero("404", "Not found", "That page does not exist on this surface.",
                 '<a class="btn btn-accent" href="/">&larr; Home</a>')
    return page(surface_id, "Not found", hero)


# ───────────────────────────── the ONE GET router ─────────────────────────────
def handle_get(surface_id: str, path: str, query: str = "") -> tuple[int, str, str]:
    """ONE handler for every surface. Returns (status, content_type, body) — socket-free so the self-test drives it."""
    p = (path or "/").rstrip("/") or "/"
    if p == "/":
        return 200, HTML, render_home(surface_id)
    if p == "/demo":
        return 200, HTML, render_demo(surface_id)
    if p == "/browse":
        if surface_id != "open-star-hubs":
            return 404, HTML, render_404(surface_id)
        q, filters = parse_browse_qs(query)
        return 200, HTML, render_browse(surface_id, q, filters)
    if p == "/favicon.ico":
        return 204, "image/x-icon", ""
    return 404, HTML, render_404(surface_id)


# ───────────────────────────── http server ─────────────────────────────
def _make_handler(surface_id: str):
    class _H(http.server.BaseHTTPRequestHandler):
        def _send(self, code: int, body: str = "", ctype: str = HTML) -> None:
            b = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            if code == 204:
                self.end_headers()
                return
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(b)))
            self.end_headers()
            if b:
                self.wfile.write(b)

        def do_GET(self):  # noqa: N802
            u = urllib.parse.urlparse(self.path)
            code, ctype, body = handle_get(surface_id, u.path, u.query)
            self._send(code, body, ctype)

        def do_POST(self):  # noqa: N802
            if urllib.parse.urlparse(self.path).path != "/run":
                self._send(404, render_404(surface_id))
                return
            try:
                n = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(n) or b"{}")
            except Exception as e:  # noqa: BLE001
                self._send(200, json.dumps({"ok": False, "error": str(e)}), "application/json")
                return
            self._send(200, json.dumps(_run_request(req)), "application/json")

        def log_message(self, *a):  # keep stderr quiet; the launcher owns logging
            pass

    return _H


def main(argv: list[str]) -> int:
    import os
    ids = surface_ids()
    positional = [a for a in argv if not a.startswith("--")]
    # surface id: a positional arg, else the SURFACE env var (env-only config for containers).
    surface_id = positional[0] if positional else os.environ.get("SURFACE", "")
    if surface_id not in ids:
        print("usage: python3 scripts/surface_server.py <surface-id> [--port N]  (or set SURFACE / PORT env)")
        print(f"surface-id must be one of: {', '.join(ids)}")
        return 2
    # Cloud-ready binding: --port/--host win, else PORT/HOST env (Cloud Run / Render / Heroku convention),
    # else the per-surface default. Host defaults to 0.0.0.0 so the same command runs in a container; locally
    # the TryCloudflare tunnel reaches it on 127.0.0.1 (covered by 0.0.0.0).
    port = (int(argv[argv.index("--port") + 1]) if "--port" in argv
            else int(os.environ.get("PORT", DEFAULT_PORTS.get(surface_id, 8000))))
    host = (argv[argv.index("--host") + 1] if "--host" in argv else os.environ.get("HOST", "0.0.0.0"))
    brand = pillar(surface_id).get("brand", surface_id)
    print(f"{brand} ({surface_id}) on http://{host}:{port}  ·  routes: / /demo "
          + ("/browse " if surface_id == "open-star-hubs" else "") + "(POST /run)")
    http.server.ThreadingHTTPServer((host, port), _make_handler(surface_id)).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
