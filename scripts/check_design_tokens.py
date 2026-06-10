#!/usr/bin/env python3
"""scripts.check_design_tokens — No-Magic-Values, applied to CSS design tokens.

Reports CSS custom properties (``--token``) that are DEFINED with more than one distinct value
across the ``web/baltor`` surfaces — the design-token analogue of the repo's no-magic-values rule
(``docs/codex/no-magic-values.md``): a value typed twice is a value that drifts. The drift this
surfaces is documented in ``docs/standards/DESIGN.md`` §Known-drift.

This is a **REPORTER, not a CI gate**: drift currently exists by design until the owner picks the
canonical palette (a brand decision — see DESIGN.md). The default run prints the drift table and
exits 0. ``--strict`` exits 1 on any drift — wire that into CI only AFTER convergence to a single
``web/baltor/tokens.css``.

``var(--x)`` aliases are EXCLUDED from drift: a token re-pointed to different other tokens by context
(e.g. ``--rail: var(--amber)`` on one stage vs ``var(--blue)`` on another) is legitimate, not drift.

CLI:
    python3 scripts/check_design_tokens.py             # scan web/baltor, print drift report (exit 0)
    python3 scripts/check_design_tokens.py --strict    # exit 1 if any token has >1 distinct value
    python3 scripts/check_design_tokens.py --self-test  # offline, deterministic proof of the detector
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

# ── Constants (single source; No-Magic-Values) ───────────────────────────────
#: Where the shipped front-end design tokens live.
WEB_DIR = _REPO_ROOT / "web" / "baltor"
#: File types that carry CSS custom-property definitions.
WEB_GLOBS = ("*.html", "*.css")
#: A CSS custom-property DEFINITION ``--name: value``. The value class excludes the delimiters that
#: terminate a CSS value (``; { } " ' < > newline``) so it never swallows a trailing ``;``-less inline
#: style attribute or HTML markup (a CSS value contains none of those).
TOKEN_DEF_RE = re.compile(r'(--[A-Za-z0-9-]+)\s*:\s*([^;{}"\'<>\n]+)')
#: Pull only ``<style>…</style>`` blocks out of an HTML file — palette tokens live in :root there;
#: inline ``style="--rail:…"`` attributes are per-element intentional tints, NOT palette drift.
_STYLE_BLOCK_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
#: Values that are themselves references to another token — excluded from drift (legit aliasing).
_VAR_REF_RE = re.compile(r"^var\(")


def _css_from(text: str, *, is_html: bool) -> str:
    """The CSS to scan: <style> blocks only for HTML (skips inline per-element overrides); whole file for .css."""
    if is_html:
        return "\n".join(_STYLE_BLOCK_RE.findall(text))
    return text


def scan_text(text: str) -> dict[str, list[str]]:
    """Return ``{token: [values…]}`` for every ``--token: value;`` definition in ``text``."""
    out: dict[str, list[str]] = {}
    for name, val in TOKEN_DEF_RE.findall(text):
        out.setdefault(name, []).append(val.strip())
    return out


def merge(per_file: dict[str, dict[str, list[str]]]) -> dict[str, set[str]]:
    """Aggregate to ``{token: {distinct non-alias values across all files}}``."""
    agg: dict[str, set[str]] = {}
    for vals in per_file.values():
        for name, vlist in vals.items():
            for v in vlist:
                if _VAR_REF_RE.match(v):
                    continue  # var() alias — context-dependent, not drift
                agg.setdefault(name, set()).add(v)
    return agg


def drift(agg: dict[str, set[str]]) -> dict[str, set[str]]:
    """The subset of tokens defined with >1 distinct value (sorted by token name)."""
    return {k: v for k, v in sorted(agg.items()) if len(v) > 1}


def scan_dir(web_dir: Path = WEB_DIR) -> tuple[dict[str, set[str]], int]:
    """Scan ``web_dir`` for token defs. Returns ``(aggregated values, files_scanned)``."""
    per_file: dict[str, dict[str, list[str]]] = {}
    files: list[Path] = []
    for g in WEB_GLOBS:
        files.extend(sorted(web_dir.glob(g)))
    for f in files:
        css = _css_from(f.read_text(encoding="utf-8", errors="ignore"), is_html=f.suffix.lower() != ".css")
        per_file[f.name] = scan_text(css)
    return merge(per_file), len(files)


def _report(strict: bool) -> int:
    agg, nfiles = scan_dir()
    rel = WEB_DIR.relative_to(_REPO_ROOT)
    d = drift(agg)
    print(f"── design-token drift report ── scanned {nfiles} file(s) under {rel} ──")
    if not d:
        print("  no drift: every --token has a single value across all surfaces. ✓")
        return 0
    print(f"  {len(d)} token(s) defined with >1 distinct value (see docs/standards/DESIGN.md §Known-drift):")
    for name, vals in d.items():
        print(f"    {name}: {', '.join(sorted(vals))}")
    print("\n  REPORTER mode → exit 0 (drift is expected until the owner picks the canonical palette).")
    if strict:
        print("  --strict set → failing on drift.")
        return 1
    return 0


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # ── synthetic fixture: --bg drifts (#000 vs #111); --ink stable; --rail is a var() alias ──
    a = scan_text(":root{--bg:#000;--ink:#fff;--rail:var(--amber);}")
    b = scan_text(".x{--bg:#111;--ink:#fff;--rail:var(--blue);}")
    check("scan_text extracts token defs (not var() usages)",
          a.get("--bg") == ["#000"] and a.get("--ink") == ["#fff"])
    agg = merge({"a": a, "b": b})
    check("merge unions distinct values per token", agg["--bg"] == {"#000", "#111"} and agg["--ink"] == {"#fff"})
    check("var() aliases excluded from aggregation", "--rail" not in agg)
    d = drift(agg)
    check("drift flags --bg (2 distinct values)", "--bg" in d and len(d["--bg"]) == 2)
    check("drift ignores stable --ink (1 value)", "--ink" not in d)
    # a multi-prop rule must not be swallowed across ; boundaries
    multi = scan_text("a{color:red;--x:#aaa;background:blue;--y:#bbb;}")
    check("definitions parsed independently within a rule", multi.get("--x") == ["#aaa"] and multi.get("--y") == ["#bbb"])

    # ── real scan: runs cleanly + detects the drift documented in DESIGN.md ──
    real, nfiles = scan_dir()
    check("real scan reads web/baltor file(s)", nfiles >= 1, str(nfiles))
    rd = drift(real)
    check("real scan detects the documented dark-ops drift (--bg/--ink/--line/--muted)",
          any(t in rd for t in ("--bg", "--ink", "--line", "--muted")), str(sorted(rd)))

    print(f"\n{'all check_design_tokens self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Report CSS design tokens defined with >1 value (No-Magic-Values for CSS).")
    p.add_argument("--strict", action="store_true", help="exit 1 on any drift (CI gate — use only after convergence)")
    p.add_argument("--self-test", action="store_true", help="offline deterministic proof of the detector")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    return _report(strict=args.strict)


if __name__ == "__main__":
    raise SystemExit(_main())
