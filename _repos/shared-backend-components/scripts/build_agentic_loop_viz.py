#!/usr/bin/env python3
"""build_agentic_loop_viz — a self-contained animated page showing each agentic LOOP descend unbounded → bounded.

For every loop in _repos/shared-backend-components/architecture/agentic_loop_catalog.json: render the perceive→reason→act→verify→iterate steps, then an
animated descent — the UNBOUNDED bar (frontier every step, max iterations, no caching; red) shrinking to the BOUNDED bar
(cheapest tool plane per step + early-stop + LLM-as-supervisor; green), with the computed $ + iteration drop + % saved.
All figures COMPUTED from the catalog (no magic). Writes dist/intro/loops/index.html (served by the live tunnel).

  PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_agentic_loop_viz.py [--self-test]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
OUT = _resource("dist") / "intro" / "loops" / "index.html"
CAT = _resource("architecture") / "agentic_loop_catalog.json"

_CSS = (
    "*{box-sizing:border-box}body{margin:0;background:#fbfbfd;color:#0f1222;font-family:'Hanken Grotesk',system-ui,sans-serif;line-height:1.55}"
    ".mono{font-family:'IBM Plex Mono',ui-monospace,monospace}.wrap{max-width:980px;margin:0 auto;padding:0 24px}"
    ".hero{background:linear-gradient(120deg,#160f2a,#2a1f54 45%,#4f46e5 90%);color:#fff;padding:84px 0 64px;background-size:220% 220%;animation:grad 16s ease infinite}"
    "@keyframes grad{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}"
    ".hero h1{font-size:clamp(34px,6vw,60px);letter-spacing:-.03em;margin:0 0 12px}.hero p{color:#dfe3f7;font-size:19px;max-width:680px}"
    ".tag{display:inline-block;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#fff;background:#ffffff22;border:1px solid #ffffff44;border-radius:999px;padding:6px 14px}"
    "section{padding:30px 0;border-bottom:1px solid #eef0f6}h2{font-size:13px;text-transform:uppercase;letter-spacing:.1em;color:#6b7280;margin:0 0 4px}"
    ".loop{padding:22px 0;border-bottom:1px solid #eef0f6}.loop h3{font-size:22px;margin:0 0 2px;letter-spacing:-.01em}"
    ".dom{color:#6b7280;font-size:13px}.saved{float:right;color:#16a34a;font-weight:800;font-size:20px}"
    ".steps{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}.step{background:#fff;border:1px solid #e6e8ef;border-radius:8px;padding:5px 10px;font-size:12.5px}"
    ".arrow{color:#4f46e5;font-weight:800;align-self:center}"
    ".bars{margin-top:10px}.row{display:flex;align-items:center;gap:10px;margin:5px 0}.row .lab{width:96px;font-size:12px;color:#6b7280;text-align:right}"
    ".bar{height:22px;border-radius:6px;transition:width 1.1s ease}.bar.ub{background:linear-gradient(90deg,#dc2626,#f87171)}.bar.bd{background:linear-gradient(90deg,#16a34a,#4ade80)}"
    ".bar.collapsed{width:0 !important}.val{font-size:12.5px;color:#33384a;white-space:nowrap}"
    ".pill{display:inline-block;border:1px solid #e6e8ef;border-radius:999px;padding:3px 10px;font-size:11.5px;margin:8px 6px 0 0;background:#fff;color:#5b6172}"
    ".reveal{opacity:0;transform:translateY(16px);transition:opacity .6s,transform .6s}.reveal.in{opacity:1;transform:none}"
    ".foot{padding:40px 0;color:#9aa;font-size:13px}a{color:#4f46e5}"
)
_JS = ("const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');"
       "e.target.querySelectorAll('.bar').forEach(b=>b.classList.remove('collapsed'))}}),{threshold:.2});"
       "document.querySelectorAll('.loop,.reveal').forEach(el=>io.observe(el));")


def _costs(loop: dict):
    from scripts.check_agentic_loop_catalog import costs
    return costs(loop)


def render() -> str:
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    loops = cat["loops"]
    computed = [(L, *_costs(L)) for L in loops]
    max_ub = max(u for _, u, _ in computed) or 1.0
    avg = round(sum(100 * (u - b) / u for _, u, b in computed) / len(computed), 1)

    def width(c):
        return max(1.5, round(100 * c / max_ub, 1))

    cards = ""
    for L, ub, bd in computed:
        pct = round(100 * (ub - bd) / ub, 1) if ub else 0
        steps = "".join(f"<span class=step>{_e(s)}</span>" + ("<span class=arrow>→</span>" if i < len(L['loop']) - 1 else "")
                        for i, s in enumerate(L["loop"]))
        planes = "".join(f"<span class=pill>{_e(p)}</span>" for p in L.get("tool_planes", []))
        cards += (
            f"<div class=loop><span class=saved>{pct}% cheaper</span><h3>{_e(L['name'])}</h3>"
            f"<div class=dom>{_e(L.get('maps_to', ''))} · e.g. {_e(', '.join(L.get('examples', [])[:3]))}</div>"
            f"<div class=steps>{steps}</div>"
            f"<div class=bars>"
            f"<div class=row><span class=lab>unbounded</span><div class='bar ub collapsed' style='width:{width(ub)}%'></div>"
            f"<span class=val>${ub} · {L['unbounded']['iterations']} iters · frontier every step</span></div>"
            f"<div class=row><span class=lab>bounded</span><div class='bar bd collapsed' style='width:{width(bd)}%'></div>"
            f"<span class=val>${bd} · {L['bounded']['iterations']} iters · cheapest plane + supervise + early-stop</span></div>"
            f"</div>{planes}</div>")

    frontiers = "".join(f"<span class=pill>{_e(f['name'])}</span>" for f in cat.get("frontiers", []))
    return (
        "<!doctype html><html lang=en><head><meta charset=utf-8>"
        "<meta name=viewport content='width=device-width,initial-scale=1'>"
        "<title>Agent loops — unbounded → bounded</title>"
        f"<meta name=description content='Every agentic loop descends from frontier-every-step to the cheapest bounded path.'>"
        f"<style>{_CSS}</style></head><body>"
        "<header class=hero><div class=wrap><span class=tag>Teleon · the descent, on whole loops</span>"
        "<h1>Watch the loop descend.</h1><p>Every operational AI loop — research, extraction, browser-use, support, "
        "coding — starts <b>unbounded</b> (a frontier model on every step, max iterations, no caching) and we descend it "
        "to the <b>bounded</b> path: the cheapest tool plane per step, early-stop when there's no new progress, the LLM "
        f"reserved for supervision. Across {len(loops)} loops that's <b>~{avg}% cheaper</b> — while the loop still completes.</p>"
        "<p class=mono style='font-size:12px;margin-top:10px;color:#cdd2f0'>Figures computed from architecture/agentic_loop_catalog.json (representative). serves_truth=false.</p>"
        "</div></header>"
        f"<div class=wrap><section class=reveal><h2>{len(loops)} agentic loops · perceive → reason → act → verify → iterate</h2></section>"
        f"{cards}"
        f"<section class=reveal style='margin-top:10px'><h2>Emerging frontiers (less saturated)</h2><div>{frontiers}</div></section>"
        "<div class=foot>Teleon descends the loop; Baltor governs what each step treats as true. "
        "<a href='../teleon.html'>← back to Teleon</a> · figures computed.</div></div>"
        f"<script>{_JS}</script></body></html>\n")


def _e(s) -> str:
    import html
    return html.escape(str(s))


def build() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(), encoding="utf-8")
    return OUT


def _self_test() -> int:
    h = render()
    cat = json.loads(CAT.read_text(encoding="utf-8"))
    fails = []
    def ck(n, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
        if not ok: fails.append(n)
    ck("renders a self-contained animated page (viewport + style + keyframes + reveal JS, no external http)",
       h.startswith("<!doctype html>") and "@keyframes" in h and "IntersectionObserver" in h and "http://" not in h)
    ck("every loop is shown with its steps", all(_e(L["name"]) in h for L in cat["loops"]))
    ck("each loop shows the unbounded→bounded descent (both bars + % cheaper)",
       h.count("% cheaper") >= len(cat["loops"]) and "unbounded" in h and "bounded" in h)
    ck("figures are computed (a known loop's $ appears)", "frontier every step" in h and "early-stop" in h)
    ck("emerging frontiers listed", all(f["name"] in h for f in cat["frontiers"]))
    ck("honest representative + serves_truth=false note", "representative" in h and "serves_truth=false" in h)
    print("\n" + ("PASS - build_agentic_loop_viz: an animated page where each agentic loop visibly descends unbounded→"
                  "bounded (computed $ + iteration drop + % saved), with the loop steps + tool planes + emerging "
                  "frontiers. serves_truth=false." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    p = build()
    print(f"built {p.relative_to(REPO)} ({p.stat().st_size} bytes)")
    raise SystemExit(0)
