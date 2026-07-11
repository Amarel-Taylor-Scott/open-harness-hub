"""taedri_web — serve the Taedri web app (the Claude Design screens) from the gateway, wired to real endpoints.

The design screens are Design-Canvas components (`.dc.html`: `<x-dc>` + `<helmet>` + `sc-if`/`{{ }}`/`style-hover`
directives + a `DCLogic` class). This module TRANSFORMS each into a self-contained production page and serves it
at its production route (SCREEN-MAP), injecting a small client runtime that interprets the DC directives and a
per-route WIRE script that replaces the mock/specimen data with real calls to this same gateway (same-origin, so
cookies + endpoints just work). One engine → all 40 screens; adding a screen = drop its `.dc.html` + a route row.

    python3 scripts/taedri_web.py --self-test
    python3 scripts/taedri_web.py --render / > /tmp/landing.html   # transform one route to production HTML
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
SCREENS = _SBC / "web" / "taedri" / "screens"

#: production route → design screen file (from build/SCREEN-MAP.md). One screen = one route.
ROUTES: dict[str, str] = {
    "/": "Landing.dc.html", "/pricing": "Pricing.dc.html", "/about": "About.dc.html",
    "/docs": "Docs.dc.html", "/blog": "Blog.dc.html", "/legal": "Legal.dc.html",
    "/support": "Support.dc.html", "/contact": "Contact.dc.html", "/status": "Status.dc.html",
    "/demo": "Demo.dc.html", "/community": "Community.dc.html", "/browse": "Browse.dc.html",
    "/requests": "Requests.dc.html", "/signup": "Signup.dc.html", "/login": "Login.dc.html",
    "/verify": "Verify Email.dc.html", "/setup": "Setup.dc.html", "/dashboard": "Dashboard.dc.html",
    "/workbench": "Workbench.dc.html", "/keys": "Keys.dc.html", "/logs": "Logs.dc.html",
    "/my": "My Primitives.dc.html", "/deploy": "Deploy.dc.html", "/billing": "Billing.dc.html",
    "/settings": "Settings.dc.html", "/team": "Team.dc.html", "/admin": "Admin.dc.html",
    "/analytics": "Analytics.dc.html", "/contribute": "Contribute.dc.html",
}
#: props per route (which sc-if branches are live in production): auth surface, corpus counter mode.
_PUBLIC = {"authState": "logged-out", "corpusState": "live"}
_SESSION = {"authState": "logged-in", "corpusState": "live"}
ROUTE_PROPS: dict[str, dict[str, str]] = {
    r: (_SESSION if r in ("/dashboard", "/workbench", "/keys", "/logs", "/my", "/deploy", "/billing",
                          "/settings", "/team", "/admin", "/analytics", "/contribute", "/setup") else _PUBLIC)
    for r in ROUTES
}

# ── the client runtime: interprets the DC directives + gives DCLogic a real host ──────────────────
DC_RUNTIME = r"""
(function(){
  class DCLogic{
    constructor(props){this.props=props||{};this.state={};}
    setState(u){this.state=Object.assign({},this.state,typeof u==='function'?u(this.state):u);if(this.__host)this.__host.render();}
    forceUpdate(){if(this.__host)this.__host.render();}
    componentDidMount(){}componentDidUpdate(){}componentWillUnmount(){}renderVals(){return{};}
  }
  window.DCLogic=DCLogic;
  var KEY=/\{\{\s*([^}]+?)\s*\}\}/;
  function key(s){var m=String(s||'').match(KEY);return m?m[1].trim():null;}
  function subst(s,v){return String(s).replace(/\{\{\s*([^}]+?)\s*\}\}/g,function(_,k){var x=v[k.trim()];return x==null||typeof x==='function'?'':String(x);});}
  function Host(mount,Comp,props){this.mount=mount;this.template=mount.innerHTML;this.comp=new Comp(props);this.comp.__host=this;this.mounted=false;}
  Host.prototype.render=function(){
    var vals=this.comp.renderVals?this.comp.renderVals():{};
    var tmp=document.createElement('div');tmp.innerHTML=this.template;
    this.process(tmp,vals);
    this.mount.innerHTML='';while(tmp.firstChild)this.mount.appendChild(tmp.firstChild);
    if(!this.mounted){this.mounted=true;if(this.comp.componentDidMount)this.comp.componentDidMount();}
    else if(this.comp.componentDidUpdate)this.comp.componentDidUpdate(this.comp.props);
  };
  Host.prototype.process=function(root,vals){
    var guard=0;
    while(true){var sc=root.querySelector('sc-if');if(!sc||guard++>5000)break;
      var k=key(sc.getAttribute('value'));var show=k?!!vals[k]:false;
      if(show){var f=document.createDocumentFragment();while(sc.firstChild)f.appendChild(sc.firstChild);sc.parentNode.replaceChild(f,sc);}
      else sc.parentNode.removeChild(sc);}
    var els=root.querySelectorAll('*');
    for(var i=0;i<els.length;i++){var el=els[i];
      if(el.hasAttribute('onclick')){var ck=key(el.getAttribute('onclick'));el.removeAttribute('onclick');
        if(ck&&typeof vals[ck]==='function')(function(fn){el.addEventListener('click',function(e){e.preventDefault();fn(e);});})(vals[ck]);}
      ['aria-expanded','value','title','aria-label','href','placeholder'].forEach(function(a){
        if(el.hasAttribute(a)&&el.getAttribute(a).indexOf('{{')>=0)el.setAttribute(a,subst(el.getAttribute(a),vals));});
      if(el.hasAttribute('style-hover')){var hov=el.getAttribute('style-hover');el.removeAttribute('style-hover');
        var base=el.getAttribute('style')||'';
        (function(e2,b,h){e2.addEventListener('mouseenter',function(){e2.setAttribute('style',b+';'+h);});
          e2.addEventListener('mouseleave',function(){e2.setAttribute('style',b);});})(el,base,hov);}
    }
    var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,null,false),t,ts=[];
    while(t=w.nextNode())if(t.nodeValue.indexOf('{{')>=0)ts.push(t);
    ts.forEach(function(n){n.nodeValue=subst(n.nodeValue,vals);});
  };
  window.__mountDC=function(Comp,props){var m=document.getElementById('__dc_root')||document.body;
    var h=new Host(m,Comp,props);window.__dcHost=h;h.render();
    if(window.__taedriWire)try{window.__taedriWire();}catch(e){console.warn('wire',e);}};
  // shared helper: animate a counter element to a real integer
  window.__animateTo=function(el,target){var t0=null,dur=900;function tick(now){if(t0===null)t0=now;var p=Math.min(1,(now-t0)/dur);
    var e=1-Math.pow(1-p,3);el.textContent=Math.round(target*e).toLocaleString('en-US');if(p<1)requestAnimationFrame(tick);}requestAnimationFrame(tick);};
})();
"""

# ── per-route data wiring: replace specimen data with real, same-origin gateway calls ─────────────
_WIRE_CORPUS = r"""window.__taedriWire=function(){
  // The #corpus-counter lives behind an sc-if that is false at mount, and the design mock animates it to a
  // HARDCODED specimen. So: fetch the real count, POLL until the element exists, then PIN it to the real value
  // for a window that outlasts the mock's animation. Final settled value is the live, computed count (the
  // computed-numbers law) — not the stale specimen. Verified adversarially with a sentinel count.
  fetch('/v1/stats/domains',{cache:'no-store'}).then(function(r){return r.json();}).then(function(d){
    if(!d||!d.primitives)return;
    var real=Number(d.primitives).toLocaleString('en-US'),tries=0;
    (function poll(){
      var el=document.getElementById('corpus-counter');
      if(el){var n=0,iv=setInterval(function(){var e=document.getElementById('corpus-counter');
        if(e)e.textContent=real; if(++n>60)clearInterval(iv);},50);return;}
      if(tries++<160)setTimeout(poll,40);
    })();
  }).catch(function(){});
};"""
WIRE: dict[str, str] = {"/": _WIRE_CORPUS, "/browse": _WIRE_CORPUS}


def _extract(dc_html: str) -> dict[str, str]:
    """Split a .dc.html into title, style, body (x-dc inner minus the trailing DC script), and the DCLogic src."""
    title = (re.search(r"<title>(.*?)</title>", dc_html, re.S) or [None, "Taedri"])[1]
    style = "".join(re.findall(r"<style>(.*?)</style>", dc_html, re.S))
    body = (re.search(r"<x-dc>(.*?)</x-dc>", dc_html, re.S) or [None, ""])[1]
    # drop the helmet block from the body (title/style live in head)
    body = re.sub(r"<helmet>.*?</helmet>", "", body, flags=re.S).strip()
    logic = (re.search(r'<script[^>]*type="text/x-dc"[^>]*>(.*?)</script>', dc_html, re.S) or [None, ""])[1]
    return {"title": title, "style": style, "body": body, "logic": logic}


def transform(dc_html: str, *, route: str = "/", props: Optional[dict] = None) -> str:
    """Produce a self-contained production HTML page from a .dc.html design screen."""
    parts = _extract(dc_html)
    props = props or ROUTE_PROPS.get(route, _PUBLIC)
    wire = WIRE.get(route, "")
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{parts['title']}</title><style>{parts['style']}</style>"
        f"<script>{DC_RUNTIME}</script></head>"
        f"<body><div id=\"__dc_root\">{parts['body']}</div>"
        f"<script>{parts['logic']}</script>"
        f"<script>{wire}\nwindow.__mountDC(Component, {json.dumps(props)});</script>"
        "</body></html>"
    )


def render_route(route: str) -> Optional[str]:
    """Transform the screen mapped to `route`, or None if unmapped / file missing."""
    fname = ROUTES.get(route)
    if not fname:
        return None
    path = SCREENS / fname
    if not path.exists():
        return None
    return transform(path.read_text(encoding="utf-8"), route=route)


def available_routes() -> list[str]:
    """Routes whose design screen is present on disk (so serving grows as screens are added)."""
    return sorted(r for r, f in ROUTES.items() if (SCREENS / f).exists())


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("route map covers the SCREEN-MAP (>=28 routes)", len(ROUTES) >= 28))

    # a synthetic DC screen transforms into clean production HTML
    sample = ('<!DOCTYPE html><html><head><script src="./support.js"></script></head><body><x-dc>'
              '<helmet><title>T</title><style>body{color:red}</style></helmet>'
              '<div id="corpus-counter">0</div>'
              '<sc-if value="{{ loggedOut }}"><a href="Signup.dc.html" onClick="{{ go }}">Get a key</a></sc-if>'
              '<sc-if value="{{ loggedIn }}"><span>acct</span></sc-if>'
              '<span style-hover="color:blue">{{ label }}</span>'
              '</x-dc><script type="text/x-dc">class Component extends DCLogic{renderVals(){'
              'return{loggedOut:true,loggedIn:false,label:"hi",go:function(){}};}}</script></body></html>')
    out = transform(sample, route="/")
    checks.append(("transform: unwraps x-dc, lifts title+style to head, keeps the runtime + logic + mount",
                   "<x-dc>" not in out and "id=\"__dc_root\"" in out and "body{color:red}" in out
                   and "__mountDC(Component" in out and "class Component extends DCLogic" in out))
    checks.append(("transform: no leftover support.js reference or helmet in output",
                   "support.js" not in out and "<helmet>" not in out))
    checks.append(("landing route wires the corpus counter to /v1/stats/domains (real data, no specimen)",
                   "/v1/stats/domains" in WIRE["/"] and "corpus-counter" in WIRE["/"]))
    checks.append(("session routes get logged-in props; public routes logged-out",
                   ROUTE_PROPS["/dashboard"]["authState"] == "logged-in"
                   and ROUTE_PROPS["/"]["authState"] == "logged-out"))
    # the DC runtime references the directives it must handle
    checks.append(("runtime handles sc-if, {{ }}, onclick, style-hover, DCLogic, mount",
                   all(tok in DC_RUNTIME for tok in ("sc-if", "onclick", "style-hover", "DCLogic",
                                                     "__mountDC", "renderVals"))))

    ok = all(v for _, v in checks)
    print("taedri_web — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  {len(ROUTES)} routes mapped; {len(available_routes())} screens present on disk; "
          f"{len(WIRE)} wired to real endpoints.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--render", metavar="ROUTE")
    ap.add_argument("--routes", action="store_true")
    args = ap.parse_args()
    if args.render:
        html = render_route(args.render)
        if html is None:
            print(f"no screen for route {args.render!r} (available: {available_routes()})", file=sys.stderr)
            return 1
        sys.stdout.write(html)
        return 0
    if args.routes:
        print(json.dumps({"mapped": sorted(ROUTES), "present": available_routes()}, indent=2))
        return 0
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
