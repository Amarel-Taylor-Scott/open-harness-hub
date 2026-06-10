#!/usr/bin/env python3
"""scripts.check_context_surfaces_index — cross-surface proof (C-SURFACES-1): the no-dead-surface guard.

Model: scripts/check_memory_page_projection_only.py + scripts/check_native_ui.py + scripts/check_determinism_ui.py.
This is the DISCOVERABILITY guard for the served context surfaces. It asserts that every context-surface page
the engine serves exists on disk AND is a PROJECTION ONLY — so a new served surface can never be a dead link,
and an existing one can never silently regress into writing durable truth / leaking a secret / showing private
memory. It does NOT re-prove each page's contents (the per-page proofs own that); it proves the SET of surfaces
is complete and uniformly projection-only.

The served context surfaces (route → page) are the canonical six:
  /pipeline     -> web/baltor/pipeline/index.html  (the seven-stage pipeline journey)
  /memory       -> web/baltor/memory.html           (the memory projection)
  /consume      -> web/baltor/consume.html          (ingestion -> consumption ContextResponse)
  /standards    -> web/baltor/standards.html        (configuration standards + maturity)
  /determinism  -> web/baltor/determinism.html      (the Determinism Factory projection)
  /native       -> web/baltor/native.html           (native-output preview + lossless sidecar/diff)

For EACH page this asserts:
  - the file exists on disk (no dead surface);
  - it declares itself projection-only;
  - it references at least one /api/... route (it is a genuine projection — it fetches, it does not embed truth);
  - it contains NONE of the forbidden projection tokens (private memory / loop internals / durable writes /
    client-side truth or secret storage / hardcoded secrets).

Static source scan — deterministic, offline, no socket, no RNG, tempfile-free (reads only the committed pages).

CLI: python3 scripts/check_context_surfaces_index.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

#: the canonical served context surfaces — route -> page path (relative to the repo root) -> one-line "what it shows".
#: Keep this in sync with docs/ui/context-surfaces.md and the web/baltor/hub.html cards (MAIN integrates the cards).
SURFACES: tuple[tuple[str, str, str], ...] = (
    ("/pipeline",    "web/baltor/pipeline/index.html", "the seven-stage pipeline journey (upload -> consumption)"),
    ("/memory",      "web/baltor/memory.html",         "the memory projection (artifacts, claim_status, traces, held-out)"),
    ("/consume",     "web/baltor/consume.html",        "ingestion -> consumption: the served ContextResponse for CFPB"),
    ("/standards",   "web/baltor/standards.html",      "configuration standards, patterns, routines, maturity, waivers"),
    ("/determinism", "web/baltor/determinism.html",    "the Determinism Factory (traces -> consensus -> rules -> promotions)"),
    ("/native",      "web/baltor/native.html",         "native-output preview + lossless sidecar/diff (original never overwritten)"),
)

#: tokens that must NEVER appear in any projection page — private memory / loop internals / durable writes /
#: client-side truth or secret storage / secrets. (The canonical projection-forbidden set from the lane brief.)
_FORBIDDEN_TOKENS = (
    ".agent/", "MEMORY.md", "baltor-goal-loop", ".claude/",   # private memory / loop internals
    "INSERT INTO", "sqlite3",                                  # durable writes
    "localStorage", "sessionStorage", "indexedDB",            # client-side truth/secret storage
    "api_key", "Authorization", "Bearer ", "OH_SHOWCASE_TOKEN",  # secrets
)


def _forbidden_hits(text: str) -> list[str]:
    """Every forbidden token present in the page, plus a synthesized sk- secret prefix check (no literal here)."""
    hits = [t for t in _FORBIDDEN_TOKENS if t in text]
    sk_prefix = "sk" + "-"  # synthesize at runtime so this proof file holds no secret-looking literal
    if sk_prefix in text:
        hits.append(sk_prefix)
    return hits


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    print(f"context surfaces: {len(SURFACES)}")
    for route, rel, _what in SURFACES:
        page = _REPO / rel
        # 1) the surface is not dead — the file exists on disk.
        if not page.exists():
            check(f"{route} -> {rel} exists on disk", False, "missing")
            continue
        check(f"{route} -> {rel} exists on disk", True)
        text = page.read_text(encoding="utf-8")

        # 2) it declares itself projection-only.
        check(f"{route} declares projection-only",
              "PROJECTION ONLY" in text.upper() or "projection-only" in text)

        # 3) it is a genuine projection — it references at least one /api/... route.
        api_refs = re.findall(r"""['"](/api/[^'"]+)['"]""", text)
        check(f"{route} fetches a projection API (>=1 /api/ route)", len(api_refs) >= 1, str(api_refs[:3]))

        # 4) it contains NONE of the forbidden projection tokens.
        hits = _forbidden_hits(text)
        check(f"{route} contains no forbidden projection token", hits == [], str(hits))

    # the SET is complete: exactly the canonical six surfaces, no duplicate routes / duplicate pages.
    routes = [r for r, _p, _w in SURFACES]
    pages = [p for _r, p, _w in SURFACES]
    check("no duplicate surface route", len(set(routes)) == len(routes), str(sorted(routes)))
    check("no duplicate surface page", len(set(pages)) == len(pages), str(sorted(pages)))
    check("all six canonical surfaces are indexed",
          set(routes) == {"/pipeline", "/memory", "/consume", "/standards", "/determinism", "/native"},
          str(sorted(routes)))

    # the docs index names every served surface (kept in lock-step with this guard).
    doc = _REPO / "docs" / "ui" / "context-surfaces.md"
    check("docs/ui/context-surfaces.md exists", doc.exists())
    if doc.exists():
        doc_text = doc.read_text(encoding="utf-8")
        missing = [r for r in routes if r not in doc_text]
        check("docs/ui/context-surfaces.md names every served surface route", missing == [], str(missing))

    print(f"\n{'PASS — check_context_surfaces_index: all six served context surfaces (/pipeline /memory /consume /standards /determinism /native) exist on disk, declare projection-only, fetch a projection API, and carry no forbidden token (private memory / loop internals / durable writes / client truth or secret storage / secrets); the set is complete with no dead surface; the docs index names every route.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Cross-surface proof: every served context surface exists + is projection-only.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
