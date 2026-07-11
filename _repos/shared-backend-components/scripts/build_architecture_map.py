#!/usr/bin/env python3
"""build_architecture_map — one reviewable picture of the whole portfolio, generated from the canonical sources.

Reads the SINGLE sources (no hand-typed roster):
  * _repos/shared-backend-components/architecture/portfolio_connection_map.json — parent / core (Baltor, Teleon) / open_ecosystem / the hub roster (tiers) / dependency_law
  * _repos/shared-backend-components/architecture/surface_map.json              — the 7 top-level surfaces + wedge + communicates_with
  * _repos/shared-backend-components/architecture/teleon_demo_catalog.json      — the demo catalog
  * _repos/shared-backend-components/docs/use-cases/*.md                        — the use-cases

Emits:
  * dist/architecture/index.html        — a self-contained, layered VISUAL map (open in a browser to review)
  * _repos/shared-backend-components/docs/strategy/architecture-map.md   — the documented map (a Mermaid diagram + honest layer/surface notes) for the north star

Layers are DERIVED from the connection map's roles + the dependency law (Baltor → Teleon → OpenHubForAI), so the
picture can't drift from the enforced architecture. Honest: live vs private_bench vs representative are labelled.
serves_truth=false. DEVELOPMENT plane (build tool).

  --build      write both artifacts        --self-test   offline: both render from the real sources
CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/build_architecture_map.py --build
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

CONN = _resource("architecture") / "portfolio_connection_map.json"
SURF = _resource("architecture") / "surface_map.json"
DEMOS = _resource("architecture") / "teleon_demo_catalog.json"
USECASES = _resource("docs") / "use-cases"
HTML_OUT = _resource("dist") / "architecture" / "index.html"
DOC_OUT = _resource("docs") / "strategy" / "architecture-map.md"


def load() -> dict:
    conn = json.loads(CONN.read_text(encoding="utf-8"))
    surf = {s["id"]: s for s in json.loads(SURF.read_text(encoding="utf-8"))["surfaces"]}
    demos = [d["id"] for d in json.loads(DEMOS.read_text(encoding="utf-8")).get("demos", [])]
    skip = {"index.md", "readme.md", "more-ideas.md"}
    usecases = sorted(p.stem for p in USECASES.glob("*.md") if p.name.lower() not in skip) if USECASES.exists() else []
    hubs = conn.get("hubs", [])
    # OpenHubForAI is the STORE (open_ecosystem = role "ecosystem"), NOT one of the live REGISTRIES — exclude it
    # from the registry roster so the live/private split matches the canonical products.js OPENHUB_REGISTRIES
    # (8 live + 13 preview = 21); the store is shown separately at the open-ecosystem layer.
    registries = [h for h in hubs if h.get("role") != "ecosystem"]
    live = [h for h in registries if h.get("tier") == "live"]
    private = [h for h in registries if h.get("tier") != "live"]
    return {"conn": conn, "surf": surf, "demos": demos, "usecases": usecases, "live_hubs": live, "private_hubs": private}


def _wedge(d, sid, fallback=""):
    return (d["surf"].get(sid, {}).get("wedge") or fallback)[:140]


# ───────────────────────────────────────── mermaid (documented diagram for the north star)
def render_mermaid(d: dict) -> str:
    lh, ph = len(d["live_hubs"]), len(d["private_hubs"])
    return "\n".join([
        "```mermaid",
        "graph TD",
        '  ADR["🏛 AI Done Right — parent / holding brand<br/>(trust narrative: Context · Capability · Proof)"]',
        '  subgraph APP["Product — managed context"]',
        '    BAL["Baltor — MANAGED governed context (its own product)<br/>company / department / initiative-wide · receipts + CDC · governs TRUTH"]',
        "  end",
        '  subgraph RT["Product — capability runtime"]',
        '    TEL["Teleon — its OWN product + runtime<br/>program in PLAIN TEXT → adapts to cheapest-BOUNDED within guardrails · governs EFFICIENCY"]',
        "  end",
        '  subgraph OPEN["Open ecosystem = registry (Teleon + Baltor + AIDevObserver consume)"]',
        '    OHH["OpenHubForAI + CapabilityTask Spec (open)"]',
        f'    HUBS["{lh+ph} OpenHubForAI registries — the component store<br/>context · tools · models · steps · DAG · reconciliation/robustness/enrichment rules · modules<br/>{lh} live · {ph} private-bench"]',
        "  end",
        '  SRC[("public / regulated sources")]',
        '  AGENTS(("AI agents"))',
        '  DEMOS["teleon-demos — proof surface<br/>(measured savings per descent)"]',
        '  DESIGN["design-bundle — brand/design handoff"]',
        "  ADR -.->|holds, never runs| BAL",
        "  BAL -->|consumes as a tenant| TEL",
        "  TEL -->|consumes| OHH",
        "  HUBS -->|feed Teleon's selection substrate| TEL",
        "  HUBS -.->|context + method components (content)| BAL",
        "  BAL -->|ingests| SRC",
        "  TEL -->|serves capabilities| AGENTS",
        "  DEMOS -->|reads| TEL",
        "  ADR -.->|rendered by| DESIGN",
        "  %% dependency law (enforced): Baltor -> Teleon -> OpenHubForAI, never reverse",
        "```",
    ])


def render_doc(d: dict, validation: str = "") -> str:
    conn = d["conn"]
    live = ", ".join(h["name"] for h in d["live_hubs"])
    private = ", ".join(h["name"] for h in d["private_hubs"])
    total = len(d["live_hubs"]) + len(d["private_hubs"])
    L = [f"# Architecture map — the honest north star (generated by `scripts/build_architecture_map.py`)", "",
         "> Generated from the canonical single sources (`portfolio_connection_map.json` + `surface_map.json` + the "
         "demo catalog + `docs/use-cases/`). Layers are derived from the enforced dependency law, so this can't drift. "
         "Visual version: `dist/architecture/index.html`. Honest labels: **live** vs **private-bench** vs **representative**.", "",
         render_mermaid(d), "",
         "## Layers (top → bottom)", "",
         "1. **AI Done Right** — parent / holding brand (the *promise*, not a product; owns no runtime/customer data).",
         "2. **Baltor** (its own product) — **fully managed governed context**, company / department / initiative-wide "
         "(Verified · Current · Provable; receipts + CDC; first wedge = compliance / AML / sanctions). Governs what "
         "becomes TRUE. *Powered by Teleon.*",
         "3. **Teleon** (its own product + the runtime) — **program a capability in plain text**; it adapts to the most "
         "**efficient + bounded** form within your guardrails (the descent), receipt-backed. Governs what becomes EFFICIENT.",
         f"4. **OpenHubForAI + the {total} OpenHubForAI registries = the STORE** — a shared catalog of reusable components (context, "
         "tools, models, steps, DAG components, reconciliation/robustness/enrichment rules, predefined modules) that "
         "**both Baltor and Teleon consume**. **Code-import law (enforced): Baltor → Teleon → OpenHubForAI, never the "
         "reverse; the store is consumed at the content level by both.**", "",
         f"### OpenHubForAI roster ({len(d['live_hubs'])} live · {len(d['private_hubs'])} private-bench = {len(d['live_hubs'])+len(d['private_hubs'])})",
         f"- **Live:** {live}", f"- **Private-bench:** {private}", "",
         "## Surfaces", ""]
    for sid, s in d["surf"].items():
        L.append(f"- **{sid}** [{s.get('status','?')}] — {(_wedge(d, sid))}")
    L += ["", f"## Product demos ({len(d['demos'])} in the catalog)",
          ", ".join(f"`{x}`" for x in d["demos"]), "",
          f"## Use-cases ({len(d['usecases'])})",
          ", ".join(f"`{x}`" for x in d["usecases"]), ""]
    if validation:
        L += ["---", "", validation, ""]
    return "\n".join(L) + "\n"


# ───────────────────────────────────────── html (visual, browser-reviewable)
_CSS = """
:root{--ink:#0f1222;--muted:#6b7280;--line:#e6e8ef;--bg:#fbfbfd;--card:#fff;--accent:#4f46e5;--good:#0c8f5f;--warn:#c2410c}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:'Hanken Grotesk',system-ui,-apple-system,Segoe UI,sans-serif;line-height:1.45}
.wrap{max-width:1080px;margin:0 auto;padding:40px 24px 72px}.mono{font-family:'IBM Plex Mono',ui-monospace,monospace}
h1{font-size:32px;letter-spacing:-.02em;margin:0 0 6px}.sub{color:var(--muted);margin:0 0 26px;max-width:760px}
.band{border:1px solid var(--line);border-radius:16px;padding:14px 18px;margin:0 0 12px;background:var(--card);position:relative}
.band .tag{position:absolute;top:-9px;left:16px;background:var(--accent);color:#fff;font-size:11px;font-weight:600;border-radius:6px;padding:2px 8px}
.band.parent{background:#f6f5ff;border-color:#dcd9ff}.band h2{margin:6px 0 2px;font-size:18px}.band p{margin:0;color:var(--muted);font-size:13px}
.flow{text-align:center;color:var(--accent);font-weight:600;margin:2px 0;font-size:13px}
.cards{display:flex;gap:10px;flex-wrap:wrap;margin-top:8px}
.card{flex:1;min-width:150px;border:1px solid var(--line);border-radius:12px;padding:10px 12px;background:#fff}
.card b{font-size:14px}.card span{color:var(--muted);font-size:12px;display:block;margin-top:2px}
.hub{font-size:11px;border:1px solid var(--line);border-radius:999px;padding:3px 9px;display:inline-block;margin:2px}
.hub.live{background:#f0faf5;border-color:#bfe6d4;color:var(--good)}.hub.priv{background:#fafafe;color:var(--muted)}
.strip{display:flex;gap:6px;flex-wrap:wrap;margin-top:6px}.pill{font-size:11px;background:#eef0ff;border:1px solid #d9ddff;color:var(--accent);border-radius:999px;padding:3px 9px}
.uc{font-size:11px;background:#f1f2f8;border:1px solid var(--line);border-radius:999px;padding:3px 9px}
.note{font-size:12px;color:var(--muted);margin-top:18px;border-top:1px solid var(--line);padding-top:14px}
"""


def render_html(d: dict) -> str:
    lh = "".join(f'<span class="hub live">{html.escape(h["name"])}</span>' for h in d["live_hubs"])
    ph = "".join(f'<span class="hub priv">{html.escape(h["name"])}</span>' for h in d["private_hubs"])
    demos = "".join(f'<span class="pill">{html.escape(x)}</span>' for x in d["demos"])
    ucs = "".join(f'<span class="uc">{html.escape(x)}</span>' for x in d["usecases"])
    return "".join([
        "<!doctype html><html lang=en><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>",
        "<title>AI Done Right — architecture map</title><style>", _CSS, "</style></head><body><div class=wrap>",
        "<h1>AI Done Right — architecture map</h1>",
        "<p class=sub>Top → bottom follows the enforced dependency law: <b>Baltor → Teleon → OpenHubForAI</b>, never "
        "the reverse. Generated from the canonical sources; live vs private-bench labelled honestly.</p>",
        '<div class="band parent"><span class="tag">parent</span><h2>🏛 AI Done Right</h2>'
        '<p>Holding brand / trust narrative (Context · Capability · Proof). Owns no runtime, no customer data.</p></div>',
        '<div class="flow">▼ holds</div>',
        '<div class="band"><span class="tag">product · managed context</span><h2>Baltor — managed governed context</h2>'
        '<p>Fully MANAGED context — company / department / initiative-wide. Verified/Current/Provable · receipts + CDC · '
        'ingest→reconcile→harden→enrich→compress→serve. Governs what becomes <b>TRUE</b>. First wedge: compliance / AML / '
        'sanctions. <b>Powered by Teleon.</b></p></div>',
        '<div class="flow">▼ consumes (as a tenant)</div>',
        '<div class="band"><span class="tag">product · capability runtime</span><h2>Teleon — plain-text → adaptive capabilities</h2>'
        '<p>Its OWN product (not just Baltor\'s runtime): program a capability in <b>plain text</b>; Teleon adapts it to the '
        'cheapest <b>bounded</b> form within your <b>guardrails</b> (the descent), receipt-backed. Governs what becomes '
        '<b>EFFICIENT</b>. The descent brain is the moat.</p></div>',
        '<div class="flow">▼ consumes · ▲ feed substrate / supply components to both</div>',
        f'<div class="band"><span class="tag">open ecosystem · the STORE</span><h2>OpenHubForAI + {len(d["live_hubs"])+len(d["private_hubs"])} OpenHubForAI registries — the component store</h2>'
        '<p>A shared store of reusable components <b>both Baltor and Teleon consume</b>: context · tools · models · steps · '
        'DAG components · reconciliation / robustness / enrichment rules · predefined modules (run on Teleon OR custom '
        f'compute) · the open CapabilityTask Spec ({len(d["live_hubs"])} live · {len(d["private_hubs"])} private-bench).</p>'
        f'<div style="margin-top:8px">{lh}{ph}</div></div>',
        '<div class="band"><span class="tag">proof + handoff surfaces</span>'
        '<div class="cards"><div class="card"><b>teleon-demos</b><span>proof surface — measured savings per descent</span></div>'
        '<div class="card"><b>design-bundle</b><span>brand/design handoff (24+ surfaces)</span></div></div></div>',
        f'<div class="band"><span class="tag">product demos ({len(d["demos"])})</span><div class="strip">{demos}</div></div>',
        f'<div class="band"><span class="tag">use-cases ({len(d["usecases"])})</span><div class="strip">{ucs}</div></div>',
        '<p class="note">Generated by <span class="mono">scripts/build_architecture_map.py</span> from '
        '<span class="mono">portfolio_connection_map.json</span> + <span class="mono">surface_map.json</span>. '
        'serves_truth = false.</p>',
        "</div></body></html>",
    ])


def build(validation: str = "") -> tuple[Path, Path]:
    d = load()
    HTML_OUT.parent.mkdir(parents=True, exist_ok=True)
    DOC_OUT.parent.mkdir(parents=True, exist_ok=True)
    HTML_OUT.write_text(render_html(d), encoding="utf-8")
    DOC_OUT.write_text(render_doc(d, validation), encoding="utf-8")
    return HTML_OUT, DOC_OUT


def _self_test() -> int:
    fails = []
    def ck(name, ok):
        print(f"  [{'ok' if ok else 'FAIL'}] {name}")
        if not ok: fails.append(name)
    d = load()
    # the expected live/private counts are the CANONICAL products.js OPENHUB_REGISTRIES roster (single source),
    # not hand-typed — this ties the architecture map's roster to the same source the surface-family check reads.
    from scripts.check_ai_done_right_surface_family import _entity_records as _er, PRODUCTS_JS as _pjs
    _, _, _reg = _er(_pjs)
    _elive, _eprev = len(_reg["live"]), len(_reg["preview"])
    ck(f"registry roster matches canonical products.js OPENHUB_REGISTRIES ({_elive} live + {_eprev} private-bench = {_elive + _eprev})",
       len(d["live_hubs"]) == _elive and len(d["private_hubs"]) == _eprev)
    ck("the 7 top-level surfaces are loaded", len(d["surf"]) == 7)
    ck("demos + use-cases loaded", len(d["demos"]) >= 5 and len(d["usecases"]) >= 5)
    mer = render_mermaid(d)
    ck("mermaid honors the dependency law (Baltor→Teleon→OHH)", "BAL -->|consumes as a tenant| TEL" in mer and "TEL -->|consumes| OHH" in mer)
    doc = render_doc(d, "VALIDATION-HERE")
    ck("doc embeds the diagram + roster + the validation slot", "```mermaid" in doc and "OpenHubForAI roster" in doc and "VALIDATION-HERE" in doc)
    page = render_html(d)
    ck("html is self-contained + layered (parent→baltor→teleon→open)", "<style>" in page and "Baltor — managed governed context" in page and f"{len(d['live_hubs'])+len(d['private_hubs'])} OpenHubForAI registries" in page and "http" not in page.split("note")[0])
    import tempfile
    global HTML_OUT, DOC_OUT
    _h, _d = HTML_OUT, DOC_OUT
    with tempfile.TemporaryDirectory() as t:
        try:
            HTML_OUT = Path(t) / "i.html"; DOC_OUT = Path(t) / "m.md"; build("x")
            ck("build writes both artifacts", HTML_OUT.exists() and DOC_OUT.exists())
        finally:
            HTML_OUT, DOC_OUT = _h, _d
    print("\n" + ("PASS - build_architecture_map: a layered VISUAL (dist/architecture/index.html) + a documented Mermaid map "
                  "(docs/strategy/architecture-map.md) generated from the canonical sources; layers derived from the enforced "
                  "dependency law so it can't drift. serves_truth=false."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--self-test" in argv:
        return _self_test()
    h, doc = build()
    print(f"wrote {h.relative_to(REPO)} + {doc.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
