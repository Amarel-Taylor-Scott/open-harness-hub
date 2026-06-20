#!/usr/bin/env python3
"""scripts.check_baltor_engine_hero_ui — PROOF: the animated Context Engine hero + its canonical language are
wired into the MAIN Baltor SPA, single-sourced from web/baltor/stages.json (no re-typed stage copy).

Asserts:
  A. SINGLE SOURCE: stages.json is valid JSON with title/eyebrow/tagline + verification_rail; EXACTLY six macro
     stages (no seventh); each stage carries num/title/kind/accent/zone_accent/copy/tags/detail; the canonical
     six stage titles are present.
  B. COMPONENT: pages/engine-hero.js registers the /engine route, defines CE.engineHeroBody + CE.initEngineHero,
     renders a <canvas id="ceFlowCanvas">, animates via requestAnimationFrame, FETCHES stages.json (single
     source), and honors prefers-reduced-motion.
  C. WIRED INTO MAIN UI: engine-hero.js is in pages/manifest.json; overview.js ("/") embeds CE.engineHeroBody();
     app.js nav links the /engine route.
  D. SINGLE-SOURCE DISCIPLINE: the distinctive stage copy lives ONLY in stages.json — not re-typed into
     engine-hero.js or overview.js.
  E. BRAND + OFFLINE: no user-facing "Oracle" product copy in the new/edited files; the component adds no
     external CDN/script (offline-first).

Deterministic + offline (static checks; no browser). Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_WEB = _REPO / "web" / "baltor"

CANONICAL_TITLES = ["Source Systems", "Reconciliation", "Anti-Fragility", "Enhancement", "Optimization", "Consumption"]
# a distinctive phrase per stage that must live ONLY in stages.json
ONLY_IN_STAGES = [
    "Deduplicates related artifacts",
    "refunds are approved after 30 days",
    "replaces brittle text with robust knowledge objects",
    "maximum allowable credit card late fee",
    "fits the result to the task budget",
    "expand approved source handles",
]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    stages_path = _WEB / "stages.json"
    hero = (_WEB / "pages" / "engine-hero.js")
    overview = (_WEB / "pages" / "overview.js")
    app = (_WEB / "app.js")
    manifest = json.loads((_WEB / "pages" / "manifest.json").read_text())

    # A — single source
    data = json.loads(stages_path.read_text())
    stages = data.get("stages", [])
    check("A: stages.json has title/eyebrow/tagline + verification_rail",
          all(data.get(k) for k in ("title", "eyebrow", "tagline")) and data.get("verification_rail"))
    check("A: EXACTLY six macro stages (no seventh)", len(stages) == 6, f"len={len(stages)}")
    need = ("num", "title", "kind", "accent", "zone_accent", "copy", "tags", "detail")
    check("A: every stage carries the required fields", all(all(k in s for k in need) for s in stages))
    titles = [s["title"] for s in stages]
    check("A: canonical six stage titles present", titles == CANONICAL_TITLES, str(titles))
    check("A: each detail has subtitle/copy/tags", all(all(k in s["detail"] for k in ("subtitle", "copy", "tags")) for s in stages))

    # B — component
    h = hero.read_text()
    check("B: registers the /engine route", 'CE.register("/engine"' in h or "CE.register('/engine'" in h)
    check("B: defines CE.engineHeroBody + CE.initEngineHero", "CE.engineHeroBody" in h and "CE.initEngineHero" in h)
    check("B: renders a <canvas id=ceFlowCanvas>", 'id="ceFlowCanvas"' in h)
    check("B: animates via requestAnimationFrame", "requestAnimationFrame" in h)
    check("B: fetches stages.json (single source)", 'fetch("stages.json")' in h or "fetch('stages.json')" in h)
    check("B: honors prefers-reduced-motion", "prefers-reduced-motion" in h)

    # C — wired into the main UI
    check("C: engine-hero.js in pages/manifest.json", "engine-hero.js" in manifest)
    ov = overview.read_text()
    check("C: overview ('/') embeds CE.engineHeroBody()", "CE.engineHeroBody(" in ov)
    check("C: app.js nav links /engine", '"/engine"' in app.read_text())

    # D — single-source discipline: distinctive copy ONLY in stages.json
    sj = stages_path.read_text()
    leaked = [p for p in ONLY_IN_STAGES if (p not in sj) or (p in h) or (p in ov)]
    check("D: distinctive stage copy lives ONLY in stages.json (not re-typed)", not leaked, "; ".join(leaked))

    # E — brand + offline
    oracle = [f.name for f, t in ((stages_path, sj), (hero, h), (overview, ov)) if "oracle" in t.lower()]
    check("E: no user-facing 'Oracle' product copy in new/edited files", not oracle, "; ".join(oracle))
    check("E: component adds no external CDN/script (offline-first)",
          "http://" not in h and "https://" not in h and "cdn" not in h.lower())

    print("\n" + ("PASS — check_baltor_engine_hero_ui: the animated Context Engine hero + its canonical six-stage "
                  "language are wired into the main Baltor SPA (overview '/' + /engine route), single-sourced from "
                  "stages.json (no re-typed copy), canvas+requestAnimationFrame, reduced-motion-aware, offline, no "
                  "Oracle product copy." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_baltor_engine_hero_ui.py --self-test")
    raise SystemExit(0)
