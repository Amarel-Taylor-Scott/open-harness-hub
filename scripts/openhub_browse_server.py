#!/usr/bin/env python3
"""scripts.openhub_browse_server — the FACETED BROWSE UI for OpenHubForAI.io.

Owner 2026-06-25. A thin stdlib http.server UI laid OVER the existing backend
`src.teleon.registry.browse` — it does NOT rebuild search/browse logic, it calls `browse()`/`facets()`.
One catalog, the registry/record is the unit, hubs are flexible facets. `GET /` serves the browse page
(a search box + the five facet groups category/type/kind/layer/status with live counts + record cards);
`GET /browse?query=&category=&type=&kind=&layer=&status=` returns `browse(query, filters)` as JSON.
Dark family theme (Hanken Grotesk), accent #3b6fd4. serves_truth=false.

  python3 scripts/openhub_browse_server.py [--port 8130]    then tunnel it
  --self-test
"""
from __future__ import annotations

import http.server
import json
import sys
import urllib.parse
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src.teleon.registry.browse import FACET_DIMS, browse, facets  # noqa: E402
from scripts._surface_accents import accent as _acc  # noqa: E402

ACCENT = _acc("open-star-hubs")  # OpenHubForAI.io accent — single-sourced from surface_capability_spec.json

_CSS = """*{box-sizing:border-box}body{font-family:'Hanken Grotesk',system-ui,sans-serif;background:#0b0e14;color:#e6edf3;margin:0;padding:2rem 1.2rem;line-height:1.5}
.wrap{max-width:1120px;margin:0 auto}a{color:var(--a);text-decoration:none}
h1{font-size:1.6rem;margin:0 0 .25rem}h1 span{color:var(--a)}
.tag{display:inline-block;border:1px solid #21262d;border-radius:999px;padding:3px 11px;color:#9aa7b4;font-size:12px;margin-bottom:1rem}
.sub{color:#9aa7b4;margin:.2rem 0 1.1rem;max-width:72ch}
input{width:100%;background:#11161d;color:#e6edf3;border:1px solid #21262d;border-radius:10px;padding:.7rem .85rem;font:14px 'Hanken Grotesk',system-ui,sans-serif}
input:focus{outline:none;border-color:var(--a)}
.layout{display:grid;grid-template-columns:236px 1fr;gap:1.4rem;margin-top:1.1rem;align-items:start}
.facets{display:flex;flex-direction:column;gap:1rem;position:sticky;top:1rem}
.facet h3{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:#6b7682;margin:0 0 .35rem}
.vals{display:flex;flex-direction:column;gap:2px;max-height:232px;overflow:auto}
.fv{display:flex;justify-content:space-between;gap:.6rem;align-items:center;width:100%;text-align:left;background:transparent;color:#c9d4df;border:1px solid transparent;border-radius:7px;padding:.26rem .5rem;font:13px 'Hanken Grotesk',system-ui,sans-serif;cursor:pointer}
.fv:hover{background:#11161d}
.fv.on{background:rgba(122,162,255,.15);border-color:var(--a);color:#fff}
.fv>span:first-child{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.ct{color:#6b7682;font-size:11px;font-variant-numeric:tabular-nums}.fv.on .ct{color:var(--a)}
.muted{color:#6b7682;font-size:13px}
.rcount{color:#9aa7b4;font-size:.85rem;margin-bottom:.75rem}.rcount b{color:#e6edf3}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(244px,1fr));gap:.8rem}
.rec{border:1px solid #21262d;border-radius:12px;background:#11161d;padding:.85rem .95rem}
.rec:hover{border-color:#2d3543}
.rh{display:flex;justify-content:space-between;align-items:flex-start;gap:.5rem;margin-bottom:.4rem}
.rid{font:12.5px ui-monospace,monospace;color:#e6edf3;font-weight:700;word-break:break-word}
.badge{font-size:9.5px;text-transform:uppercase;letter-spacing:.04em;padding:2px 7px;border-radius:999px;border:1px solid #21262d;color:#9aa7b4;white-space:nowrap}
.badge.b-active,.badge.b-live,.badge.b-ready{color:#56d4c4;border-color:rgba(86,212,196,.4)}
.badge.b-candidate,.badge.b-proposed,.badge.b-staged{color:#e0a458;border-color:rgba(224,164,88,.4)}
.holds{font-size:.82rem;color:#9aa7b4;margin-bottom:.55rem}
.chips{display:flex;flex-wrap:wrap;gap:4px}
.chip{font-size:10.5px;background:#1a2230;color:#9db4d8;border-radius:999px;padding:2px 8px}
.meta{font:11px ui-monospace,monospace;color:#5b6573;margin-top:.5rem}
.foot{color:#5b6573;font-size:11px;margin-top:1.6rem}
@media(max-width:720px){.layout{grid-template-columns:1fr}.facets{position:static}}"""


# The browser logic. Concatenation (not template literals) keeps it brace-safe; __DIMS__/__BOOT__ are
# substituted by _index(). \uXXXX escapes are preserved verbatim (raw string) for the JS engine to decode.
_JS = r"""
const DIMS = __DIMS__, BOOT = __BOOT__;
const state = {query:'', filters:{}};
const $ = id => document.getElementById(id);
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function badgeClass(s){return 'b-'+String(s||'unknown').toLowerCase().replace(/[^a-z0-9]+/g,'-');}
async function load(){
  const p = new URLSearchParams();
  if(state.query) p.set('query', state.query);
  for(const d of DIMS){ if(state.filters[d]) p.set(d, state.filters[d]); }
  let j;
  try{ j = await (await fetch('/browse?'+p.toString())).json(); }
  catch(e){ $('results').innerHTML='<div class="muted">browse endpoint unavailable</div>'; return; }
  render(j);
}
function renderFacets(facets){
  for(const dim of DIMS){
    const el=$('facet-'+dim), counts=facets[dim]||{}, active=state.filters[dim];
    const html=Object.entries(counts).map(([val,n])=>
      '<button class="fv'+(val===active?' on':'')+'" data-dim="'+dim+'" data-val="'+esc(val)+'">'+
      '<span>'+esc(val)+'</span><span class="ct">'+n+'</span></button>').join('');
    el.innerHTML = html || '<span class="muted">—</span>';
  }
}
function render(j){
  renderFacets(j.facets||{});
  $('count').textContent = j.count;
  const cards=(j.items||[]).map(it=>{
    const chips=(it.categories||[]).map(c=>'<span class="chip">'+esc(c)+'</span>').join('');
    const meta=[it.kind,it.layer,it.primary_hub].filter(Boolean).map(esc).join('  ·  ');
    return '<div class="rec"><div class="rh"><span class="rid">'+esc(it.id)+'</span>'+
      '<span class="badge '+badgeClass(it.status)+'">'+esc(it.status)+'</span></div>'+
      '<div class="holds">'+esc(it.holds)+'</div>'+
      '<div class="chips">'+chips+'</div>'+
      (meta?'<div class="meta">'+meta+'</div>':'')+'</div>';
  }).join('');
  $('results').innerHTML = cards || '<div class="muted">No records match these filters.</div>';
  const recs=j.records||[], rb=$('records');
  rb.innerHTML = recs.length
    ? '<div class="rcount"><b>'+recs.length+'</b> populated record(s) federated for “'+esc(j.query)+'”</div>'+
      '<div class="chips">'+recs.slice(0,80).map(r=>'<span class="chip">'+esc(r.registry)+' · '+esc(r.name)+'</span>').join('')+'</div>'
    : '';
}
document.addEventListener('click', e=>{
  const b=e.target.closest('.fv'); if(!b) return;
  const dim=b.dataset.dim, val=b.dataset.val;
  state.filters[dim] = state.filters[dim]===val ? undefined : val;  // click a value to filter; click again clears it
  if(!state.filters[dim]) delete state.filters[dim];
  load();
});
let _t; $('q').addEventListener('input', e=>{ state.query=e.target.value; clearTimeout(_t); _t=setTimeout(load,200); });
render(BOOT);
"""


def _safe_json(obj) -> str:
    """JSON safe to inline inside a <script> tag (no premature </script>, no JS line separators)."""
    return (json.dumps(obj, separators=(",", ":"))
            .replace("<", "\\u003c").replace(" ", "\\u2028").replace(" ", "\\u2029"))


def _facet_groups() -> str:
    """The five facet group shells, built from the backend's FACET_DIMS (no magic list) — JS fills the values."""
    return "".join(
        f'<div class="facet" data-dim="{d}"><h3>{d.capitalize()}</h3><div class="vals" id="facet-{d}"></div></div>'
        for d in FACET_DIMS)


def _index() -> str:
    """The faceted browse page. Bootstraps with the unfiltered browse() so facets + cards paint immediately;
    every interaction thereafter fetches /browse and re-renders."""
    boot = browse("", {})
    js = _JS.replace("__DIMS__", _safe_json(list(FACET_DIMS))).replace("__BOOT__", _safe_json(boot))
    return (
        "<!doctype html><html lang=en><meta charset=utf-8>"
        '<meta name=viewport content="width=device-width,initial-scale=1">'
        "<title>OpenHubForAI.io — browse every record</title>"
        f"<style>{_CSS}</style>"
        f'<div class="wrap" style="--a:{ACCENT}">'
        "<h1>OpenHubForAI.io <span>— browse every record</span></h1>"
        '<div class="tag">faceted browse · one catalog · the registry is the unit</div>'
        '<p class="sub">Search and filter every registry/record across the family. A record can sit under '
        "several categories at once — pick any facets (category · type · kind · layer "
        "· status) to combine them. serves_truth=false.</p>"
        '<input id="q" type="search" placeholder="Search records — id, what it holds, category…" '
        'autocomplete="off" spellcheck="false">'
        f'<div class="layout"><aside class="facets">{_facet_groups()}</aside>'
        '<section class="results"><div class="rcount"><b id="count">0</b> records</div>'
        '<div class="cards" id="results"></div><div id="records" style="margin-top:1.1rem"></div>'
        "</section></div>"
        '<div class="foot">UI over src.teleon.registry.browse · the backend computes facets &amp; counts '
        "· serves_truth=false</div>"
        "</div>"
        f"<script>{js}</script></html>"
    )


def _browse_response(raw_query: str) -> dict:
    """The GET /browse logic, factored so the self-test exercises it: parse the query string into
    (query, {facet filters}) and call the backend browse() — no rebuilt search logic."""
    qs = urllib.parse.parse_qs(raw_query)
    query = (qs.get("query") or [""])[0]
    filters = {d: qs[d][0] for d in FACET_DIMS if qs.get(d) and qs[d][0]}
    return browse(query, filters)


class _H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        path = u.path.rstrip("/")
        if path in ("", "/index.html"):
            self._send(200, _index())
        elif path == "/browse":
            self._send(200, json.dumps(_browse_response(u.query)), "application/json")
        else:
            self._send(404, "not found")

    def log_message(self, *a):
        pass


def self_test() -> int:
    idx = _index()
    assert "OpenHubForAI" in idx, "index titles OpenHubForAI.io"
    assert "<input" in idx and 'id="q"' in idx and 'type="search"' in idx, "index has a search input"
    assert all(d.capitalize() in idx for d in FACET_DIMS), f"all 5 facet group labels present: {FACET_DIMS}"

    # the facets() API exposes exactly the five browsable dimensions
    f = facets()
    assert set(f) == set(FACET_DIMS) and len(f["type"]) >= 100, sorted(f)

    # the GET /browse handler logic calls the backend and returns items + facet counts
    full = _browse_response("")
    assert full["count"] > 0 and full["items"] and full["facets"], "browse handler returns items + facets"
    assert full["serves_truth"] is False, "serves_truth=false"
    assert all(k in full["items"][0] for k in ("id", "holds", "status", "categories")), \
        "cards have the fields the UI renders"
    # a facet filter through the handler narrows the set and still returns facet counts
    narrowed = _browse_response("kind=discovery")
    assert 0 < narrowed["count"] < full["count"] and narrowed["facets"]["kind"], "a facet filter narrows"
    # a free-text query + a second facet combine through the handler (AND)
    combo = _browse_response("query=cost&category=Optimization")
    assert all("Optimization" in it["categories"] for it in combo["items"]), "facets combine through the handler"

    print(f"openhub_browse_server self-test: OK (index renders 'OpenHubForAI' + search + "
          f"{len(FACET_DIMS)} facet groups; browse handler -> {full['count']} records, "
          f"{len(full['facets']['category'])} categories, narrows to {narrowed['count']} on kind=discovery; "
          f"serves_truth=false)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8130
    print(f"OpenHubForAI.io faceted browse on http://127.0.0.1:{port}")
    http.server.HTTPServer(("127.0.0.1", port), _H).serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
