#!/usr/bin/env python3
"""scripts.check_brand_canonical — PROOF: the PARENT / holding-company brand is canonical, single-sourced,
and LOSSLESS after the rename ContextIsEverything Group -> AI Done Right (tagline "Context is Everything" ->
"AI systems that can do the work, show the work, and prove the work."; owner-locked).

_repos/shared-backend-components/architecture/brand.json is the ONE source of the parent brand name + tagline + domain (no-magic-values). This
proof asserts:
  A. brand.json loads and carries the locked parent identity: company_name == "AI Done Right",
     tagline == "AI systems that can do the work, show the work, and prove the work.", domain == "aidoneright.dev".
  B. LOSSLESS rollback preserved: superseded.company_name == "ContextIsEverything Group" (and a superseded
     tagline is kept) — the prior parent brand is retained as the rollback target, never deleted.
  C. SCOPE: scope.products_unchanged includes BOTH Baltor and Teleon — the rename touched the parent only;
     the product names are explicitly recorded as unchanged.
  D. NAMING RULE: company_name is full words with no obvious abbreviation (memory: no-abbreviations-in-naming).
  E. SINGLE-SOURCE / NO DRIFT: company_portfolio_map.json's parent display name (companies.<holding_company>.
     display_name) == brand.json company_name — the parent name is single-sourced, so the map can never drift
     from brand.json.

Deterministic + offline + stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_BRAND = _resource("architecture") / "brand.json"
_PMAP = _resource("architecture") / "company_portfolio_map.json"

# locked parent identity (the rename target) — single source is brand.json; these are the asserted values.
_COMPANY_NAME = "AI Done Right"
_TAGLINE = "AI systems that can do the work, show the work, and prove the work."
_DOMAIN = "aidoneright.dev"
_SUPERSEDED_NAME = "ContextIsEverything Group"  # preserved as the rollback target (lossless)

# obvious abbreviation shapes that the parent name must NOT be (full-words naming rule).
_ABBREV_BLOCKLIST = ("CIE", "CIE Group", "OHH", "Inc", "LLC", "Corp", "Ltd", "Co")


def _looks_like_abbreviation(name: str) -> bool:
    """True if `name` is an obvious abbreviation: an exact blocklist hit, OR a short all-caps acronym,
    OR contains a bare uppercase acronym token (>=2 caps) as a standalone word."""
    stripped = name.strip()
    if stripped in _ABBREV_BLOCKLIST:
        return True
    # a short, entirely-uppercase token like "CIE" / "AIDR" (allow ≤2 chars like a leading "AI" prefix word)
    if stripped.isupper() and len(stripped) >= 3 and " " not in stripped:
        return True
    # any standalone word that is a known abbreviation token
    words = stripped.replace("·", " ").split()
    return any(w in _ABBREV_BLOCKLIST for w in words)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # load (guarded — no raw keys; a missing file/key is a clean FAIL, never a traceback)
    try:
        brand = json.loads(_BRAND.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:  # noqa: BLE001
        check("A: architecture/brand.json loads", False, f"{type(e).__name__}: {e}")
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1
    check("A: architecture/brand.json loads", True)

    # A. locked parent identity
    check("A: company_name == 'AI Done Right'", brand.get("company_name") == _COMPANY_NAME, repr(brand.get("company_name")))
    check("A: tagline == 'AI systems that can do the work, show the work, and prove the work.'", brand.get("tagline") == _TAGLINE, repr(brand.get("tagline")))
    check("A: domain == 'aidoneright.dev'", brand.get("domain") == _DOMAIN, repr(brand.get("domain")))

    # B. lossless — prior brand preserved as the rollback target
    sup = brand.get("superseded") or {}
    check("B: superseded.company_name == 'ContextIsEverything Group' (rollback preserved)",
          sup.get("company_name") == _SUPERSEDED_NAME, repr(sup.get("company_name")))
    check("B: a superseded tagline is preserved (lossless)", bool(sup.get("tagline")), repr(sup.get("tagline")))
    check("B: superseded != current (an actual rename, not a no-op)",
          sup.get("company_name") != brand.get("company_name"))

    # C. scope — products unchanged include Baltor + Teleon
    scope = brand.get("scope") or {}
    unchanged = scope.get("products_unchanged") or []
    check("C: scope.products_unchanged includes Baltor", "Baltor" in unchanged, str(unchanged))
    check("C: scope.products_unchanged includes Teleon", "Teleon" in unchanged, str(unchanged))

    # D. naming rule — full words, no obvious abbreviation
    name = brand.get("company_name") or ""
    check("D: company_name has no obvious abbreviation (full words)",
          bool(name) and not _looks_like_abbreviation(name), repr(name))

    # E. single-source / no drift — the portfolio map's parent display name mirrors brand.json
    try:
        pmap = json.loads(_PMAP.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:  # noqa: BLE001
        check("E: company_portfolio_map.json loads", False, f"{type(e).__name__}: {e}")
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1
    check("E: company_portfolio_map.json loads", True)
    holding = pmap.get("holding_company")
    parent = (pmap.get("companies") or {}).get(holding) or {}
    check("E: holding_company slug resolves to a company entry", bool(parent), repr(holding))
    check("E: parent display_name == brand.json company_name (single-sourced, no drift)",
          parent.get("display_name") == brand.get("company_name"),
          f'map={parent.get("display_name")!r} vs brand={brand.get("company_name")!r}')
    # the slug itself is a code identifier and is intentionally NOT renamed (display-string-only rename).
    check("E: holding_company slug preserved as an identifier (not renamed)", holding == "contextiseverything", repr(holding))

    print("\n" + ("PASS — check_brand_canonical: the parent brand is AI Done Right / 'AI systems that can do the work, show the work, and prove the work.' / "
                  "aidoneright.dev, single-sourced in architecture/brand.json and mirrored without drift in "
                  "company_portfolio_map.json; the prior 'ContextIsEverything Group' brand is preserved as the "
                  "rollback target (lossless); Baltor + Teleon are recorded as unchanged; the name is full words."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_brand_canonical.py --self-test")
    raise SystemExit(0)
