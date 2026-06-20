#!/usr/bin/env python3
"""build_pitch_deck — generate the Teleon pitch/demo deck (HTML slides) from architecture/teleon_pitch_deck.json,
with EVERY number computed live from the engine (proof count, the actual self-optimizing receipt, the method-catalog
+ profession + standards counts). Consistent, single-sourced language; no hand-typed metrics (the README-count bug,
but for the pitch). Self-contained HTML (dark theme, arrow-key nav, print-to-PDF friendly) for technical + investor
audiences.

  --build      (re)write the HTML deck
  --self-test  validate the deck + its live numbers (the registered proof)

CLI: PYTHONPATH=. python3 scripts/build_pitch_deck.py --build | --self-test
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DECK = _REPO / "architecture" / "teleon_pitch_deck.json"
_OUT = _REPO / "dist" / "decks" / "teleon-pitch.html"


def facts() -> dict:
    """Compute every number in the deck LIVE from the engine — nothing hand-typed."""
    from scripts.flywheel_proof_modules import PROOF_MODULES
    from src.teleon.evolution.self_optimizing_unit import demonstrate
    from src.teleon.seeds.profession_capability_seeder import PROFESSIONS

    rec = {st["dimension"]: st for st in demonstrate()["steps"]}
    cat = json.loads((_REPO / "architecture" / "descent_method_catalog.json").read_text())
    methods = [m for d in cat["dimensions"] for m in d["methods"]]
    modules = [x for m in methods for x in m["modules"]]
    std = json.loads((_REPO / "architecture" / "standards_interop_manifest.json").read_text())
    n_built = sum(1 for s in std["standards"] if s["status"] == "built")
    n = lambda v: (int(v) if float(v).is_integer() else v)
    return {
        "n_proofs": len(PROOF_MODULES),
        "receipt_tokens_before": n(rec["tokens_in"]["before"]), "receipt_tokens_after": n(rec["tokens_in"]["after"]),
        "receipt_cost_before": rec["cost"]["before"], "receipt_cost_after": n(rec["cost"]["after"]),
        "receipt_det_before": rec["determinism"]["before"], "receipt_det_after": n(rec["determinism"]["after"]),
        "receipt_fresh_before": n(rec["freshness"]["before"]), "receipt_fresh_after": n(rec["freshness"]["after"]),
        "receipt_model_before": n(rec["efficiency"]["before"]), "receipt_model_after": n(rec["efficiency"]["after"]),
        "n_dimensions": len(cat["dimensions"]), "n_methods": len(methods), "n_modules": len(modules),
        "n_professions": len(PROFESSIONS), "n_built_standards": n_built,
    }


def _subs(deck: dict) -> dict:
    s = {k: str(v) for k, v in deck["language"].items()}
    s.update({k: str(v) for k, v in facts().items()})
    return s


def _fill(text: str, subs: dict) -> str:
    return re.sub(r"\{(\w+)\}", lambda m: subs.get(m.group(1), m.group(0)), text)


def render_deck(deck: dict) -> str:
    subs = _subs(deck)
    slides_html = []
    total = len(deck["slides"])
    for i, sl in enumerate(deck["slides"], 1):
        title = html.escape(_fill(sl["title"], subs))
        sub = f'<p class="sub">{html.escape(_fill(sl["subtitle"], subs))}</p>' if sl.get("subtitle") else ""
        bullets = "".join(f'<li>{html.escape(_fill(b, subs))}</li>' for b in sl.get("bullets", []))
        note = f'<p class="note">{html.escape(_fill(sl["note"], subs))}</p>' if sl.get("note") else ""
        cls = "slide title-slide" if sl["id"] == "title" else "slide"
        slides_html.append(f'<section class="{cls}" id="s{i}"><div class="wrap"><h2>{title}</h2>{sub}'
                           f'<ul>{bullets}</ul>{note}<div class="pageno">{i}/{total} · Teleon</div></div></section>')
    body = "\n".join(slides_html)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Teleon — {html.escape(subs.get('one_liner',''))}</title>
<!-- GENERATED from architecture/teleon_pitch_deck.json by scripts/build_pitch_deck.py — numbers computed live; do not hand-edit. -->
<style>
  :root {{ --bg:#0d1117; --panel:#161b22; --line:#21262d; --fg:#e6edf3; --mut:#8b949e; --acc:#58a6ff; --ok:#3fb950; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.55 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
  .slide {{ min-height:100vh; display:flex; align-items:center; padding:6vh 8vw; border-bottom:1px solid var(--line); }}
  .title-slide h2 {{ font-size:44px; }} .title-slide {{ background:linear-gradient(160deg,#0d1117,#161b22); }}
  .wrap {{ max-width:1000px; width:100%; }}
  h2 {{ font-size:28px; margin:0 0 10px; color:var(--fg); }}
  .sub {{ color:var(--acc); font-size:18px; margin:0 0 18px; }}
  ul {{ list-style:none; padding:0; margin:0; }}
  li {{ padding:6px 0; border-bottom:1px dashed var(--line); white-space:pre-wrap; }}
  li:before {{ content:"▸ "; color:var(--acc); }}
  .note {{ color:var(--mut); font-size:13px; margin-top:18px; }}
  .pageno {{ color:var(--mut); font-size:12px; margin-top:22px; }}
  @media print {{ .slide {{ min-height:auto; page-break-after:always; border:0; }} }}
</style>
</head>
<body>
{body}
<script>
// minimal slide nav: arrow keys / space scroll between full-viewport sections (works offline; print = PDF deck)
const slides=[...document.querySelectorAll('.slide')]; let i=0;
function go(n){{ i=Math.max(0,Math.min(slides.length-1,n)); slides[i].scrollIntoView({{behavior:'smooth'}}); }}
addEventListener('keydown',e=>{{ if(['ArrowRight','ArrowDown',' '].includes(e.key)){{e.preventDefault();go(i+1);}}
  else if(['ArrowLeft','ArrowUp'].includes(e.key)){{e.preventDefault();go(i-1);}} }});
</script>
</body>
</html>
"""


def write_deck() -> str:
    _OUT.parent.mkdir(parents=True, exist_ok=True)
    _OUT.write_text(render_deck(json.loads(_DECK.read_text())))
    return str(_OUT.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    deck = json.loads(_DECK.read_text())
    f = facts()
    page = render_deck(deck)

    ck("deck has the core slides incl. the flagship self-optimizing unit",
       {s["id"] for s in deck["slides"]} >= {"title", "wedge", "flagship", "distillation", "moat", "traction"})
    ck("consistent single-source language is present (wedge + thesis + proposition)",
       all(html.escape(deck["language"][k]) in page for k in ("wedge", "thesis", "proposition")))
    # numbers are COMPUTED, not hand-typed: every {placeholder} resolves + the live receipt numbers appear
    ck("no unresolved {placeholders} remain (every number computed)", not re.search(r"\{[a-z_]+\}", page),
       str(re.findall(r"\{[a-z_]+\}", page)[:5]))
    ck("the flagship slide shows the LIVE self-optimizing receipt (real before→after numbers)",
       all(str(f[k]) in page for k in ("receipt_tokens_before", "receipt_tokens_after", "receipt_cost_before",
                                       "receipt_det_after", "receipt_model_before")))
    ck("the live proof count + method/profession/standards counts appear (computed from the engine)",
       all(str(f[k]) in page for k in ("n_proofs", "n_methods", "n_professions", "n_built_standards"))
       and f["n_proofs"] >= 500 and f["n_built_standards"] >= 4)
    ck("the distillation slide names all four context primitives (compression/fragility/enrichment/efficiency)",
       all(w in page for w in ("COMPRESSION", "FRAGILITY", "ENRICHMENT", "EFFICIENCY")))
    ck("the deck never overclaims (carries the governance + honest-gap language)",
       "PROPOSES" in page and "Honest gap" in page and deck.get("serves_truth") is False)
    # NOTE: no strict on-disk freshness check — the deck embeds the LIVE proof count (volatile; changes on every
    # proof addition), so the generated artifact is rebuilt on deploy rather than pinned. We validate the RENDER.
    ck("deterministic render (same engine state -> identical deck)", render_deck(deck) == page)

    print("\n" + (f"PASS - build_pitch_deck: {len(deck['slides'])}-slide Teleon deck generated from one source with "
                  f"LIVE numbers (proofs {f['n_proofs']}; self-optimizing receipt tokens {f['receipt_tokens_before']}→"
                  f"{f['receipt_tokens_after']}, determinism {f['receipt_det_before']}→{f['receipt_det_after']}; "
                  f"{f['n_methods']} methods; {f['n_professions']} professions; {f['n_built_standards']} built "
                  f"standards) — consistent language, no hand-typed metrics, honest about the gap."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_deck())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: build_pitch_deck.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
