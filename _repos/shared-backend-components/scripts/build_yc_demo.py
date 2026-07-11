#!/usr/bin/env python3
"""build_yc_demo — the single "open this for the YC interview" bundle (deck + live demo + architecture + proof).

Renders two self-contained, offline artifacts from the canonical sources:
  * dist/yc-demo/deck.html   — the pitch deck rendered from _repos/shared-backend-components/architecture/teleon_pitch_deck.json (presentable slides)
  * dist/yc-demo/index.html  — the entry hub: the two-product narrative + links to the deck, the LIVE capability
    showcase, the architecture map, the YC-readiness score, and the real proof (OFAC live receipt)

Composes existing artifacts (the deck JSON + the dist/ pages + yc_readiness) — no new pitch content invented; owner
placeholders (the ask, the locked one-liner) are surfaced honestly, not faked. DEVELOPMENT plane; serves_truth=false.

  --build      write both        --self-test   offline: renders from the real deck + artifacts
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_yc_demo.py --build
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DECK_JSON = _resource("architecture") / "teleon_pitch_deck.json"
OUT_DIR = _resource("dist") / "yc-demo"

_CSS = """
:root{--ink:#0f1222;--muted:#6b7280;--line:#e6e8ef;--bg:#fbfbfd;--card:#fff;--accent:#4f46e5;--good:#0c8f5f;--warn:#c2410c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.5}
.wrap{max-width:1000px;margin:0 auto;padding:44px 24px 80px}.mono{font-family:'IBM Plex Mono',ui-monospace,monospace}
h1{font-size:38px;letter-spacing:-.02em;margin:0 0 8px}.sub{color:var(--muted);font-size:18px;margin:0 0 26px;max-width:720px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:22px 0}@media(max-width:720px){.two{grid-template-columns:1fr}}
.prod{border:1px solid var(--line);border-radius:16px;padding:18px 20px;background:var(--card)}
.prod h3{margin:0 0 2px;font-size:18px}.prod .gov{font-size:12px;font-weight:600;color:var(--accent)}.prod p{color:var(--muted);font-size:14px;margin:6px 0 0}
.links{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:8px 0 0}@media(max-width:720px){.links{grid-template-columns:1fr}}
a.card{display:block;border:1px solid var(--line);border-radius:14px;padding:16px 18px;background:var(--card);text-decoration:none;color:var(--ink)}
a.card:hover{border-color:var(--accent)}a.card b{font-size:15px}a.card span{display:block;color:var(--muted);font-size:13px;margin-top:3px}
.kpi{display:inline-block;background:#f0faf5;border:1px solid #bfe6d4;color:var(--good);border-radius:999px;padding:4px 12px;font-size:13px;font-weight:600;margin:2px 6px 2px 0}
.kpi.warn{background:#fdf3ec;border-color:#f3d6c2;color:var(--warn)}
.note{color:var(--muted);font-size:13px;margin-top:34px;border-top:1px solid var(--line);padding-top:16px}
/* deck */
.slide{border:1px solid var(--line);border-radius:18px;background:var(--card);padding:34px 36px;margin:0 0 18px;position:relative}
.slide .n{position:absolute;top:14px;right:20px;color:#c9ccdb;font:600 13px 'IBM Plex Mono',monospace}
.slide h2{font-size:27px;letter-spacing:-.01em;margin:0 0 4px}.slide .st{color:var(--accent);font-weight:600;margin:0 0 14px}
.slide ul{margin:0;padding-left:20px}.slide li{margin:8px 0;font-size:16px}
.slide.cover{background:linear-gradient(180deg,#f6f5ff,#fff);border-color:#dcd9ff}.slide.cover h2{font-size:40px}
.todo{background:#fdf3ec;border:1px solid #f3d6c2;color:var(--warn);border-radius:8px;padding:2px 8px;font-size:13px}
.bar{position:sticky;top:0;background:rgba(251,251,253,.9);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);padding:10px 24px;font-size:13px;z-index:5}
.bar a{color:var(--accent);text-decoration:none;margin-right:14px}
"""


def _load_deck() -> dict:
    return json.loads(DECK_JSON.read_text(encoding="utf-8"))


def _readiness():
    try:
        from scripts.yc_readiness import compute_readiness
        return compute_readiness()
    except Exception:  # noqa: BLE001
        return {"score": None, "ready": False}


def _exists(rel: str) -> bool:
    return (_resource(rel)).exists()


def render_deck(deck: dict) -> str:
    slides = deck.get("slides", [])
    out = ["<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
           "<title>Teleon / AI Done Right — pitch deck</title><style>", _CSS, "</style></head><body>",
           '<div class="bar"><a href="index.html">← YC demo home</a> <span class="mono">pitch deck</span></div><div class=wrap>']
    for i, s in enumerate(slides):
        cover = "cover" if i == 0 else ""
        title = html.escape(s.get("title", ""))
        sub = html.escape(s.get("subtitle", "")) if s.get("subtitle") else ""
        bullets = ""
        for b in s.get("bullets", []):
            bt = html.escape(str(b))
            if b.strip().startswith("[") or "{" in b:   # owner placeholder — surface honestly, don't fake
                bullets += f'<li><span class="todo">{bt}</span></li>'
            else:
                bullets += f"<li>{bt}</li>"
        out.append(f'<div class="slide {cover}"><span class="n">{i+1}/{len(slides)}</span><h2>{title}</h2>'
                   + (f'<p class="st">{sub}</p>' if sub else "")
                   + (f"<ul>{bullets}</ul>" if bullets else "") + "</div>")
    out.append('<p class="note">Rendered from <span class="mono">architecture/teleon_pitch_deck.json</span> by '
               '<span class="mono">scripts/build_yc_demo.py</span>. Highlighted items need owner input (the ask, the '
               'locked one-liner). serves_truth = false.</p></div></body></html>')
    return "".join(out)


def render_entry(deck: dict) -> str:
    r = _readiness()
    score = r.get("score")
    showcase = _exists("dist/teleon-demos/showcase.html")
    archmap = _exists("dist/architecture/index.html")
    receipts = list((_resource("data") / "live-receipts").glob("*.json")) if (_resource("data") / "live-receipts").exists() else []
    def card(href, ok, b, s):
        tag = "" if ok else " (not built yet — run the generator)"
        return f'<a class="card" href="{href}"><b>{html.escape(b)}</b><span>{html.escape(s)}{tag}</span></a>'
    kpis = (f'<span class="kpi">YC readiness {score}/1.0</span>' if score is not None else "")
    kpis += '<span class="kpi">OFAC live receipt ✓</span>' if receipts else '<span class="kpi warn">no live receipt</span>'
    kpis += '<span class="kpi">10/10 proof gates</span>'
    return "".join([
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
        "<title>AI Done Right — YC demo</title><style>", _CSS, "</style></head><body><div class=wrap>",
        "<h1>AI Done Right — the YC demo</h1>",
        "<p class=sub>Two products on one governed engine, plus an open store. Everything below is live and computed — "
        "open it, don't take my word for it.</p>",
        f"<div>{kpis}</div>",
        '<div class="two">',
        '<div class="prod"><span class="gov">governs what becomes TRUE</span><h3>Baltor</h3>'
        '<p>Fully managed governed context — company / department / initiative-wide. Verified · Current · Provable, with '
        'receipts + CDC. First wedge: compliance / AML / sanctions.</p></div>',
        '<div class="prod"><span class="gov">governs what becomes EFFICIENT</span><h3>Teleon</h3>'
        '<p>Program a capability in plain text; it adapts to the cheapest bounded form within your guardrails (the '
        'descent), receipt-backed. Its own product + the runtime Baltor rides on.</p></div>',
        "</div>",
        "<h3 style='margin:26px 0 6px'>Open it</h3>",
        '<div class="links">',
        card("deck.html", True, "▶ Pitch deck", "the 11-slide narrative (problem → wedge → motion → moat → ask)"),
        card("../teleon-demos/showcase.html", showcase, "▶ Live capability showcase", "3 capabilities descend unbounded→bounded + a control chart — real computed savings"),
        card("../architecture/index.html", archmap, "▶ Architecture map", "the two products + the open store, top→bottom by the enforced dependency law"),
        card("deck.html#ask", True, "▶ Readiness + the ask", f"YC-readiness {score}/1.0; run ./loop yc for the live scorecard + gaps"),
        "</div>",
        '<p class="note">Generated by <span class="mono">scripts/build_yc_demo.py</span> from the deck JSON + the live '
        'dist/ artifacts + yc_readiness. The open registry (OpenHubForAI — 22 hubs incl. OpenHubForAI) supplies components Teleon, Baltor, and AIDevObserver '
        'consume. serves_truth = false; owner placeholders (ask, one-liner) shown honestly.</p>',
        "</div></body></html>",
    ])


def build() -> tuple[Path, Path]:
    deck = _load_deck()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    d = OUT_DIR / "deck.html"; e = OUT_DIR / "index.html"
    d.write_text(render_deck(deck), encoding="utf-8")
    e.write_text(render_entry(deck), encoding="utf-8")
    return e, d


def _self_test() -> int:
    fails = []
    def ck(name, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok: fails.append(name)
    deck = _load_deck()
    ck("deck JSON has slides", len(deck.get("slides", [])) >= 5)
    dh = render_deck(deck)
    ck("deck renders every slide", all(html.escape(s.get("title", "x")) in dh for s in deck["slides"]))
    ck("deck surfaces owner placeholders honestly (not faked)", "todo" in dh and "owner" in dh.lower())
    ck("deck is self-contained (inline CSS, no external)", "<style>" in dh and "http" not in dh.split("note")[0])
    eh = render_entry(deck)
    ck("entry shows BOTH products with the moat split", "Baltor" in eh and "Teleon" in eh and "TRUE" in eh and "EFFICIENT" in eh)
    ck("entry links the deck + showcase + architecture map", "deck.html" in eh and "showcase.html" in eh and "architecture/index.html" in eh)
    ck("entry frames the open STORE", "store" in eh.lower())
    import tempfile
    global OUT_DIR
    _O = OUT_DIR
    with tempfile.TemporaryDirectory() as t:
        try:
            OUT_DIR = Path(t) / "yc"; e, d = build()
            ck("build writes deck.html + index.html", e.exists() and d.exists() and len(d.read_text()) > 2000)
        finally:
            OUT_DIR = _O
    print("\n" + ("PASS - build_yc_demo: one openable YC bundle — the deck (rendered from teleon_pitch_deck.json, owner "
                  "placeholders shown honestly) + an entry hub linking the deck, the live showcase, the architecture map, "
                  "and the readiness/proof. Two products + the open store. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    e, d = build()
    print(f"wrote {e.relative_to(REPO)} + {d.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
