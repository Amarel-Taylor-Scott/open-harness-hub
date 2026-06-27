#!/usr/bin/env python3
"""scripts.check_baltor_design_system — PROOF: the Baltor SPA implements the canonical OpenHarness/AI Done Right
"branded house" design system (from the Claude Design bundle), on Baltor's own dir-d (teal) scope, while the shared
design files stay the single source and our Baltor-specific additions are preserved.

Asserts:
  A. BRAND SCOPE: the Baltor React SPA mounts under the runtime scope `'oh ' + BRANDCE.dir + ' theme-…'`
     (ce-main.jsx), where BRANDCE = PRODUCTS.contextEnrichment, whose dir is Baltor's canonical teal scope
     dir-d (not dir-s). (The scope is applied by the React shell at mount, not hardcoded in index.html.)
  B. FONTS: index.html loads Hanken Grotesk (display) + IBM Plex Mono; the stale Space Grotesk / JetBrains Mono are gone.
  C. TOKENS: oh-tokens.css gives dir-d the teal accent (#0e7c86 light / #2dd4bf dark) + Hanken Grotesk display.
  D. CANONICAL PRIMITIVE + SCALE: oh-components.css carries the shared card surface (.oh-card + .pt-panel alias) and
     the canonical scale vars (--fs-h1, --pad-card, --maxw-site) — "change a primitive here → every site updates".
  E. PRESERVED: our Baltor-SPA additions survived the adoption (the .oh-prog build-checklist bars).
  F. SPEC PERSISTED: the design spec is durable in-repo (docs/design/aidoneright-claude-design: FAMILY-README +
     HANDOFF + shared/oh-tokens.css).
  G. BRANDED-HOUSE RULE: proto.css declares NO hardcoded display font — it sizes/types via var(--font-*) tokens.

Deterministic + offline (static checks). Exit 0/1.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_W = _REPO / "web" / "baltor"


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    idx = (_W / "index.html").read_text()
    tokens = (_W / "styles" / "oh-tokens.css").read_text()
    comp = (_W / "styles" / "oh-components.css").read_text()
    proto = (_W / "styles" / "proto.css").read_text()
    ce_main = (_W / "ce-main.jsx").read_text()
    ce_store = (_W / "ce-store.jsx").read_text()
    products = (_W / "kit" / "products.js").read_text()
    # the React shell mounts the app under Baltor's runtime scope (ce-main.jsx) → BRANDCE.dir, and
    # BRANDCE is PRODUCTS.contextEnrichment (ce-store.jsx), whose own dir is the canonical teal dir-d.
    # The first `dir: '…'` after the contextEnrichment key is that block's dir field.
    _ce_dir = re.search(r"dir: '(dir-[a-z])'", products[products.find("contextEnrichment:"):])
    ce_dir = _ce_dir.group(1) if _ce_dir else None

    check("A: SPA mounts under the Baltor dir-d (teal) runtime scope (not dir-s)",
          "'oh ' + BRANDCE.dir + ' theme-'" in ce_main
          and "BRANDCE = PRODUCTS.contextEnrichment" in ce_store
          and 'src="ce-main.jsx"' in idx
          and ce_dir == "dir-d", f"contextEnrichment.dir={ce_dir}")
    check("B: loads Hanken Grotesk + IBM Plex Mono; no stale Space Grotesk/JetBrains",
          "Hanken+Grotesk" in idx and "IBM+Plex+Mono" in idx and "Space+Grotesk" not in idx and "JetBrains" not in idx)
    check("C: dir-d teal accent + Hanken display in tokens",
          "#0e7c86" in tokens and "#2dd4bf" in tokens and 'dir-d { --font-display: "Hanken Grotesk"' in tokens)
    check("D: canonical card primitive + scale in oh-components",
          ".oh-card" in comp and ".pt-panel" in comp and "--fs-h1" in comp and "--pad-card" in comp and "--maxw-site" in comp)
    check("E: Baltor-SPA additions preserved (.oh-prog)", ".oh-prog" in comp)
    DD = _REPO / "docs" / "design" / "aidoneright-claude-design"
    check("F: design spec persisted in-repo",
          (DD / "FAMILY-README.md").exists() and (DD / "HANDOFF.md").exists() and (DD / "shared" / "oh-tokens.css").exists())
    check("G: proto.css has no hardcoded display font (uses var(--font-*))",
          "Space Grotesk" not in proto and "Hanken Grotesk" not in proto and "var(--font-display)" in proto)

    print("\n" + ("PASS — check_baltor_design_system: the Baltor SPA implements the canonical branded-house design "
                  "(dir-d teal scope, Hanken Grotesk + IBM Plex Mono, shared card primitive + scale), preserves its "
                  "own additions, keeps proto.css on var(--font-*) tokens, and the design spec is persisted in-repo."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_baltor_design_system.py --self-test")
    raise SystemExit(0)
