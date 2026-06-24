"""build_capability_mvp — the MVP showcase: the whole federation wired up, end to end, funneling to enterprise.

Computes the federation's LIVE responses (the reinvention guardrail + federated build-a-capability search over the
registries) and bakes them into a self-contained, offline HTML showcase at dist/capability-mvp/index.html. It is
the open, demoable surface that shows every layer working — and funnels to the capability-defined enterprise tools
(Teleon = compile/run/govern; Baltor = governed truth). Numbers are COMPUTED from registry_ontology (no magic).
serves_truth=false (the showcase grounds 'what exists', never asserts truth).

  python3 scripts/build_capability_mvp.py            # build dist/capability-mvp/index.html
  python3 scripts/build_capability_mvp.py --self-test
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.registry import available  # noqa: E402
from src.teleon.registry.reinvention_guard import check as guard_check  # noqa: E402
from src.teleon.registry.search import build_capability  # noqa: E402

_ONT = _REPO / "architecture" / "registry_ontology.json"
_OUT = _REPO / "dist" / "capability-mvp" / "index.html"

_GUARD_INTENTS = [
    "Let me write a function to parse a PDF and extract its text from scratch",
    "I'll implement my own address validation and geocoding",
    "Let me build a CSV parsing utility from scratch",
    "Let me build a novel quantum-resistant consensus protocol from scratch",
]
_BUILD_INTENT = "address verification"
_LAYER_LABELS = {
    "layer0_discovery": "Discovery", "layer1_capability": "Capability", "layer2_execution": "Execution",
    "layer3_optimization": "Optimization", "layer4_verification": "Verification",
}


def _compute() -> dict:
    doc = json.loads(_ONT.read_text())
    regs = doc.get("registries", [])
    layers = {k: len(v.get("registry_ids", [])) for k, v in doc.get("universes", {}).items()
              if isinstance(v, dict) and "registry_ids" in v}
    guard = []
    for intent in _GUARD_INTENTS:
        r = guard_check(intent)
        existing = {dom: [h["name"] for h in hits][:3] for dom, hits in r.get("existing", {}).items()} if r["fire"] else {}
        guard.append({"intent": intent, "fire": r["fire"], "existing": existing, "reason": r.get("reason", "")})
    build = {reg: items[:4] for reg, items in build_capability(_BUILD_INTENT)["ingredients_by_registry"].items() if items}
    return {
        "n_registries": len(regs),
        "status": dict(Counter(r["status"] for r in regs)),
        "layers": layers,
        "menu": len(available()),
        "guard": guard,
        "build_intent": _BUILD_INTENT,
        "build": build,
    }


def _render(d: dict) -> str:
    e = html.escape
    bars = "".join(
        f'<div class="bar"><span class="lbl">{_LAYER_LABELS.get(k, k)}</span>'
        f'<span class="track"><span class="fill" style="width:{int(100 * v / max(d["layers"].values()))}%"></span></span>'
        f'<span class="num">{v}</span></div>'
        for k, v in d["layers"].items()
    )
    guard_rows = ""
    for g in d["guard"]:
        if g["fire"]:
            chips = " ".join(f'<code>{e(x)}</code>' for items in g["existing"].values() for x in items)
            guard_rows += (f'<div class="g fire"><div class="verdict">REINVENTION</div>'
                           f'<div class="gi">“{e(g["intent"])}”</div>'
                           f'<div class="gx">already exists → {chips}</div></div>')
        else:
            guard_rows += (f'<div class="g quiet"><div class="verdict ok">BUILD IT</div>'
                           f'<div class="gi">“{e(g["intent"])}”</div>'
                           f'<div class="gx">{e(g["reason"]) or "genuinely novel — nothing to reuse"}</div></div>')
    build_rows = "".join(
        f'<div class="b"><span class="breg">{e(reg)}</span><span class="bing">{e(", ".join(items))}</span></div>'
        for reg, items in d["build"].items()
    )
    backed = d["status"].get("live", 0) + d["status"].get("partial", 0)
    return _CSS.replace("__N__", str(d["n_registries"])).replace("__BACKED__", str(backed)) \
        .replace("__MENU__", str(d["menu"])).replace("__LIVE__", str(d["status"].get("live", 0))) \
        .replace("__BARS__", bars).replace("__GUARD__", guard_rows) \
        .replace("__BUILDINTENT__", e(d["build_intent"])).replace("__BUILD__", build_rows)


_CSS = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>The Capability Federation — what already exists</title>
<style>
:root{--bg:#0b0e14;--panel:#121723;--line:#1f2738;--ink:#e6edf7;--dim:#8a97ad;--ember:#d2542f;--ok:#2f9e6e;--accent:#5b7cf0}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 -apple-system,Segoe UI,Inter,system-ui,sans-serif}
.wrap{max-width:980px;margin:0 auto;padding:0 22px}
.hero{padding:80px 0 34px}.kicker{color:var(--accent);font-weight:600;letter-spacing:.12em;text-transform:uppercase;font-size:12px}
h1{font-size:46px;line-height:1.05;margin:14px 0 12px;letter-spacing:-.02em}h1 .em{color:var(--ember)}
.sub{color:var(--dim);font-size:19px;max-width:680px}
.stats{display:flex;gap:30px;margin:30px 0 6px;flex-wrap:wrap}.stat .v{font-size:30px;font-weight:700}.stat .k{color:var(--dim);font-size:13px}
section{padding:30px 0;border-top:1px solid var(--line)}h2{font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--dim);margin:0 0 16px}
.g{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--ember);border-radius:9px;padding:14px 16px;margin-bottom:10px}
.g.quiet{border-left-color:var(--ok)}
.verdict{font-size:11px;font-weight:700;letter-spacing:.1em;color:var(--ember)}.verdict.ok{color:var(--ok)}
.gi{font-size:17px;margin:3px 0 6px}.gx{color:var(--dim);font-size:14px}
code{background:#0c1119;border:1px solid var(--line);border-radius:5px;padding:1px 7px;color:var(--ink);font-size:13px;margin:0 2px}
.b{display:flex;gap:14px;padding:8px 0;border-bottom:1px solid var(--line)}.breg{color:var(--accent);min-width:170px;font-family:ui-monospace,monospace;font-size:13px}.bing{color:var(--ink)}
.bar{display:flex;align-items:center;gap:12px;margin:7px 0}.lbl{min-width:110px;color:var(--dim);font-size:14px}
.track{flex:1;height:9px;background:#0c1119;border-radius:6px;overflow:hidden}.fill{display:block;height:100%;background:linear-gradient(90deg,var(--accent),var(--ember))}.num{min-width:28px;text-align:right;color:var(--ink);font-weight:600}
.funnel{background:linear-gradient(180deg,#121723,#0d1119);border:1px solid var(--line);border-radius:14px;padding:30px;margin:14px 0 60px}
.funnel h3{font-size:24px;margin:0 0 10px}.funnel p{color:var(--dim);margin:0 0 18px;max-width:640px}
.cta{display:inline-flex;gap:10px}.btn{display:inline-block;padding:11px 20px;border-radius:9px;font-weight:600;text-decoration:none}
.btn.p{background:var(--ember);color:#fff}.btn.s{border:1px solid var(--line);color:var(--ink)}
.note{color:var(--dim);font-size:12px;padding:24px 0 50px;border-top:1px solid var(--line)}
</style></head><body><div class="wrap">
<div class="hero"><div class="kicker">AI, done right · open capability index</div>
<h1>Most AI rebuilds <span class="em">what already exists.</span><br>This is the index that knows.</h1>
<p class="sub">A governed federation of <b>__N__ registries</b> — tools, models, sources, standards, formulas, strategies — that an agent searches to <b>build</b>, <b>troubleshoot</b>, and <b>improve</b> a capability instead of regenerating it from scratch.</p>
<div class="stats">
<div class="stat"><div class="v">__N__</div><div class="k">registries, 5 layers</div></div>
<div class="stat"><div class="v">__BACKED__</div><div class="k">backed by real modules</div></div>
<div class="stat"><div class="v">__MENU__</div><div class="k">live on the search menu</div></div>
<div class="stat"><div class="v">__LIVE__</div><div class="k">fully live registries</div></div>
</div></div>

<section><h2>The reinvention guardrail · grounded, not vibes</h2>
<p class="sub" style="margin-bottom:18px">Fires only when a solution genuinely exists in the federation — silent on the actually-novel. The precision <i>is</i> the product.</p>
__GUARD__</section>

<section><h2>Build a capability · “__BUILDINTENT__”</h2>
<p class="sub" style="margin-bottom:14px">One query, every registry — the ingredients to compose a verified DAG.</p>
__BUILD__</section>

<section><h2>The federation · __N__ registries across 5 layers</h2>__BARS__</section>

<div class="funnel"><h3>This is the open index. The enterprise layer runs it.</h3>
<p>The federation grounds <i>what exists</i>. <b>Teleon</b> compiles a capability request into the cheapest verified execution graph over it, runs it, and proves it with receipts. <b>Baltor</b> governs the truth the capabilities serve. The open index funnels into the capability-defined runtime.</p>
<div class="cta"><a class="btn p" href="#">Teleon — compile · run · govern →</a><a class="btn s" href="#">Baltor — governed context →</a></div></div>

<div class="note">serves_truth = false — this index grounds pointers + shapes (“what exists”), never truth; a verification rail disposes truth. All counts computed from architecture/registry_ontology.json. Governed: discovery ≠ trust.</div>
</div></body></html>"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    d = _compute()
    htmldoc = _render(d)

    if not args.self_test:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        _OUT.write_text(htmldoc)
        print(f"wrote {_OUT.relative_to(_REPO)} ({len(htmldoc)} bytes): {d['n_registries']} registries, "
              f"{sum(1 for g in d['guard'] if g['fire'])} reinvention fires, {len(d['build'])} build-registries")
        return 0

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    ck("computes all registries (not hand-typed)", d["n_registries"] >= 90, str(d["n_registries"]))
    ck("the guardrail FIRES on a solved problem (grounded)", any(g["fire"] for g in d["guard"]))
    ck("the guardrail stays QUIET on novel work (precision)", any(not g["fire"] for g in d["guard"]))
    ck("build-a-capability returns ingredients across registries", len(d["build"]) >= 2, str(list(d["build"])))
    ck("html renders the count + the funnel + governance note", all(
        s in htmldoc for s in (str(d["n_registries"]), "Teleon", "Baltor", "serves_truth = false")))
    ck("html is self-contained (inline css, no external deps)", "<style>" in htmldoc and "http" not in htmldoc.split("</style>")[0])

    if fails:
        print(f"\nFAIL - build_capability_mvp: {len(fails)} of {checks} assertions failed")
        return 1
    print(f"PASS - build_capability_mvp: MVP showcase wires the whole federation ({d['n_registries']} registries) "
          f"end-to-end — guardrail + build-a-capability live, funnels to Teleon/Baltor; {checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
