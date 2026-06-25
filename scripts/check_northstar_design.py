#!/usr/bin/env python3
"""scripts.check_northstar_design — the NORTHSTAR guardrail (owner 2026-06-25).

"Everything should be northstar design and setup — no placeholders, dummy, orphaned or side designs." This is the
contract that PREVENTS them:
  - HARD (gate-enforced by self_test → the live guard): egregious placeholder content in a SURFACE — lorem ipsum,
    PLACEHOLDER, 'replace me', 'dummy data'. These must NEVER ship; if one appears, the gate goes red.
  - SOFT (--check warnings): stub / coming-soon tells, and SIDE surfaces (a web/ dir that is not a registered pillar)
    — visible sprawl without failing the build.
Scoped to the surfaces (the 5 pillars' canonical surfaces + the tracked design source), so normal code TODOs are
untouched. Pairs with check_surface_and_dev_contract (which guards that the built-out surfaces still EXIST).

  --self-test   detector works + the LIVE guard (zero hard placeholders across all current surface files)
  --check       report hard + soft + side-surface findings
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
SPEC = REPO / "architecture" / "surface_capability_spec.json"

# all-caps PLACEHOLDER is a deliberate placeholder MARKER (case-sensitive); the descriptive phrases are real
# placeholder CONTENT (case-insensitive). Lowercase "placeholder" (HTML input attrs / JS identifiers) is NOT a tell.
HARD = re.compile(r"(?i:lorem ipsum|placeholder text|replace[ _]me\b|dummy data|sample sample)|\bPLACEHOLDER\b")
SOFT = re.compile(r"coming soon|full content lands next|reuses the shared kit skeleton|\bstub\b|\bTODO\b|\bFIXME\b", re.I)
SURFACE_GLOBS = ("*.html", "*.jsx", "*.js")


def _surface_roots() -> list[Path]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    roots = [REPO / p["canonical_surface"] for p in spec.get("pillars", []) if (REPO / p["canonical_surface"]).is_dir()]
    design = REPO / "dist" / "sites" / "openharness-design"
    if design.is_dir():
        roots.append(design)
    return roots


def _surface_files() -> list[Path]:
    out: list[Path] = []
    for base in _surface_roots():
        for g in SURFACE_GLOBS:
            out += [f for f in base.rglob(g) if "node_modules" not in f.parts and "vendor" not in f.parts]
    return sorted(set(out))


def _scan(rx: re.Pattern) -> list[str]:
    hits: list[str] = []
    for f in _surface_files():
        try:
            t = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for m in rx.finditer(t):
            pre = t[max(0, m.start() - 13):m.start()].rstrip().lower()
            if pre.endswith(("placeholder", 'placeholder="', "placeholder='", "placeholder:")):
                continue  # legit HTML input placeholder= attribute, not placeholder CONTENT
            ln = t.count("\n", 0, m.start()) + 1
            hits.append(f"{f.relative_to(REPO)}:{ln}: '{m.group(0)}'")
    return hits


def hard_violations() -> list[str]:
    return _scan(HARD)


def soft_warnings() -> list[str]:
    return _scan(SOFT)


def side_surfaces() -> list[str]:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    reg = {p["canonical_surface"].split("/")[-1] for p in spec["pillars"] if p["canonical_surface"].startswith("web/")}
    web = REPO / "web"
    if not web.is_dir():
        return []
    skip = {"vendor", "shared", "node_modules"}
    return [f"web/{d.name}" for d in sorted(web.iterdir())
            if d.is_dir() and d.name not in reg and d.name not in skip and not d.name.startswith((".", "_"))]


def check() -> int:
    hard, soft, side = hard_violations(), soft_warnings(), side_surfaces()
    for s in side:
        print(f"  [warn · side surface] {s} — not a registered pillar in surface_capability_spec")
    for w in soft[:25]:
        print(f"  [warn · stub] {w}")
    if soft[25:]:
        print(f"  … +{len(soft) - 25} more stub warnings")
    if hard:
        print("NORTHSTAR VIOLATION — placeholder/dummy content in a surface (must be real, not placeholder):")
        for v in hard:
            print(f"  [placeholder] {v}")
        return 1
    print(f"northstar OK ({len(_surface_files())} surface files; 0 hard placeholders; "
          f"{len(soft)} stub warning(s); {len(side)} side surface(s))")
    return 0


def self_test() -> int:
    assert HARD.search("PLACEHOLDER") and HARD.search("Lorem Ipsum dolor"), "catches markers"
    assert not HARD.search("the real product copy") and not HARD.search('<input placeholder="Email">'), "ignores lowercase attrs"
    assert isinstance(side_surfaces(), list) and isinstance(soft_warnings(), list)
    hv = hard_violations()
    assert hv == [], f"northstar: hard placeholder(s) found in a surface: {hv[:5]}"   # LIVE guard
    print(f"check_northstar_design self-test: OK (detector + LIVE guard: 0 hard placeholders across "
          f"{len(_surface_files())} surface files)")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    if "--check" in argv:
        return check()
    print("usage: check_northstar_design.py --self-test | --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
