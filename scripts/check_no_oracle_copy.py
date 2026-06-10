#!/usr/bin/env python3
"""scripts.check_no_oracle_copy — CI guard: no new user-facing "Oracle" PRODUCT copy.

"Oracle" is retired as product language (docs/product-language.md). This fails if "oracle"
(case-insensitive) appears in a USER-FACING surface outside the allowlist. The allowlist is the
ONE migration map (data/alias-packs/legacy-oracle-migration.yaml), the legacy redirect stub
(web/baltor/oracle-hero.html), and the product-language doc itself. The *technical* term
"oracle source / oracle publisher" lives in docs/strategy + scripts/processors/assurance and is
NOT scanned here (this check targets user-facing UI + alias copy only).

CLI:
    python3 scripts/check_no_oracle_copy.py --self-test
    python3 scripts/check_no_oracle_copy.py            # scan; exit 1 on violations
"""
from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]

#: User-facing surfaces to scan (globs relative to repo root).
SCAN_GLOBS = ["web/baltor/**/*.html", "web/baltor/**/*.js", "data/alias-packs/*.yaml"]

#: Allowlisted files where "oracle" may legitimately appear.
ALLOWLIST = {
    "web/baltor/oracle-hero.html",                    # legacy redirect stub (deprecation comment)
    "data/alias-packs/legacy-oracle-migration.yaml",  # the deprecation MAP
    "docs/product-language.md",                        # the migration note
}


def scan_text(text: str) -> bool:
    """True iff the text contains 'oracle' (case-insensitive)."""
    return "oracle" in (text or "").lower()


def scan() -> list[str]:
    """Return violations: user-facing files (outside the allowlist) that contain 'oracle'."""
    violations: list[str] = []
    seen: set[Path] = set()
    for glob in SCAN_GLOBS:
        for path in _REPO.glob(glob):
            if not path.is_file() or path in seen:
                continue
            seen.add(path)
            rel = path.relative_to(_REPO).as_posix()
            if rel in ALLOWLIST:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            # Ignore governance declarations: a `blocked_terms` list legitimately names "oracle".
            scannable_lines = [ln for ln in text.splitlines() if "blocked_terms" not in ln.lower()]
            scannable = "\n".join(scannable_lines)
            if scan_text(scannable):
                first = next((ln.strip() for ln in scannable_lines if "oracle" in ln.lower()), "")
                violations.append(f"{rel}: {first[:100]}")
    return violations


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    check("scan_text flags 'Baltor Oracle Engine'", scan_text("Baltor Oracle Engine"))
    check("scan_text passes 'Baltor Context Engine'", not scan_text("Baltor Context Engine"))
    violations = scan()
    check("repo user-facing surfaces are Oracle-free (outside allowlist)", not violations, "; ".join(violations[:3]))

    print(f"\n{'all check_no_oracle_copy self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="CI guard: no new user-facing Oracle product copy.")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    violations = scan()
    if violations:
        print("FAIL — user-facing 'Oracle' copy found outside the allowlist:")
        print("\n".join(f"  - {v}" for v in violations))
        return 1
    print("OK — no new user-facing Oracle product copy.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
