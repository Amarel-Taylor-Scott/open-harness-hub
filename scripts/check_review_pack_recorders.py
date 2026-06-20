#!/usr/bin/env python3
"""scripts.check_review_pack_recorders — guard: every review-pack screenshot has a real producer.

``scripts/make_review_pack.py`` lists a curated set of visual artifacts (``SCREENSHOTS``) as review
evidence. That list is hand-maintained, while the things that PRODUCE the frames live in the e2e
recorders (``e2e/record_*.mjs`` ``shot(page, 'name')`` calls) and the GIF stitcher (``e2e/make_gif.mjs``,
parameterised by ``OUT=…gif``). Nothing kept the two in sync — so a SCREENSHOTS entry could reference a
frame that NO committed command regenerates (a dead/stale-evidence reference: the file lingers on disk
from a one-off manual run and silently goes stale while everything around it refreshes). This is the
``live-dashboard.gif`` drift caught in pass C42 — produced once by hand, then a day stale while the
``dash-*.png`` it was stitched from were refreshed.

This proof asserts: **every ``SCREENSHOTS`` entry is produced by some COMMITTED recorder/stitcher
invocation.** It reads only committed source (``.mjs`` / ``.sh`` / ``.json`` / ``make_review_pack.py``),
never the gitignored ``e2e/artifacts/`` PNGs — so it runs in CI/the flywheel without any recording having
been taken. (The reverse direction — a recorder frame NOT in SCREENSHOTS — is allowed: SCREENSHOTS is a
curated subset, e.g. record_demo emits 01–08 but the pack shows only a few.)

CLI:
    python3 scripts/check_review_pack_recorders.py             # check the real repo, print PASS/FAIL
    python3 scripts/check_review_pack_recorders.py --self-test  # fixture-logic proof + the real-repo check
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_E2E = _REPO / "e2e"

#: a `shot(<ident>, 'NAME')` call in a recorder produces NAME.png
_SHOT_RE = re.compile(r"""shot\(\s*\w+\s*,\s*['"]([A-Za-z0-9_-]+)['"]\s*\)""")
#: a direct `page.screenshot({ path: `${ART}/NAME.png` })` (or quoted path) produces NAME.png/.gif
_PATH_RE = re.compile(r"""path\s*:\s*[`'"][^`'"]*?/([A-Za-z0-9_-]+\.(?:png|gif))[`'"]""")
#: make_gif's default output: `process.env.OUT || 'NAME.gif'`
_GIF_DEFAULT_RE = re.compile(r"""process\.env\.OUT\s*\|\|\s*['"]([A-Za-z0-9_.-]+\.gif)['"]""")
#: a parameterised gif: shell `OUT=NAME.gif` or JS object `OUT: 'NAME.gif'`
_GIF_PARAM_RE = re.compile(r"""OUT\s*[=:]\s*['"]?([A-Za-z0-9_.-]+\.gif)['"]?""")


def discover_producers(files: list[Path]) -> set[str]:
    """The set of artifact filenames the given committed source files are able to (re)produce."""
    produced: set[str] = set()
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for m in _SHOT_RE.finditer(text):
            produced.add(m.group(1) + ".png")
        for m in _PATH_RE.finditer(text):
            produced.add(m.group(1))
        for rx in (_GIF_DEFAULT_RE, _GIF_PARAM_RE):
            for m in rx.finditer(text):
                produced.add(m.group(1))
    return produced


def orphans(screenshots: list[str], produced: set[str]) -> list[str]:
    """SCREENSHOTS entries that NO producer regenerates — the dead/stale-evidence references."""
    return [s for s in screenshots if s not in produced]


def _producer_files() -> list[Path]:
    files = sorted(_E2E.glob("record_*.mjs"))
    for extra in ("make_gif.mjs", "run.sh", "package.json"):
        p = _E2E / extra
        if p.exists():
            files.append(p)
    return files


def _check_real() -> tuple[bool, str]:
    """The live guard: every make_review_pack SCREENSHOTS entry has a committed producer."""
    sys.path.insert(0, str(_REPO))
    from scripts.make_review_pack import SCREENSHOTS  # the single source of the curated list

    produced = discover_producers(_producer_files())
    missing = orphans(list(SCREENSHOTS), produced)
    if missing:
        return False, f"{len(missing)} SCREENSHOTS entr{'y' if len(missing) == 1 else 'ies'} with NO committed producer: {missing}"
    return True, f"all {len(SCREENSHOTS)} review-pack screenshots are produced by a committed recorder/stitcher ({len(produced)} producible)"


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    # 1) fixture: a recorder + a gif stitcher define producers; an orphan is detected, the rest pass.
    tmp = Path(tempfile.mkdtemp(prefix="rp-recorders-"))
    (tmp / "record_foo.mjs").write_text(
        "await shot(page, 'foo-loaded');\nawait shot(page, 'foo-after');\n"
        "await page.screenshot({ path: `${ART}/foo-direct.png`, fullPage: true });\n"
        "spawnSync(node, ['make_gif.mjs'], {env: {OUT: 'foo-strip.gif'}});\n", encoding="utf-8")
    (tmp / "make_gif.mjs").write_text("const OUT = process.env.OUT || 'default-demo.gif';\n", encoding="utf-8")
    produced = discover_producers([tmp / "record_foo.mjs", tmp / "make_gif.mjs"])
    check("extracts shot() png producers", {"foo-loaded.png", "foo-after.png"} <= produced)
    check("extracts direct page.screenshot({path}) png producers", "foo-direct.png" in produced)
    check("extracts default + parameterised gif producers", {"default-demo.gif", "foo-strip.gif"} <= produced)
    check("a fully-covered SCREENSHOTS list has no orphans",
          orphans(["foo-loaded.png", "foo-direct.png", "foo-strip.gif", "default-demo.gif"], produced) == [])
    check("an unproduced entry is flagged as an orphan",
          orphans(["foo-loaded.png", "ghost.gif"], produced) == ["ghost.gif"])

    # 2) the REAL guard against the actual repo (committed files only — CI-safe, no artifacts needed).
    real_ok, real_detail = _check_real()
    check(f"REAL repo: {real_detail}", real_ok, real_detail)

    print(f"\n{'PASS — check_review_pack_recorders: every review-pack screenshot is regenerated by a committed recorder/stitcher (no dead/stale-evidence reference).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Guard: every review-pack screenshot has a committed producer.")
    p.add_argument("--self-test", action="store_true", help="fixture-logic proof + the real-repo check")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    ok, detail = _check_real()
    print(("PASS — " if ok else "FAIL — ") + detail)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(_main())
