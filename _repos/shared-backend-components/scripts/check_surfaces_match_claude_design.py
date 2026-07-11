#!/usr/bin/env python3
"""Contract: every product surface follows the Claude Design designs (2026-06-27).

For each surface this asserts, in the BUNDLE SOURCE the port ships from, that the design's
load-bearing copy/structure is PRESENT and the retired design-exploration scaffolding (A/B
variant pickers, experiment panels, legacy positioning, the parent Demo + two-layer model) is
ABSENT. Static + deterministic (no browser) so it runs in the offline proof gate and a future
edit that drifts a surface away from the adopted design fails here instead of silently shipping.

Companion to _repos/shared-backend-components/scripts/check_ai_done_right_surface_family.py (the products.js 4-product model) and
the port --check (web/ == bundle). serves_truth=false.

CLI:  python3 _repos/shared-backend-components/scripts/check_surfaces_match_claude_design.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
BUNDLE = _resource("dist/sites/aidoneright-design")

# (surface, bundle source file, MUST contain [design copy/structure], MUST NOT contain [retired])
CONTRACTS: list[tuple[str, Path, list[str], list[str]]] = [
    # must_not targets the rendered JSX usage ("OhExperimentsPanel />"), not the word, so the
    # retirement comments that document what was removed don't trip the contract.
    ("AI Done Right", BUNDLE / "context-is-everything" / "cie-main.jsx",
     ["Three products you run, on one shared foundation", "One open store underneath it all",
      "How it fits", "Discovery is not trust", "Your keys stay yours",
      "About AI Done Right", "Our mission", "Privacy policy", "Terms of service", "RESOURCE_IDS"],
     # no login on the overview site; humanized copy (no arrow glyphs, no em/en dashes)
     ["OhExperimentsPanel />", 'href="Demo Control Tower.html"', "Open resources",
      "one stack, two layers", "Sign in", "signInHref", "→", "—", "–"]),
    ("Baltor", BUNDLE / "context-enrichment" / "ce-landing.jsx",
     ["Canonical hero copy", "BRANDCE.hook", "LANDING_LAYOUTS.default"],
     ["ce-abset", "OhExperimentsPanel />", "const TESTS =", "Preview landing variants"]),
    ("Teleon", BUNDLE / "teleon" / "teleon-main.jsx",
     ["HERO_LINES.A", "TLN_LAYOUTS.default"],
     ["OhExperimentsPanel />", "tln-abpill", "cycleHero", "Cycle hero A/B variant"]),
    ("OpenHubForAI", BUNDLE / "openhubforai" / "proto-pages-build.jsx",
     ["The open store", "Browse the store", "navigate('/registries')"],
     ["The harness layer for production agents", "Power your agents with", "OPENHUBFORAI_SUBHEADS"]),
]

PRODUCTS_JS = BUNDLE / "shared" / "products.js"
OPS_CONSOLE = _resource("scripts/ops_console_service.py")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    for surface, path, must, must_not in CONTRACTS:
        if not path.exists():
            ck(f"{surface}: bundle source exists", False, str(path))
            continue
        src = path.read_text(encoding="utf-8")
        for needle in must:
            ck(f"{surface}: adopts design copy/structure '{needle[:42]}'", needle in src)
        for needle in must_not:
            ck(f"{surface}: retired scaffolding/legacy absent '{needle[:42]}'", needle not in src)

    # the parent 4-product model lives in products.js (the family check verifies it fully)
    pj = PRODUCTS_JS.read_text(encoding="utf-8")
    ck("products.js: four products present [teleon, baltor, aidevobserver, openHubForAI]",
       all(f"'{p}'" in pj for p in ("teleon", "baltor", "aidevobserver", "openHubForAI")))
    ck("products.js: Open*Hub registries consolidated into OpenHubForAI (OPENHUB_REGISTRIES)",
       "OPENHUB_REGISTRIES" in pj)

    # the Global Operations Console API-keys view (credential plane, env-names only;
    # redaction-safety — no value field — is asserted by ops_console_service's own self-test)
    ops = OPS_CONSOLE.read_text(encoding="utf-8")
    ck("ops console: API-keys view + /api/ops/keys + credential plane (env-names only)",
       all(t in ops for t in ("API keys", "/api/ops/keys", "_collect_keys", "from src.teleon.runtime import credentials")))

    if fails:
        print(f"\nFAIL - check_surfaces_match_claude_design: {len(fails)} failure(s): {fails}")
        return 1
    print(f"\nPASS - check_surfaces_match_claude_design: {len(CONTRACTS)} surfaces follow the Claude Design "
          f"designs (design copy present, A/B/experiment scaffolding + legacy positioning retired); the parent "
          f"shows four products; the Operations Console exposes the credential-plane API-keys view.")
    return 0


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_surfaces_match_claude_design.py --self-test")
    raise SystemExit(0)
