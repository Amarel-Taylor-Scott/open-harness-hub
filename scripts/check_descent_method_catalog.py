#!/usr/bin/env python3
"""check_descent_method_catalog — proof for the descent METHOD catalog: for EVERY improvement dimension (descent
axis), the concrete methods to accomplish it, each grounded in a variety of real candidate modules (researched).

Verifies the catalog covers every canonical DESCENT_AXES axis (single source), every method has a 'how' + >= 1
candidate module, every module is license-flagged with `vendorable` agreeing with its license class (copyleft/
source-available/unstated/unverified are non-vendorable — adopt-behind-a-port only), and the generated human
"how-to per dimension" map is fresh. Discovery != trust; nothing here is promoted; serves_truth=false.

  --build      (re)write the human method-catalog map
  --self-test  validate the catalog + map (the registered proof)

CLI: PYTHONPATH=. python3 scripts/check_descent_method_catalog.py --build | --self-test
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    _R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _R not in sys.path:
        sys.path.insert(0, _R)

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_CAT = _REPO / "architecture" / "descent_method_catalog.json"
_MAP = _REPO / "docs" / "architecture" / "descent-method-catalog.md"

_PERMISSIVE = ("mit", "apache-2.0", "bsd", "isc", "cc0", "bsd-3", "apache")
_BLOCKED = ("agpl", "gpl", "lgpl", "proprietary", "bsl", "elv2", "source-available", "unstated", "unverified")


def _vendorable(license_: str) -> bool:
    l = license_.lower()
    if any(t in l for t in _BLOCKED):
        return False
    return any(l.startswith(p) or l == p for p in _PERMISSIVE)


def load() -> dict:
    return json.loads(_CAT.read_text())


def render_map(c: dict) -> str:
    lines = ["# Descent method catalog — how to accomplish each dimension (generated)",
             "",
             f"> GENERATED from `architecture/descent_method_catalog.json` by "
             f"`scripts/check_descent_method_catalog.py` — do not hand-edit. Updated {c['updated']}.",
             "", f"{c['principle']}", "",
             "Each module is a **candidate** (discovery ≠ trust). `[v]` = vendorable (clean permissive); "
             "`[port]` = copyleft/source-available/unstated/unverified → adopt behind a port, verify before use.", ""]
    for d in c["dimensions"]:
        lines.append(f"## `{d['axis']}` ({len(d['methods'])} methods)")
        lines.append("")
        for m in d["methods"]:
            lines.append(f"- **{m['method']}** — {m['how']}")
            for mod in m["modules"]:
                tag = "[v]" if mod["vendorable"] else "[port]"
                lines.append(f"  - {tag} `{mod['repo']}` — {mod['what']} — {mod['license']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def write_map() -> str:
    _MAP.parent.mkdir(parents=True, exist_ok=True)
    _MAP.write_text(render_map(load()))
    return str(_MAP.relative_to(_REPO))


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    from src.teleon.evolution.descent_axes import DESCENT_AXES

    c = load()
    dims = c["dimensions"]
    axes = {d["axis"] for d in dims}
    ck("catalog carries the principle + serves_truth false", bool(c.get("principle")) and c.get("serves_truth") is False)

    # single source: EVERY canonical descent axis has a methods list (no dimension left without a how)
    missing = sorted(set(DESCENT_AXES) - axes)
    ck("every canonical DESCENT_AXES dimension is covered (all 17)", not missing and len(axes) >= len(DESCENT_AXES), str(missing))

    # every dimension has methods; every method has a 'how' + >= 1 module; every module is repo+license+vendorable
    methods = [m for d in dims for m in d["methods"]]
    modules = [x for m in methods for x in m["modules"]]
    ck("every dimension has >= 1 method", all(d["methods"] for d in dims))
    ck("every method has a 'how' + at least one candidate module",
       all(m.get("how") and m.get("modules") for m in methods))
    ck("every module carries repo + license + vendorable",
       all({"repo", "license", "vendorable"} <= set(x) for x in modules))

    # the governance teeth: vendorable agrees with the license class (copyleft/source-available/unverified -> not vendorable)
    mism = [x["repo"] for x in modules if x["vendorable"] != _vendorable(x["license"])]
    ck("vendorable agrees with the license class (consistent governance)", not mism, str(mism))
    leaky = [x["repo"] for x in modules if not _vendorable(x["license"]) and x["vendorable"]]
    ck("no copyleft/source-available/unstated/unverified module is marked vendorable", not leaky, str(leaky))

    # it's a real VARIETY (the owner asked for "a variety of how modules"): many methods, many modules
    ck("the catalog is a real variety (>= 50 methods, >= 90 candidate modules across the dimensions)",
       len(methods) >= 50 and len(modules) >= 90, f"{len(methods)} methods / {len(modules)} modules")

    # the example the owner gave is present: tokens_in via compression / redundant-text dedupe
    ti = next((d for d in dims if d["axis"] == "tokens_in"), {})
    ti_methods = {m["method"] for m in ti.get("methods", [])}
    ck("the owner's example is captured: reduce a skill's tokens via compression + redundant-text dedupe",
       any("compression" in m for m in ti_methods) and any("dedupe" in m for m in ti_methods), str(ti_methods))

    # generated map is fresh if present; deterministic
    page = render_map(c)
    ck("the how-to map renders every dimension + method", all(d["axis"] in page for d in dims))
    if _MAP.exists():
        ck("the on-disk how-to map is fresh vs the catalog (regenerate with --build)", _MAP.read_text() == page)
    ck("deterministic", render_map(load()) == page)

    nv = sum(1 for x in modules if x["vendorable"])
    print("\n" + (f"PASS - check_descent_method_catalog: all {len(axes)} dimensions × {len(methods)} methods × "
                  f"{len(modules)} candidate modules ({nv} vendorable / {len(modules)-nv} behind-a-port); every "
                  f"method has a 'how' + a variety of researched modules; license class governs vendorability; the "
                  f"how-to map is generated. Discovery != trust — nothing promoted; never serves truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


def _main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--build" in argv:
        print("wrote:", write_map())
        return 0
    if "--self-test" in argv:
        return _self_test()
    print("usage: check_descent_method_catalog.py --build | --self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
