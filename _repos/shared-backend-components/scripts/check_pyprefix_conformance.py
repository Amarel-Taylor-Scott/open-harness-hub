#!/usr/bin/env python3
"""Contract: every MIGRATED path stays 100% conformant to the pyprefix typed-identifier convention.

The migration manifest (_repos/shared-backend-components/architecture/pyprefix_migration.json) lists the paths already renamed to the
typed convention (py_class_/py_function_/py_method_/py_inst_/py_const_). This gate runs `pyprefix check`
over each migrated path and FAILS on any violation — so once a package adopts the typed names, new or
edited code cannot silently diverge. This is the regression contract the owner asked for; it is what
keeps the deterministic-graph guarantee true over time.

An EMPTY `migrated` list passes (nothing migrated yet — the migration is just starting). As ChatGPT
Codex migrates packages, each is added to the manifest only after the full proof gate is green, and
from then on this contract holds the line. serves_truth=false.

CLI:  python3 _repos/shared-backend-components/scripts/check_pyprefix_conformance.py --self-test
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
MANIFEST = _resource("architecture") / "pyprefix_migration.json"

sys.path.insert(0, str(_resource("scripts")))
import pyprefix  # noqa: E402  (the convention + checker live here, single source)


def _check_manifest(manifest_path: Path, exempt_extra: set | None = None) -> tuple[list[dict], list[str]]:
    """Return (violations, checked_paths) for every `migrated` path in the manifest."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    exempt = set(data.get("global_exempt", [])) | (exempt_extra or set())
    violations: list[dict] = []
    checked: list[str] = []
    for rel in data.get("migrated", []):
        target = (_resource(rel))
        if not target.exists():
            violations.append({"path": rel, "error": "migrated path does not exist"})
            continue
        checked.append(rel)
        violations.extend(pyprefix.check_path(target, exempt=exempt))
    return violations, checked


def _self_test() -> int:
    import tempfile
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # the real manifest parses + an empty migrated list passes
    real = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ck("manifest parses + declares the contract fields",
       all(k in real for k in ("migrated", "global_exempt", "policy", "standard", "conformance_gate")))
    v_real, checked_real = _check_manifest(MANIFEST)
    ck("every migrated path (if any) is 100% conformant",
       not [x for x in v_real if "error" not in x],
       str([f"{x.get('path')}:{x.get('line')} {x.get('name')}" for x in v_real][:6]))
    ck("no migrated path is missing on disk", not [x for x in v_real if x.get("error")], str([x for x in v_real if x.get("error")]))

    # hermetic: a manifest pointing at a CONFORMANT file passes; a NON-conformant one fails
    with tempfile.TemporaryDirectory() as d:
        good = Path(d) / "good.py"
        good.write_text("py_const_good__N = 1\n\n\ndef py_function_good__go():\n    return py_const_good__N\n", encoding="utf-8")
        bad = Path(d) / "bad.py"
        bad.write_text("def go():\n    return 1\n", encoding="utf-8")
        man_good = Path(d) / "m_good.json"
        man_good.write_text(json.dumps({"migrated": ["good.py"], "global_exempt": []}), encoding="utf-8")
        man_bad = Path(d) / "m_bad.json"
        man_bad.write_text(json.dumps({"migrated": ["bad.py"], "global_exempt": []}), encoding="utf-8")

        # patch REPO root resolution by checking the temp paths directly via pyprefix
        ck("conformant migrated file -> 0 violations", not pyprefix.check_path(good, exempt=set()))
        bad_v = pyprefix.check_path(bad, exempt=set())
        ck("non-conformant migrated file -> flagged with location-derived target",
           any(x["name"] == "go" and x["target"] == "py_function_bad__go" for x in bad_v))
        ent = Path(d) / "ent.py"
        ent.write_text("def main():\n    return 1\n\n\ndef _self_test():\n    return 2\n", encoding="utf-8")
        ck("entry points exempt (main / _self_test never flagged)", not pyprefix.check_path(ent, exempt=set()))

    if fails:
        print(f"\nFAIL - check_pyprefix_conformance: {len(fails)} failure(s): {fails}")
        return 1
    print(f"\nPASS - check_pyprefix_conformance: the migration manifest is valid; all {len(checked_real)} migrated "
          f"path(s) are 100% conformant to the pyprefix convention (regression contract holds); the checker flags "
          f"non-conformant code with its typed target name.")
    return 0


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    if "--self-test" in argv or not argv:
        return _self_test()
    v, checked = _check_manifest(MANIFEST)
    for x in v:
        print(f"  {x.get('path')}:{x.get('line', '?')}  {x.get('name', x.get('error'))}")
    print(f"{len(checked)} migrated path(s) checked, {len(v)} violation(s).")
    return 1 if v else 0


if __name__ == "__main__":
    raise SystemExit(main())
