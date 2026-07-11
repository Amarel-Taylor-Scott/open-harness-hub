#!/usr/bin/env python3
"""scripts.check_portfolio_no_dead_anchors — PROOF: every in-page anchor on every portfolio site resolves.

A dead in-page anchor (an `href="#x"` with no matching `id="x"`) means a CTA/nav link that scrolls nowhere. This
caught a real portfolio-wide bug: section ids are generated as the heading's first word
(`render_site`: `id="{h.lower().split(' ')[0]}"`), so hand-set CTA anchors (`#registry`, `#capabilitytask`,
`#cfpb-demo`, `#adapters`, `#thesis`) never matched a section and the flagship CTAs were dead. This proof renders
each site from the generator (source of truth) and fails if ANY `#anchor` does not resolve to an `id`.

Asserts (over scripts.portfolio_lib.render_site for every SITE_ORDER site):
  A. Every `href="#x"` has a matching `id="x"` in the same page (no dead in-page anchors).
  B. Each site's primary + secondary CTA anchors specifically resolve (the flagship links work).
  C. Deterministic (re-render identical).

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts import portfolio_lib as P

_HREF = re.compile(r'href="#([\w.-]+)"')
_ID = re.compile(r'id="([\w.-]+)"')


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    all_ok = True
    for sid in P.SITE_ORDER:
        html = P.render_site(sid)
        ids = set(_ID.findall(html))
        anchors = set(_HREF.findall(html))
        dead = sorted(a for a in anchors if a not in ids)
        check(f"A[{sid}]: every in-page anchor resolves to an id", not dead, f"dead anchors: {dead}")
        s = P.SITES[sid]
        cta_anchors = [h[1].lstrip("#") for h in (s["cta_primary"], s["cta_secondary"]) if h[1].startswith("#")]
        cta_dead = [a for a in cta_anchors if a not in ids]
        check(f"B[{sid}]: primary + secondary CTA anchors resolve", not cta_dead, f"dead CTA: {cta_dead}")
        all_ok = all_ok and not dead and not cta_dead

    check("C: deterministic (re-render identical for a sample site)",
          P.render_site(P.SITE_ORDER[0]) == P.render_site(P.SITE_ORDER[0]))

    print("\n" + ("PASS — check_portfolio_no_dead_anchors: every portfolio site's in-page anchors (incl. both CTAs) "
                  "resolve to a real section id — no dead links." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_portfolio_no_dead_anchors.py --self-test")
    raise SystemExit(0)
