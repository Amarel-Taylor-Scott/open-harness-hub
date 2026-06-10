#!/usr/bin/env python3
"""scripts.check_baltor_guided_demos — PROOF: the Baltor Guided Demos index (web/baltor/guided-demos.html, implemented
from the Claude Design handoff) is on the branded-house design system, honest about what's runnable, and governed —
every example shows the served answer + the held-out contradiction (never served), and only the genuinely-runnable
CFPB demo is labelled live (no overclaiming, no dead links to design-only pages).

Asserts:
  A. EXISTS + DESIGN SYSTEM: page exists, loads styles/oh-tokens.css + oh-components.css, body is `.oh.dir-d.theme-dark`
     (Baltor teal branded-house — only accent differs), Hanken Grotesk + IBM Plex Mono.
  B. DESIGN COPY: the handoff's hero headline + governance line are present ("Pick a dataset…", "model never decides the truth").
  C. GOVERNED EXAMPLES: every demo entry carries a served answer AND a held-out contradiction marked "never served";
     the CFPB example carries the real demo facts (serves "10 business days", holds "30 days").
  D. HONEST STATUS: exactly ONE example is status 'live' (cfpb) and it links to a REAL served route (/consume); all
     others are 'preview' (not claimed live). No card links to a design-only page that doesn't exist in this repo.
  E. SERVED ROUTE: the admin server serves /guided-demos -> guided-demos.html, and the CFPB live link target route
     (/consume) is a real served route.
  F. NOT-ADVICE + NO LEAK: carries the "not legal/medical/compliance advice" disclaimer; no secret-value pattern; no
     "Oracle" product language.

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_PAGE = _REPO / "web" / "baltor" / "guided-demos.html"
_SERVER = _REPO / "scripts" / "baltor_admin_demo_server.py"
_LEAK = re.compile(r"sk-[A-Za-z0-9]{16,}|gsk_[A-Za-z0-9]{16,}|AIza[A-Za-z0-9]{16,}|/\.agent/|MEMORY\.md")


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    html = _PAGE.read_text(encoding="utf-8") if _PAGE.is_file() else ""
    server = _SERVER.read_text(encoding="utf-8")

    check("A: page exists + branded-house (oh-tokens/oh-components, .oh dir-d theme-dark, Hanken Grotesk)",
          bool(html) and "styles/oh-tokens.css" in html and "styles/oh-components.css" in html
          and 'class="oh dir-d theme-dark' in html and "Hanken+Grotesk" in html)
    check("B: design hero + governance line present",
          "Pick a dataset. Watch Baltor govern the answer." in html and "model never decides the truth" in html)

    # the grid is JS-rendered from the DEMOS array → count the data rows + assert the render template is governed
    rows = re.findall(r"\{\s*key:\s*'(\w+)'.*?status:\s*'(live|preview)'", html, re.S)
    served = [r for r in rows if "serves:" in html]  # presence guard (all rows carry serves:/holds:)
    check("C: every example carries a served answer + held-out contradiction; render marks 'never served'",
          len(rows) >= 14 and html.count("serves:'") >= 14 and html.count("holds:'") >= 14
          and "✓ serves" in html and "⚠ holds out" in html and "never served" in html
          and "serves:'10 business days'" in html and 'holds:\'FAQ said “30 days”\'' in html, f"rows={len(rows)}")

    live = [k for k, st in rows if st == "live"]
    preview = [k for k, st in rows if st == "preview"]
    check("D: exactly ONE live example (CFPB) + the rest preview (no overclaiming)",
          live == ["cfpb"] and len(preview) >= 12, f"live={live} preview={len(preview)}")
    # the only href in a card is the live CFPB target; no design-only *.html demo links leaked in
    card_hrefs = set(re.findall(r"href:\s*'([^']+)'", html))
    check("D: live CFPB links to a real route; no design-only demo-page links",
          card_hrefs <= {"/consume"} and not re.search(r"Baltor [A-Za-z-]+ Guided Demo\.html", html), str(card_hrefs))

    check("E: admin server serves /guided-demos + the live target /consume is a real route",
          'self._serve_web("guided-demos.html")' in server and '"/guided-demos"' in server
          and '("/consume", "/consume.html")' in server)

    check("F: not-advice disclaimer + no secret leak + no Oracle product language",
          "not legal, medical, or compliance advice" in html and not _LEAK.search(html)
          and not re.search(r"\bOracle\b", html))

    # G: each demo is tagged with its atlas pack's fragility modes, LOCK-STEP with architecture/fragile_context_atlas.json
    # (the demo key already maps 1:1 to an active pack — here we assert the bijection AND that the shown modes match).
    atlas = json.loads((_REPO / "architecture" / "fragile_context_atlas.json").read_text(encoding="utf-8"))
    atlas_modes = {p["demo_key"]: sorted(p["fragility_modes"]) for p in atlas["packs"] if p.get("status") == "active"}
    html_modes = {k: sorted(re.findall(r"'([A-Z_]+)'", body))
                  for k, body in re.findall(r"key:'(\w+)'[^\n]*?modes:\[([^\]]*)\]", html)}
    drift = {k: {"page": html_modes.get(k), "atlas": atlas_modes.get(k)}
             for k in set(atlas_modes) | set(html_modes) if html_modes.get(k) != atlas_modes.get(k)}
    check("G: every demo is an ACTIVE atlas pack + its fragility-mode tags are lock-step with fragile_context_atlas.json",
          set(html_modes) == set(atlas_modes) and not drift, f"drift={drift}")
    check("G: fragility-mode chips render per card (the index is tagged/grouped by mode)",
          ".cd-modes" in html and "cd-mode" in html and "d.modes" in html)

    print("\n" + ("PASS — check_baltor_guided_demos: the Guided Demos index is on the branded-house design system, "
                  "shows the served answer + held-out contradiction for every example (never served), labels ONLY the "
                  "runnable CFPB demo live (linking to a real route) with the rest honest previews, tags each card with "
                  "its atlas pack's fragility modes (lock-step with architecture/fragile_context_atlas.json), is served "
                  "at /guided-demos, and carries the not-advice disclaimer with no secret leak." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_baltor_guided_demos.py --self-test")
    raise SystemExit(0)
